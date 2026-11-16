# =============================================================
# graph/candidate_graph.py
# TalentMatch AI - Candidate Workflow Graph Orchestration
# =============================================================

import json
import os
import re
from typing import TypedDict, Optional
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from utils.file_parser import extract_essential_resume_text

# Output token ceiling for every LLM invocation in this graph. High enough that a
# compact structured-JSON analysis (or a fully tailored resume) is never cut off
# mid-sentence, which previously produced schema-mismatch / truncated-JSON errors.
LLM_MAX_OUTPUT_TOKENS = 4096


# ------------------------------------------------------------------
# STATE DEFINITION
# ------------------------------------------------------------------
class CandidateState(TypedDict):
    """Represents the global state synchronized across the pipeline graph nodes."""
    resume_text: str
    target_job: str
    job_description: Optional[str]
    current_question: Optional[str]
    candidate_answer: Optional[str]
    analysis_report: Optional[str]
    interview_questions: Optional[str]
    mock_evaluation: Optional[str]
    career_guidance: Optional[str]
    tailored_resume: Optional[str]  # Dedicated tracking slot for Step 6 output
    error: Optional[str]


# ------------------------------------------------------------------
# LLM INVOCATION FACTORY
# ------------------------------------------------------------------
def get_llm():
    """Instantiates the LLM client engine dynamically based on the available API key."""
    groq_key = os.getenv("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    # 1. Determine if we are utilizing a Groq configuration ecosystem
    if groq_key or (openai_key and openai_key.startswith("gsk_")):
        from langchain_groq import ChatGroq
        
        active_key = groq_key if groq_key else openai_key
        model_name = os.getenv("LLM_MODEL_NAME", "llama-3.3-70b-versatile")
        
        # Fallback guard in case environmental variables default to an OpenAI target model name
        if "gpt-" in model_name.lower():
            model_name = "llama-3.3-70b-versatile"
            
        return ChatGroq(
            model=model_name,
            temperature=0.3,
            max_tokens=LLM_MAX_OUTPUT_TOKENS,
            groq_api_key=active_key
        )

    # 2. Otherwise default downstream architecture directly to OpenAI core
    else:
        from langchain_openai import ChatOpenAI

        model_name = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")
        base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

        return ChatOpenAI(
            model=model_name,
            temperature=0.3,
            max_tokens=LLM_MAX_OUTPUT_TOKENS,
            openai_api_key=openai_key,
            openai_api_base=base_url
        )


# ------------------------------------------------------------------
# WORKFLOW GRAPH NODES
# ------------------------------------------------------------------

def _close_open_brackets(text: str) -> str:
    """Closes any string literal / array / object still open at the end of `text`,
    tracking nesting depth (and honoring escaped quotes) rather than naively
    counting characters, so a response cut short mid-field can still round-trip
    through `json.loads` once the dangling structures are capped off."""
    stack = []
    in_string = False
    escaped = False
    for ch in text:
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if stack:
                stack.pop()

    repaired = text + ('"' if in_string else "")
    repaired += "".join("}" if ch == "{" else "]" for ch in reversed(stack))
    return repaired


def _parse_llm_json_response(raw_text: str) -> dict:
    """
    Parses a JSON object out of an LLM response, tolerating the minor formatting
    quirks models commonly introduce - a ```json fence wrapper, leading/trailing
    prose, or an object cut short mid-field by a token-limit truncation. Never
    raises: a response that can't be salvaged just yields an empty dict, so the
    caller can fall back to defaults instead of hitting a schema-mismatch crash.
    """
    if not raw_text:
        return {}

    candidate_text = raw_text.strip()

    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", candidate_text, re.DOTALL)
    if fence_match:
        candidate_text = fence_match.group(1).strip()

    try:
        return json.loads(candidate_text)
    except json.JSONDecodeError:
        pass

    brace_start = candidate_text.find("{")
    if brace_start == -1:
        return {}
    snippet = candidate_text[brace_start:]

    # Prefer the outermost well-formed {...} block, in case of trailing prose after it
    brace_match = re.search(r"\{.*\}", snippet, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    # Likely truncated mid-object (hit max_tokens with no closing brace at all):
    # close whatever string/array/object is still open and retry
    try:
        return json.loads(_close_open_brackets(snippet))
    except json.JSONDecodeError:
        pass

    # Still broken - drop the last, incomplete "key": value field and retry
    trimmed = re.sub(r',\s*"[^"]*"\s*:\s*[^,]*$', "", snippet)
    if trimmed != snippet:
        try:
            return json.loads(_close_open_brackets(trimmed))
        except json.JSONDecodeError:
            pass

    return {}


def _format_analysis_report(parsed: dict, fallback_text: str) -> str:
    """
    Renders the compact structured-JSON payload from analyze_resume_node back into
    the markdown report format downstream consumers already expect: a leading
    "Alignment Score: N%" line for `parse_score_metrics`' regex, single-line
    "Label: value" summaries for the recruiter portal's keyword-snippet extractor,
    and a fully bulleted breakdown underneath for on-screen/expander display.
    """
    if not parsed:
        return fallback_text or "Error: The model returned an unparseable analysis response."

    score = parsed.get("alignment_score", 75)
    strengths = [s for s in (parsed.get("match_strengths") or []) if s][:2]
    gaps = [g for g in (parsed.get("critical_gaps") or []) if g][:2]
    upgrades = [u for u in (parsed.get("instant_upgrades") or []) if u][:2]
    experience_summary = parsed.get("key_experience_summary") or "Not specified."

    # Experience Summary is listed first among the searchable single-line summaries
    # (ahead of Match Strengths / Critical Gaps) so the recruiter portal's
    # keyword-snippet extractor - which returns the first line matching
    # "experience"/"background"/"history" - lands on this dedicated line instead of
    # incidentally matching a strength/gap bullet that happens to mention "experience".
    lines = [
        f"Alignment Score: {score}%",
        f"Experience Summary: {experience_summary}",
        f"Match Strengths: {'; '.join(strengths) if strengths else 'Not specified.'}",
        f"Critical Gaps: {'; '.join(gaps) if gaps else 'Not specified.'}",
        "",
        "### Match Strengths",
    ]
    lines += [f"- {item}" for item in strengths] if strengths else ["- Not specified."]
    lines += ["", "### Critical Gaps & Missing Keywords"]
    lines += [f"- {item}" for item in gaps] if gaps else ["- Not specified."]
    lines += ["", "### Instant Upgrades"]
    lines += [f"- {item}" for item in upgrades] if upgrades else ["- Not specified."]

    return "\n".join(lines)


def analyze_resume_node(state: CandidateState) -> dict:
    """Computes structural alignment weights and matches resume contents against requirements."""
    llm = get_llm()
    jd_context = state.get("job_description") or "No explicit job description provided."

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an elite Tech Recruiter and Applicant Tracking System (ATS) optimization expert.
Analyze the provided resume against the Target Job Role and optional Job Description text.
Identify key metric gaps, keyword omissions, structural anomalies, and overall alignment strength.

Respond with ONLY a single, compact, valid JSON object - no markdown code fences, no commentary
before or after it - using exactly this schema:
{{
  "alignment_score": <integer 0-100>,
  "match_strengths": [<at most 2 short bullet strings, each under 20 words>],
  "critical_gaps": [<at most 2 short bullet strings, each under 20 words>],
  "instant_upgrades": [<at most 2 short, actionable bullet strings, each under 20 words>],
  "key_experience_summary": <one concise sentence summarizing the candidate's relevant experience>
}}

Keep every field concise and high-density. Never include more than 2 items in any list."""),
        ("user", "Target Job: {target_job}\nRecruiter Job Description Context: {job_description}\n\nResume Body Text:\n{resume_text}")
    ])

    chain = prompt | llm
    response = chain.invoke({
        "target_job": state["target_job"],
        "job_description": jd_context,
        "resume_text": state["resume_text"]
    })

    parsed_analysis = _parse_llm_json_response(response.content)
    return {"analysis_report": _format_analysis_report(parsed_analysis, response.content)}


def generate_questions_node(state: CandidateState) -> dict:
    """Isolates core technical skill layers and builds diagnostic evaluation parameters."""
    llm = get_llm()
    jd_context = state.get("job_description") or "No explicit job description provided."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an elite Technical Interviewer. Generate a highly customized set of interview questions.
Analyze the candidate's resume alongside their target role and job description specs.
Generate exactly 5 highly tactical technical interview questions designed to test the specific engineering skills required for this combination. 

Break down the layout into:
- 3 Hard Technical/Architectural Questions (relevant to the Tech Stack implied by the role and JD)
- 2 Scenario/System Design Questions"""),
        ("user", "Target Job: {target_job}\nJob Description Matrix: {job_description}\n\nResume Body Text:\n{resume_text}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "target_job": state["target_job"],
        "job_description": jd_context,
        "resume_text": state["resume_text"]
    })
    
    return {"interview_questions": response.content}


def evaluate_mock_node(state: CandidateState) -> dict:
    """Verifies mock interaction payload inputs against validation baselines."""
    llm = get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an Advanced Mock Interview Evaluation Engine.
Review the technical prompt/question provided to the user, evaluate their structural argument payload, and provide clear constructive corrections.

Provide:
- An overall response grade (e.g., Strong Pass, Pass, Borderline, Needs Improvement)
- Technical Accuracy Assessment (Is their code/logic or conceptual architecture accurate?)
- What was missing from the answer
- An optimized model response showing how a Principal Engineer would answer it"""),
        ("user", "Target Role context: {target_job}\n\nInterview Prompt: {question}\nCandidate Argument Payload:\n{answer}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "target_job": state["target_job"],
        "question": state.get("current_question", ""),
        "answer": state.get("candidate_answer", "")
    })
    
    return {"mock_evaluation": response.content}


def career_guidance_node(state: CandidateState) -> dict:
    """Synthesizes technical development roadmaps based on identified domain deltas."""
    llm = get_llm()
    jd_context = state.get("job_description") or "No explicit job description provided."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an Executive Technical Career Coach.
Based on the candidate's core resume and their ultimate career target/job description parameters, outline an optimization learning roadmap.
Map out the missing system architectural boundaries, library environments, frameworks, and structural pipeline concepts they must learn.

Format clearly with markdown headers:
- Immediate Tech Stack Additions (What tools to study next)
- Project Architecture Blueprint (Describe 1 target resume-worthy project they should build to prove competency)
- 30-60-90 Day Skills Milestones"""),
        ("user", "Target Job Goal: {target_job}\nTarget Job Description: {job_description}\n\nResume Profile Base:\n{resume_text}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "target_job": state["target_job"],
        "job_description": jd_context,
        "resume_text": state["resume_text"]
    })
    
    return {"career_guidance": response.content}


def tailor_resume_node(state: CandidateState) -> dict:
    """
    NEW NODE (Step 6): Re-architects and rewrites the source resume text using 
    the target job specs, structural gap notes, and the recruiter's job description.
    """
    llm = get_llm()
    jd_context = state.get("job_description") or "No explicit job description provided."
    preceding_analysis = state.get("analysis_report") or "Ensure optimization alignment to standard industry metrics."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an Expert AI Resume Writer specializing in FAANG and tier-1 tech startup resume optimization.
Your task is to completely rewrite the user's original resume to perfectly tailor it for their Target Job and the specific Recruiter Job Description.

Operational Rules:
1. DO NOT invent fake companies, degrees, or certifications.
2. Optimize existing project and role descriptions to highlight matching keywords, metrics, and technical requirements found in the Job Description.
3. Use high-impact action verbs and structure bullet points using the XYZ formula (Accomplished [X] as measured by [Y], by doing [Z]).
4. Output a pristine, fully fleshed-out, professional Markdown resume ready for deployment."""),
        ("user", """Target Job Role: {target_job}
Target Job Description Matrix:
{job_description}

Preceding Alignment Strategy Notes:
{analysis_notes}

Original Resume Payload:
{resume_text}""")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "target_job": state["target_job"],
        "job_description": jd_context,
        "analysis_notes": preceding_analysis,
        "resume_text": state["resume_text"]
    })
    
    return {"tailored_resume": response.content}


# ------------------------------------------------------------------
# GRAPH ORCHESTRATION BUILDER
# ------------------------------------------------------------------

def create_candidate_graph():
    """Assembles node routes and returns an executable workflow compilation graph state."""
    workflow = StateGraph(CandidateState)
    
    # 1. Register Graph Processing Processing Nodes
    workflow.add_node("analyze_resume", analyze_resume_node)
    workflow.add_node("generate_questions", generate_questions_node)
    workflow.add_node("evaluate_mock", evaluate_mock_node)
    workflow.add_node("career_guidance", career_guidance_node)
    workflow.add_node("tailor_resume", tailor_resume_node)  # Added to state map layout
    
    # 2. Setup Operational Processing Entry Point
    workflow.set_entry_point("analyze_resume")
    
    # 3. Establish Direct Flow Edges (Linear isolated node execution scheme)
    workflow.add_edge("analyze_resume", "generate_questions")
    workflow.add_edge("generate_questions", "evaluate_mock")
    workflow.add_edge("evaluate_mock", "career_guidance")
    workflow.add_edge("career_guidance", "tailor_resume")
    workflow.add_edge("tailor_resume", END)
    
    return workflow.compile()


# ------------------------------------------------------------------
# RUNNER INTERFACE
# ------------------------------------------------------------------

def run_candidate_workflow(
    resume_text: str,
    target_job: str,
    job_description: Optional[str] = None,
    run_analysis: bool = False,
    run_interview_gen: bool = False,
    run_mock: bool = False,
    run_career: bool = False,
    run_resume_generation: bool = False,  # Flag mapping to Step 6
    current_question: Optional[str] = None,
    candidate_answer: Optional[str] = None,
) -> dict:
    """
    Executes targeted state isolation mutations depending on parameters invoked by app.py.

    Returns:
        A structural state values map ledger containing computed payload reports.
    """
    # Strip formatting noise (tab indentation, duplicate blank lines, page breaks,
    # non-printable characters) before the resume text ever reaches an LLM prompt,
    # so the input token budget is spent on signal rather than boilerplate.
    cleaned_resume_text = extract_essential_resume_text(resume_text)

    # Build core tracking dictionary mapping variables down to nodes
    initial_state: CandidateState = {
        "resume_text": cleaned_resume_text,
        "target_job": target_job,
        "job_description": job_description if job_description and job_description.strip() else None,
        "current_question": current_question,
        "candidate_answer": candidate_answer,
        "analysis_report": None,
        "interview_questions": None,
        "mock_evaluation": None,
        "career_guidance": None,
        "tailored_resume": None,
        "error": None
    }
    
    try:
        # Isolated execution router minimizing resource overhead based on UI flags
        if run_analysis:
            return analyze_resume_node(initial_state)
            
        elif run_interview_gen:
            return generate_questions_node(initial_state)
            
        elif run_mock:
            return evaluate_mock_node(initial_state)
            
        elif run_career:
            return career_guidance_node(initial_state)
            
        elif run_resume_generation:
            # First fetch the raw profile analytics matrix data layer if not pre-cached
            # to feed optimal engineering suggestions straight to the typing node
            analysis_data = analyze_resume_node(initial_state)
            initial_state["analysis_report"] = analysis_data.get("analysis_report")
            
            return tailor_resume_node(initial_state)
            
        else:
            # Fallback optimization route executing the entire unified processing pipeline
            compiled_graph = create_candidate_graph()
            return compiled_graph.invoke(initial_state)
            
    except Exception as workflow_exception:
        return {"error": f"{type(workflow_exception).__name__}: {str(workflow_exception)}"}