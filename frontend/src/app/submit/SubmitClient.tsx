'use client';

import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useEffect, useState } from "react";
import { getGitStats } from "@/lib/api";

interface SubmitClientProps {
  userEmail: string;
  currentWeekMonday: string;
}

export default function SubmitClient({ userEmail, currentWeekMonday }: SubmitClientProps) {
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [autoFetchedLines, setAutoFetchedLines] = useState<number | null>(null);
  const [codeLinesAdded, setCodeLinesAdded] = useState<string>('0');
  const [documentLinesAdded, setDocumentLinesAdded] = useState<string>('0');
  const [submitting, setSubmitting] = useState(false);
  const [customRepoUrls, setCustomRepoUrls] = useState<string[]>(['']);
  const [repoUrlErrors, setRepoUrlErrors] = useState<{ [key: number]: string | null }>({});

  const [existingSubmission, setExistingSubmission] = useState<any | null>(null);

  // Auto-fetch git stats and check existing submission on component mount
  useEffect(() => {
    async function fetchGitStats() {
      try {
        setLoading(true);
        setFetchError(null);

        // Fetch user by email
        const usersResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users`);
        const users = await usersResponse.json();
        const user = users.find((u: any) => u.email === userEmail);

        if (!user) {
          setFetchError('User not found in database');
          setLoading(false);
          return;
        }

        // Check for existing submission for this week
        const submissionsResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users/${user.id}/submissions`);
        const submissions = await submissionsResponse.json();
        const existing = submissions.find((s: any) => s.week_start_date === currentWeekMonday);

        if (existing) {
          setExistingSubmission(existing);
          setCodeLinesAdded(existing.code_lines_added.toString());
          setDocumentLinesAdded((existing.document_lines_added || 0).toString());

          // Parse repository URLs from the stored string
          if (existing.repository_url) {
            const repoUrls = existing.repository_url.split(',').filter((url: string) => url.trim());
            if (repoUrls.length > 0) {
              setCustomRepoUrls(repoUrls);
            }
          }
        }

        // Fetch git stats (use custom repos if provided, otherwise user's default repo)
        const since = new Date(currentWeekMonday).toISOString();
        const nonEmptyCustomRepos = customRepoUrls.filter(url => url.trim());

        // Prefer custom repos, fallback to user's repo_url
        const repoUrlToFetch = nonEmptyCustomRepos.length > 0
          ? nonEmptyCustomRepos[0]  // Use first custom repo for single repo API
          : user.repo_url;

        if (repoUrlToFetch) {
          try {
            const stats = await getGitStats(user.id, since, repoUrlToFetch);

            // Only auto-fill if there's no existing submission
            if (!existing) {
              setAutoFetchedLines(stats.lines_added);
              setCodeLinesAdded(stats.lines_added.toString());
            }
          } catch (statsError: any) {
            console.error('Git stats fetch failed:', statsError);
            // Don't fail the whole page load if git stats fail
            setFetchError(`Git stats: ${statsError.message}`);
          }
        }

      } catch (error: any) {
        console.error('Failed to fetch git stats:', error);
        setFetchError(error.message || 'Unable to fetch git stats automatically');
      } finally {
        setLoading(false);
      }
    }

    fetchGitStats();
  }, [userEmail, currentWeekMonday]);

  // Validate GitHub URL format
  function validateGitHubUrl(url: string): boolean {
    if (!url) return true; // Empty is allowed (optional field)

    // Allow both HTTPS and SSH formats
    const httpsPattern = /^https:\/\/github\.com\/.+\/.+/;
    const sshPattern = /^git@github\.com:.+\/.+\.git$/;

    return httpsPattern.test(url) || sshPattern.test(url);
  }

  // Handle custom repo URL changes with validation
  function handleCustomRepoUrlChange(index: number, value: string) {
    const newUrls = [...customRepoUrls];
    newUrls[index] = value;
    setCustomRepoUrls(newUrls);

    // Validate the URL
    if (value && !validateGitHubUrl(value)) {
      setRepoUrlErrors({...repoUrlErrors, [index]: 'Only GitHub URLs are allowed (e.g., https://github.com/user/repo or git@github.com:user/repo.git)'});
    } else {
      const newErrors = {...repoUrlErrors};
      delete newErrors[index];
      setRepoUrlErrors(newErrors);
    }
  }

  // Add new repository URL field
  function addRepoUrlField() {
    if (customRepoUrls.length < 5) {
      setCustomRepoUrls([...customRepoUrls, '']);
    }
  }

  // Remove repository URL field
  function removeRepoUrlField(index: number) {
    if (customRepoUrls.length > 1) {
      setCustomRepoUrls(customRepoUrls.filter((_, i) => i !== index));
      const newErrors = {...repoUrlErrors};
      delete newErrors[index];
      setRepoUrlErrors(newErrors);
    }
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);

    const formData = new FormData(e.currentTarget);
    const codeLinesAdded = formData.get('code_lines_added');
    const documentLinesAdded = formData.get('document_lines_added');
    const notes = formData.get('notes');
    const weekStartDate = formData.get('week_start_date');

    // Validate all custom repo URLs if provided
    const nonEmptyUrls = customRepoUrls.filter(url => url.trim() !== '');
    for (let i = 0; i < nonEmptyUrls.length; i++) {
      if (!validateGitHubUrl(nonEmptyUrls[i])) {
        alert(`Please enter valid GitHub URLs (Repository ${i + 1} is invalid)`);
        setSubmitting(false);
        return;
      }
    }

    try {
      // Get user ID from email
      const usersResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users`);
      const users = await usersResponse.json();
      const user = users.find((u: any) => u.email === userEmail);

      if (!user) {
        throw new Error('User not found');
      }

      // Prepare submission data
      const submissionData: any = {
        week_start_date: weekStartDate,
        code_lines_added: parseInt(codeLinesAdded as string) || 0,
        document_lines_added: parseInt(documentLinesAdded as string) || 0,
        documents_created: 0, // Deprecated field
        notes: notes || null,
      };

      // Include custom repo URLs if provided (filter out empty strings)
      if (nonEmptyUrls.length > 0) {
        submissionData.custom_repo_urls = nonEmptyUrls;
      }

      let response;

      if (existingSubmission) {
        // UPDATE existing submission (PATCH)
        response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/users/${user.id}/submissions/${existingSubmission.id}`,
          {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(submissionData),
          }
        );
      } else {
        // CREATE new submission (POST)
        response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/users/${user.id}/submissions`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(submissionData),
          }
        );
      }

      if (response.ok) {
        // Redirect to dashboard on success
        window.location.href = '/dashboard';
      } else {
        const error = await response.json();
        alert(error.detail || 'Submission failed');
      }
    } catch (error: any) {
      alert(error.message || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="container mx-auto px-4 py-8 max-w-2xl">
      <div className="rounded-lg border bg-card p-8">
        <h2 className="text-3xl font-bold mb-2">
          {existingSubmission ? '✏️ Update Weekly Submission' : '📝 Weekly Submission'}
        </h2>
        <p className="text-muted-foreground mb-8">
          {existingSubmission
            ? <>Update your weekly submission for week of <strong>{currentWeekMonday}</strong></>
            : <>Submit your weekly coding activities for week of <strong>{currentWeekMonday}</strong></>
          }
        </p>

        {/* Existing submission notification */}
        {existingSubmission && (
          <div className="mb-6 p-4 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900">
            <p className="text-sm text-blue-700 dark:text-blue-400 font-semibold">
              ℹ️ You already have a submission for this week
            </p>
            <p className="text-xs text-blue-600 dark:text-blue-300 mt-1">
              Current values have been loaded. You can update them below.
            </p>
          </div>
        )}

        {/* Auto-fetch status */}
        {loading && (
          <div className="mb-6 p-4 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900">
            <p className="text-sm text-blue-700 dark:text-blue-400">
              🔄 Fetching your git statistics...
            </p>
          </div>
        )}

        {!loading && autoFetchedLines !== null && (
          <div className="mb-6 p-4 rounded-lg bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900">
            <p className="text-sm text-green-700 dark:text-green-400">
              ✅ Auto-fetched from your GitHub: <strong>{autoFetchedLines}</strong> lines added this week
            </p>
          </div>
        )}

        {!loading && fetchError && (
          <div className="mb-6 p-4 rounded-lg bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-900">
            <p className="text-sm text-yellow-700 dark:text-yellow-400">
              ⚠️ {fetchError}
            </p>
            <p className="text-xs text-yellow-600 dark:text-yellow-500 mt-1">
              Please enter your code lines manually or add your GitHub repository URL in your profile.
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
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
              value={codeLinesAdded}
              onChange={(e) => setCodeLinesAdded(e.target.value)}
              required
              disabled={loading}
              className="w-full px-4 py-2 rounded-md border bg-background disabled:opacity-50"
              placeholder="e.g., 450"
            />
            <p className="text-xs text-muted-foreground">
              {autoFetchedLines !== null
                ? 'Auto-fetched from GitHub (you can modify if needed)'
                : 'Total lines of code added this week'}
            </p>
          </div>

          {/* Custom Repository URLs (Optional) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">
                🔗 Custom Repository URLs <span className="text-muted-foreground font-normal">(Optional, max 5)</span>
              </label>
              {customRepoUrls.length < 5 && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addRepoUrlField}
                  disabled={loading || submitting}
                  className="h-8 px-3"
                >
                  ➕ Add Repository
                </Button>
              )}
            </div>

            <p className="text-xs text-muted-foreground">
              Leave empty to use your default repository. Add custom repositories for team projects, lab work, or organization projects.
            </p>

            {customRepoUrls.map((url, index) => (
              <div key={index} className="space-y-2">
                <div className="flex gap-2">
                  <div className="flex-1">
                    <input
                      type="text"
                      value={url}
                      onChange={(e) => handleCustomRepoUrlChange(index, e.target.value)}
                      disabled={loading || submitting}
                      className={`w-full px-4 py-2 rounded-md border bg-background disabled:opacity-50 ${
                        repoUrlErrors[index] ? 'border-red-500' : ''
                      }`}
                      placeholder={`Repository ${index + 1}: e.g., https://github.com/Transconnectome/connectome-kb`}
                    />
                    {repoUrlErrors[index] && (
                      <p className="text-xs text-red-500 mt-1">
                        {repoUrlErrors[index]}
                      </p>
                    )}
                  </div>
                  {customRepoUrls.length > 1 && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => removeRepoUrlField(index)}
                      disabled={loading || submitting}
                      className="h-10 px-3 text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      ✖
                    </Button>
                  )}
                </div>
              </div>
            ))}

            {customRepoUrls.filter(url => url.trim() !== '').length > 0 &&
             Object.keys(repoUrlErrors).length === 0 && (
              <div className="mt-2 p-3 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900">
                <p className="text-xs text-blue-700 dark:text-blue-400 font-semibold mb-1">
                  📍 This week's submission will use:
                </p>
                <ul className="text-xs text-blue-600 dark:text-blue-300 space-y-1">
                  {customRepoUrls.filter(url => url.trim() !== '').map((url, idx) => (
                    <li key={idx} className="font-mono">• {url}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Document Lines Added */}
          <div className="space-y-2">
            <label htmlFor="document_lines_added" className="text-sm font-medium">
              📄 Document Lines Added
            </label>
            <input
              type="number"
              id="document_lines_added"
              name="document_lines_added"
              min="0"
              value={documentLinesAdded}
              onChange={(e) => setDocumentLinesAdded(e.target.value)}
              required
              disabled={loading}
              className="w-full px-4 py-2 rounded-md border bg-background disabled:opacity-50"
              placeholder="e.g., 320"
            />
            <p className="text-xs text-muted-foreground">
              Total lines from documents (PDFs, markdown, text files, etc.)
            </p>
            <p className="text-xs text-blue-600 dark:text-blue-400">
              💡 Tip: Use our DocumentAnalyzer to count lines in PDFs automatically
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
              disabled={loading}
              className="w-full px-4 py-2 rounded-md border bg-background disabled:opacity-50"
              placeholder="Describe what you worked on this week..."
            />
            <p className="text-xs text-muted-foreground">
              Brief summary of your work this week (max 5000 characters)
            </p>
          </div>

          {/* Submit Button */}
          <div className="flex gap-4 pt-4">
            <Button
              type="submit"
              size="lg"
              className="flex-1"
              disabled={loading || submitting}
            >
              {submitting
                ? (existingSubmission ? '⏳ Updating...' : '⏳ Submitting...')
                : (existingSubmission ? '✅ Update Weekly Report' : '✅ Submit Weekly Report')
              }
            </Button>
            <Link href="/dashboard" className="flex-1">
              <Button type="button" variant="outline" size="lg" className="w-full" disabled={submitting}>
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
            <li>• Git statistics are automatically fetched from your default GitHub repository</li>
            <li>• You can specify up to 5 custom repository URLs for team projects, lab work, or organization projects</li>
            <li>• You can modify auto-fetched values if needed</li>
            <li>• Include meaningful notes to track your progress</li>
          </ul>
        </div>
      </div>
    </main>
  );
}
