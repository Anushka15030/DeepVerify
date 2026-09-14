import type { Evidence } from "@/types/research";
import { formatPercent } from "@/lib/formatters";

type EvidenceSectionProps = {
  evidence: Evidence[];
};

export default function EvidenceSection({
  evidence,
}: EvidenceSectionProps) {
  return (
    <div className="mt-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        Evidence
      </p>

      {evidence.length > 0 ? (
        <div className="mt-3 space-y-3">
          {evidence.map((item, index) => {
            const source = item.sources?.[0];

            return (
              <div
                key={index}
                className="rounded-lg bg-slate-950 px-3 py-3"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  {source?.url ? (
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium text-blue-400 hover:underline"
                    >
                      {source.title || source.url}
                    </a>
                  ) : (
                    <p className="text-sm font-medium text-slate-300">
                      {source?.title || "Untitled source"}
                    </p>
                  )}

                  <span className="whitespace-nowrap rounded-full border border-slate-700 px-2 py-0.5 text-xs text-slate-300">
                    {formatPercent(item.confidence)} confidence
                  </span>
                </div>

                {source?.provider && (
                  <p className="mt-1 text-xs text-slate-500">
                    Provider: {source.provider}
                  </p>
                )}

                {source?.page_number != null && (
                  <p className="mt-1 text-xs text-slate-500">
                    Page: {source.page_number}
                  </p>
                )}

                {item.excerpt && (
                  <p className="mt-2 text-xs leading-5 text-slate-400">
                    {item.excerpt}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-500">
          No evidence was returned for this run.
        </p>
      )}
    </div>
  );
}