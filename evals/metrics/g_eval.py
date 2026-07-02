"""G-Eval — LLM-as-judge scoring for subjective response quality."""

import json

# pyrefly: ignore [missing-import]
from groq import Groq

MODEL = "llama-3.3-70b-versatile"

_SYSTEM = """You are an evaluator assessing an AI assistant's response for an issue tracking system.

You will be given:
- A user prompt
- The assistant's response
- Evaluation criteria

Think step by step about whether the response meets the criteria.
Then provide a score from 1 to 5:
  1 = completely fails the criteria
  2 = mostly fails
  3 = partially meets
  4 = mostly meets
  5 = fully meets

Respond with JSON only:
{"score": <1-5>, "reasoning": "<one or two sentences>"}"""


def g_eval(prompt: str, response: str, criteria: str, groq_client: Groq) -> tuple[int, str]:
    """Returns (score 1-5, reasoning)."""
    content = f"""User prompt: {prompt}

Assistant response: {response}

Criteria: {criteria}"""

    try:
        resp = groq_client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": content},
            ],
            max_tokens=150,
            temperature=0,
        )
        raw = (resp.choices[0].message.content or "").strip()
        data = json.loads(raw)
        return int(data.get("score", 1)), str(data.get("reasoning", ""))
    except Exception as e:
        print(f"[G-Eval] error: {e}")
        return 0, f"eval error: {e}"
