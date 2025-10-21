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
