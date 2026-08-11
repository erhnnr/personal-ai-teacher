from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent; APP=ROOT/"app"; sys.path.insert(0,str(APP))
from review_integrity import ReviewIntegrityError, apply_hash_bound_decisions
DIR=ROOT/"data/knowledge/factual_approval"
PACK=DIR/"biology_hash_bound_reviewer_packet.json"
DEC=DIR/"biology_hash_bound_review_decisions.json"
OUT=DIR/"biology_hash_bound_review_results.json"
def read(p): return json.loads(p.read_text(encoding="utf-8"))
def main():
    try: result=apply_hash_bound_decisions(read(PACK),read(DEC))
    except ReviewIntegrityError as e: print("HASH-BOUND REVIEW APPLY: FAIL"); print(e); raise SystemExit(1)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    c=result["counts"]
    print("KNOWLEDGE FACTORY V2 — PHASE 6M HASH-BOUND REVIEW RESULTS")
    print("Integrity validation : PASS")
    print(f"APPROVED              : {c.get('APPROVED_FOR_EVIDENCE_READY',0)}")
    print(f"MANUAL REVIEW         : {c.get('MANUAL_REVIEW_REQUIRED',0)}")
    print(f"REJECTED              : {c.get('REJECTED',0)}")
    print("Student ready         : False")
    print("Student visible       : False")
    print(f"OUTPUT | {OUT}")
if __name__=="__main__": main()
