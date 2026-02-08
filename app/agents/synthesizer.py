from datetime import datetime
from app.gemini import generate_text

def synthesizer_agent(state):
    # Support dict-based state (LangGraph) and object-based state (ResearchState)
    if isinstance(state, dict):
        sources = state.get("sources") or []
        topic = state.get("topic", "")
        existing_report = state.get("report")
    else:
        sources = getattr(state, "sources", None) or []
        topic = getattr(state, "topic", "")
        existing_report = getattr(state, "report", None)

    # ✅ Skip if already synthesized (works for dict + object)
    if existing_report:
        return state

    if not sources:
        msg = "No sources were retrieved. Check Tavily key/config or try a different query."
        return {"report": msg} if isinstance(state, dict) else _set_and_return(state, msg)

    # Build notes
    notes = "\n\n".join(
        f"Source ({s.get('url','')}): {(s.get('content','') or '')[:900]}"
        for s in sources
        if isinstance(s, dict)
    )

    today = datetime.now().strftime("%B %d, %Y")

    prompt = f"""
Write a structured research report on:

{topic}

Date: {today}
Do NOT include placeholder author names.

Include these headings exactly:
# Research Report: {topic}
## Date
## Overview
## Key Findings
## Conflicting Viewpoints
## Conclusion
## References

Rules:
- Use concise bullets under Key Findings.
- References must be a bullet list of clickable URLs (prefer the exact source URLs from notes).
- Do not invent citations that aren't in the notes.

Research Notes:
{notes}
"""

    report_text = generate_text(prompt)

    if isinstance(state, dict):
        return {"report": report_text}
    else:
        state.report = report_text
        return state

def _set_and_return(state, msg: str):
    state.report = msg
    return state
