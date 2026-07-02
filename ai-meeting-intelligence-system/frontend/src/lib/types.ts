export type ActionItem = {
  title: string;
  owner?: string | null;
  due_date?: string | null;
  status: string;
};

export type MeetingListItem = {
  id: string;
  title?: string | null;
  participants: string[];
  created_at: string;
};

export type MeetingOut = {
  id: string;
  title?: string | null;
  participants: string[];
  audio_filename?: string | null;
  transcript_text: string;
  speaker_segments?: Array<{
    speaker: string;
    speaker_id?: string;
    text: string;
    start?: number | null;
    end?: number | null;
  }>;
  summary?: string | null;
  key_points?: string[];
  sentiment?: Record<string, unknown> | null;
  action_items: ActionItem[];
  created_at: string;
};

export type AskResponse = {
  answer: string;
  sources: Array<{
    id: string;
    meeting_id: string;
    chunk_index: number;
    distance: number;
    chunk: string;
  }>;
};

export type GraphData = {
  nodes: Array<{ id: string; label: string; kind: string }>;
  edges: Array<{ source: string; target: string; kind: string }>;
};

export type TaskTrackerOut = {
  id: string;
  task_id: string;
  task_name: string;
  assigned_to?: string | null;
  meeting_id?: string | null;
  deadline?: string | null;
  status: "pending" | "completed";
  created_at: string;
  updated_at: string;
};

