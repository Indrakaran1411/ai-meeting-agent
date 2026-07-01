import axios, { AxiosProgressEvent } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface MeetingListResponseItem {
  id: string;
  title: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  meeting_date: string | null;
  duration_minutes: number | null;
  source: string | null;
  summary_preview: string | null;
}

export interface MeetingListResponse {
  total_count: number;
  items: MeetingListResponseItem[];
}

export interface MeetingDetailResponse {
  id: string;
  title: string;
  meeting_date: string | null;
  duration_minutes: number | null;
  source: string | null;
  consent_given: boolean;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  file_path: string | null;
  summary: string | null;
  created_at: string;
  updated_at: string;
}

export interface MeetingStatisticsResponse {
  total_meetings: number;
  completed_meetings: number;
  processing_meetings: number;
  failed_meetings: number;
  pending_meetings: number;
  total_action_items: number;
  total_decisions: number;
  total_risks: number;
}

export interface ActionItemResponse {
  id: string;
  meeting_id: string;
  description: string;
  assignee: string | null;
  due_date: string | null;
  verbatim_quote: string | null;
  status: 'draft' | 'approved' | 'synced';
  created_at: string;
  updated_at: string;
}

export interface DecisionResponse {
  id: string;
  meeting_id: string;
  description: string;
  rationale: string | null;
  verbatim_quote: string | null;
  status: 'draft' | 'approved' | 'synced';
  created_at: string;
  updated_at: string;
}

export interface RiskResponse {
  id: string;
  meeting_id: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  mitigation: string | null;
  verbatim_quote: string | null;
  status: 'draft' | 'approved' | 'synced';
  created_at: string;
  updated_at: string;
}

export interface TranscriptResponse {
  id: string;
  meeting_id: string;
  speaker: string | null;
  content: string;
  segment_index: number;
  start_time: number;
  end_time: number;
  created_at: string;
  updated_at: string;
}

export interface SyncLogResponse {
  id: string;
  meeting_id: string;
  request_id: string | null;
  webhook_url: string | null;
  status: 'pending' | 'success' | 'failed';
  http_status: number | null;
  response_message: string | null;
  payload_hash: string | null;
  dispatched_at: string | null;
  created_at: string;
}

export interface ChatSignalResponse {
  id: string;
  source: string;
  channel_id: string;
  message_id: string;
  sender_name: string | null;
  content: string;
  signal_type: 'blocker' | 'decision' | 'risk' | 'general';
  confidence: number | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardResponse {
  statistics: MeetingStatisticsResponse;
  recent_meetings: MeetingListResponseItem[];
  recent_action_items: ActionItemResponse[];
}

export interface MeetingSyncResponse {
  success: boolean;
  meeting_id: string;
  status_code: number | null;
  message: string;
  dispatched_at: string | null;
  sync_log_id: string | null;
  skipped: boolean;
  reason: string | null;
}

export const api = {
  getDashboard: async (): Promise<DashboardResponse> => {
    const res = await axiosInstance.get<DashboardResponse>('/dashboard');
    return res.data;
  },

  getStatistics: async (): Promise<MeetingStatisticsResponse> => {
    const res = await axiosInstance.get<MeetingStatisticsResponse>('/meetings/stats');
    return res.data;
  },

  getMeetings: async (params: {
    limit?: number;
    offset?: number;
    status?: string;
    source?: string;
    q?: string;
  }): Promise<MeetingListResponse> => {
    // If a search query 'q' is present, call search; otherwise call standard listing.
    const endpoint = params.q ? '/meetings/search' : '/meetings';
    const res = await axiosInstance.get<MeetingListResponse>(endpoint, { params });
    return res.data;
  },

  getMeeting: async (id: string): Promise<MeetingDetailResponse> => {
    const res = await axiosInstance.get<MeetingDetailResponse>(`/meetings/${id}`);
    return res.data;
  },

  getMeetingActionItems: async (id: string): Promise<ActionItemResponse[]> => {
    const res = await axiosInstance.get<ActionItemResponse[]>(`/meetings/${id}/action-items`);
    return res.data;
  },

  getMeetingDecisions: async (id: string): Promise<DecisionResponse[]> => {
    const res = await axiosInstance.get<DecisionResponse[]>(`/meetings/${id}/decisions`);
    return res.data;
  },

  getMeetingRisks: async (id: string): Promise<RiskResponse[]> => {
    const res = await axiosInstance.get<RiskResponse[]>(`/meetings/${id}/risks`);
    return res.data;
  },

  getMeetingTranscript: async (id: string): Promise<TranscriptResponse[]> => {
    const res = await axiosInstance.get<TranscriptResponse[]>(`/meetings/${id}/transcript`);
    return res.data;
  },

  getMeetingSyncLogs: async (id: string): Promise<SyncLogResponse[]> => {
    const res = await axiosInstance.get<SyncLogResponse[]>(`/meetings/${id}/sync-logs`);
    return res.data;
  },

  getChatSignals: async (params?: { limit?: number; offset?: number }): Promise<ChatSignalResponse[]> => {
    const res = await axiosInstance.get<ChatSignalResponse[]>('/chat-signals', { params });
    return res.data;
  },

  uploadMeeting: async (
    formData: FormData,
    onUploadProgress?: (progressEvent: AxiosProgressEvent) => void
  ) => {
    const res = await axiosInstance.post('/meetings/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
    return res.data;
  },

  patchActionItem: async (id: string, payload: Partial<ActionItemResponse>): Promise<ActionItemResponse> => {
    const res = await axiosInstance.patch<ActionItemResponse>(`/action-items/${id}`, payload);
    return res.data;
  },

  patchDecision: async (id: string, payload: Partial<DecisionResponse>): Promise<DecisionResponse> => {
    const res = await axiosInstance.patch<DecisionResponse>(`/decisions/${id}`, payload);
    return res.data;
  },

  patchRisk: async (id: string, payload: Partial<RiskResponse>): Promise<RiskResponse> => {
    const res = await axiosInstance.patch<RiskResponse>(`/risks/${id}`, payload);
    return res.data;
  },

  deleteActionItem: async (id: string): Promise<void> => {
    await axiosInstance.delete(`/action-items/${id}`);
  },

  deleteDecision: async (id: string): Promise<void> => {
    await axiosInstance.delete(`/decisions/${id}`);
  },

  deleteRisk: async (id: string): Promise<void> => {
    await axiosInstance.delete(`/risks/${id}`);
  },

  deleteMeeting: async (id: string): Promise<void> => {
    await axiosInstance.delete(`/meetings/${id}`);
  },

  syncMeeting: async (id: string): Promise<MeetingSyncResponse> => {
    const res = await axiosInstance.post<MeetingSyncResponse>(`/meetings/${id}/sync`);
    return res.data;
  },
};
