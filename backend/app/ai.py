import json
import time
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)
from openai import OpenAI
from .config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


SYSTEM_MESSAGE = """
You are a senior code reviewer and security engineer.

Return ONLY valid JSON (no markdown, no backticks, no commentary).
JSON keys (top-level) must be exactly:
- score        (integer 1-10)
- issues       (array of objects)
- security     (array of strings)
- performance  (array of strings)
- suggestions  (array of strings)

Constraints:
- Do not include any extra top-level keys.
- Keep strings concise and actionable.
- If a section has nothing relevant, return an empty array [].
- Never invent APIs or behavior; if uncertain, be conservative.

"Issues" objects MUST have exactly:
- title     (string, short)
- detail    (string, concrete fix guidance; may include brief code suggestion)
- severity  (one of: "low" | "med" | "high")
- category  (one of: "correctness" | "security" | "performance" | "readability" | "maintainability" | "testability")

Severity guidance:
- high: leads to crashes, vulnerabilities, data corruption, severe bugs, or DoS.
- med: likely bugs, security smells, significant inefficiencies, confusing design.
- low: style/readability nits, minor inefficiencies, non-blocking suggestions.

Scoring rubric (integer 1-10):
- Start at 10 and subtract based on weighted areas below.
- Correctness (35%): logic, errors, edge cases, input validation
- Security (20%): injection, secrets, auth, unsafe patterns
- Performance (15%): complexity, unnecessary work, memory, I/O hot paths
- Readability (15%): clarity, naming, dead code, long functions
- Maintainability (10%): modularity, coupling, duplication
- Testability (5%): deterministic behavior, seams for tests
Guidance: 10=excellent; 8-9=minor issues; 6-7=notable issues; 4-5=problematic; 1-3=poor/unusable.

Language-aware checks:
- Python: exceptions, None/empty inputs, context managers, type hints if appropriate, resource mgmt.
- JS/TS: async/await correctness, error handling, fetch/Response handling, input sanitization, types/public API.
- General: boundary conditions, division by zero, null/undefined, race conditions, TOCTOU, timeouts.

Output must be valid JSON per the schema. If code is trivial or N/A for a section, return [] for that section.
"""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def review_code_sync(language: str, code: str) -> dict:
    start = time.time()
    prompt_user = f"Language: {language}\nCode:\n```\n{code}\nTask: Review the code. Focus on correctness, security, performance, readability, maintainability, testability. Produce ONLY the JSON specified by the system message.```"
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": prompt_user},
        ],
        temperature=0.1,
        max_tokens=900,
        response_format={"type": "json_object"},
        seed=42,
    )
    content = resp.choices[0].message.content.strip()
    data = json.loads(content)
    data["duration_ms"] = int((time.time() - start) * 1000)
    data["model"] = "gpt-4o-mini"
    return data
