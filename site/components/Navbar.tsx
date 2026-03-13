'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { Menu, X, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

const navLinks = [
  { href: '/tools', label: 'Tools' },
  { href: '/llms', label: 'LLM Rankings' },
  { href: '/news', label: 'AI News' },
  { href: '/guides', label: 'Guides' },
  { href: '/about', label: 'About Veltix' },
];

export default function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-7 h-7 rounded-lg bg-accent/10 border border-accent/30 flex items-center justify-center group-hover:shadow-glow-sm transition-all duration-200">
            <Zap size={14} className="text-accent" />
          </div>
          <span className="font-bold text-sm tracking-tight">
            Veltrix<span className="text-accent">.</span>
          </span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                'px-3 py-1.5 text-sm rounded-lg transition-all duration-200',
                pathname === link.href
                  ? 'text-accent bg-accent/10'
                  : 'text-secondary hover:text-primary hover:bg-surface-2'
              )}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* CTA */}
        <div className="hidden md:flex items-center gap-3">
          <Link href="/subscribe" className="text-sm text-secondary hover:text-primary transition-colors">
            Subscribe
          </Link>
          <Link href="/free" className="btn-primary text-xs px-4 py-2">
            Insider Access →
          </Link>
        </div>

        {/* Mobile toggle */}
        <button onClick={() => setOpen(!open)} className="md:hidden p-2 text-secondary hover:text-primary">
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden border-t border-border bg-background/95 backdrop-blur-xl px-4 py-4 flex flex-col gap-1">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setOpen(false)}
              className={cn(
                'px-3 py-2.5 text-sm rounded-lg transition-colors',
                pathname === link.href ? 'text-accent bg-accent/10' : 'text-secondary hover:text-primary hover:bg-surface-2'
              )}
            >
              {link.label}
            </Link>
          ))}
          <div className="pt-3 mt-2 border-t border-border flex flex-col gap-2">
            <Link href="/subscribe" onClick={() => setOpen(false)} className="btn-secondary text-center text-sm">Subscribe for Free</Link>
            <Link href="/free" onClick={() => setOpen(false)} className="btn-primary text-center text-sm">Insider Access →</Link>
          </div>
        </div>
      )}
    </header>
  );
}
