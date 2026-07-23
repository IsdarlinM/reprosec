import json
from reprosec.importers import import_burp_xml,import_zap_json


def test_burp_xml_import(tmp_path):
    p=tmp_path/'b.xml';p.write_text('<items><item><url>https://example.com/a</url><request base64="false">GET /a HTTP/1.1\r\nHost: example.com\r\n\r\n</request><status>200</status><response base64="false">HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nok</response></item></items>')
    req,res=import_burp_xml(p);assert len(req)==1 and len(res)==1 and req[0].import_metadata['format']=='burp-xml'

def test_zap_json_import(tmp_path):
    p=tmp_path/'z.json';p.write_text(json.dumps({'messages':[{'host':'example.com','request':'GET / HTTP/1.1\r\nHost: example.com\r\n\r\n','status':200,'response_body':'ok'}]}))
    req,res=import_zap_json(p);assert len(req)==1 and len(res)==1
