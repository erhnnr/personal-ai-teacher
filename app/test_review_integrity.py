import hashlib, sys
from pathlib import Path
APP=Path(__file__).resolve().parent
sys.path.insert(0,str(APP))
from review_integrity import ReviewIntegrityError, apply_hash_bound_decisions, packet_sha256, sha256_text, validate_packet
TEXT="Official evidence text."
def packet():
    h=sha256_text(TEXT); p={"records":[{"record_id":"R1","outcome_id":"BİY.X","text_sha256":h,"reviewed_text_sha256":h,"evidence_text":TEXT}]}; p["packet_sha256"]=packet_sha256(p); return p
def decisions(p):
    h=p["records"][0]["reviewed_text_sha256"]; ph=p["packet_sha256"]
    return {"review_packet_sha256":ph,"decisions":[{"record_id":"R1","reviewed_text_sha256":h,"review_packet_sha256":ph,"status":"APPROVED_FOR_EVIDENCE_READY","reviewer_type":"EXTERNAL_LLM","reviewer_id":"reviewer-x","factual_support":True,"outcome_support":True,"source_consistency":True,"rationale":"Supported."}]}
def must_fail(fn):
    try: fn()
    except ReviewIntegrityError: return
    raise AssertionError("Expected ReviewIntegrityError")
def test_exact_utf8_hash(): assert sha256_text(TEXT)==hashlib.sha256(TEXT.encode("utf-8")).hexdigest()
def test_valid_packet(): validate_packet(packet())
def test_text_tamper_blocked():
    p=packet(); p["records"][0]["evidence_text"]="Tampered"; must_fail(lambda:validate_packet(p))
def test_packet_hash_tamper_blocked():
    p=packet(); p["packet_sha256"]="0"*64; must_fail(lambda:validate_packet(p))
def test_missing_reviewed_hash_blocked():
    p=packet(); d=decisions(p); d["decisions"][0].pop("reviewed_text_sha256"); must_fail(lambda:apply_hash_bound_decisions(p,d))
def test_wrong_reviewed_hash_blocked():
    p=packet(); d=decisions(p); d["decisions"][0]["reviewed_text_sha256"]="f"*64; must_fail(lambda:apply_hash_bound_decisions(p,d))
def test_wrong_packet_hash_blocked():
    p=packet(); d=decisions(p); d["review_packet_sha256"]="f"*64; must_fail(lambda:apply_hash_bound_decisions(p,d))
def test_approval_requires_all_true():
    p=packet(); d=decisions(p); d["decisions"][0]["factual_support"]=False; must_fail(lambda:apply_hash_bound_decisions(p,d))
def test_valid_decision_stays_not_visible():
    p=packet(); r=apply_hash_bound_decisions(p,decisions(p)); assert r["student_ready"] is False and r["student_visible"] is False; assert r["results"][0]["student_visible"] is False
