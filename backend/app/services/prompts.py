SYSTEM_PROMPT = (
    "You are a strict, fair evaluation judge. "
    "You will be given a question, a reference context, and an LLM-generated answer. "
    "Your job is to score the answer on a specific dimension. "
    "Respond with ONLY a valid JSON object like {\"score\": 3, \"reason\": \"brief explanation\"}. "
    "Use double quotes for JSON keys and string values. No other text."
)

FAITHFULNESS_PROMPT = """Rate the FAITHFULNESS of this answer (1-5).
1=contradicts context, 2=mostly unsupported, 3=partially supported, 4=mostly faithful, 5=fully supported

Question: {question}
Context: {context}
LLM Answer: {llm_answer}

JSON only:"""

RELEVANCE_PROMPT = """Rate the RELEVANCE of this answer (1-5).
1=off-topic, 2=tangentially related, 3=partially addresses question, 4=mostly addresses it, 5=directly answers it

Question: {question}
Context: {context}
LLM Answer: {llm_answer}

JSON only:"""

COHERENCE_PROMPT = """Rate the COHERENCE of this answer (1-5).
1=incomprehensible, 2=hard to follow, 3=understandable but awkward, 4=well-written, 5=clear and logical

Question: {question}
Context: {context}
LLM Answer: {llm_answer}

JSON only:"""

DIMENSION_PROMPTS = {
    "faithfulness": FAITHFULNESS_PROMPT,
    "relevance": RELEVANCE_PROMPT,
    "coherence": COHERENCE_PROMPT,
}
