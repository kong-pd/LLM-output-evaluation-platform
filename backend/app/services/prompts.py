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

CONTEXT_RELEVANCE_PROMPT = """Rate the CONTEXT RELEVANCE (1-5). This evaluates the RETRIEVER, not the answer.
Is the provided context actually relevant to answering this question?
1=completely irrelevant context, 2=barely related, 3=somewhat relevant, 4=mostly relevant, 5=perfectly relevant

Question: {question}
Context: {context}
LLM Answer: {llm_answer}

JSON only:"""

GROUNDEDNESS_PROMPT = """Rate the GROUNDEDNESS of this answer (1-5).
Does the answer actually USE the provided context, or does it ignore it and make things up?
1=completely ignores context, 2=barely uses context, 3=partially grounded, 4=mostly grounded, 5=fully grounded in context

Question: {question}
Context: {context}
LLM Answer: {llm_answer}

JSON only:"""

DIMENSION_PROMPTS = {
    "faithfulness": FAITHFULNESS_PROMPT,
    "relevance": RELEVANCE_PROMPT,
    "coherence": COHERENCE_PROMPT,
    "context_relevance": CONTEXT_RELEVANCE_PROMPT,
    "groundedness": GROUNDEDNESS_PROMPT,
}

ERROR_CLASSIFICATION_SYSTEM = (
    "You are an error classifier for LLM outputs. "
    "Given a question, context, and a low-quality LLM answer, classify the PRIMARY error type. "
    "Respond with ONLY a valid JSON object. No other text."
)

ERROR_CLASSIFICATION_PROMPT = """Classify the PRIMARY error type of this LLM answer.

Error types:
- hallucination: answer contains facts not in the context (made things up)
- contradicts: answer directly contradicts the context
- incomplete: answer is partially correct but missing key information
- off_topic: answer does not address the question at all
- poor_reasoning: answer uses flawed logic or draws wrong conclusions
- no_error: answer is acceptable despite low auto-score

Question: {question}
Context: {context}
LLM Answer: {llm_answer}

Respond with ONLY: {{"error_type": "<type>", "reason": "<brief explanation>"}}"""
