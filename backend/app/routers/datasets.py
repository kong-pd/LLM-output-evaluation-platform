from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from app.models.database import get_db, Dataset, EvalItem
from app.models.schemas import DatasetOut, EvalItemOut, EvalItemListOut
from app.services.ingestion import ingest_csv, IngestionError
from app.services.evaluation import evaluate_dataset

router = APIRouter(prefix="/api/datasets", tags=["datasets"])
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/upload", response_model=DatasetOut)
async def upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only .csv files are accepted.")
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(400, f"File too large (max {MAX_FILE_SIZE // 1024 // 1024} MB).")
    try:
        result = ingest_csv(contents, file.filename, db)
    except IngestionError as e:
        raise HTTPException(422, str(e))
    background_tasks.add_task(evaluate_dataset, result.dataset.id)
    return result.dataset


@router.get("", response_model=list[DatasetOut])
def list_datasets(db: Session = Depends(get_db)):
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    ds = db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found.")
    return ds


@router.get("/{dataset_id}/items", response_model=EvalItemListOut)
def list_items(
    dataset_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    ds = db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found.")
    query = db.query(EvalItem).filter(EvalItem.dataset_id == dataset_id).order_by(EvalItem.row_index)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return EvalItemListOut(items=items, total=total, page=page, page_size=page_size)


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    ds = db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found.")
    db.delete(ds)
    db.commit()
    return {"detail": "Deleted."}
