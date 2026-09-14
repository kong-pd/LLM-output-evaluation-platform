SYSTEM_PROMPT = (
    "You are a strict, fair evaluation judge. "
    "You will be given a question, a reference context, and an LLM-generated answer. "
    "Your job is to score the answer on a specific dimension. "
    "Respond with ONLY a valid JSON object, no other text."
)

FAITHFULNESS_PROMPT = """Rate the FAITHFULNESS of this answer.

Faithfulness = Does the answer ONLY contain information that is supported by the context?

Scoring rubric:
1 — Contradicts the context, or fabricates facts not in the context
2 — Mostly unsupported claims, with major inaccuracies
3 — Partially supported, but some claims have no basis in the context
4 — Mostly faithful, only minor unsupported details
5 — Every claim in the answer is directly supported by the context

---
Question: {question}

Context: {context}

LLM Answer: {llm_answer}
---

Respond with ONLY: {{"score": <1-5>, "reason": "<brief explanation>"}}"""

RELEVANCE_PROMPT = """Rate the RELEVANCE of this answer.

Relevance = Does the answer directly address what the question is asking?

Scoring rubric:
1 — Completely off-topic, does not address the question at all
2 — Tangentially related, but misses the core question
3 — Partially addresses the question, but key parts are missing
4 — Addresses the question well, with minor gaps
5 — Directly and completely answers the question

---
Question: {question}

Context: {context}

LLM Answer: {llm_answer}
---

Respond with ONLY: {{"score": <1-5>, "reason": "<brief explanation>"}}"""

COHERENCE_PROMPT = """Rate the COHERENCE of this answer.

Coherence = Is the answer well-organized, logically structured, and easy to read?

Scoring rubric:
1 — Incomprehensible, garbled, or self-contradictory
2 — Hard to follow, poor structure, jumps between ideas
3 — Understandable but awkward, some logical gaps
4 — Well-written with minor organizational issues
5 — Clear, logical, well-structured, and easy to follow

---
Question: {question}

Context: {context}

LLM Answer: {llm_answer}
---

Respond with ONLY: {{"score": <1-5>, "reason": "<brief explanation>"}}"""

DIMENSION_PROMPTS = {
    "faithfulness": FAITHFULNESS_PROMPT,
    "relevance": RELEVANCE_PROMPT,
    "coherence": COHERENCE_PROMPT,
}
