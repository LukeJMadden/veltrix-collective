import Link from 'next/link';
import { Zap } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-border mt-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 rounded-lg bg-accent/10 border border-accent/30 flex items-center justify-center">
                <Zap size={14} className="text-accent" />
              </div>
              <span className="font-bold text-sm">Veltrix<span className="text-accent">.</span></span>
            </Link>
            <p className="text-secondary text-xs leading-relaxed">
              You need AI to keep up with AI. Veltrix tracks, tests, and ranks everything so you don&apos;t have to.
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold text-primary uppercase tracking-wider mb-3">Explore</p>
            <div className="flex flex-col gap-2">
              {[['Tools Rankings', '/tools'], ['LLM Rankings', '/llms'], ['AI News', '/news'], ['Guides', '/guides']].map(([label, href]) => (
                <Link key={href} href={href} className="text-secondary hover:text-primary text-sm transition-colors">{label}</Link>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold text-primary uppercase tracking-wider mb-3">Tools</p>
            <div className="flex flex-col gap-2">
              {[['AI Matchmaker', '/tools/matchmaker'], ['LLM Tester', '/tools/llm-tester'], ['News Summariser', '/tools/news-summarizer']].map(([label, href]) => (
                <Link key={href} href={href} className="text-secondary hover:text-primary text-sm transition-colors">{label}</Link>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold text-primary uppercase tracking-wider mb-3">Community</p>
            <div className="flex flex-col gap-2">
              {[['About Veltix', '/about'], ['Insider Access', '/free'], ['Subscribe', '/subscribe'], ['Discord', 'https://discord.gg/veltrix']].map(([label, href]) => (
                <Link key={href} href={href} className="text-secondary hover:text-primary text-sm transition-colors">{label}</Link>
              ))}
            </div>
          </div>
        </div>
        <div className="pt-8 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-muted text-xs">© {new Date().getFullYear()} Veltrix Collective. Built by AI. Curated by Veltix.</p>
          <div className="flex items-center gap-4">
            <Link href="/privacy" className="text-muted hover:text-secondary text-xs transition-colors">Privacy</Link>
            <Link href="/terms" className="text-muted hover:text-secondary text-xs transition-colors">Terms</Link>
            <a href="https://x.com/veltrixai" target="_blank" rel="noopener noreferrer" className="text-muted hover:text-secondary text-xs transition-colors">@veltrixai</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
