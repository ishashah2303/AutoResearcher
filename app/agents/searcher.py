# app/agents/searcher.py
import os
from app import state
from tavily import TavilyClient
from app.state import ResearchState

def search_agent(state: ResearchState) -> ResearchState:
    # Stop if plan is done
    if state.current_step >= len(state.plan):
        return state

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing TAVILY_API_KEY")

    client = TavilyClient(api_key=api_key)

    query = state.plan[state.current_step]
    print(f"🔍 Searching step {state.current_step + 1}/{len(state.plan)}: {query}")



    resp = client.search(
        query=query,
        max_results=5,
        search_depth="basic",
        include_answer=False,
        include_raw_content=False,
    )

    results = resp.get("results", []) if isinstance(resp, dict) else []

    # Deduplicate by URL
    seen = set(s.get("url") for s in state.sources if isinstance(s, dict))
    for r in results:
        url = r.get("url")
        content = r.get("content") or ""
        if not url or url in seen:
            continue
        seen.add(url)
        state.sources.append({
            "url": url,
            "content": content[:4000],
            "source_type": "tavily",
        })

    # ✅ CRITICAL: advance the loop
    state.current_step += 1
    return state
