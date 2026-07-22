from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .capsule import safe_extract, verify_archive
from .models import CapsuleMetadata, RequestRecord, ResponseRecord
from .redact import redact_capsule

@contextmanager
def _capsule_root(raw_path: str) -> Iterator[Path]:
    p=Path(raw_path).expanduser().resolve()
    if p.is_dir() and (p/'capsule.json').is_file(): yield p; return
    if p.suffix=='.rcap' and p.is_file():
        with tempfile.TemporaryDirectory() as td: yield safe_extract(p,Path(td))
        return
    raise HTTPException(400,'path must point to an unpacked capsule directory or existing .rcap')

def _timeline(root:Path)->list[dict[str,object]]:
    events=[]
    for path in sorted((root/'requests').glob('*.json')):
        r=RequestRecord.model_validate_json(path.read_text(encoding='utf-8')); events.append({'observed_at':r.observed_at,'type':'request','id':r.request_id,'method':r.method,'url':r.url})
    for path in sorted((root/'responses').glob('*.json')):
        r=ResponseRecord.model_validate_json(path.read_text(encoding='utf-8')); events.append({'observed_at':r.observed_at,'type':'response','id':r.response_id,'request_id':r.request_id,'status':r.status_code})
    events.sort(key=lambda item:str(item['observed_at'])); return events

def create_app()->FastAPI:
    app=FastAPI(title='ReproSec Local API',version=__version__,redoc_url=None)
    @app.middleware('http')
    async def headers(request,call_next):
        response=await call_next(request); response.headers['Content-Security-Policy']="default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"; response.headers['X-Content-Type-Options']='nosniff'; response.headers['Referrer-Policy']='no-referrer'; return response
    web_root=Path(__file__).with_name('webdist')
    if (web_root/'assets').is_dir(): app.mount('/assets',StaticFiles(directory=web_root/'assets'),name='assets')
    @app.get('/',include_in_schema=False)
    async def web_index():
        index=web_root/'index.html'; return FileResponse(index) if index.is_file() else JSONResponse(status_code=503,content={'error':'Web UI assets are not installed'})
    @app.get('/api/v1/health')
    async def health()->dict[str,str]: return {'status':'ok','version':__version__}
    @app.get('/api/v1/capabilities')
    async def capabilities()->dict[str,object]: return {'schema_version':'0.2','implemented':['har_import','raw_http_import','curl_import','structured_redaction','deterministic_pack_verify','signed_manifests','safe_replay','streaming_response_limits','deterministic_extractors','semantic_json_diff','timeline','evidence_lineage'],'ai_required':False,'cloud_uploads_default':False}
    @app.get('/api/v1/verify')
    async def verify(path:str)->dict[str,object]:
        p=Path(path).expanduser().resolve()
        if p.suffix!='.rcap' or not p.is_file(): raise HTTPException(400,'path must point to an existing .rcap file')
        errors=verify_archive(p); return {'valid':not errors,'errors':errors}
    @app.get('/api/v1/workspace/inspect')
    async def workspace_inspect(path:str)->dict[str,object]:
        with _capsule_root(path) as root:
            meta=dict(CapsuleMetadata.model_validate_json((root/'capsule.json').read_text(encoding='utf-8')).model_dump(mode='json')); meta['counts']={name:len(list((root/name).glob('*.json'))) for name in ('requests','responses','workflow','assertions','extractors')}; return meta
    @app.get('/api/v1/workspace/redaction-preview')
    async def redaction_preview(path:str)->dict[str,object]:
        with _capsule_root(path) as root:
            preview=redact_capsule(root,apply=False); return {'files_scanned':preview.files_scanned,'files_changed':preview.files_changed,'detections':preview.detections,'applied':False}
    @app.get('/api/v1/workspace/timeline')
    async def workspace_timeline(path:str)->list[dict[str,object]]:
        with _capsule_root(path) as root: return _timeline(root)
    return app
