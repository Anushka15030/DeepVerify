"use client";

import { useState } from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type ResearchEvent = {
  type: string;
  payload: Record<string, any>;
};

export default function Home() {
  const [question, setQuestion] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [runId, setRunId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [events, setEvents] = useState<ResearchEvent[]>([]);

  const formatAgentName = (agent?: string) => {
    if (!agent) {
      return "DeepVerify";
    }

    return agent
      .split("_")
      .map(
        (word: string) =>
          word.charAt(0).toUpperCase() + word.slice(1)
      )
      .join(" ");
  };

  const formatEventType = (type?: string) => {
    if (!type) {
      return "Unknown event";
    }

    return type.replaceAll("_", " ");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!question.trim()) {
      setError("Please enter a research question.");
      return;
    }

    setLoading(true);
    setError("");
    setEvents([]);
    setRunId(null);

    try {
      const response = await fetch(`${API_URL}/research`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: question.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error(
          `Request failed with status ${response.status}`
        );
      }

      const data = await response.json();

      if (!data?.run_id) {
        throw new Error("Backend did not return a run ID.");
      }

      setRunId(data.run_id);

      const eventSource = new EventSource(
        `${API_URL}/research/${data.run_id}/events`
      );

      eventSource.addEventListener("agent_event", (event) => {
        const message = event as MessageEvent;

        try {
          const agentEvent = JSON.parse(message.data);

          if (!agentEvent || typeof agentEvent !== "object") {
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

          setEvents((prev) => [...prev, safeEvent]);
        } catch (err) {
          console.error(
            "Failed to parse agent event:",
            err
          );
        }
      });

      eventSource.addEventListener("stream_end", () => {
        eventSource.close();
        setLoading(false);
      });

      eventSource.onerror = () => {
        eventSource.close();
        setLoading(false);
        setError(
          "The research event stream was interrupted."
        );
      };
    } catch (err) {
      console.error("Research request failed:", err);

      setLoading(false);
      setError(
        "Unable to start research. Make sure the backend server is running."
      );
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Deep<span className="text-blue-400">Verify</span>
            </h1>

            <p className="text-sm text-slate-400">
              AI-powered research & fact verification
            </p>
          </div>

          <div className="rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-300">
            Research Agent
          </div>
        </div>
      </header>

      {/* Main */}
      <section className="mx-auto flex min-h-[calc(100vh-89px)] max-w-4xl items-center px-6 py-12">
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
              Ask a research question and DeepVerify will
              investigate sources, extract claims, verify facts,
              and provide evidence-backed results.
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
              onChange={(e) => setQuestion(e.target.value)}
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
                      e.target.files?.[0] || null;

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

            {/* Success */}
            {runId && (
              <div className="mt-5 rounded-xl border border-green-500/30 bg-green-500/10 px-4 py-3">
                <p className="text-sm font-medium text-green-300">
                  Research started successfully.
                </p>

                <p className="mt-1 break-all text-xs text-green-400/70">
                  Run ID: {runId}
                </p>
              </div>
            )}

            {/* Research Activity */}
            {events.length > 0 && (
              <div className="mt-5 rounded-xl border border-slate-700 bg-slate-950 p-5">
                <div className="mb-5 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-200">
                      Research Activity
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      Live investigation timeline
                    </p>
                  </div>

                  {loading && (
                    <div className="flex items-center gap-2 text-xs text-blue-400">
                      <span className="h-2 w-2 animate-pulse rounded-full bg-blue-400" />
                      Running
                    </div>
                  )}

                  {!loading &&
                    events.some(
                      (event) =>
                        event.type === "run_completed"
                    ) && (
                      <div className="flex items-center gap-2 text-xs text-green-400">
                        <span className="h-2 w-2 rounded-full bg-green-400" />
                        Completed
                      </div>
                    )}
                </div>

                <div className="space-y-0">
                  {events.map((event, index) => {
                    const agent =
                      event.payload?.agent;

                    const isLast =
                      index === events.length - 1;

                    return (
                      <div
                        key={`${event.type}-${index}`}
                        className="flex gap-4"
                      >
                        {/* Timeline */}
                        <div className="flex flex-col items-center">
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-blue-500/30 bg-blue-500/10">
                            <span className="h-2 w-2 rounded-full bg-blue-400" />
                          </div>

                          {!isLast && (
                            <div className="h-full min-h-8 w-px bg-slate-800" />
                          )}
                        </div>

                        {/* Event */}
                        <div className="pb-5">
                          <p className="text-sm font-medium text-slate-200">
                            {formatAgentName(agent)}
                          </p>

                          <p className="mt-1 text-xs capitalize text-blue-400">
                            {formatEventType(
                              event.type
                            )}
                          </p>

                          {/* Plan Created */}
                          {event.type ===
                            "plan_created" && (
                            <p className="mt-2 text-xs text-slate-500">
                              Created{" "}
                              {event.payload
                                ?.subtask_count ??
                                0}{" "}
                              research subtasks
                            </p>
                          )}

                          {/* Search Completed */}
                          {event.type ===
                            "search_completed" && (
                            <p className="mt-2 text-xs text-slate-500">
                              Found{" "}
                              {event.payload
                                ?.evidence_count ??
                                0}{" "}
                              pieces of evidence
                            </p>
                          )}

                          {/* Claims Extracted */}
                          {event.type ===
                            "claims_extracted" && (
                            <p className="mt-2 text-xs text-slate-500">
                              Extracted{" "}
                              {event.payload
                                ?.claims_count ??
                                0}{" "}
                              claims
                            </p>
                          )}

                          {/* Claim Checked */}
                          {event.type ===
                            "claim_checked" && (
                            <p className="mt-2 text-xs text-slate-500">
                              Grounding score:{" "}
                              <span className="text-slate-300">
                                {Math.round(
                                  (event.payload
                                    ?.grounding_score ??
                                    0) * 100
                                )}
                                %
                              </span>
                            </p>
                          )}

                          {/* Revision Requested */}
                          {event.type ===
                            "revision_requested" && (
                            <p className="mt-2 text-xs text-slate-500">
                              {event.payload
                                ?.queries_count ??
                                0}{" "}
                              targeted queries
                              generated
                            </p>
                          )}

                          {/* Revision Search Completed */}
                          {event.type ===
                            "revision_search_completed" && (
                            <p className="mt-2 text-xs text-slate-500">
                              Found{" "}
                              {event.payload
                                ?.evidence_count ??
                                0}{" "}
                              additional evidence
                            </p>
                          )}

                          {/* Run Completed */}
                          {event.type ===
                            "run_completed" && (
                            <p className="mt-2 text-xs text-green-400">
                              Research completed
                              successfully
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

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
              DeepVerify will create a research run and
              track the investigation in real time.
            </p>
          </form>
        </div>
      </section>
    </main>
  );
}