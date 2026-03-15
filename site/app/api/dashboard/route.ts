import { NextRequest, NextResponse } from 'next/server';

const DASHBOARD_KEY = process.env.DASHBOARD_KEY || 'veltrix2026';

export async function GET(request: NextRequest) {
  const key = request.nextUrl.searchParams.get('key');
  
  if (key !== DASHBOARD_KEY) {
    return new NextResponse(
      `<!DOCTYPE html>
<html>
<head><title>Access Denied</title>
<style>body{background:#080a0f;color:#5a6a7a;font-family:monospace;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}
.box{text-align:center;} h1{color:#ff3b5c;font-size:24px;} p{margin-top:12px;} a{color:#00e5ff;}</style>
</head>
<body><div class="box">
<h1>Access Denied</h1>
<p>Add <code>?key=YOUR_KEY</code> to the URL</p>
</div></body></html>`,
      { status: 401, headers: { 'Content-Type': 'text/html' } }
    );
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

  // Fetch the dashboard HTML from the repo or serve it inline
  // We inject the real keys via a script block replacement
  const dashboardRes = await fetch(
    'https://raw.githubusercontent.com/LukeJMadden/veltrix-collective/main/dashboard/veltrix-dashboard.html',
    { next: { revalidate: 3600 } } // cache for 1 hour
  );
  
  let html = await dashboardRes.text();
  
  // Inject real Supabase credentials
  html = html.replace(
    'PASTE_YOUR_ANON_KEY_HERE',
    supabaseAnonKey
  );
  
  // Also inject via script tag at the top for any dynamic usage
  html = html.replace(
    '<head>',
    `<head>
    <script>
      window.SUPABASE_URL = "${supabaseUrl}";
      window.SUPABASE_ANON_KEY = "${supabaseAnonKey}";
    </script>`
  );

  return new NextResponse(html, {
    headers: { 
      'Content-Type': 'text/html',
      'X-Frame-Options': 'SAMEORIGIN',
      'Cache-Control': 'no-store'
    }
  });
}