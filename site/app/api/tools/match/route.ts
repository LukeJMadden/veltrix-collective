import { NextRequest, NextResponse } from 'next/server';
import { createServerClient } from '@/lib/supabase';
import Anthropic from '@anthropic-ai/sdk';
import crypto from 'crypto';

const FREE_DAILY_LIMIT = 5;
const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

function getIPHash(req: NextRequest): string {
  const ip = req.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown';
  return crypto.createHash('sha256').update(ip).digest('hex').substring(0, 16);
}

export async function POST(req: NextRequest) {
  try {
    const { query } = await req.json();
    if (!query?.trim()) return NextResponse.json({ error: 'Query required' }, { status: 400 });

    const supabase = createServerClient();
    const ipHash = getIPHash(req);
    const today = new Date().toISOString().split('T')[0];

    // Rate limit check (using automation_logs as simple counter)
    const { count } = await supabase.from('automation_logs')
      .select('*', { count: 'exact', head: true })
      .eq('script_name', `matchmaker:${ipHash}`)
      .gte('run_at', `${today}T00:00:00.000Z`);

    const usesLeft = FREE_DAILY_LIMIT - (count || 0);
    if (usesLeft <= 0) return NextResponse.json({ error: 'Daily limit reached', uses_left: 0 }, { status: 429 });

    // Get all tools from DB
    const { data: tools } = await supabase.from('tools').select('name,url,affiliate_url,category,description,pricing_model,score').order('score', { ascending: false });

    const toolList = (tools || []).map(t => `- ${t.name} (${t.category}, ${t.pricing_model}): ${t.description}`).join('\n');

    const message = await client.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: 1024,
      messages: [{
        role: 'user',
        content: `You are Veltrix, an AI tool curator. A user wants to: "${query}"

Here are the available tools in the Veltrix database:
${toolList}

Return EXACTLY 3 tool recommendations in this JSON format (no markdown, just raw JSON):
{
  "recommendations": [
    {
      "name": "Tool Name",
      "url": "tool url from the list",
      "reason": "2-3 sentence explanation of exactly why this tool fits their use case",
      "pricing": "pricing model"
    }
  ]
}

Pick the 3 best matches. Be specific about why each tool fits their exact need.`
      }]
    });

    const content = message.content[0].type === 'text' ? message.content[0].text : '';
    let recommendations = [];
    try {
      const parsed = JSON.parse(content);
      recommendations = parsed.recommendations || [];
      // Add affiliate URLs from DB
      recommendations = recommendations.map((rec: { name: string; url: string; reason: string; pricing: string }) => {
        const match = tools?.find(t => t.name === rec.name);
        return { ...rec, affiliate_url: match?.affiliate_url || rec.url };
      });
    } catch { return NextResponse.json({ error: 'Failed to parse recommendations' }, { status: 500 }); }

    // Log usage
    await supabase.from('automation_logs').insert({ script_name: `matchmaker:${ipHash}`, status: 'success', message: query.substring(0, 100) });

    return NextResponse.json({ recommendations, uses_left: usesLeft - 1 });
  } catch (err) {
    console.error('Matchmaker error:', err);
    return NextResponse.json({ error: 'Something went wrong' }, { status: 500 });
  }
}
