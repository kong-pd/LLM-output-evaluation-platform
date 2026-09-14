import csv
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.models.database import get_db, Dataset, EvalItem, Annotation

router = APIRouter(prefix="/api/datasets", tags=["analysis"])


@router.get("/{dataset_id}/agreement")
def get_agreement(dataset_id: str, db: Session = Depends(get_db)):
    ds = db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found.")

    annotations = (
        db.query(Annotation)
        .join(EvalItem)
        .filter(EvalItem.dataset_id == dataset_id)
        .all()
    )

    if not annotations:
        return {"total_annotations": 0, "overall_agreement": None, "per_dimension": {}, "message": "No annotations yet."}

    total = len(annotations)
    exact_match = sum(1 for a in annotations if a.human_score == a.auto_score)
    close_match = sum(1 for a in annotations if abs(a.human_score - a.auto_score) <= 1)
    agree_count = sum(1 for a in annotations if a.action == "agree")

    per_dim = {}
    for dim in ["faithfulness", "relevance", "coherence"]:
        dim_anns = [a for a in annotations if a.dimension == dim]
        if not dim_anns:
            continue
        per_dim[dim] = {
            "count": len(dim_anns),
            "exact_match_rate": round(sum(1 for a in dim_anns if a.human_score == a.auto_score) / len(dim_anns), 3),
            "close_match_rate": round(sum(1 for a in dim_anns if abs(a.human_score - a.auto_score) <= 1) / len(dim_anns), 3),
            "avg_auto": round(sum(a.auto_score for a in dim_anns) / len(dim_anns), 2),
            "avg_human": round(sum(a.human_score for a in dim_anns) / len(dim_anns), 2),
        }

    return {
        "total_annotations": total,
        "agree_count": agree_count,
        "override_count": total - agree_count,
        "exact_match_rate": round(exact_match / total, 3),
        "close_match_rate": round(close_match / total, 3),
        "per_dimension": per_dim,
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
        "auto_faithfulness", "auto_relevance", "auto_coherence", "auto_model", "auto_status",
        "human_faithfulness", "human_relevance", "human_coherence",
    ])

    for item in items:
        human_scores = {}
        for ann in item.annotations:
            human_scores[ann.dimension] = ann.human_score

        writer.writerow([
            item.row_index + 1,
            item.question,
            item.context,
            item.llm_answer,
            item.auto_faithfulness,
            item.auto_relevance,
            item.auto_coherence,
            item.auto_eval_model or "",
            item.auto_eval_status,
            human_scores.get("faithfulness", ""),
            human_scores.get("relevance", ""),
            human_scores.get("coherence", ""),
        ])

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{ds.name}_report.csv"'},
    )
