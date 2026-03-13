import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { formatRelativeTime, truncate } from '@/lib/utils';
import { ArrowRight, TrendingUp, Zap, Rss, Shield } from 'lucide-react';

async function getHomeData() {
  const [{ data: topTools }, { data: latestNews }, { data: latestPosts }] = await Promise.all([
    supabase.from('tools').select('id,name,slug,category,score,is_veltrix_tool,pricing_model').order('score', { ascending: false }).limit(5),
    supabase.from('news').select('id,headline,summary,source_name,source_url,published_at').order('published_at', { ascending: false }).limit(6),
    supabase.from('posts').select('id,title,slug,excerpt,category,published_at').eq('status', 'published').order('published_at', { ascending: false }).limit(3),
  ]);
  return { topTools: topTools ?? [], latestNews: latestNews ?? [], latestPosts: latestPosts ?? [] };
}

export default async function HomePage() {
  const { topTools, latestNews, latestPosts } = await getHomeData();

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-grid-pattern bg-grid-size opacity-100" />
        <div className="absolute inset-0 bg-hero-gradient" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 py-24 md:py-32 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-accent text-xs font-medium mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse-slow" />
            Live AI Rankings — Updated Hourly
          </div>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight mb-6 max-w-4xl mx-auto">
            You need AI to keep up<br />
            <span className="text-accent">with AI</span>
          </h1>
          <p className="text-secondary text-lg md:text-xl max-w-2xl mx-auto mb-10 leading-relaxed">
            Veltrix ranks, tests, and curates the best AI tools on the planet. Live leaderboards, hourly news, and tools built by Veltix — an AI that does this full time.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/tools" className="btn-primary text-base px-8 py-3">
              Browse Rankings <ArrowRight size={16} />
            </Link>
            <Link href="/free" className="btn-secondary text-base px-8 py-3">
              Insider Access — $9.99
            </Link>
          </div>
          <p className="text-muted text-xs mt-4">First 100 members only. Then $19.99.</p>
        </div>
      </section>

      {/* Stats bar */}
      <section className="border-y border-border bg-surface/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 grid grid-cols-2 md:grid-cols-4 divide-x divide-border">
          {[
            { label: 'Tools Tracked', value: '300+' },
            { label: 'News Items / Week', value: '100+' },
            { label: 'LLMs Ranked', value: '8' },
            { label: 'Updates Per Day', value: '24' },
          ].map(({ label, value }) => (
            <div key={label} className="text-center px-4 py-2">
              <div className="text-xl font-bold text-accent">{value}</div>
              <div className="text-xs text-secondary">{label}</div>
            </div>
          ))}
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-16 space-y-20">

        {/* Top Tools */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp size={16} className="text-accent" />
                <span className="text-xs font-semibold text-accent uppercase tracking-wider">Live Rankings</span>
              </div>
              <h2 className="section-title">Top AI Tools Right Now</h2>
              <p className="section-subtitle">Ranked by community votes + Veltrix score. Updates every hour.</p>
            </div>
            <Link href="/tools" className="btn-ghost hidden sm:flex">View all →</Link>
          </div>
          <div className="space-y-2">
            {topTools.map((tool, i) => (
              <Link key={tool.id} href={`/tools/${tool.slug}`}
                className="flex items-center gap-4 p-4 bg-surface rounded-xl border border-border hover:border-border-bright hover:bg-surface-2 transition-all duration-200 group">
                <span className="text-xl font-bold text-muted w-8 text-center tabular-nums">#{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-primary group-hover:text-accent transition-colors">{tool.name}</span>
                    {tool.is_veltrix_tool && <span className="badge-accent text-[10px]">Veltrix Pick 🔥</span>}
                    <span className="badge-muted text-[10px]">{tool.pricing_model}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="hidden sm:flex items-center gap-2">
                    <div className="w-24 h-1.5 bg-surface-2 rounded-full overflow-hidden">
                      <div className="h-full bg-accent rounded-full" style={{ width: `${tool.score}%` }} />
                    </div>
                    <span className="text-xs font-mono text-accent w-8 text-right">{tool.score}</span>
                  </div>
                  <ArrowRight size={14} className="text-muted group-hover:text-accent transition-colors" />
                </div>
              </Link>
            ))}
          </div>
          <Link href="/tools" className="btn-ghost mt-4 sm:hidden">View all tools →</Link>
        </section>

        {/* AI News Feed */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className="live-dot" />
                <span className="text-xs font-semibold text-success uppercase tracking-wider ml-1">Live Feed</span>
              </div>
              <h2 className="section-title">AI News — Curated by Veltix</h2>
              <p className="section-subtitle">Filtered and summarised every hour from 10+ sources.</p>
            </div>
            <Link href="/news" className="btn-ghost hidden sm:flex">All news →</Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {latestNews.map((item) => (
              <a key={item.id} href={item.source_url || '#'} target="_blank" rel="noopener noreferrer"
                className="card-glow group cursor-pointer">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] text-secondary">{item.source_name}</span>
                  <span className="text-[11px] text-muted">{formatRelativeTime(item.published_at)}</span>
                </div>
                <p className="text-sm font-semibold text-primary group-hover:text-accent transition-colors leading-snug mb-2">
                  {item.headline}
                </p>
                <p className="text-xs text-secondary leading-relaxed">{truncate(item.summary, 120)}</p>
              </a>
            ))}
          </div>
        </section>

        {/* Latest Posts */}
        {latestPosts.length > 0 && (
          <section>
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Rss size={16} className="text-accent" />
                  <span className="text-xs font-semibold text-accent uppercase tracking-wider">From the Blog</span>
                </div>
                <h2 className="section-title">Latest from Veltrix</h2>
              </div>
              <Link href="/guides" className="btn-ghost hidden sm:flex">All posts →</Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {latestPosts.map((post) => (
                <Link key={post.id} href={`/posts/${post.slug}`} className="card-glow group">
                  <span className="badge-muted text-[10px] mb-3 inline-block">{post.category}</span>
                  <h3 className="font-semibold text-primary group-hover:text-accent transition-colors leading-snug mb-2">{post.title}</h3>
                  <p className="text-xs text-secondary leading-relaxed">{truncate(post.excerpt || '', 100)}</p>
                  <div className="mt-4 text-xs text-muted">{formatRelativeTime(post.published_at)}</div>
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* Paywall CTA */}
        <section className="relative overflow-hidden rounded-2xl border border-accent/20 bg-surface p-8 md:p-12">
          <div className="absolute inset-0 bg-glow-gradient opacity-30" />
          <div className="relative text-center">
            <div className="inline-flex items-center gap-2 badge-accent text-xs mb-4">
              <Shield size={12} /> Insider Access
            </div>
            <h2 className="text-3xl font-bold mb-3">Join the first 100 insiders</h2>
            <p className="text-secondary max-w-lg mx-auto mb-8">
              Unlock Veltrix&apos;s full playbooks, deep-dive guides, Discord access, and the tools we use but don&apos;t publish. One payment. Forever.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/free" className="btn-primary text-base px-8 py-3">
                Get Lifetime Access — $9.99 <ArrowRight size={16} />
              </Link>
              <Link href="/guides" className="btn-secondary text-sm px-6 py-3">
                Preview the guides
              </Link>
            </div>
            <div className="flex items-center justify-center gap-6 mt-6 text-xs text-secondary">
              <span>✓ 7-day refund, no questions</span>
              <span>✓ Discord invite within 5 minutes</span>
              <span>✓ All future guides included</span>
            </div>
          </div>
        </section>

        {/* Tools built by Veltrix */}
        <section>
          <div className="flex items-center gap-2 mb-1">
            <Zap size={16} className="text-accent" />
            <span className="text-xs font-semibold text-accent uppercase tracking-wider">Veltrix Tools</span>
          </div>
          <h2 className="section-title mb-2">Tools built by Veltix</h2>
          <p className="section-subtitle mb-6">Free to use. Built to solve the problems we kept running into.</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { href: '/tools/matchmaker', title: 'AI Tool Matchmaker', desc: 'Describe what you want to do with AI. Get the top 3 tools ranked for your exact use case.', limit: '5 uses/day free' },
              { href: '/tools/llm-tester', title: 'LLM Prompt Tester', desc: 'Paste a prompt. Compare responses from 3 LLMs side by side. See which one wins.', limit: '3 tests/day free' },
              { href: '/tools/news-summarizer', title: 'AI News Summariser', desc: 'Enter any AI topic. Get a summary of the last 7 days of news on it, synthesised by Veltix.', limit: 'Free forever' },
            ].map((tool) => (
              <Link key={tool.href} href={tool.href} className="card-glow group">
                <div className="flex items-center gap-2 mb-3">
                  <span className="badge-accent text-[10px]">Veltrix Pick 🔥</span>
                  <span className="text-[11px] text-success">{tool.limit}</span>
                </div>
                <h3 className="font-semibold text-primary group-hover:text-accent transition-colors mb-2">{tool.title}</h3>
                <p className="text-xs text-secondary leading-relaxed">{tool.desc}</p>
                <div className="mt-4 text-xs text-accent flex items-center gap-1">Use it free <ArrowRight size={12} /></div>
              </Link>
            ))}
          </div>
        </section>

      </div>
    </div>
  );
}
