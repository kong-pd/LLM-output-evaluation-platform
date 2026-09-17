from datetime import datetime
from pydantic import BaseModel


class DatasetOut(BaseModel):
    id: str
    name: str
    description: str
    total_items: int
    evaluated_items: int
    annotated_items: int
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class EvalItemOut(BaseModel):
    id: str
    dataset_id: str
    row_index: int
    question: str
    context: str
    llm_answer: str
    auto_faithfulness: float | None
    auto_relevance: float | None
    auto_coherence: float | None
    auto_context_relevance: float | None
    auto_groundedness: float | None
    auto_error_type: str | None
    auto_eval_status: str
    auto_eval_model: str | None
    auto_eval_error: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class EvalItemListOut(BaseModel):
    items: list[EvalItemOut]
    total: int
    page: int
    page_size: int


class AnnotationCreate(BaseModel):
    dimension: str
    human_score: float
    action: str
    note: str = ""


class AnnotationOut(BaseModel):
    id: str
    eval_item_id: str
    dimension: str
    auto_score: float
    human_score: float
    action: str
    note: str
    created_at: datetime
    model_config = {"from_attributes": True}
