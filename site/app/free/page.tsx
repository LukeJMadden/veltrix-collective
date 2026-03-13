import Link from 'next/link';
import { ArrowRight, CheckCircle, Lock, Users, BookOpen, Zap, MessageCircle } from 'lucide-react';

const GUIDES = [
  'The Exact Automation Stack Veltrix Runs — Step by Step',
  'How to Build and Monetise a Claude Tool in 48 Hours',
  'The $9/month AI Business Stack That Makes $X,XXX',
  'Prompt Engineering Playbook: How Veltrix Writes Every Piece of Content',
  'The Veltrix Affiliate Strategy — Which Programs Pay and Which Don\'t',
];

const INCLUDED = [
  { icon: BookOpen, title: 'All insider guides', desc: 'Deep-dive playbooks on building, automating, and monetising with AI.' },
  { icon: Users, title: 'Discord community', desc: 'Invite arrives within 5 minutes of purchase. Real people, real builds.' },
  { icon: Zap, title: 'Unlimited tool usage', desc: 'Remove daily limits on all Veltrix tools. Unlimited matchmaker + LLM tester.' },
  { icon: MessageCircle, title: 'All future guides', desc: 'One payment, all future content included. No recurring charges.' },
];

export default function FreePage() {
  const lemonsqueezyUrl = process.env.NEXT_PUBLIC_LEMON_SQUEEZY_CHECKOUT_URL || '#';

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-16">
      {/* Header */}
      <div className="text-center mb-14">
        <div className="inline-flex items-center gap-2 badge-warning text-xs mb-4 px-3 py-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-warning animate-pulse-slow" />
          First 100 members — $9.99 lifetime
        </div>
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          Veltrix Insider Access
        </h1>
        <p className="text-secondary text-lg max-w-2xl mx-auto leading-relaxed">
          Join the first 100 insiders. Unlock Veltrix&apos;s full playbooks, deep-dive guides, Discord access, and unlimited tool usage. One payment. Forever.
        </p>
      </div>

      {/* Price */}
      <div className="text-center mb-10">
        <div className="inline-flex items-end gap-2 mb-2">
          <span className="text-5xl font-bold text-primary">$9.99</span>
          <span className="text-secondary text-lg mb-2">lifetime</span>
        </div>
        <p className="text-xs text-muted">First 100 members only. Price goes to $19.99 after.</p>
      </div>

      {/* CTA */}
      <div className="text-center mb-14">
        <a href={lemonsqueezyUrl} className="btn-primary text-base px-10 py-4 inline-flex shadow-glow">
          Get Lifetime Access — $9.99 <ArrowRight size={18} />
        </a>
        <div className="flex flex-wrap items-center justify-center gap-4 mt-4 text-xs text-secondary">
          <span className="flex items-center gap-1"><CheckCircle size={11} className="text-success" />7-day refund, no questions</span>
          <span className="flex items-center gap-1"><CheckCircle size={11} className="text-success" />Discord invite in 5 minutes</span>
          <span className="flex items-center gap-1"><CheckCircle size={11} className="text-success" />One payment, forever</span>
        </div>
      </div>

      {/* What's included */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-14">
        {INCLUDED.map(({ icon: Icon, title, desc }) => (
          <div key={title} className="card flex gap-4">
            <div className="w-10 h-10 rounded-xl bg-accent/10 border border-accent/20 flex items-center justify-center flex-shrink-0">
              <Icon size={18} className="text-accent" />
            </div>
            <div>
              <h3 className="font-semibold text-primary mb-1">{title}</h3>
              <p className="text-sm text-secondary">{desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Guide list */}
      <div className="mb-14">
        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
          <Lock size={18} className="text-accent" /> What&apos;s inside the vault
        </h2>
        <div className="space-y-3">
          {GUIDES.map((guide, i) => (
            <div key={i} className="flex items-start gap-3 p-4 bg-surface rounded-xl border border-border">
              <CheckCircle size={16} className="text-accent flex-shrink-0 mt-0.5" />
              <span className="text-sm text-primary">{guide}</span>
            </div>
          ))}
          <div className="flex items-start gap-3 p-4 bg-surface rounded-xl border border-border/50 border-dashed">
            <Zap size={16} className="text-muted flex-shrink-0 mt-0.5" />
            <span className="text-sm text-muted">+ all future guides, added automatically</span>
          </div>
        </div>
      </div>

      {/* Final CTA */}
      <div className="text-center p-10 rounded-2xl border border-accent/20 bg-surface relative overflow-hidden">
        <div className="absolute inset-0 bg-glow-gradient opacity-20" />
        <div className="relative">
          <h2 className="text-2xl font-bold mb-2">First 100 members only</h2>
          <p className="text-secondary text-sm mb-6">After 100 members, the price goes to $19.99. It won&apos;t drop again.</p>
          <a href={lemonsqueezyUrl} className="btn-primary text-base px-10 py-4 inline-flex shadow-glow">
            Get Lifetime Access — $9.99 <ArrowRight size={18} />
          </a>
        </div>
      </div>
    </div>
  );
}
