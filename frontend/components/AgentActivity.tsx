import type { AgentStatus, ResearchEvent } from "@/types/research";
import AgentCard from "@/components/AgentCard";

type AgentActivityProps = {
  agents: {
    id: string;
    name: string;
    description: string;
  }[];
  events: ResearchEvent[];
  loading: boolean;
  getAgentStatus: (
    agent: string,
    events: ResearchEvent[],
    loading: boolean
  ) => AgentStatus;
};

export default function AgentActivity({
  agents,
  events,
  loading,
  getAgentStatus,
}: AgentActivityProps) {
  return (
    <div className="mt-5 rounded-xl border border-slate-700 bg-slate-950 p-5">
      <div className="mb-5">
        <p className="text-sm font-semibold text-slate-200">
          Agent Activity
        </p>

        <p className="mt-1 text-xs text-slate-500">
          Current status of the research agents
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {agents.map((agent) => {
          const status = getAgentStatus(agent.id, events, loading);

          return (
            <AgentCard
              key={agent.id}
              name={agent.name}
              description={agent.description}
              status={status}
            />
          );
        })}
      </div>
    </div>
  );
}
