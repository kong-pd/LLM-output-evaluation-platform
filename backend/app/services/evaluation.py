import logging
from sqlalchemy.orm import Session
from app.models.database import Dataset, EvalItem, SessionLocal
from app.services.prompts import SYSTEM_PROMPT, DIMENSION_PROMPTS
from app.services.llm_client import get_score, LLMClientError

logger = logging.getLogger(__name__)


async def evaluate_item(item: EvalItem, db: Session) -> None:
    item.auto_eval_status = "running"
    db.commit()

    try:
        scores = {}
        model_used = ""
        for dimension, prompt_template in DIMENSION_PROMPTS.items():
            user_prompt = prompt_template.format(
                question=item.question,
                context=item.context or "(no context provided)",
                llm_answer=item.llm_answer,
            )
            result = await get_score(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
            scores[dimension] = result["score"]
            model_used = result.get("model", "")

        item.auto_faithfulness = scores["faithfulness"]
        item.auto_relevance = scores["relevance"]
        item.auto_coherence = scores["coherence"]
        item.auto_eval_model = model_used
        item.auto_eval_status = "done"
    except LLMClientError as e:
        logger.error(f"Eval failed for item {item.id}: {e}")
        item.auto_eval_status = "error"
        item.auto_eval_error = str(e)
    except Exception as e:
        logger.error(f"Unexpected error for item {item.id}: {e}")
        item.auto_eval_status = "error"
        item.auto_eval_error = f"Unexpected error: {e}"

    db.commit()


async def evaluate_dataset(dataset_id: str) -> None:
    db = SessionLocal()
    try:
        dataset = db.get(Dataset, dataset_id)
        if not dataset:
            logger.error(f"Dataset {dataset_id} not found")
            return

        dataset.status = "evaluating"
        db.commit()

        items = (
            db.query(EvalItem)
            .filter(EvalItem.dataset_id == dataset_id, EvalItem.auto_eval_status == "pending")
            .order_by(EvalItem.row_index)
            .all()
        )

        done_count = 0
        for item in items:
            await evaluate_item(item, db)
            if item.auto_eval_status == "done":
                done_count += 1
            dataset.evaluated_items = done_count
            db.commit()

        dataset.status = "evaluated"
        db.commit()
        logger.info(f"Dataset {dataset_id}: evaluated {done_count}/{len(items)} items")
    except Exception as e:
        logger.error(f"Dataset evaluation failed: {e}")
        dataset = db.get(Dataset, dataset_id)
        if dataset:
            dataset.status = "error"
            db.commit()
    finally:
        db.close()
