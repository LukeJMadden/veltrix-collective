// Telegram Bot Webhook for Veltrix Collective
// Handles incoming messages like /start and responds appropriately
// Deploy to: site/pages/api/telegram-webhook.js (or app/api/telegram-webhook/route.js for App Router)

import { createClient } from '@supabase/supabase-js';

const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

// Send message to Telegram user
async function sendMessage(chatId, text) {
  if (!TELEGRAM_BOT_TOKEN) {
    console.error('TELEGRAM_BOT_TOKEN not configured');
    return false;
  }

  try {
    const response = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: chatId,
        text: text,
        parse_mode: 'HTML'
      })
    });

    const result = await response.json();
    
    if (!result.ok) {
      console.error('Telegram API error:', result);
      return false;
    }

    return true;
  } catch (error) {
    console.error('Send message error:', error);
    return false;
  }
}

// Log bot interactions for debugging
async function logInteraction(chatId, username, message, response) {
  try {
    await supabase.from('support_logs').insert({
      email: `telegram_${chatId}`,
      category: 'telegram_bot',
      subject: message,
      body_snippet: response,
      auto_resolved: true
    });
  } catch (error) {
    console.error('Log interaction error:', error);
  }
}

// Handle different bot commands
function handleCommand(command, username) {
  switch (command) {
    case '/start':
      return `👋 Hello ${username ? `@${username}` : 'there'}!

I'm the Veltrix Publisher bot. I help Luke share AI news and insights with you.

🔗 <b>What you can do:</b>
• Visit <a href="https://veltrixcollective.com">Veltrix Collective</a> for AI tool rankings
• Get insider access for detailed analysis
• Join our Discord community for real-time discussions

Type /help to see all commands, or just say hi! 👋`;

    case '/help':
      return `🤖 <b>Veltrix Publisher Bot Commands</b>

/start - Get started with Veltrix
/help - Show this help message  
/latest - Get the latest AI news summary
/tools - See top AI tool recommendations
/about - Learn about Veltrix Collective

💡 <b>Quick Links:</b>
• <a href="https://veltrixcollective.com/tools">AI Tools Rankings</a>
• <a href="https://veltrixcollective.com/news">Latest AI News</a>
• <a href="https://veltrixcollective.com/insider">Insider Access</a>

Questions? Just type them and I'll help! 🚀`;

    case '/latest':
      return `📰 <b>Latest from Veltrix</b>

I'm currently fetching the latest AI news and insights. Check out our live news feed at <a href="https://veltrixcollective.com/news">veltrixcollective.com/news</a> for real-time updates.

🔥 <b>Popular this week:</b>
• AI tool comparisons and rankings
• Model performance benchmarks  
• Industry analysis and trends

Want more? Get <a href="https://veltrixcollective.com/insider">insider access</a> for detailed breakdowns! 📊`;

    case '/tools':
      return `🛠️ <b>Top AI Tools Right Now</b>

Based on our latest rankings and user feedback:

🥇 <b>LLM Powerhouses:</b> GPT-4, Claude, Gemini
🎨 <b>Creative Tools:</b> Midjourney, Runway, Luma
⚡ <b>Productivity:</b> Cursor, Notion AI, Perplexity
📊 <b>Analytics:</b> Browse our full rankings

👉 See complete tool comparisons: <a href="https://veltrixcollective.com/tools">veltrixcollective.com/tools</a>

Need a specific recommendation? Just ask! 🎯`;

    case '/about':
      return `🤖 <b>About Veltrix Collective</b>

We're an AI-powered platform tracking the rapidly evolving AI landscape. Built by AI, curated by Veltix, owned by you.

🎯 <b>What we do:</b>
• Rank and compare AI tools daily
• Summarize AI news with insider analysis  
• Build tools to help you navigate AI better
• Create a community of AI practitioners

👨‍💻 <b>Behind the scenes:</b> Luke Madden founded Veltrix to solve the "you need AI to keep up with AI" problem.

🔗 <a href="https://veltrixcollective.com">Visit our site</a> | <a href="https://veltrixcollective.com/insider">Get insider access</a>`;

    default:
      return `🤔 I didn't recognize that command. Try:

• /start - Get started
• /help - See all commands
• /latest - Latest AI news  
• /tools - AI tool recommendations

Or just tell me what you're looking for! I'm here to help with AI tools and news. 🚀`;
  }
}

// Main webhook handler
export default async function handler(req, res) {
  // Only accept POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const update = req.body;
    
    // Ignore non-message updates
    if (!update.message || !update.message.text) {
      return res.status(200).json({ status: 'ignored' });
    }

    const { message } = update;
    const chatId = message.chat.id;
    const text = message.text.trim();
    const username = message.from.username;
    const firstName = message.from.first_name || '';

    console.log(`Telegram message from ${username || chatId}: ${text}`);

    let responseText;

    // Handle commands (start with /) 
    if (text.startsWith('/')) {
      responseText = handleCommand(text, username);
    } else {
      // Handle natural language messages
      const lowerText = text.toLowerCase();
      
      if (lowerText.includes('hello') || lowerText.includes('hi') || lowerText.includes('hey')) {
        responseText = `Hey ${firstName || 'there'}! 👋 

Great to meet you! I'm here to help with AI tools and news. Try:

• /latest for recent AI updates
• /tools for tool recommendations  
• /help for all commands

What are you working on with AI? 🤖`;
      } else if (lowerText.includes('tool') || lowerText.includes('recommend')) {
        responseText = `🛠️ Looking for AI tool recommendations? 

I'd love to help! What are you trying to do?

• Writing & content creation
• Image/video generation  
• Code development
• Data analysis
• General productivity

Or check our full rankings: <a href="https://veltrixcollective.com/tools">veltrixcollective.com/tools</a> 🎯`;
      } else if (lowerText.includes('news') || lowerText.includes('update')) {
        responseText = handleCommand('/latest', username);
      } else {
        responseText = `Thanks for reaching out! 😊

I'm the Veltrix bot - I help with AI tool recommendations and news updates.

Try /help to see what I can do, or visit <a href="https://veltrixcollective.com">veltrixcollective.com</a> to explore our AI tool rankings and news.

What can I help you with today? 🚀`;
      }
    }

    // Send response
    const sent = await sendMessage(chatId, responseText);
    
    if (sent) {
      // Log successful interaction
      await logInteraction(chatId, username, text, 'Response sent successfully');
      console.log(`Response sent to ${username || chatId}`);
    } else {
      console.error(`Failed to send response to ${username || chatId}`);
    }

    return res.status(200).json({ 
      status: sent ? 'success' : 'error',
      message: sent ? 'Response sent' : 'Failed to send response'
    });

  } catch (error) {
    console.error('Webhook error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

// Export config for Vercel
export const config = {
  api: {
    bodyParser: {
      sizeLimit: '1mb',
    },
  },
}