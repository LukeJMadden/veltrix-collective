import { supabase, type LLMRanking } from '@/lib/supabase';
import { formatContextWindow, formatCost, formatRelativeTime } from '@/lib/utils';
import { ExternalLink, RefreshCw } from 'lucide-react';
import Link from 'next/link';

async function getLLMs(): Promise<LLMRanking[]> {
  const { data } = await supabase.from('llm_rankings').select('*').order('score_overall', { ascending: false });
  return data ?? [];
}

function ScoreBar({ value, max = 100 }: { value: number; max?: number }) {
  const pct = (value / max) * 100;
  const color = pct >= 90 ? '#00c2ff' : pct >= 75 ? '#00e676' : pct >= 60 ? '#ffab00' : '#ff4444';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-surface-2 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="text-xs font-mono w-7 text-right" style={{ color }}>{value}</span>
    </div>
  );
}

export default async function LLMsPage() {
  const llms = await getLLMs();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
      <div className="mb-10">
        <div className="flex items-center gap-2 mb-2">
          <RefreshCw size={14} className="text-accent" />
          <span className="text-xs font-semibold text-accent uppercase tracking-wider">Updated Weekly</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-2">LLM Rankings</h1>
        <p className="text-secondary max-w-2xl">Every major LLM ranked across 6 criteria. Veltrix reads benchmark reports weekly and updates scores automatically. No opinions — just data.</p>
      </div>

      {/* Criteria legend */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-3 mb-8">
        {[
          { key: 'Overall', color: '#00c2ff' },
          { key: 'Coding', color: '#00e676' },
          { key: 'Reasoning', color: '#a78bfa' },
          { key: 'Creativity', color: '#fb923c' },
          { key: 'Speed', color: '#facc15' },
          { key: 'Cost Eff.', color: '#34d399' },
        ].map(({ key, color }) => (
          <div key={key} className="flex items-center gap-1.5 text-xs text-secondary">
            <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
            {key}
          </div>
        ))}
      </div>

      {/* Desktop table */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border text-xs text-muted uppercase tracking-wider">
              <th className="text-left pb-3 pl-2">#</th>
              <th className="text-left pb-3">Model</th>
              <th className="text-left pb-3">Overall</th>
              <th className="text-left pb-3">Coding</th>
              <th className="text-left pb-3">Reasoning</th>
              <th className="text-left pb-3">Creativity</th>
              <th className="text-left pb-3">Speed</th>
              <th className="text-left pb-3">Cost Eff.</th>
              <th className="text-left pb-3">Context</th>
              <th className="text-left pb-3">Input/1M</th>
              <th className="text-right pb-3 pr-2">API</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50">
            {llms.map((llm, i) => (
              <tr key={llm.id} className="group hover:bg-surface/50 transition-colors">
                <td className="py-4 pl-2 text-muted font-bold">{i + 1}</td>
                <td className="py-4">
                  <div>
                    <div className="font-semibold text-primary">{llm.model_name}</div>
                    <div className="text-xs text-secondary capitalize">{llm.provider}</div>
                  </div>
                </td>
                <td className="py-4 w-28"><ScoreBar value={llm.score_overall} /></td>
                <td className="py-4 w-28"><ScoreBar value={llm.score_coding} /></td>
                <td className="py-4 w-28"><ScoreBar value={llm.score_reasoning} /></td>
                <td className="py-4 w-28"><ScoreBar value={llm.score_creativity} /></td>
                <td className="py-4 w-28"><ScoreBar value={llm.score_speed} /></td>
                <td className="py-4 w-28"><ScoreBar value={llm.score_cost_efficiency} /></td>
                <td className="py-4 text-xs text-secondary">{formatContextWindow(llm.context_window)}</td>
                <td className="py-4 text-xs text-secondary">{formatCost(llm.input_cost_per_1m)}</td>
                <td className="py-4 pr-2 text-right">
                  {llm.affiliate_url && (
                    <a href={llm.affiliate_url} target="_blank" rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-accent hover:underline">
                      API <ExternalLink size={10} />
                    </a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="md:hidden space-y-3">
        {llms.map((llm, i) => (
          <div key={llm.id} className="card">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-muted font-bold text-sm">#{i + 1}</span>
                  <span className="font-semibold text-primary">{llm.model_name}</span>
                </div>
                <span className="text-xs text-secondary capitalize">{llm.provider}</span>
              </div>
              <div className="text-xl font-bold text-accent">{llm.score_overall}</div>
            </div>
            <div className="space-y-2">
              {[
                { label: 'Coding', value: llm.score_coding },
                { label: 'Reasoning', value: llm.score_reasoning },
                { label: 'Speed', value: llm.score_speed },
              ].map(({ label, value }) => (
                <div key={label} className="flex items-center gap-3">
                  <span className="text-xs text-muted w-16">{label}</span>
                  <ScoreBar value={value} />
                </div>
              ))}
            </div>
            {llm.affiliate_url && (
              <a href={llm.affiliate_url} target="_blank" rel="noopener noreferrer"
                className="mt-3 flex items-center gap-1 text-xs text-accent hover:underline">
                Get API access <ExternalLink size={10} />
              </a>
            )}
          </div>
        ))}
      </div>

      <div className="mt-10 p-6 rounded-xl border border-accent/20 bg-surface text-center">
        <p className="text-sm text-secondary mb-3">Want the full prompt comparison tool? Test any prompt across models in real time.</p>
        <Link href="/tools/llm-tester" className="btn-primary text-sm">Try LLM Prompt Tester →</Link>
      </div>
    </div>
  );
}
