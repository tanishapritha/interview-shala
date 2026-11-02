/**
 * Shared types mirroring apps/api Pydantic schemas / frontend contracts.
 */

export type RoundType =
  | 'technical'
  | 'hr'
  | 'behavioral'
  | 'project'
  | 'system_design'
  | 'dsa';

export type SessionStatus =
  | 'pending'
  | 'connecting'
  | 'listening'
  | 'thinking'
  | 'speaking'
  | 'interrupted'
  | 'reconnecting'
  | 'completed'
  | 'failed';

export type Severity = 'mild' | 'moderate' | 'needs_improvement' | 'critical';

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp?: string | null;
}

export interface AnonymousSessionResponse {
  sessionId: string;
  expiresInDays: number;
}

export interface MigrateAnonymousRequest {
  anonymousSessionId?: string | null;
}

export interface MessageResponse {
  message: string;
  details?: Record<string, unknown> | null;
}

export interface InterviewProject {
  id: string;
  company: string;
  role: string;
  jobDescription?: string | null;
  companyUrl?: string | null;
  interviewDate?: string | null;
  additionalContext?: string | null;
  readinessScore: number;
  progressPercent: number;
  createdAt: string;
  updatedAt: string;
}

export interface InterviewProjectCreate {
  company: string;
  role: string;
  jobDescription?: string | null;
  companyUrl?: string | null;
  interviewDate?: string | null;
  additionalContext?: string | null;
}

export interface InterviewProjectUpdate {
  company?: string;
  role?: string;
  jobDescription?: string | null;
  companyUrl?: string | null;
  interviewDate?: string | null;
  additionalContext?: string | null;
}

export interface PreparationTask {
  id: string;
  title: string;
  description?: string | null;
  roundType: RoundType;
  priority: number;
  completed: boolean;
  estimatedMinutes?: number | null;
}

export interface PreparationRound {
  id: string;
  name: string;
  roundType: RoundType;
  priority: number;
  progressPercent: number;
  topics: string[];
  questionCount: number;
  description?: string | null;
}

export interface PreparationPlan {
  id: string;
  projectId: string;
  summary: string;
  rounds: PreparationRound[];
  tasks: PreparationTask[];
  todayTasks: PreparationTask[];
}

export interface SkillScore {
  skill: string;
  score: number;
  maxScore: number;
}

export interface PracticeSession {
  id: string;
  projectId: string;
  roundId?: string | null;
  roundType: RoundType;
  status: SessionStatus;
  score?: number | null;
  durationSeconds?: number | null;
  questionsCompleted?: number | null;
  skillScores?: SkillScore[];
  strengths?: string[];
  improvements?: string[];
  nextAction?: string | null;
  createdAt: string;
  completedAt?: string | null;
}

export interface PracticeSessionCreate {
  projectId: string;
  roundId?: string | null;
  roundType?: RoundType;
}

export interface PracticeSessionComplete {
  durationSeconds?: number | null;
  questionsCompleted?: number | null;
  transcriptSummary?: string | null;
  skillScores?: SkillScore[] | null;
  strengths?: string[] | null;
  improvements?: string[] | null;
}

export interface Weakness {
  id: string;
  skill: string;
  severity: Severity;
  observationCount: number;
  summary: string;
  evidence: string[];
  recommendedExercise: string;
  recentProgress?: number | null;
  updatedAt: string;
}

export interface QuickStartPayload {
  company: string;
  role: string;
  jobDescription?: string;
  interviewDate?: string;
  companyUrl?: string;
  additionalContext?: string;
}

export interface QuickStartResponse {
  project: InterviewProject;
  plan: PreparationPlan;
}

export interface LiveKitTokenResponse {
  token: string;
  roomName: string;
  livekitUrl: string;
  sessionId: string;
}

/** API route path helpers (relative to /api/v1). */
export const ApiRoutes = {
  health: '/health',
  anonymousAuth: '/auth/anonymous',
  migrateAuth: '/auth/migrate',
  projects: '/projects',
  quickStart: '/projects/quick-start',
  project: (id: string) => `/projects/${id}`,
  projectPlan: (id: string) => `/projects/${id}/plan`,
  plan: (id: string) => `/plans/${id}`,
  planTask: (planId: string, taskId: string) => `/plans/${planId}/tasks/${taskId}`,
  round: (id: string) => `/rounds/${id}`,
  roundsByProject: (projectId: string) => `/rounds/by-project/${projectId}`,
  sessions: '/sessions',
  session: (id: string) => `/sessions/${id}`,
  sessionToken: (id: string) => `/sessions/${id}/token`,
  sessionComplete: (id: string) => `/sessions/${id}/complete`,
  weaknessesByProject: (projectId: string) => `/weaknesses/project/${projectId}`,
} as const;
