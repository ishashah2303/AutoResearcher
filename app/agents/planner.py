from app.state import ResearchState
from app.gemini import generate_text
import logging

logger = logging.getLogger(__name__)

def planner_agent(state: ResearchState) -> ResearchState:
    """
    Creates a research plan with 3-4 concrete steps.
    Simplified to reduce token usage and rate limit issues.
    """
    # ✅ IMPROVEMENT: Shorter, more focused prompt
    prompt = f"""Create a research plan for: {state.topic}

List 3-4 specific search queries. Keep each query under 20 words.

Format:
1. [query]
2. [query]
3. [query]

Example for "AI in healthcare":
1. AI medical diagnosis accuracy studies
2. AI healthcare implementation challenges
3. Future AI healthcare applications"""

    try:
        logger.info(f"Planning research for: {state.topic}")
        output = generate_text(prompt)
        
        # Parse the output
        steps = []
        for line in output.split("\n"):
            line = line.strip()
            # Match numbered lines
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Remove numbering and bullets
                clean_line = line.lstrip("0123456789.-•) \t")
                if clean_line:
                    steps.append(clean_line)
        
        # Fallback to basic split if parsing fails
        if not steps:
            steps = [s.strip() for s in output.split("\n") if s.strip()]
        
        # Limit to 4 steps to avoid rate limits
        steps = steps[:4]
        
        # If we still don't have steps, create default ones
        if not steps:
            logger.warning("Failed to parse plan, using default steps")
            steps = [
                f"Find recent articles about {state.topic}",
                f"Search for expert opinions on {state.topic}",
                f"Look for case studies related to {state.topic}",
            ]
        
        state.plan = steps
        state.current_step = 0
        state.status = f"Created plan with {len(steps)} steps"
        
        logger.info(f"Plan created with {len(steps)} steps: {steps}")
        
    except Exception as e:
        logger.error(f"Error in planner agent: {str(e)}")
        # Create a simple fallback plan
        state.plan = [
            f"Research overview of {state.topic}",
            f"Find key developments in {state.topic}",
            f"Explore challenges in {state.topic}",
        ]
        state.current_step = 0
        state.status = "Using fallback plan due to error"
    
    return state