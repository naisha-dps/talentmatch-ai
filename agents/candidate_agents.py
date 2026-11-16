# =============================================================
# agents/candidate_agents.py
# LangChain-powered agents for the Candidate Module
# Each function is a standalone agent that takes input and
# returns the LLM's response as a string.
# =============================================================

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils.llm_config import get_llm
from prompts.candidate_prompts import (
    RESUME_ANALYZER_PROMPT,
    INTERVIEW_QUESTIONS_PROMPT,
    MOCK_INTERVIEW_EVALUATOR_PROMPT,
    CAREER_GUIDANCE_PROMPT,
)


def run_resume_analyzer(resume_text: str, target_job: str) -> str:
    """
    Agent 1: Analyze a resume for strengths, weaknesses,
    missing sections, improvements, and ATS score tailored to a target job.

    Args:
        resume_text (str): Raw text extracted from the PDF resume
        target_job (str): The specific job role the candidate wants to target

    Returns:
        str: Formatted analysis report from the LLM
    """
    # Create a PromptTemplate with both resume_text and target_job placeholders
    prompt = PromptTemplate(
        input_variables=["resume_text", "target_job"],
        template=RESUME_ANALYZER_PROMPT,
    )

    # Get the LLM instance (lower temperature for more analytical output)
    llm = get_llm(temperature=0.4)

    # Build the LangChain chain: prompt → LLM → string parser
    chain = prompt | llm | StrOutputParser()

    # Run the chain with both the resume text and the job role as input
    result = chain.invoke({"resume_text": resume_text, "target_job": target_job})
    return result


def run_interview_question_generator(resume_text: str) -> str:
    """
    Agent 2: Generate personalized interview questions based on resume.
    Produces technical, HR, and behavioral questions.
    """
    prompt = PromptTemplate(
        input_variables=["resume_text"],
        template=INTERVIEW_QUESTIONS_PROMPT,
    )

    llm = get_llm(temperature=0.6)
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"resume_text": resume_text})
    return result


def run_mock_interview_evaluator(question: str, answer: str) -> str:
    """
    Agent 3: Evaluate a single mock interview answer.
    Provides score, feedback, and improvement tips.
    """
    prompt = PromptTemplate(
        input_variables=["question", "answer"],
        template=MOCK_INTERVIEW_EVALUATOR_PROMPT,
    )

    llm = get_llm(temperature=0.3)
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"question": question, "answer": answer})
    return result


def run_career_guidance(resume_text: str) -> str:
    """
    Agent 4: Generate personalized career guidance including
    skills to learn, certifications, projects, and roadmap.
    """
    prompt = PromptTemplate(
        input_variables=["resume_text"],
        template=CAREER_GUIDANCE_PROMPT,
    )

    llm = get_llm(temperature=0.7)
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"resume_text": resume_text})
    return result