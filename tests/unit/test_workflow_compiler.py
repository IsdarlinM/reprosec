from reprosec.capsule import initialize_directory,add_request,add_response
from reprosec.models import RequestRecord,ResponseRecord
from reprosec.workflow_compiler import WorkflowCompiler


def test_compiler_outputs_hypothesis_and_extractors(tmp_path):
    root=tmp_path/'c';initialize_directory(root,'x');r1=RequestRecord(method='POST',url='https://example.test/doc');add_request(root,r1);add_response(root,ResponseRecord(request_id=r1.request_id,status_code=200,body='{"document_id":"abc123"}'))
    r2=RequestRecord(method='GET',url='https://example.test/doc/abc123');add_request(root,r2)
    out=WorkflowCompiler().compile(root);assert out['status']=='HYPOTHESIS' and out['extractors'] and out['deterministic_replay_required'] is True
