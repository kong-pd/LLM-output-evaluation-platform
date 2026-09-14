import logging
from sqlalchemy.orm import Session
from app.models.database import Dataset, EvalItem, SessionLocal
from app.services.prompts import SYSTEM_PROMPT, DIMENSION_PROMPTS
from app.services.llm_client import get_score, LLMClientError

logger = logging.getLogger(__name__)


async def evaluate_item(item, db):
    item.auto_eval_status = "running"
    db.commit()
    try:
        scores = {}
        model_used = ""
        for dim, template in DIMENSION_PROMPTS.items():
            prompt = template.format(question=item.question, context=item.context or "(none)", llm_answer=item.llm_answer)
            result = await get_score(SYSTEM_PROMPT, prompt)
            scores[dim] = result["score"]
            model_used = result.get("model", "")
        item.auto_faithfulness = scores["faithfulness"]
        item.auto_relevance = scores["relevance"]
        item.auto_coherence = scores["coherence"]
        item.auto_eval_model = model_used
        item.auto_eval_status = "done"
    except Exception as e:
        logger.error(f"Eval failed for item {item.id}: {e}")
        item.auto_eval_status = "error"
        item.auto_eval_error = str(e)
    db.commit()


async def evaluate_dataset(dataset_id):
    db = SessionLocal()
    try:
        dataset = db.get(Dataset, dataset_id)
        if not dataset:
            return
        dataset.status = "evaluating"
        db.commit()

        items = db.query(EvalItem).filter(EvalItem.dataset_id == dataset_id, EvalItem.auto_eval_status == "pending").order_by(EvalItem.row_index).all()
        done = 0
        for item in items:
            await evaluate_item(item, db)
            if item.auto_eval_status == "done":
                done += 1
            dataset.evaluated_items = done
            db.commit()

        dataset.status = "evaluated"
        db.commit()
    except Exception as e:
        logger.error(f"Dataset eval failed: {e}")
        ds = db.get(Dataset, dataset_id)
        if ds:
            ds.status = "error"
            db.commit()
    finally:
        db.close()
