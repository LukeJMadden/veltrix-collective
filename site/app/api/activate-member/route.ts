import { NextRequest, NextResponse } from 'next/server';
import { createServerClient } from '@/lib/supabase';
import crypto from 'crypto';

// Lemon Squeezy webhook handler
export async function POST(req: NextRequest) {
  const body = await req.text();
  const signature = req.headers.get('x-signature');

  // Verify webhook signature
  const secret = process.env.LEMON_SQUEEZY_WEBHOOK_SECRET;
  if (secret && signature) {
    const hmac = crypto.createHmac('sha256', secret).update(body).digest('hex');
    if (hmac !== signature) {
      return NextResponse.json({ error: 'Invalid signature' }, { status: 401 });
    }
  }

  const payload = JSON.parse(body);
  const eventName = payload.meta?.event_name;

  if (eventName !== 'order_created') {
    return NextResponse.json({ received: true });
  }

  const customerEmail = payload.data?.attributes?.user_email;
  const orderId = payload.data?.id;
  const productId = payload.data?.attributes?.first_order_item?.product_id?.toString();

  if (!customerEmail) return NextResponse.json({ error: 'No email in payload' }, { status: 400 });

  const supabase = createServerClient();

  // Find or create user
  let { data: user } = await supabase.from('users').select('*').eq('email', customerEmail).single();

  if (!user) {
    const referralCode = Math.random().toString(36).substring(2, 10).toUpperCase();
    const { data: newUser } = await supabase.from('users').insert({
      email: customerEmail, tier: 'lifetime', referral_code: referralCode, lemon_squeezy_order_id: orderId,
    }).select().single();
    user = newUser;
  } else {
    await supabase.from('users').update({ tier: 'lifetime', lemon_squeezy_order_id: orderId }).eq('email', customerEmail);
  }

  // Send Discord invite + confirmation email via Brevo (fire and forget)
  try {
    await fetch(`${process.env.NEXT_PUBLIC_BASE_URL}/api/email/activation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: customerEmail, referral_code: user?.referral_code }),
    });
  } catch { /* non-blocking */ }

  return NextResponse.json({ success: true, tier: 'lifetime' });
}
