import { NextRequest, NextResponse } from 'next/server';
import { createServerClient } from '@/lib/supabase';
import crypto from 'crypto';

function getIPHash(req: NextRequest): string {
  const ip = req.headers.get('x-forwarded-for')?.split(',')[0] || req.headers.get('x-real-ip') || 'unknown';
  return crypto.createHash('sha256').update(ip).digest('hex').substring(0, 16);
}

export async function POST(req: NextRequest) {
  try {
    const { toolId } = await req.json();
    if (!toolId) return NextResponse.json({ error: 'toolId required' }, { status: 400 });

    const supabase = createServerClient();
    const ipHash = getIPHash(req);
    const today = new Date().toISOString().split('T')[0];

    // Check if already voted today
    const { data: existing } = await supabase.from('tool_votes')
      .select('id').eq('tool_id', toolId).eq('ip_hash', ipHash)
      .gte('voted_at', `${today}T00:00:00.000Z`).single();

    if (existing) return NextResponse.json({ error: 'Already voted today' }, { status: 429 });

    // Record vote
    await supabase.from('tool_votes').insert({ tool_id: toolId, ip_hash: ipHash });

    // Increment vote count
    await supabase.rpc('increment_tool_votes', { p_tool_id: toolId });

    return NextResponse.json({ success: true });
  } catch (err) {
    console.error('Vote error:', err);
    return NextResponse.json({ error: 'Vote failed' }, { status: 500 });
  }
}
