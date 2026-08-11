from __future__ import annotations
import copy, hashlib, json

ALLOWED_STATUSES={"APPROVED_FOR_EVIDENCE_READY","MANUAL_REVIEW_REQUIRED","REJECTED"}
ALLOWED_REVIEWER_TYPES={"HUMAN","EXTERNAL_LLM"}

class ReviewIntegrityError(ValueError): pass

def sha256_text(text:str)->str:
    if not isinstance(text,str): raise ReviewIntegrityError("Evidence text must be a string.")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def packet_sha256(packet:dict)->str:
    clean=copy.deepcopy(packet); clean.pop("packet_sha256",None)
    raw=json.dumps(clean,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def validate_packet(packet:dict)->None:
    if not isinstance(packet,dict): raise ReviewIntegrityError("Reviewer packet must be an object.")
    expected=packet.get("packet_sha256")
    if not expected or expected!=packet_sha256(packet): raise ReviewIntegrityError("Reviewer packet SHA-256 mismatch.")
    records=packet.get("records")
    if not isinstance(records,list): raise ReviewIntegrityError("Reviewer packet records must be a list.")
    seen=set()
    for r in records:
        rid=r.get("record_id")
        if not rid or rid in seen: raise ReviewIntegrityError(f"Invalid/duplicate record_id: {rid}")
        seen.add(rid)
        actual=sha256_text(r.get("evidence_text"))
        if r.get("text_sha256")!=actual: raise ReviewIntegrityError(f"{rid}: source text SHA-256 mismatch.")
        if r.get("reviewed_text_sha256")!=actual: raise ReviewIntegrityError(f"{rid}: reviewed text SHA-256 mismatch.")

def apply_hash_bound_decisions(packet:dict, decisions_doc:dict)->dict:
    validate_packet(packet)
    ph=packet["packet_sha256"]
    if decisions_doc.get("review_packet_sha256")!=ph: raise ReviewIntegrityError("Decisions document is not bound to this reviewer packet.")
    decisions=decisions_doc.get("decisions")
    if not isinstance(decisions,list): raise ReviewIntegrityError("Decisions must be a list.")
    records={r["record_id"]:r for r in packet["records"]}
    if len(decisions)!=len(records): raise ReviewIntegrityError("Every packet record must have exactly one decision.")
    dmap={}
    for d in decisions:
        rid=d.get("record_id")
        if rid in dmap or rid not in records: raise ReviewIntegrityError(f"Invalid decision record_id: {rid}")
        dmap[rid]=d
    results=[]
    for rid,r in records.items():
        d=dmap[rid]
        if d.get("reviewed_text_sha256")!=r["reviewed_text_sha256"]: raise ReviewIntegrityError(f"{rid}: decision not bound to exact reviewed text.")
        if d.get("review_packet_sha256")!=ph: raise ReviewIntegrityError(f"{rid}: decision not bound to packet.")
        if d.get("status") not in ALLOWED_STATUSES: raise ReviewIntegrityError(f"{rid}: invalid status.")
        if d.get("reviewer_type") not in ALLOWED_REVIEWER_TYPES: raise ReviewIntegrityError(f"{rid}: invalid reviewer_type.")
        if not isinstance(d.get("reviewer_id"),str) or not d["reviewer_id"].strip(): raise ReviewIntegrityError(f"{rid}: reviewer_id required.")
        for f in ("factual_support","outcome_support","source_consistency"):
            if not isinstance(d.get(f),bool): raise ReviewIntegrityError(f"{rid}: {f} must be boolean.")
        if not isinstance(d.get("rationale"),str) or not d["rationale"].strip(): raise ReviewIntegrityError(f"{rid}: rationale required.")
        if d["status"]=="APPROVED_FOR_EVIDENCE_READY" and not all(d[f] for f in ("factual_support","outcome_support","source_consistency")):
            raise ReviewIntegrityError(f"{rid}: approval requires all support checks true.")
        results.append({**{k:d[k] for k in ("record_id","reviewed_text_sha256","review_packet_sha256","status","reviewer_type","reviewer_id","factual_support","outcome_support","source_consistency","rationale")},"outcome_id":r.get("outcome_id"),"student_ready":False,"student_visible":False})
    counts={s:sum(x["status"]==s for x in results) for s in ALLOWED_STATUSES}
    return {"schema_version":"2.0-hash-bound","review_packet_sha256":ph,"integrity_policy":"DECISION_BOUND_TO_EXACT_REVIEWED_TEXT_AND_PACKET","authenticated_signature":False,"student_ready":False,"student_visible":False,"counts":counts,"results":results}
