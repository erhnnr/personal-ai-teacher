import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))
import verify_curriculum_evidence as v

def make_corpus(package_id, text):
    return {"packages":[{"package_id":package_id,"pages":[{
        "page":10,"text":text,"text_status":"READY","image_status":"LINKED",
        "source_anchor":"index.html#p=10","html_path":"files/basic-html/page10.html",
        "image_path":"files/thumb/10.jpg"}]}]}

def make_outcome(grade, package_id, title):
    return {"id":"BİY.X","grade":grade,"theme_number":1,"theme_name":"Tema",
            "title":title,"candidate_pages":[{"package_id":package_id,"page":10,"score":100.0}]}

def test_wrong_affinity_cannot_verify():
    o=make_outcome(9,"MEBI-AYT-BIYOLOJI","Genetik testlerin danışmanlığın önemi")
    r=v.verify_candidate(o,o["candidate_pages"][0],v.build_page_lookup(make_corpus("MEBI-AYT-BIYOLOJI","Genetik testlerin danışmanlığın önemi")))
    assert r["verification_status"]=="REVIEW_REQUIRED"

def test_two_hits_bigram_still_review():
    o=make_outcome(12,"MEBI-AYT-BIYOLOJI","Genetik testlerin danışmanlık önemi")
    r=v.verify_candidate(o,o["candidate_pages"][0],v.build_page_lookup(make_corpus("MEBI-AYT-BIYOLOJI","Genetik testlerin başka içerik")))
    assert r["checks"]["distinctive_title_hit_count"]==2
    assert r["checks"]["title_bigram_hit_count"]==1
    assert r["verification_status"]=="REVIEW_REQUIRED"

def test_three_hits_with_affinity_can_verify():
    o=make_outcome(12,"MEBI-AYT-BIYOLOJI","DNA replikasyonu genetik kopyalanma")
    r=v.verify_candidate(o,o["candidate_pages"][0],v.build_page_lookup(make_corpus("MEBI-AYT-BIYOLOJI","DNA replikasyonu genetik süreç")))
    assert r["checks"]["distinctive_title_hit_count"]>=3
    assert r["checks"]["package_affinity"] is True
    assert r["verification_status"]=="VERIFIED_SUPPORT_CANDIDATE"
