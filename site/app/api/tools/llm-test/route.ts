import { NextRequest, NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import crypto from 'crypto';

const FREE_DAILY_LIMIT = 3;
const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

function getIPHash(req: NextRequest): string {
  const ip = req.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown';
  return crypto.createHash('sha256').update(ip).digest('hex').substring(0, 16);
}

const rateLimitMap = new Map<string, { count: number; date: string }>();

function checkRateLimit(ipHash: string): boolean {
  const today = new Date().toISOString().split('T')[0];
  const entry = rateLimitMap.get(ipHash);
  if (!entry || entry.date !== today) { rateLimitMap.set(ipHash, { count: 1, date: today }); return true; }
  if (entry.count >= FREE_DAILY_LIMIT) return false;
  entry.count++; return true;
}

const MODELS = [
  { id: 'claude-3-5-haiku-20241022', label: 'Claude 3.5 Haiku', provider: 'Anthropic', type: 'anthropic' },
  { id: 'gpt-4o-mini',               label: 'GPT-4o Mini',       provider: 'OpenAI',    type: 'openai' },
  { id: 'gpt-4o',                    label: 'GPT-4o',            provider: 'OpenAI',    type: 'openai' },
];

async function callOpenAI(model: string, prompt: string): Promise<{ response: string; latency_ms: number }> {
  const start = Date.now();
  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model,
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 512,
    }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || 'OpenAI error');
  return { response: data.choices?.[0]?.message?.content || 'No response', latency_ms: Date.now() - start };
}

export async function POST(req: NextRequest) {
  try {
    const { prompt } = await req.json();
    if (!prompt?.trim()) return NextResponse.json({ error: 'Prompt required' }, { status: 400 });
    if (prompt.length > 2000) return NextResponse.json({ error: 'Prompt too long (max 2000 chars)' }, { status: 400 });

    const ipHash = getIPHash(req);
    if (!checkRateLimit(ipHash)) {
      return NextResponse.json({ error: 'Daily limit of 3 tests reached. Upgrade to Insider Access for unlimited testing.' }, { status: 429 });
    }

    const results = await Promise.all(MODELS.map(async (model) => {
      try {
        if (model.type === 'anthropic') {
          const start = Date.now();
          const msg = await anthropic.messages.create({
            model: model.id, max_tokens: 512,
            messages: [{ role: 'user', content: prompt }],
          });
          const response = msg.content[0].type === 'text' ? msg.content[0].text : '';
          return { model: model.label, provider: model.provider, response, latency_ms: Date.now() - start };
        } else {
          const { response, latency_ms } = await callOpenAI(model.id, prompt);
          return { model: model.label, provider: model.provider, response, latency_ms };
        }
      } catch {
        return { model: model.label, provider: model.provider, response: `Could not get response from ${model.label}`, latency_ms: 0 };
      }
    }));

    return NextResponse.json({ results });
  } catch (err) {
    console.error('LLM test error:', err);
    return NextResponse.json({ error: 'Something went wrong' }, { status: 500 });
  }
}
