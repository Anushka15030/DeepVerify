import type { Evidence } from "@/types/research";
import { formatPercent } from "@/lib/formatters";
import { useState } from "react";

type EvidenceSectionProps = {
  evidence: Evidence[];
};

const INITIAL_VISIBLE = 6;
const EXCERPT_LIMIT = 420;

export default function EvidenceSection({
  evidence,
}: EvidenceSectionProps) {
  const [showAll, setShowAll] = useState(false);

  const visibleEvidence = showAll
    ? evidence
    : evidence.slice(0, INITIAL_VISIBLE);

  return (
    <div className="mt-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Evidence
          </p>

          <p className="mt-1 text-xs text-slate-600">
            {evidence.length} evidence items retrieved
          </p>
        </div>
      </div>

      {evidence.length > 0 ? (
        <>
          <div className="mt-3 space-y-3">
            {visibleEvidence.map((item, index) => {
              const source = item.sources?.[0];

              return (
                <EvidenceCard
                  key={`${index}-${source?.title ?? "evidence"}`}
                  item={item}
                  index={index}
                  source={source}
                />
              );
            })}
          </div>

          {evidence.length > INITIAL_VISIBLE && (
            <button
              type="button"
              onClick={() => setShowAll((current) => !current)}
              className="mt-4 w-full rounded-lg border border-slate-700 px-3 py-2 text-xs font-medium text-slate-300 transition hover:bg-slate-800"
            >
              {showAll
                ? "Show fewer evidence items"
                : `Show all ${evidence.length} evidence items`}
            </button>
          )}
        </>
      ) : (
        <p className="mt-3 text-sm text-slate-500">
          No evidence was returned for this run.
        </p>
      )}
    </div>
  );
}

type EvidenceCardProps = {
  item: Evidence;
  index: number;
  source?: Evidence["sources"][number];
};

function EvidenceCard({
  item,
  index,
  source,
}: EvidenceCardProps) {
  const [expanded, setExpanded] = useState(false);

  const excerpt = item.excerpt ?? "";
  const isLong = excerpt.length > EXCERPT_LIMIT;

  const displayedExcerpt =
    !expanded && isLong
      ? `${excerpt.slice(0, EXCERPT_LIMIT)}...`
      : excerpt;

  return (
    <div className="min-w-0 rounded-lg bg-slate-950 px-3 py-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-xs text-slate-600">
            Evidence #{index + 1}
          </p>

          {source?.url ? (
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-1 block break-words text-sm font-medium text-blue-400 hover:underline"
            >
              {source.title || source.url}
            </a>
          ) : (
            <p className="mt-1 break-words text-sm font-medium text-slate-300">
              {source?.title || "Untitled source"}
            </p>
          )}
        </div>

        <span className="shrink-0 whitespace-nowrap rounded-full border border-slate-700 px-2 py-0.5 text-xs text-slate-300">
          {formatPercent(item.confidence)}
        </span>
      </div>

      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500">
        {source?.provider && (
          <span>Provider: {source.provider}</span>
        )}

        {source?.page_number != null && (
          <span>Page: {source.page_number}</span>
        )}
      </div>

      {excerpt && (
        <div className="mt-2">
          <p className="break-words text-xs leading-5 text-slate-400">
            {displayedExcerpt}
          </p>

          {isLong && (
            <button
              type="button"
              onClick={() => setExpanded((current) => !current)}
              className="mt-1 text-xs font-medium text-blue-400 hover:underline"
            >
              {expanded ? "Show less" : "Read more"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}