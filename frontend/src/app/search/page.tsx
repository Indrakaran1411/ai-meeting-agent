'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { 
  Search, 
  Brain, 
  Calendar, 
  Clock, 
  Sparkles, 
  ArrowRight,
  MessageSquare,
  FileText,
  AlertCircle
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

export default function SemanticSearchPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeQuery, setActiveQuery] = useState('');

  // Run semantic search query using React Query
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['semantic-search', activeQuery],
    queryFn: () => api.semanticSearch(activeQuery, 15),
    enabled: activeQuery.trim() !== '',
    retry: false,
  });

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      setActiveQuery(searchTerm.trim());
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  // Convert similarity score to a percentage representation
  const formatScore = (score: number) => {
    const percentage = Math.round(score * 100);
    return `${percentage}% Match`;
  };

  const getScoreBadgeColor = (score: number) => {
    if (score >= 0.8) return 'bg-emerald-50 text-emerald-700 border-emerald-100 dark:bg-emerald-500/10 dark:text-emerald-400';
    if (score >= 0.6) return 'bg-indigo-50 text-indigo-700 border-indigo-100 dark:bg-indigo-500/10 dark:text-indigo-400';
    return 'bg-amber-50 text-amber-700 border-amber-100 dark:bg-amber-500/10 dark:text-amber-400';
  };

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Brain className="h-6 w-6 text-indigo-600 animate-pulse" />
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 bg-clip-text text-transparent">
            AI Semantic Search
          </h1>
        </div>
        <p className="text-muted-foreground text-sm">
          Query corporate intelligence using vector embeddings. Locate meetings and relevant transcripts by contextual meaning, not just exact keywords.
        </p>
      </div>

      {/* Search Input Box */}
      <Card className="border-slate-100 shadow-sm bg-gradient-to-br from-indigo-50/30 to-purple-50/10">
        <CardContent className="p-6">
          <form onSubmit={handleSearchSubmit} className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                type="text"
                placeholder="e.g., authentication service blocker, database schema migrations, roadmap dates..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 h-12 bg-white border-slate-200/80 focus-visible:ring-indigo-500"
              />
            </div>
            <Button 
              type="submit" 
              className="h-12 px-6 bg-indigo-600 hover:bg-indigo-700 transition-colors font-medium gap-2"
              disabled={isLoading}
            >
              {isLoading ? (
                <Sparkles className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              Search AI
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Search results listing */}
      <div className="space-y-4">
        {activeQuery && (
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              Showing AI results for &quot;<strong className="text-slate-900">{activeQuery}</strong>&quot;
            </span>
            {data && <span>Found {data.results.length} relevant matches</span>}
          </div>
        )}

        {isLoading && (
          <div className="space-y-4">
            {[1, 2, 3].map((n) => (
              <Card key={n} className="border-slate-100 animate-pulse">
                <CardContent className="p-6 space-y-4">
                  <div className="flex justify-between items-start">
                    <div className="space-y-2 flex-1">
                      <div className="h-5 bg-slate-100 rounded w-1/3"></div>
                      <div className="h-3 bg-slate-100 rounded w-1/4"></div>
                    </div>
                    <div className="h-6 bg-slate-100 rounded w-16"></div>
                  </div>
                  <div className="h-12 bg-slate-50 rounded"></div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {isError && (
          <Card className="border-red-100 bg-red-50/30">
            <CardContent className="p-6 flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-900">Semantic Search Error</h3>
                <p className="text-sm text-red-700/90 mt-1">
                  {error instanceof Error ? error.message : 'An unexpected error occurred while performing semantic search.'}
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {data && data.results.length === 0 && (
          <Card className="border-slate-100 py-12 text-center">
            <CardContent className="space-y-2">
              <AlertCircle className="h-8 w-8 text-slate-300 mx-auto" />
              <h3 className="font-medium text-slate-800">No Semantic Matches Found</h3>
              <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                No matching summaries or transcript segments were found for your query. Try adjusting your search query or rephrase it.
              </p>
            </CardContent>
          </Card>
        )}

        {data && data.results.length > 0 && (
          <div className="space-y-4">
            {data.results.map((result, idx) => {
              const meeting = result.meeting;
              return (
                <Card 
                  key={`${meeting.id}-${idx}`} 
                  className="border-slate-100 hover:border-indigo-100 shadow-sm hover:shadow-md transition-all duration-200"
                >
                  <CardContent className="p-6 space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                      <div className="space-y-1.5">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-bold text-slate-900 text-lg hover:text-indigo-600 transition-colors">
                            <Link href={`/meetings/${meeting.id}`}>
                              {meeting.title}
                            </Link>
                          </h3>
                          <Badge variant="secondary" className="text-[10px] bg-slate-50 font-normal">
                            {meeting.source || 'Upload'}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3.5 w-3.5" />
                            {formatDate(meeting.meeting_date)}
                          </span>
                          {meeting.duration_minutes !== null && (
                            <span className="flex items-center gap-1">
                              <Clock className="h-3.5 w-3.5" />
                              {meeting.duration_minutes}m
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Badge className={`text-xs border ${getScoreBadgeColor(result.similarity_score)}`}>
                          {formatScore(result.similarity_score)}
                        </Badge>
                        
                        {result.matching_summary ? (
                          <Badge variant="outline" className="text-xs bg-indigo-50/20 text-indigo-700 border-indigo-200 flex items-center gap-1 font-medium">
                            <FileText className="h-3 w-3" />
                            Summary Match
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-xs bg-purple-50/20 text-purple-700 border-purple-200 flex items-center gap-1 font-medium">
                            <MessageSquare className="h-3 w-3" />
                            Transcript Match
                          </Badge>
                        )}
                      </div>
                    </div>

                    {/* Result Content Chunk */}
                    {result.matching_summary ? (
                      <div className="p-3.5 rounded-lg border border-indigo-50/50 bg-indigo-50/10">
                        <p className="text-xs font-semibold text-indigo-900 mb-1 flex items-center gap-1">
                          <FileText className="h-3.5 w-3.5" />
                          Meeting Summary
                        </p>
                        <p className="text-sm text-slate-700 leading-relaxed line-clamp-3">
                          {meeting.summary_preview || 'No summary preview available.'}
                        </p>
                      </div>
                    ) : (
                      <div className="p-3.5 rounded-lg border border-purple-50/50 bg-purple-50/10">
                        <p className="text-xs font-semibold text-purple-900 mb-1 flex items-center gap-1">
                          <MessageSquare className="h-3.5 w-3.5" />
                          Relevant Transcript Segment
                        </p>
                        <p className="text-sm text-slate-700 italic leading-relaxed line-clamp-4">
                          &quot;{result.relevant_transcript_chunk}&quot;
                        </p>
                      </div>
                    )}

                    {/* Navigate details footer link */}
                    <div className="flex justify-end pt-1">
                      <Link 
                        href={`/meetings/${meeting.id}`}
                        className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1 hover:translate-x-0.5 transition-all"
                      >
                        Open Meeting Details
                        <ArrowRight className="h-3 w-3" />
                      </Link>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {!activeQuery && (
          <Card className="border-slate-100 py-16 text-center border-dashed">
            <CardContent className="space-y-4">
              <div className="h-12 w-12 rounded-full bg-indigo-50 flex items-center justify-center mx-auto text-indigo-600">
                <Brain className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <h3 className="font-semibold text-slate-800 text-lg">AI Semantic Workspace</h3>
                <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                  Type a query above to locate specific topics, actions, or problems discussed across any transcribed meetings.
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
