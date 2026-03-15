import { NextResponse } from 'next/server';

export async function GET() {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  if (!token) return NextResponse.json({ error: 'TELEGRAM_BOT_TOKEN not set' });
  
  const webhookInfo = await fetch(`https://api.telegram.org/bot${token}/getWebhookInfo`);
  const webhookData = await webhookInfo.json();
  
  return NextResponse.json({ 
    token_set: !!token,
    token_prefix: token.substring(0, 10) + '...',
    webhook_info: webhookData
  });
}