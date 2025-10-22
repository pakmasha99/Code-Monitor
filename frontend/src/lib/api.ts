/**
 * API Client for FastAPI Backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface User {
  id: number;
  name: string;
  email: string;
  github_username?: string;
  repo_url?: string;
  created_at: string;
}

export interface WeeklySubmission {
  id: number;
  user_id: number;
  week_start: string;
  lines_added: number;
  documents_created: number;
  created_at: string;
}

export interface Ranking {
  id: number;
  user_id: number;
  week_start: string;
  rank: number;
  total_score: number;
  productivity_score: number;
  quality_score: number;
  consistency_score: number;
  user?: User;
}

// Backend response schema for current week rankings
export interface CurrentWeekRankingResponse {
  rank_position: number;
  user_id: number;
  user_name: string;
  user_email: string;
  total_score: number;
  category_scores: {
    productivity: number;
    quality: number;
    consistency: number;
  };
  week_start_date: string;
}

export interface LeaderboardEntry extends Ranking {
  user: User;
}

export interface GitStatsResponse {
  commits_count: number;
  files_changed: number;
  code_lines_added: number;
  document_lines_added: number;
  lines_added: number;
  lines_deleted: number;
  languages_breakdown: Record<string, number>;
  analyzed_since: string;
  repo_url: string;
}

/**
 * Fetch all users
 */
export async function getUsers(): Promise<User[]> {
  const response = await fetch(`${API_URL}/api/users`);
  if (!response.ok) {
    throw new Error('Failed to fetch users');
  }
  return response.json();
}

/**
 * Get user by ID
 */
export async function getUser(userId: number): Promise<User> {
  const response = await fetch(`${API_URL}/api/users/${userId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch user');
  }
  return response.json();
}

/**
 * Create a new user
 */
export async function createUser(userData: {
  name: string;
  email: string;
  github_username?: string;
  repo_url?: string;
}): Promise<User> {
  const response = await fetch(`${API_URL}/api/users`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });
  if (!response.ok) {
    throw new Error('Failed to create user');
  }
  return response.json();
}

/**
 * Get current week rankings (leaderboard)
 */
export async function getCurrentWeekRankings(): Promise<CurrentWeekRankingResponse[]> {
  const response = await fetch(`${API_URL}/api/rankings/current`);
  if (!response.ok) {
    throw new Error('Failed to fetch rankings');
  }
  return response.json();
}

/**
 * Get rankings for a specific week
 */
export async function getRankingsForWeek(weekStart: string): Promise<LeaderboardEntry[]> {
  const response = await fetch(`${API_URL}/api/rankings/week/${weekStart}`);
  if (!response.ok) {
    throw new Error('Failed to fetch week rankings');
  }
  return response.json();
}

/**
 * Get top N rankings
 */
export async function getTopRankings(limit: number = 10): Promise<LeaderboardEntry[]> {
  const response = await fetch(`${API_URL}/api/rankings/top/${limit}`);
  if (!response.ok) {
    throw new Error('Failed to fetch top rankings');
  }
  return response.json();
}

/**
 * Get user ranking history
 */
export async function getUserRankingHistory(userId: number): Promise<Ranking[]> {
  const response = await fetch(`${API_URL}/api/users/${userId}/ranking/history`);
  if (!response.ok) {
    throw new Error('Failed to fetch user ranking history');
  }
  return response.json();
}

/**
 * Update rankings for a specific week
 */
export async function updateRankings(weekStart?: string): Promise<{ message: string; users_updated: number }> {
  const url = weekStart
    ? `${API_URL}/api/rankings/update/${weekStart}`
    : `${API_URL}/api/rankings/update`;

  const response = await fetch(url, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to update rankings');
  }
  return response.json();
}

/**
 * Get weekly submissions for a user
 */
export async function getUserSubmissions(userId: number): Promise<WeeklySubmission[]> {
  const response = await fetch(`${API_URL}/api/submissions/user/${userId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch user submissions');
  }
  return response.json();
}

/**
 * Create a weekly submission
 */
export async function createSubmission(submissionData: {
  user_id: number;
  week_start: string;
  lines_added: number;
  documents_created: number;
}): Promise<WeeklySubmission> {
  const response = await fetch(`${API_URL}/api/submissions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(submissionData),
  });
  if (!response.ok) {
    throw new Error('Failed to create submission');
  }
  return response.json();
}

/**
 * Health check
 */
export async function healthCheck(): Promise<{ status: string; database: string }> {
  const response = await fetch(`${API_URL}/health`);
  if (!response.ok) {
    throw new Error('API is not healthy');
  }
  return response.json();
}

/**
 * Get git statistics for a user's repository
 */
export async function getGitStats(
  userId: number,
  since: string,
  repoUrl?: string
): Promise<GitStatsResponse> {
  const params = new URLSearchParams({ since });
  if (repoUrl) {
    params.append('repo_url', repoUrl);
  }

  const response = await fetch(`${API_URL}/api/users/${userId}/git-stats?${params.toString()}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch git stats');
  }
  return response.json();
}

/**
 * Get git statistics for multiple repositories (aggregated)
 */
export async function getGitStatsMultiRepo(
  userId: number,
  since: string,
  repoUrls: string[]
): Promise<GitStatsResponse> {
  const params = new URLSearchParams({ since });
  // Join multiple repo URLs with comma
  params.append('repo_urls', repoUrls.join(','));

  const response = await fetch(`${API_URL}/api/users/${userId}/git-stats?${params.toString()}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch git stats');
  }
  return response.json();
}

// ============================================================================
// RAG (Code Search & Q&A) API
// ============================================================================

export interface SearchResult {
  id: string;
  content: string;
  score: number;
  file_path?: string;
  language?: string;
  function_name?: string;
  summary?: string;
}

export interface SearchResponse {
  query: string;
  search_type: string;
  alpha?: number;
  results: SearchResult[];
  total: number;
}

export interface AskResponse {
  question: string;
  answer: string;
  sources: SearchResult[];
  confidence: number;
}

export interface ReindexResponse {
  status: string;
  task_id?: string;
  message: string;
}

/**
 * Search code using RAG (hybrid search)
 */
export async function searchCode(
  query: string,
  searchType: 'bm25' | 'vector' | 'hybrid' = 'hybrid',
  limit: number = 10
): Promise<SearchResponse> {
  const response = await fetch(`${API_URL}/api/v1/rag/search`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      query,
      limit,
      search_type: searchType
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Code search failed');
  }

  return response.json();
}

/**
 * Ask a question about the codebase
 */
export async function askCodeQuestion(
  question: string,
  maxContext: number = 5
): Promise<AskResponse> {
  const response = await fetch(`${API_URL}/api/v1/rag/ask`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      question,
      max_context: maxContext,
      include_sources: true
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Question answering failed');
  }

  return response.json();
}

/**
 * Trigger codebase reindexing for a user
 */
export async function triggerReindex(userId: number): Promise<ReindexResponse> {
  const response = await fetch(`${API_URL}/api/v1/rag/reindex`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ user_id: userId })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Reindex failed');
  }

  return response.json();
}
