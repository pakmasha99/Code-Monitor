import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { Button } from "@/components/ui/button";
import Link from "next/link";

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

  // Get user ID from email (we need to fetch from backend)
  const userEmail = session.user.email;

  async function handleSubmit(formData: FormData) {
    'use server';

    const codeLinesAdded = formData.get('code_lines_added');
    const documentsCreated = formData.get('documents_created');
    const notes = formData.get('notes');
    const weekStartDate = formData.get('week_start_date');

    // First, get user ID from email
    const usersResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users`);
    const users = await usersResponse.json();
    const user = users.find((u: any) => u.email === userEmail);

    if (!user) {
      throw new Error('User not found');
    }

    // Submit the weekly submission
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/users/${user.id}/submissions`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          week_start_date: weekStartDate,
          code_lines_added: parseInt(codeLinesAdded as string) || 0,
          documents_created: parseInt(documentsCreated as string) || 0,
          notes: notes || null,
        }),
      }
    );

    if (response.ok) {
      // Redirect to dashboard on success
      redirect('/dashboard');
    } else {
      const error = await response.json();
      throw new Error(error.detail || 'Submission failed');
    }
  }

  const currentWeekMonday = getCurrentWeekMonday();

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

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 max-w-2xl">
        <div className="rounded-lg border bg-card p-8">
          <h2 className="text-3xl font-bold mb-2">
            Weekly Submission
          </h2>
          <p className="text-muted-foreground mb-8">
            Submit your weekly coding activities for week of <strong>{currentWeekMonday}</strong>
          </p>

          <form action={handleSubmit} className="space-y-6">
            {/* Hidden week start date */}
            <input type="hidden" name="week_start_date" value={currentWeekMonday} />

            {/* Code Lines Added */}
            <div className="space-y-2">
              <label htmlFor="code_lines_added" className="text-sm font-medium">
                📝 Code Lines Added
              </label>
              <input
                type="number"
                id="code_lines_added"
                name="code_lines_added"
                min="0"
                defaultValue="0"
                required
                className="w-full px-4 py-2 rounded-md border bg-background"
                placeholder="e.g., 450"
              />
              <p className="text-xs text-muted-foreground">
                Total lines of code added this week
              </p>
            </div>

            {/* Documents Created */}
            <div className="space-y-2">
              <label htmlFor="documents_created" className="text-sm font-medium">
                📄 Documents Created
              </label>
              <input
                type="number"
                id="documents_created"
                name="documents_created"
                min="0"
                defaultValue="0"
                required
                className="w-full px-4 py-2 rounded-md border bg-background"
                placeholder="e.g., 3"
              />
              <p className="text-xs text-muted-foreground">
                Number of documentation files/pages created
              </p>
            </div>

            {/* Notes */}
            <div className="space-y-2">
              <label htmlFor="notes" className="text-sm font-medium">
                📋 Weekly Notes (Optional)
              </label>
              <textarea
                id="notes"
                name="notes"
                rows={4}
                maxLength={5000}
                className="w-full px-4 py-2 rounded-md border bg-background"
                placeholder="Describe what you worked on this week..."
              />
              <p className="text-xs text-muted-foreground">
                Brief summary of your work this week (max 5000 characters)
              </p>
            </div>

            {/* Submit Button */}
            <div className="flex gap-4 pt-4">
              <Button type="submit" size="lg" className="flex-1">
                ✅ Submit Weekly Report
              </Button>
              <Link href="/dashboard" className="flex-1">
                <Button type="button" variant="outline" size="lg" className="w-full">
                  Cancel
                </Button>
              </Link>
            </div>
          </form>

          {/* Info Box */}
          <div className="mt-8 p-4 rounded-lg bg-muted">
            <h3 className="font-semibold mb-2">ℹ️ Submission Guidelines</h3>
            <ul className="text-sm space-y-1 text-muted-foreground">
              <li>• You can submit once per week (Monday to Sunday)</li>
              <li>• Submissions are used to calculate your weekly ranking</li>
              <li>• Be honest and accurate in your reporting</li>
              <li>• Include meaningful notes to track your progress</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
