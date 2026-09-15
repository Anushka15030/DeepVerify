import type {
  ClaimCheck,
  Evidence,
  ResearchResult,
} from "@/types/research";
import { formatNumber, formatPercent } from "@/lib/formatters";
import { useState } from "react";
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

  const claimChecks = result.claim_checks ?? [];

  const verdictCounts = {
    supported: claimChecks.filter(
      (check) => check.verdict === "supported",
    ).length,

    refuted: claimChecks.filter(
      (check) => check.verdict === "refuted",
    ).length,

    unverifiable: claimChecks.filter(
      (check) => check.verdict === "unverifiable",
    ).length,

    inconclusive: claimChecks.filter(
      (check) => check.verdict === "inconclusive",
    ).length,
  };

  const strongestRefutedClaim = claimChecks.find(
    (check) => check.verdict === "refuted",
  );

  const strongestUnverifiableClaim = claimChecks.find(
    (check) =>
      check.verdict === "unverifiable" ||
      check.verdict === "inconclusive",
  );

  return (
    <div className="mt-5 rounded-xl border border-slate-700 bg-slate-950 p-5">
      {/* Header */}
      <div className="mb-5">
        <p className="text-sm font-semibold text-slate-100">
          DeepVerify — Verification Report
        </p>

        <p className="mt-1 text-xs text-slate-500">
          Autonomous evidence analysis and claim verification
        </p>
      </div>

      {/* Research Question */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Research Question
        </p>

        <p className="mt-2 break-words text-sm leading-6 text-slate-200">
          {result.original_question || "—"}
        </p>
      </div>

      {/* Verification Summary */}
      <div className="mt-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Verification Summary
            </p>

            <p className="mt-1 text-sm text-slate-300">
              {formatNumber(claimChecks.length)} claims analyzed
            </p>
          </div>

          <div className="text-right">
            <p className="text-xs text-slate-500">
              Evidence Grounding
            </p>

            <p className="mt-1 text-2xl font-bold text-purple-400">
              {formatPercent(result.grounding_score)}
            </p>
          </div>
        </div>

        {/* Verdict counts */}
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <VerdictSummary
            label="Supported"
            count={verdictCounts.supported}
            className="border-emerald-500/20 bg-emerald-500/5 text-emerald-400"
          />

          <VerdictSummary
            label="Refuted"
            count={verdictCounts.refuted}
            className="border-red-500/20 bg-red-500/5 text-red-400"
          />

          <VerdictSummary
            label="Unverifiable"
            count={verdictCounts.unverifiable}
            className="border-amber-500/20 bg-amber-500/5 text-amber-400"
          />

          <VerdictSummary
            label="Inconclusive"
            count={verdictCounts.inconclusive}
            className="border-slate-700 bg-slate-950 text-slate-300"
          />
        </div>

        {/* Secondary metrics */}
        <div className="mt-3 grid grid-cols-2 gap-3">
          <MetricCard
            label="Evidence Items"
            value={formatNumber(result.evidence.length)}
          />

          <MetricCard
            label="Revision Cycles"
            value={formatNumber(result.revision_count)}
          />
        </div>
      </div>

      {/* Important finding */}
      {strongestRefutedClaim ? (
        <ClaimHighlight
          title="Critical Finding"
          check={strongestRefutedClaim}
          variant="refuted"
        />
      ) : strongestUnverifiableClaim ? (
        <ClaimHighlight
          title="Evidence Limitation"
          check={strongestUnverifiableClaim}
          variant="unverifiable"
        />
      ) : null}

      {/* Research Plan */}
      <ResearchPlan
        subtasks={result.research_plan?.subtasks ?? []}
      />

      {/* Claims */}
      <ClaimsSection claims={result.claims ?? []} />

      {/* Claim Verification */}
      <ClaimVerification claimChecks={claimChecks} />

      {/* Evidence */}
      <EvidenceSection evidence={result.evidence ?? []} />
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Summary components                                                         */
/* -------------------------------------------------------------------------- */

type VerdictSummaryProps = {
  label: string;
  count: number;
  className: string;
};

function VerdictSummary({
  label,
  count,
  className,
}: VerdictSummaryProps) {
  return (
    <div
      className={`rounded-lg border p-3 ${className}`}
    >
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium">
          {label}
        </p>

        <p className="text-xl font-bold">
          {count}
        </p>
      </div>
    </div>
  );
}

type MetricCardProps = {
  label: string;
  value: string;
};

function MetricCard({
  label,
  value,
}: MetricCardProps) {
  return (
    <div className="rounded-lg bg-slate-950 p-3">
      <p className="text-xs text-slate-500">
        {label}
      </p>

      <p className="mt-1 text-lg font-semibold text-slate-200">
        {value}
      </p>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Highlighted finding                                                        */
/* -------------------------------------------------------------------------- */

type ClaimHighlightProps = {
  title: string;
  check: ClaimCheck;
  variant: "refuted" | "unverifiable";
};

function ClaimHighlight({
  title,
  check,
  variant,
}: ClaimHighlightProps) {
  const isRefuted = variant === "refuted";

  const source = check.evidence?.[0]?.sources?.[0];

  return (
    <div
      className={`mt-4 rounded-xl border p-4 ${
        isRefuted
          ? "border-red-500/30 bg-red-500/5"
          : "border-amber-500/30 bg-amber-500/5"
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p
          className={`text-xs font-semibold uppercase tracking-wide ${
            isRefuted
              ? "text-red-400"
              : "text-amber-400"
          }`}
        >
          {title}
        </p>

        <span
          className={`rounded-full border px-2 py-1 text-xs font-semibold ${
            isRefuted
              ? "border-red-500/30 text-red-400"
              : "border-amber-500/30 text-amber-400"
          }`}
        >
          {isRefuted ? "REFUTED" : "UNVERIFIABLE"}
        </span>
      </div>

      <p className="mt-3 text-sm font-medium leading-6 text-slate-200">
        “{check.claim}”
      </p>

      {check.explanation && (
        <div className="mt-3 rounded-lg bg-slate-950/70 p-3">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-600">
            Why
          </p>

          <p className="mt-1 text-xs leading-5 text-slate-400">
            {check.explanation}
          </p>
        </div>
      )}

      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
        <span>
          Grounding: {formatPercent(check.grounding_score)}
        </span>

        {source?.page_number != null && (
          <span>
            Source page: {source.page_number}
          </span>
        )}

        {source?.provider && (
          <span>
            Provider: {source.provider}
          </span>
        )}
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Claim verification                                                         */
/* -------------------------------------------------------------------------- */

type ClaimVerificationProps = {
  claimChecks: ClaimCheck[];
};

function ClaimVerification({
  claimChecks,
}: ClaimVerificationProps) {
  return (
    <div className="mt-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Claim Verification
        </p>

        <p className="mt-1 text-xs text-slate-600">
          {claimChecks.length} verification checks
        </p>
      </div>

      {claimChecks.length > 0 ? (
        <div className="mt-3 space-y-3">
          {claimChecks.map((check, index) => (
            <ClaimCheckCard
              key={`${index}-${check.claim}`}
              check={check}
              index={index}
            />
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

type ClaimCheckCardProps = {
  check: ClaimCheck;
  index: number;
};

function ClaimCheckCard({
  check,
  index,
}: ClaimCheckCardProps) {
  const [showEvidence, setShowEvidence] = useState(false);

  const supportingEvidence = check.evidence ?? [];
  const visibleEvidence = supportingEvidence.slice(0, 2);

  const verdictStyle = getVerdictStyle(check.verdict);

  return (
    <div className="min-w-0 rounded-lg bg-slate-950 px-3 py-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-xs text-slate-600">
            Claim #{index + 1}
          </p>

          <p className="mt-1 break-words text-sm leading-5 text-slate-300">
            {check.claim}
          </p>
        </div>

        <span
          className={`shrink-0 whitespace-nowrap rounded-full border px-2 py-0.5 text-xs font-medium capitalize ${verdictStyle}`}
        >
          {check.verdict}
        </span>
      </div>

      <div className="mt-3 flex items-center gap-2">
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-800">
          <div
            className={`h-full rounded-full ${getGroundingBarClass(
              check.verdict,
            )}`}
            style={{
              width: `${Math.min(
                Math.max(check.grounding_score * 100, 0),
                100,
              )}%`,
            }}
          />
        </div>

        <span className="shrink-0 text-xs font-semibold text-slate-400">
          {formatPercent(check.grounding_score)}
        </span>
      </div>

      {check.explanation && (
        <p className="mt-2 break-words text-xs leading-5 text-slate-500">
          {check.explanation}
        </p>
      )}

      {supportingEvidence.length > 0 && (
        <div className="mt-3 border-t border-slate-800 pt-3">
          <button
            type="button"
            onClick={() =>
              setShowEvidence((current) => !current)
            }
            className="flex w-full items-center justify-between text-left text-xs font-medium text-slate-500 hover:text-slate-300"
          >
            <span>
              Supporting evidence ({supportingEvidence.length})
            </span>

            <span>
              {showEvidence ? "Hide" : "Show"}
            </span>
          </button>

          {showEvidence && (
            <div className="mt-2 space-y-2">
              {visibleEvidence.map(
                (evidence: Evidence, evidenceIndex) => {
                  const source = evidence.sources?.[0];

                  return (
                    <div
                      key={evidenceIndex}
                      className="min-w-0 rounded-md border border-slate-800 bg-slate-900 px-3 py-2"
                    >
                      {source?.title && (
                        <p className="break-words text-xs font-medium text-slate-400">
                          {source.title}
                        </p>
                      )}

                      {source?.page_number != null && (
                        <p className="mt-1 text-xs text-slate-600">
                          Page {source.page_number}
                        </p>
                      )}

                      <p className="mt-1 break-words text-xs leading-5 text-slate-500">
                        {evidence.excerpt}
                      </p>
                    </div>
                  );
                },
              )}

              {supportingEvidence.length > 2 && (
                <p className="text-xs text-slate-600">
                  Showing 2 of {supportingEvidence.length} supporting
                  evidence items.
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Verdict styling                                                            */
/* -------------------------------------------------------------------------- */

function getVerdictStyle(
  verdict: ClaimCheck["verdict"],
) {
  switch (verdict) {
    case "supported":
      return "border-emerald-500/30 bg-emerald-500/10 text-emerald-400";

    case "refuted":
      return "border-red-500/30 bg-red-500/10 text-red-400";

    case "unverifiable":
      return "border-amber-500/30 bg-amber-500/10 text-amber-400";

    case "inconclusive":
    default:
      return "border-slate-700 bg-slate-900 text-slate-400";
  }
}

function getGroundingBarClass(
  verdict: ClaimCheck["verdict"],
) {
  switch (verdict) {
    case "supported":
      return "bg-emerald-400";

    case "refuted":
      return "bg-red-400";

    case "unverifiable":
      return "bg-amber-400";

    case "inconclusive":
    default:
      return "bg-slate-500";
  }
}