import type { Subtask } from "@/types/research";

type ResearchPlanProps = {
  subtasks: Subtask[];
};

export default function ResearchPlan({
  subtasks,
}: ResearchPlanProps) {
  return (
    <div className="mt-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        Research Plan
      </p>

      {subtasks.length > 0 ? (
        <div className="mt-3 space-y-2">
          {subtasks.map((subtask, index) => (
            <li
              key={subtask.id}
              className="rounded-lg bg-slate-950 px-3 py-3"
            >
              <div className="flex gap-3">
                <span className="shrink-0 text-xs text-slate-600">
                  {index + 1}.
                </span>

                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-200">
                    {subtask.title}
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    Purpose:{" "}
                    <span className="text-slate-400">
                      {subtask.purpose}
                    </span>
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    Query:{" "}
                    <span className="text-slate-400">
                      {subtask.query}
                    </span>
                  </p>
                </div>
              </div>
            </li>
          ))}
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-500">
          No research plan details were returned for this run.
        </p>
      )}
    </div>
  );
}