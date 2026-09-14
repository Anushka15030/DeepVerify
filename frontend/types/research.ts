export type ResearchEvent = {
  type: string;
  payload: Record<string, any>;
};

export type AgentStatus = "waiting" | "active" | "completed";

export type Subtask = {
  id: string;
  query: string;
  title: string;
  purpose: string;
  status: string;
  priority: number;
  description: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type ResearchPlan = {
  topic: string;
  subtasks: Subtask[];
  metadata: Record<string, any>;
};

export type EvidenceSource = {
  url: string;
  title: string;
  snippet: string;
  retrieved_at: string;
  provider: string;
  document_id: string | null;
  page_number: number | null;
  bbox: any;
  image_url: string | null;
};

export type Evidence = {
  excerpt: string;
  sources: EvidenceSource[];
  confidence: number;
};

export type ClaimCheck = {
  claim: string;
  verdict: string;
  evidence: Evidence[];
  grounding_score: number;
  explanation: string;
};

export type ResearchResult = {
  run_id: string;
  original_question: string;
  research_plan: ResearchPlan;
  evidence: Evidence[];
  draft: string;
  claims: string[];
  claim_checks: ClaimCheck[];
  grounding_score: number;
  revision_count: number;
  revision_queries: string[];
  agent_events: ResearchEvent[];
  errors: any[];
};