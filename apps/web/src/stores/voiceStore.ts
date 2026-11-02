import { create } from 'zustand';
import type { SessionStatus } from '@/types';

type TranscriptLine = {
  id: string;
  role: 'interviewer' | 'candidate';
  text: string;
  at: number;
};

type VoiceState = {
  status: SessionStatus;
  sessionId: string | null;
  roomName: string | null;
  currentQuestion: string | null;
  elapsedSeconds: number;
  muted: boolean;
  transcript: TranscriptLine[];
  transcriptOpen: boolean;
  setStatus: (status: SessionStatus) => void;
  setSession: (sessionId: string, roomName: string) => void;
  setCurrentQuestion: (q: string | null) => void;
  setElapsed: (seconds: number) => void;
  setMuted: (muted: boolean) => void;
  addTranscript: (line: Omit<TranscriptLine, 'id' | 'at'>) => void;
  setTranscriptOpen: (open: boolean) => void;
  reset: () => void;
};

const initial = {
  status: 'pending' as SessionStatus,
  sessionId: null,
  roomName: null,
  currentQuestion: null,
  elapsedSeconds: 0,
  muted: false,
  transcript: [] as TranscriptLine[],
  transcriptOpen: false,
};

export const useVoiceStore = create<VoiceState>((set) => ({
  ...initial,
  setStatus: (status) => set({ status }),
  setSession: (sessionId, roomName) => set({ sessionId, roomName }),
  setCurrentQuestion: (currentQuestion) => set({ currentQuestion }),
  setElapsed: (elapsedSeconds) => set({ elapsedSeconds }),
  setMuted: (muted) => set({ muted }),
  addTranscript: (line) =>
    set((s) => ({
      transcript: [
        ...s.transcript,
        { ...line, id: crypto.randomUUID(), at: Date.now() },
      ],
    })),
  setTranscriptOpen: (transcriptOpen) => set({ transcriptOpen }),
  reset: () => set({ ...initial, transcript: [] }),
}));
