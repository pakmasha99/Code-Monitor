'use client';

import { useState } from 'react';
import { searchCode, askCodeQuestion, type SearchResult, type SearchResponse, type AskResponse } from '@/lib/api';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export default function CodeSearchPage() {
  const [activeTab, setActiveTab] = useState<'search' | 'ask'>('search');

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState<'bm25' | 'vector' | 'hybrid'>('hybrid');
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Q&A state
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [askLoading, setAskLoading] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearchLoading(true);
    setSearchError(null);

    try {
      const results = await searchCode(searchQuery, searchType, 10);
      setSearchResults(results);
    } catch (error: any) {
      setSearchError(error.message || 'Search failed');
    } finally {
      setSearchLoading(false);
    }
  }

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;

    setAskLoading(true);
    setAskError(null);

    try {
      const response = await askCodeQuestion(question, 5);
      setAnswer(response);
    } catch (error: any) {
      setAskError(error.message || 'Question answering failed');
    } finally {
      setAskLoading(false);
    }
  }

  return (
    <main className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">🔍 Code Search & Q&A</h1>
        <p className="text-muted-foreground">
          Search through your codebase or ask questions using RAG (Retrieval-Augmented Generation)
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 border-b">
        <button
          onClick={() => setActiveTab('search')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'search'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Code Search
        </button>
        <button
          onClick={() => setActiveTab('ask')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'ask'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Q&A
        </button>
      </div>

      {/* Search Tab */}
      {activeTab === 'search' && (
        <div className="space-y-6">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex gap-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search for functions, classes, or code patterns..."
                className="flex-1 px-4 py-2 rounded-md border bg-background"
                disabled={searchLoading}
              />
              <Button type="submit" disabled={searchLoading || !searchQuery.trim()}>
                {searchLoading ? 'Searching...' : 'Search'}
              </Button>
            </div>

            <div className="flex gap-4 items-center">
              <span className="text-sm text-muted-foreground">Search Type:</span>
              <div className="flex gap-2">
                {(['hybrid', 'bm25', 'vector'] as const).map((type) => (
                  <label key={type} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="searchType"
                      value={type}
                      checked={searchType === type}
                      onChange={() => setSearchType(type)}
                      disabled={searchLoading}
                    />
                    <span className="text-sm">{type.toUpperCase()}</span>
                  </label>
                ))}
              </div>
            </div>
          </form>

          {searchError && (
            <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900">
              <p className="text-sm text-red-700 dark:text-red-400">{searchError}</p>
            </div>
          )}

          {searchResults && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">
                  Results ({searchResults.total})
                </h2>
                <span className="text-sm text-muted-foreground">
                  Search type: {searchResults.search_type}
                </span>
              </div>

              {searchResults.results.length === 0 ? (
                <p className="text-center py-8 text-muted-foreground">
                  No results found. Try a different query or reindex your codebase.
                </p>
              ) : (
                <div className="space-y-4">
                  {searchResults.results.map((result) => (
                    <div
                      key={result.id}
                      className="p-4 rounded-lg border bg-card hover:bg-accent transition-colors"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <p className="font-mono text-sm text-muted-foreground">
                            {result.file_path}
                            {result.function_name && ` → ${result.function_name}`}
                          </p>
                          {result.language && (
                            <span className="inline-block mt-1 px-2 py-0.5 text-xs rounded bg-primary/10 text-primary">
                              {result.language}
                            </span>
                          )}
                        </div>
                        <span className="text-sm font-medium text-muted-foreground">
                          Score: {(result.score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <pre className="mt-2 p-3 rounded bg-muted overflow-x-auto text-sm">
                        <code>{result.content}</code>
                      </pre>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Q&A Tab */}
      {activeTab === 'ask' && (
        <div className="space-y-6">
          <form onSubmit={handleAsk} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="question" className="text-sm font-medium">
                Ask a question about your codebase
              </label>
              <textarea
                id="question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="e.g., How does authentication work in this codebase?"
                rows={3}
                className="w-full px-4 py-2 rounded-md border bg-background"
                disabled={askLoading}
              />
            </div>
            <Button type="submit" disabled={askLoading || !question.trim()}>
              {askLoading ? 'Thinking...' : 'Ask Question'}
            </Button>
          </form>

          {askError && (
            <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900">
              <p className="text-sm text-red-700 dark:text-red-400">{askError}</p>
            </div>
          )}

          {answer && (
            <div className="space-y-6">
              <div className="p-6 rounded-lg border bg-card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold">Answer</h2>
                  <span className="text-sm text-muted-foreground">
                    Confidence: {(answer.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="prose dark:prose-invert max-w-none">
                  <p className="whitespace-pre-wrap">{answer.answer}</p>
                </div>
              </div>

              {answer.sources.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Sources ({answer.sources.length})</h3>
                  <div className="space-y-3">
                    {answer.sources.map((source) => (
                      <div
                        key={source.id}
                        className="p-4 rounded-lg border bg-card"
                      >
                        <p className="font-mono text-sm text-muted-foreground mb-2">
                          {source.file_path}
                          {source.function_name && ` → ${source.function_name}`}
                        </p>
                        <pre className="p-3 rounded bg-muted overflow-x-auto text-xs">
                          <code>{source.content}</code>
                        </pre>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Back to Dashboard */}
      <div className="mt-8">
        <Link href="/dashboard">
          <Button variant="outline">← Back to Dashboard</Button>
        </Link>
      </div>
    </main>
  );
}
