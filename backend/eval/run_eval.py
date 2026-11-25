import sys, os, json, requests

sys.path.insert(0, os.path.dirname(__file__))
from ground_truth import GROUND_TRUTH

BASE = "http://localhost:8000/api"
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "test_documents")
USERNAME = os.getenv("APP_USERNAME", "admin")
PASSWORD = os.getenv("APP_PASSWORD", "changeme123")

def get_token():
    resp = requests.post(f"{BASE}/auth/login", json={"username": USERNAME, "password": PASSWORD})
    resp.raise_for_status()
    return resp.json()["token"]

def run_case(name, case, headers):
    extractions = []
    canonical_metrics = []
    ocr_triggered = False

    for filename in case["files"]:
        path = os.path.join(UPLOADS_DIR, filename)
        if not os.path.exists(path):
            print(f"  [SKIP] {filename} not found at {path}")
            return None
        with open(path, "rb") as f:
            resp = requests.post(f"{BASE}/documents/extract",
                                  files={"file": (filename, f, "application/pdf")}, headers=headers)
        resp.raise_for_status()
        extraction = resp.json()
        extractions.append(extraction)
        ocr_triggered = ocr_triggered or extraction.get("ocr_used", False)

        resp = requests.post(f"{BASE}/documents/canonicalize", json=extraction, headers=headers)
        resp.raise_for_status()
        canonical_metrics.extend(resp.json())

    resp = requests.post(f"{BASE}/documents/consistency-check",
                          json={"metrics": canonical_metrics, "extractions": extractions}, headers=headers)
    resp.raise_for_status()
    consistency = resp.json()

    resp = requests.post(f"{BASE}/documents/risk-assessment",
                          json={"metrics": canonical_metrics, "extractions": extractions}, headers=headers)
    resp.raise_for_status()
    risk = resp.json()

    metrics_found = len(canonical_metrics)
    metrics_ok = metrics_found >= case["min_metrics_expected"]

    found_discrepancy_names = {d["canonical_name"] for d in consistency["discrepancies"]}
    expected_discrepancy_names = set(case["expected_discrepancy_metrics"])
    discrepancy_hits = expected_discrepancy_names & found_discrepancy_names
    discrepancy_recall = len(discrepancy_hits) / len(expected_discrepancy_names) if expected_discrepancy_names else None

    flagged_texts = [c["raw_text"] for c in consistency["unsupported_claims"]]
    expected_subs = case["expected_unsupported_substrings"]
    matched_expected = [s for s in expected_subs if any(s.lower() in t.lower() for t in flagged_texts)]
    claim_recall = len(matched_expected) / len(expected_subs) if expected_subs else None

    result = {
        "name": name,
        "metrics_found": metrics_found,
        "metrics_ok": metrics_ok,
        "discrepancy_recall": discrepancy_recall,
        "discrepancies_found": sorted(found_discrepancy_names),
        "discrepancies_expected": sorted(expected_discrepancy_names),
        "unsupported_claim_recall": claim_recall,
        "unsupported_claims_found_count": len(flagged_texts),
        "risk_flags_triggered": len(risk["flags"]),
        "ocr_triggered": ocr_triggered,
    }
    if case.get("expect_ocr"):
        result["ocr_expectation_met"] = ocr_triggered

    return result

def main():
    print("Logging in...")
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    results = []
    for name, case in GROUND_TRUTH.items():
        print(f"\nRunning case: {name}")
        result = run_case(name, case, headers)
        if result:
            results.append(result)
            print(json.dumps(result, indent=2))

    with open(os.path.join(os.path.dirname(__file__), "eval_report.json"), "w") as f:
        json.dump(results, f, indent=2)

    print("\n=== Summary ===")
    for r in results:
        print(f"{r['name']}: metrics={r['metrics_found']} (ok={r['metrics_ok']}), "
              f"discrepancy_recall={r['discrepancy_recall']}, "
              f"unsupported_claim_recall={r['unsupported_claim_recall']}, "
              f"risk_flags={r['risk_flags_triggered']}, ocr={r['ocr_triggered']}")

if __name__ == "__main__":
    main()