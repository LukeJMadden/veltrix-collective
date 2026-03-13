import { NextRequest, NextResponse } from 'next/server';
import { createServerClient } from '@/lib/supabase';

export async function POST(req: NextRequest) {
  try {
    const { email, goal, referral_code } = await req.json();
    if (!email || !email.includes('@')) return NextResponse.json({ error: 'Valid email required.' }, { status: 400 });

    const supabase = createServerClient();

    // Check if already subscribed
    const { data: existing } = await supabase.from('users').select('id,email,tier').eq('email', email).single();
    if (existing) return NextResponse.json({ message: "You're already subscribed. Check your inbox for the latest from Veltix.", existing: true });

    // Generate referral code
    const referralCode = Math.random().toString(36).substring(2, 10).toUpperCase();

    // Look up who referred them
    let referredById = null;
    if (referral_code) {
      const { data: referrer } = await supabase.from('users').select('id').eq('referral_code', referral_code.toUpperCase()).single();
      if (referrer) referredById = referral_code.toUpperCase();
    }

    // Insert user
    const { data: newUser, error } = await supabase.from('users').insert({
      email,
      tier: 'free',
      referral_code: referralCode,
      referred_by: referredById,
      goal: goal || null,
      segment: 'new',
    }).select().single();

    if (error) throw error;

    // Log referral if applicable
    if (referredById) {
      await supabase.from('referrals').insert({ referrer_code: referredById, referred_email: email, referred_user_id: newUser.id, status: 'confirmed' });
      // Increment referral count for referrer
      await supabase.rpc('increment_referral_count', { referrer_code: referredById });
    }

    // Trigger Brevo welcome email via webhook (fire and forget)
    try {
      await fetch(`${process.env.NEXT_PUBLIC_BASE_URL}/api/email/welcome`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, referral_code: referralCode, goal }),
      });
    } catch { /* non-blocking */ }

    return NextResponse.json({ message: "You're subscribed. Check your inbox — your first email from Veltix is on its way.", referral_code: referralCode });
  } catch (err: unknown) {
    console.error('Subscribe error:', err);
    return NextResponse.json({ error: 'Something went wrong. Please try again.' }, { status: 500 });
  }
}
