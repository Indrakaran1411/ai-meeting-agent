'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { 
  FileText, 
  CheckCircle2, 
  Activity, 
  CheckSquare, 
  FileCheck, 
  AlertTriangle, 
  ArrowRight,
  Upload,
  Calendar,
  Clock,
  ExternalLink,
  RefreshCw,
  Trash2,
  ListTodo
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const [deletingMeetingId, setDeletingMeetingId] = useState<string | null>(null);

  // Fetch consolidated dashboard data
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['dashboard'],
    queryFn: api.getDashboard,
    refetchInterval: 15000, // Auto-refresh every 15s to capture processing updates
  });

  // Delete Meeting Mutation
  const deleteMutation = useMutation({
    mutationFn: api.deleteMeeting,
    onSuccess: () => {
      toast.success('Meeting deleted successfully');
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

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 bg-card rounded-xl border border-border">
        <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
        <h2 className="text-xl font-semibold mb-2">Failed to load dashboard</h2>
        <p className="text-muted-foreground mb-6 max-w-md">
          {error instanceof Error ? error.message : 'An error occurred while fetching dashboard statistics.'}
        </p>
        <Button onClick={() => refetch()} variant="outline" className="gap-2">
          <RefreshCw className="h-4 w-4" /> Retry
        </Button>
      </div>
    );
  }

  const stats = data?.statistics;
  const recentMeetings = data?.recent_meetings || [];
  const recentActionItems = data?.recent_action_items || [];

  const kpis = [
    {
      title: 'Total Meetings',
      value: stats?.total_meetings ?? 0,
      icon: FileText,
      color: 'text-indigo-600',
      bg: 'bg-indigo-50',
      border: 'border-indigo-100',
    },
    {
      title: 'Completed Meetings',
      value: stats?.completed_meetings ?? 0,
      icon: CheckCircle2,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
      border: 'border-emerald-100',
    },
    {
      title: 'Processing Meetings',
      value: stats?.processing_meetings ?? 0,
      icon: Activity,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
      border: 'border-amber-100',
      pulse: (stats?.processing_meetings ?? 0) > 0,
    },
    {
      title: 'Action Items',
      value: stats?.total_action_items ?? 0,
      icon: CheckSquare,
      color: 'text-sky-600',
      bg: 'bg-sky-50',
      border: 'border-sky-100',
    },
    {
      title: 'Decisions Reached',
      value: stats?.total_decisions ?? 0,
      icon: FileCheck,
      color: 'text-purple-600',
      bg: 'bg-purple-50',
      border: 'border-purple-100',
    },
    {
      title: 'Risks & Blockers',
      value: stats?.total_risks ?? 0,
      icon: AlertTriangle,
      color: 'text-rose-600',
      bg: 'bg-rose-50',
      border: 'border-rose-100',
    },
  ];

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
    });
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 md:text-4xl">
            Dashboard
          </h1>
          <p className="text-muted-foreground mt-1.5">
            Real-time meeting intelligence and action items.
          </p>
        </div>
        <Link href="/upload">
          <Button className="bg-indigo-600 hover:bg-indigo-700 text-white gap-2 font-medium shadow-sm hover:shadow transition-all">
            <Upload className="h-4 w-4" /> Upload Meeting
          </Button>
        </Link>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => (
              <Card key={i} className="animate-pulse border-slate-200">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <div className="h-4 w-24 bg-slate-200 rounded"></div>
                  <div className="h-8 w-8 bg-slate-200 rounded-full"></div>
                </CardHeader>
                <CardContent>
                  <div className="h-8 w-16 bg-slate-200 rounded mb-1"></div>
                  <div className="h-3 w-32 bg-slate-100 rounded"></div>
                </CardContent>
              </Card>
            ))
          : kpis.map((kpi) => {
              const Icon = kpi.icon;
              return (
                <Card 
                  key={kpi.title} 
                  className={`border ${kpi.border} transition-all duration-300 hover:shadow-md hover:-translate-y-0.5 group`}
                >
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-semibold text-muted-foreground tracking-tight group-hover:text-slate-900 transition-colors">
                      {kpi.title}
                    </CardTitle>
                    <div className={`p-2 rounded-lg ${kpi.bg} ${kpi.color} transition-all`}>
                      <Icon className={`h-4 w-4 ${kpi.pulse ? 'animate-bounce' : ''}`} />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-extrabold tracking-tight text-slate-950">
                      {kpi.value}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      System aggregated count
                    </p>
                  </CardContent>
                </Card>
              );
            })}
      </div>

      {/* Main Sections */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Recent Meetings Table */}
        <Card className="lg:col-span-2 border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-lg font-bold tracking-tight">Recent Meetings</CardTitle>
              <CardDescription>Latest uploads in the ingestion pipeline.</CardDescription>
            </div>
            <Link href="/meetings" className="text-sm font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1">
              View all <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="p-6 space-y-4">
                <div className="h-10 bg-slate-100 rounded animate-pulse"></div>
                <div className="h-10 bg-slate-100 rounded animate-pulse"></div>
                <div className="h-10 bg-slate-100 rounded animate-pulse"></div>
              </div>
            ) : recentMeetings.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-8 text-center min-h-[220px]">
                <Clock className="h-10 w-10 text-slate-300 mb-3" />
                <p className="font-semibold text-slate-700">No meetings yet</p>
                <p className="text-sm text-muted-foreground mb-4">Get started by uploading your first meeting audio.</p>
                <Link href="/upload">
                  <Button variant="outline" size="sm" className="gap-2">
                    <Upload className="h-3.5 w-3.5" /> Upload Now
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
                      <TableHead className="font-semibold text-slate-700">Date</TableHead>
                      <TableHead className="font-semibold text-slate-700">Duration</TableHead>
                      <TableHead className="text-right font-semibold text-slate-700">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {recentMeetings.map((meeting) => (
                      <TableRow key={meeting.id} className="hover:bg-slate-50/30">
                        <TableCell className="font-semibold text-slate-900 max-w-[200px] truncate">
                          {meeting.title}
                        </TableCell>
                        <TableCell>{getStatusBadge(meeting.status)}</TableCell>
                        <TableCell className="text-muted-foreground text-sm flex items-center gap-1.5 py-4">
                          <Calendar className="h-3.5 w-3.5 text-slate-400" />
                          {formatDate(meeting.meeting_date)}
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

        {/* Action Items List */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg font-bold tracking-tight">Recent Tasks</CardTitle>
            <CardDescription>Extracted action items pending review.</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-4">
                <div className="h-12 bg-slate-100 rounded animate-pulse"></div>
                <div className="h-12 bg-slate-100 rounded animate-pulse"></div>
                <div className="h-12 bg-slate-100 rounded animate-pulse"></div>
              </div>
            ) : recentActionItems.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-6 text-center min-h-[220px]">
                <ListTodo className="h-10 w-10 text-slate-300 mb-3" />
                <p className="font-semibold text-slate-700">No pending action items</p>
                <p className="text-xs text-muted-foreground max-w-[180px] mx-auto">Tasks will appear once meeting audio finishes processing.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {recentActionItems.map((item) => (
                  <div 
                    key={item.id} 
                    className="flex flex-col gap-1.5 p-3 rounded-lg border border-slate-100 bg-slate-50/50 hover:bg-slate-50 transition-colors"
                  >
                    <p className="text-sm font-semibold text-slate-900 line-clamp-2">
                      {item.description}
                    </p>
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span className="font-medium text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                        {item.assignee || 'Unassigned'}
                      </span>
                      {item.due_date && (
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(item.due_date)}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

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
