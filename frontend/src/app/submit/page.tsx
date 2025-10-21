import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import SubmitClient from "./SubmitClient";

// Force dynamic rendering
export const dynamic = 'force-dynamic';

// Helper function to get current week's Monday
function getCurrentWeekMonday(): string {
  const today = new Date();
  const dayOfWeek = today.getDay();
  const diff = dayOfWeek === 0 ? -6 : 1 - dayOfWeek; // Adjust for Sunday (0)
  const monday = new Date(today);
  monday.setDate(today.getDate() + diff);
  return monday.toISOString().split('T')[0];
}

export default async function SubmitPage() {
  const session = await auth();

  if (!session?.user) {
    redirect('/');
  }

  const currentWeekMonday = getCurrentWeekMonday();
  const userEmail = session.user.email!;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold">🎯 Code-Monitor</h1>
            <span className="text-sm text-muted-foreground">Weekly Submit</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/dashboard">
              <Button variant="outline" size="sm">
                ← Back to Dashboard
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Client Component with Auto-fetch Logic */}
      <SubmitClient userEmail={userEmail} currentWeekMonday={currentWeekMonday} />
    </div>
  );
}
