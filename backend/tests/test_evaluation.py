import os
import json
import asyncio

from app.models.database import init_db
from app.services.llm_client import _parse_score, LLMClientError

init_db()


def test_parse_clean_json():
    result = _parse_score('{"score": 4, "reason": "Mostly faithful"}')
    assert result["score"] == 4.0
    assert result["reason"] == "Mostly faithful"


def test_parse_json_in_code_block():
    result = _parse_score('```json\n{"score": 3, "reason": "Partially relevant"}\n```')
    assert result["score"] == 3.0


def test_parse_rejects_out_of_range():
    try:
        _parse_score('{"score": 7, "reason": "Great"}')
        assert False, "Should have raised"
    except ValueError:
        pass


def test_parse_rejects_garbage():
    try:
        _parse_score("I think the score is about 4")
        assert False, "Should have raised"
    except json.JSONDecodeError:
        pass


def test_no_api_keys_raises_clear_error():
    from app.services import llm_client
    original_chain = llm_client.FALLBACK_CHAIN
    llm_client.FALLBACK_CHAIN = []
    try:
        asyncio.get_event_loop().run_until_complete(llm_client.get_score("system", "user"))
        assert False, "Should have raised"
    except LLMClientError as e:
        assert "No API keys configured" in str(e)
    finally:
        llm_client.FALLBACK_CHAIN = original_chain


def test_integration_real_scoring():
    has_key = any([os.getenv("GEMINI_API_KEY"), os.getenv("GROK_API_KEY"), os.getenv("ANTHROPIC_API_KEY")])
    if not has_key:
        import pytest
        pytest.skip("No API keys set")

    from app.services import llm_client
    llm_client.FALLBACK_CHAIN = llm_client._build_chain()
    from app.services.prompts import SYSTEM_PROMPT, FAITHFULNESS_PROMPT

    prompt = FAITHFULNESS_PROMPT.format(
        question="What are your business hours?",
        context="Our office is open Monday to Friday, 9 AM to 6 PM EST.",
        llm_answer="We are open 24/7 and you can always reach us by phone anytime.",
    )
    result = asyncio.get_event_loop().run_until_complete(llm_client.get_score(SYSTEM_PROMPT, prompt))
    print(f"\n  Model: {result['model']} | Score: {result['score']} | Reason: {result['reason']}")
    assert 1.0 <= result["score"] <= 5.0
    assert result["model"]
