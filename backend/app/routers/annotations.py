from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db, EvalItem, Annotation, Dataset
from app.models.schemas import AnnotationCreate, AnnotationOut

router = APIRouter(prefix="/api/items", tags=["annotations"])
VALID_DIMENSIONS = {"faithfulness", "relevance", "coherence"}
VALID_ACTIONS = {"agree", "disagree", "override"}


@router.post("/{item_id}/annotations", response_model=AnnotationOut)
def create_annotation(item_id: str, body: AnnotationCreate, db: Session = Depends(get_db)):
    item = db.get(EvalItem, item_id)
    if not item:
        raise HTTPException(404, "Eval item not found.")
    if body.dimension not in VALID_DIMENSIONS:
        raise HTTPException(400, f"Dimension must be one of: {VALID_DIMENSIONS}")
    if body.action not in VALID_ACTIONS:
        raise HTTPException(400, f"Action must be one of: {VALID_ACTIONS}")
    if not (1 <= body.human_score <= 5):
        raise HTTPException(400, "Score must be between 1 and 5.")

    auto_score = {"faithfulness": item.auto_faithfulness, "relevance": item.auto_relevance, "coherence": item.auto_coherence}[body.dimension]
    if auto_score is None:
        raise HTTPException(400, "Item has not been auto-evaluated yet.")

    annotation = Annotation(
        eval_item_id=item_id, dimension=body.dimension,
        auto_score=auto_score, human_score=body.human_score,
        action=body.action, note=body.note,
    )
    db.add(annotation)

    dataset = db.get(Dataset, item.dataset_id)
    if dataset:
        dataset.annotated_items = (
            db.query(EvalItem.id)
            .filter(EvalItem.dataset_id == dataset.id, EvalItem.annotations.any())
            .distinct().count()
        )

    db.commit()
    db.refresh(annotation)
    return annotation


@router.get("/{item_id}/annotations", response_model=list[AnnotationOut])
def list_annotations(item_id: str, db: Session = Depends(get_db)):
    item = db.get(EvalItem, item_id)
    if not item:
        raise HTTPException(404, "Eval item not found.")
    return item.annotations
