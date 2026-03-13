import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const { email, referral_code } = await req.json();
    const brevoKey = process.env.BREVO_API_KEY;
    const discordInvite = process.env.DISCORD_INVITE_URL || 'https://discord.gg/veltrix';

    await fetch('https://api.brevo.com/v3/smtp/email', {
      method: 'POST',
      headers: { 'api-key': brevoKey!, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sender: { name: 'Veltix from Veltrix Collective', email: 'hello@veltrixcollective.com' },
        to: [{ email }],
        subject: "You're a Veltrix Insider — here's everything",
        htmlContent: `
<div style="max-width:560px;margin:0 auto;font-family:Inter,-apple-system,sans-serif;color:#ffffff;background:#080b0f;padding:32px;border-radius:12px;border:1px solid #1e2733;">
  <div style="margin-bottom:24px;">
    <span style="font-size:24px;font-weight:800;">Veltrix<span style="color:#00c2ff;">.</span></span>
  </div>
  <div style="padding:16px;background:rgba(0,198,118,0.1);border:1px solid rgba(0,198,118,0.2);border-radius:8px;margin-bottom:24px;">
    <p style="color:#00e676;font-weight:600;font-size:15px;margin:0;">✓ Insider Access confirmed</p>
  </div>
  <h1 style="font-size:22px;font-weight:700;margin-bottom:16px;">Welcome to the inside.</h1>
  <p style="color:#8b9ab0;font-size:15px;line-height:1.6;margin-bottom:24px;">Your lifetime access is live. Here's what you've unlocked:</p>

  <div style="margin-bottom:24px;">
    <a href="${discordInvite}" style="display:block;padding:16px;background:#5865f2;border-radius:8px;text-decoration:none;text-align:center;color:#fff;font-weight:600;font-size:15px;margin-bottom:12px;">
      Join the Insider Discord →
    </a>
    <a href="https://www.veltrixcollective.com/guides" style="display:block;padding:16px;background:#0f1318;border:1px solid #00c2ff;border-radius:8px;text-decoration:none;text-align:center;color:#00c2ff;font-weight:600;font-size:15px;">
      Access Your Insider Guides →
    </a>
  </div>

  <p style="color:#8b9ab0;font-size:14px;line-height:1.6;">Unlimited AI Matchmaker and LLM Tester usage is automatically enabled for your account.</p>
  <p style="color:#8b9ab0;font-size:14px;line-height:1.6;margin-top:12px;">Your referral code: <strong style="color:#fff;">${referral_code}</strong> — share it and earn rewards when people subscribe.</p>

  <p style="color:#4a5568;font-size:12px;margin-top:32px;">— Veltix · <a href="https://www.veltrixcollective.com" style="color:#4a5568;">veltrixcollective.com</a></p>
</div>`
      }),
    });

    return NextResponse.json({ success: true });
  } catch (err) {
    console.error('Activation email error:', err);
    return NextResponse.json({ error: 'Email failed' }, { status: 500 });
  }
}
