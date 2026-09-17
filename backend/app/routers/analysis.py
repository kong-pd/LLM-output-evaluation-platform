import csv
import io
from collections import Counter
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.models.database import get_db, Dataset, EvalItem, Annotation

router = APIRouter(prefix="/api/datasets", tags=["analysis"])

ALL_DIMS = ["faithfulness", "relevance", "coherence", "context_relevance", "groundedness"]


def _cohens_kappa(pairs):
    if len(pairs) < 2:
        return None
    labels = [1, 2, 3, 4, 5]
    n = len(pairs)
    observed = sum(1 for a, h in pairs if a == h) / n
    ac = Counter(a for a, _ in pairs)
    hc = Counter(h for _, h in pairs)
    expected = sum((ac.get(k, 0) / n) * (hc.get(k, 0) / n) for k in labels)
    if expected == 1.0:
        return 1.0
    return round((observed - expected) / (1 - expected), 3)


def _confusion_matrix(pairs):
    matrix = {}
    for auto, human in pairs:
        a, h = int(auto), int(human)
        matrix.setdefault(a, {})
        matrix[a][h] = matrix[a].get(h, 0) + 1
    return [{"auto_score": s, **{f"human_{h}": matrix.get(s, {}).get(h, 0) for h in range(1, 6)}} for s in range(1, 6)]


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
    for dim in ALL_DIMS:
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
        "total_annotations": total, "agree_count": agree_count, "override_count": total - agree_count,
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
        return {"items": []}

    results = []
    for item in items:
        scores = [s for s in [item.auto_faithfulness, item.auto_relevance, item.auto_coherence, item.auto_context_relevance, item.auto_groundedness] if s is not None]
        if not scores:
            continue
        avg = round(sum(scores) / len(scores), 2)
        all_dims = [("faithfulness", item.auto_faithfulness), ("relevance", item.auto_relevance), ("coherence", item.auto_coherence), ("context_relevance", item.auto_context_relevance), ("groundedness", item.auto_groundedness)]
        valid = [(n, s) for n, s in all_dims if s is not None]
        weakest = min(valid, key=lambda x: x[1]) if valid else ("", 0)
        results.append({
            "row": item.row_index + 1, "question": item.question, "avg_score": avg,
            "weakest_dimension": weakest[0],
            "difficulty": "hard" if avg <= 2.5 else "medium" if avg <= 3.5 else "easy",
            "error_type": item.auto_error_type,
        })
    results.sort(key=lambda x: x["avg_score"])
    return {"items": results}


@router.get("/{dataset_id}/rca")
def get_rca(dataset_id: str, db: Session = Depends(get_db)):
    ds = db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found.")
    items = db.query(EvalItem).filter(EvalItem.dataset_id == dataset_id, EvalItem.auto_eval_status == "done").all()

    error_counts = Counter(i.auto_error_type for i in items if i.auto_error_type)
    total_errors = sum(error_counts.values())
    total_items = len(items)

    pipeline_diagnosis = []
    scores = {"faithfulness": [], "relevance": [], "coherence": [], "context_relevance": [], "groundedness": []}
    for item in items:
        if item.auto_faithfulness is not None: scores["faithfulness"].append(item.auto_faithfulness)
        if item.auto_relevance is not None: scores["relevance"].append(item.auto_relevance)
        if item.auto_coherence is not None: scores["coherence"].append(item.auto_coherence)
        if item.auto_context_relevance is not None: scores["context_relevance"].append(item.auto_context_relevance)
        if item.auto_groundedness is not None: scores["groundedness"].append(item.auto_groundedness)

    avgs = {k: round(sum(v) / len(v), 2) if v else None for k, v in scores.items()}

    if avgs.get("context_relevance") and avgs["context_relevance"] < 3.5:
        pipeline_diagnosis.append({"component": "retriever", "issue": "Retrieved context is often irrelevant to the question", "avg_score": avgs["context_relevance"], "action": "Improve retrieval strategy, embeddings, or chunk size"})
    if avgs.get("groundedness") and avgs["groundedness"] < 3.5:
        pipeline_diagnosis.append({"component": "generator", "issue": "LLM ignores context and generates from its own knowledge", "avg_score": avgs["groundedness"], "action": "Strengthen grounding instructions in the prompt"})
    if avgs.get("faithfulness") and avgs["faithfulness"] < 3.5:
        pipeline_diagnosis.append({"component": "generator", "issue": "LLM produces claims that contradict or go beyond the context", "avg_score": avgs["faithfulness"], "action": "Add 'only use provided context' constraints to prompt"})
    if avgs.get("relevance") and avgs["relevance"] < 3.5:
        pipeline_diagnosis.append({"component": "generator", "issue": "Answers don't address the actual question", "avg_score": avgs["relevance"], "action": "Check if question is being passed correctly to the LLM"})

    return {
        "total_items": total_items,
        "items_with_errors": total_errors,
        "error_rate": round(total_errors / total_items, 3) if total_items else 0,
        "error_breakdown": [{"type": t, "count": c, "pct": round(c / total_items, 3)} for t, c in error_counts.most_common()],
        "avg_scores": avgs,
        "pipeline_diagnosis": pipeline_diagnosis,
    }


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
        "auto_faithfulness", "auto_relevance", "auto_coherence", "auto_context_relevance", "auto_groundedness",
        "error_type", "auto_model", "auto_status",
        "human_faithfulness", "human_relevance", "human_coherence",
    ])
    for item in items:
        hs = {a.dimension: a.human_score for a in item.annotations}
        writer.writerow([
            item.row_index + 1, item.question, item.context, item.llm_answer,
            item.auto_faithfulness, item.auto_relevance, item.auto_coherence,
            item.auto_context_relevance, item.auto_groundedness,
            item.auto_error_type or "", item.auto_eval_model or "", item.auto_eval_status,
            hs.get("faithfulness", ""), hs.get("relevance", ""), hs.get("coherence", ""),
        ])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{ds.name}_report.csv"'})
