import asyncio
import json
import re
import logging
from sqlalchemy.orm import Session
from app.models.database import Dataset, EvalItem, SessionLocal
from app.services.prompts import SYSTEM_PROMPT, DIMENSION_PROMPTS, ERROR_CLASSIFICATION_SYSTEM, ERROR_CLASSIFICATION_PROMPT
from app.services.llm_client import get_score, LLMClientError

logger = logging.getLogger(__name__)

ALL_DIMS = ["faithfulness", "relevance", "coherence", "context_relevance", "groundedness"]
SCORE_FIELDS = {
    "faithfulness": "auto_faithfulness",
    "relevance": "auto_relevance",
    "coherence": "auto_coherence",
    "context_relevance": "auto_context_relevance",
    "groundedness": "auto_groundedness",
}


async def classify_error(item):
    if not item.context:
        return None
    scores = [item.auto_faithfulness, item.auto_relevance, item.auto_coherence]
    scores = [s for s in scores if s is not None]
    if not scores or min(scores) > 3:
        return None
    try:
        prompt = ERROR_CLASSIFICATION_PROMPT.format(question=item.question, context=item.context or "(none)", llm_answer=item.llm_answer)
        result = await get_score(ERROR_CLASSIFICATION_SYSTEM, prompt)
        return None
    except Exception:
        pass
    return None


async def classify_error_for_item(item):
    if not item.context:
        return None
    scores = [item.auto_faithfulness, item.auto_relevance, item.auto_coherence]
    scores = [s for s in scores if s is not None]
    if not scores or min(scores) > 3:
        return None

    from app.services.llm_client import FALLBACK_CHAIN, _CALLERS, LLMClientError
    prompt = ERROR_CLASSIFICATION_PROMPT.format(question=item.question, context=item.context or "(none)", llm_answer=item.llm_answer)

    for p in FALLBACK_CHAIN:
        try:
            raw = await _CALLERS[p.provider](p, ERROR_CLASSIFICATION_SYSTEM, prompt)
            text = raw.strip()
            if "```" in text:
                text = re.sub(r"```\w*\n?", "", text).strip()
            match = re.search(r"\{[^{}]+\}", text)
            if match:
                obj = json.loads(match.group(0).replace("'", '"'))
                error_type = obj.get("error_type", "")
                if error_type in ("hallucination", "contradicts", "incomplete", "off_topic", "poor_reasoning", "no_error"):
                    return error_type
        except Exception:
            continue
    return None


async def evaluate_item(item, db):
    item.auto_eval_status = "running"
    db.commit()
    try:
        model_used = ""
        has_context = bool(item.context and item.context.strip())
        dims_to_score = ALL_DIMS if has_context else ["relevance", "coherence"]

        for dim in dims_to_score:
            template = DIMENSION_PROMPTS[dim]
            prompt = template.format(question=item.question, context=item.context or "(none)", llm_answer=item.llm_answer)
            result = await get_score(SYSTEM_PROMPT, prompt)
            setattr(item, SCORE_FIELDS[dim], result["score"])
            model_used = result.get("model", "")
            await asyncio.sleep(1)

        error_type = await classify_error_for_item(item)
        if error_type:
            item.auto_error_type = error_type
            await asyncio.sleep(1)

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
