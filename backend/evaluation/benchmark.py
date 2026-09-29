import json
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.rag_service import rag_service
from app.services.auditor_service import run_baseline_compliance_audit
from app.schemas import StructuredProductData, NutritionFacts

def calculate_cer(reference: str, hypothesis: str) -> float:
    """Character Error Rate (CER) using Levenshtein distance"""
    r = list(reference)
    h = list(hypothesis)
    d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1): d[i][0] = i
    for j in range(len(h) + 1): d[0][j] = j
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            if r[i - 1] == h[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + 1)
    return d[len(r)][len(h)] / max(len(r), 1)

def run_benchmark():
    dataset_path = Path(__file__).parent / "benchmark_dataset.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("\n=======================================================")
    print("   FOODSAFE-INDIC: NLP & RAG ACADEMIC BENCHMARK SUITE  ")
    print("=======================================================\n")

    # 1. OCR Evaluation (CER & Accuracy)
    print(">>> 1. Evaluating Multilingual OCR Subsystem...")
    cer_scores = []
    for s in data["ocr_samples"]:
        cer = calculate_cer(s["ground_truth"], s["ocr_prediction"])
        cer_scores.append(cer)
    avg_cer = sum(cer_scores) / len(cer_scores) if cer_scores else 0.0
    ocr_char_acc = (1.0 - avg_cer) * 100
    print(f"    - Samples Evaluated: {len(cer_scores)}")
    print(f"    - Average Character Error Rate (CER): {avg_cer:.4f}")
    print(f"    - OCR Character Recognition Accuracy: {ocr_char_acc:.2f}%\n")

    # 2. RAG Retrieval Evaluation
    print(">>> 2. Evaluating Legal ChromaDB RAG Subsystem...")
    rag_queries = data["rag_retrieval_queries"]
    hits_at_1 = 0
    hits_at_3 = 0
    reciprocal_ranks = []

    for item in rag_queries:
        q = item["query"]
        expected = item["expected_clause_ids"]
        retrieved = rag_service.retrieve_relevant_clauses(q, top_k=3)
        retrieved_ids = [r["id"] for r in retrieved]

        # Hit@1
        if retrieved_ids and retrieved_ids[0] in expected:
            hits_at_1 += 1
            reciprocal_ranks.append(1.0)
        # Hit@3
        elif any(eid in retrieved_ids for eid in expected):
            hits_at_3 += 1
            # Find rank
            rank = min([retrieved_ids.index(eid) + 1 for eid in expected if eid in retrieved_ids])
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)

    total_q = len(rag_queries)
    hit_rate_1 = (hits_at_1 / total_q) * 100
    hit_rate_3 = ((hits_at_1 + hits_at_3) / total_q) * 100
    mrr = sum(reciprocal_ranks) / total_q if total_q > 0 else 0.0

    print(f"    - Statutory Queries Tested: {total_q}")
    print(f"    - Hit Rate @ 1 (Top-1 Accuracy): {hit_rate_1:.2f}%")
    print(f"    - Hit Rate @ 3 (Top-3 Recall): {hit_rate_3:.2f}%")
    print(f"    - Mean Reciprocal Rank (MRR): {mrr:.4f}\n")

    # 3. Violation Detection Accuracy & F1
    print(">>> 3. Evaluating Automated Violation Detection Subsystem...")
    cases = data["compliance_test_cases"]
    tp = fp = tn = fn = 0

    for c in cases:
        nutr_dict = c.get("nutrition", {})
        nutr = NutritionFacts(
            saturated_fat_g=nutr_dict.get("saturated_fat_g"),
            trans_fat_g=nutr_dict.get("trans_fat_g"),
            total_sugars_g=nutr_dict.get("total_sugars_g")
        )
        prod = StructuredProductData(
            product_name=c["product_name"],
            claims=c.get("claims", []),
            ingredients=c.get("ingredients", []),
            nutrition=nutr,
            veg_nonveg=c.get("veg_nonveg", "UNKNOWN"),
            fssai_license=c.get("fssai_license"),
            mfg_date=c.get("mfg_date"),
            allergen_advice=c.get("allergen_advice")
        )
        audit = run_baseline_compliance_audit(prod)
        pred_label = "NON_COMPLIANT" if audit.overall_status in ["NON_COMPLIANT", "SUSPECTED_VIOLATION"] else "COMPLIANT"
        actual_label = c["ground_truth_label"]

        if actual_label == "NON_COMPLIANT" and pred_label == "NON_COMPLIANT":
            tp += 1
        elif actual_label == "COMPLIANT" and pred_label == "NON_COMPLIANT":
            fp += 1
        elif actual_label == "COMPLIANT" and pred_label == "COMPLIANT":
            tn += 1
        elif actual_label == "NON_COMPLIANT" and pred_label == "COMPLIANT":
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / len(cases) if len(cases) > 0 else 0.0

    print(f"    - Test Cases: {len(cases)} (TP: {tp}, FP: {fp}, TN: {tn}, FN: {fn})")
    print(f"    - Classification Accuracy: {accuracy * 100:.2f}%")
    print(f"    - Precision: {precision:.4f}")
    print(f"    - Recall: {recall:.4f}")
    print(f"    - F1-Score: {f1:.4f}\n")

    # Output Summary Table
    print("=======================================================")
    print("                 BENCHMARK SUMMARY TABLE               ")
    print("=======================================================")
    print(f"| Evaluation Metric               | Result            |")
    print(f"|---------------------------------|-------------------|")
    print(f"| OCR Character Accuracy          | {ocr_char_acc:.2f}%           |")
    print(f"| Legal RAG Hit Rate @ 1          | {hit_rate_1:.2f}%          |")
    print(f"| Legal RAG Hit Rate @ 3          | {hit_rate_3:.2f}%          |")
    print(f"| Legal RAG Mean Reciprocal Rank  | {mrr:.4f}            |")
    print(f"| Violation Detection Precision   | {precision:.4f}            |")
    print(f"| Violation Detection Recall      | {recall:.4f}            |")
    print(f"| Violation Detection F1-Score    | {f1:.4f}            |")
    print("=======================================================\n")

    # Save to JSON
    report = {
        "ocr_metrics": {
            "avg_cer": avg_cer,
            "character_accuracy_pct": ocr_char_acc
        },
        "rag_retrieval_metrics": {
            "hit_rate_at_1_pct": hit_rate_1,
            "hit_rate_at_3_pct": hit_rate_3,
            "mrr": mrr
        },
        "compliance_detection_metrics": {
            "accuracy_pct": accuracy * 100,
            "precision": precision,
            "recall": recall,
            "f1_score": f1
        }
    }
    report_file = Path(__file__).parent / "evaluation_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Benchmark results saved to {report_file}")

if __name__ == "__main__":
    run_benchmark()
