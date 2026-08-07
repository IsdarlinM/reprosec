import pytest

from reprosec.stability import ReplayObservation, StabilityPolicy, analyze_stability


def observation(
    observation_id: str,
    *,
    status: int = 200,
    body: str = '{"ok":true,"request_id":"one"}',
    request_id: str = "one",
    content_type_header: str = "content-type",
) -> ReplayObservation:
    return ReplayObservation(
        observation_id=observation_id,
        status_code=status,
        headers={
            content_type_header: "application/json",
            "date": "Thu, 06 Aug 2026 20:00:00 GMT",
            "x-request-id": request_id,
        },
        body=body,
    )


def test_default_volatile_headers_are_ignored() -> None:
    items = [
        observation("one", request_id="a"),
        observation("two", request_id="b"),
        observation("three", request_id="c"),
    ]
    report = analyze_stability(items)
    assert report.deterministic is True
    assert report.stable_headers is True
    assert report.flakiness_score == 0.0


def test_content_type_header_is_case_insensitive_for_json_canonicalization() -> None:
    items = [
        observation("one", body='{"a":1,"b":2}', content_type_header="Content-Type"),
        observation("two", body='{"b":2,"a":1}', content_type_header="CONTENT-TYPE"),
        observation("three", body='{"a":1,"b":2}', content_type_header="content-type"),
    ]
    report = analyze_stability(items)
    assert report.deterministic is True
    assert report.stable_body is True


def test_ignored_json_path_prevents_false_flakiness() -> None:
    items = [
        observation("one", body='{"ok":true,"request_id":"a"}'),
        observation("two", body='{"ok":true,"request_id":"b"}'),
        observation("three", body='{"ok":true,"request_id":"c"}'),
    ]
    policy = StabilityPolicy(ignored_json_paths={"request_id"})
    report = analyze_stability(items, policy)
    assert report.deterministic is True
    assert report.stable_body is True
    assert report.volatile_json_paths == []


def test_dynamic_json_is_reported_and_not_deterministic() -> None:
    items = [
        observation("one", body='{"ok":true,"request_id":"a"}'),
        observation("two", body='{"ok":true,"request_id":"b"}'),
        observation("three", body='{"ok":true,"request_id":"c"}'),
    ]
    report = analyze_stability(items)
    assert report.deterministic is False
    assert report.stable_body is False
    assert report.volatile_json_paths == ["request_id"]
    assert report.flakiness_score == pytest.approx(2 / 3, abs=1e-6)


def test_status_variation_blocks_deterministic_assertions() -> None:
    items = [
        observation("one", status=200),
        observation("two", status=200),
        observation("three", status=503),
    ]
    report = analyze_stability(items)
    assert report.deterministic is False
    assert report.stable_status is False


def test_regex_normalization_is_explicit() -> None:
    items = [
        ReplayObservation(observation_id="one", status_code=200, body="job=123"),
        ReplayObservation(observation_id="two", status_code=200, body="job=456"),
        ReplayObservation(observation_id="three", status_code=200, body="job=789"),
    ]
    policy = StabilityPolicy(regex_substitutions=[(r"job=\d+", "job=<dynamic>")])
    assert analyze_stability(items, policy).deterministic is True


def test_invalid_regex_is_rejected_when_policy_is_created() -> None:
    with pytest.raises(ValueError, match="invalid regex substitution"):
        StabilityPolicy(regex_substitutions=[("[", "x")])


def test_minimum_sample_count_is_enforced() -> None:
    with pytest.raises(ValueError, match="at least 3 observations"):
        analyze_stability([observation("one"), observation("two")])
