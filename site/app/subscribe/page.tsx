'use client';
// site/app/subscribe/page.tsx
// Multi-step signup — collects name, email, gender, location, goals
// Replaces the old single-field form that was returning 500 errors

import { useState, useRef, useEffect } from 'react';

const STEPS = ['name', 'contact', 'location', 'goals', 'done'] as const;

const GENDER_OPTIONS = [
  { value: 'male',       label: 'Male' },
  { value: 'female',     label: 'Female' },
  { value: 'non-binary', label: 'Non-binary' },
  { value: 'prefer-not', label: 'Prefer not to say' },
  { value: 'other',      label: 'Other' },
];

const COUNTRIES = [
  { code: 'AU', name: 'Australia' }, { code: 'NZ', name: 'New Zealand' },
  { code: 'GB', name: 'United Kingdom' }, { code: 'IE', name: 'Ireland' },
  { code: 'US', name: 'United States' }, { code: 'CA', name: 'Canada' },
  { code: 'IN', name: 'India' }, { code: 'SG', name: 'Singapore' },
  { code: 'JP', name: 'Japan' }, { code: 'DE', name: 'Germany' },
  { code: 'FR', name: 'France' }, { code: 'NL', name: 'Netherlands' },
  { code: 'AE', name: 'UAE' }, { code: 'ZA', name: 'South Africa' },
  { code: 'OTHER', name: 'Other' },
];

const GOALS_1M = [
  'Automate one task in my job',
  'Learn which AI tools are worth paying for',
  'Build my first AI-powered workflow',
  'Stay ahead of what my team is using',
  'Understand LLMs well enough to use them daily',
];

const GOALS_12M = [
  'Be the AI-literate person on my team',
  'Launch a side project using AI tools',
  'Save 10+ hours a week through automation',
  'Build a product or service powered by AI',
  'Move into an AI-adjacent role',
];

type FormData = {
  preferredName: string;
  email: string;
  gender: string;
  country: string;
  city: string;
  goal1Month: string;
  goal12Month: string;
};

export default function SubscribePage() {
  const [step, setStep]       = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');
  const [referralCode, setReferralCode] = useState('');
  const firstRef = useRef<HTMLInputElement | HTMLSelectElement | null>(null);

  const [form, setForm] = useState<FormData>({
    preferredName: '', email: '', gender: '',
    country: '', city: '', goal1Month: '', goal12Month: '',
  });

  // Pick up ?ref= from URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setReferralCode(params.get('ref') || '');
  }, []);

  useEffect(() => {
    setTimeout(() => (firstRef.current as HTMLElement | null)?.focus(), 100);
  }, [step]);

  const update = (field: keyof FormData, value: string) =>
    setForm(f => ({ ...f, [field]: value }));

  const canAdvance = () => {
    if (step === 0) return form.preferredName.trim().length >= 2;
    if (step === 1) return form.email.includes('@') && !!form.gender;
    if (step === 2) return !!form.country;
    if (step === 3) return form.goal1Month.trim().length >= 5;
    return true;
  };

  const handleNext = async () => {
    setError('');
    if (step < STEPS.length - 2) { setStep(s => s + 1); return; }
    setLoading(true);
    try {
      const resp = await fetch('/api/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, referralCode }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || 'Something went wrong');
      setStep(STEPS.length - 1);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const progress = (step / (STEPS.length - 1)) * 100;

  return (
    <main style={{
      minHeight: '100vh',
      background: 'linear-gradient(160deg, #060610 0%, #0a0a1a 50%, #060610 100%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px 16px',
      fontFamily: 'inherit',
    }}>
      {/* Logo */}
      <a href="/" style={{ marginBottom: '32px', textDecoration: 'none' }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '10px',
          color: 'rgba(255,255,255,0.5)', fontSize: '14px',
        }}>
          <div style={{
            width: '32px', height: '32px', borderRadius: '8px',
            background: 'rgba(0,230,255,0.1)', border: '1px solid rgba(0,230,255,0.25)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px',
          }}>⚡</div>
          Veltrix Collective
        </div>
      </a>

      {/* Card */}
      <div style={{
        width: '100%', maxWidth: '420px',
        background: 'linear-gradient(135deg, #0a0a12 0%, #0d0d1e 100%)',
        border: '1px solid rgba(0,230,255,0.12)',
        borderRadius: '20px',
        boxShadow: '0 0 80px rgba(0,230,255,0.06), 0 32px 80px rgba(0,0,0,0.7)',
        overflow: 'hidden',
      }}>
        {/* Progress */}
        <div style={{ height: '2px', background: 'rgba(255,255,255,0.05)' }}>
          <div style={{
            height: '100%', width: `${progress}%`,
            background: 'linear-gradient(90deg, #00e6ff, #0077ff)',
            transition: 'width 0.4s cubic-bezier(0.4,0,0.2,1)',
          }} />
        </div>

        <div style={{ padding: '36px 32px 32px' }}>

          {/* Step 0: Name */}
          {step === 0 && (
            <StepWrap icon="⚡" title="What should we call you?" sub="No surnames. Just what you like to be called.">
              <input
                ref={firstRef as React.RefObject<HTMLInputElement>}
                type="text" value={form.preferredName} autoComplete="given-name"
                onChange={e => update('preferredName', e.target.value)}
                onKeyDown={e => e.key === 'Enter' && canAdvance() && handleNext()}
                placeholder="e.g. Alex, Jamie, Priya..."
                style={inputSt}
              />
            </StepWrap>
          )}

          {/* Step 1: Email + Gender */}
          {step === 1 && (
            <StepWrap icon="✉️" title={`Good to meet you, ${form.preferredName}.`} sub="Your email and how you identify — helps us personalise.">
              <input
                ref={firstRef as React.RefObject<HTMLInputElement>}
                type="email" value={form.email} autoComplete="email"
                onChange={e => update('email', e.target.value)}
                onKeyDown={e => e.key === 'Enter' && canAdvance() && handleNext()}
                placeholder="you@email.com"
                style={{ ...inputSt, marginBottom: '12px' }}
              />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                {GENDER_OPTIONS.map(opt => (
                  <button key={opt.value} type="button" onClick={() => update('gender', opt.value)}
                    style={{ ...chipSt, ...(form.gender === opt.value ? chipActiveSt : {}) }}>
                    {opt.label}
                  </button>
                ))}
              </div>
            </StepWrap>
          )}

          {/* Step 2: Location */}
          {step === 2 && (
            <StepWrap icon="🌏" title="Where are you based?" sub="We send the newsletter at 5am your time — so this genuinely matters.">
              <select
                ref={firstRef as React.RefObject<HTMLSelectElement>}
                value={form.country} onChange={e => update('country', e.target.value)}
                style={{ ...inputSt, marginBottom: '10px' }}>
                <option value="">Select your country...</option>
                {COUNTRIES.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
              </select>
              <input
                type="text" value={form.city} placeholder="City (optional)"
                onChange={e => update('city', e.target.value)}
                style={inputSt}
              />
            </StepWrap>
          )}

          {/* Step 3: Goals */}
          {step === 3 && (
            <StepWrap icon="🎯" title="What are you here to do?" sub="Veltix checks in on this. It helps us send what matters to you.">
              <Label>In the next month...</Label>
              <textarea
                ref={firstRef as React.RefObject<HTMLTextAreaElement> as unknown as React.RefObject<HTMLInputElement>}
                value={form.goal1Month} rows={2}
                onChange={e => update('goal1Month', e.target.value)}
                placeholder="e.g. Automate one task at work with AI"
                style={{ ...inputSt, resize: 'none', marginBottom: '6px' }}
              />
              <Chips items={GOALS_1M} onSelect={v => update('goal1Month', v)} />

              <Label style={{ marginTop: '14px' }}>In 12 months...</Label>
              <textarea
                value={form.goal12Month} rows={2}
                onChange={e => update('goal12Month', e.target.value)}
                placeholder="e.g. Be the AI-literate person on my team"
                style={{ ...inputSt, resize: 'none', marginBottom: '6px' }}
              />
              <Chips items={GOALS_12M} onSelect={v => update('goal12Month', v)} />
            </StepWrap>
          )}

          {/* Step 4: Done */}
          {step === STEPS.length - 1 && (
            <div style={{ textAlign: 'center', padding: '8px 0' }}>
              <div style={{
                width: '60px', height: '60px', margin: '0 auto 20px',
                background: 'rgba(0,230,255,0.08)', border: '1px solid rgba(0,230,255,0.25)',
                borderRadius: '18px', display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '26px',
              }}>⚡</div>
              <h2 style={{ fontSize: '22px', fontWeight: 700, color: '#fff', marginBottom: '10px', letterSpacing: '-0.02em' }}>
                You&apos;re in, {form.preferredName}.
              </h2>
              <p style={{ color: 'rgba(255,255,255,0.45)', fontSize: '14px', lineHeight: 1.6, marginBottom: '24px' }}>
                Your first briefing hits at{' '}
                <span style={{ color: '#00e6ff', fontWeight: 600 }}>5am your time</span> — curated AI news, tool rankings, and what actually matters. No noise.
              </p>
              <div style={{ ...cardSt, marginBottom: '20px' }}>
                <p style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Refer friends, get rewards</p>
                <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)', lineHeight: 1.5 }}>
                  Refer 10 paying subscribers in a month → that month is free for you.
                </p>
              </div>
              <a href="/" style={primaryBtnSt as React.CSSProperties}>
                Start exploring →
              </a>
            </div>
          )}

          {/* Error */}
          {error && (
            <p style={{ color: '#ff5555', fontSize: '13px', marginTop: '12px', textAlign: 'center' }}>{error}</p>
          )}

          {/* Nav */}
          {step < STEPS.length - 1 && (
            <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              {step > 0
                ? <button onClick={() => setStep(s => s - 1)} style={backBtnSt}>← Back</button>
                : <div />}
              <button
                onClick={handleNext}
                disabled={!canAdvance() || loading}
                style={{
                  ...primaryBtnSt as React.CSSProperties,
                  opacity: canAdvance() && !loading ? 1 : 0.35,
                  cursor: canAdvance() && !loading ? 'pointer' : 'not-allowed',
                  minWidth: '130px',
                }}>
                {loading ? 'Saving...' : step === STEPS.length - 2 ? 'Join free →' : 'Continue →'}
              </button>
            </div>
          )}

          {/* Dots */}
          {step < STEPS.length - 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '6px', marginTop: '20px' }}>
              {STEPS.slice(0, -1).map((_, i) => (
                <div key={i} style={{
                  width: i === step ? '20px' : '6px', height: '6px', borderRadius: '3px',
                  background: i <= step ? '#00e6ff' : 'rgba(255,255,255,0.1)',
                  transition: 'all 0.3s ease',
                }} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <p style={{ color: 'rgba(255,255,255,0.2)', fontSize: '12px', marginTop: '24px' }}>
        ✓ Free forever · ✓ No spam · ✓ Unsubscribe any time
      </p>
    </main>
  );
}

// Sub-components
function StepWrap({ icon, title, sub, children }: { icon: string; title: string; sub: string; children: React.ReactNode }) {
  return (
    <div>
      <div style={{
        width: '42px', height: '42px', marginBottom: '18px',
        background: 'rgba(0,230,255,0.07)', border: '1px solid rgba(0,230,255,0.18)',
        borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px',
      }}>{icon}</div>
      <h1 style={{ fontSize: '20px', fontWeight: 700, color: '#fff', marginBottom: '6px', letterSpacing: '-0.02em', lineHeight: 1.3 }}>{title}</h1>
      <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px', marginBottom: '22px', lineHeight: 1.5 }}>{sub}</p>
      {children}
    </div>
  );
}

function Label({ children, style = {} }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <p style={{ fontSize: '11px', color: 'rgba(255,255,255,0.3)', marginBottom: '7px', letterSpacing: '0.06em', textTransform: 'uppercase', ...style }}>
      {children}
    </p>
  );
}

function Chips({ items, onSelect }: { items: string[]; onSelect: (v: string) => void }) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
      {items.map(item => (
        <button key={item} type="button" onClick={() => onSelect(item)} style={suggSt}>{item}</button>
      ))}
    </div>
  );
}

// Styles
const inputSt: React.CSSProperties = {
  width: '100%', boxSizing: 'border-box',
  background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.09)',
  borderRadius: '10px', padding: '12px 14px', color: '#fff', fontSize: '15px',
  outline: 'none', fontFamily: 'inherit', display: 'block',
  transition: 'border-color 0.2s',
};

const chipSt: React.CSSProperties = {
  background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.09)',
  borderRadius: '8px', padding: '9px 12px', color: 'rgba(255,255,255,0.55)',
  cursor: 'pointer', fontSize: '13px', fontFamily: 'inherit', transition: 'all 0.2s',
};

const chipActiveSt: React.CSSProperties = {
  background: 'rgba(0,230,255,0.09)', border: '1px solid rgba(0,230,255,0.4)', color: '#00e6ff',
};

const suggSt: React.CSSProperties = {
  background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)',
  borderRadius: '20px', padding: '5px 10px', color: 'rgba(255,255,255,0.35)',
  cursor: 'pointer', fontSize: '11px', fontFamily: 'inherit', transition: 'all 0.2s',
};

const primaryBtnSt = {
  display: 'inline-block',
  background: 'linear-gradient(135deg, #00e6ff 0%, #0077ff 100%)',
  border: 'none', borderRadius: '10px', padding: '13px 28px',
  color: '#000', fontWeight: 700, fontSize: '14px', letterSpacing: '-0.01em',
  cursor: 'pointer', fontFamily: 'inherit', textDecoration: 'none',
  transition: 'opacity 0.2s',
};

const backBtnSt: React.CSSProperties = {
  background: 'none', border: 'none', color: 'rgba(255,255,255,0.3)',
  fontSize: '14px', cursor: 'pointer', padding: '8px', fontFamily: 'inherit',
};

const cardSt: React.CSSProperties = {
  background: 'rgba(0,230,255,0.04)', border: '1px solid rgba(0,230,255,0.12)',
  borderRadius: '12px', padding: '14px 16px', textAlign: 'left',
};
