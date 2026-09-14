import type { ResearchEvent } from "@/types/research";
import { formatAgentName, formatEventType, getEventStyle } from "@/lib/formatters";

type ResearchActivityProps = {
  events: ResearchEvent[];
  loading: boolean;
};

export default function ResearchActivity({
  events,
  loading,
}: ResearchActivityProps) {
  return (
    <div className="mt-5 rounded-xl border border-slate-700 bg-slate-950 p-5">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-200">
            Research Activity
          </p>

          <p className="mt-1 text-xs text-slate-500">
            Live investigation timeline
          </p>
        </div>

        {loading && (
          <div className="flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-3 py-1.5 text-xs text-blue-400">
            <span className="h-2 w-2 animate-pulse rounded-full bg-blue-400" />
            Researching
          </div>
        )}

        {!loading &&
          events.some((event) => event.type === "run_completed") && (
            <div className="flex items-center gap-2 rounded-full border border-green-500/20 bg-green-500/10 px-3 py-1.5 text-xs text-green-400">
              <span className="h-2 w-2 rounded-full bg-green-400" />
              Completed
            </div>
          )}
      </div>

      <div className="space-y-0">
        {events.map((event, index) => {
          const agent = event.payload?.agent;

          const isLast = index === events.length - 1;

          const style = getEventStyle(event.type);

          return (
            <div key={`${event.type}-${index}`} className="flex gap-4">
              {/* Timeline */}
              <div className="flex flex-col items-center">
                <div
                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full border ${style.circle}`}
                >
                  <span className={`h-2.5 w-2.5 rounded-full ${style.dot}`} />
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
                      {formatAgentName(agent)}
                    </p>

                    <p className={`mt-1 text-xs capitalize ${style.text}`}>
                      {formatEventType(event.type)}
                    </p>
                  </div>

                  <span className="text-xs text-slate-600">
                    #{index + 1}
                  </span>
                </div>

                {/* Plan Created */}
                {event.type === "plan_created" && (
                  <div className="mt-3 rounded-lg bg-slate-950 px-3 py-2">
                    <p className="text-xs text-slate-400">
                      Research plan created with{" "}
                      <span className="text-slate-200">
                        {event.payload?.subtask_count ?? 0}
                      </span>{" "}
                      subtasks.
                    </p>
                  </div>
                )}

                {/* Search Started */}
                {event.type === "search_started" && (
                  <div className="mt-3 rounded-lg bg-slate-950 px-3 py-2">
                    <p className="text-xs text-slate-400">
                      Agent is searching for relevant evidence.
                    </p>
                  </div>
                )}

                {/* Search Completed */}
                {event.type === "search_completed" && (
                  <div className="mt-3 rounded-lg bg-slate-950 px-3 py-2">
                    <p className="text-xs text-slate-400">
                      Found{" "}
                      <span className="text-slate-200">
                        {event.payload?.evidence_count ?? 0}
                      </span>{" "}
                      pieces of evidence.
                    </p>
                  </div>
                )}

                {/* Claims Extracted */}
                {event.type === "claims_extracted" && (
                  <div className="mt-3 rounded-lg bg-slate-950 px-3 py-2">
                    <p className="text-xs text-slate-400">
                      Extracted{" "}
                      <span className="text-slate-200">
                        {event.payload?.claims_count ?? 0}
                      </span>{" "}
                      claims for verification.
                    </p>
                  </div>
                )}

                {/* Claim Checked */}
                {event.type === "claim_checked" && (
                  <div className="mt-3 rounded-lg bg-slate-950 px-3 py-2">
                    <div className="flex items-center justify-between">
                      <p className="text-xs text-slate-400">
                        Claim grounding
                      </p>

                      <p className="text-sm font-semibold text-purple-400">
                        {Math.round(
                          (event.payload?.grounding_score ?? 0) * 100
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
                              (event.payload?.grounding_score ?? 0) * 100,
                              0
                            ),
                            100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Revision Requested */}
                {event.type === "revision_requested" && (
                  <div className="mt-3 rounded-lg border border-amber-500/10 bg-amber-500/5 px-3 py-2">
                    <p className="text-xs text-amber-300/80">
                      Verification confidence was below the target
                      threshold.
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      Generated{" "}
                      <span className="text-slate-300">
                        {event.payload?.queries_count ?? 0}
                      </span>{" "}
                      targeted queries.
                    </p>

                    <p className="mt-1 text-xs text-slate-600">
                      Revision round {(event.payload?.revision_count ?? 0) + 1}
                      .
                    </p>
                  </div>
                )}

                {/* Revision Search Started */}
                {event.type === "revision_search_started" && (
                  <div className="mt-3 rounded-lg bg-slate-950 px-3 py-2">
                    <p className="text-xs text-slate-400">
                      Running targeted follow-up searches.
                    </p>
                  </div>
                )}

                {/* Revision Search Completed */}
                {event.type === "revision_search_completed" && (
                  <div className="mt-3 rounded-lg bg-slate-950 px-3 py-2">
                    <p className="text-xs text-slate-400">
                      Found{" "}
                      <span className="text-slate-200">
                        {event.payload?.evidence_count ?? 0}
                      </span>{" "}
                      additional evidence.
                    </p>
                  </div>
                )}

                {/* Revision Not Needed */}
                {event.type === "revision_not_needed" && (
                  <div className="mt-3 rounded-lg border border-green-500/10 bg-green-500/5 px-3 py-2">
                    <p className="text-xs text-green-400">
                      Current evidence is sufficient. No further revision
                      required.
                    </p>
                  </div>
                )}

                {/* Run Completed */}
                {event.type === "run_completed" && (
                  <div className="mt-3 rounded-lg border border-green-500/10 bg-green-500/5 px-3 py-2">
                    <p className="text-xs text-green-400">
                      Research completed successfully.
                    </p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
