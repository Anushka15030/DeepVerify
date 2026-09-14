type ClaimsSectionProps = {
  claims: string[];
};

export default function ClaimsSection({
  claims,
}: ClaimsSectionProps) {
  return (
    <div className="mt-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        Extracted Claims
      </p>

      {claims.length > 0 ? (
        <ol className="mt-3 space-y-2">
          {claims.map((claim, index) => (
            <li
              key={`${index}-${claim}`}
              className="flex items-start gap-3 rounded-lg bg-slate-950 px-3 py-2"
            >
              <span className="shrink-0 text-xs text-slate-600">
                #{index + 1}
              </span>

              <span className="text-sm text-slate-300">
                {claim}
              </span>
            </li>
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