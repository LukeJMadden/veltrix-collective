# Veltrix Mission Control Dashboard

Open `index.html` locally in any browser.

## To enable live Supabase data
Edit `index.html` and replace `PASTE_YOUR_ANON_KEY_HERE` with the value of `NEXT_PUBLIC_SUPABASE_ANON_KEY` from your Vercel dashboard. This is the public anon key — safe to use locally as RLS is enforced.

## What it shows
- Overview: live stats from Supabase (news count, tools, posts) + service status
- Build Plan: all 11 phases, click to expand detail
- Agents: all 10 agents with status, autonomy tier, trigger schedule
- Data Flow: visual diagram of the full system
- Schema: all Supabase tables with fields and RLS status
- Security: interactive checklist (progress saved in browser localStorage)
- Growth: insider milestone tracker and free vs paid breakdown
- Live News: latest 50 items from Scout, refreshes every 60s

## Do not deploy publicly
This file connects directly to your Supabase project. Keep it local.