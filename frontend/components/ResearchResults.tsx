import type {
  ClaimCheck,
  Evidence,
  ResearchResult,
} from "@/types/research";
import { formatNumber, formatPercent } from "@/lib/formatters";
import ResearchPlan from "./ResearchPlan";
import ClaimsSection from "./ClaimsSection";
import EvidenceSection from "./EvidenceSection";

type ResearchResultsProps = {
  result: ResearchResult | null;
  resultLoading: boolean;
  resultError: string;
};

export default function ResearchResults({
  result,
  resultLoading,
  resultError,
}: ResearchResultsProps) {
  if (resultLoading) {
    return (
      <div className="mt-5 flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-400">
        <span className="h-2 w-2 animate-pulse rounded-full bg-blue-400" />
        Loading final research results...
      </div>
    );
  }

  if (resultError) {
    return (
      <div className="mt-5 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
        {resultError}
      </div>
    );
  }

  if (!result) {
    return null;
  }

  return (
    <div className="mt-5 rounded-xl border border-slate-700 bg-slate-950 p-5">
      <div className="mb-5">
        <p className="text-sm font-semibold text-slate-200">
          Research Results
        </p>

        <p className="mt-1 text-xs text-slate-500">
          Final output for this research run
        </p>
      </div>

      {/* Research Summary */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Research Question
        </p>

        <p className="mt-2 text-sm text-slate-200">
          {result.original_question || "—"}
        </p>

        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-lg bg-slate-950 p-3">
            <p className="text-xs text-slate-500">
              Grounding
            </p>

            <p className="mt-1 text-lg font-semibold text-purple-400">
              {formatPercent(result.grounding_score)}
            </p>
          </div>

          <div className="rounded-lg bg-slate-950 p-3">
            <p className="text-xs text-slate-500">
              Evidence
            </p>

            <p className="mt-1 text-lg font-semibold text-slate-200">
              {formatNumber(result.evidence.length)}
            </p>
          </div>

          <div className="rounded-lg bg-slate-950 p-3">
            <p className="text-xs text-slate-500">
              Claims
            </p>

            <p className="mt-1 text-lg font-semibold text-slate-200">
              {formatNumber(result.claims.length)}
            </p>
          </div>

          <div className="rounded-lg bg-slate-950 p-3">
            <p className="text-xs text-slate-500">
              Revisions
            </p>

            <p className="mt-1 text-lg font-semibold text-amber-400">
              {formatNumber(result.revision_count)}
            </p>
          </div>
        </div>
      </div>

      {/* Research Plan */}
      <ResearchPlan
        subtasks={result.research_plan?.subtasks ?? []}
      />

      {/* Claims */}
      <ClaimsSection
        claims={result.claims ?? []}
      />

      {/* Claim Verification */}
      <ClaimVerification
        claimChecks={result.claim_checks ?? []}
      />

      {/* Evidence */}
      <EvidenceSection
        evidence={result.evidence ?? []}
      />
    </div>
  );
}

type ClaimVerificationProps = {
  claimChecks: ClaimCheck[];
};

function ClaimVerification({
  claimChecks,
}: ClaimVerificationProps) {
  return (
    <div className="mt-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        Claim Verification
      </p>

      {claimChecks.length > 0 ? (
        <div className="mt-3 space-y-3">
          {claimChecks.map((check, index) => (
            <div
              key={`${index}-${check.claim}`}
              className="rounded-lg bg-slate-950 px-3 py-3"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-xs text-slate-600">
                    Claim #{index + 1}
                  </p>

                  <p className="mt-1 text-sm text-slate-300">
                    {check.claim}
                  </p>
                </div>

                <span className="whitespace-nowrap rounded-full border border-slate-700 px-2 py-0.5 text-xs capitalize text-slate-300">
                  {check.verdict}
                </span>
              </div>

              <div className="mt-3 flex items-center gap-2">
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-800">
                  <div
                    className="h-full rounded-full bg-purple-400"
                    style={{
                      width: `${Math.min(
                        Math.max(
                          check.grounding_score * 100,
                          0,
                        ),
                        100,
                      )}%`,
                    }}
                  />
                </div>

                <span className="text-xs font-semibold text-purple-400">
                  {formatPercent(check.grounding_score)}
                </span>
              </div>

              {check.explanation && (
                <p className="mt-2 text-xs leading-5 text-slate-500">
                  {check.explanation}
                </p>
              )}

              {/* Only show evidence belonging to THIS claim */}
              {check.evidence?.length > 0 && (
                <div className="mt-3 border-t border-slate-800 pt-3">
                  <p className="text-xs font-medium text-slate-500">
                    Supporting evidence
                  </p>

                  <div className="mt-2 space-y-2">
                    {check.evidence.map(
                      (evidence: Evidence, evidenceIndex) => {
                        const source =
                          evidence.sources?.[0];

                        return (
                          <div
                            key={evidenceIndex}
                            className="rounded-md border border-slate-800 bg-slate-900 px-3 py-2"
                          >
                            {source?.title && (
                              <p className="text-xs font-medium text-slate-400">
                                {source.title}
                              </p>
                            )}

                            <p className="mt-1 text-xs leading-5 text-slate-500">
                              {evidence.excerpt}
                            </p>
                          </div>
                        );
                      },
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-500">
          No claim verification details were returned for this run.
        </p>
      )}
    </div>
  );
}