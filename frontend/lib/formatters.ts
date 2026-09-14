import type { AgentStatus } from "@/types/research";

/* Small helper: return the first defined/non-null value among a list
   of possible field names on an object. Used everywhere below so we
   don't assume one exact backend key name. */
export function pick<T = any>(obj: any, keys: string[]): T | undefined {
  if (!obj || typeof obj !== "object") return undefined;
  for (const key of keys) {
    if (obj[key] !== undefined && obj[key] !== null) {
      return obj[key];
    }
  }
  return undefined;
}

export function formatPercent(value: unknown): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "—";
}

export function formatNumber(value: unknown): string {
  return typeof value === "number" ? String(value) : "—";
}

export const formatAgentName = (agent?: string) => {
  if (!agent) {
    return "DeepVerify";
  }

  return agent
    .split("_")
    .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

export const formatEventType = (type?: string) => {
  if (!type) {
    return "Unknown event";
  }

  return type.replaceAll("_", " ");
};

export const getEventStyle = (type: string) => {
  if (type.includes("completed")) {
    return {
      dot: "bg-green-400",
      circle: "border-green-500/30 bg-green-500/10",
      text: "text-green-400",
    };
  }

  if (type.includes("revision")) {
    return {
      dot: "bg-amber-400",
      circle: "border-amber-500/30 bg-amber-500/10",
      text: "text-amber-400",
    };
  }

  if (type === "claim_checked") {
    return {
      dot: "bg-purple-400",
      circle: "border-purple-500/30 bg-purple-500/10",
      text: "text-purple-400",
    };
  }

  return {
    dot: "bg-blue-400",
    circle: "border-blue-500/30 bg-blue-500/10",
    text: "text-blue-400",
  };
};

export const getAgentStatusText = (status: AgentStatus) => {
  if (status === "active") {
    return "Working...";
  }

  if (status === "completed") {
    return "Completed";
  }

  return "Waiting";
};
