'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { 
  Video, 
  Search, 
  Calendar, 
  Clock, 
  RefreshCw, 
  Trash2, 
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  X,
  Upload,
  AlertTriangle
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';

const LIMIT = 10;

export default function MeetingsPage() {
  const queryClient = useQueryClient();
  
  // Search & Filtering State
  const [q, setQ] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sourceFilter, setSourceFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [deletingMeetingId, setDeletingMeetingId] = useState<string | null>(null);

  // Derive offset
  const offset = (currentPage - 1) * LIMIT;

  // React Query params
  const queryParams = {
    limit: LIMIT,
    offset,
    ...(q.trim() !== '' && { q: q.trim() }),
    ...(statusFilter !== 'all' && { status: statusFilter }),
    ...(sourceFilter !== 'all' && { source: sourceFilter }),
  };

  // Fetch paginated meetings
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['meetings', queryParams],
    queryFn: () => api.getMeetings(queryParams),
    placeholderData: (previousData) => previousData, // keep previous data while fetching new pages
  });

  // Delete Meeting Mutation
  const deleteMutation = useMutation({
    mutationFn: api.deleteMeeting,
    onSuccess: () => {
      toast.success('Meeting deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      setDeletingMeetingId(null);
    },
    onError: (err: unknown) => {
      console.error(err);
      toast.error('Failed to delete meeting');
      setDeletingMeetingId(null);
    }
  });

  const handleDeleteConfirm = () => {
    if (deletingMeetingId) {
      deleteMutation.mutate(deletingMeetingId);
    }
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQ(e.target.value);
    setCurrentPage(1); // reset to first page on search
  };

  const handleStatusChange = (value: string | null) => {
    setStatusFilter(value || 'all');
    setCurrentPage(1); // reset on filter
  };

  const handleSourceChange = (value: string | null) => {
    setSourceFilter(value || 'all');
    setCurrentPage(1); // reset on filter
  };

  const clearFilters = () => {
    setQ('');
    setStatusFilter('all');
    setSourceFilter('all');
    setCurrentPage(1);
  };

  const totalCount = data?.total_count || 0;
  const meetings = data?.items || [];
  const totalPages = Math.ceil(totalCount / LIMIT);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100/80 border-emerald-200">Completed</Badge>;
      case 'processing':
        return <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100/80 border-amber-200 animate-pulse">Processing</Badge>;
      case 'pending':
        return <Badge className="bg-indigo-100 text-indigo-800 hover:bg-indigo-100/80 border-indigo-200">Pending</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 md:text-4xl">
            Meetings
          </h1>
          <p className="text-muted-foreground mt-1.5">
            Manage your meeting library, trigger webhook syncs, and review insights.
          </p>
        </div>
        <Link href="/upload">
          <Button className="bg-indigo-600 hover:bg-indigo-700 text-white gap-2 font-medium shadow-sm">
            <Upload className="h-4 w-4" /> Upload Meeting
          </Button>
        </Link>
      </div>

      {/* Filters Card */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-4 flex flex-col md:flex-row gap-4 items-end">
          {/* Keyword Search */}
          <div className="flex-1 space-y-1.5 w-full">
            <label className="text-xs font-semibold text-slate-600">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search meeting titles or summaries..."
                value={q}
                onChange={handleSearchChange}
                className="pl-9 bg-slate-50/50 focus:bg-white"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div className="w-full md:w-48 space-y-1.5">
            <label className="text-xs font-semibold text-slate-600">Status</label>
            <Select value={statusFilter} onValueChange={handleStatusChange}>
              <SelectTrigger>
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="processing">Processing</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Source Filter */}
          <div className="w-full md:w-48 space-y-1.5">
            <label className="text-xs font-semibold text-slate-600">Source Platform</label>
            <Select value={sourceFilter} onValueChange={handleSourceChange}>
              <SelectTrigger>
                <SelectValue placeholder="All platforms" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sources</SelectItem>
                <SelectItem value="Upload">Manual Upload</SelectItem>
                <SelectItem value="Zoom">Zoom</SelectItem>
                <SelectItem value="Teams">Microsoft Teams</SelectItem>
                <SelectItem value="Google Meet">Google Meet</SelectItem>
                <SelectItem value="Slack">Slack Call</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Clear Filters Button */}
          {(q || statusFilter !== 'all' || sourceFilter !== 'all') && (
            <Button variant="ghost" onClick={clearFilters} className="gap-1 text-slate-600 w-full md:w-auto">
              <X className="h-4 w-4" /> Clear
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Main Table Card */}
      <Card className="border-slate-200 shadow-sm overflow-hidden">
        <CardContent className="p-0">
          {isError ? (
            <div className="flex flex-col items-center justify-center p-8 text-center min-h-[300px]">
              <AlertTriangle className="h-10 w-10 text-destructive mb-3" />
              <p className="font-semibold text-slate-700">Failed to load meetings</p>
              <p className="text-sm text-muted-foreground mb-4">Check backend container status.</p>
              <Button onClick={() => refetch()} variant="outline" size="sm">Retry</Button>
            </div>
          ) : isLoading ? (
            <div className="p-6 space-y-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-12 bg-slate-100 rounded animate-pulse"></div>
              ))}
            </div>
          ) : meetings.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-center min-h-[300px]">
              <Video className="h-12 w-12 text-slate-300 mb-3" />
              <h3 className="text-lg font-bold text-slate-800">No meetings found</h3>
              <p className="text-sm text-muted-foreground max-w-sm mt-1 mb-6">
                Try refining your filters or upload a new meeting recording.
              </p>
              <Link href="/upload">
                <Button className="bg-indigo-600 hover:bg-indigo-700 text-white gap-2 font-medium">
                  <Upload className="h-4 w-4" /> Upload Now
                </Button>
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50/50 hover:bg-slate-50/50">
                    <TableHead className="font-semibold text-slate-700">Title</TableHead>
                    <TableHead className="font-semibold text-slate-700">Status</TableHead>
                    <TableHead className="font-semibold text-slate-700">Source</TableHead>
                    <TableHead className="font-semibold text-slate-700">Date & Time</TableHead>
                    <TableHead className="font-semibold text-slate-700">Duration</TableHead>
                    <TableHead className="text-right font-semibold text-slate-700">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {meetings.map((meeting) => (
                    <TableRow key={meeting.id} className="hover:bg-slate-50/30">
                      <TableCell className="py-4">
                        <div className="font-semibold text-slate-900 max-w-[240px] truncate" title={meeting.title}>
                          {meeting.title}
                        </div>
                        {meeting.summary_preview && (
                          <div className="text-xs text-muted-foreground max-w-[320px] truncate mt-0.5">
                            {meeting.summary_preview}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>{getStatusBadge(meeting.status)}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="bg-white border-slate-200 text-slate-700 font-medium">
                          {meeting.source || 'Upload'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        <span className="flex items-center gap-1.5">
                          <Calendar className="h-3.5 w-3.5 text-slate-400" />
                          {formatDate(meeting.meeting_date)}
                        </span>
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {meeting.duration_minutes ? (
                          <span className="flex items-center gap-1.5">
                            <Clock className="h-3.5 w-3.5 text-slate-400" />
                            {meeting.duration_minutes}m
                          </span>
                        ) : (
                          '--'
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1.5">
                          <Link href={`/meetings/${meeting.id}`}>
                            <Button size="icon" variant="ghost" className="h-8 w-8 hover:bg-slate-100 text-slate-700" title="View details">
                              <ExternalLink className="h-3.5 w-3.5" />
                            </Button>
                          </Link>
                          <Link href={`/meetings/${meeting.id}/sync`}>
                            <Button size="icon" variant="ghost" className="h-8 w-8 hover:bg-slate-100 text-indigo-600" title="Sync integrations">
                              <RefreshCw className="h-3.5 w-3.5" />
                            </Button>
                          </Link>
                          <Button 
                            size="icon" 
                            variant="ghost" 
                            className="h-8 w-8 hover:bg-rose-50 text-rose-600" 
                            title="Delete meeting"
                            onClick={() => setDeletingMeetingId(meeting.id)}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination Footer */}
      {!isLoading && !isError && totalPages > 1 && (
        <div className="flex items-center justify-between py-2">
          <p className="text-sm text-muted-foreground font-medium">
            Showing <span className="font-semibold text-slate-900">{offset + 1}</span> to{' '}
            <span className="font-semibold text-slate-900">
              {Math.min(offset + LIMIT, totalCount)}
            </span>{' '}
            of <span className="font-semibold text-slate-900">{totalCount}</span> meetings
          </p>
          <div className="flex items-center gap-1.5">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="h-9 gap-1 font-semibold"
            >
              <ChevronLeft className="h-4 w-4" /> Previous
            </Button>
            <span className="text-sm font-semibold text-slate-700 px-3">
              Page {currentPage} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="h-9 gap-1 font-semibold"
            >
              Next <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Delete Meeting Confirmation Dialog */}
      <Dialog open={deletingMeetingId !== null} onOpenChange={(open) => !open && setDeletingMeetingId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Meeting</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this meeting? This will permanently delete the meeting metadata, transcripts, action items, decisions, risks, and sync logs from the database. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setDeletingMeetingId(null)} disabled={deleteMutation.isPending}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteConfirm} disabled={deleteMutation.isPending}>
              {deleteMutation.isPending ? 'Deleting...' : 'Delete Permanently'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
