DeepVerify

Evidence-Grounded AI Research & Fact-Checking System

DeepVerify is an AI-powered research and fact-checking system that researches a user's question using evidence, extracts factual claims, verifies those claims against relevant evidence, and transparently reports the verification results.

Problem

Large Language Models can generate fluent answers containing unsupported or inaccurate factual claims. Users often have to manually search for evidence, compare sources, identify claims, and determine whether the evidence actually supports them.

DeepVerify makes this process systematic and transparent.

Idea

DeepVerify follows an evidence-grounded, claim-level verification workflow:

User Question
      ↓
Research Planning
      ↓
Web / Document Evidence Collection
      ↓
Draft Generation
      ↓
Claim Extraction
      ↓
Claim ↔ Evidence Matching
      ↓
Fact Verification
      ↓
Grounding Score & Transparent Result
      ↓
Evidence Sufficient?
   ↙             ↘
 Yes             No
 ↓                ↓
Final Result   Revision / New Search
                  │
                  └──────→ Evidence Collection

The system reports the verdict, relevant evidence, explanation, verification method, and grounding score for each claim.

Key Features

Research Planning — converts a question into research subtasks.

Web Evidence Acquisition — searches the web using Tavily.

Document Retrieval — retrieves evidence from documents using PyMuPDF.

Draft Generation — uses Gemini to generate research content.

Claim Extraction — identifies factual claims from the draft.

Claim–Evidence Matching — selects relevant evidence for each claim using relevance and evidence confidence.

LLM Fact Checking — verifies claims using Gemini.

Deterministic Fallback — provides graceful degradation if LLM verification fails.

Transparent Results — reports verdict, evidence, explanation, verification method, and grounding score.

Iterative Research — can perform additional research when evidence is insufficient.

Live Research Activity — uses Server-Sent Events (SSE) for progress updates.

Claim Verdicts

Verdict

Meaning

supported

Available evidence supports the claim.

refuted

Available evidence contradicts the claim.

inconclusive

Evidence exists, but it is insufficient to confidently determine support or refutation.

unverifiable

There is not enough usable evidence to verify the claim.

Verification Methods

LLM: Gemini evaluates the claim against selected evidence.

Deterministic fallback: Uses textual relevance and evidence confidence when LLM verification fails. It deliberately avoids making an unsupported support/refute decision.

Note: The grounding score measures how strongly a claim is grounded in available evidence. It is not a probability that the claim is true.

System Architecture

                         ┌──────────────────┐
                         │    User / UI     │
                         └────────┬─────────┘
                                  ↓
                         ┌──────────────────┐
                         │ Research Planner │
                         └────────┬─────────┘
                                  ↓
                    ┌──────────────────────────┐
                    │   Evidence Acquisition   │
                    │                          │
                    │  Tavily Web Search       │
                    │  PyMuPDF Document Search  │
                    └────────────┬─────────────┘
                                 ↓
                         ┌──────────────────┐
                         │  Evidence Store  │
                         │ Excerpts         │
                         │ Sources          │
                         │ Confidence       │
                         └────────┬─────────┘
                                  ↓
                         ┌──────────────────┐
                         │ Draft Generation │
                         │    Gemini LLM    │
                         └────────┬─────────┘
                                  ↓
                         ┌──────────────────┐
                         │ Claim Extraction │
                         └────────┬─────────┘
                                  ↓
                    ┌──────────────────────────┐
                    │ Claim ↔ Evidence Matching│
                    └────────────┬─────────────┘
                                 ↓
                     ┌────────────────────────┐
                     │   Fact Verification    │
                     │                        │
                     │ Gemini LLM Checker     │
                     │          ↓             │
                     │ Deterministic Fallback │
                     └────────────┬───────────┘
                                  ↓
                     ┌────────────────────────┐
                     │ Verification Result     │
                     │ Verdict                 │
                     │ Evidence                │
                     │ Explanation             │
                     │ Verification Method     │
                     │ Grounding Score         │
                     └────────────┬───────────┘
                                  ↓
                           ┌────────────┐
                           │ Grounding  │
                           │   Check    │
                           └─────┬──────┘
                            YES  │  NO
                             ↓   ↓
                         Final   Revision /
                         Result  New Search
                                  │
                                  └──────→ Evidence

Technology Stack

Frontend

Next.js

React

TypeScript

Backend

Python

FastAPI

Pydantic

AI

Google Gemini

Research & Retrieval

Tavily Web Search

PyMuPDF

Communication

REST API

Server-Sent Events (SSE)

Testing

Pytest

Project Structure

DeepVerify/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── fact_checker.py
│   │   │   └── llm_fact_checker.py
│   │   ├── core/
│   │   │   └── models.py
│   │   └── graph/
│   │       ├── nodes/
│   │       │   └── fact_checker.py
│   │       └── state.py
│   └── tests/
│       ├── test_fact_checker.py
│       ├── test_fact_checking_quality.py
│       ├── test_llm_fact_checker.py
│       ├── test_graph_runner.py
│       └── ...
├── frontend/
│   ├── app/
│   │   └── page.tsx
│   ├── components/
│   ├── types/
│   │   └── research.ts
│   └── lib/
│       └── formatters.ts
└── README.md

API

Start a Research Run

POST /research

{
  "question": "Your research question"
}

Get Research Result

GET /research/{run_id}

Research Events

GET /research/{run_id}/events

The events endpoint provides live research progress through SSE.

Running the Project

Backend

From the backend directory, activate the project's Python environment, install the required dependencies, configure the required environment variables, and start the FastAPI application using the project's configured entry point.

Required external services include the Gemini API and Tavily API for live research and LLM-based verification.

Frontend

cd frontend
npm install
npm run dev

The frontend communicates with the local backend API.

Testing

Run the backend test suite:

cd backend
python -m pytest

The current implementation has been validated with 106 passing tests.

Tests cover deterministic and LLM fact checking, supported/refuted/inconclusive/unverifiable outcomes, evidence selection, verification methods, explanations, and graph/workflow integration.

Example Workflow

Question
   ↓
Research Plan
   ↓
Evidence Collection
   ↓
Draft Generation
   ↓
Claim Extraction
   ↓
Claim–Evidence Matching
   ↓
Fact Verification
   ↓
Grounding Check
   ↓
Final Transparent Result

If evidence is insufficient, DeepVerify can generate revision queries and perform additional research before re-verification.

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

The focus is therefore on claim-level evidence grounding and transparency, rather than only generating a fluent answer.

Current Limitations

Verification quality depends on the quality and coverage of retrieved evidence.

Conflicting or ambiguous sources can result in an inconclusive verdict.

LLM-based verification can still make mistakes.

The deterministic fallback is a graceful-degradation mechanism, not a complete replacement for semantic fact checking.

Grounding score should be interpreted as an evidence-grounding measure, not a calibrated truth probability.

Future Enhancements

Evidence-to-Claim Traceability — explicit path from claim → evidence → source → verification method → verdict.

Source Quality & Ranking — improved assessment and ranking of source reliability.

Improved Atomic Claim Extraction — break complex statements into independently verifiable claims.

Source Diversity & Contradiction Detection — identify disagreements between sources.

Research History & Run Comparison — compare research runs and evidence evolution.

Confidence Calibration — improve the interpretation and consistency of grounding scores.

Repository

DeepVerify on GitHub

Project Status

DeepVerify currently includes:

Research planning

Web and document evidence acquisition

Evidence representation

LLM-based draft generation

Claim extraction

Claim–evidence matching

LLM fact checking

Deterministic fallback verification

Claim-level verdicts

Evidence and explanation reporting

Verification method reporting

Grounding score

Iterative research/revision

Live research activity through SSE

Automated backend testing

License

Add the project's chosen license here before public release.
