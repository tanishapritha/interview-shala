import { apiFetch } from '@/lib/api';
import type {
  InterviewProject,
  LiveKitTokenResponse,
  PracticeSession,
  PreparationPlan,
  PreparationRound,
  QuickStartPayload,
  Weakness,
} from '@/types';

function authHeaders(anonymousId: string | null, token?: string | null) {
  return { anonymousId, token };
}

export async function createAnonymousSession(): Promise<{ anonymousId: string }> {
  // APIModel serializes session_id as sessionId (camelCase).
  const data = await apiFetch<{ sessionId: string }>('/api/v1/auth/anonymous', {
    method: 'POST',
  });
  return { anonymousId: data.sessionId };
}

export async function quickStart(
  payload: QuickStartPayload,
  anonymousId: string | null,
  token?: string | null,
): Promise<{ project: InterviewProject; plan: PreparationPlan }> {
  return apiFetch('/api/v1/projects/quick-start', {
    method: 'POST',
    body: payload,
    ...authHeaders(anonymousId, token),
  });
}

export async function getProject(id: string, anonymousId: string | null, token?: string | null): Promise<InterviewProject> {
  return apiFetch(`/api/v1/projects/${id}`, authHeaders(anonymousId, token));
}

export async function getPlan(projectId: string, anonymousId: string | null, token?: string | null): Promise<PreparationPlan> {
  return apiFetch(`/api/v1/projects/${projectId}/plan`, authHeaders(anonymousId, token));
}

export async function getRound(roundId: string, anonymousId: string | null, token?: string | null): Promise<PreparationRound> {
  return apiFetch(`/api/v1/rounds/${roundId}`, authHeaders(anonymousId, token));
}

export async function listWeaknesses(projectId: string, anonymousId: string | null, token?: string | null): Promise<Weakness[]> {
  return apiFetch(`/api/v1/weaknesses/project/${projectId}`, authHeaders(anonymousId, token));
}

export async function createSession(projectId: string, roundId: string | undefined, roundType: string, anonymousId: string | null, token?: string | null): Promise<PracticeSession> {
  return apiFetch('/api/v1/sessions', {
    method: 'POST',
    body: { projectId, roundId, roundType },
    ...authHeaders(anonymousId, token),
  });
}

export async function getLiveKitToken(sessionId: string, anonymousId: string | null, token?: string | null): Promise<LiveKitTokenResponse> {
  return apiFetch(`/api/v1/sessions/${sessionId}/token`, {
    method: 'POST',
    ...authHeaders(anonymousId, token),
  });
}

export async function completeSession(
  sessionId: string,
  payload: { durationSeconds: number; transcript?: { role: string; text: string }[] },
  anonymousId: string | null,
  token?: string | null,
): Promise<PracticeSession> {
  return apiFetch(`/api/v1/sessions/${sessionId}/complete`, {
    method: 'POST',
    body: payload,
    ...authHeaders(anonymousId, token),
  });
}

export async function listSessions(projectId: string, anonymousId: string | null, token?: string | null): Promise<PracticeSession[]> {
  return apiFetch(`/api/v1/sessions?project_id=${projectId}`, authHeaders(anonymousId, token));
}
