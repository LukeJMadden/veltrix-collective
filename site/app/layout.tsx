import type { Metadata } from 'next';
import './globals.css';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';

export const metadata: Metadata = {
  title: { default: 'Veltrix Collective — You need AI to keep up with AI', template: '%s | Veltrix Collective' },
  description: 'Veltrix ranks, tests, and curates the best AI tools on the planet. Live rankings, AI news, and tools built by an AI — for humans who build with AI.',
  keywords: ['AI tools', 'LLM rankings', 'Claude tools', 'AI news', 'best AI tools 2025', 'Veltrix'],
  metadataBase: new URL('https://www.veltrixcollective.com'),
  openGraph: {
    type: 'website',
    siteName: 'Veltrix Collective',
    title: 'Veltrix Collective — You need AI to keep up with AI',
    description: 'Live AI tool rankings, curated AI news, and tools built by Veltrix. The AI-native hub for builders.',
    url: 'https://www.veltrixcollective.com',
  },
  twitter: { card: 'summary_large_image', creator: '@veltrixai' },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-primary min-h-screen flex flex-col antialiased">
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
