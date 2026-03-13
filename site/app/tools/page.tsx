'use client';
import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { supabase, type Tool } from '@/lib/supabase';
import { getCategoryLabel, formatRelativeTime } from '@/lib/utils';
import { ArrowRight, ThumbsUp, Filter, Search, ExternalLink } from 'lucide-react';

const CATEGORIES = ['all', 'claude-tools', 'llm', 'coding', 'image', 'video', 'writing', 'productivity', 'voice', 'audio'];

export default function ToolsPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [filtered, setFiltered] = useState<Tool[]>([]);
  const [category, setCategory] = useState('all');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [votingId, setVotingId] = useState<number | null>(null);

  const fetchTools = useCallback(async () => {
    const { data } = await supabase.from('tools').select('*').order('score', { ascending: false });
    if (data) { setTools(data); setFiltered(data); }
    setLoading(false);
  }, []);

  useEffect(() => { fetchTools(); const interval = setInterval(fetchTools, 60000); return () => clearInterval(interval); }, [fetchTools]);

  useEffect(() => {
    let result = tools;
    if (category !== 'all') result = result.filter(t => t.category === category);
    if (search) result = result.filter(t => t.name.toLowerCase().includes(search.toLowerCase()) || t.description?.toLowerCase().includes(search.toLowerCase()));
    setFiltered(result);
  }, [tools, category, search]);

  const handleVote = async (toolId: number) => {
    setVotingId(toolId);
    try {
      const response = await fetch('/api/tools/vote', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ toolId }) });
      if (response.ok) { await fetchTools(); }
    } finally { setVotingId(null); }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-2 mb-2">
          <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse-slow" />
          <span className="text-xs font-semibold text-accent uppercase tracking-wider">Live Leaderboard</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-2">AI Tools Rankings</h1>
        <p className="text-secondary">Ranked by community votes + Veltrix score. Updated every hour.</p>
      </div>

      {/* Search + Filter */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input type="text" placeholder="Search tools..." value={search} onChange={e => setSearch(e.target.value)} className="input pl-9" />
        </div>
        <div className="flex items-center gap-1 overflow-x-auto pb-1 scrollbar-none">
          <Filter size={14} className="text-muted flex-shrink-0" />
          {CATEGORIES.map(cat => (
            <button key={cat} onClick={() => setCategory(cat)}
              className={`flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${category === cat ? 'bg-accent text-background' : 'bg-surface-2 text-secondary hover:text-primary border border-border'}`}>
              {cat === 'all' ? 'All' : getCategoryLabel(cat)}
            </button>
          ))}
        </div>
      </div>

      {/* Tool List */}
      {loading ? (
        <div className="space-y-2">{[...Array(10)].map((_, i) => <div key={i} className="h-16 bg-surface rounded-xl border border-border animate-pulse" />)}</div>
      ) : (
        <div className="space-y-2">
          {filtered.map((tool, i) => (
            <div key={tool.id} className="flex items-center gap-4 p-4 bg-surface rounded-xl border border-border hover:border-border-bright transition-all duration-200 group">
              <span className="text-xl font-bold text-muted w-8 text-center tabular-nums flex-shrink-0">#{i + 1}</span>

              {/* Logo placeholder */}
              <div className="w-10 h-10 rounded-lg bg-surface-2 border border-border flex-shrink-0 flex items-center justify-center text-xs font-bold text-secondary">
                {tool.name.substring(0, 2).toUpperCase()}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <Link href={`/tools/${tool.slug}`} className="font-semibold text-primary hover:text-accent transition-colors">{tool.name}</Link>
                  {tool.is_veltrix_tool && <span className="badge-accent text-[10px]">Veltrix Pick 🔥</span>}
                  <span className="badge-muted text-[10px]">{getCategoryLabel(tool.category)}</span>
                  <span className="badge-muted text-[10px] hidden sm:inline-flex">{tool.pricing_model}</span>
                </div>
                {tool.description && <p className="text-xs text-secondary mt-0.5 truncate hidden sm:block">{tool.description}</p>}
              </div>

              <div className="flex items-center gap-3 flex-shrink-0">
                {/* Score bar */}
                <div className="hidden md:flex items-center gap-2">
                  <div className="w-20 h-1.5 bg-surface-2 rounded-full overflow-hidden">
                    <div className="h-full bg-accent rounded-full transition-all duration-500" style={{ width: `${tool.score}%` }} />
                  </div>
                  <span className="text-xs font-mono text-accent w-8 text-right">{Math.round(tool.score)}</span>
                </div>

                {/* Vote */}
                <button onClick={() => handleVote(tool.id)} disabled={votingId === tool.id}
                  className="flex items-center gap-1 px-2 py-1 rounded-lg bg-surface-2 border border-border hover:border-accent/30 hover:text-accent text-secondary text-xs transition-all duration-200 disabled:opacity-50">
                  <ThumbsUp size={12} />
                  <span>{tool.votes}</span>
                </button>

                {/* External link */}
                {(tool.affiliate_url || tool.url) && (
                  <a href={tool.affiliate_url || tool.url} target="_blank" rel="noopener noreferrer"
                    className="p-1.5 rounded-lg text-muted hover:text-accent hover:bg-surface-2 transition-all duration-200">
                    <ExternalLink size={14} />
                  </a>
                )}
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="text-center py-16 text-secondary">
              <p className="text-lg font-medium mb-2">No tools found</p>
              <p className="text-sm">Try a different search or category filter.</p>
            </div>
          )}
        </div>
      )}

      {/* CTA */}
      <div className="mt-12 p-6 rounded-xl border border-accent/20 bg-surface text-center">
        <p className="text-sm text-secondary mb-3">Want the tools Veltrix uses but doesn&apos;t publish publicly?</p>
        <Link href="/free" className="btn-primary text-sm">Unlock Insider Guides → <ArrowRight size={14} /></Link>
      </div>
    </div>
  );
}
