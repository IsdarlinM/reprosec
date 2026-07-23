import json
import pytest
from sric.scope import ScopeEngine, ScopePolicy
from reprosec.browser import BrowserRecorder
from reprosec.capture import CaptureRecorder, CaptureDeniedError
from reprosec.capsule import initialize_directory


def test_browser_recorder_redacts_sensitive_fields(tmp_path):
    root=tmp_path/'c';initialize_directory(root,'x');p=tmp_path/'events.jsonl';p.write_text(json.dumps({'type':'storage','data':{'token':'abc','safe':'ok'}})+'\n')
    events=BrowserRecorder(root).import_jsonl(p)
    assert events[0].data['token']=='<redacted>' and events[0].data['safe']=='ok'


def test_capture_fails_scope_before_network_and_tls_tunnel_is_metadata_only(tmp_path):
    root=tmp_path/'c';initialize_directory(root,'x');rec=CaptureRecorder(root,ScopeEngine(ScopePolicy(allow_targets=['allowed.example'])))
    with pytest.raises(CaptureDeniedError):rec.capture('GET','https://denied.example/')
    evt=rec.record_tls_tunnel('allowed.example',443);assert evt.data['decrypted'] is False


def test_browser_recording_lifecycle(tmp_path):
    from reprosec.browser import BrowserRecordingSession
    root=tmp_path/'c2';initialize_directory(root,'x');rec=BrowserRecordingSession(root)
    assert rec.status()['active'] is False
    assert rec.start(actor_id='A')['active'] is True
    assert rec.stop()['active'] is False


def test_capture_proxy_refuses_non_loopback(tmp_path):
    from reprosec.capture import LocalCaptureProxy
    root=tmp_path/'c3';initialize_directory(root,'x')
    with pytest.raises(ValueError):LocalCaptureProxy(root,ScopeEngine(ScopePolicy()),host='0.0.0.0')
