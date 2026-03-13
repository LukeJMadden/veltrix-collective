import { NextRequest, NextResponse } from 'next/server';
import { createServerClient } from '@/lib/supabase';
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

export async function POST(req: NextRequest) {
  try {
    const { topic } = await req.json();
    if (!topic?.trim()) return NextResponse.json({ error: 'Topic required' }, { status: 400 });

    const supabase = createServerClient();
    const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();

    // Pull relevant news from Supabase
    const { data: newsItems } = await supabase.from('news')
      .select('headline,summary,source_name,published_at')
      .gte('published_at', sevenDaysAgo)
      .order('published_at', { ascending: false })
      .limit(50);

    // Filter for topic relevance
    const topicLower = topic.toLowerCase();
    const relevant = (newsItems || []).filter(item =>
      item.headline?.toLowerCase().includes(topicLower) ||
      item.summary?.toLowerCase().includes(topicLower)
    );

    const newsContext = relevant.length > 0
      ? relevant.slice(0, 15).map(n => `- ${n.headline} (${n.source_name}): ${n.summary}`).join('\n')
      : 'No specific news items found for this topic in the last 7 days.';

    const message = await client.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: 600,
      messages: [{
        role: 'user',
        content: `You are Veltrix. A user wants a 7-day news summary about: "${topic}"

Here are the relevant news items from our database:
${newsContext}

Write a 3-4 sentence synthesis in Veltrix voice — authoritative, direct, no filler.
Focus on what actually matters about this topic this week.
If there's little news, say so directly and note what the broader landscape looks like.

Return ONLY a JSON object (no markdown):
{
  "summary": "your 3-4 sentence synthesis here",
  "top_stories": [
    {"headline": "headline text", "source": "source name", "published_at": "date string"}
  ]
}
Limit top_stories to 3 items max.`
      }]
    });

    const content = message.content[0].type === 'text' ? message.content[0].text : '{}';
    let parsed: { summary: string; top_stories: { headline: string; source: string; published_at: string }[] };
    try { parsed = JSON.parse(content); }
    catch { return NextResponse.json({ error: 'Failed to generate summary' }, { status: 500 }); }

    return NextResponse.json({ topic, ...parsed, generated_at: new Date().toISOString() });
  } catch (err) {
    console.error('News summary error:', err);
    return NextResponse.json({ error: 'Something went wrong' }, { status: 500 });
  }
}
