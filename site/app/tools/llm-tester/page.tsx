'use client';
import { useState } from 'react';
import { ArrowRight, ThumbsUp, Zap, Copy, Check } from 'lucide-react';
import Link from 'next/link';

type ModelResult = { model: string; provider: string; response: string; latency_ms: number; };

const MODELS = [
  { id: 'claude-3-5-haiku-20241022', label: 'Claude 3.5 Haiku', provider: 'Anthropic' },
  { id: 'gpt-4o-mini',               label: 'GPT-4o Mini',       provider: 'OpenAI' },
  { id: 'gpt-4o',                    label: 'GPT-4o',            provider: 'OpenAI' },
];

export default function LLMTesterPage() {
  const [prompt, setPrompt] = useState('');
  const [results, setResults] = useState<ModelResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [votes, setVotes] = useState<Record<string, number>>({});
  const [copied, setCopied] = useState<string | null>(null);

  const handleTest = async () => {
    if (!prompt.trim()) return;
    setLoading(true); setError(''); setResults([]); setVotes({});
    try {
      const res = await fetch('/api/tools/llm-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();
      if (res.status === 429) { setError('Daily limit reached. Upgrade to Insider Access for unlimited tests.'); return; }
      if (!res.ok) { setError(data.error || 'Something went wrong.'); return; }
      setResults(data.results || []);
    } catch { setError('Network error. Please try again.'); }
    finally { setLoading(false); }
  };

  const handleCopy = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(id); setTimeout(() => setCopied(null), 2000);
  };

  const handleVote = (model: string) => setVotes(prev => ({ ...prev, [model]: (prev[model] || 0) + 1 }));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 badge-accent text-xs mb-4">
          <Zap size={12} /> Veltrix Tool
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-3">LLM Prompt Tester</h1>
        <p className="text-secondary max-w-xl mx-auto">Paste any prompt. Get responses from 3 different LLMs side by side. See which one wins for your use case.</p>
      </div>

      {/* Models shown */}
      <div className="flex justify-center gap-3 mb-8">
        {MODELS.map(m => (
          <div key={m.id} className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-2 border border-border">
            <span className="w-2 h-2 rounded-full bg-accent" />
            <span className="text-xs text-secondary">{m.label}</span>
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="max-w-3xl mx-auto mb-8">
        <label className="text-xs font-medium text-secondary mb-1.5 block">Your prompt</label>
        <textarea value={prompt} onChange={e => setPrompt(e.target.value)}
          placeholder="Write a cold email subject line for a SaaS product targeting small business owners..."
          className="input min-h-[120px] resize-y" />
        <div className="flex justify-between items-center mt-3">
          <span className="text-xs text-muted">3 free tests per day · <Link href="/free" className="text-accent hover:underline">Unlimited with Insider Access</Link></span>
          <button onClick={handleTest} disabled={loading || !prompt.trim()} className="btn-primary">
            {loading ? 'Testing...' : <>Test across models <ArrowRight size={16} /></>}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && <div className="max-w-3xl mx-auto p-4 rounded-xl bg-danger/10 border border-danger/20 text-danger text-sm mb-6">{error}</div>}

      {/* Loading */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {MODELS.map(m => (
            <div key={m.id} className="card">
              <div className="h-4 bg-surface-2 rounded animate-pulse mb-3 w-24" />
              <div className="space-y-2">{[...Array(6)].map((_, i) => <div key={i} className="h-3 bg-surface-2 rounded animate-pulse" style={{ width: `${70 + Math.random() * 30}%` }} />)}</div>
            </div>
          ))}
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {results.map((r) => (
              <div key={r.model} className="card flex flex-col">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-primary text-sm">{r.model}</h3>
                    <span className="text-[11px] text-muted">{r.provider} · {r.latency_ms}ms</span>
                  </div>
                  <button onClick={() => handleCopy(r.response, r.model)} className="p-1.5 rounded text-muted hover:text-primary hover:bg-surface-2 transition-colors">
                    {copied === r.model ? <Check size={14} className="text-success" /> : <Copy size={14} />}
                  </button>
                </div>
                <div className="flex-1 text-sm text-secondary leading-relaxed whitespace-pre-wrap bg-surface-2 rounded-lg p-3 text-xs font-mono">
                  {r.response}
                </div>
                <button onClick={() => handleVote(r.model)}
                  className={`mt-3 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-medium transition-all duration-200 border ${(votes[r.model] || 0) > 0 ? 'border-accent/30 bg-accent/10 text-accent' : 'border-border bg-surface-2 text-secondary hover:border-border-bright'}`}>
                  <ThumbsUp size={12} /> Best response {(votes[r.model] || 0) > 0 && '✓'}
                </button>
              </div>
            ))}
          </div>
          <div className="text-center mt-8">
            <p className="text-xs text-muted mb-3">Want to test longer prompts or more models?</p>
            <Link href="/free" className="btn-primary text-sm">Insider Access — unlimited testing →</Link>
          </div>
        </div>
      )}
    </div>
  );
}
