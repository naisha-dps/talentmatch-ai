# =============================================================
# agents/recruiter_agents.py
# LangChain-powered agents for the Recruiter Module
# =============================================================

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils.llm_config import get_llm
from prompts.recruiter_prompts import (
    CANDIDATE_MATCHING_PROMPT,
    SKILL_GAP_PROMPT,
    HIRING_RECOMMENDATION_PROMPT,
)


def run_candidate_matcher(resume_text: str, job_description: str) -> str:
    """
    Agent 1: Compare candidate resume vs job description.
    Generates a match percentage and detailed explanation.

    Args:
        resume_text (str): Extracted text from candidate's PDF resume
        job_description (str): The job description entered by the recruiter

    Returns:
        str: Match report with percentage and key matches/gaps
    """
    prompt = PromptTemplate(
        input_variables=["resume_text", "job_description"],
        template=CANDIDATE_MATCHING_PROMPT,
    )

    # Low temperature for consistent, objective scoring
    llm = get_llm(temperature=0.3)

    # Chain: prompt → LLM → string output
    chain = prompt | llm | StrOutputParser()

    result = chain.invoke({
        "resume_text": resume_text,
        "job_description": job_description,
    })
    return result


def run_skill_gap_analyzer(resume_text: str, job_description: str) -> str:
    """
    Agent 2: Deep skill gap analysis comparing candidate to JD.
    Identifies strong skills, missing skills, and ramp-up time.

    Args:
        resume_text (str): Extracted text from candidate's PDF resume
        job_description (str): The job description entered by the recruiter

    Returns:
        str: Detailed skill gap report
    """
    prompt = PromptTemplate(
        input_variables=["resume_text", "job_description"],
        template=SKILL_GAP_PROMPT,
    )

    llm = get_llm(temperature=0.3)

    chain = prompt | llm | StrOutputParser()

    result = chain.invoke({
        "resume_text": resume_text,
        "job_description": job_description,
    })
    return result


def run_hiring_recommendation(resume_text: str, job_description: str) -> str:
    """
    Agent 3: Generate a final hiring recommendation.
    Categorizes as: Strong Hire / Hire / Consider / Reject

    Args:
        resume_text (str): Extracted text from candidate's PDF resume
        job_description (str): The job description entered by the recruiter

    Returns:
        str: Final recommendation with detailed reasoning
    """
    prompt = PromptTemplate(
        input_variables=["resume_text", "job_description"],
        template=HIRING_RECOMMENDATION_PROMPT,
    )

    # Slightly higher temperature for nuanced, thoughtful recommendation
    llm = get_llm(temperature=0.4)

    chain = prompt | llm | StrOutputParser()

    result = chain.invoke({
        "resume_text": resume_text,
        "job_description": job_description,
    })
    return result
