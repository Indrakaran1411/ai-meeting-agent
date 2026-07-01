'use client';

import React from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import axios from 'axios';
import { 
  ArrowLeft, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Database, 
  AlertTriangle,
  History,
  Info,
  Loader2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

export default function SyncPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const meetingId = params.id as string;

  // 1. Fetch meeting details
  const { data: meeting, isLoading: isMeetingLoading, isError: isMeetingError } = useQuery({
    queryKey: ['meeting', meetingId],
    queryFn: () => api.getMeeting(meetingId),
  });

  // 2. Fetch sync logs
  const { data: logs = [], isLoading: isLogsLoading } = useQuery({
    queryKey: ['sync-logs', meetingId],
    queryFn: () => api.getMeetingSyncLogs(meetingId),
    enabled: !!meeting,
  });

  // 3. Sync Meeting Mutation
  const syncMutation = useMutation({
    mutationFn: () => api.syncMeeting(meetingId),
    onSuccess: (data) => {
      if (data.skipped) {
        toast.info('Sync skipped: Identical payload was already successfully synchronized (Idempotency Guard).');
      } else if (data.success) {
        toast.success('Meeting insights successfully synchronized to Project Management system!');
      } else {
        toast.error(`Sync completed with errors: ${data.message}`);
      }
      // Refresh sync logs and meeting details
      queryClient.invalidateQueries({ queryKey: ['sync-logs', meetingId] });
      queryClient.invalidateQueries({ queryKey: ['meeting', meetingId] });
    },
    onError: (err: unknown) => {
      console.error(err);
      let detail = 'Webhook server returned error.';
      if (axios.isAxiosError(err)) {
        detail = err.response?.data?.error?.message || err.message || detail;
      } else if (err instanceof Error) {
        detail = err.message;
      }
      toast.error(`Failed to synchronize: ${detail}`);
      queryClient.invalidateQueries({ queryKey: ['sync-logs', meetingId] });
    }
  });

  if (isMeetingLoading || isLogsLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <LoaderComponent />
      </div>
    );
  }

  if (isMeetingError || !meeting) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 bg-card rounded-xl border border-border">
        <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
        <h2 className="text-xl font-semibold mb-2">Meeting Not Found</h2>
        <p className="text-muted-foreground mb-6">Cannot establish sync panel for non-existent meeting.</p>
        <Button onClick={() => router.push('/meetings')} className="bg-indigo-600 hover:bg-indigo-700 text-white">
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to Meetings
        </Button>
      </div>
    );
  }

  // Derive sync statistics from logs list
  const lastAttempt = logs[0] || null; // logs are sorted desc by created_at in backend
  const lastSuccessAttempt = logs.find(l => l.status === 'success') || null;
  const retryCount = logs.filter(l => l.status === 'failed').length;
  
  const payloadHash = lastAttempt?.payload_hash || 'None';
  const status = lastAttempt?.status || 'Never Synced';
  const lastSyncDate = lastSuccessAttempt?.dispatched_at 
    ? new Date(lastSuccessAttempt.dispatched_at).toLocaleString() 
    : lastAttempt?.created_at
      ? new Date(lastAttempt.created_at).toLocaleString()
      : 'Never Synced';

  const getStatusIcon = (statusStr: string) => {
    switch (statusStr) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-emerald-600" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-rose-600" />;
      case 'pending':
        return <RefreshCw className="h-5 w-5 text-indigo-600 animate-spin" />;
      default:
        return <Info className="h-5 w-5 text-slate-400" />;
    }
  };

  const getStatusBadge = (statusStr: string) => {
    switch (statusStr) {
      case 'success':
        return <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">Success</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      case 'pending':
        return <Badge className="bg-indigo-100 text-indigo-800 border-indigo-200">Pending</Badge>;
      default:
        return <Badge variant="outline">{statusStr}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Navigation Header */}
      <div className="flex items-center justify-between">
        <Link href={`/meetings/${meetingId}`} className="text-slate-500 hover:text-slate-900">
          <Button variant="ghost" size="sm" className="gap-1 text-xs">
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Meeting Details
          </Button>
        </Link>
      </div>

      {/* Title */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Synchronization Hub</h1>
        <p className="text-muted-foreground mt-1.5">
          Push approved action items, decisions, and risks for <span className="font-semibold text-slate-900">&quot;{meeting.title}&quot;</span> to external webhooks.
        </p>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Status Card */}
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Sync Status</p>
              <div className="flex items-center gap-1.5 pt-0.5">
                <span className="text-lg font-bold text-slate-900 capitalize">{status}</span>
              </div>
            </div>
            <div className="p-2 bg-slate-50 border border-slate-100 rounded-lg">
              {getStatusIcon(status)}
            </div>
          </CardContent>
        </Card>

        {/* Last Sync Card */}
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Last Sync Attempt</p>
              <p className="text-sm font-bold text-slate-900 pt-0.5 truncate max-w-[140px] md:max-w-none" title={lastSyncDate}>
                {lastSyncDate}
              </p>
            </div>
            <div className="p-2 bg-slate-50 border border-slate-100 rounded-lg">
              <Clock className="h-5 w-5 text-slate-500" />
            </div>
          </CardContent>
        </Card>

        {/* Payload Hash Card */}
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Payload Hash</p>
              <p className="text-xs font-mono text-slate-600 pt-1 select-all truncate max-w-[150px]" title={payloadHash}>
                {payloadHash.slice(0, 12)}
                {payloadHash !== 'None' && '...'}
              </p>
            </div>
            <div className="p-2 bg-slate-50 border border-slate-100 rounded-lg">
              <Database className="h-5 w-5 text-slate-500" />
            </div>
          </CardContent>
        </Card>

        {/* Retry Count Card */}
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Failed Retries</p>
              <p className="text-2xl font-black text-slate-900">
                {retryCount} <span className="text-xs text-slate-400 font-semibold">({logs.length} total attempts)</span>
              </p>
            </div>
            <div className="p-2 bg-slate-50 border border-slate-100 rounded-lg">
              <History className="h-5 w-5 text-slate-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sync trigger card */}
      <Card className="border-indigo-100 bg-gradient-to-r from-indigo-50/20 to-purple-50/20 shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg font-bold text-slate-900">Dispatch Integration Payload</CardTitle>
          <CardDescription>
            This action compiles meeting details along with approved action items, decisions, and risks, and pushes a secure JSON schema payload to your configured PM webhook endpoint.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-5 mx-6 mb-6 rounded-xl border border-slate-150 shadow-sm">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground font-semibold flex items-center gap-1">
              <Info className="h-3.5 w-3.5 text-indigo-500" />
              Idempotency Guard Enabled
            </p>
            <p className="text-sm font-semibold text-slate-800">
              Duplicates (same insight data) will be skipped automatically to prevent redundant Jira/Linear tickets.
            </p>
          </div>
          <Button 
            onClick={() => syncMutation.mutate()} 
            disabled={syncMutation.isPending} 
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold gap-2 py-5 px-6 shadow-md shadow-indigo-200 hover:shadow-indigo-300 hover:-translate-y-0.5 transition-all w-full sm:w-auto"
          >
            {syncMutation.isPending ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" /> Synchronizing...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4" /> Sync Meeting Insights
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Detailed logs history */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg font-bold tracking-tight">Sync Execution Logs</CardTitle>
          <CardDescription>Historical record of every dispatch attempt for this meeting.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-8 text-center min-h-[180px]">
              <History className="h-8 w-8 text-slate-300 mb-2" />
              <p className="font-semibold text-slate-600">No sync runs yet</p>
              <p className="text-xs text-muted-foreground">Trigger your first webhook sync using the button above.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50/50 hover:bg-slate-50/50">
                    <TableHead className="font-semibold text-slate-700">Timestamp</TableHead>
                    <TableHead className="font-semibold text-slate-700">Log ID</TableHead>
                    <TableHead className="font-semibold text-slate-700">Status</TableHead>
                    <TableHead className="font-semibold text-slate-700">HTTP Code</TableHead>
                    <TableHead className="font-semibold text-slate-700">Response Message</TableHead>
                    <TableHead className="font-semibold text-slate-700">Payload Hash</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logs.map((log) => (
                    <TableRow key={log.id} className="hover:bg-slate-50/30">
                      <TableCell className="font-semibold text-slate-900 text-xs">
                        {new Date(log.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell className="font-mono text-[10px] text-muted-foreground select-all">
                        {log.id}
                      </TableCell>
                      <TableCell>{getStatusBadge(log.status)}</TableCell>
                      <TableCell className="font-semibold text-slate-800 text-xs">
                        {log.http_status ? `HTTP ${log.http_status}` : '--'}
                      </TableCell>
                      <TableCell className="text-xs text-slate-600 max-w-[220px] truncate" title={log.response_message || ''}>
                        {log.response_message || 'N/A'}
                      </TableCell>
                      <TableCell className="font-mono text-[10px] text-muted-foreground truncate max-w-[120px]" title={log.payload_hash || ''}>
                        {log.payload_hash || 'N/A'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function LoaderComponent() {
  return (
    <div className="flex flex-col items-center justify-center p-8 space-y-4">
      <Loader2 className="h-8 w-8 text-indigo-600 animate-spin" />
      <p className="text-muted-foreground text-sm font-medium animate-pulse">Loading sync audits...</p>
    </div>
  );
}
