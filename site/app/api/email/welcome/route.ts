import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const { email, referral_code, goal } = await req.json();
    const brevoKey = process.env.BREVO_API_KEY;
    if (!brevoKey) return NextResponse.json({ error: 'Email not configured' }, { status: 500 });

    const referralUrl = `https://www.veltrixcollective.com/subscribe?ref=${referral_code}`;

    const res = await fetch('https://api.brevo.com/v3/smtp/email', {
      method: 'POST',
      headers: { 'api-key': brevoKey, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sender: { name: 'Veltix from Veltrix Collective', email: 'hello@veltrixcollective.com' },
        to: [{ email }],
        subject: 'Welcome to Veltrix — here\'s what to explore first',
        htmlContent: `
<div style="max-width:560px;margin:0 auto;font-family:Inter,-apple-system,sans-serif;color:#ffffff;background:#080b0f;padding:32px;border-radius:12px;border:1px solid #1e2733;">
  <div style="margin-bottom:24px;">
    <span style="font-size:24px;font-weight:800;letter-spacing:-0.5px;">Veltrix<span style="color:#00c2ff;">.</span></span>
  </div>
  <h1 style="font-size:22px;font-weight:700;margin-bottom:16px;color:#fff;">You're in. Let's go.</h1>
  <p style="color:#8b9ab0;font-size:15px;line-height:1.6;margin-bottom:24px;">
    I'm Veltix. I run this operation — tracking AI tools, ranking LLMs, and summarising everything worth knowing.
    ${goal ? `<br><br>You said you want to: <strong style="color:#fff;">${goal}</strong>. I'll keep that in mind.` : ''}
  </p>
  <p style="color:#8b9ab0;font-size:15px;line-height:1.6;margin-bottom:24px;">Here's where to start:</p>
  <div style="margin-bottom:32px;space-y:12px;">
    ${[
      ['🏆 AI Tool Rankings', 'https://www.veltrixcollective.com/tools', 'See which tools are winning right now'],
      ['📡 LLM Rankings', 'https://www.veltrixcollective.com/llms', 'The fastest way to pick the right model'],
      ['⚡ AI Matchmaker', 'https://www.veltrixcollective.com/tools/matchmaker', 'Tell me what you need — I\'ll find the tool'],
    ].map(([label, url, desc]) => `
    <div style="margin-bottom:12px;padding:12px 16px;background:#0f1318;border:1px solid #1e2733;border-radius:8px;">
      <a href="${url}" style="color:#00c2ff;font-weight:600;text-decoration:none;font-size:14px;">${label}</a>
      <p style="color:#8b9ab0;font-size:13px;margin:4px 0 0;">${desc}</p>
    </div>`).join('')}
  </div>
  <div style="padding:20px;background:#0f1318;border:1px solid #2a3545;border-radius:8px;margin-bottom:24px;">
    <p style="color:#fff;font-weight:600;font-size:14px;margin-bottom:8px;">Share Veltrix, get rewarded</p>
    <p style="color:#8b9ab0;font-size:13px;margin-bottom:12px;">Your referral link — every person who subscribes through it counts toward unlocking rewards.</p>
    <a href="${referralUrl}" style="color:#00c2ff;font-size:13px;word-break:break-all;">${referralUrl}</a>
  </div>
  <p style="color:#4a5568;font-size:12px;">— Veltix · <a href="https://www.veltrixcollective.com" style="color:#4a5568;">veltrixcollective.com</a> · <a href="{{unsubscribeUrl}}" style="color:#4a5568;">Unsubscribe</a></p>
</div>`
      }),
    });

    if (!res.ok) { const err = await res.json(); throw new Error(JSON.stringify(err)); }
    return NextResponse.json({ success: true });
  } catch (err) {
    console.error('Welcome email error:', err);
    return NextResponse.json({ error: 'Email failed' }, { status: 500 });
  }
}
