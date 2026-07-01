'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { 
  Search as SearchIcon, 
  Brain, 
  Calendar, 
  Sparkles, 
  ArrowRight,
  MessageSquare,
  FileText,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  User,
  Sliders
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

const LIMIT = 10;

export default function SemanticSearchPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeQuery, setActiveQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [minSimilarity, setMinSimilarity] = useState(0.0);

  // Derive offset
  const offset = (currentPage - 1) * LIMIT;

  // Run semantic search query using React Query
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['semantic-search', activeQuery, LIMIT, offset, minSimilarity],
    queryFn: () => api.semanticSearch(activeQuery, LIMIT, offset, minSimilarity),
    enabled: activeQuery.trim() !== '',
    retry: false,
  });

  // Reset page when search term or minimum similarity changes
  useEffect(() => {
    setCurrentPage(1);
  }, [activeQuery, minSimilarity]);

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

  // Helper to format float seconds to MM:SS
  const formatTime = (secs: number | null) => {
    if (secs === null || secs === undefined) return '';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  // Highlights keywords in text matching the active search query
  const highlightText = (text: string, query: string) => {
    if (!text) return '';
    if (!query || !query.trim()) return <span>{text}</span>;
    
    const terms = query.split(/\s+/).filter(Boolean);
    if (terms.length === 0) return <span>{text}</span>;
    
    // Create regex matching any of the query terms
    const escapedTerms = terms.map(t => t.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'));
    const regex = new RegExp(`(${escapedTerms.join('|')})`, 'gi');
    const parts = text.split(regex);
    
    return (
      <span>
        {parts.map((part, i) => {
          const isMatch = terms.some(term => term.toLowerCase() === part.toLowerCase());
          return isMatch ? (
            <mark key={i} className="bg-yellow-200 text-yellow-900 rounded px-0.5 font-medium select-all">
              {part}
            </mark>
          ) : (
            part
          );
        })}
      </span>
    );
  };

  // Determine if next page button should be enabled
  const hasMore = data ? data.results.length === LIMIT : false;

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

      {/* Search Input & Similarity Settings Card */}
      <Card className="border-slate-100 shadow-sm bg-gradient-to-br from-indigo-50/30 to-purple-50/10">
        <CardContent className="p-6 space-y-4">
          <form onSubmit={handleSearchSubmit} className="flex gap-3">
            <div className="relative flex-1">
              <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                type="text"
                placeholder="e.g., authentication service blocker, database schema migrations, roadmap dates..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 h-12 bg-white border-slate-200/80 focus-visible:ring-indigo-500 text-slate-900"
              />
            </div>
            <Button 
              type="submit" 
              className="h-12 px-6 bg-indigo-600 hover:bg-indigo-700 transition-colors font-medium gap-2 text-white"
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

          {/* Similarity Threshold Slider */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 border-t border-slate-100/80 text-xs">
            <div className="flex items-center gap-2 text-slate-600">
              <Sliders className="h-3.5 w-3.5 text-slate-400" />
              <span className="font-medium">Minimum Similarity Threshold:</span>
              <span className="font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                {Math.round(minSimilarity * 100)}% Match
              </span>
            </div>
            <div className="flex items-center gap-3 w-full sm:w-64">
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={minSimilarity}
                onChange={(e) => setMinSimilarity(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
              />
              <span className="text-slate-400 font-mono w-6 text-right">
                {minSimilarity.toFixed(2)}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Search results listing */}
      <div className="space-y-4">
        {activeQuery && (
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              Showing page {currentPage} results for &quot;<strong className="text-slate-900">{activeQuery}</strong>&quot;
            </span>
            {data && <span>Found {data.results.length} matches this page</span>}
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
                No matching summaries or transcript segments were found for your query with the current filters. Try lowering the similarity threshold or adjust your query.
              </p>
            </CardContent>
          </Card>
        )}

        {data && data.results.length > 0 && (
          <div className="space-y-4">
            {data.results.map((result, idx) => {
              const hasTimestamps = result.start_time !== null && result.end_time !== null;
              
              return (
                <Card 
                  key={`${result.meeting_id}-${idx}`} 
                  className="border-slate-100 hover:border-indigo-100 shadow-sm hover:shadow-md transition-all duration-200"
                >
                  <CardContent className="p-6 space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                      <div className="space-y-1.5">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-bold text-slate-900 text-lg hover:text-indigo-600 transition-colors">
                            <Link href={`/meetings/${result.meeting_id}`}>
                              {result.meeting_title}
                            </Link>
                          </h3>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3.5 w-3.5" />
                            {formatDate(result.meeting_date)}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Badge className={`text-xs border ${getScoreBadgeColor(result.similarity_score)}`}>
                          {formatScore(result.similarity_score)}
                        </Badge>
                        
                        {result.result_type === 'summary' ? (
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
                    {result.result_type === 'summary' ? (
                      <div className="p-3.5 rounded-lg border border-indigo-50/50 bg-indigo-50/10">
                        <p className="text-xs font-semibold text-indigo-900 mb-1 flex items-center gap-1">
                          <FileText className="h-3.5 w-3.5" />
                          Meeting Summary Match
                        </p>
                        <p className="text-sm text-slate-700 leading-relaxed line-clamp-3">
                          {highlightText(result.matched_text, activeQuery)}
                        </p>
                      </div>
                    ) : (
                      <div className="p-3.5 rounded-lg border border-purple-50/50 bg-purple-50/10 space-y-2">
                        <div className="flex items-center justify-between text-xs font-semibold text-purple-900">
                          <div className="flex items-center gap-1">
                            <MessageSquare className="h-3.5 w-3.5" />
                            Relevant Transcript Segment
                          </div>
                          <div className="flex items-center gap-3 text-slate-500 font-normal">
                            {result.speaker && (
                              <span className="flex items-center gap-1">
                                <User className="h-3 w-3 text-purple-400" />
                                Speaker: <strong className="text-slate-700">{result.speaker}</strong>
                              </span>
                            )}
                            {hasTimestamps && (
                              <span className="bg-slate-100 px-1.5 py-0.5 rounded font-mono text-[10px]">
                                {formatTime(result.start_time)} - {formatTime(result.end_time)}
                              </span>
                            )}
                          </div>
                        </div>
                        <p className="text-sm text-slate-700 italic leading-relaxed line-clamp-4">
                          &quot;{highlightText(result.matched_text, activeQuery)}&quot;
                        </p>
                      </div>
                    )}

                    {/* Summary preview preview if it was a transcript match */}
                    {result.result_type === 'transcript' && result.summary_preview && (
                      <p className="text-xs text-muted-foreground line-clamp-1 border-t border-slate-50 pt-2">
                        <strong>Summary:</strong> {result.summary_preview}
                      </p>
                    )}

                    {/* Navigate details footer link */}
                    <div className="flex justify-end pt-1">
                      <Link 
                        href={`/meetings/${result.meeting_id}`}
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

            {/* Pagination Controls */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-100">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1 || isLoading}
                className="gap-1"
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              <span className="text-sm text-slate-600">
                Page <strong className="text-slate-900">{currentPage}</strong>
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => prev + 1)}
                disabled={!hasMore || isLoading}
                className="gap-1"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
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
