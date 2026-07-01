'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api-client';
import axios from 'axios';
import { 
  UploadCloud, 
  FileAudio, 
  CheckCircle, 
  AlertTriangle, 
  Loader2, 
  Compass,
  ArrowRight
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';

export default function UploadPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [meetingDate, setMeetingDate] = useState('');
  const [source, setSource] = useState('Upload');
  const [duration, setDuration] = useState('');
  const [consent, setConsent] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  // Uploading / processing states
  const [step, setStep] = useState<'form' | 'uploading' | 'processing' | 'success' | 'error'>('form');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [meetingId, setMeetingId] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<string>('pending');
  const [errorMessage, setErrorMessage] = useState('');

  // Handle file select
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      const validTypes = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 'audio/mp4', 'audio/m4a', 'video/mp4', 'audio/x-m4a'];
      const ext = selectedFile.name.split('.').pop()?.toLowerCase();
      
      // Basic check
      if (validTypes.includes(selectedFile.type) || ['mp3', 'wav', 'mp4', 'm4a'].includes(ext || '')) {
        setFile(selectedFile);
        if (!title) {
          // Auto-fill title with file name (without extension)
          setTitle(selectedFile.name.replace(/\.[^/.]+$/, ""));
        }
      } else {
        toast.error('Invalid file type. Please upload MP3, WAV, MP4 or M4A audio.');
      }
    }
  };

  // Submit form
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      toast.error('Please select an audio file to upload.');
      return;
    }
    if (!consent) {
      toast.error('You must give consent to process the recording.');
      return;
    }

    setStep('uploading');
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('title', title);
    formData.append('consent_given', String(consent));
    formData.append('source', source);
    if (meetingDate) {
      // API expects ISO 8601 datetime format
      formData.append('meeting_date', new Date(meetingDate).toISOString());
    }
    if (duration) {
      formData.append('duration_minutes', duration);
    }
    formData.append('audio_file', file);

    try {
      const response = await api.uploadMeeting(formData, (progressEvent) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        }
      });

      setMeetingId(response.meeting_id);
      setProcessingStatus(response.status);
      setStep('processing');
    } catch (err: unknown) {
      console.error(err);
      setStep('error');
      let msg = 'An error occurred during upload. Please verify backend connectivity.';
      if (axios.isAxiosError(err)) {
        msg = err.response?.data?.error?.message || err.message || msg;
      } else if (err instanceof Error) {
        msg = err.message;
      }
      setErrorMessage(msg);
    }
  };

  // Poll for processing status
  useEffect(() => {
    if (step !== 'processing' || !meetingId) return;

    const checkStatus = async (id: NodeJS.Timeout) => {
      try {
        const meeting = await api.getMeeting(meetingId);
        setProcessingStatus(meeting.status);

        if (meeting.status === 'completed') {
          setStep('success');
          toast.success('Meeting processed successfully!');
          clearInterval(id);
          // Redirect to details page after 2 seconds
          setTimeout(() => {
            router.push(`/meetings/${meetingId}`);
          }, 2000);
        } else if (meeting.status === 'failed') {
          setStep('error');
          setErrorMessage('Audio transcription or AI insight extraction failed. Check celery worker logs.');
          clearInterval(id);
        }
      } catch (err: unknown) {
        console.error('Polling error:', err);
      }
    };

    const intervalId = setInterval(() => {
      checkStatus(intervalId);
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(intervalId);
  }, [step, meetingId, router]);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 md:text-4xl">
          Upload Meeting
        </h1>
        <p className="text-muted-foreground mt-1.5">
          Ingest a new recording to transcribe and extract summaries, decisions, and tasks.
        </p>
      </div>

      {step === 'form' && (
        <form onSubmit={handleSubmit}>
          <Card className="border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg font-bold tracking-tight">Meeting Details</CardTitle>
              <CardDescription>Fill in metadata and select the meeting recording file.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              {/* File Dropzone */}
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700">Audio File</label>
                <div className="flex justify-center rounded-xl border border-dashed border-slate-300 px-6 py-8 bg-slate-50/50 hover:bg-slate-50 transition-colors relative">
                  <div className="text-center space-y-2">
                    <UploadCloud className="mx-auto h-10 w-10 text-slate-400" />
                    <div className="flex text-sm text-slate-600 justify-center">
                      <label className="relative cursor-pointer rounded-md font-semibold text-indigo-600 focus-within:outline-none focus-within:ring-2 focus-within:ring-indigo-600 focus-within:ring-offset-2 hover:text-indigo-500">
                        <span>Upload a file</span>
                        <input 
                          type="file" 
                          className="sr-only" 
                          accept="audio/*,video/mp4" 
                          onChange={handleFileChange}
                        />
                      </label>
                      <p className="pl-1">or drag and drop</p>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      MP3, WAV, MP4, M4A up to 100MB
                    </p>
                    {file && (
                      <div className="flex items-center gap-2 mt-4 bg-white p-2.5 rounded-lg border border-slate-100 shadow-sm inline-flex">
                        <FileAudio className="h-5 w-5 text-indigo-600" />
                        <span className="text-sm font-semibold text-slate-900 max-w-[280px] truncate">
                          {file.name}
                        </span>
                        <span className="text-xs text-muted-foreground bg-slate-100 px-2 py-0.5 rounded">
                          {(file.size / (1024 * 1024)).toFixed(2)} MB
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Title Input */}
              <div className="space-y-1.5">
                <label htmlFor="title" className="text-sm font-semibold text-slate-700">Meeting Title *</label>
                <Input 
                  id="title" 
                  value={title} 
                  onChange={(e) => setTitle(e.target.value)} 
                  placeholder="e.g. Q3 Sales Strategy Planning" 
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Meeting Date */}
                <div className="space-y-1.5">
                  <label htmlFor="date" className="text-sm font-semibold text-slate-700">Meeting Date & Time</label>
                  <Input 
                    id="date" 
                    type="datetime-local" 
                    value={meetingDate} 
                    onChange={(e) => setMeetingDate(e.target.value)}
                  />
                </div>

                {/* Duration */}
                <div className="space-y-1.5">
                  <label htmlFor="duration" className="text-sm font-semibold text-slate-700">Duration (Minutes)</label>
                  <Input 
                    id="duration" 
                    type="number" 
                    min="0"
                    placeholder="e.g. 45" 
                    value={duration} 
                    onChange={(e) => setDuration(e.target.value)}
                  />
                </div>
              </div>

              {/* Source Platform */}
              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-700">Source Platform</label>
                <Select value={source} onValueChange={(val) => setSource(val || 'Upload')}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select platform" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Upload">Manual Upload</SelectItem>
                    <SelectItem value="Zoom">Zoom</SelectItem>
                    <SelectItem value="Teams">Microsoft Teams</SelectItem>
                    <SelectItem value="Google Meet">Google Meet</SelectItem>
                    <SelectItem value="Slack">Slack Call</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Consent Toggle */}
              <div className="flex items-start gap-3 bg-indigo-50/50 p-4 rounded-xl border border-indigo-100/50">
                <input 
                  type="checkbox" 
                  id="consent" 
                  checked={consent} 
                  onChange={(e) => setConsent(e.target.checked)}
                  className="mt-1 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600"
                />
                <label htmlFor="consent" className="text-sm text-indigo-950 font-medium cursor-pointer">
                  I confirm that all participants have provided explicit consent for this meeting to be recorded, transcribed, and analyzed by the AI Meeting Agent.
                </label>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end gap-3 border-t border-slate-100 bg-slate-50/30 py-4">
              <Button type="button" variant="outline" onClick={() => router.back()}>
                Cancel
              </Button>
              <Button type="submit" className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium" disabled={!file || !consent}>
                Start Ingestion
              </Button>
            </CardFooter>
          </Card>
        </form>
      )}

      {/* Uploading Progress Screen */}
      {step === 'uploading' && (
        <Card className="border-slate-200 shadow-sm py-8">
          <CardContent className="flex flex-col items-center justify-center space-y-6 text-center">
            <div className="p-4 bg-indigo-50 text-indigo-600 rounded-full animate-bounce">
              <UploadCloud className="h-10 w-10" />
            </div>
            <div className="space-y-1">
              <CardTitle className="text-xl font-bold tracking-tight">Uploading Recording</CardTitle>
              <CardDescription>Streaming audio file to backend file storage...</CardDescription>
            </div>
            <div className="w-full max-w-md space-y-2">
              <Progress value={uploadProgress} className="h-2" />
              <div className="flex justify-between text-xs text-muted-foreground font-semibold">
                <span>{uploadProgress}% Uploaded</span>
                <span>Please keep this window open</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Processing Screen */}
      {step === 'processing' && (
        <Card className="border-slate-200 shadow-sm py-8">
          <CardContent className="flex flex-col items-center justify-center space-y-6 text-center">
            <div className="relative flex items-center justify-center">
              <Loader2 className="h-14 w-14 text-indigo-600 animate-spin" />
              <Compass className="h-6 w-6 text-indigo-600 absolute animate-pulse" />
            </div>
            <div className="space-y-1.5">
              <CardTitle className="text-xl font-bold tracking-tight">AI Pipeline Running</CardTitle>
              <CardDescription>File received! Transcribing and generating analytics.</CardDescription>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 max-w-md w-full space-y-3.5 text-sm text-left">
              <div className="flex items-center gap-3">
                <div className="h-5 w-5 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-bold">1</div>
                <span className="font-semibold text-slate-800">Audio Ingestion: Success</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-5 w-5 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold">
                  {processingStatus === 'pending' ? <span className="animate-pulse">●</span> : '2'}
                </div>
                <span className={`font-semibold ${processingStatus === 'pending' ? 'text-indigo-600' : 'text-slate-800'}`}>
                  Speech-to-Text Transcription: {processingStatus === 'pending' ? 'Pending...' : 'Active'}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-5 w-5 rounded-full bg-indigo-50 text-indigo-400 flex items-center justify-center text-xs font-bold">3</div>
                <span className={`font-semibold ${processingStatus === 'processing' ? 'text-indigo-600 animate-pulse' : 'text-slate-400'}`}>
                  Gemini LLM Insight Extraction: {processingStatus === 'processing' ? 'Running...' : 'Pending'}
                </span>
              </div>
            </div>
            <p className="text-xs text-muted-foreground animate-pulse font-medium">
              This usually takes 1–3 minutes depending on meeting duration.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Success Redirect Screen */}
      {step === 'success' && (
        <Card className="border-slate-200 shadow-sm py-8">
          <CardContent className="flex flex-col items-center justify-center space-y-5 text-center">
            <div className="p-4 bg-emerald-50 text-emerald-600 rounded-full">
              <CheckCircle className="h-12 w-12" />
            </div>
            <div className="space-y-1">
              <CardTitle className="text-2xl font-bold tracking-tight text-slate-900">Processing Complete!</CardTitle>
              <CardDescription>Meeting transcript, decisions, and actions have been compiled.</CardDescription>
            </div>
            <div className="flex items-center gap-2 text-sm text-indigo-600 font-semibold animate-pulse">
              <span>Redirecting to Meeting Intelligence Details</span>
              <ArrowRight className="h-4 w-4" />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Screen */}
      {step === 'error' && (
        <Card className="border-slate-200 shadow-sm py-8">
          <CardContent className="flex flex-col items-center justify-center space-y-6 text-center">
            <div className="p-4 bg-rose-50 text-rose-600 rounded-full">
              <AlertTriangle className="h-12 w-12" />
            </div>
            <div className="space-y-1.5 max-w-md">
              <CardTitle className="text-xl font-bold tracking-tight text-slate-900">Ingestion Failure</CardTitle>
              <CardDescription className="text-rose-600 font-semibold bg-rose-50 p-3 rounded-lg border border-rose-100 text-sm">
                {errorMessage}
              </CardDescription>
            </div>
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => setStep('form')}>
                Back to Form
              </Button>
              <Button className="bg-indigo-600 hover:bg-indigo-700 text-white" onClick={handleSubmit}>
                Retry Ingestion
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
