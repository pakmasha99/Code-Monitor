import { Button } from "@/components/ui/button";
import { Github } from "lucide-react";
import { signIn, auth } from "@/auth";
import { redirect } from "next/navigation";

// Force dynamic rendering to prevent caching of session state
export const dynamic = 'force-dynamic';

export default async function Home() {
  const session = await auth();

  // If user is already signed in, redirect to dashboard
  if (session?.user) {
    redirect('/dashboard');
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-br from-background to-muted">
      <div className="text-center space-y-8 max-w-2xl">
        <div className="space-y-4">
          <h1 className="text-6xl font-bold tracking-tight">
            🎯 Code-Monitor
          </h1>
          <p className="text-2xl font-medium text-primary">
            Developer Performance Dashboard
          </p>
          <p className="text-lg text-muted-foreground">
            Track your team's coding performance with weekly rankings,
            visualize progress, and celebrate achievements together.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <form
            action={async () => {
              "use server"
              await signIn("github", { redirectTo: "/dashboard" })
            }}
          >
            <Button type="submit" size="lg" className="gap-2">
              <Github className="h-5 w-5" />
              Sign in with GitHub
            </Button>
          </form>
          <Button size="lg" variant="outline">
            Learn More
          </Button>
        </div>

        <div className="grid grid-cols-3 gap-8 pt-12">
          <div className="space-y-2">
            <div className="text-4xl font-bold text-primary">📊</div>
            <h3 className="font-semibold">Weekly Rankings</h3>
            <p className="text-sm text-muted-foreground">
              Compete with your team
            </p>
          </div>
          <div className="space-y-2">
            <div className="text-4xl font-bold text-primary">📈</div>
            <h3 className="font-semibold">Live Dashboard</h3>
            <p className="text-sm text-muted-foreground">
              Real-time metrics
            </p>
          </div>
          <div className="space-y-2">
            <div className="text-4xl font-bold text-primary">🏆</div>
            <h3 className="font-semibold">Achievements</h3>
            <p className="text-sm text-muted-foreground">
              Track your progress
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
