// Auth types
export interface User {
  id: string
  email: string
  full_name: string
  role: 'admin' | 'member' | 'viewer'
  organization_id: string
  is_active: boolean
  created_at: string
}

export interface Organization {
  id: string
  name: string
  type: string
  subscription_tier: 'free' | 'pro' | 'enterprise'
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
  organization_name: string
}

// Paper types
export type PaperSource =
  | 'doi'
  | 'openalex'
  | 'pubmed'
  | 'arxiv'
  | 'crossref'
  | 'semantic_scholar'
  | 'manual'
  | 'pdf'

export interface Author {
  id: string
  name: string
  orcid?: string
  affiliations: string[]
  h_index?: number
  citation_count?: number
  works_count?: number
}

export interface PaperAuthor {
  author: Author
  position: number
  is_corresponding: boolean
}

export interface Paper {
  id: string
  organization_id: string
  doi?: string
  source: PaperSource
  source_id?: string
  title: string
  abstract?: string
  publication_date?: string
  journal?: string
  volume?: string
  issue?: string
  pages?: string
  keywords: string[]
  references_count?: number
  citations_count?: number
  has_pdf: boolean
  has_embedding: boolean
  created_at: string
  updated_at: string
}

export interface PaperDetail extends Paper {
  authors: PaperAuthor[]
  mesh_terms: string[]
}

export interface PaperListResponse {
  items: Paper[]
  total: number
  page: number
  page_size: number
  pages: number
}

// Scoring types
export interface PaperScore {
  id: string
  paper_id: string
  organization_id: string
  novelty: number
  novelty_reasoning: string
  ip_potential: number
  ip_potential_reasoning: string
  marketability: number
  marketability_reasoning: string
  feasibility: number
  feasibility_reasoning: string
  commercialization: number
  commercialization_reasoning: string
  overall_score: number
  confidence: number
  model_version: string
  created_at: string
}

export interface ScoreResponse {
  scores: PaperScore
  paper: Paper
}

// Project types
export interface ProjectStage {
  id: string
  name: string
  color: string
  order: number
}

export interface Project {
  id: string
  organization_id: string
  name: string
  description?: string
  stages: ProjectStage[]
  scoring_weights: Record<string, number>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface PaperProjectStatus {
  paper_id: string
  project_id: string
  stage: string
  priority: number
  tags: string[]
  notes?: string
  assigned_to?: string
  rejection_reason?: string
  rejection_notes?: string
  added_at: string
  updated_at: string
}

export interface KanbanPaper extends Paper {
  status: PaperProjectStatus
  latest_score?: PaperScore
}

export interface KanbanColumn {
  stage: ProjectStage
  papers: KanbanPaper[]
  count: number
}

export interface KanbanBoard {
  project: Project
  columns: KanbanColumn[]
}

export interface ProjectStatistics {
  total_papers: number
  by_stage: Record<string, number>
  by_priority: Record<string, number>
  rejection_reasons: Record<string, number>
  average_score?: number
}

// Search types
export type SearchMode = 'fulltext' | 'semantic' | 'hybrid'

export interface SearchRequest {
  query: string
  mode?: SearchMode
  page?: number
  page_size?: number
  sources?: PaperSource[]
  min_score?: number
  max_score?: number
  date_from?: string
  date_to?: string
  has_embedding?: boolean
  has_score?: boolean
  semantic_weight?: number
}

export interface SearchResultHighlight {
  title?: string
  abstract?: string
}

export interface SearchResult {
  paper: Paper
  relevance_score: number
  highlights: SearchResultHighlight
  latest_score?: PaperScore
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
  page: number
  page_size: number
  pages: number
  query: string
  mode: SearchMode
}

// Pagination types
export interface PaginationParams {
  page: number
  page_size: number
}

// API Error types
export interface ApiError {
  detail: string | { msg: string; type: string }[]
}
