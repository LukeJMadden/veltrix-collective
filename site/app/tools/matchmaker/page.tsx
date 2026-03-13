'use client';
import { useState } from 'react';
import { ArrowRight, Search, Zap, ExternalLink } from 'lucide-react';
import Link from 'next/link';

type Recommendation = { name: string; url: string; reason: string; affiliate_url?: string; pricing: string; };

const EXAMPLE_QUERIES = ['Generate images for my Etsy shop', 'Write code without knowing how to code', 'Transcribe and summarise meetings automatically', 'Build a chatbot for my website', 'Create video content without filming'];

export default function MatchmakerPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [usesLeft, setUsesLeft] = useState<number | null>(null);

  const handleSearch = async (q?: string) => {
    const searchQuery = q || query;
    if (!searchQuery.trim()) return;
    setLoading(true); setError(''); setResults([]);
    try {
      const res = await fetch('/api/tools/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery }),
      });
      const data = await res.json();
      if (res.status === 429) { setError('Daily limit reached. Upgrade to Insider Access for unlimited searches.'); return; }
      if (!res.ok) { setError(data.error || 'Something went wrong.'); return; }
      setResults(data.recommendations || []);
      setUsesLeft(data.uses_left);
    } catch { setError('Network error. Please try again.'); }
    finally { setLoading(false); }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12">
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 badge-accent text-xs mb-4">
          <Zap size={12} /> Veltrix Tool
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-3">AI Tool Matchmaker</h1>
        <p className="text-secondary">Describe what you want to do with AI. Get the top 3 tools for your exact use case — ranked and explained.</p>
        {usesLeft !== null && <p className="text-xs text-muted mt-2">{usesLeft} free searches remaining today</p>}
      </div>

      {/* Input */}
      <div className="flex gap-2 mb-4">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" />
          <input type="text" value={query} onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="What do you want to do with AI?" className="input pl-10 py-3" />
        </div>
        <button onClick={() => handleSearch()} disabled={loading || !query.trim()} className="btn-primary px-5 py-3 flex-shrink-0">
          {loading ? '...' : <><ArrowRight size={16} /></>}
        </button>
      </div>

      {/* Example queries */}
      <div className="flex flex-wrap gap-2 mb-8">
        {EXAMPLE_QUERIES.map(q => (
          <button key={q} onClick={() => { setQuery(q); handleSearch(q); }}
            className="text-xs px-3 py-1.5 rounded-full bg-surface-2 border border-border text-secondary hover:text-primary hover:border-border-bright transition-all">
            {q}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-xl bg-danger/10 border border-danger/20 text-danger text-sm mb-6">
          {error}
          {error.includes('limit') && <Link href="/free" className="ml-2 underline">Upgrade →</Link>}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map(i => <div key={i} className="h-28 bg-surface rounded-xl border border-border animate-pulse" />)}
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <p className="text-xs text-secondary">Top 3 recommendations for &ldquo;{query}&rdquo;</p>
          {results.map((rec, i) => (
            <div key={i} className="card-glow">
              <div className="flex items-start justify-between gap-4 mb-3">
                <div className="flex items-center gap-3">
                  <span className="w-8 h-8 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center text-accent font-bold text-sm flex-shrink-0">
                    {i + 1}
                  </span>
                  <div>
                    <h3 className="font-semibold text-primary">{rec.name}</h3>
                    <span className="text-xs text-muted">{rec.pricing}</span>
                  </div>
                </div>
                <a href={rec.affiliate_url || rec.url} target="_blank" rel="noopener noreferrer"
                  className="btn-secondary text-xs px-3 py-1.5 flex-shrink-0 flex items-center gap-1">
                  Try it <ExternalLink size={11} />
                </a>
              </div>
              <p className="text-sm text-secondary leading-relaxed">{rec.reason}</p>
            </div>
          ))}
          <div className="text-center pt-4">
            <p className="text-xs text-muted mb-3">Want unlimited searches and the tools Veltrix actually uses?</p>
            <Link href="/free" className="btn-primary text-sm">Insider Access — $9.99 →</Link>
          </div>
        </div>
      )}
    </div>
  );
}
