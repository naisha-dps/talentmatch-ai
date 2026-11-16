# =============================================================
# ui/recruiter_portal.py
# TalentMatch AI - Recruiter Workspace (Resume Ranking, Candidate
# Comparison, Job Description Matching, Batch Resume Processing, Leaderboard)
# =============================================================
import asyncio
import inspect
import io
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import streamlit as st
from openpyxl.utils import get_column_letter

from graph.candidate_graph import run_candidate_workflow
from utils.file_parser import extract_texts_from_zip, parse_resume_file
from ui.workspace_helpers import check_api_infrastructure, parse_score_metrics

# Score thresholds shared by the on-screen shortlist labels and the Excel export
HIGH_MATCH_THRESHOLD = 80
SHORTLIST_THRESHOLD = 60

# Batch Processing Cap choices offered in the UI, mapped to an actual candidate
# count (None = "Process All"). Capping keeps large ZIP archives (100+ files)
# from firing off more Groq calls in one run than the account's rate limit allows.
BATCH_CAP_OPTIONS = {"10": 10, "20 (Default)": 20, "50": 50, "100": 100, "Process All": None}

# Retry/backoff tuning for individual LLM calls against the reasoning graph
MAX_WORKFLOW_RETRIES = 3
RETRY_BASE_DELAY_SECONDS = 1.0
INTER_FILE_DELAY_SECONDS = 0.5


def _snippet_for_terms(report_text: str, terms: list, default: str) -> str:
    """Pulls the first line matching any of `terms` out of a report, trimmed for display."""
    for log_line in report_text.split("\n"):
        if any(term in log_line.lower() for term in terms):
            return log_line.strip("- *#").split(":")[-1].strip()[:70] + "..."
    return default


def _shortlist_status_for_score(score: int) -> str:
    if score >= HIGH_MATCH_THRESHOLD:
        return "High Potential (>=80%)"
    if score >= SHORTLIST_THRESHOLD:
        return "Potential Match (60-79%)"
    return "Gaps Identified (<60%)"


def _invoke_candidate_workflow(extracted_file_text: str, recruiter_jd_spec: str) -> str:
    """Runs the (possibly async) reasoning graph exactly once and returns the report text.

    `run_candidate_workflow` catches its own internal exceptions (API errors, timeouts,
    auth failures, ...) and returns them as {"error": "..."} instead of raising - a
    "successful" call with no `analysis_report` key. Left unchecked, that silently
    collapses to an empty string here, which means the retry/backoff wrapper never
    sees an exception to retry on, and the caller's failure log ends up with no idea
    why the call actually failed. Re-raising the embedded error restores both: retries
    fire, and the real API/JSON error message reaches the "Skipping ..." log line.
    """
    if inspect.iscoroutinefunction(run_candidate_workflow):
        with ThreadPoolExecutor() as executor:
            evaluation_output = executor.submit(lambda: asyncio.run(run_candidate_workflow(
                resume_text=extracted_file_text,
                target_job="Enterprise Position Candidate Evaluation",
                job_description=recruiter_jd_spec,
                run_analysis=True
            ))).result()
    else:
        evaluation_output = run_candidate_workflow(
            resume_text=extracted_file_text,
            target_job="Enterprise Position Candidate Evaluation",
            job_description=recruiter_jd_spec,
            run_analysis=True
        )

    if isinstance(evaluation_output, dict) and evaluation_output.get("error"):
        raise RuntimeError(evaluation_output["error"])

    if isinstance(evaluation_output, str):
        return evaluation_output
    if isinstance(evaluation_output, dict):
        return evaluation_output.get("analysis_report", "")
    return ""


def _invoke_candidate_workflow_with_retry(extracted_file_text: str, recruiter_jd_spec: str) -> str:
    """Wraps `_invoke_candidate_workflow` with exponential backoff so a transient Groq
    rate-limit/timeout on one candidate doesn't need to fail the whole batch. Re-raises
    the last exception once retries are exhausted, letting the caller decide to skip."""
    last_exception = None
    for attempt in range(MAX_WORKFLOW_RETRIES):
        try:
            return _invoke_candidate_workflow(extracted_file_text, recruiter_jd_spec)
        except Exception as workflow_ex:
            last_exception = workflow_ex
            if attempt < MAX_WORKFLOW_RETRIES - 1:
                time.sleep(RETRY_BASE_DELAY_SECONDS * (2 ** attempt))
    raise last_exception


def _build_excel_report(recruiter_dataframe: pd.DataFrame, total_ingested: int) -> bytes:
    """Compiles the full batch run into a two-sheet, in-memory .xlsx workbook."""
    export_df = recruiter_dataframe.rename(columns={
        "Candidate Profile": "Candidate Name",
        "Match Score": "Match Score (%)",
        "Shortlist Status": "Shortlist Status",
        "Primary Strength Highlight": "Primary Strengths",
        "Isolated Core Gaps": "Critical Skill Gaps",
        "Key Experience Summary": "Key Experience Summary",
        "Comprehensive Report Content": "Detailed Analysis",
    })[[
        "Candidate Name", "File Name", "Match Score (%)", "Shortlist Status",
        "Primary Strengths", "Critical Skill Gaps", "Key Experience Summary", "Detailed Analysis",
    ]]

    shortlisted_count = int((recruiter_dataframe["Match Score"] >= SHORTLIST_THRESHOLD).sum())
    high_match_count = int((recruiter_dataframe["Match Score"] >= HIGH_MATCH_THRESHOLD).sum())
    average_score = float(recruiter_dataframe["Match Score"].mean()) if not recruiter_dataframe.empty else 0.0

    summary_df = pd.DataFrame({
        "Metric": [
            "Total Resumes Ingested",
            "Shortlisted Count (Useful Resumes >= 60%)",
            "High Match Count (>= 80%)",
            "Average Match Score (%)",
        ],
        "Value": [
            total_ingested,
            shortlisted_count,
            high_match_count,
            round(average_score, 2),
        ],
    })

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        export_df.to_excel(writer, sheet_name="Candidate Leaderboard & Matrix", index=False)
        summary_df.to_excel(writer, sheet_name="Executive Summary Metrics", index=False)

        for sheet_name, frame in (
            ("Candidate Leaderboard & Matrix", export_df),
            ("Executive Summary Metrics", summary_df),
        ):
            worksheet = writer.sheets[sheet_name]
            for col_idx, column_name in enumerate(frame.columns, start=1):
                max_content_len = max(
                    [len(str(column_name))] + [len(str(v)) for v in frame[column_name].astype(str)]
                )
                worksheet.column_dimensions[get_column_letter(col_idx)].width = min(max_content_len + 4, 60)

    return excel_buffer.getvalue()


def render_recruiter_portal() -> None:
    """Renders the full Recruiter workspace: batch resume upload, job description
    matching, ranked leaderboard, and per-candidate diagnostic reports."""

    st.markdown(
        '<div class="section-header">Recruiter Portal &mdash; Comparative Batch Evaluation Pipeline</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "Ingest a series of applicant vectors simultaneously to calculate core competency scores, "
        "rank candidate standings, and isolate background deficits."
    )
    st.markdown("<br>", unsafe_allow_html=True)

    col_r1, col_r2 = st.columns(2)

    with col_r1:
        st.markdown("### Candidate Resume Profiles Channel Ingest")
        batch_uploaded_files = st.file_uploader(
            "Upload Candidate Resumes (PDF, DOCX, CSV, or a ZIP archive of these):",
            type=["pdf", "docx", "csv", "zip"],
            accept_multiple_files=True,
            help="Drop individual applicant PDF/DOCX/CSV files and/or a single ZIP archive bundling multiple candidate files (any mix of PDF, DOCX, CSV) to parse concurrently against requirement matrices. Each CSV row is treated as a separate candidate.",
            key="recruiter_batch_input",
        )

    with col_r2:
        st.markdown("### Core Requirement Specification Matrix")
        recruiter_jd_spec = st.text_area(
            "Target Job Posting Parameters:",
            placeholder="Provide targeted operational roles, required structural technology competencies, database frameworks, and background requirements here...",
            height=180,
            key="recruiter_jd_context",
        )

    st.markdown("---")
    cap_col, cutoff_col = st.columns(2)
    with cap_col:
        st.markdown("### Batch Processing Cap")
        batch_cap_choice = st.selectbox(
            "Maximum candidates to process per run:",
            options=list(BATCH_CAP_OPTIONS.keys()),
            index=1,
            help="Caps how many ingested candidate records are sent through the AI reasoning pipeline in a single run, so large ZIP archives (100+ files) don't blow past Groq API rate limits. Re-run to process the remainder, or choose 'Process All'.",
            key="recruiter_batch_cap_choice",
        )
        batch_processing_cap = BATCH_CAP_OPTIONS[batch_cap_choice]
    with cutoff_col:
        st.markdown("### Live Dynamic Filtering Safeguard Threshold")
        live_score_cutoff = st.slider("Minimum Competency Core Affinity Threshold Score (%)", min_value=0, max_value=100, value=60)
    st.markdown("<br>", unsafe_allow_html=True)

    execute_batch = st.button("Execute Batch Talent Assessment Process", type="primary", use_container_width=True)

    if execute_batch:
        if not batch_uploaded_files or not recruiter_jd_spec.strip():
            st.warning("Awaiting Processing Criteria: Please feed candidate profile bundles and target requirement scripts.")
        elif check_api_infrastructure():
            st.session_state["recruiter_logs"] = []
            st.session_state["recruiter_run_executed"] = True
            # Reset incrementally-populated results now, at the start of the run, so that
            # every successful candidate evaluation below can be appended straight into
            # session_state as it completes - a crash or rate-limit wall partway through
            # the batch still leaves prior candidates rendered in the leaderboard below.
            st.session_state["cached_recruiter_run_data"] = []

            st.session_state["recruiter_logs"].append("**Initializing Core Processing Engine Pipeline...**")

            # Stage 1: flatten every uploaded source (loose PDF/DOCX/CSV files and/or
            # ZIP archives bundling a mix of these) into a single (file_name,
            # extracted_text) worklist, entirely in memory - no extracted file is
            # ever written to disk. A single CSV upload can expand into multiple
            # candidate records, one per row.
            resume_payloads = []

            for current_target_file in batch_uploaded_files:
                if current_target_file.name.lower().endswith(".zip"):
                    st.session_state["recruiter_logs"].append(f"*Unpacking ZIP archive:* `{current_target_file.name}`")
                    try:
                        current_target_file.seek(0)
                        zip_entries = extract_texts_from_zip(current_target_file)
                        if not zip_entries:
                            st.session_state["recruiter_logs"].append(f"*No supported resume files (PDF/DOCX/CSV) found inside* `{current_target_file.name}`")
                        else:
                            st.session_state["recruiter_logs"].append(f"*Extracted {len(zip_entries)} candidate record(s) from* `{current_target_file.name}`")
                        resume_payloads.extend(zip_entries)
                    except Exception as zip_ex:
                        st.session_state["recruiter_logs"].append(f"*Archive extraction failed for* `{current_target_file.name}`: {str(zip_ex)}")
                    continue

                st.session_state["recruiter_logs"].append(f"*Reading binary stream:* `{current_target_file.name}`")
                try:
                    current_target_file.seek(0)
                    file_entries = parse_resume_file(current_target_file, current_target_file.name)
                    resume_payloads.extend(file_entries)
                except Exception as parse_ex:
                    st.session_state["recruiter_logs"].append(f"*Parser crash on* `{current_target_file.name}`: {str(parse_ex)}")

            total_ingested_from_files = len(resume_payloads)

            # Enforce the Batch Processing Cap: only the first N ingested records are
            # actually sent to the LLM this run, so a 100+ file ZIP can't blow through
            # the Groq rate limit in one shot. Re-running (or choosing "Process All")
            # covers the remainder.
            if batch_processing_cap is not None and total_ingested_from_files > batch_processing_cap:
                st.session_state["recruiter_logs"].append(
                    f"*Batch Processing Cap active:* processing {batch_processing_cap} of "
                    f"{total_ingested_from_files} ingested candidate record(s) this run. "
                    f"Re-run (or select 'Process All') to cover the remainder."
                )
                resume_payloads = resume_payloads[:batch_processing_cap]

            total_resumes_ingested = len(resume_payloads)
            st.session_state["cached_recruiter_total_ingested"] = total_resumes_ingested

            # Stage 2: run the AI reasoning graph against every extracted resume. Each
            # successful evaluation is appended to session_state immediately so the
            # leaderboard below always reflects everything completed so far, even if a
            # later file in the batch fails outright or the run is interrupted.
            for payload_file_name, extracted_file_text in resume_payloads:
                extracted_char_count = len(extracted_file_text) if extracted_file_text else 0

                if not extracted_file_text or not extracted_file_text.strip():
                    st.session_state["recruiter_logs"].append(
                        f"❌ Parser returned 0 characters for `{payload_file_name}`. Skipping LLM call."
                    )
                    continue

                st.session_state["recruiter_logs"].append(
                    f"📄 Extracted {extracted_char_count} characters from `{payload_file_name}`. Invoking AI Reasoning Node..."
                )

                try:
                    target_report_text = _invoke_candidate_workflow_with_retry(extracted_file_text, recruiter_jd_spec)

                    if target_report_text:
                        calculated_score_index = parse_score_metrics(target_report_text)
                        humanized_cand_name = payload_file_name.rsplit(".", 1)[0].replace("_", " ").title()

                        core_strengths = _snippet_for_terms(
                            target_report_text, ["strength", "meets", "match"],
                            "Competency metrics align well with requirements.",
                        )
                        key_gaps = _snippet_for_terms(
                            target_report_text, ["gap", "missing", "omission"],
                            "Review deep-dive logs below.",
                        )
                        key_experience = _snippet_for_terms(
                            target_report_text, ["experience", "background", "history"],
                            "See detailed analysis for the full experience summary.",
                        )

                        st.session_state["cached_recruiter_run_data"].append({
                            "Candidate Profile": humanized_cand_name,
                            "File Name": payload_file_name,
                            "Match Score": calculated_score_index,
                            "Shortlist Status": _shortlist_status_for_score(calculated_score_index),
                            "Primary Strength Highlight": core_strengths,
                            "Isolated Core Gaps": key_gaps,
                            "Key Experience Summary": key_experience,
                            "Comprehensive Report Content": target_report_text
                        })
                        st.session_state["recruiter_logs"].append(f"*Successfully mapped:* `{payload_file_name}` (Calculated Fit: {calculated_score_index}%)")
                    else:
                        st.session_state["recruiter_logs"].append(f"*Graph Schema Mismatch:* No valid text returned for `{payload_file_name}`.")

                except Exception as graph_ex:
                    st.session_state["recruiter_logs"].append(
                        f"⚠️ Skipping `{payload_file_name}` due to API rate limit/timeout: {str(graph_ex)}"
                    )

                # Brief pause between candidates to stay clear of the Groq rate limit,
                # even on a run of consecutive successes.
                time.sleep(INTER_FILE_DELAY_SECONDS)

            st.session_state["recruiter_logs"].append("**Batch execution sequence finished.**")

    if st.session_state.get("recruiter_run_executed") and isinstance(st.session_state.get("recruiter_logs"), list):
        with st.expander("System Pipeline Processing Console Logs", expanded=True):
            for log_entry in st.session_state["recruiter_logs"]:
                st.markdown(log_entry)

    if st.session_state.get("cached_recruiter_run_data"):
        recruiter_dataframe = pd.DataFrame(st.session_state["cached_recruiter_run_data"])
        recruiter_dataframe = recruiter_dataframe.sort_values(by="Match Score", ascending=False).reset_index(drop=True)
        filtered_recruiter_df = recruiter_dataframe[recruiter_dataframe["Match Score"] >= live_score_cutoff]

        total_resumes_ingested = st.session_state.get("cached_recruiter_total_ingested", len(recruiter_dataframe))
        useful_resumes_count = int((recruiter_dataframe["Match Score"] >= SHORTLIST_THRESHOLD).sum())
        useful_resumes_pct = (useful_resumes_count / total_resumes_ingested * 100) if total_resumes_ingested else 0.0

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Structural Compatibility Standings Leaderboard Matrix")

        metric_col, download_col = st.columns([2, 1])
        with metric_col:
            st.metric(
                "Useful Resumes Found",
                f"{useful_resumes_count} / {total_resumes_ingested} Candidates ({useful_resumes_pct:.1f}%)",
            )
        with download_col:
            st.markdown("<div style='margin-top: 1.7rem;'></div>", unsafe_allow_html=True)
            excel_report_bytes = _build_excel_report(recruiter_dataframe, total_resumes_ingested)
            st.download_button(
                label="Download Full Excel Report (.xlsx)",
                data=excel_report_bytes,
                file_name="talentmatch_batch_assessment_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="recruiter_excel_download",
            )

        if filtered_recruiter_df.empty:
            st.warning("No parsed candidates match your current slider score threshold filters.")
        else:
            st.data_editor(
                filtered_recruiter_df[["Candidate Profile", "Match Score", "Primary Strength Highlight", "Isolated Core Gaps"]],
                use_container_width=True,
                disabled=True,
                column_config={
                    "Match Score": st.column_config.ProgressColumn(
                        "Match Strength Index",
                        format="%d%%",
                        min_value=0,
                        max_value=100,
                    )
                },
                key="live_batch_leaderboard_viewer"
            )

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### Full Structural Alignment Diagnostic Logs Repositories")
            for idx, row_data in filtered_recruiter_df.iterrows():
                with st.expander(f"{row_data['Candidate Profile']} — Core Score Weight: {row_data['Match Score']}%"):
                    st.markdown(row_data["Comprehensive Report Content"])

    elif st.session_state.get("recruiter_run_executed"):
        st.error("**Empty Analysis Deficit:** The batch engine finished running but zero records were processed successfully.")
    else:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("Dashboard Standby: Input analysis variables above and click 'Execute Batch Talent Assessment Process' to generate results.")
