"use client";

import { useState } from "react";

import type {
  AgentStatus,
  ResearchEvent,
  ResearchResult,
} from "@/types/research";

import { formatAgentName, formatEventType, getEventStyle } from "@/lib/formatters";

import AgentActivity from "@/components/AgentActivity";
import ResearchResults from "@/components/ResearchResults";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [question, setQuestion] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [loading, setLoading] = useState(false);
  const [runId, setRunId] = useState<string | null>(null);
  const [error, setError] = useState("");

  const [events, setEvents] = useState<ResearchEvent[]>([]);

  const [result, setResult] = useState<ResearchResult | null>(null);
  const [resultLoading, setResultLoading] = useState(false);
  const [resultError, setResultError] = useState("");

  /*
   * Determine the current state of each research agent
   * from the actual event sequence produced by the backend.
   */
  const getAgentStatus = (
    agent: string,
    events: ResearchEvent[],
    loading: boolean,
  ): AgentStatus => {
    if (!events.length) {
      return "waiting";
    }

    if (
      events.some(
        (event) => event.type === "run_completed",
      )
    ) {
      return "completed";
    }

    const completedAgents = new Set<string>();

    let activeAgent: string | null = null;

    const completeActiveAgent = () => {
      if (activeAgent) {
        completedAgents.add(activeAgent);
      }
    };

    for (const event of events) {
      switch (event.type) {
        case "plan_created":
          completeActiveAgent();
          activeAgent = "planner";
          break;

        case "search_started": {
          const searchAgent = event.payload?.agent;

          completeActiveAgent();

          if (searchAgent === "document_researcher") {
            activeAgent = "document_researcher";
          }

          if (searchAgent === "web_researcher") {
            activeAgent = "web_researcher";
          }

          break;
        }

        case "search_completed": {
          const searchAgent = event.payload?.agent;

          if (searchAgent === "document_researcher") {
            completedAgents.add("document_researcher");

            if (activeAgent === "document_researcher") {
              activeAgent = null;
            }
          }

          if (searchAgent === "web_researcher") {
            completedAgents.add("web_researcher");

            if (activeAgent === "web_researcher") {
              activeAgent = null;
            }
          }

          break;
        }

        case "claims_extracted":
          completeActiveAgent();
          activeAgent = "claim_extractor";
          break;

        case "claim_checked":
          completeActiveAgent();
          activeAgent = "fact_checker";
          break;

        case "revision_requested":
          completeActiveAgent();
          activeAgent = "revision_decider";
          break;

        case "revision_search_started":
          completeActiveAgent();
          activeAgent = "revision_researcher";
          break;

        case "revision_search_completed":
          completedAgents.add("revision_researcher");

          if (activeAgent === "revision_researcher") {
            activeAgent = null;
          }

          break;

        case "revision_not_needed":
          completeActiveAgent();
          activeAgent = null;
          break;

        case "run_completed":
          activeAgent = null;
          break;
      }
    }

    if (loading && activeAgent === agent) {
      return "active";
    }

    if (completedAgents.has(agent)) {
      return "completed";
    }

    return "waiting";
  };

  /*
   * Fetch the final result after the SSE stream ends.
   */
  const fetchResearchResult = async (id: string) => {
    setResultLoading(true);
    setResultError("");

    try {
      const response = await fetch(
        `${API_URL}/research/${id}`,
      );

      if (!response.ok) {
        throw new Error(
          `Request failed with status ${response.status}`,
        );
      }

      const data = await response.json();

      setResult(data as ResearchResult);
    } catch (err) {
      console.error(
        "Failed to fetch research result:",
        err,
      );

      setResultError(
        "Unable to load the final research results.",
      );
    } finally {
      setResultLoading(false);
    }
  };

  /*
   * Start a research run and connect to its SSE event stream.
   */
  const handleSubmit = async (
    e: React.FormEvent<HTMLFormElement>,
  ) => {
    e.preventDefault();

    if (!question.trim()) {
      setError("Please enter a research question.");
      return;
    }

    setLoading(true);
    setError("");

    setEvents([]);
    setRunId(null);

    setResult(null);
    setResultError("");

    try {
      const response = await fetch(
        `${API_URL}/research`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: question.trim(),
          }),
        },
      );

      if (!response.ok) {
        throw new Error(
          `Request failed with status ${response.status}`,
        );
      }

      const data = await response.json();

      if (!data?.run_id) {
        throw new Error(
          "Backend did not return a run ID.",
        );
      }

      setRunId(data.run_id);

      const eventSource = new EventSource(
        `${API_URL}/research/${data.run_id}/events`,
      );

      eventSource.addEventListener(
        "agent_event",
        (event) => {
          const message = event as MessageEvent;

          try {
            const agentEvent = JSON.parse(
              message.data,
            );

            if (
              !agentEvent ||
              typeof agentEvent !== "object"
            ) {
              return;
            }

            const safeEvent: ResearchEvent = {
              type:
                typeof agentEvent.type === "string"
                  ? agentEvent.type
                  : "unknown",

              payload:
                agentEvent.payload &&
                typeof agentEvent.payload === "object"
                  ? agentEvent.payload
                  : {},
            };

            setEvents((prev) => [
              ...prev,
              safeEvent,
            ]);
          } catch (err) {
            console.error(
              "Failed to parse agent event:",
              err,
            );
          }
        },
      );

      eventSource.addEventListener(
        "stream_end",
        () => {
          eventSource.close();

          setLoading(false);

          fetchResearchResult(data.run_id);
        },
      );

      eventSource.onerror = () => {
        eventSource.close();

        setLoading(false);

        setError(
          "The research event stream was interrupted.",
        );
      };
    } catch (err) {
      console.error(
        "Research request failed:",
        err,
      );

      setLoading(false);

      setError(
        "Unable to start research. Make sure the backend server is running.",
      );
    }
  };

  /*
   * Live statistics from SSE events.
   */
  const latestGroundingScore =
    [...events]
      .reverse()
      .find(
        (event) =>
          event.type === "claim_checked" &&
          typeof event.payload?.grounding_score ===
            "number",
      )?.payload?.grounding_score;

  const revisionCount = events.filter(
    (event) =>
      event.type === "revision_requested",
  ).length;

  const evidenceCount = events.reduce(
    (total, event) => {
      if (
        event.type === "search_completed" ||
        event.type ===
          "revision_search_completed"
      ) {
        return (
          total +
          (event.payload?.evidence_count ?? 0)
        );
      }

      return total;
    },
    0,
  );

  const claimsCount =
    [...events]
      .reverse()
      .find(
        (event) =>
          event.type === "claims_extracted",
      )?.payload?.claims_count ?? 0;

  /*
   * Agent definitions.
   */
  const agents = [
    {
      id: "planner",
      name: "Planner",
      description: "Research strategy",
    },
    {
      id: "document_researcher",
      name: "Document Researcher",
      description: "Document investigation",
    },
    {
      id: "web_researcher",
      name: "Web Researcher",
      description: "Source investigation",
    },
    {
      id: "claim_extractor",
      name: "Claim Extractor",
      description: "Claim identification",
    },
    {
      id: "fact_checker",
      name: "Fact Checker",
      description: "Claim verification",
    },
    {
      id: "revision_decider",
      name: "Revision Decider",
      description: "Research refinement",
    },
    {
      id: "revision_researcher",
      name: "Revision Researcher",
      description: "Targeted follow-up searches",
    },
  ];

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Deep
              <span className="text-blue-400">
                Verify
              </span>
            </h1>

            <p className="text-sm text-slate-400">
              AI-powered research & fact
              verification
            </p>
          </div>

          <div className="rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-300">
            Research Agent
          </div>
        </div>
      </header>

      {/* Main */}
      <section className="mx-auto flex min-h-[calc(100vh-89px)] max-w-5xl items-center px-6 py-12">
        <div className="w-full">
          {/* Heading */}
          <div className="mb-10 text-center">
            <div className="mb-4 inline-flex rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-2 text-xs font-medium text-blue-400">
              AI Research War Room
            </div>

            <h2 className="text-4xl font-bold tracking-tight sm:text-5xl">
              Research anything.
              <br />
              <span className="text-blue-400">
                Verify everything.
              </span>
            </h2>

            <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-slate-400">
              Ask a research question and
              DeepVerify will investigate
              sources, extract claims, verify
              facts, and provide
              evidence-backed results.
            </p>
          </div>

          {/* Research Card */}
          <form
            onSubmit={handleSubmit}
            className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-2xl"
          >
            {/* Question */}
            <label
              htmlFor="question"
              className="mb-3 block text-sm font-medium text-slate-200"
            >
              Research Question
            </label>

            <textarea
              id="question"
              value={question}
              onChange={(e) =>
                setQuestion(e.target.value)
              }
              placeholder="e.g. What are the major causes of climate change?"
              rows={5}
              disabled={loading}
              className="w-full resize-none rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
            />

            {/* File Upload */}
            <div className="mt-6">
              <label
                htmlFor="file"
                className="mb-3 block text-sm font-medium text-slate-200"
              >
                Supporting Document{" "}
                <span className="font-normal text-slate-500">
                  (optional)
                </span>
              </label>

              <label
                htmlFor="file"
                className="flex cursor-pointer items-center justify-between rounded-xl border border-slate-700 bg-slate-950 px-4 py-4 transition hover:border-slate-600"
              >
                <div>
                  <p className="text-sm text-slate-300">
                    {file
                      ? file.name
                      : "Upload a PDF document"}
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    PDF files only
                  </p>
                </div>

                <span className="rounded-lg border border-slate-700 px-3 py-2 text-xs text-slate-300">
                  Choose PDF
                </span>

                <input
                  id="file"
                  type="file"
                  accept=".pdf,application/pdf"
                  className="hidden"
                  disabled={loading}
                  onChange={(e) => {
                    const selectedFile =
                      e.target.files?.[0] ?? null;

                    setFile(selectedFile);
                  }}
                />
              </label>
            </div>

            {/* Error */}
            {error && (
              <div className="mt-5 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                {error}
              </div>
            )}

            {/* Run ID */}
            {runId && (
              <div className="mt-5 rounded-xl border border-green-500/30 bg-green-500/10 px-4 py-3">
                <p className="text-sm font-medium text-green-300">
                  Research started
                  successfully.
                </p>

                <p className="mt-1 break-all text-xs text-green-400/70">
                  Run ID: {runId}
                </p>
              </div>
            )}

            {/* Live War Room Stats */}
            {events.length > 0 && (
              <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                  <p className="text-xs text-slate-500">
                    Evidence
                  </p>

                  <p className="mt-1 text-xl font-semibold text-slate-200">
                    {evidenceCount}
                  </p>
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                  <p className="text-xs text-slate-500">
                    Claims
                  </p>

                  <p className="mt-1 text-xl font-semibold text-slate-200">
                    {claimsCount}
                  </p>
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                  <p className="text-xs text-slate-500">
                    Grounding
                  </p>

                  <p className="mt-1 text-xl font-semibold text-purple-400">
                    {typeof latestGroundingScore ===
                    "number"
                      ? `${Math.round(
                          latestGroundingScore * 100,
                        )}%`
                      : "—"}
                  </p>
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                  <p className="text-xs text-slate-500">
                    Revisions
                  </p>

                  <p className="mt-1 text-xl font-semibold text-amber-400">
                    {revisionCount}
                  </p>
                </div>
              </div>
            )}

            {/* Agent Activity */}
            <AgentActivity
              agents={agents}
              events={events}
              loading={loading}
              getAgentStatus={getAgentStatus}
            />

            {/* Research Activity */}
            {events.length > 0 && (
              <div className="mt-5 rounded-xl border border-slate-700 bg-slate-950 p-5">
                <div className="mb-6 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-200">
                      Research Activity
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      Live investigation
                      timeline
                    </p>
                  </div>

                  {loading && (
                    <div className="flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-3 py-1.5 text-xs text-blue-400">
                      <span className="h-2 w-2 animate-pulse rounded-full bg-blue-400" />
                      Researching
                    </div>
                  )}

                  {!loading &&
                    events.some(
                      (event) =>
                        event.type ===
                        "run_completed",
                    ) && (
                      <div className="flex items-center gap-2 rounded-full border border-green-500/20 bg-green-500/10 px-3 py-1.5 text-xs text-green-400">
                        <span className="h-2 w-2 rounded-full bg-green-400" />
                        Completed
                      </div>
                    )}
                </div>

                <div className="space-y-0">
                  {events.map(
                    (event, index) => {
                      const agent =
                        event.payload?.agent;

                      const isLast =
                        index ===
                        events.length - 1;

                      const style =
                        getEventStyle(
                          event.type,
                        );

                      return (
                        <div
                          key={`${event.type}-${index}`}
                          className="flex gap-4"
                        >
                          {/* Timeline */}
                          <div className="flex flex-col items-center">
                            <div
                              className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full border ${style.circle}`}
                            >
                              <span
                                className={`h-2.5 w-2.5 rounded-full ${style.dot}`}
                              />
                            </div>

                            {!isLast && (
                              <div className="h-full min-h-8 w-px bg-slate-800" />
                            )}
                          </div>

                          {/* Event Card */}
                          <div className="mb-4 flex-1 rounded-xl border border-slate-800 bg-slate-900/60 p-4 transition hover:border-slate-700">
                            <div className="flex flex-wrap items-start justify-between gap-2">
                              <div>
                                <p className="text-sm font-semibold text-slate-200">
                                  {formatAgentName(
                                    agent,
                                  )}
                                </p>

                                <p
                                  className={`mt-1 text-xs capitalize ${style.text}`}
                                >
                                  {formatEventType(
                                    event.type,
                                  )}
                                </p>
                              </div>

                              <span className="text-xs text-slate-600">
                                #{index + 1}
                              </span>
                            </div>

                            {/* Plan Created */}
                            {event.type ===
                              "plan_created" && (
                              <div className="mt-3 rounded-lg bg-slate-950 px-3 py-2">
                                <p className="text-xs text-slate-400">
                                  Research plan
                                  created with{" "}
                                  <span className="text-slate-200">
                                    {event.payload
                                      ?.subtask_count ??
                                      0}
                                  </span>{" "}
                                  subtasks.
                                </p>
                              </div>
                            )}

                            {/* Search Started */}
                            {event.type ===
                              "search_started" && (
                              <div className="mt-3 rounded-lg bg-slate-950 px-3 py-2">
                                <p className="text-xs text-slate-400">
                                  Agent is
                                  searching for
                                  relevant
                                  evidence.
                                </p>
                              </div>
                            )}

                            {/* Search Completed */}
                            {event.type ===
                              "search_completed" && (
                              <div className="mt-3 rounded-lg bg-slate-950 px-3 py-2">
                                <p className="text-xs text-slate-400">
                                  Found{" "}
                                  <span className="text-slate-200">
                                    {event.payload
                                      ?.evidence_count ??
                                      0}
                                  </span>{" "}
                                  pieces of
                                  evidence.
                                </p>
                              </div>
                            )}

                            {/* Claims Extracted */}
                            {event.type ===
                              "claims_extracted" && (
                              <div className="mt-3 rounded-lg bg-slate-950 px-3 py-2">
                                <p className="text-xs text-slate-400">
                                  Extracted{" "}
                                  <span className="text-slate-200">
                                    {event.payload
                                      ?.claims_count ??
                                      0}
                                  </span>{" "}
                                  claims for
                                  verification.
                                </p>
                              </div>
                            )}

                            {/* Claim Checked */}
                            {event.type ===
                              "claim_checked" && (
                              <div className="mt-3 rounded-lg bg-slate-950 px-3 py-2">
                                <div className="flex items-center justify-between">
                                  <p className="text-xs text-slate-400">
                                    Claim
                                    grounding
                                  </p>

                                  <p className="text-sm font-semibold text-purple-400">
                                    {Math.round(
                                      (event.payload
                                        ?.grounding_score ??
                                        0) * 100,
                                    )}
                                    %
                                  </p>
                                </div>

                                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-800">
                                  <div
                                    className="h-full rounded-full bg-purple-400 transition-all duration-500"
                                    style={{
                                      width: `${Math.min(
                                        Math.max(
                                          (event.payload
                                            ?.grounding_score ??
                                            0) *
                                            100,
                                          0,
                                        ),
                                        100,
                                      )}%`,
                                    }}
                                  />
                                </div>
                              </div>
                            )}

                            {/* Revision Requested */}
                            {event.type ===
                              "revision_requested" && (
                              <div className="mt-3 rounded-lg border border-amber-500/10 bg-amber-500/5 px-3 py-2">
                                <p className="text-xs text-amber-300/80">
                                  Verification
                                  confidence was
                                  below the target
                                  threshold.
                                </p>

                                <p className="mt-1 text-xs text-slate-500">
                                  Generated{" "}
                                  <span className="text-slate-300">
                                    {event.payload
                                      ?.queries_count ??
                                      0}
                                  </span>{" "}
                                  targeted
                                  queries.
                                </p>

                                <p className="mt-1 text-xs text-slate-600">
                                  Revision round{" "}
                                  {(event.payload
                                    ?.revision_count ??
                                    0) + 1}
                                  .
                                </p>
                              </div>
                            )}

                            {/* Revision Search Started */}
                            {event.type ===
                              "revision_search_started" && (
                              <div className="mt-3 rounded-lg bg-slate-950 px-3 py-2">
                                <p className="text-xs text-slate-400">
                                  Running targeted
                                  follow-up
                                  searches.
                                </p>
                              </div>
                            )}

                            {/* Revision Search Completed */}
                            {event.type ===
                              "revision_search_completed" && (
                              <div className="mt-3 rounded-lg bg-slate-950 px-3 py-2">
                                <p className="text-xs text-slate-400">
                                  Found{" "}
                                  <span className="text-slate-200">
                                    {event.payload
                                      ?.evidence_count ??
                                      0}
                                  </span>{" "}
                                  additional
                                  evidence.
                                </p>
                              </div>
                            )}

                            {/* Revision Not Needed */}
                            {event.type ===
                              "revision_not_needed" && (
                              <div className="mt-3 rounded-lg border border-green-500/10 bg-green-500/5 px-3 py-2">
                                <p className="text-xs text-green-400">
                                  Current evidence
                                  is sufficient.
                                  No further
                                  revision
                                  required.
                                </p>
                              </div>
                            )}

                            {/* Run Completed */}
                            {event.type ===
                              "run_completed" && (
                              <div className="mt-3 rounded-lg border border-green-500/10 bg-green-500/5 px-3 py-2">
                                <p className="text-xs text-green-400">
                                  Research
                                  completed
                                  successfully.
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    },
                  )}
                </div>
              </div>
            )}

            {/* Final Research Results */}
            <ResearchResults
              result={result}
              resultLoading={resultLoading}
              resultError={resultError}
            />

            {/* Button */}
            <button
              type="submit"
              disabled={loading}
              className="mt-8 w-full rounded-xl bg-blue-600 px-6 py-4 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading
                ? "Researching..."
                : "Start Research"}
            </button>

            <p className="mt-4 text-center text-xs text-slate-500">
              DeepVerify will create a research run
              and track the investigation in real
              time.
            </p>
          </form>
        </div>
      </section>
    </main>
  );
}