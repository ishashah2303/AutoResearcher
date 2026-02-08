from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from app.graph import research_graph
from app.state import ResearchState
import json
import time
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AutoResearcher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

URL_RE = re.compile(
    r'(?P<url>(https?://[^\s\]\)]+)|((?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/[^\s\]\)]+))'
)

def linkify(text: str) -> str:
    """Convert URLs in text to markdown links"""
    if not text:
        return text

    def repl(m):
        raw = m.group(0)
        url = raw if raw.startswith("http") else "https://" + raw
        return f"[{raw}]({url})"
    return URL_RE.sub(repl, text)


@app.get("/")
def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AutoResearcher API"}


@app.post("/research")
def research(topic: str):
    """
    Main research endpoint with improved error handling.
    
    Args:
        topic: Research topic (3-500 characters)
        
    Returns:
        JSON with report and sources
        
    Raises:
        HTTPException: For various error conditions
    """
    # ✅ Input validation
    if not topic or len(topic.strip()) < 3:
        raise HTTPException(
            status_code=400, 
            detail="Topic must be at least 3 characters long"
        )
    
    if len(topic) > 500:
        raise HTTPException(
            status_code=400,
            detail="Topic must be less than 500 characters"
        )
    
    logger.info(f"Starting research for topic: {topic}")
    
    try:
        state = ResearchState(topic=topic)
        
        # Invoke the research graph
        result = research_graph.invoke(
            state.dict(), 
            {"recursion_limit": 30}
        )
        
        report = linkify(result.get("report") or "")
        sources = result.get("sources", []) or []
        
        logger.info(f"Research completed successfully. Sources: {len(sources)}")
        
        return {
            "success": True,
            "report": report, 
            "sources": sources,
            "topic": topic
        }
    
    except RuntimeError as e:
        error_msg = str(e)
        
        # ✅ Handle rate limit errors gracefully
        if "rate limit" in error_msg.lower():
            logger.warning(f"Rate limit hit for topic: {topic}")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": "The AI service is rate limited. Please wait 1-2 minutes and try again.",
                    "retry_after": 60,
                    "tip": "Try a simpler topic or wait between requests"
                }
            )
        
        # ✅ Handle Tavily API errors
        if "TAVILY_API_KEY" in error_msg:
            logger.error("Tavily API key missing")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Configuration error",
                    "message": "Search API key not configured. Please contact administrator."
                }
            )
        
        # Other runtime errors
        logger.error(f"Runtime error during research: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Research failed",
                "message": error_msg
            }
        )
    
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error during research: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again."
            }
        )


@app.get("/research_stream")
def research_stream(topic: str):
    """
    Streaming research endpoint with real-time progress updates.
    
    Args:
        topic: Research topic
        
    Returns:
        Server-Sent Events stream
    """
    # ✅ Input validation
    if not topic or len(topic.strip()) < 3:
        return JSONResponse(
            status_code=400,
            content={"error": "Topic must be at least 3 characters long"}
        )
    
    logger.info(f"Starting streaming research for topic: {topic}")
    
    def sse():
        try:
            # Initial event
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting research...', 'progress': 0})}\n\n"
            
            state = ResearchState(topic=topic)
            
            # Stream state updates as the graph runs
            for update in research_graph.stream(
                state.dict(), 
                {"recursion_limit": 30}, 
                stream_mode="values"
            ):
                msg = update.get("status") or ""
                prog = update.get("progress")
                
                payload = {
                    "type": "progress",
                    "message": msg,
                    "progress": prog if prog is not None else None,
                    "current_step": update.get("current_step"),
                    "total_steps": len(update.get("plan") or []),
                }
                yield f"data: {json.dumps(payload)}\n\n"
            
            # Get final result
            final = research_graph.invoke(state.dict(), {"recursion_limit": 30})
            report = linkify(final.get("report") or "")
            sources = final.get("sources", []) or []
            
            yield f"data: {json.dumps({'type': 'final', 'report': report, 'sources': sources, 'progress': 1.0})}\n\n"
            logger.info("Streaming research completed successfully")
        
        except RuntimeError as e:
            error_msg = str(e)
            if "rate limit" in error_msg.lower():
                yield f"data: {json.dumps({'type': 'error', 'message': 'Rate limit exceeded. Please wait and try again.'})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
        
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': 'An error occurred during research'})}\n\n"
    
    return StreamingResponse(sse(), media_type="text/event-stream")


@app.get("/health")
def health_check():
    """Detailed health check"""
    import os
    
    health = {
        "status": "healthy",
        "gemini_key_configured": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
        "tavily_key_configured": bool(os.getenv("TAVILY_API_KEY")),
    }
    
    return health