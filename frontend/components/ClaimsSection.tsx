import { useState } from "react";

type ClaimsSectionProps = {
  claims: string[];
};

const CLAIM_LIMIT = 320;

export default function ClaimsSection({
  claims,
}: ClaimsSectionProps) {
  return (
    <div className="mt-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Extracted Claims
        </p>

        <p className="mt-1 text-xs text-slate-600">
          {claims.length} claims extracted
        </p>
      </div>

      {claims.length > 0 ? (
        <ol className="mt-3 space-y-2">
          {claims.map((claim, index) => (
            <ClaimItem
              key={`${index}-${claim}`}
              claim={claim}
              index={index}
            />
          ))}
        </ol>
      ) : (
        <p className="mt-3 text-sm text-slate-500">
          No claims were returned for this run.
        </p>
      )}
    </div>
  );
}

type ClaimItemProps = {
  claim: string;
  index: number;
};

function ClaimItem({
  claim,
  index,
}: ClaimItemProps) {
  const [expanded, setExpanded] = useState(false);

  const isLong = claim.length > CLAIM_LIMIT;

  const displayedClaim =
    !expanded && isLong
      ? `${claim.slice(0, CLAIM_LIMIT)}...`
      : claim;

  return (
    <li className="flex min-w-0 items-start gap-3 rounded-lg bg-slate-950 px-3 py-2">
      <span className="shrink-0 text-xs text-slate-600">
        #{index + 1}
      </span>

      <div className="min-w-0 flex-1">
        <p className="break-words text-sm leading-5 text-slate-300">
          {displayedClaim}
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
    </li>
  );
}