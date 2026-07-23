from reprosec.diffing import diff_responses_v2
from reprosec.models import Header, NetworkObservation, ResponseRecord


def test_diff_v2_surfaces_cookie_redirect_timing_network_and_sensitive_fields():
    a=ResponseRecord(request_id='R',status_code=200,headers=[Header(name='Set-Cookie',value='sid=1')],body='{"owner":"a"}',redirect_chain=['/a'],network=NetworkObservation(http_version='HTTP/1.1',tls_version='TLS1.2',peer_ip='1.1.1.1',duration_ms=10))
    b=ResponseRecord(request_id='R',status_code=403,headers=[Header(name='Set-Cookie',value='new=1')],body='{"owner":"b"}',redirect_chain=['/b'],network=NetworkObservation(http_version='HTTP/2',tls_version='TLS1.3',peer_ip='2.2.2.2',duration_ms=30))
    d=diff_responses_v2(a,b);assert d.redirects_changed and d.http_version_changed and d.timing_delta_ms==20 and 'new' in d.cookies_added and d.authorization_relevant
