# app/agents/evaluator.py
import json
import re
from app.state import ResearchState
from app.gemini import generate_text

def evaluator_agent(state: ResearchState) -> ResearchState:
    print(f"🧪 Evaluating {len(state.sources)} sources so far")

    # Ensure list exists
    if not state.sources:
        return state

    # Keep already-scored sources; only score new ones
    to_score = []
    kept = []
    for i, src in enumerate(state.sources):
        if isinstance(src, dict) and "score" in src:
            kept.append(src)
        else:
            # minimal payload to reduce tokens
            to_score.append({
                "id": i,
                "url": (src.get("url","") if isinstance(src, dict) else ""),
                "snippet": ((src.get("content","") if isinstance(src, dict) else "")[:600]),
            })

    if not to_score:
        state.sources = kept
        return state

    prompt = f"""
You are scoring source credibility for a research assistant.
For each item, return a JSON array of objects: [{{"id": <int>, "score": <float 0..1>}}, ...]
Return ONLY valid JSON. No markdown, no explanation.

Scoring guide:
- 0.9–1.0: peer-reviewed journals, gov/edu, major medical orgs, reputable news with citations
- 0.6–0.8: generally credible outlets, clear authorship, references
- 0.3–0.5: blogs, unclear sourcing, promotional content
- 0.0–0.2: spam, unverifiable, sensational, no sources

Items:
{json.dumps(to_score, ensure_ascii=False)}
"""

    raw = generate_text(prompt)

    # Parse JSON safely
    try:
        # strip accidental code fences if model adds them
        raw_clean = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.IGNORECASE).strip()
        scores = json.loads(raw_clean)
    except Exception as e:
        # If parsing fails, assign a conservative default
        for item in to_score:
            # Find original source by id
            src = state.sources[item["id"]]
            if isinstance(src, dict):
                src["score"] = 0.3
                src["eval_error"] = f"JSON parse failed: {e}"
                kept.append(src)
        state.sources = kept
        return state

    score_map = {}
    for obj in scores if isinstance(scores, list) else []:
        try:
            score_map[int(obj["id"])] = max(0.0, min(1.0, float(obj["score"])))
        except Exception:
            continue

    # Attach scores back to sources
    for item in to_score:
        src = state.sources[item["id"]]
        if isinstance(src, dict):
            src["score"] = score_map.get(item["id"], 0.3)
            kept.append(src)

    # Filter, but don't wipe everything
    filtered = [s for s in kept if s.get("score", 0) >= 0.6]
    state.sources = filtered if filtered else sorted(kept, key=lambda s: s.get("score", 0), reverse=True)[:3]
    return state
