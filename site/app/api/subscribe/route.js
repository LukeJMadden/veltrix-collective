// site/app/api/subscribe/route.js
// Multi-step signup: collects name, email, gender, country/city, goals
// Saves to public.users via service key, adds to Brevo list

import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL  = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_KEY  = process.env.SUPABASE_SERVICE_KEY;   // service key — bypasses RLS
const BREVO_KEY     = process.env.BREVO_API_KEY;

// Timezone map: country code → IANA timezone (primary zone)
const COUNTRY_TIMEZONE = {
  AU: 'Australia/Sydney',    NZ: 'Pacific/Auckland',
  GB: 'Europe/London',       IE: 'Europe/Dublin',
  US: 'America/New_York',    CA: 'America/Toronto',
  IN: 'Asia/Kolkata',        SG: 'Asia/Singapore',
  JP: 'Asia/Tokyo',          DE: 'Europe/Berlin',
  FR: 'Europe/Paris',        NL: 'Europe/Amsterdam',
  AE: 'Asia/Dubai',          ZA: 'Africa/Johannesburg',
};

export async function POST(req) {
  try {
    const body = await req.json();
    const {
      email,
      preferredName,
      gender,
      country,
      city,
      goal,           // legacy field (1-month goal)
      goal1Month,
      goal12Month,
      referralCode,
    } = body;

    if (!email || !email.includes('@')) {
      return Response.json({ error: 'Valid email required' }, { status: 400 });
    }

    const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

    // Resolve timezone from country
    const timezone = COUNTRY_TIMEZONE[country?.toUpperCase()] || 'UTC';

    // Upsert user — if email exists, update their details
    const { data: user, error: dbError } = await supabase
      .from('users')
      .upsert(
        {
          email:          email.toLowerCase().trim(),
          preferred_name: preferredName || null,
          gender:         gender || null,
          country:        country?.toUpperCase() || null,
          city:           city || null,
          timezone:       timezone,
          goal:           goal1Month || goal || null,
          goal_1_month:   goal1Month || goal || null,
          goal_12_month:  goal12Month || null,
          referred_by:    referralCode || null,
          tier:           'free',
          segment:        'new',
          onboarding_step: 0,
          last_active:    new Date().toISOString(),
        },
        { onConflict: 'email', ignoreDuplicates: false }
      )
      .select('id, referral_code')
      .single();

    if (dbError) {
      console.error('Supabase error:', dbError);
      return Response.json({ error: 'Failed to save subscriber' }, { status: 500 });
    }

    // Add to Brevo contact list
    if (BREVO_KEY) {
      try {
        await fetch('https://api.brevo.com/v3/contacts', {
          method: 'POST',
          headers: {
            'api-key': BREVO_KEY,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: email.toLowerCase().trim(),
            attributes: {
              FIRSTNAME:   preferredName || '',
              COUNTRY:     country || '',
              CITY:        city || '',
              GOAL:        goal1Month || goal || '',
              TIMEZONE:    timezone,
            },
            listIds: [2],       // main newsletter list — update ID if different
            updateEnabled: true,
          }),
        });
      } catch (brevoErr) {
        // Don't fail the whole request if Brevo fails — user is saved in Supabase
        console.error('Brevo error (non-fatal):', brevoErr);
      }
    }

    return Response.json({
      success: true,
      referralCode: user?.referral_code || null,
      message: "You're in. First email lands at 5am your time.",
    });

  } catch (err) {
    console.error('Subscribe route error:', err);
    return Response.json({ error: 'Something went wrong. Please try again.' }, { status: 500 });
  }
}
