# =============================================================
# graph/recruiter_graph.py
# LangGraph Workflow for the Recruiter Module
#
# Flow:
#   resume_upload → job_description_node → candidate_matcher
#                 → skill_gap_analyzer → hiring_recommendation
# =============================================================

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from agents.recruiter_agents import (
    run_candidate_matcher,
    run_skill_gap_analyzer,
    run_hiring_recommendation,
)


# ------------------------------------------------------------------
# STATE DEFINITION
# ------------------------------------------------------------------
class RecruiterState(TypedDict):
    # Inputs
    resume_text: str                         # Raw text from candidate's PDF
    job_description: str                     # Job description from recruiter

    # Outputs from each agent node
    match_report: Optional[str]              # From candidate_matcher node
    skill_gap_report: Optional[str]          # From skill_gap_analyzer node
    hiring_recommendation: Optional[str]     # From hiring_recommendation node

    # Control flags
    run_matching: bool
    run_skill_gap: bool
    run_recommendation: bool

    # Error tracking
    error: Optional[str]


# ------------------------------------------------------------------
# NODE FUNCTIONS
# ------------------------------------------------------------------

def resume_upload_node(state: RecruiterState) -> dict:
    """
    Node 1: Resume Upload Validation
    Ensures the resume text is valid before processing.
    """
    if not state.get("resume_text") or len(state["resume_text"].strip()) < 50:
        return {"error": "Resume text is too short or empty. Please upload a valid PDF."}
    return {"error": None}


def job_description_node(state: RecruiterState) -> dict:
    """
    Node 2: Job Description Validation
    Ensures a job description was provided.
    """
    if not state.get("job_description") or len(state["job_description"].strip()) < 20:
        return {"error": "Job description is too short. Please provide more details."}
    return {"error": None}


def candidate_matcher_node(state: RecruiterState) -> dict:
    """
    Node 3: Candidate Matching Agent
    Compares resume vs job description and generates match %.
    """
    if not state.get("run_matching"):
        return {}

    # Stop pipeline if there was an earlier error
    if state.get("error"):
        return {}

    try:
        match_report = run_candidate_matcher(
            state["resume_text"],
            state["job_description"]
        )
        return {"match_report": match_report}
    except Exception as e:
        return {"error": f"Candidate matching failed: {str(e)}"}


def skill_gap_node(state: RecruiterState) -> dict:
    """
    Node 4: Skill Gap Analyzer
    Identifies strong skills and skill gaps.
    """
    if not state.get("run_skill_gap"):
        return {}

    if state.get("error"):
        return {}

    try:
        skill_gap_report = run_skill_gap_analyzer(
            state["resume_text"],
            state["job_description"]
        )
        return {"skill_gap_report": skill_gap_report}
    except Exception as e:
        return {"error": f"Skill gap analysis failed: {str(e)}"}


def hiring_recommendation_node(state: RecruiterState) -> dict:
    """
    Node 5: Hiring Recommendation Agent
    Provides final hiring decision: Strong Hire / Hire / Consider / Reject
    """
    if not state.get("run_recommendation"):
        return {}

    if state.get("error"):
        return {}

    try:
        recommendation = run_hiring_recommendation(
            state["resume_text"],
            state["job_description"]
        )
        return {"hiring_recommendation": recommendation}
    except Exception as e:
        return {"error": f"Hiring recommendation failed: {str(e)}"}


# ------------------------------------------------------------------
# GRAPH CONSTRUCTION
# ------------------------------------------------------------------

def build_recruiter_graph():
    """
    Build and compile the LangGraph StateGraph for the recruiter workflow.

    Returns:
        CompiledStateGraph: The compiled workflow ready to invoke.
    """
    graph = StateGraph(RecruiterState)

    # Register all nodes
    graph.add_node("resume_upload", resume_upload_node)
    graph.add_node("job_description_node", job_description_node)
    graph.add_node("candidate_matcher", candidate_matcher_node)
    graph.add_node("skill_gap", skill_gap_node)
    
    # FIX: Renamed string identifier to prevent overlapping with RecruiterState['hiring_recommendation']
    graph.add_node("hiring_recommendation_node_id", hiring_recommendation_node)

    # Define linear pipeline
    graph.set_entry_point("resume_upload")
    graph.add_edge("resume_upload", "job_description_node")
    graph.add_edge("job_description_node", "candidate_matcher")
    graph.add_edge("candidate_matcher", "skill_gap")
    
    # FIX: Updated routing strings here to point to your updated node ID string
    graph.add_edge("skill_gap", "hiring_recommendation_node_id")
    graph.add_edge("hiring_recommendation_node_id", END)

    return graph.compile()


# Singleton compiled graph
recruiter_graph = build_recruiter_graph()


def run_recruiter_workflow(
    resume_text: str,
    job_description: str,
    run_matching: bool = False,
    run_skill_gap: bool = False,
    run_recommendation: bool = False,
) -> RecruiterState:
    """
    Main entry point for the recruiter LangGraph workflow.

    Args:
        resume_text: Extracted text from candidate's PDF resume
        job_description: Job description text from recruiter
        run_matching: Whether to run candidate matching
        run_skill_gap: Whether to run skill gap analysis
        run_recommendation: Whether to generate hiring recommendation

    Returns:
        RecruiterState: Final state with all agent outputs populated
    """
    initial_state: RecruiterState = {
        "resume_text": resume_text,
        "job_description": job_description,
        "match_report": None,
        "skill_gap_report": None,
        "hiring_recommendation": None,
        "run_matching": run_matching,
        "run_skill_gap": run_skill_gap,
        "run_recommendation": run_recommendation,
        "error": None,
    }

    final_state = recruiter_graph.invoke(initial_state)
    return final_state