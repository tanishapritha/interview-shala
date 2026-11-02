import { useState, type FormEvent } from 'react';
import { createAnonymousSession, quickStart } from '@/services/projects';
import { useSessionStore } from '@/stores/sessionStore';
import type { PreparationPlan } from '@/types';

export default function App() {
  const anonymousId = useSessionStore((state) => state.anonymousId);
  const setAnonymousId = useSessionStore((state) => state.setAnonymousId);
  const project = useSessionStore((state) => state.project);
  const plan = useSessionStore((state) => state.plan);
  const setProject = useSessionStore((state) => state.setProject);
  const [company, setCompany] = useState('');
  const [role, setRole] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [interviewDate, setInterviewDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      let sessionId = anonymousId;
      if (!sessionId) {
        const session = await createAnonymousSession();
        sessionId = session.anonymousId;
        setAnonymousId(sessionId);
      }
      const result = await quickStart({
        company: company.trim(),
        role: role.trim(),
        ...(jobDescription.trim() ? { jobDescription: jobDescription.trim() } : {}),
        ...(interviewDate ? { interviewDate } : {}),
      }, sessionId);
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

  if (project && plan) {
    return <PreparationDashboard company={project.company} role={project.role} plan={plan} onStartOver={startOver} />;
  }

  return (
    <main className="landing">
      <nav className="topbar" aria-label="Main navigation">
        <a className="brand" href="/" aria-label="Interview Shala home"><span className="brand-mark">i.</span> interview shala</a>
        <span className="topbar-note">A calmer way to prepare.</span>
      </nav>
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow"><span className="eyebrow-dot" /> YOUR NEXT INTERVIEW, WITH A PLAN</p>
          <h1>Walk into your next interview <em>ready.</em></h1>
          <p className="hero-description">Prepare for the company, practise the right rounds, and understand what to improve — one focused step at a time.</p>
          <div className="trust-row"><span>✳</span> Start free · No account required</div>
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
          <p className="privacy-note">Your preparation is saved to this browser session. You can create an account later.</p>
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
      <nav className="topbar"><a className="brand" href="/"><span className="brand-mark">i.</span> interview shala</a><button className="text-button" onClick={onStartOver}>New preparation plan</button></nav>
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
