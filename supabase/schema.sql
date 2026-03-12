-- ============================================================
-- VELTRIX COLLECTIVE — SUPABASE SCHEMA
-- Run this in your Supabase SQL editor
-- ============================================================

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- ============================================================
-- USERS / SUBSCRIBERS
-- ============================================================
create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  created_at timestamptz default now(),
  tier text default 'free',                    -- 'free' | 'lifetime' | 'pro'
  discord_invited boolean default false,
  discord_username text,
  lemon_squeezy_order_id text,

  -- Subscriber Intelligence fields
  referral_code text unique default upper(substring(replace(gen_random_uuid()::text, '-', ''), 1, 8)),
  referred_by text,                            -- referral_code of the person who referred them
  referral_count integer default 0,
  referral_reward_tier text default 'none',    -- 'none' | 'bronze' | 'silver' | 'gold'

  -- Engagement tracking
  last_active timestamptz default now(),
  email_open_count integer default 0,
  email_click_count integer default 0,
  tool_usage_count integer default 0,
  page_view_count integer default 0,

  -- Segmentation
  segment text default 'new',                  -- 'new' | 'engaged' | 'power' | 'dormant' | 'at-risk'
  tags text[] default '{}',                    -- ['content-fan', 'tool-user', 'community-member']

  -- Goal tracking
  goal text,                                   -- self-reported goal on signup
  goal_check_count integer default 0,
  last_goal_check timestamptz,

  -- Lead magnet
  lead_magnet_delivered boolean default false,
  lead_magnet_version text,

  -- Onboarding
  onboarding_step integer default 0,
  onboarding_complete boolean default false
);

-- Row Level Security for users
alter table users enable row level security;
create policy "Users can read own record" on users for select using (auth.uid() = id);

-- ============================================================
-- TOOLS RANKINGS
-- ============================================================
create table if not exists tools (
  id serial primary key,
  name text not null,
  slug text unique,
  url text,
  category text,                               -- 'claude-tools' | 'llm' | 'image' | 'productivity' | 'writing' | 'coding'
  description text,
  score numeric default 0,
  votes integer default 0,
  affiliate_url text,
  is_veltrix_tool boolean default false,
  featured boolean default false,
  logo_url text,
  pricing_model text,                          -- 'free' | 'freemium' | 'paid' | 'open-source'
  monthly_price_usd numeric,
  tags text[] default '{}',
  updated_at timestamptz default now(),
  created_at timestamptz default now()
);

-- Tool votes (one per user per tool per day)
create table if not exists tool_votes (
  id serial primary key,
  tool_id integer references tools(id),
  ip_hash text,
  user_id uuid references users(id),
  voted_at timestamptz default now()
);

-- ============================================================
-- CONTENT / BLOG POSTS
-- ============================================================
create table if not exists posts (
  id serial primary key,
  title text,
  slug text unique,
  content text,
  excerpt text,
  status text default 'draft',                 -- 'draft' | 'published'
  category text,                               -- 'news' | 'guides' | 'rankings' | 'tools'
  tags text[] default '{}',
  meta_title text,
  meta_description text,
  og_image_url text,
  is_paywalled boolean default false,
  view_count integer default 0,
  published_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- ============================================================
-- NEWS FEED
-- ============================================================
create table if not exists news (
  id serial primary key,
  headline text,
  summary text,
  source_url text,
  source_name text,
  category text default 'ai-general',
  relevance_score numeric default 0,
  published_at timestamptz default now(),
  created_at timestamptz default now()
);

-- ============================================================
-- NEWSLETTER ISSUES
-- ============================================================
create table if not exists newsletters (
  id serial primary key,
  subject text,
  content_html text,
  content_premium_html text,
  status text default 'draft',                 -- 'draft' | 'sent'
  recipient_count integer default 0,
  open_count integer default 0,
  click_count integer default 0,
  sent_at timestamptz,
  created_at timestamptz default now()
);

-- ============================================================
-- DIGITAL PRODUCTS
-- ============================================================
create table if not exists products (
  id serial primary key,
  title text not null,
  slug text unique,
  description text,
  price_usd numeric,
  product_type text,                           -- 'prompt-pack' | 'guide' | 'template' | 'cheatsheet'
  lemon_squeezy_product_id text,
  gumroad_product_id text,
  pdf_url text,
  preview_url text,
  sales_count integer default 0,
  active boolean default true,
  created_at timestamptz default now()
);

-- ============================================================
-- LLM RANKINGS
-- ============================================================
create table if not exists llm_rankings (
  id serial primary key,
  model_name text not null,
  provider text,                               -- 'anthropic' | 'openai' | 'google' | 'meta' | 'mistral'
  slug text unique,
  score_overall numeric default 0,
  score_coding numeric default 0,
  score_reasoning numeric default 0,
  score_creativity numeric default 0,
  score_speed numeric default 0,
  score_cost_efficiency numeric default 0,
  context_window integer,
  input_cost_per_1m numeric,
  output_cost_per_1m numeric,
  api_url text,
  affiliate_url text,
  notes text,
  updated_at timestamptz default now()
);

-- ============================================================
-- REFERRALS
-- ============================================================
create table if not exists referrals (
  id serial primary key,
  referrer_code text not null,
  referred_email text,
  referred_user_id uuid references users(id),
  status text default 'pending',              -- 'pending' | 'confirmed' | 'rewarded'
  reward_type text,                           -- 'guide-unlock' | 'discount' | 'upgrade'
  created_at timestamptz default now()
);

-- ============================================================
-- SUPPORT INTERACTIONS
-- ============================================================
create table if not exists support_logs (
  id serial primary key,
  email text,
  category text,                              -- 'refund' | 'access-issue' | 'question' | 'bug' | 'other'
  subject text,
  body_snippet text,
  resolution text,
  auto_resolved boolean default false,
  created_at timestamptz default now()
);

-- ============================================================
-- GOAL CHECK-INS
-- ============================================================
create table if not exists goal_checkins (
  id serial primary key,
  user_id uuid references users(id),
  email text,
  goal text,
  checkin_number integer,
  response_summary text,
  sent_at timestamptz default now()
);

-- ============================================================
-- PROGRAMMATIC SEO COMPARISONS CACHE
-- ============================================================
create table if not exists tool_comparisons (
  id serial primary key,
  tool_a_id integer references tools(id),
  tool_b_id integer references tools(id),
  slug text unique,
  content text,
  meta_description text,
  view_count integer default 0,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- ============================================================
-- AUTOMATION LOGS
-- ============================================================
create table if not exists automation_logs (
  id serial primary key,
  script_name text,
  status text,                                -- 'success' | 'error' | 'skipped'
  message text,
  records_processed integer default 0,
  run_at timestamptz default now()
);

-- ============================================================
-- INDEXES
-- ============================================================
create index if not exists idx_posts_slug on posts(slug);
create index if not exists idx_posts_status on posts(status);
create index if not exists idx_posts_published_at on posts(published_at desc);
create index if not exists idx_news_published_at on news(published_at desc);
create index if not exists idx_tools_category on tools(category);
create index if not exists idx_tools_score on tools(score desc);
create index if not exists idx_users_email on users(email);
create index if not exists idx_users_referral_code on users(referral_code);
create index if not exists idx_users_segment on users(segment);

-- ============================================================
-- SEED DATA — INITIAL TOOLS
-- ============================================================
insert into tools (name, slug, url, category, description, score, affiliate_url, is_veltrix_tool, pricing_model, featured) values
('Claude', 'claude', 'https://claude.ai', 'llm', 'Anthropic''s frontier AI — best for reasoning, coding, and long-context tasks.', 97, 'https://claude.ai', false, 'freemium', true),
('ChatGPT', 'chatgpt', 'https://chatgpt.com', 'llm', 'OpenAI''s flagship model. Still the most-used AI assistant on the planet.', 94, 'https://chatgpt.com', false, 'freemium', true),
('Cursor', 'cursor', 'https://cursor.sh', 'coding', 'AI-native code editor. Pair programmer built into VS Code. Developers swear by it.', 93, 'https://cursor.sh', false, 'freemium', true),
('Perplexity', 'perplexity', 'https://perplexity.ai', 'productivity', 'AI search that actually cites its sources. Replaces Google for research tasks.', 91, 'https://perplexity.ai', false, 'freemium', false),
('Midjourney', 'midjourney', 'https://midjourney.com', 'image', 'Still the gold standard for AI image generation. Unmatched aesthetic quality.', 90, 'https://midjourney.com', false, 'paid', true),
('Notion AI', 'notion-ai', 'https://notion.so', 'productivity', 'AI built into your notes and docs. Best for teams already using Notion.', 85, 'https://notion.so', false, 'freemium', false),
('Runway', 'runway', 'https://runwayml.com', 'video', 'AI video generation and editing. Gen-3 Alpha is genuinely impressive.', 88, 'https://runwayml.com', false, 'freemium', false),
('ElevenLabs', 'elevenlabs', 'https://elevenlabs.io', 'voice', 'Best-in-class voice cloning and TTS. Free tier is surprisingly generous.', 89, 'https://elevenlabs.io', false, 'freemium', false),
('Gemini', 'gemini', 'https://gemini.google.com', 'llm', 'Google''s frontier model. Best multimodal capabilities and Google Workspace integration.', 88, 'https://gemini.google.com', false, 'freemium', false),
('Grok', 'grok', 'https://grok.com', 'llm', 'xAI''s model with real-time X/Twitter data. Useful for current events.', 79, 'https://grok.com', false, 'freemium', false),
('v0 by Vercel', 'v0-vercel', 'https://v0.dev', 'coding', 'Generate full React/Next.js UI from a prompt. Saves hours on frontend work.', 87, 'https://v0.dev', false, 'freemium', false),
('Bolt.new', 'bolt-new', 'https://bolt.new', 'coding', 'Full-stack app builder from a prompt. Deploys instantly. No setup required.', 86, 'https://bolt.new', false, 'freemium', false),
('Suno', 'suno', 'https://suno.com', 'audio', 'AI music generation. Describe a song, get a full track with vocals in seconds.', 84, 'https://suno.com', false, 'freemium', false),
('Descript', 'descript', 'https://descript.com', 'video', 'Edit video by editing the transcript. AI removes filler words, silences, and more.', 83, 'https://descript.com', false, 'freemium', false),
('Grammarly', 'grammarly', 'https://grammarly.com', 'writing', 'AI writing assistant. The free tier catches more than most people realise.', 78, 'https://grammarly.com', false, 'freemium', false),
('Copy.ai', 'copy-ai', 'https://copy.ai', 'writing', 'Marketing copy generator. Good for social posts, ads, and email subject lines.', 75, 'https://copy.ai', false, 'freemium', false),
('Lovable', 'lovable', 'https://lovable.dev', 'coding', 'Build full-stack apps from a prompt and deploy to Supabase + Vercel instantly.', 85, 'https://lovable.dev', false, 'freemium', false),
('Replit AI', 'replit-ai', 'https://replit.com', 'coding', 'Cloud IDE with AI built in. Best for beginners who want to ship fast.', 80, 'https://replit.com', false, 'freemium', false),
('Jasper', 'jasper', 'https://jasper.ai', 'writing', 'Enterprise content AI. Solid for teams needing brand voice consistency at scale.', 74, 'https://jasper.ai', false, 'paid', false),
('Otter.ai', 'otter-ai', 'https://otter.ai', 'productivity', 'AI meeting transcription and summaries. Joins your Zoom/Meet automatically.', 81, 'https://otter.ai', false, 'freemium', false),
('Gamma', 'gamma', 'https://gamma.app', 'productivity', 'AI presentation builder. Better-looking slides than PowerPoint in a fraction of the time.', 82, 'https://gamma.app', false, 'freemium', false),
('Claude API', 'claude-api', 'https://console.anthropic.com', 'claude-tools', 'Direct API access to Claude. Build anything. The most powerful AI API available.', 96, 'https://console.anthropic.com', false, 'paid', true),
('Anthropic Workbench', 'anthropic-workbench', 'https://console.anthropic.com', 'claude-tools', 'Prompt engineering environment for Claude. Test and iterate on prompts with full controls.', 88, 'https://console.anthropic.com', false, 'free', false),
('Claude for Sheets', 'claude-for-sheets', 'https://workspace.google.com/marketplace/app/claude_for_sheets/909417792475', 'claude-tools', 'Use Claude directly inside Google Sheets. Great for bulk processing and data enrichment.', 83, null, false, 'free', false),
('OpenRouter', 'openrouter', 'https://openrouter.ai', 'llm', 'Single API for 100+ LLMs. Switch models without changing your code.', 87, 'https://openrouter.ai', false, 'paid', false),
('Stable Diffusion', 'stable-diffusion', 'https://stability.ai', 'image', 'Open-source image model. Run it locally or via API. Completely free if self-hosted.', 81, 'https://stability.ai', false, 'freemium', false),
('Flux', 'flux', 'https://blackforestlabs.ai', 'image', 'New challenger to Midjourney. Exceptional photorealism. Available via Replicate API.', 86, 'https://replicate.com/black-forest-labs', false, 'freemium', false),
('Whisper', 'whisper', 'https://openai.com/research/whisper', 'voice', 'OpenAI''s open-source speech-to-text. Runs locally. Industry-best transcription accuracy.', 88, null, false, 'free', false),
('Synthesia', 'synthesia', 'https://synthesia.io', 'video', 'Create AI avatar videos without a camera. Good for training and product content.', 77, 'https://synthesia.io', false, 'paid', false),
('Make.com', 'make', 'https://make.com', 'productivity', 'No-code automation platform. Powerful but we prefer native scripts for reliability.', 76, 'https://make.com', false, 'freemium', false)
on conflict (slug) do nothing;

-- Seed LLM rankings
insert into llm_rankings (model_name, provider, slug, score_overall, score_coding, score_reasoning, score_creativity, score_speed, score_cost_efficiency, context_window, input_cost_per_1m, output_cost_per_1m, api_url, affiliate_url) values
('Claude Opus 4', 'anthropic', 'claude-opus-4', 96, 95, 97, 96, 72, 65, 200000, 15.00, 75.00, 'https://docs.anthropic.com/en/api/getting-started', 'https://console.anthropic.com'),
('Claude Sonnet 4', 'anthropic', 'claude-sonnet-4', 93, 92, 93, 91, 88, 88, 200000, 3.00, 15.00, 'https://docs.anthropic.com/en/api/getting-started', 'https://console.anthropic.com'),
('GPT-4o', 'openai', 'gpt-4o', 91, 90, 90, 88, 85, 80, 128000, 2.50, 10.00, 'https://platform.openai.com', 'https://platform.openai.com'),
('o3', 'openai', 'o3', 95, 97, 98, 85, 45, 55, 200000, 10.00, 40.00, 'https://platform.openai.com', 'https://platform.openai.com'),
('Gemini 2.0 Flash', 'google', 'gemini-2-flash', 88, 87, 88, 84, 95, 92, 1000000, 0.10, 0.40, 'https://aistudio.google.com', 'https://aistudio.google.com'),
('Gemini 2.0 Pro', 'google', 'gemini-2-pro', 90, 89, 91, 87, 78, 72, 2000000, 1.25, 5.00, 'https://aistudio.google.com', 'https://aistudio.google.com'),
('Llama 3.3 70B', 'meta', 'llama-3-3-70b', 83, 82, 83, 80, 88, 97, 128000, 0.23, 0.40, 'https://together.ai', null),
('Mistral Large 2', 'mistral', 'mistral-large-2', 85, 86, 84, 82, 87, 85, 128000, 2.00, 6.00, 'https://mistral.ai/api', 'https://mistral.ai')
on conflict (slug) do nothing;
