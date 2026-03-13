'use client';
import { useEffect, useState, useCallback } from 'react';
import { supabase, type NewsItem } from '@/lib/supabase';
import { formatRelativeTime } from '@/lib/utils';
import { ExternalLink, RefreshCw } from 'lucide-react';

const SOURCES = ['All', 'TechCrunch', 'The Verge', 'Anthropic', 'OpenAI', 'Hugging Face', 'VentureBeat'];

export default function NewsPage() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [source, setSource] = useState('All');
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchNews = useCallback(async () => {
    let query = supabase.from('news').select('*').order('published_at', { ascending: false }).limit(50);
    const { data } = await query;
    if (data) { setNews(data); setLastUpdated(new Date()); }
    setLoading(false);
  }, []);

  useEffect(() => { fetchNews(); const interval = setInterval(fetchNews, 60000 * 5); return () => clearInterval(interval); }, [fetchNews]);

  const filtered = source === 'All' ? news : news.filter(n => n.source_name?.toLowerCase().includes(source.toLowerCase()));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-2">
          <div className="live-dot" />
          <span className="text-xs font-semibold text-success uppercase tracking-wider ml-1">Live Feed</span>
          <span className="text-xs text-muted">— updated hourly by Veltix</span>
        </div>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold">AI News</h1>
            <p className="text-secondary mt-1">10+ sources. Filtered, summarised, and delivered in Veltix voice.</p>
          </div>
          <button onClick={fetchNews} className="btn-ghost text-xs">
            <RefreshCw size={12} /> Refresh
          </button>
        </div>
      </div>

      {/* Source filter */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-6 scrollbar-none">
        {SOURCES.map(s => (
          <button key={s} onClick={() => setSource(s)}
            className={`flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${source === s ? 'bg-accent text-background' : 'bg-surface-2 text-secondary hover:text-primary border border-border'}`}>
            {s}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[...Array(12)].map((_, i) => <div key={i} className="h-32 bg-surface rounded-xl border border-border animate-pulse" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((item) => (
            <a key={item.id} href={item.source_url} target="_blank" rel="noopener noreferrer"
              className="card-glow group flex flex-col gap-2 cursor-pointer">
              <div className="flex items-center justify-between">
                <span className="badge-muted text-[10px]">{item.source_name}</span>
                <span className="text-[11px] text-muted">{formatRelativeTime(item.published_at)}</span>
              </div>
              <h3 className="font-semibold text-primary group-hover:text-accent transition-colors leading-snug text-sm">
                {item.headline}
              </h3>
              <p className="text-xs text-secondary leading-relaxed flex-1">{item.summary}</p>
              <div className="flex items-center gap-1 text-xs text-accent opacity-0 group-hover:opacity-100 transition-opacity">
                Read source <ExternalLink size={10} />
              </div>
            </a>
          ))}
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="text-center py-16 text-secondary">
          <p className="text-lg font-medium mb-2">No news from this source yet</p>
          <p className="text-sm">Check back shortly — Veltix fetches new articles every hour.</p>
        </div>
      )}

      <div className="mt-8 text-center text-xs text-muted">
        Last updated: {lastUpdated.toLocaleTimeString()} · Auto-refreshes every 5 minutes
      </div>
    </div>
  );
}
