export type RunRecord = {
  run_id: string;
  status: string;
  stage: string;
  created_at: string;
  updated_at: string;
  scope: Record<string, unknown>;
  summary: Record<string, unknown>;
  error_message?: string | null;
  artifacts: Array<{ stage: string; name: string; path: string }>;
};

export type GraphNode = {
  node_id: string;
  node_type: string;
  label: string;
  message_volume?: number;
  team_id?: string;
  channel_id?: string;
};

export type GraphLink = {
  edge_id: string;
  source: string;
  target: string;
  edge_type: string;
  weight: number;
  conversation_count: number;
};

export type GraphPayload = {
  run_id: string;
  mode: string;
  nodes: GraphNode[];
  links: GraphLink[];
};

export type NodeDetailPayload = {
  node: GraphNode;
  metrics: Record<string, number>;
  conversations: Record<string, unknown>[];
  messages: Record<string, unknown>[];
};

export type EdgeDetailPayload = {
  edge: GraphLink;
  conversations: Record<string, unknown>[];
};

export type SummaryPayload = {
  run: RunRecord;
  summary: Record<string, number>;
  top_clusters: Array<Record<string, unknown>>;
  recommendation_count: number;
};

export type Recommendation = {
  suggestion_id: string;
  action: string;
  proposed_channel_name: string;
  team_id?: string;
  source_channels: string;
  rationale: string;
  confidence: number;
  evidence_count: number;
};

export type RecommendationsPayload = {
  recommendations: Recommendation[];
  taxonomy_markdown: string;
};

export type ClusterPayload = {
  summary: Array<Record<string, unknown>>;
  conversations: Array<Record<string, unknown>>;
};
