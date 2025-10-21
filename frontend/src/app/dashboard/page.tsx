import { auth, signOut } from "@/auth";
import { redirect } from "next/navigation";
import { Button } from "@/components/ui/button";
import { LogOut, Plus, Search } from "lucide-react";
import Link from "next/link";
import { getCurrentWeekRankings } from "@/lib/api";
import { LeaderboardChart } from "@/components/charts/LeaderboardChart";
import { ActivityChart } from "@/components/charts/ActivityChart";
import { ScoreBreakdownChart } from "@/components/charts/ScoreBreakdownChart";

// Force dynamic rendering to prevent caching of session state
export const dynamic = 'force-dynamic';

export default async function DashboardPage() {
  const session = await auth();

  if (!session?.user) {
    redirect('/');
  }

  // Fetch user's own stats and activity data
  let userStats = {
    rank: 0,
    score: 0,
    linesAdded: 0,
    codeLines: 0,
    documentLines: 0,
    commits: 0,
    productivity: 0
  };
  let activityData: Array<{ week: string; commits: number; lines: number; score: number }> = [];

  try {
    // Get all users to find current user's ID
    const usersResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users`);
    const users = await usersResponse.json();
    const currentUser = users.find((u: any) => u.email === session.user!.email);

    if (currentUser) {
      // Get rankings to find user's rank and score
      const rankings = await getCurrentWeekRankings();
      const userRanking = rankings.find(r => r.user_name === currentUser.name);

      if (userRanking) {
        userStats.rank = userRanking.rank_position;
        userStats.score = userRanking.total_score;
        userStats.productivity = userRanking.category_scores?.productivity || userRanking.total_score;
      }

      // Get user's submissions to get lines added and build activity data
      const submissionsResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/users/${currentUser.id}/submissions`
      );
      const submissions = await submissionsResponse.json();

      // Build activity data from real submissions
      if (submissions.length > 0) {
        const latestSubmission = submissions[0]; // Most recent first from API
        userStats.codeLines = latestSubmission.code_lines_added || 0;
        userStats.documentLines = latestSubmission.document_lines_added || 0;
        userStats.linesAdded = userStats.codeLines + userStats.documentLines;

        // Convert submissions to activity chart format (last 4 weeks)
        activityData = submissions.slice(0, 4).reverse().map((sub: any, index: number) => {
          const weekDate = new Date(sub.week_start_date);
          const weekLabel = `Week ${index + 1} (${weekDate.getMonth() + 1}/${weekDate.getDate()})`;

          return {
            week: weekLabel,
            commits: 0, // We don't track commits in submissions yet
            lines: sub.code_lines_added,
            score: 0, // Will be filled from rankings if available
          };
        });

        // Try to get ranking history to fill in scores
        try {
          const rankingHistoryResponse = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/api/users/${currentUser.id}/ranking/history`
          );
          const rankingHistory = await rankingHistoryResponse.json();

          // Match rankings to activity data by week_start_date
          activityData = activityData.map(activity => {
            const matchingRanking = rankingHistory.find((r: any) => {
              const activityWeek = activity.week.match(/\((\d+)\/(\d+)\)/);
              if (!activityWeek) return false;

              const rankingDate = new Date(r.week_start_date);
              return rankingDate.getMonth() + 1 === parseInt(activityWeek[1]) &&
                     rankingDate.getDate() === parseInt(activityWeek[2]);
            });

            return {
              ...activity,
              score: matchingRanking ? matchingRanking.total_score : 0,
            };
          });
        } catch (error) {
          console.error('Failed to fetch ranking history:', error);
        }
      }
    }
  } catch (error) {
    console.error('Failed to fetch user stats:', error);
  }

  // Fetch real leaderboard data from FastAPI
  let leaderboardData;
  try {
    const rankings = await getCurrentWeekRankings();

    // If API returns empty array, use mock data for demonstration
    if (rankings.length === 0) {
      leaderboardData = [
        { name: '이영희', score: 130, rank: 1 },
        { name: '김철수', score: 80, rank: 2 },
        { name: '박민수', score: 65, rank: 3 },
      ];
    } else {
      leaderboardData = rankings.slice(0, 10).map(ranking => ({
        name: ranking.user_name,  // Backend returns user_name directly
        score: ranking.total_score,
        rank: ranking.rank_position,  // Backend returns rank_position
      }));
    }
  } catch (error) {
    // Fallback to mock data if API is not available
    console.error('Failed to fetch leaderboard:', error);
    leaderboardData = [
      { name: '이영희', score: 130, rank: 1 },
      { name: '김철수', score: 80, rank: 2 },
      { name: '박민수', score: 65, rank: 3 },
    ];
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold">🎯 Code-Monitor</h1>
            <span className="text-sm text-muted-foreground">Dashboard</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/submit">
              <Button variant="default" size="sm">
                <Plus className="h-4 w-4 mr-2" />
                Weekly Submit
              </Button>
            </Link>
            <Link href="/code-search">
              <Button variant="outline" size="sm">
                <Search className="h-4 w-4 mr-2" />
                Code Q&A
              </Button>
            </Link>
            <div className="text-sm text-right">
              <p className="font-medium">{session.user.name}</p>
              <p className="text-muted-foreground">{session.user.email}</p>
            </div>
            <form
              action={async () => {
                "use server"
                await signOut({ redirectTo: "/" })
              }}
            >
              <Button type="submit" variant="outline" size="sm">
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </form>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="space-y-8">
          {/* Welcome Section */}
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-3xl font-bold mb-2">
              Welcome back, {session.user.name}! 👋
            </h2>
            <p className="text-muted-foreground">
              Here's your weekly coding performance overview
            </p>
          </div>

          {/* Stats Grid - Bento Style */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="rounded-lg border bg-card p-6">
              <div className="text-4xl mb-2">📊</div>
              <h3 className="font-semibold text-lg mb-1">Your Rank</h3>
              <p className="text-3xl font-bold text-primary">
                {userStats.rank > 0 ? `#${userStats.rank}` : 'N/A'}
              </p>
              <p className="text-sm text-muted-foreground mt-1">This week</p>
            </div>

            <div className="rounded-lg border bg-card p-6">
              <div className="text-4xl mb-2">⚡</div>
              <h3 className="font-semibold text-lg mb-1">Total Score</h3>
              <p className="text-3xl font-bold text-primary">{userStats.score.toLocaleString()}</p>
              <p className="text-sm text-muted-foreground mt-1">Points</p>
            </div>

            <div className="rounded-lg border bg-card p-6">
              <div className="text-4xl mb-2">💻</div>
              <h3 className="font-semibold text-lg mb-1">Lines Added</h3>
              <p className="text-3xl font-bold text-primary">{userStats.linesAdded.toLocaleString()}</p>
              <p className="text-sm text-muted-foreground mt-1">This week</p>
            </div>
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Leaderboard Chart */}
            <div className="rounded-lg border bg-card p-6">
              <h2 className="text-2xl font-bold mb-4">📊 Leaderboard Visualization</h2>
              <LeaderboardChart data={leaderboardData} />
            </div>

            {/* Score Breakdown */}
            <div className="rounded-lg border bg-card p-6">
              <h2 className="text-2xl font-bold mb-4">🎯 Your Lines Breakdown</h2>
              <ScoreBreakdownChart
                codeLines={userStats.codeLines}
                documentLines={userStats.documentLines}
              />
            </div>
          </div>

          {/* Activity Trend Chart */}
          {activityData.length > 0 && (
            <div className="rounded-lg border bg-card p-6">
              <h2 className="text-2xl font-bold mb-4">📈 Your Activity Trend (Last {activityData.length} Week{activityData.length > 1 ? 's' : ''})</h2>
              <ActivityChart data={activityData} />
            </div>
          )}

          {/* Leaderboard Table */}
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-2xl font-bold mb-6">🏆 Current Week Leaderboard</h2>
            <div className="space-y-4">
              {leaderboardData.slice(0, 3).map((entry, index) => {
                const medals = ['🥇', '🥈', '🥉'];
                const bgColors = [
                  'bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-900',
                  'bg-slate-50 dark:bg-slate-950/20 border',
                  'bg-orange-50 dark:bg-orange-950/20 border-orange-200 dark:border-orange-900'
                ];
                const textColors = [
                  'text-amber-600 dark:text-amber-500',
                  'text-slate-600 dark:text-slate-400',
                  'text-orange-600 dark:text-orange-500'
                ];

                return (
                  <div
                    key={index}
                    className={`flex items-center gap-4 p-4 rounded-lg ${bgColors[index]}`}
                  >
                    <div className="text-3xl">{medals[index]}</div>
                    <div className="flex-1">
                      <p className="font-semibold text-lg">{entry.name}</p>
                      <p className="text-sm text-muted-foreground">Rank #{entry.rank}</p>
                    </div>
                    <div className="text-right">
                      <p className={`text-2xl font-bold ${textColors[index]}`}>{entry.score.toLocaleString()}</p>
                      <p className="text-sm text-muted-foreground">lines</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
