import { auth, signOut } from "@/auth";
import { redirect } from "next/navigation";
import { Button } from "@/components/ui/button";
import { LogOut } from "lucide-react";
import { getCurrentWeekRankings } from "@/lib/api";
import { LeaderboardChart } from "@/components/charts/LeaderboardChart";
import { ActivityChart } from "@/components/charts/ActivityChart";
import { ScoreBreakdownChart } from "@/components/charts/ScoreBreakdownChart";

// Mock data for charts (will be replaced with real API data)
const mockActivityData = [
  { week: 'Week 1', commits: 12, lines: 450, score: 65 },
  { week: 'Week 2', commits: 15, lines: 850, score: 80 },
  { week: 'Week 3', commits: 10, lines: 600, score: 70 },
  { week: 'Week 4', commits: 18, lines: 920, score: 95 },
];

export default async function DashboardPage() {
  const session = await auth();

  if (!session?.user) {
    redirect('/');
  }

  // Fetch real leaderboard data from FastAPI
  let leaderboardData;
  try {
    const rankings = await getCurrentWeekRankings();
    leaderboardData = rankings.slice(0, 10).map(ranking => ({
      name: ranking.user_name,  // Backend returns user_name directly
      score: ranking.total_score,
      rank: ranking.rank_position,  // Backend returns rank_position
    }));
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="rounded-lg border bg-card p-6">
              <div className="text-4xl mb-2">📊</div>
              <h3 className="font-semibold text-lg mb-1">Your Rank</h3>
              <p className="text-3xl font-bold text-primary">#2</p>
              <p className="text-sm text-muted-foreground mt-1">This week</p>
            </div>

            <div className="rounded-lg border bg-card p-6">
              <div className="text-4xl mb-2">⚡</div>
              <h3 className="font-semibold text-lg mb-1">Total Score</h3>
              <p className="text-3xl font-bold text-primary">80</p>
              <p className="text-sm text-muted-foreground mt-1">Points</p>
            </div>

            <div className="rounded-lg border bg-card p-6">
              <div className="text-4xl mb-2">💻</div>
              <h3 className="font-semibold text-lg mb-1">Lines Added</h3>
              <p className="text-3xl font-bold text-primary">850</p>
              <p className="text-sm text-muted-foreground mt-1">This week</p>
            </div>

            <div className="rounded-lg border bg-card p-6">
              <div className="text-4xl mb-2">🔥</div>
              <h3 className="font-semibold text-lg mb-1">Commits</h3>
              <p className="text-3xl font-bold text-primary">15</p>
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
              <h2 className="text-2xl font-bold mb-4">🎯 Your Score Breakdown</h2>
              <ScoreBreakdownChart
                productivity={80}
                quality={0}
                consistency={0}
              />
            </div>
          </div>

          {/* Activity Trend Chart */}
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-2xl font-bold mb-4">📈 Your Activity Trend (Last 4 Weeks)</h2>
            <ActivityChart data={mockActivityData} />
          </div>

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
                      <p className={`text-2xl font-bold ${textColors[index]}`}>{entry.score}</p>
                      <p className="text-sm text-muted-foreground">points</p>
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
