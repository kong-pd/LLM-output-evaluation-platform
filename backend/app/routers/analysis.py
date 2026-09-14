import csv
import io
from collections import Counter
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.models.database import get_db, Dataset, EvalItem, Annotation

router = APIRouter(prefix="/api/datasets", tags=["analysis"])


def _cohens_kappa(pairs):
    if len(pairs) < 2:
        return None
    labels = [1, 2, 3, 4, 5]
    n = len(pairs)
    observed_agree = sum(1 for a, h in pairs if a == h) / n
    auto_counts = Counter(a for a, _ in pairs)
    human_counts = Counter(h for _, h in pairs)
    expected_agree = sum((auto_counts.get(k, 0) / n) * (human_counts.get(k, 0) / n) for k in labels)
    if expected_agree == 1.0:
        return 1.0
    return round((observed_agree - expected_agree) / (1 - expected_agree), 3)


def _confusion_matrix(pairs):
    matrix = {}
    for auto, human in pairs:
        a, h = int(auto), int(human)
        matrix.setdefault(a, {})
        matrix[a][h] = matrix[a].get(h, 0) + 1
    rows = []
    for auto_score in range(1, 6):
        row = {"auto_score": auto_score}
        for human_score in range(1, 6):
            row[f"human_{human_score}"] = matrix.get(auto_score, {}).get(human_score, 0)
        rows.append(row)
    return rows


@router.get("/{dataset_id}/agreement")
def get_agreement(dataset_id: str, db: Session = Depends(get_db)):
    ds = db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found.")

    annotations = db.query(Annotation).join(EvalItem).filter(EvalItem.dataset_id == dataset_id).all()
    if not annotations:
        return {"total_annotations": 0, "message": "No annotations yet."}

    total = len(annotations)
    agree_count = sum(1 for a in annotations if a.action == "agree")
    pairs_all = [(a.auto_score, a.human_score) for a in annotations]

    per_dim = {}
    for dim in ["faithfulness", "relevance", "coherence"]:
        dim_anns = [a for a in annotations if a.dimension == dim]
        if not dim_anns:
            continue
        pairs = [(a.auto_score, a.human_score) for a in dim_anns]
        per_dim[dim] = {
            "count": len(dim_anns),
            "exact_match_rate": round(sum(1 for a, h in pairs if a == h) / len(pairs), 3),
            "close_match_rate": round(sum(1 for a, h in pairs if abs(a - h) <= 1) / len(pairs), 3),
            "avg_auto": round(sum(a for a, _ in pairs) / len(pairs), 2),
            "avg_human": round(sum(h for _, h in pairs) / len(pairs), 2),
            "cohens_kappa": _cohens_kappa(pairs),
        }

    return {
        "total_annotations": total,
        "agree_count": agree_count,
        "override_count": total - agree_count,
        "exact_match_rate": round(sum(1 for a, h in pairs_all if a == h) / total, 3),
        "close_match_rate": round(sum(1 for a, h in pairs_all if abs(a - h) <= 1) / total, 3),
        "cohens_kappa": _cohens_kappa(pairs_all),
        "confusion_matrix": _confusion_matrix(pairs_all),
        "per_dimension": per_dim,
    }


@router.get("/{dataset_id}/difficulty")
def get_difficulty(dataset_id: str, db: Session = Depends(get_db)):
    ds = db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found.")

    items = db.query(EvalItem).filter(EvalItem.dataset_id == dataset_id, EvalItem.auto_eval_status == "done").order_by(EvalItem.row_index).all()
    if not items:
        return {"items": [], "message": "No evaluated items yet."}

    results = []
    for item in items:
        scores = [s for s in [item.auto_faithfulness, item.auto_relevance, item.auto_coherence] if s is not None]
        if not scores:
            continue
        avg = round(sum(scores) / len(scores), 2)
        lowest_dim = min(
            [("faithfulness", item.auto_faithfulness or 99), ("relevance", item.auto_relevance or 99), ("coherence", item.auto_coherence or 99)],
            key=lambda x: x[1],
        )
        results.append({
            "row": item.row_index + 1,
            "question": item.question,
            "avg_score": avg,
            "faithfulness": item.auto_faithfulness,
            "relevance": item.auto_relevance,
            "coherence": item.auto_coherence,
            "weakest_dimension": lowest_dim[0],
            "difficulty": "hard" if avg <= 2.5 else "medium" if avg <= 3.5 else "easy",
        })

    results.sort(key=lambda x: x["avg_score"])
    return {"items": results}


@router.get("/{dataset_id}/export")
def export_report(dataset_id: str, db: Session = Depends(get_db)):
    ds = db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found.")

    items = db.query(EvalItem).filter(EvalItem.dataset_id == dataset_id).order_by(EvalItem.row_index).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "row", "question", "context", "llm_answer",
        "auto_faithfulness", "auto_relevance", "auto_coherence", "auto_model", "auto_status",
        "human_faithfulness", "human_relevance", "human_coherence", "avg_score", "difficulty",
    ])

    for item in items:
        human_scores = {ann.dimension: ann.human_score for ann in item.annotations}
        scores = [s for s in [item.auto_faithfulness, item.auto_relevance, item.auto_coherence] if s is not None]
        avg = round(sum(scores) / len(scores), 2) if scores else ""
        diff = ("hard" if avg and avg <= 2.5 else "medium" if avg and avg <= 3.5 else "easy") if avg else ""

        writer.writerow([
            item.row_index + 1, item.question, item.context, item.llm_answer,
            item.auto_faithfulness, item.auto_relevance, item.auto_coherence,
            item.auto_eval_model or "", item.auto_eval_status,
            human_scores.get("faithfulness", ""), human_scores.get("relevance", ""), human_scores.get("coherence", ""),
            avg, diff,
        ])

    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{ds.name}_report.csv"'})
