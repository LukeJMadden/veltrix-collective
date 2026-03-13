import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Server-side client with service role (for API routes only)
export function createServerClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  );
}

export type Tool = {
  id: number;
  name: string;
  slug: string;
  url: string;
  category: string;
  description: string;
  score: number;
  votes: number;
  affiliate_url: string | null;
  is_veltrix_tool: boolean;
  featured: boolean;
  logo_url: string | null;
  pricing_model: string;
  monthly_price_usd: number | null;
  tags: string[];
  updated_at: string;
};

export type Post = {
  id: number;
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  status: string;
  category: string;
  tags: string[];
  is_paywalled: boolean;
  view_count: number;
  published_at: string;
  created_at: string;
};

export type NewsItem = {
  id: number;
  headline: string;
  summary: string;
  source_url: string;
  source_name: string;
  category: string;
  relevance_score: number;
  published_at: string;
};

export type LLMRanking = {
  id: number;
  model_name: string;
  provider: string;
  slug: string;
  score_overall: number;
  score_coding: number;
  score_reasoning: number;
  score_creativity: number;
  score_speed: number;
  score_cost_efficiency: number;
  context_window: number;
  input_cost_per_1m: number;
  output_cost_per_1m: number;
  api_url: string | null;
  affiliate_url: string | null;
  notes: string | null;
  updated_at: string;
};

export type User = {
  id: string;
  email: string;
  tier: string;
  referral_code: string;
  referral_count: number;
  segment: string;
  goal: string | null;
  created_at: string;
};
