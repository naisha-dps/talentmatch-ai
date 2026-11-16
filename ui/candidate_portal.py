# =============================================================
# ui/candidate_portal.py
# TalentMatch AI - Candidate Workspace (Resume Analysis, Optimization,
# Interview Preparation, Voice Interview, Career Roadmap, Resume Generation)
# =============================================================
import os
import re

import pandas as pd
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from groq import Groq

from graph.candidate_graph import run_candidate_workflow
from utils.pdf_parser import extract_text_from_pdf
from utils.voice_utils import analyze_candidate_audio, generate_agent_speech
from ui.workspace_helpers import check_api_infrastructure, render_pipeline_runner


def render_candidate_portal() -> None:
    """Renders the full Candidate workspace: upload, analysis, interview prep,
    voice interview, career roadmap, and tailored resume generation."""

    st.markdown(
        '<div class="section-header">Candidate Optimization & Preparation Workspace</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "Isolate skill deficits, prepare for technical interview evaluations, and refactor "
        "professional profiles through targeted optimization loops."
    )
    st.markdown("---")

    workflow_stages = ["Upload", "Analysis", "Questions", "Voice Interview", "Roadmap", "Tailor Engine"]

    st.subheader("Step 1: Ingest Local Profile Asset")
    cand_upload = st.file_uploader(
        "Select Personal Text-Based PDF Document",
        type=["pdf"],
        help="Upload standard text-based PDF formats directly to parse contents into memory vectors.",
        key="candidate_pdf_uploader",
    )

    if cand_upload is not None:
        cand_upload.seek(0)
        parsed_resume_content = extract_text_from_pdf(cand_upload)

        noise_patterns = [
            r"This site uses cookies.*",
            r"Privacy Policy.*",
            r"Edit this Resume",
            r"Got it!",
            r"https?://\S+",
        ]
        for pattern in noise_patterns:
            parsed_resume_content = re.sub(pattern, "", parsed_resume_content, flags=re.IGNORECASE)
        parsed_resume_content = parsed_resume_content.strip()

        st.session_state["candidate_raw_text"] = parsed_resume_content

        st.markdown(
            f'<div class="success-badge">File stream locked: Indexed {len(parsed_resume_content.split())} '
            f'individual textual metrics elements.</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        with st.expander("Examine Parsed String Payload Preview", expanded=False):
            st.text_area(
                "Raw String Output",
                value=parsed_resume_content[:1800] + "\n\n[Truncated for visualization constraints...]",
                height=180,
                disabled=True,
                label_visibility="collapsed",
            )

    active_resume_payload = st.session_state.get("candidate_raw_text", "")

    if not active_resume_payload:
        st.info("Ingestion channel clear. Provide a profile document layout block to open analytical features.")
        return

    st.markdown("---")
    st.subheader("Step 2: Core Context Evaluation Settings")
    render_pipeline_runner(workflow_stages, current_index=1)
    st.markdown("<br>", unsafe_allow_html=True)

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        target_role = st.text_input(
            "Target Professional Designation Role:",
            placeholder="e.g., Senior Technical Architect, Associate Engineer, Data Scientist",
            key="session_role_title",
        )

    with col_c2:
        target_jd_text = st.text_area(
            "Target Job Description Context Payload (Optional):",
            placeholder="Paste formal enterprise posting requirements to calibrate fine-grained target comparisons...",
            height=70,
            key="session_jd_context",
        )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Execute Core Structural Analysis Run", key="trigger_analysis"):
        if not target_role.strip():
            st.error("Operation Denied: A concrete Target Designation Title parameter must be populated.")
        elif check_api_infrastructure():
            with st.spinner("Invoking LangGraph multi-agent profile comparison matrix..."):
                try:
                    resp = run_candidate_workflow(
                        resume_text=active_resume_payload,
                        target_job=target_role,
                        job_description=target_jd_text,
                        run_analysis=True,
                    )
                    if resp.get("error"):
                        st.error(f"Graph Pipeline Abort Exception: {resp['error']}")
                    elif resp.get("analysis_report"):
                        st.session_state["saved_analysis_report"] = resp["analysis_report"]
                        st.success("Analysis report generated successfully.")
                except Exception as failure:
                    st.error(f"Critical execution breakdown detected: {str(failure)}")

    if st.session_state.get("saved_analysis_report"):
        with st.container():
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown("### ATS Alignment & Deficit Metrics Report")
            st.markdown(st.session_state["saved_analysis_report"])
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Step 3: Static Interview Preparation Bank Framework")
    render_pipeline_runner(workflow_stages, current_index=2)
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Generate Targeting Framework Quest Pack", key="trigger_questions"):
        if check_api_infrastructure():
            with st.spinner("Isolating potential technical friction criteria vectors..."):
                try:
                    resp = run_candidate_workflow(
                        resume_text=active_resume_payload,
                        target_job=st.session_state.get("session_role_title", ""),
                        job_description=st.session_state.get("session_jd_context", ""),
                        run_interview_gen=True,
                    )
                    if resp.get("error"):
                        st.error(f"Graph Pipeline Abort Exception: {resp['error']}")
                    elif resp.get("interview_questions"):
                        st.session_state["saved_interview_questions"] = resp["interview_questions"]
                        st.success("Targeting framework compilation finalized.")
                except Exception as failure:
                    st.error(f"Critical execution breakdown detected: {str(failure)}")

    if st.session_state.get("saved_interview_questions"):
        with st.container():
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown("### Technical Vetting Questions Array")
            st.markdown(st.session_state["saved_interview_questions"])
            st.markdown("</div>", unsafe_allow_html=True)

    # =============================================================
    # STEP 4: MULTI-TURN DYNAMIC & ADAPTIVE VOICE INTERVIEW SIMULATOR
    # =============================================================
    st.markdown("---")
    st.subheader("Step 4: Live Adaptive Voice Interview Portal")
    render_pipeline_runner(workflow_stages, current_index=3)
    st.markdown("<br>", unsafe_allow_html=True)

    if not st.session_state["interview_active"] and not st.session_state["interview_complete"]:
        st.markdown(
            '<div class="info-badge"><b>Ready to begin your adaptive simulation?</b> Instead of going '
            "through fixed pre-generated prompts, the AI agent will analyze your engineering background, "
            "present an opening problem, and dynamically adjust its questions turn-by-turn based on the "
            "content of your spoken answers. Ensure your microphone is accessible.</div>",
            unsafe_allow_html=True,
        )

        if st.button("Start Live Conversational Interview Session", key="initiate_live_interview"):
            if check_api_infrastructure():
                with st.spinner("AI Interviewer is analyzing profile dependencies to generate your custom opening question..."):
                    try:
                        user_groq_key = os.getenv("GROQ_API_KEY")
                        if not user_groq_key:
                            st.error("Configuration Error: GROQ_API_KEY missing from current environment profiles.")
                        else:
                            client = Groq(api_key=user_groq_key)
                            chat_completion = client.chat.completions.create(
                                messages=[
                                    {
                                        "role": "system",
                                        "content": (
                                            "You are a professional corporate recruiter and technical interviewer "
                                            f"evaluating a candidate for the role of {st.session_state.get('session_role_title', 'Software Engineer')}. "
                                            f"Target Job Parameters: {st.session_state.get('session_jd_context', '')}. "
                                            f"Candidate Profile Matrix:\n{active_resume_payload}"
                                        ),
                                    },
                                    {
                                        "role": "user",
                                        "content": (
                                            "Formulate the opening technical or situational engineering interview "
                                            "question for this specific candidate. Acknowledge their target objective, "
                                            "and prompt them to expand on a deep core architectural component or "
                                            "project from their background. Output ONLY the question text itself. "
                                            "Do not include introductory conversational pleasantries, welcoming "
                                            "remarks, or context headers."
                                        ),
                                    },
                                ],
                                model="llama-3.3-70b-versatile",
                            )
                            initial_question = chat_completion.choices[0].message.content.strip()

                            st.session_state["current_question_text"] = initial_question
                            st.session_state["current_question_idx"] = 0
                            st.session_state["interview_history"] = []
                            st.session_state["interview_active"] = True
                            st.session_state["current_question_audio"] = None
                            st.rerun()
                    except Exception as init_err:
                        st.error(f"Runtime startup disruption: {str(init_err)}")

    elif st.session_state["interview_active"]:
        current_idx = st.session_state["current_question_idx"]
        total_questions = 3

        st.markdown(f"### AI Interviewer: Question {current_idx + 1} of {total_questions}")
        active_question = st.session_state["current_question_text"]

        st.markdown(
            f'<div class="result-card" style="border-left: 4px solid #6366f1;"><b>Interviewer Question:</b>'
            f'<br><span style="font-size:1.15rem; color:#ffffff;">{active_question}</span></div>',
            unsafe_allow_html=True,
        )

        if st.session_state["current_question_audio"] is None:
            with st.spinner("Agent preparing vocal projection synthesis..."):
                st.session_state["current_question_audio"] = generate_agent_speech(active_question)

        st.audio(st.session_state["current_question_audio"], format="audio/mp3", autoplay=True)

        st.markdown("---")
        st.write("**Activate your response stream below:**")

        c_mic, c_play = st.columns([1, 3])
        with c_mic:
            recorded_answer_stream = audio_recorder(
                text="Tap to Answer",
                recording_color="#ef4444",
                neutral_color="#6366f1",
                icon_name="microphone",
                icon_size="2x",
                key=f"live_stream_mic_{current_idx}",
            )
        with c_play:
            if recorded_answer_stream:
                st.success("Audio data cached. Ready for evaluation transmission.")
                st.audio(recorded_answer_stream, format="audio/wav")

        st.markdown("<br>", unsafe_allow_html=True)

        is_last_q = (current_idx + 1 >= total_questions)
        btn_label = "Complete Interview & Compute Final Scores" if is_last_q else "Submit Answer & Await Dynamic Follow-up Turn"

        if st.button(btn_label, key="submit_turn_action"):
            if not recorded_answer_stream:
                st.error("Validation Halt: Please record an audio answer response before trying to advance.")
            elif check_api_infrastructure():
                with st.spinner("Processing voice sample metrics through Groq API matrix..."):
                    try:
                        user_groq_key = os.getenv("GROQ_API_KEY")
                        metrics_pack = analyze_candidate_audio(recorded_answer_stream, user_groq_key)

                        st.session_state["interview_history"].append({
                            "question": active_question,
                            "answer": metrics_pack["transcript"],
                            "score": metrics_pack["confidence_score"],
                            "fillers": metrics_pack["filler_count"],
                        })

                        st.session_state["current_question_audio"] = None

                        if is_last_q:
                            st.session_state["interview_active"] = False
                            st.session_state["interview_complete"] = True

                            consolidated_transcript = ""
                            for i, history_turn in enumerate(st.session_state["interview_history"]):
                                consolidated_transcript += f"""
                                [ROUND {i+1} CHRONOLOGY]
                                Interviewer Prompt: {history_turn['question']}
                                Candidate Vocal Transcription: {history_turn['answer']}
                                Vocal Telemetry: Delivery Fluency {history_turn['score']}%, Stalling Count {history_turn['fillers']}
                                """

                            with st.spinner("Invoking evaluation nodes to execute comprehensive diagnostic aggregation..."):
                                resp = run_candidate_workflow(
                                    resume_text=active_resume_payload,
                                    target_job=st.session_state.get("session_role_title", ""),
                                    job_description=st.session_state.get("session_jd_context", ""),
                                    run_mock=True,
                                    current_question="Comprehensive Conversational Dynamic Interview Assessment Stream",
                                    candidate_answer=consolidated_transcript,
                                )

                                if resp.get("mock_evaluation"):
                                    st.session_state["saved_mock_evaluation"] = resp["mock_evaluation"]
                                    closing_verdict = (
                                        "Your interactive session is complete. The diagnostic execution loop has "
                                        "calculated your technical competencies and delivery metrics. Review the "
                                        "dashboard elements for full optimization tracking details."
                                    )
                                    st.session_state["agent_audio_response"] = generate_agent_speech(closing_verdict)
                        else:
                            with st.spinner("AI Interviewer is analyzing your response to construct a reactive follow-up turn..."):
                                client = Groq(api_key=user_groq_key)

                                chat_mem = [
                                    {
                                        "role": "system",
                                        "content": (
                                            "You are a strict technical interviewer running a live dynamic voice "
                                            "dialogue loop. Target Professional Designation: "
                                            f"{st.session_state.get('session_role_title', 'Software Engineer')}. "
                                            f"Requirement Context Matrix: {st.session_state.get('session_jd_context', '')}. "
                                            f"Candidate Original Profile Blueprint:\n{active_resume_payload}\n\n"
                                            "INSTRUCTIONS: Review the ongoing conversation chronology. Evaluate the "
                                            "user's latest technical statements. Actively follow up by probing deep "
                                            "architectural tradeoffs, pointing out technical gaps, or requesting "
                                            "structural deep dives based exactly on their input text. Maintain a "
                                            "natural, organic conversational flow. Return ONLY the content string "
                                            "of your next question. Avoid label prefixes (e.g. 'Interviewer:') and "
                                            "conversational introductory filler text (e.g. 'Great response, let's "
                                            "shift focus...')."
                                        ),
                                    }
                                ]

                                for turn in st.session_state["interview_history"]:
                                    chat_mem.append({"role": "assistant", "content": turn["question"]})
                                    chat_mem.append({"role": "user", "content": turn["answer"]})

                                chat_completion = client.chat.completions.create(
                                    messages=chat_mem,
                                    model="llama-3.3-70b-versatile",
                                )
                                next_followup_question = chat_completion.choices[0].message.content.strip()

                                st.session_state["current_question_text"] = next_followup_question
                                st.session_state["current_question_idx"] += 1

                        st.rerun()

                    except Exception as error_context:
                        st.error(f"Turn synchronization processing failed: {str(error_context)}")

    elif st.session_state["interview_complete"]:
        st.success("Conversation Session Finished! Complete system evaluations have been compiled successfully.")

        if st.session_state.get("agent_audio_response"):
            st.markdown("### AI Recruiter Closing Verdict Speech")
            st.audio(st.session_state["agent_audio_response"], format="audio/mp3")

        with st.expander("View Spoken Transcription History & Live Telemetry", expanded=True):
            history_table_data = []
            for idx, turn in enumerate(st.session_state["interview_history"]):
                history_table_data.append({
                    "Turn": f"Q{idx+1}",
                    "Question Prompt": turn["question"],
                    "Your Decoded Answer": turn["answer"],
                    "Fluency Rating": f"{turn['score']}%",
                    "Filler Count": turn["fillers"],
                })
            st.dataframe(pd.DataFrame(history_table_data), use_container_width=True)

        if st.session_state.get("saved_mock_evaluation"):
            with st.container():
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown("### Multi-Turn Technical & Presentation Performance Review Matrix")
                st.markdown(st.session_state["saved_mock_evaluation"])
                st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Initialize a Brand New Practice Interview"):
            st.session_state["interview_complete"] = False
            st.session_state["saved_mock_evaluation"] = ""
            st.session_state["agent_audio_response"] = None
            st.rerun()

    st.markdown("---")
    st.subheader("Step 5: Structural Upskilling Roadmap Synthesis")
    render_pipeline_runner(workflow_stages, current_index=4)
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Compile Professional Optimization Trajectory", key="trigger_career_mapping"):
        if check_api_infrastructure():
            with st.spinner("Mapping current competencies against modern architectural standards..."):
                try:
                    resp = run_candidate_workflow(
                        resume_text=active_resume_payload,
                        target_job=st.session_state.get("session_role_title", ""),
                        job_description=st.session_state.get("session_jd_context", ""),
                        run_career=True,
                    )
                    if resp.get("error"):
                        st.error(f"Graph Pipeline Abort Exception: {resp['error']}")
                    elif resp.get("career_guidance"):
                        st.session_state["saved_career_guidance"] = resp["career_guidance"]
                        st.success("Tactical roadmap synthesis completed.")
                except Exception as failure:
                    st.error(f"Critical execution breakdown detected: {str(failure)}")

    if st.session_state.get("saved_career_guidance"):
        with st.container():
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown("### Targeted Development Progression Roadmaps")
            st.markdown(st.session_state["saved_career_guidance"])
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Step 6: High-Impact Profile Optimization Output")
    render_pipeline_runner(workflow_stages, current_index=5)
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Generate Optimized Layout Copy", key="trigger_tailored_generation"):
        if check_api_infrastructure():
            with st.spinner("Restructuring profile expressions matching metric score thresholds..."):
                try:
                    resp = run_candidate_workflow(
                        resume_text=active_resume_payload,
                        target_job=st.session_state.get("session_role_title", ""),
                        job_description=st.session_state.get("session_jd_context", ""),
                        run_resume_generation=True,
                    )
                    if resp.get("error"):
                        st.error(f"Graph Pipeline Abort Exception: {resp['error']}")
                    elif resp.get("tailored_resume"):
                        st.session_state["saved_tailored_resume"] = resp["tailored_resume"]
                        st.success("Targeted markdown layout build compiled successfully.")
                except Exception as failure:
                    st.error(f"Critical execution breakdown detected: {str(failure)}")

    if st.session_state.get("saved_tailored_resume"):
        with st.expander("Examine Optimized Resume Blueprint Code (Markdown)", expanded=True):
            st.code(st.session_state["saved_tailored_resume"], language="markdown")
            st.markdown("---")
            st.markdown(st.session_state["saved_tailored_resume"])
