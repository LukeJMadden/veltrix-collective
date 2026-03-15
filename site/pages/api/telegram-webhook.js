// Telegram Bot Webhook for Veltrix Collective (Pages Router)
// Handles incoming messages like /start and responds appropriately
// Deploy to: site/pages/api/telegram-webhook.js

import { createClient } from '@supabase/supabase-js';

const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

// Handle different bot commands
function handleCommand(command, username) {
  switch (command) {
    case '/start':
      return `👋 Hello ${username ? `@$t{username}` : 'there'}!\n\nI'm the Veltrix Publisher bot. I help Luke share AI news and insights with you.\n\n• Visit https://veltrixcollective.com for AI tool rankings\n\nType /help for all commands!`;
    case '/help':
      return `🤖 Veltrix Publisher Bot Commands\n\n/start - Get started with Veltrix\n/help - Show this help message\n/tools - AI tool recommendations\n/latest - Latest AI news\n/about - About Veltrix Collective\n\nVisit https://veltrixcollective.com for more!`;
    default:
      return `I didn't recognize that command. Try /help to see all available commands!`;
  }
}

// Main webhook handler
export default async function handler(req, res) {
  if (req.method === 'GET') {
    return res.status(200).json({ status: 'Telegram webhook endpoint', message: 'Use POST to send updates' });
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const update = req.body;
    
    if (!update.message || !update.message.text) {
      return res.status(200).json({ status: 'ignored' });
    }

    const { message } = update;
    const chatId = message.chat.id;
    const text = message.text.trim();
    const username = message.from.username;

    let responseText = handleCommand(text, username);

    if (!TELEGRAM_BOT_TOKEN) {
      console.error('Telegram bot token not configured');
      return res.status(200).json({ status: 'no_token' });
    }

    // Send response via Telegram API
    const response = await fetch(`https://api.telegram.org/bot${TELEG_BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: chatId, text: responseText })
    });

    const result = await response.json();
    
    return res.status(200).json({ 
      status: result.ok ? 'success' : 'error',
      message: result.ok ? 'Response sent' : `Error: ${result.description}`
    });
  } catch (error) {
    console.error('Webhook error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
