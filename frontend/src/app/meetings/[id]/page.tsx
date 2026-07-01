'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  api, 
  ActionItemResponse, 
  DecisionResponse, 
  RiskResponse 
} from '@/lib/api-client';
import { 
  Calendar, 
  Clock, 
  RefreshCw, 
  Trash2, 
  AlertTriangle, 
  Loader2, 
  ArrowLeft,
  Search,
  Check,
  Edit2,
  X,
  FileText,
  MessageSquare,
  ListTodo,
  FileCheck,
  ShieldAlert,
  Terminal,
  Activity,
  User
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

export default function MeetingDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const meetingId = params.id as string;

  // Active Tab
  const [activeTab, setActiveTab] = useState('summary');

  // Search keyword inside transcripts tab
  const [transcriptSearch, setTranscriptSearch] = useState('');

  // Editing state
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [editFields, setEditFields] = useState<Record<string, unknown>>({});

  // Query Meeting detail (Polls if pending/processing)
  const { data: meeting, isLoading: isMeetingLoading, isError: isMeetingError, error: meetingError } = useQuery({
    queryKey: ['meeting', meetingId],
    queryFn: () => api.getMeeting(meetingId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return (status === 'pending' || status === 'processing') ? 5000 : false;
    }
  });

  // Queries for individual tabs
  const { data: actionItems, isLoading: isActionItemsLoading } = useQuery({
    queryKey: ['action-items', meetingId],
    queryFn: () => api.getMeetingActionItems(meetingId),
    enabled: !!meeting && meeting.status === 'completed' && activeTab === 'action-items'
  });

  const { data: decisions, isLoading: isDecisionsLoading } = useQuery({
    queryKey: ['decisions', meetingId],
    queryFn: () => api.getMeetingDecisions(meetingId),
    enabled: !!meeting && meeting.status === 'completed' && activeTab === 'decisions'
  });

  const { data: risks, isLoading: isRisksLoading } = useQuery({
    queryKey: ['risks', meetingId],
    queryFn: () => api.getMeetingRisks(meetingId),
    enabled: !!meeting && meeting.status === 'completed' && activeTab === 'risks'
  });

  const { data: transcripts, isLoading: isTranscriptsLoading } = useQuery({
    queryKey: ['transcript', meetingId],
    queryFn: () => api.getMeetingTranscript(meetingId),
    enabled: !!meeting && meeting.status === 'completed' && activeTab === 'transcript'
  });

  const { data: syncLogs, isLoading: isSyncLogsLoading } = useQuery({
    queryKey: ['sync-logs', meetingId],
    queryFn: () => api.getMeetingSyncLogs(meetingId),
    enabled: !!meeting && meeting.status === 'completed' && activeTab === 'sync-logs'
  });

  const { data: chatSignals, isLoading: isChatSignalsLoading } = useQuery({
    queryKey: ['chat-signals'],
    queryFn: () => api.getChatSignals(),
    enabled: !!meeting && meeting.status === 'completed' && activeTab === 'chat-signals'
  });

  // Action Item mutations
  const patchActionItemMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<ActionItemResponse> }) => 
      api.patchActionItem(id, payload),
    onSuccess: () => {
      toast.success('Action item updated');
      queryClient.invalidateQueries({ queryKey: ['action-items', meetingId] });
      setEditingItemId(null);
    },
    onError: () => toast.error('Failed to update action item')
  });

  const deleteActionItemMutation = useMutation({
    mutationFn: api.deleteActionItem,
    onSuccess: () => {
      toast.success('Action item deleted');
      queryClient.invalidateQueries({ queryKey: ['action-items', meetingId] });
    },
    onError: () => toast.error('Failed to delete action item')
  });

  // Decision mutations
  const patchDecisionMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<DecisionResponse> }) => 
      api.patchDecision(id, payload),
    onSuccess: () => {
      toast.success('Decision updated');
      queryClient.invalidateQueries({ queryKey: ['decisions', meetingId] });
      setEditingItemId(null);
    },
    onError: () => toast.error('Failed to update decision')
  });

  const deleteDecisionMutation = useMutation({
    mutationFn: api.deleteDecision,
    onSuccess: () => {
      toast.success('Decision deleted');
      queryClient.invalidateQueries({ queryKey: ['decisions', meetingId] });
    },
    onError: () => toast.error('Failed to delete decision')
  });

  // Risk mutations
  const patchRiskMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<RiskResponse> }) => 
      api.patchRisk(id, payload),
    onSuccess: () => {
      toast.success('Risk updated');
      queryClient.invalidateQueries({ queryKey: ['risks', meetingId] });
      setEditingItemId(null);
    },
    onError: () => toast.error('Failed to update risk')
  });

  const deleteRiskMutation = useMutation({
    mutationFn: api.deleteRisk,
    onSuccess: () => {
      toast.success('Risk deleted');
      queryClient.invalidateQueries({ queryKey: ['risks', meetingId] });
    },
    onError: () => toast.error('Failed to delete risk')
  });

  // Inline editing actions
  const startEditing = (item: ActionItemResponse | DecisionResponse | RiskResponse) => {
    setEditingItemId(item.id);
    setEditFields({ ...item } as unknown as Record<string, unknown>);
  };

  const handleEditChange = (field: string, value: unknown) => {
    setEditFields((prev: Record<string, unknown>) => ({ ...prev, [field]: value }));
  };

  const saveActionItemEdit = (id: string) => {
    patchActionItemMutation.mutate({
      id,
      payload: {
        description: editFields.description as string,
        assignee: editFields.assignee as string | null,
        due_date: (editFields.due_date as string) || null,
        status: editFields.status as 'draft' | 'approved' | 'synced',
      }
    });
  };

  const saveDecisionEdit = (id: string) => {
    patchDecisionMutation.mutate({
      id,
      payload: {
        description: editFields.description as string,
        rationale: editFields.rationale as string | null,
        status: editFields.status as 'draft' | 'approved' | 'synced',
      }
    });
  };

  const saveRiskEdit = (id: string) => {
    patchRiskMutation.mutate({
      id,
      payload: {
        description: editFields.description as string,
        severity: editFields.severity as 'low' | 'medium' | 'high' | 'critical',
        mitigation: editFields.mitigation as string | null,
        status: editFields.status as 'draft' | 'approved' | 'synced',
      }
    });
  };

  // Helper formats
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatTimestamp = (sec: number) => {
    const minutes = Math.floor(sec / 60);
    const seconds = Math.floor(sec % 60);
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100 border-emerald-200">Completed</Badge>;
      case 'processing':
        return <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100 border-amber-200 animate-pulse">Processing</Badge>;
      case 'pending':
        return <Badge className="bg-indigo-100 text-indigo-800 hover:bg-indigo-100 border-indigo-200">Pending</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getInsightStatusBadge = (status: string) => {
    switch (status) {
      case 'synced':
        return <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">Synced</Badge>;
      case 'approved':
        return <Badge className="bg-sky-100 text-sky-800 border-sky-200">Approved</Badge>;
      case 'draft':
        return <Badge className="bg-slate-100 text-slate-800 border-slate-200">Draft</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (isMeetingLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="h-10 w-10 text-indigo-600 animate-spin" />
        <p className="text-muted-foreground font-medium animate-pulse">Retrieving meeting data...</p>
      </div>
    );
  }

  if (isMeetingError || !meeting) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 bg-card rounded-xl border border-border">
        <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
        <h2 className="text-xl font-semibold mb-2">Meeting Not Found</h2>
        <p className="text-muted-foreground mb-6 max-w-md">
          {meetingError instanceof Error ? meetingError.message : 'The requested meeting ID does not exist or has been deleted.'}
        </p>
        <Button onClick={() => router.push('/meetings')} className="bg-indigo-600 hover:bg-indigo-700 text-white">
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to Meetings
        </Button>
      </div>
    );
  }

  // If meeting is not completed, display processing screen
  if (meeting.status === 'pending' || meeting.status === 'processing') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center max-w-lg mx-auto p-6 bg-card rounded-xl border border-border space-y-6">
        <div className="relative flex items-center justify-center">
          <Loader2 className="h-16 w-14 text-indigo-600 animate-spin" />
          <Activity className="h-6 w-6 text-indigo-600 absolute animate-pulse" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Meeting Processing</h2>
          <p className="text-muted-foreground text-sm">
            Celery workers are currently transcribing the audio file and extracting structured insights. This tab will unlock automatically once completed.
          </p>
        </div>
        <div className="w-full space-y-3.5 text-left border border-slate-100 rounded-xl p-4 bg-slate-50 text-sm">
          <div className="flex items-center gap-3">
            <div className="h-5 w-5 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-bold">✓</div>
            <span className="font-semibold text-slate-800">Audio Ingestion Complete</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="h-5 w-5 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold">
              {meeting.status === 'pending' ? <span className="animate-pulse">●</span> : '✓'}
            </div>
            <span className={`font-semibold ${meeting.status === 'pending' ? 'text-indigo-600' : 'text-slate-800'}`}>
              Speech-to-Text Transcription: {meeting.status === 'pending' ? 'Active...' : 'Completed'}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="h-5 w-5 rounded-full bg-indigo-50 text-indigo-400 flex items-center justify-center text-xs font-bold">
              {meeting.status === 'processing' ? <span className="animate-pulse">●</span> : '3'}
            </div>
            <span className={`font-semibold ${meeting.status === 'processing' ? 'text-indigo-600 animate-pulse' : 'text-slate-400'}`}>
              Gemini LLM Insight Extraction: {meeting.status === 'processing' ? 'Active...' : 'Pending'}
            </span>
          </div>
        </div>
        <Button onClick={() => router.push('/meetings')} variant="outline" className="w-full">
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to Meetings List
        </Button>
      </div>
    );
  }

  // Handle display of failed state
  if (meeting.status === 'failed') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center max-w-lg mx-auto p-6 bg-card rounded-xl border border-border space-y-6">
        <AlertTriangle className="h-14 w-14 text-destructive" />
        <div className="space-y-2">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Ingestion Failure</h2>
          <p className="text-muted-foreground text-sm">
            An error occurred in the Celery speech-to-text or Gemini LLM parsing pipeline. Check logs for details.
          </p>
        </div>
        <Button onClick={() => router.push('/meetings')} className="bg-indigo-600 hover:bg-indigo-700 text-white w-full">
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to Meetings List
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb and action header */}
      <div className="flex items-center gap-3">
        <Link href="/meetings" className="text-slate-500 hover:text-slate-900">
          <Button variant="ghost" size="sm" className="gap-1 text-xs">
            <ArrowLeft className="h-3 w-3" /> Meetings
          </Button>
        </Link>
      </div>

      {/* Main Info Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-card border border-border rounded-xl p-5 shadow-sm">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-slate-900">{meeting.title}</h1>
            {getStatusBadge(meeting.status)}
          </div>
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-muted-foreground font-semibold">
            <span className="flex items-center gap-1.5">
              <Calendar className="h-4 w-4 text-slate-400" />
              {formatDate(meeting.meeting_date)}
            </span>
            {meeting.duration_minutes && (
              <span className="flex items-center gap-1.5">
                <Clock className="h-4 w-4 text-slate-400" />
                {meeting.duration_minutes} Minutes
              </span>
            )}
            <span className="bg-slate-100 text-slate-700 px-2.5 py-0.5 rounded text-xs font-bold">
              {meeting.source || 'Upload'}
            </span>
          </div>
        </div>
        <Link href={`/meetings/${meetingId}/sync`}>
          <Button className="bg-indigo-600 hover:bg-indigo-700 text-white gap-2 font-medium shadow-sm">
            <RefreshCw className="h-4 w-4 animate-spin-slow" /> Synchronization Hub
          </Button>
        </Link>
      </div>

      {/* Tab Interface */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid grid-cols-4 lg:grid-cols-7 h-auto p-1.5 bg-card border border-border rounded-xl">
          <TabsTrigger value="summary" className="py-2.5 text-xs md:text-sm font-semibold gap-2 rounded-lg">
            <FileText className="h-4 w-4 hidden md:block" /> Summary
          </TabsTrigger>
          <TabsTrigger value="transcript" className="py-2.5 text-xs md:text-sm font-semibold gap-2 rounded-lg">
            <MessageSquare className="h-4 w-4 hidden md:block" /> Transcript
          </TabsTrigger>
          <TabsTrigger value="action-items" className="py-2.5 text-xs md:text-sm font-semibold gap-2 rounded-lg">
            <ListTodo className="h-4 w-4 hidden md:block" /> Action Items
          </TabsTrigger>
          <TabsTrigger value="decisions" className="py-2.5 text-xs md:text-sm font-semibold gap-2 rounded-lg">
            <FileCheck className="h-4 w-4 hidden md:block" /> Decisions
          </TabsTrigger>
          <TabsTrigger value="risks" className="py-2.5 text-xs md:text-sm font-semibold gap-2 rounded-lg">
            <ShieldAlert className="h-4 w-4 hidden md:block" /> Risks
          </TabsTrigger>
          <TabsTrigger value="chat-signals" className="py-2.5 text-xs md:text-sm font-semibold gap-2 rounded-lg">
            <Terminal className="h-4 w-4 hidden md:block" /> Chat Signals
          </TabsTrigger>
          <TabsTrigger value="sync-logs" className="py-2.5 text-xs md:text-sm font-semibold gap-2 rounded-lg">
            <RefreshCw className="h-4 w-4 hidden md:block" /> Sync Logs
          </TabsTrigger>
        </TabsList>

        {/* -------------------- 1. Summary Tab -------------------- */}
        <TabsContent value="summary" className="space-y-6 focus:outline-none">
          <Card className="border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg font-bold tracking-tight">Executive Summary</CardTitle>
              <CardDescription>AI-generated overview of the meeting core discussion.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="p-5 bg-slate-50/50 rounded-xl border border-slate-100 text-slate-800 leading-relaxed font-medium">
                {meeting.summary || 'No summary was generated.'}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* -------------------- 2. Transcript Tab -------------------- */}
        <TabsContent value="transcript" className="space-y-6 focus:outline-none">
          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div>
                <CardTitle className="text-lg font-bold tracking-tight">Speech Transcript</CardTitle>
                <CardDescription>Order-index segments with diarized speakers.</CardDescription>
              </div>
              <div className="relative w-full sm:w-72">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Filter transcript keywords..."
                  value={transcriptSearch}
                  onChange={(e) => setTranscriptSearch(e.target.value)}
                  className="pl-9 bg-slate-50/50 focus:bg-white"
                />
              </div>
            </CardHeader>
            <CardContent>
              {isTranscriptsLoading ? (
                <div className="space-y-4">
                  <div className="h-10 bg-slate-50 rounded animate-pulse"></div>
                  <div className="h-10 bg-slate-50 rounded animate-pulse"></div>
                  <div className="h-10 bg-slate-50 rounded animate-pulse"></div>
                </div>
              ) : !transcripts || transcripts.length === 0 ? (
                <div className="flex flex-col items-center justify-center p-8 text-center min-h-[200px]">
                  <MessageSquare className="h-10 w-10 text-slate-300 mb-3" />
                  <p className="font-semibold text-slate-700">No transcript segments found</p>
                </div>
              ) : (
                <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2 divide-y divide-slate-100">
                  {transcripts
                    .filter(seg => seg.content.toLowerCase().includes(transcriptSearch.toLowerCase()))
                    .map((seg, idx) => (
                      <div key={seg.id} className={cn("pt-4 flex flex-col sm:flex-row gap-4 items-start", idx === 0 ? "pt-0 border-t-0" : "")}>
                        <div className="w-full sm:w-44 flex flex-row sm:flex-col items-center sm:items-start justify-between sm:justify-start gap-1">
                          <span className="font-bold text-slate-800 flex items-center gap-1">
                            <User className="h-3.5 w-3.5 text-indigo-500" />
                            {seg.speaker || `Speaker ${seg.segment_index}`}
                          </span>
                          <span className="text-xs font-semibold text-muted-foreground bg-slate-100 px-2 py-0.5 rounded flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatTimestamp(seg.start_time)} - {formatTimestamp(seg.end_time)}
                          </span>
                        </div>
                        <p className="flex-1 text-slate-700 text-sm leading-relaxed whitespace-pre-wrap font-medium">
                          {seg.content}
                        </p>
                      </div>
                    ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* -------------------- 3. Action Items Tab -------------------- */}
        <TabsContent value="action-items" className="space-y-6 focus:outline-none">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">Action Items</h2>
          </div>
          
          {isActionItemsLoading ? (
            <div className="space-y-4">
              <div className="h-20 bg-slate-100 rounded animate-pulse"></div>
              <div className="h-20 bg-slate-100 rounded animate-pulse"></div>
            </div>
          ) : !actionItems || actionItems.length === 0 ? (
            <Card className="border-slate-200 shadow-sm py-12 text-center">
              <ListTodo className="h-10 w-10 text-slate-300 mx-auto mb-3" />
              <p className="font-semibold text-slate-700">No action items extracted</p>
            </Card>
          ) : (
            <div className="grid gap-4">
              {actionItems.map((item) => {
                const isEditing = editingItemId === item.id;
                return (
                  <Card key={item.id} className="border-slate-200 hover:shadow-sm transition-all">
                    <CardContent className="p-5 space-y-4">
                      {isEditing ? (
                        <div className="space-y-4">
                          <div className="space-y-1.5">
                            <label className="text-xs font-bold text-slate-600">Task Description</label>
                            <Input
                              value={(editFields.description as string) || ''}
                              onChange={(e) => handleEditChange('description', e.target.value)}
                            />
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                            <div className="space-y-1.5">
                              <label className="text-xs font-bold text-slate-600">Assignee</label>
                              <Input
                                value={(editFields.assignee as string) || ''}
                                onChange={(e) => handleEditChange('assignee', e.target.value)}
                                placeholder="Name"
                              />
                            </div>
                            <div className="space-y-1.5">
                              <label className="text-xs font-bold text-slate-600">Due Date</label>
                              <Input
                                type="date"
                                value={(editFields.due_date as string) || ''}
                                onChange={(e) => handleEditChange('due_date', e.target.value)}
                              />
                            </div>
                            <div className="space-y-1.5">
                              <label className="text-xs font-bold text-slate-600">Review Status</label>
                              <Select 
                                value={editFields.status as string} 
                                onValueChange={(val) => handleEditChange('status', val)}
                              >
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="draft">Draft</SelectItem>
                                  <SelectItem value="approved">Approved</SelectItem>
                                  <SelectItem value="synced">Synced</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                          </div>
                          <div className="flex justify-end gap-2 pt-2">
                            <Button size="sm" variant="outline" onClick={() => setEditingItemId(null)}>
                              <X className="h-4 w-4 mr-1.5" /> Cancel
                            </Button>
                            <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white" onClick={() => saveActionItemEdit(item.id)}>
                              <Check className="h-4 w-4 mr-1.5" /> Save
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          <div className="flex items-start justify-between gap-4">
                            <div className="space-y-1.5">
                              <p className="font-semibold text-slate-900 leading-snug">{item.description}</p>
                              {item.verbatim_quote && (
                                <p className="text-xs text-muted-foreground italic bg-slate-50 p-2.5 rounded border border-slate-100/50">
                                  &quot;{item.verbatim_quote}&quot;
                                </p>
                              )}
                            </div>
                            {getInsightStatusBadge(item.status)}
                          </div>
                          <div className="flex flex-wrap items-center justify-between gap-4 pt-3 border-t border-slate-100 text-xs text-muted-foreground font-semibold">
                            <div className="flex gap-4">
                              <span className="flex items-center gap-1">
                                <User className="h-3.5 w-3.5 text-indigo-500" />
                                Assignee: <span className="text-slate-800">{item.assignee || 'Unassigned'}</span>
                              </span>
                              {item.due_date && (
                                <span className="flex items-center gap-1">
                                  <Calendar className="h-3.5 w-3.5 text-slate-400" />
                                  Due: <span className="text-slate-800">{formatDate(item.due_date)}</span>
                                </span>
                              )}
                            </div>
                            <div className="flex gap-1.5">
                              <Button size="icon" variant="ghost" className="h-7 w-7 text-slate-500 hover:bg-slate-100" onClick={() => startEditing(item)}>
                                <Edit2 className="h-3.5 w-3.5" />
                              </Button>
                              <Button 
                                size="icon" 
                                variant="ghost" 
                                className="h-7 w-7 text-rose-600 hover:bg-rose-50"
                                onClick={() => deleteActionItemMutation.mutate(item.id)}
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* -------------------- 4. Decisions Tab -------------------- */}
        <TabsContent value="decisions" className="space-y-6 focus:outline-none">
          <h2 className="text-lg font-bold text-slate-900 tracking-tight">Decisions</h2>
          
          {isDecisionsLoading ? (
            <div className="space-y-4">
              <div className="h-20 bg-slate-100 rounded animate-pulse"></div>
            </div>
          ) : !decisions || decisions.length === 0 ? (
            <Card className="border-slate-200 shadow-sm py-12 text-center">
              <FileCheck className="h-10 w-10 text-slate-300 mx-auto mb-3" />
              <p className="font-semibold text-slate-700">No decisions extracted</p>
            </Card>
          ) : (
            <div className="grid gap-4">
              {decisions.map((item) => {
                const isEditing = editingItemId === item.id;
                return (
                  <Card key={item.id} className="border-slate-200 hover:shadow-sm">
                    <CardContent className="p-5 space-y-4">
                      {isEditing ? (
                        <div className="space-y-4">
                          <div className="space-y-1.5">
                            <label className="text-xs font-bold text-slate-600">Decision Summary</label>
                            <Input
                              value={(editFields.description as string) || ''}
                              onChange={(e) => handleEditChange('description', e.target.value)}
                            />
                          </div>
                          <div className="space-y-1.5">
                            <label className="text-xs font-bold text-slate-600">Rationale</label>
                            <Input
                              value={(editFields.rationale as string) || ''}
                              onChange={(e) => handleEditChange('rationale', e.target.value)}
                              placeholder="Explanation"
                            />
                          </div>
                          <div className="w-full sm:w-48 space-y-1.5">
                            <label className="text-xs font-bold text-slate-600">Review Status</label>
                            <Select 
                              value={editFields.status as string} 
                              onValueChange={(val) => handleEditChange('status', val)}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="draft">Draft</SelectItem>
                                <SelectItem value="approved">Approved</SelectItem>
                                <SelectItem value="synced">Synced</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="flex justify-end gap-2 pt-2">
                            <Button size="sm" variant="outline" onClick={() => setEditingItemId(null)}>
                              <X className="h-4 w-4 mr-1.5" /> Cancel
                            </Button>
                            <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white" onClick={() => saveDecisionEdit(item.id)}>
                              <Check className="h-4 w-4 mr-1.5" /> Save
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          <div className="flex items-start justify-between gap-4">
                            <div className="space-y-2">
                              <p className="font-semibold text-slate-900 leading-snug">{item.description}</p>
                              {item.rationale && (
                                <p className="text-sm text-slate-700 bg-indigo-50/30 border border-indigo-100/30 p-2.5 rounded-lg">
                                  <strong className="text-xs font-bold text-indigo-950 uppercase tracking-wide block mb-1">Rationale</strong>
                                  {item.rationale}
                                </p>
                              )}
                              {item.verbatim_quote && (
                                <p className="text-xs text-muted-foreground italic bg-slate-50 p-2 rounded">
                                  &quot;{item.verbatim_quote}&quot;
                                </p>
                              )}
                            </div>
                            {getInsightStatusBadge(item.status)}
                          </div>
                          <div className="flex justify-end gap-1.5 pt-3 border-t border-slate-100">
                            <Button size="icon" variant="ghost" className="h-7 w-7 text-slate-500 hover:bg-slate-100" onClick={() => startEditing(item)}>
                              <Edit2 className="h-3.5 w-3.5" />
                            </Button>
                            <Button 
                              size="icon" 
                              variant="ghost" 
                              className="h-7 w-7 text-rose-600 hover:bg-rose-50"
                              onClick={() => deleteDecisionMutation.mutate(item.id)}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* -------------------- 5. Risks Tab -------------------- */}
        <TabsContent value="risks" className="space-y-6 focus:outline-none">
          <h2 className="text-lg font-bold text-slate-900 tracking-tight">Risks & Blockers</h2>
          
          {isRisksLoading ? (
            <div className="space-y-4">
              <div className="h-20 bg-slate-100 rounded animate-pulse"></div>
            </div>
          ) : !risks || risks.length === 0 ? (
            <Card className="border-slate-200 shadow-sm py-12 text-center">
              <ShieldAlert className="h-10 w-10 text-slate-300 mx-auto mb-3" />
              <p className="font-semibold text-slate-700">No risks identified</p>
            </Card>
          ) : (
            <div className="grid gap-4">
              {risks.map((item) => {
                const isEditing = editingItemId === item.id;
                
                const getSeverityBadge = (sev: string) => {
                  switch (sev) {
                    case 'critical':
                      return <Badge variant="destructive">Critical</Badge>;
                    case 'high':
                      return <Badge className="bg-rose-100 text-rose-800 border-rose-200">High</Badge>;
                    case 'medium':
                      return <Badge className="bg-amber-100 text-amber-800 border-amber-200">Medium</Badge>;
                    case 'low':
                      return <Badge className="bg-slate-100 text-slate-800 border-slate-200">Low</Badge>;
                    default:
                      return <Badge variant="outline">{sev}</Badge>;
                  }
                };

                return (
                  <Card key={item.id} className="border-slate-200 hover:shadow-sm">
                    <CardContent className="p-5 space-y-4">
                      {isEditing ? (
                        <div className="space-y-4">
                          <div className="space-y-1.5">
                            <label className="text-xs font-bold text-slate-600">Risk Description</label>
                            <Input
                              value={(editFields.description as string) || ''}
                              onChange={(e) => handleEditChange('description', e.target.value)}
                            />
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                            <div className="space-y-1.5">
                              <label className="text-xs font-bold text-slate-600">Severity</label>
                              <Select 
                                value={editFields.severity as string} 
                                onValueChange={(val) => handleEditChange('severity', val)}
                              >
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="low">Low</SelectItem>
                                  <SelectItem value="medium">Medium</SelectItem>
                                  <SelectItem value="high">High</SelectItem>
                                  <SelectItem value="critical">Critical</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                            <div className="space-y-1.5 sm:col-span-2">
                              <label className="text-xs font-bold text-slate-600">Mitigation Strategy</label>
                              <Input
                                value={(editFields.mitigation as string) || ''}
                                onChange={(e) => handleEditChange('mitigation', e.target.value)}
                                placeholder="Suggested plan"
                              />
                            </div>
                          </div>
                          <div className="w-full sm:w-48 space-y-1.5">
                            <label className="text-xs font-bold text-slate-600">Review Status</label>
                            <Select 
                              value={editFields.status as string} 
                              onValueChange={(val) => handleEditChange('status', val)}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="draft">Draft</SelectItem>
                                <SelectItem value="approved">Approved</SelectItem>
                                <SelectItem value="synced">Synced</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="flex justify-end gap-2 pt-2">
                            <Button size="sm" variant="outline" onClick={() => setEditingItemId(null)}>
                              <X className="h-4 w-4 mr-1.5" /> Cancel
                            </Button>
                            <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white" onClick={() => saveRiskEdit(item.id)}>
                              <Check className="h-4 w-4 mr-1.5" /> Save
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          <div className="flex items-start justify-between gap-4">
                            <div className="space-y-2">
                              <div className="flex items-center gap-2">
                                {getSeverityBadge(item.severity)}
                                <p className="font-semibold text-slate-900 leading-snug">{item.description}</p>
                              </div>
                              {item.mitigation && (
                                <p className="text-sm text-slate-700 bg-rose-50/30 border border-rose-100/30 p-2.5 rounded-lg">
                                  <strong className="text-xs font-bold text-rose-950 uppercase tracking-wide block mb-1">Mitigation Plan</strong>
                                  {item.mitigation}
                                </p>
                              )}
                              {item.verbatim_quote && (
                                <p className="text-xs text-muted-foreground italic bg-slate-50 p-2 rounded">
                                  &quot;{item.verbatim_quote}&quot;
                                </p>
                              )}
                            </div>
                            {getInsightStatusBadge(item.status)}
                          </div>
                          <div className="flex justify-end gap-1.5 pt-3 border-t border-slate-100">
                            <Button size="icon" variant="ghost" className="h-7 w-7 text-slate-500 hover:bg-slate-100" onClick={() => startEditing(item)}>
                              <Edit2 className="h-3.5 w-3.5" />
                            </Button>
                            <Button 
                              size="icon" 
                              variant="ghost" 
                              className="h-7 w-7 text-rose-600 hover:bg-rose-50"
                              onClick={() => deleteRiskMutation.mutate(item.id)}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* -------------------- 6. Chat Signals Tab -------------------- */}
        <TabsContent value="chat-signals" className="space-y-6 focus:outline-none">
          <Card className="border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg font-bold tracking-tight">Corporate Chat Signals</CardTitle>
              <CardDescription>Real-time channel streams parsed by the intelligence daemon.</CardDescription>
            </CardHeader>
            <CardContent>
              {isChatSignalsLoading ? (
                <div className="space-y-4">
                  <div className="h-10 bg-slate-100 rounded animate-pulse"></div>
                </div>
              ) : !chatSignals || chatSignals.length === 0 ? (
                <div className="flex flex-col items-center justify-center p-8 text-center min-h-[200px]">
                  <Terminal className="h-10 w-10 text-slate-300 mb-3" />
                  <p className="font-semibold text-slate-700">No chat signals classified yet</p>
                </div>
              ) : (
                <div className="space-y-4 divide-y divide-slate-100 max-h-[500px] overflow-y-auto pr-2">
                  {chatSignals.map((sig, idx) => {
                    const getSignalBadge = (type: string) => {
                      switch (type) {
                        case 'blocker':
                          return <Badge className="bg-rose-100 text-rose-800 border-rose-200">Blocker</Badge>;
                        case 'decision':
                          return <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">Decision</Badge>;
                        case 'risk':
                          return <Badge className="bg-amber-100 text-amber-800 border-amber-200">Risk</Badge>;
                        default:
                          return <Badge className="bg-slate-100 text-slate-800 border-slate-200">General</Badge>;
                      }
                    };

                    return (
                      <div key={sig.id} className={cn("pt-4 flex flex-col gap-2.5", idx === 0 ? "pt-0" : "")}>
                        <div className="flex items-center justify-between text-xs text-muted-foreground font-semibold">
                          <div className="flex items-center gap-3">
                            <span className="font-bold text-slate-900 flex items-center gap-1">
                              <User className="h-3.5 w-3.5 text-indigo-500" />
                              {sig.sender_name || 'Anonymous'}
                            </span>
                            <span>•</span>
                            <span className="bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded text-[10px] font-bold">
                              #{sig.channel_id}
                            </span>
                            <span>via</span>
                            <span className="font-bold text-indigo-600 capitalize">{sig.source}</span>
                          </div>
                          <span>{formatDate(sig.created_at)}</span>
                        </div>
                        <div className="p-3 bg-slate-50/50 rounded-xl border border-slate-100/50 text-slate-800 text-sm leading-relaxed font-medium">
                          {sig.content}
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          {getSignalBadge(sig.signal_type)}
                          {sig.confidence && (
                            <span className="text-muted-foreground font-semibold">
                              Confidence: <span className="font-bold text-slate-800">{(sig.confidence * 100).toFixed(0)}%</span>
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* -------------------- 7. Sync Logs Tab -------------------- */}
        <TabsContent value="sync-logs" className="space-y-6 focus:outline-none">
          <Card className="border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg font-bold tracking-tight">Synchronization Logs</CardTitle>
              <CardDescription>Audit timeline records of dispatch attempts sent to project management webhooks.</CardDescription>
            </CardHeader>
            <CardContent>
              {isSyncLogsLoading ? (
                <div className="space-y-4">
                  <div className="h-10 bg-slate-100 rounded animate-pulse"></div>
                </div>
              ) : !syncLogs || syncLogs.length === 0 ? (
                <div className="flex flex-col items-center justify-center p-8 text-center min-h-[200px]">
                  <RefreshCw className="h-10 w-10 text-slate-300 mb-3" />
                  <p className="font-semibold text-slate-700">No synchronization attempts recorded</p>
                  <p className="text-xs text-muted-foreground mt-1">Navigate to the Synchronization Hub to sync approved insights.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {syncLogs.map((log) => {
                    const getSyncStatusBadge = (status: string) => {
                      switch (status) {
                        case 'success':
                          return <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">Success</Badge>;
                        case 'failed':
                          return <Badge variant="destructive">Failed</Badge>;
                        case 'pending':
                          return <Badge className="bg-indigo-100 text-indigo-800 border-indigo-200">Pending</Badge>;
                        default:
                          return <Badge variant="outline">{status}</Badge>;
                      }
                    };

                    return (
                      <div key={log.id} className="flex gap-4 p-4 rounded-xl border border-slate-100 bg-slate-50/50 hover:bg-slate-50 transition-colors">
                        <div className="flex flex-col items-center justify-center">
                          <div className={cn(
                            "p-2 rounded-full",
                            log.status === 'success' ? "bg-emerald-50 text-emerald-600" : log.status === 'failed' ? "bg-rose-50 text-rose-600" : "bg-indigo-50 text-indigo-600"
                          )}>
                            <RefreshCw className="h-4.5 w-4.5" />
                          </div>
                        </div>
                        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              {getSyncStatusBadge(log.status)}
                              {log.http_status && (
                                <Badge variant="outline" className="font-bold">
                                  HTTP {log.http_status}
                                </Badge>
                              )}
                            </div>
                            <p className="text-slate-800 font-bold pt-1">
                              Response: <span className="font-semibold text-slate-600">{log.response_message || 'N/A'}</span>
                            </p>
                            {log.payload_hash && (
                              <p className="text-[10px] text-muted-foreground font-mono truncate max-w-[280px]">
                                Hash: {log.payload_hash}
                              </p>
                            )}
                          </div>
                          <div className="space-y-1 text-left md:text-right font-medium text-slate-700 text-xs">
                            <p className="text-slate-500 font-semibold">
                              Attempt: <span className="font-mono text-slate-700 select-all">{log.id.slice(0, 8)}...</span>
                            </p>
                            {log.dispatched_at && (
                              <p>Completed: {new Date(log.dispatched_at).toLocaleString()}</p>
                            )}
                            <p className="text-[10px] text-slate-400">Created: {new Date(log.created_at).toLocaleString()}</p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
