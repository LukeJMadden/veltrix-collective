import { supabase } from '@/lib/supabase';
import Link from 'next/link';
import { Lock, ArrowRight, CheckCircle } from 'lucide-react';

async function getPosts() {
  const { data } = await supabase.from('posts').select('id,title,slug,excerpt,category,is_paywalled,published_at').eq('status', 'published').order('published_at', { ascending: false });
  return data ?? [];
}

const INSIDER_GUIDES = [
  { title: 'The Exact Automation Stack Veltrix Runs — Step by Step', desc: 'Every script, cron job, and API call that powers this site. Copy the whole thing.' },
  { title: 'How to Build and Monetise a Claude Tool in 48 Hours', desc: 'A complete playbook for shipping a paid AI tool as fast as humanly possible.' },
  { title: 'The $9/month AI Business Stack That Makes $X,XXX', desc: 'The exact tools, in the exact order, to run a lean AI business from scratch.' },
  { title: 'Prompt Engineering Playbook: How Veltrix Writes Every Piece of Content', desc: 'The prompts Veltrix uses for posts, social captions, newsletters, and guides.' },
  { title: 'The Veltrix Affiliate Strategy — Which Programs Pay and Which Don't', desc: 'Honest breakdown of every affiliate program in the AI space. What actually converts.' },
];

export default async function GuidesPage() {
  const posts = await getPosts();
  const freeContent = posts.filter(p => !p.is_paywalled);
  const paidContent = posts.filter(p => p.is_paywalled);

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12">
      <div className="mb-10">
        <h1 className="text-3xl md:text-4xl font-bold mb-2">Guides & Deep Dives</h1>
        <p className="text-secondary">Free content for everyone. The serious playbooks for insiders.</p>
      </div>

      {/* Free posts */}
      {freeContent.length > 0 && (
        <section className="mb-12">
          <h2 className="text-lg font-bold mb-4 text-primary">Free Content</h2>
          <div className="space-y-3">
            {freeContent.map(post => (
              <Link key={post.id} href={`/posts/${post.slug}`} className="card-glow flex items-center gap-4 group p-4">
                <div className="flex-1">
                  <span className="badge-muted text-[10px] mb-1 inline-block">{post.category}</span>
                  <h3 className="font-semibold text-primary group-hover:text-accent transition-colors">{post.title}</h3>
                  {post.excerpt && <p className="text-xs text-secondary mt-1 line-clamp-2">{post.excerpt}</p>}
                </div>
                <ArrowRight size={16} className="text-muted group-hover:text-accent transition-colors flex-shrink-0" />
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Paywall section */}
      <section>
        <div className="flex items-center gap-3 mb-6">
          <Lock size={18} className="text-accent" />
          <div>
            <h2 className="text-lg font-bold text-primary">Insider Guides</h2>
            <p className="text-xs text-secondary">Unlock with Veltrix Insider Access — $9.99 lifetime</p>
          </div>
        </div>

        <div className="space-y-3">
          {(paidContent.length > 0 ? paidContent : INSIDER_GUIDES).map((guide, i) => (
            <div key={i} className="relative card overflow-hidden">
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Lock size={14} className="text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-primary">{guide.title}</h3>
                  <p className="text-xs text-secondary mt-1">{'desc' in guide ? guide.desc : guide.excerpt}</p>
                </div>
              </div>
              {/* Blur overlay */}
              <div className="absolute inset-0 bg-surface/50 backdrop-blur-[1px] flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity duration-200">
                <Link href="/free" className="btn-primary text-sm px-6 py-2">Unlock Access →</Link>
              </div>
            </div>
          ))}
        </div>

        {/* CTA */}
        <div className="mt-8 p-8 rounded-2xl border border-accent/20 bg-surface text-center">
          <h3 className="text-xl font-bold mb-2">Join the first 100 insiders</h3>
          <p className="text-secondary text-sm max-w-md mx-auto mb-6">
            One payment. Every guide. Discord access. All future guides included. First 100 at $9.99 — then $19.99.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-6">
            <Link href="/free" className="btn-primary px-8 py-3">Get Lifetime Access — $9.99 <ArrowRight size={16} /></Link>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-secondary">
            {['7-day refund, no questions', 'Discord invite in 5 min', 'All future guides included'].map(item => (
              <span key={item} className="flex items-center gap-1"><CheckCircle size={11} className="text-success" />{item}</span>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
