from reprosec.conformance import run_public_suite

def test_public_conformance_suite():
    r=run_public_suite();assert r['passed']==r['total'] and r['total']>=5
