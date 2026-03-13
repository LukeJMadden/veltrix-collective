'use client';
import { useState } from 'react';
import { ArrowRight, CheckCircle, Zap } from 'lucide-react';
import Link from 'next/link';

export default function SubscribePage() {
  const [email, setEmail] = useState('');
  const [goal, setGoal] = useState('');
  const [referral, setReferral] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setStatus('loading');
    try {
      const res = await fetch('/api/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, goal, referral_code: referral }),
      });
      const data = await res.json();
      if (res.ok) { setStatus('success'); setMessage(data.message); }
      else { setStatus('error'); setMessage(data.error || 'Something went wrong.'); }
    } catch { setStatus('error'); setMessage('Network error. Please try again.'); }
  };

  if (status === 'success') {
    return (
      <div className="max-w-lg mx-auto px-4 py-24 text-center">
        <div className="w-16 h-16 rounded-2xl bg-success/10 border border-success/30 flex items-center justify-center mx-auto mb-6">
          <CheckCircle size={28} className="text-success" />
        </div>
        <h1 className="text-2xl font-bold mb-3">You&apos;re in.</h1>
        <p className="text-secondary mb-6">{message || "Check your inbox — your first email from Veltix is on its way."}</p>
        <div className="flex flex-col gap-3">
          <Link href="/" className="btn-primary">Explore Veltrix <ArrowRight size={16} /></Link>
          <Link href="/free" className="btn-secondary">Upgrade to Insider Access</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-16">
      <div className="text-center mb-10">
        <div className="w-14 h-14 rounded-2xl bg-accent/10 border border-accent/30 flex items-center justify-center mx-auto mb-4">
          <Zap size={24} className="text-accent" />
        </div>
        <h1 className="text-3xl font-bold mb-2">Stay in the loop</h1>
        <p className="text-secondary">Weekly AI news, tool rankings, and Veltrix picks — straight to your inbox. Free, forever.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-xs font-medium text-secondary mb-1.5 block">Email address</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" className="input" required />
        </div>
        <div>
          <label className="text-xs font-medium text-secondary mb-1.5 block">What&apos;s your main goal with AI? <span className="text-muted">(optional)</span></label>
          <input type="text" value={goal} onChange={e => setGoal(e.target.value)} placeholder="e.g. build tools, save time at work, learn..." className="input" />
          <p className="text-[11px] text-muted mt-1">Veltix will check in on this. It helps us personalise what we send you.</p>
        </div>
        <div>
          <label className="text-xs font-medium text-secondary mb-1.5 block">Referral code <span className="text-muted">(optional)</span></label>
          <input type="text" value={referral} onChange={e => setReferral(e.target.value)} placeholder="If someone referred you" className="input" />
        </div>

        {status === 'error' && <p className="text-danger text-sm">{message}</p>}

        <button type="submit" disabled={status === 'loading'} className="btn-primary w-full py-3 text-base justify-center">
          {status === 'loading' ? 'Subscribing...' : <>Subscribe Free <ArrowRight size={16} /></>}
        </button>
      </form>

      <div className="mt-6 flex flex-wrap justify-center gap-4 text-xs text-muted">
        <span>✓ Weekly digest, no spam</span>
        <span>✓ Unsubscribe any time</span>
        <span>✓ Goal check-ins from Veltix</span>
      </div>

      <div className="mt-8 p-4 rounded-xl border border-border bg-surface text-center">
        <p className="text-xs text-secondary mb-2">Want the full playbooks?</p>
        <Link href="/free" className="text-accent text-sm font-medium hover:underline">Insider Access — $9.99 →</Link>
      </div>
    </div>
  );
}
