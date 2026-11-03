import { useEffect, useState, type FormEvent } from 'react';
import {
  SignInButton,
  SignUpButton,
  SignedIn,
  SignedOut,
  UserButton,
  useAuth,
} from '@clerk/clerk-react';
import { getCurrentUser, migrateAnonymousSession, quickStart } from '@/services/projects';
import { useSessionStore } from '@/stores/sessionStore';
import type { PreparationPlan } from '@/types';

export default function App() {
  return (
    <>
      <SignedOut><SignedOutLanding /></SignedOut>
      <SignedIn><AuthenticatedApp /></SignedIn>
    </>
  );
}

function SignedOutLanding() {
  return (
    <main className="landing auth-landing">
      <nav className="topbar" aria-label="Main navigation">
        <a className="brand" href="/" aria-label="Interview Shala home"><span className="brand-mark">i.</span> interview shala</a>
        <div className="auth-actions">
          <SignInButton mode="modal"><button className="text-button" type="button">Sign in</button></SignInButton>
          <SignUpButton mode="modal"><button className="auth-primary-button" type="button">Create account</button></SignUpButton>
        </div>
      </nav>
      <section className="hero auth-hero">
        <div className="hero-copy">
          <p className="eyebrow"><span className="eyebrow-dot" /> PREPARE WITH PURPOSE</p>
          <h1>Walk into your next interview <em>ready.</em></h1>
          <p className="hero-description">A voice-first preparation companion that remembers what you know, finds the gaps, and helps you improve. Then face a realistic interview without hints.</p>
          <div className="trust-row"><span>✳</span> Your preparation, saved to your account.</div>
        </div>
        <section className="auth-card" aria-labelledby="auth-heading">
          <p className="eyebrow">GET STARTED</p>
          <h2 id="auth-heading">Build your preparation history.</h2>
          <p>Sign in to create a private candidate profile and keep your preparation, sessions and progress together.</p>
          <SignUpButton mode="modal"><button className="primary-button" type="button">Create your account <span aria-hidden>↗</span></button></SignUpButton>
          <SignInButton mode="modal"><button className="auth-secondary-button" type="button">I already have an account</button></SignInButton>
        </section>
      </section>
      <section className="feature-strip" aria-label="How it works">
        <article><span className="feature-number">01</span><div><h3>One persistent profile</h3><p>Your sessions and preparation history stay connected to your account.</p></div></article>
        <article><span className="feature-number">02</span><div><h3>Practice and interview</h3><p>Work with an adaptive coach, then test yourself under realistic conditions.</p></div></article>
        <article><span className="feature-number">03</span><div><h3>Evidence over guesswork</h3><p>Track real attempts, strengths, recurring mistakes and improvement.</p></div></article>
      </section>
      <footer className="footer"><span>interview shala</span><span>Thoughtful preparation. Better interviews.</span></footer>
    </main>
  );
}

function AuthenticatedApp() {
  const { getToken, isLoaded, userId } = useAuth();
  const anonymousId = useSessionStore((state) => state.anonymousId);
  const clearAnonymousId = useSessionStore((state) => state.clearAnonymousId);
  const setOwnerUserId = useSessionStore((state) => state.setOwnerUserId);
  const clearForIdentityChange = useSessionStore((state) => state.clearForIdentityChange);
  const [identityReady, setIdentityReady] = useState(false);
  const [identityError, setIdentityError] = useState('');
  const [migrationNotice, setMigrationNotice] = useState('');
  const project = useSessionStore((state) => state.project);
  const plan = useSessionStore((state) => state.plan);
  const setProject = useSessionStore((state) => state.setProject);
  const [company, setCompany] = useState('');
  const [role, setRole] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [interviewDate, setInterviewDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    async function initializeIdentity() {
      try {
        const token = await getToken();
        if (!token) throw new Error('Clerk did not provide a session token.');
        const profile = await getCurrentUser(token);
        const storedOwnerId = useSessionStore.getState().ownerUserId;
        const storedProject = useSessionStore.getState().project;

        if (storedOwnerId && storedOwnerId !== profile.id) {
          clearForIdentityChange();
        } else if (!storedOwnerId && storedProject && !anonymousId) {
          // Older local state without a verifiable owner must never be shown
          // to a different signed-in account.
          clearForIdentityChange();
        }
        setOwnerUserId(profile.id);

        if (anonymousId && (!storedOwnerId || storedOwnerId === profile.id)) {
          try {
            await migrateAnonymousSession(anonymousId, token);
            clearAnonymousId();
          } catch {
            // Do not display browser-cached preparation whose ownership could
            // not be established for the signed-in candidate.
            if (active) {
              setMigrationNotice('An older anonymous preparation could not be securely linked to this account. New preparation will be saved to your account.');
            }
            useSessionStore.getState().clear();
            clearAnonymousId();
          }
        }
      } catch (cause) {
        if (active) {
          setIdentityError(cause instanceof Error ? cause.message : 'Could not initialize your account.');
        }
      } finally {
        if (active) setIdentityReady(true);
      }
    }

    if (isLoaded && userId) void initializeIdentity();
    return () => { active = false; };
  }, [anonymousId, clearAnonymousId, clearForIdentityChange, getToken, isLoaded, setOwnerUserId, userId]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      const token = await getToken();
      if (!token) throw new Error('Your sign-in session expired. Please sign in again.');
      const result = await quickStart({
        company: company.trim(),
        role: role.trim(),
        ...(jobDescription.trim() ? { jobDescription: jobDescription.trim() } : {}),
        ...(interviewDate ? { interviewDate } : {}),
      }, null, token);
      setProject(result.project, result.plan);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  function startOver() {
    useSessionStore.getState().clear();
  }

  if (!isLoaded || !identityReady) {
    return <main className="auth-loading"><span className="brand-mark">i.</span><p>Securing your preparation space…</p></main>;
  }

  if (identityError) {
    return <main className="auth-loading"><h1>We couldn't verify your account.</h1><p>{identityError}</p><p>Check the Clerk and API configuration, then reload.</p></main>;
  }

  if (project && plan) {
    return <PreparationDashboard company={project.company} role={project.role} plan={plan} onStartOver={startOver} />;
  }

  return (
    <main className="landing">
      <nav className="topbar" aria-label="Main navigation">
        <a className="brand" href="/" aria-label="Interview Shala home"><span className="brand-mark">i.</span> interview shala</a>
        <div className="authenticated-nav"><span className="topbar-note">Your preparation space</span><UserButton /></div>
      </nav>
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow"><span className="eyebrow-dot" /> YOUR NEXT INTERVIEW, WITH A PLAN</p>
          <h1>Walk into your next interview <em>ready.</em></h1>
          <p className="hero-description">Prepare for the company, practise the right rounds, and understand what to improve — one focused step at a time.</p>
          <div className="trust-row"><span>✳</span> Your preparation is saved to your account.</div>
        </div>
        <form className="quickstart-card" onSubmit={handleSubmit}>
          <div className="card-heading"><div><p className="eyebrow">QUICK START</p><h2>Build your preparation plan</h2></div><span className="step-count">01 / 01</span></div>
          <label htmlFor="company">Company</label>
          <input id="company" value={company} onChange={(event) => setCompany(event.target.value)} placeholder="e.g. Google, HL Mando, a startup" required maxLength={255} />
          <label htmlFor="role">Role you're interviewing for</label>
          <input id="role" value={role} onChange={(event) => setRole(event.target.value)} placeholder="e.g. AI Engineer Intern" required maxLength={255} />
          <label htmlFor="date">Interview date <span className="optional">Optional</span></label>
          <input id="date" type="date" value={interviewDate} onChange={(event) => setInterviewDate(event.target.value)} />
          <label htmlFor="jd">Job description <span className="optional">Optional</span></label>
          <textarea id="jd" value={jobDescription} onChange={(event) => setJobDescription(event.target.value)} placeholder="Paste the job description to make your plan more relevant..." rows={4} />
          {error && <p className="error-message" role="alert">{error}</p>}
          <button className="primary-button" type="submit" disabled={loading}>{loading ? 'Building your plan…' : 'Build my preparation plan'} <span aria-hidden>↗</span></button>
          {migrationNotice && <p className="migration-notice" role="status">{migrationNotice}</p>}
          <p className="privacy-note">Your preparation is saved to your authenticated account.</p>
        </form>
      </section>
      <section className="feature-strip" aria-label="How it works">
        <article><span className="feature-number">01</span><div><h3>Know what to prepare</h3><p>A focused plan based on your role and company.</p></div></article>
        <article><span className="feature-number">02</span><div><h3>Practise with purpose</h3><p>Work through technical, project and people rounds.</p></div></article>
        <article><span className="feature-number">03</span><div><h3>Improve with evidence</h3><p>Build confidence by working on real gaps.</p></div></article>
      </section>
      <footer className="footer"><span>interview shala</span><span>Thoughtful preparation. Better interviews.</span></footer>
    </main>
  );
}

function PreparationDashboard({ company, role, plan, onStartOver }: { company: string; role: string; plan: PreparationPlan; onStartOver: () => void }) {
  return (
    <main className="dashboard">
      <nav className="topbar"><a className="brand" href="/"><span className="brand-mark">i.</span> interview shala</a><div className="authenticated-nav"><button className="text-button" onClick={onStartOver}>New preparation plan</button><UserButton /></div></nav>
      <section className="dashboard-heading"><p className="eyebrow">YOUR PREPARATION SPACE</p><h1>{role} <span>at</span> {company}</h1><p>{plan.summary}</p></section>
      <section className="dashboard-grid">
        <div className="plan-main">
          <div className="section-heading"><div><p className="eyebrow">YOUR ROADMAP</p><h2>Interview rounds</h2></div><span className="count-pill">{plan.rounds.length} rounds</span></div>
          <div className="round-list">
            {plan.rounds.map((round, index) => <article className="round-card" key={round.id}>
              <span className="round-index">{String(index + 1).padStart(2, '0')}</span>
              <div className="round-content"><h3>{round.name}</h3><p>{round.description}</p><div className="topic-list">{round.topics.map((topic) => <span key={topic}>{topic}</span>)}</div></div>
              <span className="question-count">{round.questionCount} Qs</span>
            </article>)}
          </div>
        </div>
        <aside className="tasks-panel"><p className="eyebrow">START HERE</p><h2>Today's focus</h2><p className="panel-description">A few high-value steps to get moving.</p>
          <div className="task-list">
            {(plan.todayTasks?.length ? plan.todayTasks : plan.tasks).map((task) => <label className="task-item" key={task.id}><input type="checkbox" /><span><strong>{task.title}</strong><small>{task.estimatedMinutes ? task.estimatedMinutes + ' min' : 'Preparation task'}</small></span></label>)}
          </div>
          <div className="honesty-note"><span>✳</span><p>Voice practice and evidence-based feedback are not connected yet. This plan is generated from your role and the information you provided.</p></div>
        </aside>
      </section>
    </main>
  );
}
