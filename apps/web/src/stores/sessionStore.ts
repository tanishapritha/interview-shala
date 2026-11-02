import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { InterviewProject, PreparationPlan } from '@/types';

type SessionState = {
  anonymousId: string | null;
  activeProjectId: string | null;
  project: InterviewProject | null;
  plan: PreparationPlan | null;
  setAnonymousId: (id: string) => void;
  setProject: (project: InterviewProject, plan?: PreparationPlan | null) => void;
  setPlan: (plan: PreparationPlan) => void;
  clear: () => void;
};

export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      anonymousId: null,
      activeProjectId: null,
      project: null,
      plan: null,
      setAnonymousId: (id) => set({ anonymousId: id }),
      setProject: (project, plan = null) =>
        set({
          project,
          plan,
          activeProjectId: project.id,
        }),
      setPlan: (plan) => set({ plan }),
      clear: () =>
        set({
          project: null,
          plan: null,
          activeProjectId: null,
        }),
    }),
    {
      name: 'interview-shala-session',
      partialize: (state) => ({
        anonymousId: state.anonymousId,
        activeProjectId: state.activeProjectId,
        project: state.project,
        plan: state.plan,
      }),
    },
  ),
);
