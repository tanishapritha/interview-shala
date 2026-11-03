import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { InterviewProject, PreparationPlan } from '@/types';

type SessionState = {
  anonymousId: string | null;
  ownerUserId: string | null;
  activeProjectId: string | null;
  project: InterviewProject | null;
  plan: PreparationPlan | null;
  setAnonymousId: (id: string) => void;
  clearAnonymousId: () => void;
  setOwnerUserId: (id: string) => void;
  clearForIdentityChange: () => void;
  setProject: (project: InterviewProject, plan?: PreparationPlan | null) => void;
  setPlan: (plan: PreparationPlan) => void;
  clear: () => void;
};

export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      anonymousId: null,
      ownerUserId: null,
      activeProjectId: null,
      project: null,
      plan: null,
      setAnonymousId: (id) => set({ anonymousId: id }),
      clearAnonymousId: () => set({ anonymousId: null }),
      setOwnerUserId: (id) => set({ ownerUserId: id }),
      clearForIdentityChange: () => set({ anonymousId: null, ownerUserId: null, activeProjectId: null, project: null, plan: null }),
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
        ownerUserId: state.ownerUserId,
        activeProjectId: state.activeProjectId,
        project: state.project,
        plan: state.plan,
      }),
    },
  ),
);
