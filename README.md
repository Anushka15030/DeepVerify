<div align="center">

DeepVerify

Evidence-Grounded AI Research & Fact-Checking System

An AI-powered research system that researches questions, collects evidence, extracts factual claims, verifies them against relevant evidence, and transparently reports the results.

<p>
  <a href="https://github.com/Anushka15030/DeepVerify">
    <img src="https://img.shields.io/badge/Project-DeepVerify-blue?style=for-the-badge" alt="DeepVerify">
  </a>
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Next.js-Frontend-000000?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js">
  <img src="https://img.shields.io/badge/Gemini-LLM-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini">
</p>

</div>

Table of Contents

Overview

Problem

Idea & Proposed Solution

Key Features

System Architecture

Technology Stack

Project Structure

How It Works

API

Claim Verification

Grounding Score

Iterative Research

Running the Project

Testing

What Makes DeepVerify Different?

Current Limitations

Future Enhancements

Project Status

Repository

License

Overview

DeepVerify is an evidence-grounded AI research and fact-checking system.

Instead of treating an LLM-generated answer as the final output, DeepVerify introduces a research and verification layer that:

Plans the research.

Collects evidence from available sources.

Generates a research draft.

Extracts factual claims.

Matches claims with relevant evidence.

Verifies claims.

Reports the verdict, evidence, explanation, verification method, and grounding score.

Performs additional research when the available evidence is insufficient.

Core principle: Move from "the AI says this is true" to "the AI shows the evidence behind this claim."

Problem

Large Language Models can generate fluent and convincing answers that contain:

Unsupported factual claims

Inaccurate information

Weakly grounded conclusions

Claims whose supporting evidence is unclear

Users often have to manually search for evidence, compare sources, identify factual statements, and decide whether the evidence actually supports those statements.

DeepVerify is designed to make this process systematic, claim-level, evidence-grounded, and transparent.

Idea & Proposed Solution

DeepVerify follows an evidence-grounded research workflow:

User Question
      │
      ▼
Research Planning
      │
      ▼
Web / Document Evidence Collection
      │
      ▼
Draft Generation
      │
      ▼
Claim Extraction
      │
      ▼
Claim ↔ Evidence Matching
      │
      ▼
Fact Verification
      │
      ▼
Grounding Check
   ┌──┴───────────────┐
   │                  │
  YES                 NO
   │                  │
   ▼                  ▼
Final Result     Revision / New Search
                       │
                       └──────► Evidence Collection

The final result is designed to show not only what the system concluded, but also why it reached that conclusion.

Key Features

🔎 Research Planning

Breaks the user's question into research subtasks.

🌐 Web Evidence Acquisition

Uses Tavily to retrieve relevant web evidence.

📄 Document Retrieval

Uses PyMuPDF for document-based evidence retrieval.

🤖 LLM-Powered Research

Uses Gemini for draft generation and LLM-based fact checking.

🧩 Claim Extraction

Extracts factual claims from generated research content.

🔗 Claim–Evidence Matching

Selects evidence relevant to each claim using evidence relevance and confidence.

✅ Claim-Level Fact Checking

Supports:

supported

refuted

inconclusive

unverifiable

🛡️ Deterministic Fallback

If LLM verification fails, DeepVerify falls back to a deterministic verification mechanism instead of failing the complete workflow.

📊 Transparent Verification

Each claim can report:

Verdict

Relevant evidence

Explanation

Verification method

Grounding score

🔄 Iterative Research

If the evidence is insufficient, DeepVerify can perform additional research and re-verify the claims.

📡 Live Research Activity

Uses Server-Sent Events (SSE) to stream research progress to the frontend.

System Architecture

                               ┌──────────────────┐
                               │    User / UI     │
                               └────────┬─────────┘
                                        │
                                        ▼
                               ┌──────────────────┐
                               │ Research Planner │
                               └────────┬─────────┘
                                        │
                                        ▼
                     ┌────────────────────────────────┐
                     │      Evidence Acquisition      │
                     │                                │
                     │  ┌────────────┐ ┌────────────┐ │
                     │  │   Tavily   │ │  PyMuPDF   │ │
                     │  │ Web Search │ │  Retrieval │ │
                     │  └─────┬──────┘ └─────┬──────┘ │
                     └────────┼───────────────┼────────┘
                              │               │
                              └───────┬───────┘
                                      ▼
                              ┌──────────────────┐
                              │  Evidence Store  │
                              │                  │
                              │ Excerpts         │
                              │ Sources          │
                              │ Confidence       │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │ Draft Generation │
                              │    Gemini LLM    │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │ Claim Extraction │
                              └────────┬─────────┘
                                       │
                                       ▼
                         ┌────────────────────────────┐
                         │  Claim ↔ Evidence Matching│
                         └──────────────┬─────────────┘
                                        │
                                        ▼
                         ┌────────────────────────────┐
                         │     Fact Verification      │
                         │                            │
                         │  Gemini LLM Fact Checker   │
                         │            │               │
                         │         failure            │
                         │            ▼               │
                         │ Deterministic Fallback    │
                         └──────────────┬─────────────┘
                                        │
                                        ▼
                         ┌────────────────────────────┐
                         │    Verification Result     │
                         │                            │
                         │ Verdict                    │
                         │ Evidence                   │
                         │ Explanation                │
                         │ Verification Method        │
                         │ Grounding Score            │
                         └──────────────┬─────────────┘
                                        │
                                        ▼
                                  ┌────────────┐
                                  │ Grounding  │
                                  │   Check    │
                                  └─────┬──────┘
                                   YES │  NO
                                       │
                         ┌─────────────┘ └───────────────┐
                         ▼                               ▼
                  ┌──────────────┐              ┌─────────────────┐
                  │ Final Result │              │ Revision / New │
                  │    → User    │              │ Search Queries │
                  └──────────────┘              └────────┬────────┘
                                                          │
                                                          └──► Evidence

Technology Stack

Layer

Technology

Frontend

Next.js, React, TypeScript

Backend

Python, FastAPI, Pydantic

AI / LLM

Google Gemini

Web Research

Tavily

Document Retrieval

PyMuPDF

Communication

REST API, Server-Sent Events (SSE)

Testing

Pytest

Project Structure

DeepVerify/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── fact_checker.py
│   │   │   └── llm_fact_checker.py
│   │   │
│   │   ├── core/
│   │   │   └── models.py
│   │   │
│   │   └── graph/
│   │       ├── nodes/
│   │       │   └── fact_checker.py
│   │       └── state.py
│   │
│   └── tests/
│       ├── test_fact_checker.py
│       ├── test_fact_checking_quality.py
│       ├── test_llm_fact_checker.py
│       ├── test_graph_runner.py
│       └── ...
│
├── frontend/
│   ├── app/
│   │   └── page.tsx
│   ├── components/
│   │   ├── AgentCard.tsx
│   │   ├── AgentActivity.tsx
│   │   ├── ResearchActivity.tsx
│   │   ├── ResearchPlan.tsx
│   │   ├── ClaimsSection.tsx
│   │   ├── EvidenceSection.tsx
│   │   └── ResearchResults.tsx
│   ├── types/
│   │   └── research.ts
│   └── lib/
│       └── formatters.ts
│
└── README.md

How It Works

1. Research Planning

The user's question is converted into a set of research subtasks.

2. Evidence Collection

The system gathers evidence through web search and document retrieval.

3. Draft Generation

Gemini uses the collected evidence to generate research content.

4. Claim Extraction

The system identifies factual claims from the draft.

5. Claim–Evidence Matching

Each claim is compared with available evidence and relevant evidence is selected.

6. Fact Verification

The selected evidence is passed to the LLM fact checker.

If LLM verification fails, the deterministic fallback is used.

7. Grounding Check

The system calculates the overall grounding of the verified claims and determines whether more research is necessary.

8. Final Result

The final result exposes claim-level verification information rather than presenting an unsupported answer alone.

API

Start a Research Run

POST /research

Request:

{
  "question": "What are the major causes and impacts of climate change?"
}

Get Research Result

GET /research/{run_id}

Returns the current/final research state.

Research Events

GET /research/{run_id}/events

Streams live research events using Server-Sent Events (SSE).

Claim Verification

DeepVerify uses four claim verdicts:

Verdict

Meaning

supported

Available evidence supports the claim.

refuted

Available evidence contradicts the claim.

inconclusive

Evidence is available, but it is insufficient to confidently determine support or refutation.

unverifiable

There is not enough usable evidence to verify the claim.

Verification Methods

LLM Verification

Gemini evaluates the claim against the selected evidence and returns a structured verification result.

Deterministic Fallback

When LLM verification fails, the deterministic fallback:

Filters usable evidence.

Measures textual relevance between the claim and evidence.

Selects relevant evidence.

Uses evidence confidence to calculate grounding.

Returns an inconclusive result rather than making an unsupported support/refute decision.

This provides graceful degradation when the LLM verification layer is unavailable or fails.

Grounding Score

The grounding score represents how strongly the claim is grounded in the evidence available to the system.

It is useful for understanding evidence coverage and verification strength.

Important: The grounding score is not a probability of truth and should not be interpreted as "there is an X% probability that the claim is true."

Iterative Research

DeepVerify can perform additional research when the available evidence is insufficient.

Initial Research
       │
       ▼
Evidence Collection
       │
       ▼
Claim Verification
       │
       ▼
Grounding Check
       │
       ▼
Insufficient Evidence
       │
       ▼
Revision Queries
       │
       ▼
Additional Research
       │
       ▼
Updated Evidence
       │
       ▼
Re-verification

This allows the system to improve evidence coverage before producing the final result.

Running the Project

The exact commands for starting the backend should follow the project's configured FastAPI entry point and environment setup.

1. Clone the Repository

git clone https://github.com/Anushka15030/DeepVerify.git
cd DeepVerify

2. Backend

Navigate to the backend:

cd backend

Create/activate the project's Python environment, install the required dependencies, and configure the required environment variables for Gemini and Tavily.

Start the FastAPI application using the project's configured entry point.

3. Frontend

From the frontend directory:

cd frontend
npm install
npm run dev

The frontend communicates with the local backend API.

Environment Variables

Configure the required API credentials before using live research features.

Example:

GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key

Keep API keys private and never commit them to GitHub.

Testing

Run the backend test suite:

cd backend
python -m pytest

Current Test Status

106 tests passing

The test suite covers:

Deterministic fact checking

LLM fact checking

Supported claims

Refuted claims

Inconclusive claims

Unverifiable claims

Evidence selection

Verification method reporting

Explanations

Graph/workflow integration

What Makes DeepVerify Different?

A conventional AI workflow can look like:

Question → LLM → Answer

DeepVerify instead follows:

Question
   ↓
Research
   ↓
Evidence
   ↓
Claims
   ↓
Claim ↔ Evidence
   ↓
Verification
   ↓
Verdict + Evidence + Explanation

The system is therefore focused on claim-level evidence grounding and transparency, rather than simply generating a fluent answer.

Current Limitations

Verification quality depends on the quality and coverage of retrieved evidence.

Conflicting or ambiguous sources can result in an inconclusive verdict.

LLM-based verification can still make mistakes.

The deterministic fallback is a graceful-degradation mechanism, not a complete replacement for semantic fact checking.

Grounding score should be interpreted as an evidence-grounding measure, not a calibrated probability of truth.

Future Enhancements

The planned roadmap includes:

1. Evidence-to-Claim Traceability

Explicit audit path:

Claim
  ↓
Evidence
  ↓
Source
  ↓
Verification Method
  ↓
Verdict

2. Source Quality & Ranking

Improve assessment and ranking of source reliability.

3. Improved Atomic Claim Extraction

Break complex statements into smaller independently verifiable claims.

4. Source Diversity & Contradiction Detection

Identify disagreements and relationships between sources.

5. Research History & Run Comparison

Compare research runs and evidence evolution.

6. Confidence Calibration

Improve the interpretation and consistency of grounding scores.

Project Status

Implemented

Research planning

Web evidence acquisition

Document retrieval

Evidence representation

LLM-based draft generation

Claim extraction

Claim–evidence matching

LLM fact checking

Deterministic fallback verification

Claim-level verdicts

Evidence reporting

Explanation reporting

Verification method reporting

Grounding score

Iterative research/revision

Live research activity through SSE

Automated backend testing

Planned

Evidence-to-claim traceability

Source quality & ranking

Advanced contradiction detection

Research history and run comparison

Confidence calibration

Repository

<p align="center">

<a href="https://github.com/Anushka15030/DeepVerify">
  <img src="https://img.shields.io/badge/GitHub-DeepVerify-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
</a>

</p>

Repository:
https://github.com/Anushka15030/DeepVerify

License

Add the project's chosen license here before public release.

<div align="center">

Research. Verify. Understand.

DeepVerify

</div>
