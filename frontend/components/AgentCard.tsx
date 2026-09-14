import type { AgentStatus } from "@/types/research";
import { getAgentStatusText } from "@/lib/formatters";

type AgentCardProps = {
  name: string;
  description: string;
  status: AgentStatus;
};

export default function AgentCard({
  name,
  description,
  status,
}: AgentCardProps) {
  return (
    <div
      className={`rounded-xl border px-4 py-3 transition ${
        status === "active"
          ? "border-blue-500/30 bg-blue-500/5"
          : status === "completed"
          ? "border-green-500/20 bg-green-500/5"
          : "border-slate-800 bg-slate-900/50"
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className={`flex h-8 w-8 items-center justify-center rounded-full ${
              status === "active"
                ? "bg-blue-500/10"
                : status === "completed"
                ? "bg-green-500/10"
                : "bg-slate-800"
            }`}
          >
            {status === "completed" ? (
              <span className="text-sm text-green-400">✓</span>
            ) : status === "active" ? (
              <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-blue-400" />
            ) : (
              <span className="h-2 w-2 rounded-full bg-slate-600" />
            )}
          </div>

          <div>
            <p className="text-sm font-medium text-slate-200">{name}</p>

            <p className="mt-0.5 text-xs text-slate-500">{description}</p>
          </div>
        </div>

        <span
          className={`text-xs ${
            status === "active"
              ? "text-blue-400"
              : status === "completed"
              ? "text-green-400"
              : "text-slate-600"
          }`}
        >
          {getAgentStatusText(status)}
        </span>
      </div>
    </div>
  );
}
