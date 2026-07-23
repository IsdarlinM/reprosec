from reprosec.capsule import initialize_directory, add_actor, add_session, add_validation, build_manifest
from reprosec.models import ActorRecord, SessionRecord, SecretReference, ValidationRecord


def test_rcap03_layout_multi_actor_secret_refs_and_validation(tmp_path):
    root=tmp_path/'c';meta=initialize_directory(root,'v03')
    assert meta.schema_version=='0.3' and all((root/x).is_dir() for x in ('actors','sessions','network','validation'))
    actor=ActorRecord(label='Actor A');add_actor(root,actor)
    session=SessionRecord(actor_id=actor.actor_id,label='browser',secret_references=[SecretReference(secret_ref='SEC-1',purpose='session-cookie')]);add_session(root,session)
    validation=ValidationRecord(result='VALIDATED',evidence_ids=['E1']);add_validation(root,validation)
    raw=(root/'sessions'/f'{session.session_id}.json').read_text(); assert 'SEC-1' in raw and 'actual-cookie-value' not in raw
    assert build_manifest(root).schema_version=='0.3'


def test_capsule_can_link_to_shared_sric_workspace(tmp_path):
    from sric.workspace import Workspace
    from reprosec.capsule import initialize_directory
    ws=Workspace.create(tmp_path,'research')
    cap=tmp_path/'cap'
    meta=initialize_directory(cap,'linked',workspace_id=str(ws.metadata['workspace_id']))
    assert meta.workspace_id==ws.metadata['workspace_id']
