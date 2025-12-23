from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import (
    Flask,
    Response,
    abort,
    redirect,
    render_template_string,
    request,
    send_from_directory,
    url_for,
)

"""
J Supreme Marketing — Single-file Flask website (SEO + ad-ready)

✅ Single file: app.py
✅ Backgrounds from ./images/ OR ./static/img/
✅ Pages: Home, Insights, Blog, Start/Contact, Privacy, Terms, Thank You
✅ robots.txt + sitemap.xml
✅ Leads saved to leads.csv
✅ Newsletter saved to newsletter.csv
✅ AdSense-ready: clean ad slots + head script toggle via env vars

RUN LOCAL
1) pip install flask
2) python app.py
3) Open http://127.0.0.1:5000

FOLDER SETUP
your_project/
  app.py
  images/
    home_bg_1920x1080.jpg
    insights_bg_1920x1080.jpg
    start_bg_1920x1080.jpg
    privacy_bg_1920x1080.jpg
    terms_bg_1920x1080.jpg
    thank_you_bg_1920x1080.jpg

ADSENSE (optional)
- Set env:
  ADSENSE_CLIENT=ca-pub-XXXXXXXXXXXXXXXX
  ADSENSE_ENABLED=1

- Optional ad slots:
  ADSENSE_SLOT_HEADER=1234567890
  ADSENSE_SLOT_INARTICLE=1234567890
  ADSENSE_SLOT_SIDEBAR=1234567890
"""

# -----------------------
# Config
# -----------------------
APP_NAME = "J Supreme Marketing"
SLOGAN = "Strategy · Execution · Distribution"

CANONICAL_DOMAIN = os.getenv("CANONICAL_DOMAIN", "").strip()  # e.g. https://yourdomain.com
LEADS_CSV = Path(os.getenv("LEADS_CSV", "leads.csv"))
NEWSLETTER_CSV = Path(os.getenv("NEWSLETTER_CSV", "newsletter.csv"))

INCLUDE_PIXELS = bool(os.getenv("INCLUDE_PIXELS", "").strip())

ADSENSE_ENABLED = bool(os.getenv("ADSENSE_ENABLED", "").strip())
ADSENSE_CLIENT = os.getenv("ADSENSE_CLIENT", "").strip()  # example: ca-pub-1234567890123456
ADSENSE_SLOT_HEADER = os.getenv("ADSENSE_SLOT_HEADER", "").strip()
ADSENSE_SLOT_INARTICLE = os.getenv("ADSENSE_SLOT_INARTICLE", "").strip()
ADSENSE_SLOT_SIDEBAR = os.getenv("ADSENSE_SLOT_SIDEBAR", "").strip()

# Image folders:
STATIC_IMG_DIR = Path.cwd() / "static" / "img"
IMAGES_DIR = Path.cwd() / "images"

# -----------------------
# App
# -----------------------
app = Flask(__name__, static_folder=None)  # We'll serve /static ourselves

# -----------------------
# Simple Blog Posts (edit these anytime)
# -----------------------
BLOG_POSTS = [
    {
        "slug": "positioning-before-promotion",
        "title": "Positioning Before Promotion",
        "date": "2025-12-23",
        "excerpt": "Why pushing harder rarely fixes weak demand—and what to diagnose first.",
        "html": """
<p>Most brands don’t have an advertising problem. They have a <strong>positioning</strong> problem.</p>
<p>Before you spend more on ads, audit three things:</p>
<ul>
  <li><strong>Offer clarity:</strong> can a stranger repeat what you do in one sentence?</li>
  <li><strong>Audience fit:</strong> are you speaking to buyers or browsers?</li>
  <li><strong>Proof:</strong> do you show outcomes, not just features?</li>
</ul>
<p>When these are aligned, distribution becomes leverage—not guesswork.</p>
""",
    },
    {
        "slug": "the-signal-audit-framework",
        "title": "The Signal Audit Framework",
        "date": "2025-12-23",
        "excerpt": "A simple way to diagnose why marketing isn’t converting—without guessing.",
        "html": """
<p>The fastest way to improve marketing is to stop “tweaking” and start diagnosing.</p>
<p>We look at:</p>
<ul>
  <li><strong>Signal:</strong> what’s being communicated (message + positioning)</li>
  <li><strong>System:</strong> how demand moves (funnel + conversion logic)</li>
  <li><strong>Distribution:</strong> where you show up (channels + targeting)</li>
</ul>
<p>Fix the system, and the results follow.</p>
""",
    },
]

# -----------------------
# Helpers
# -----------------------
def site_url(path: str = "/") -> str:
    if CANONICAL_DOMAIN:
        return CANONICAL_DOMAIN.rstrip("/") + path
    return path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_csv_header(path: Path, header: list[str]) -> None:
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)


def save_row(path: Path, header: list[str], row: list[str]) -> None:
    ensure_csv_header(path, header)
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(row)


def save_lead(data: dict) -> None:
    header = [
        "created_at_utc",
        "name",
        "email",
        "company",
        "website",
        "budget",
        "goal",
        "message",
        "source",
        "ip",
        "user_agent",
    ]
    row = [
        now_iso(),
        data.get("name", ""),
        data.get("email", ""),
        data.get("company", ""),
        data.get("website", ""),
        data.get("budget", ""),
        data.get("goal", ""),
        data.get("message", ""),
        data.get("source", ""),
        data.get("ip", ""),
        data.get("user_agent", ""),
    ]
    save_row(LEADS_CSV, header, row)


def save_subscriber(data: dict) -> None:
    header = ["created_at_utc", "email", "source", "ip", "user_agent"]
    row = [
        now_iso(),
        data.get("email", ""),
        data.get("source", ""),
        data.get("ip", ""),
        data.get("user_agent", ""),
    ]
    save_row(NEWSLETTER_CSV, header, row)


def find_bg_file(filename: str) -> Path | None:
    p1 = STATIC_IMG_DIR / filename
    if p1.exists():
        return p1
    p2 = IMAGES_DIR / filename
    if p2.exists():
        return p2
    return None


def bg_image_for(page: str) -> str | None:
    mapping = {
        "home": "home_bg_1920x1080.jpg",
        "insights": "insights_bg_1920x1080.jpg",
        "start": "start_bg_1920x1080.jpg",
        "privacy": "privacy_bg_1920x1080.jpg",
        "terms": "terms_bg_1920x1080.jpg",
        "thank_you": "thank_you_bg_1920x1080.jpg",
        "blog": "insights_bg_1920x1080.jpg",
    }
    filename = mapping.get(page)
    if not filename:
        return None
    if find_bg_file(filename):
        return f"/static/img/{filename}"
    return None


def get_post(slug: str) -> dict | None:
    for p in BLOG_POSTS:
        if p["slug"] == slug:
            return p
    return None


def render_page(body_html: str, *, page: str, title: str, desc: str) -> str:
    return render_template_string(
        BASE,
        app_name=APP_NAME,
        slogan=SLOGAN,
        meta_title=title,
        meta_desc=desc,
        canonical=site_url(request.path),
        include_pixels=INCLUDE_PIXELS,
        adsense_enabled=ADSENSE_ENABLED and bool(ADSENSE_CLIENT),
        adsense_client=ADSENSE_CLIENT,
        adsense_slot_header=ADSENSE_SLOT_HEADER,
        adsense_slot_inarticle=ADSENSE_SLOT_INARTICLE,
        adsense_slot_sidebar=ADSENSE_SLOT_SIDEBAR,
        body=render_template_string(body_html, hero_bg_url=bg_image_for(page)),
    )


# -----------------------
# Static files
# -----------------------
@app.route("/static/<path:filename>")
def static_files(filename: str):
    base = Path.cwd() / "static"
    if not base.exists():
        abort(404)
    return send_from_directory(base, filename)


@app.route("/static/img/<path:filename>")
def static_img_files(filename: str):
    p = find_bg_file(filename)
    if not p:
        abort(404)
    return send_from_directory(p.parent, p.name)


# -----------------------
# SEO: robots + sitemap
# -----------------------
@app.route("/robots.txt")
def robots():
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {site_url('/sitemap.xml')}",
    ]
    return Response("\n".join(lines) + "\n", mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    pages = [
        (site_url(url_for("home")), "weekly", "1.0"),
        (site_url(url_for("insights")), "weekly", "0.7"),
        (site_url(url_for("blog")), "weekly", "0.7"),
        (site_url(url_for("start")), "monthly", "0.7"),
        (site_url(url_for("privacy")), "yearly", "0.2"),
        (site_url(url_for("terms")), "yearly", "0.2"),
        (site_url(url_for("thank_you")), "yearly", "0.1"),
    ]

    # Add blog posts
    for p in BLOG_POSTS:
        pages.append((site_url(url_for("blog_post", slug=p["slug"])), "monthly", "0.6"))

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for loc, changefreq, priority in pages:
        xml.append("  <url>")
        xml.append(f"    <loc>{loc}</loc>")
        xml.append(f"    <changefreq>{changefreq}</changefreq>")
        xml.append(f"    <priority>{priority}</priority>")
        xml.append("  </url>")
    xml.append("</urlset>")
    return Response("\n".join(xml), mimetype="application/xml")


# -----------------------
# HTML Template (embedded)
# -----------------------
BASE = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{{ meta_title }}</title>
  <meta name="description" content="{{ meta_desc }}" />
  <link rel="canonical" href="{{ canonical }}" />

  <meta property="og:title" content="{{ meta_title }}" />
  <meta property="og:description" content="{{ meta_desc }}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{{ canonical }}" />

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:wght@400;500;600&display=swap" rel="stylesheet">

  {% if adsense_enabled %}
    {# Auto ads script (Google provides the exact code in AdSense). #}
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={{ adsense_client }}" crossorigin="anonymous"></script>
  {% endif %}

  <style>
    :root{
      --bg:#07070a; --bg2:#0b0b10; --text:#f2f2f2; --muted:#b9b9c4;
      --line:rgba(255,255,255,.10);
      --glass:rgba(0,0,0,.22);

      /* Clear hero tuning */
      --hero-bright: 1.05;
      --hero-contrast: 1.22;
      --hero-sat: 1.18;
      --hero-blur: 0px;

      /* Lighter overlay */
      --overlay-a: 0.48;
      --overlay-b: 0.24;
      --overlay-c: 0.08;
    }

    *{box-sizing:border-box}
    html,body{height:100%}
    body{
      margin:0;
      color:var(--text);
      font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;
      background:
        radial-gradient(1200px 800px at 70% 20%, rgba(255,255,255,.06), transparent 60%),
        linear-gradient(180deg, var(--bg), var(--bg2));
    }

    .container{width:min(1180px,92vw);margin:0 auto}
    a{color:inherit}

    header{
      position:fixed; inset:0 0 auto 0; z-index:50;
      background:linear-gradient(180deg, rgba(0,0,0,.70), rgba(0,0,0,0));
      backdrop-filter: blur(6px);
    }

    .topbar{
      display:flex; align-items:center; justify-content:space-between;
      padding:14px 0;
    }

    .brand{
      font-family:"Playfair Display",Georgia,serif;
      text-decoration:none;
      font-size:17px;
      letter-spacing:.2px;
      position:relative;
      top:-1px;
      margin-left:2px;
    }

    nav{display:flex; gap:18px; align-items:center}
    nav a{
      text-decoration:none;
      font-size:13px; letter-spacing:.3px;
      color:rgba(255,255,255,.78);
    }
    nav a:hover{color:rgba(255,255,255,.95)}
    .navcta{
      padding:10px 12px; border:1px solid var(--line); border-radius:999px;
      background:rgba(0,0,0,.10);
    }

    .hero{
      min-height:92vh;
      padding-top:92px;
      display:flex; align-items:center;
      position:relative; overflow:hidden;
      isolation:isolate;
    }

    .hero-bg{
      position:absolute; inset:0; z-index:0;
      background: center/cover no-repeat;
      filter: brightness(var(--hero-bright)) contrast(var(--hero-contrast)) saturate(var(--hero-sat)) blur(var(--hero-blur));
      image-rendering: -webkit-optimize-contrast;
      backface-visibility: hidden;
      transform: translateZ(0);
      will-change: transform, filter;
    }

    .hero-bg.fallback{
      background:
        radial-gradient(700px 400px at 70% 55%, rgba(255,255,255,.09), transparent 65%),
        linear-gradient(180deg, #0a0a0f, #06060a);
    }

    .hero-overlay{
      position:absolute; inset:0; z-index:1;
      pointer-events:none;
      background: linear-gradient(
        90deg,
        rgba(0,0,0,var(--overlay-a)) 0%,
        rgba(0,0,0,var(--overlay-b)) 45%,
        rgba(0,0,0,var(--overlay-c)) 75%,
        rgba(0,0,0,0) 100%
      );
    }

    .hero-inner{position:relative; z-index:2; width:100%}

    h1{
      font-family:"Playfair Display",Georgia,serif;
      font-weight:500; line-height:1.05;
      font-size:clamp(40px,5vw,62px);
      margin:0 0 18px 0;
      text-shadow: 0 10px 30px rgba(0,0,0,.35);
    }

    .sub{color:var(--muted); line-height:1.6; max-width:55ch; margin:0 0 22px 0}
    .actions{display:flex; gap:14px; align-items:center; flex-wrap:wrap}
    .btn{
      display:inline-flex; align-items:center; justify-content:center;
      padding:12px 16px; border:1px solid var(--line);
      border-radius:10px; text-decoration:none;
      background:rgba(0,0,0,.22);
      font-weight:500;
      cursor:pointer;
    }
    .btn:hover{background:rgba(255,255,255,.06)}
    .link{color:rgba(255,255,255,.78); text-decoration:none}
    .link:hover{color:rgba(255,255,255,.95)}

    .strip{
      border-top:1px solid var(--line);
      border-bottom:1px solid var(--line);
      background:rgba(255,255,255,.02);
    }
    .strip-inner{
      display:grid; grid-template-columns:repeat(3,1fr);
      gap:16px; padding:22px 0;
    }
    .pill{
      padding:16px; border:1px solid var(--line); border-radius:14px;
      background:rgba(0,0,0,.18);
    }
    .kicker{font-size:12px; letter-spacing:.24em; color:rgba(255,255,255,.78)}
    .pill p{margin:10px 0 0 0; color:var(--muted); font-size:14px; line-height:1.5}

    .section{padding:64px 0}
    .muted{background:rgba(255,255,255,.02); border-top:1px solid var(--line); border-bottom:1px solid var(--line)}
    h2{
      font-family:"Playfair Display",Georgia,serif;
      font-weight:500; font-size:32px;
      margin:0 0 18px 0;
    }
    .grid2{display:grid; grid-template-columns:repeat(2,1fr); gap:14px}
    .card{
      padding:18px; border:1px solid var(--line); border-radius:14px;
      background:rgba(255,255,255,.04);
    }
    .card .title{font-weight:600; margin-bottom:8px}
    .card .desc{color:var(--muted); line-height:1.5}

    .proof{display:grid; grid-template-columns:repeat(3,1fr); gap:14px}
    .proof-item{
      padding:18px; border:1px solid var(--line); border-radius:14px;
      background:rgba(0,0,0,.15);
      display:flex; gap:14px; align-items:flex-start;
    }
    .badge{
      min-width:44px; height:44px; border:1px solid var(--line);
      border-radius:12px; display:flex; align-items:center; justify-content:center;
      background:rgba(255,255,255,.03); font-weight:600;
    }
    .proof-item p{margin:0; color:var(--muted); line-height:1.55}

    .cta{padding:54px 0}
    .cta-inner{
      border:1px solid var(--line); border-radius:16px;
      padding:22px; background:var(--glass);
      display:flex; align-items:center; justify-content:space-between; gap:18px;
    }
    .cta-inner h3{
      margin:0 0 6px 0;
      font-family:"Playfair Display",Georgia,serif;
      font-weight:500; font-size:24px;
    }
    .cta-inner p{margin:0; color:var(--muted)}

    .page{padding-top:120px; padding-bottom:70px}
    .lead{color:var(--muted); max-width:80ch; line-height:1.6}

    /* BLOG */
    .blogwrap{display:grid; grid-template-columns: 1.35fr .65fr; gap:16px; align-items:start}
    .postcard{
      padding:18px; border:1px solid var(--line); border-radius:14px;
      background:rgba(255,255,255,.03);
    }
    .postcard a{text-decoration:none}
    .postmeta{color:rgba(255,255,255,.60); font-size:13px; margin-top:8px}
    .postbody{color:var(--muted); line-height:1.75}
    .sidebar{
      padding:18px; border:1px solid var(--line); border-radius:14px;
      background:rgba(0,0,0,.12);
      position:sticky; top:110px;
    }

    /* NEWSLETTER */
    .newsletter{
      margin-top:18px;
      border:1px solid var(--line);
      border-radius:14px;
      padding:16px;
      background:rgba(255,255,255,.03);
      display:grid;
      gap:10px;
    }
    .newsletter .hint{color:rgba(255,255,255,.65); font-size:13px; line-height:1.5}
    .newsletter .row{
      display:grid; grid-template-columns: 1fr auto; gap:10px;
    }

    /* ADS (refined containers) */
    .adbox{
      border:1px solid rgba(255,255,255,.10);
      border-radius:14px;
      background:rgba(0,0,0,.18);
      padding:14px;
    }
    .adlabel{
      font-size:11px;
      letter-spacing:.22em;
      color:rgba(255,255,255,.45);
      margin:0 0 10px 0;
    }

    form{
      margin-top:18px;
      border:1px solid var(--line);
      border-radius:14px;
      padding:16px;
      background:rgba(255,255,255,.03);
      display:grid;
      gap:12px;
      max-width:720px;
    }
    label{font-size:13px; color:rgba(255,255,255,.78)}
    input, textarea, select{
      width:100%;
      padding:12px;
      border-radius:12px;
      border:1px solid rgba(255,255,255,.12);
      background:rgba(0,0,0,.25);
      color:var(--text);
      outline:none;
      font-family:inherit;
    }
    textarea{min-height:120px; resize:vertical}
    .row2{display:grid; grid-template-columns:1fr 1fr; gap:12px}

    footer{
      border-top:1px solid var(--line);
      padding:22px 0;
      background:rgba(0,0,0,.25);
    }
    .footer-inner{
      display:flex; justify-content:space-between; gap:14px; flex-wrap:wrap;
    }
    .footbrand{font-family:"Playfair Display",Georgia,serif; font-size:16px}
    .foottag{color:rgba(255,255,255,.65); font-size:13px; margin-top:4px}
    .footlinks a{color:rgba(255,255,255,.75); text-decoration:none; font-size:13px}
    .footlinks a:hover{color:rgba(255,255,255,.95)}
    .dot{color:rgba(255,255,255,.40); margin:0 8px}

    @media (max-width: 980px){
      :root{ --hero-bright:1.02; --hero-contrast:1.18; --overlay-a:0.55; --overlay-b:0.30; --overlay-c:0.10; }
      .blogwrap{grid-template-columns:1fr}
      .sidebar{position:static}
    }

    @media (max-width: 600px){
      :root{ --hero-bright:0.95; --hero-contrast:1.15; --hero-blur:0px; --overlay-a:0.60; --overlay-b:0.35; --overlay-c:0.12; }
      .hero-overlay{
        background: linear-gradient(
          180deg,
          rgba(0,0,0,var(--overlay-a)) 0%,
          rgba(0,0,0,var(--overlay-b)) 55%,
          rgba(0,0,0,var(--overlay-c)) 100%
        );
      }
      .newsletter .row{grid-template-columns:1fr}
    }

    @media (max-width: 860px){
      nav{display:none}
      .strip-inner{grid-template-columns:1fr}
      .grid2{grid-template-columns:1fr}
      .proof{grid-template-columns:1fr}
      .cta-inner{flex-direction:column; align-items:flex-start}
      .row2{grid-template-columns:1fr}
    }
  </style>

  {% if include_pixels %}
  <!-- OPTIONAL AD PIXELS PLACEHOLDER -->
  {% endif %}
</head>

<body>
  <header>
    <div class="container topbar">
      <a class="brand" href="{{ url_for('home') }}">{{ app_name }}</a>
      <nav>
        <a href="{{ url_for('home') }}#approach">Approach</a>
        <a href="{{ url_for('home') }}#capabilities">Capabilities</a>
        <a href="{{ url_for('home') }}#proof">Proof</a>
        <a href="{{ url_for('blog') }}">Blog</a>
        <a class="navcta" href="{{ url_for('start') }}">Start Conversation</a>
      </nav>
    </div>
  </header>

  {{ body|safe }}

  <footer>
    <div class="container footer-inner">
      <div>
        <div class="footbrand">{{ app_name }}</div>
        <div class="foottag">{{ slogan }}</div>
      </div>
      <div class="footlinks">
        <a href="{{ url_for('insights') }}">Insights</a>
        <span class="dot">•</span>
        <a href="{{ url_for('blog') }}">Blog</a>
        <span class="dot">•</span>
        <a href="{{ url_for('privacy') }}">Privacy</a>
        <span class="dot">•</span>
        <a href="{{ url_for('terms') }}">Terms</a>
        <span class="dot">•</span>
        <a href="mailto:jordanmorrisr@gmail.com">jordanmorrisr@gmail.com</a>
        <span class="dot">•</span>
        <a href="tel:+16582182282">(658) 218-2282</a>
      </div>
    </div>
  </footer>
</body>
</html>
"""

HERO_OPEN = r"""
<main class="hero">
  {% if hero_bg_url %}
    <div class="hero-bg" style="background-image:url('{{ hero_bg_url }}');"></div>
  {% else %}
    <div class="hero-bg fallback"></div>
  {% endif %}
  <div class="hero-overlay"></div>
  <div class="container hero-inner">
"""

HERO_CLOSE = r"""
  </div>
</main>
"""

NEWSLETTER_BLOCK = r"""
<div class="newsletter">
  <div class="kicker">NEWSLETTER</div>
  <div class="hint">Short strategy dispatches—no spam. If it’s not useful, we won’t send it.</div>
  <form method="post" action="{{ url_for('newsletter_subscribe') }}" style="margin:0; padding:0; border:none; background:transparent; max-width:none;">
    <div class="row">
      <input name="email" type="email" required placeholder="you@company.com" aria-label="Email address" />
      <button class="btn" type="submit">Subscribe</button>
    </div>
    <input type="hidden" name="source" value="newsletter_block" />
  </form>
</div>
"""

def adsense_ad_unit(slot: str) -> str:
    """
    Returns an AdSense ad unit HTML block (only used when enabled + slot set).
    Note: Actual slot IDs and client ID come from env vars.
    """
    if not (ADSENSE_ENABLED and ADSENSE_CLIENT and slot):
        return ""

    # Responsive ad unit example structure (Google provides variations).
    return f"""
<div class="adbox">
  <div class="adlabel">ADVERTISEMENT</div>
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="{ADSENSE_CLIENT}"
       data-ad-slot="{slot}"
       data-ad-format="auto"
       data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</div>
""".strip()


HOME_BODY = HERO_OPEN + r"""
    <h1>We don’t chase.<br/>We appear, diagnose, and solve.</h1>
    <p class="sub">Strategy-led marketing for brands that need clarity—not noise.</p>
    <div class="actions">
      <a class="btn" href="{{ url_for('start') }}">Request a Signal Audit</a>
      <a class="link" href="{{ url_for('blog') }}">Read the blog →</a>
    </div>
""" + HERO_CLOSE + r"""

<section id="approach" class="strip">
  <div class="container strip-inner">
    <div class="pill">
      <div class="kicker">APPEAR</div>
      <p>Show up where it matters—without begging.</p>
    </div>
    <div class="pill">
      <div class="kicker">DIAGNOSE</div>
      <p>Find why marketing isn’t converting, not just how it looks.</p>
    </div>
    <div class="pill">
      <div class="kicker">SOLVE</div>
      <p>Systems + messaging aligned to outcomes.</p>
    </div>
  </div>
</section>

<section id="capabilities" class="section">
  <div class="container">
    <h2>What we actually do</h2>
    <div class="grid2">
      <div class="card">
        <div class="title">Brand Strategy & Positioning</div>
        <div class="desc">Clarify the offer, audience, and angle.</div>
      </div>
      <div class="card">
        <div class="title">Creative Direction & Design Systems</div>
        <div class="desc">Cohesive visuals that scale across platforms.</div>
      </div>
      <div class="card">
        <div class="title">Paid Ads & Distribution Strategy</div>
        <div class="desc">Targeted reach with measurable intent.</div>
      </div>
      <div class="card">
        <div class="title">Websites & Conversion Logic</div>
        <div class="desc">Pages built to convert, not just look good.</div>
      </div>
    </div>
  </div>
</section>

<section id="proof" class="section muted">
  <div class="container">
    <h2>Results without theatrics</h2>
    <div class="proof">
      <div class="proof-item">
        <div class="badge">↑</div>
        <p>Stronger positioning + clearer messaging for growing brands.</p>
      </div>
      <div class="proof-item">
        <div class="badge">ROAS</div>
        <p>Campaigns scaled with controlled spend and clean reporting.</p>
      </div>
      <div class="proof-item">
        <div class="badge">System</div>
        <p>Marketing systems clients stop “tweaking” every week.</p>
      </div>
    </div>
  </div>
</section>

<section class="cta">
  <div class="container cta-inner">
    <div>
      <h3>If your brand feels noisy or underperforming—</h3>
      <p>That’s not a motivation problem. It’s a systems problem.</p>
    </div>
    <a class="btn" href="{{ url_for('start') }}">Start with a conversation</a>
  </div>
</section>
"""


INSIGHTS_BODY = HERO_OPEN + r"""
    <h1>Too many brands want attention.<br/>You deserve influence.</h1>
    <p class="sub">We help brands think in systems, seize signals, and become unignorable.</p>
    <div class="actions">
      <a class="btn" href="{{ url_for('start') }}">Start Conversation</a>
      <a class="link" href="{{ url_for('blog') }}">Read the blog →</a>
    </div>
""" + HERO_CLOSE + r"""
<section class="section">
  <div class="container">
    <h2>Marketing dispatches</h2>
    <div class="grid2">
      <div class="card">
        <div class="kicker">STRATEGY</div>
        <div class="title" style="margin-top:10px;">Leading the Conversation vs Chasing Noise</div>
        <div class="desc">Why proactive positioning beats reactive marketing.</div>
      </div>
      <div class="card">
        <div class="kicker">DIAGNOSIS</div>
        <div class="title" style="margin-top:10px;">5 Signals Your Funnel is Misfiring</div>
        <div class="desc">Fix the system, not the surface.</div>
      </div>
      <div class="card">
        <div class="kicker">DISTRIBUTION</div>
        <div class="title" style="margin-top:10px;">Distribution is a Weapon</div>
        <div class="desc">Reach is leverage—when the message is tight.</div>
      </div>
      <div class="card">
        <div class="kicker">SYSTEMS</div>
        <div class="title" style="margin-top:10px;">Ads Don’t Fix Broken Offers</div>
        <div class="desc">Align offer, message, and distribution before scaling spend.</div>
      </div>
    </div>

    """ + NEWSLETTER_BLOCK + r"""
  </div>
</section>
"""


BLOG_LIST_BODY = r"""
<main class="page">
  <div class="container">
    <h1>Blog</h1>
    <p class="lead">Short, practical strategy notes—built for operators.</p>

    <div class="blogwrap" style="margin-top:18px;">
      <div>
        {% for p in posts %}
          <div class="postcard" style="margin-bottom:12px;">
            <a href="{{ url_for('blog_post', slug=p.slug) }}">
              <div class="kicker">INSIGHT</div>
              <div class="title" style="font-weight:700; font-size:18px; margin-top:8px;">{{ p.title }}</div>
            </a>
            <div class="postmeta">{{ p.date }}</div>
            <div class="desc" style="color:var(--muted); margin-top:10px; line-height:1.6;">{{ p.excerpt }}</div>
          </div>
        {% endfor %}
      </div>

      <aside class="sidebar">
        <div class="kicker">START HERE</div>
        <div style="font-weight:700; margin-top:10px;">Want a diagnosis?</div>
        <div class="desc" style="color:var(--muted); margin-top:8px; line-height:1.6;">
          Request a Signal Audit and we’ll tell you what’s actually breaking conversions.
        </div>
        <div style="margin-top:12px;">
          <a class="btn" href="{{ url_for('start') }}">Request a Signal Audit</a>
        </div>

        """ + NEWSLETTER_BLOCK + r"""

        {% if ad_sidebar %}
          <div style="margin-top:12px;">{{ ad_sidebar|safe }}</div>
        {% endif %}
      </aside>
    </div>
  </div>
</main>
"""


BLOG_POST_BODY = r"""
<main class="page">
  <div class="container">
    <div class="blogwrap">
      <article class="postcard">
        <div class="kicker">BLOG POST</div>
        <h1 style="font-size:42px; margin-top:10px;">{{ post.title }}</h1>
        <div class="postmeta">{{ post.date }}</div>

        {% if ad_header %}
          <div style="margin-top:14px;">{{ ad_header|safe }}</div>
        {% endif %}

        <div class="postbody" style="margin-top:16px;">
          {{ post.html|safe }}
        </div>

        {% if ad_inarticle %}
          <div style="margin-top:18px;">{{ ad_inarticle|safe }}</div>
        {% endif %}

        <div style="margin-top:18px;">
          <a class="link" href="{{ url_for('blog') }}">← Back to Blog</a>
        </div>
      </article>

      <aside class="sidebar">
        <div class="kicker">MORE</div>
        <div class="desc" style="color:var(--muted); margin-top:10px; line-height:1.6;">
          Get short strategy dispatches and frameworks.
        </div>

        """ + NEWSLETTER_BLOCK + r"""

        {% if ad_sidebar %}
          <div style="margin-top:12px;">{{ ad_sidebar|safe }}</div>
        {% endif %}
      </aside>
    </div>
  </div>
</main>
"""


START_BODY = r"""
<main class="page">
  <div class="container">
    <h1>Request a Signal Audit</h1>
    <p class="lead">This is a diagnosis-first intake. If you’re a fit, we’ll respond with next steps.</p>

    <form method="post" action="{{ url_for('lead') }}">
      <div class="row2">
        <div>
          <label for="name">Name *</label>
          <input id="name" name="name" required placeholder="Your name" />
        </div>
        <div>
          <label for="email">Email *</label>
          <input id="email" name="email" type="email" required placeholder="you@company.com" />
        </div>
      </div>

      <div class="row2">
        <div>
          <label for="company">Company</label>
          <input id="company" name="company" placeholder="Company name" />
        </div>
        <div>
          <label for="website">Website (optional)</label>
          <input id="website" name="website" placeholder="https://..." />
        </div>
      </div>

      <div class="row2">
        <div>
          <label for="budget">Monthly marketing budget</label>
          <select id="budget" name="budget">
            <option value="">Select…</option>
            <option>$0–$500</option>
            <option>$500–$2,000</option>
            <option>$2,000–$5,000</option>
            <option>$5,000–$10,000</option>
            <option>$10,000+</option>
          </select>
        </div>
        <div>
          <label for="goal">Primary goal</label>
          <select id="goal" name="goal">
            <option value="">Select…</option>
            <option>More leads</option>
            <option>More sales</option>
            <option>Brand positioning</option>
            <option>Website conversion</option>
            <option>Full marketing system</option>
          </select>
        </div>
      </div>

      <div>
        <label for="message">What’s happening right now? *</label>
        <textarea id="message" name="message" required
          placeholder="Briefly describe the problem: traffic but no conversions, inconsistent leads, unclear positioning, etc."></textarea>
      </div>

      <input type="hidden" name="source" value="website_form" />
      <button class="btn" type="submit">Submit</button>
      <div class="lead" style="font-size:13px; opacity:.75; margin:0;">
        Or email: <a href="mailto:jordanmorrisr@gmail.com">jordanmorrisr@gmail.com</a> · IG:
        <a href="https://instagram.com/jsuprememarketing" target="_blank" rel="noopener">@jsuprememarketing</a>
      </div>
    </form>
  </div>
</main>
"""

THANKS_BODY = r"""
<main class="page">
  <div class="container">
    <h1>Received.</h1>
    <p class="lead">Your Signal Audit request has been submitted.</p>
    <div class="actions" style="margin-top:18px;">
      <a class="btn" href="{{ url_for('home') }}">Back to home</a>
      <a class="link" href="{{ url_for('blog') }}">Read Blog →</a>
    </div>
  </div>
</main>
"""

NEWSLETTER_THANKS_BODY = r"""
<main class="page">
  <div class="container">
    <h1>Subscribed.</h1>
    <p class="lead">You’re on the list. When we send, it’ll be short and actually useful.</p>
    <div class="actions" style="margin-top:18px;">
      <a class="btn" href="{{ url_for('blog') }}">Read the Blog</a>
      <a class="link" href="{{ url_for('home') }}">Back to home →</a>
    </div>
  </div>
</main>
"""

PRIVACY_BODY = r"""
<main class="page">
  <div class="container">
    <h1>Privacy Policy</h1>
    <p class="lead">
      We collect information you submit via forms (e.g., name, email, message) to respond to your request.
      We do not sell your personal information.
    </p>
    <p class="lead">
      Newsletter emails are stored only to send strategy dispatches. You can request removal anytime:
      <a href="mailto:jordanmorrisr@gmail.com">jordanmorrisr@gmail.com</a>
    </p>
  </div>
</main>
"""

TERMS_BODY = r"""
<main class="page">
  <div class="container">
    <h1>Terms of Service</h1>
    <p class="lead">
      Information on this site is provided for general purposes. Services are subject to written agreement.
      Results are not guaranteed; performance depends on offer, market, budget, and execution.
    </p>
  </div>
</main>
"""

# -----------------------
# Routes
# -----------------------
@app.route("/")
def home():
    return render_page(
        HOME_BODY,
        page="home",
        title=f"{APP_NAME} | Strategy-led Marketing",
        desc="Strategy-led marketing: positioning, systems, and distribution that converts.",
    )


@app.route("/insights")
def insights():
    return render_page(
        INSIGHTS_BODY,
        page="insights",
        title=f"{APP_NAME} | Insights",
        desc="Marketing insights on positioning, systems, and distribution.",
    )


@app.route("/blog")
def blog():
    # Render list via template vars
    body = render_template_string(
        BLOG_LIST_BODY,
        posts=BLOG_POSTS,
        ad_sidebar=adsense_ad_unit(ADSENSE_SLOT_SIDEBAR),
    )
    return render_page(
        body,
        page="blog",
        title=f"{APP_NAME} | Blog",
        desc="Practical marketing strategy notes: positioning, systems, and distribution.",
    )


@app.route("/blog/<slug>")
def blog_post(slug: str):
    post = get_post(slug)
    if not post:
        abort(404)

    body = render_template_string(
        BLOG_POST_BODY,
        post=post,
        ad_header=adsense_ad_unit(ADSENSE_SLOT_HEADER),
        ad_inarticle=adsense_ad_unit(ADSENSE_SLOT_INARTICLE),
        ad_sidebar=adsense_ad_unit(ADSENSE_SLOT_SIDEBAR),
    )
    return render_page(
        body,
        page="blog",
        title=f"{APP_NAME} | {post['title']}",
        desc=post["excerpt"],
    )


@app.route("/start")
def start():
    return render_page(
        START_BODY,
        page="start",
        title=f"{APP_NAME} | Request a Signal Audit",
        desc="Request a Signal Audit—diagnosis-first marketing for brands that want clarity and influence.",
    )


@app.route("/thank-you")
def thank_you():
    return render_page(
        THANKS_BODY,
        page="thank_you",
        title=f"{APP_NAME} | Thank You",
        desc="Submission received.",
    )


@app.route("/newsletter/thanks")
def newsletter_thanks():
    return render_page(
        NEWSLETTER_THANKS_BODY,
        page="insights",
        title=f"{APP_NAME} | Subscribed",
        desc="Newsletter subscribed.",
    )


@app.route("/privacy")
def privacy():
    return render_page(
        PRIVACY_BODY,
        page="privacy",
        title=f"{APP_NAME} | Privacy Policy",
        desc="Privacy policy for J Supreme Marketing.",
    )


@app.route("/terms")
def terms():
    return render_page(
        TERMS_BODY,
        page="terms",
        title=f"{APP_NAME} | Terms",
        desc="Terms of service for J Supreme Marketing.",
    )


@app.route("/api/lead", methods=["POST"])
def lead():
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip()
    message = (request.form.get("message") or "").strip()

    if not name or not email or not message:
        abort(400, "Missing required fields.")

    payload = {
        "name": name,
        "email": email,
        "company": (request.form.get("company") or "").strip(),
        "website": (request.form.get("website") or "").strip(),
        "budget": (request.form.get("budget") or "").strip(),
        "goal": (request.form.get("goal") or "").strip(),
        "message": message,
        "source": (request.form.get("source") or "website_form").strip(),
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "user_agent": request.headers.get("User-Agent", ""),
    }
    save_lead(payload)
    return redirect(url_for("thank_you"), code=302)


@app.route("/lead", methods=["POST"])
def lead_alias():
    return redirect(url_for("lead"), code=307)


@app.route("/api/newsletter", methods=["POST"])
def newsletter_subscribe():
    email = (request.form.get("email") or "").strip()
    if not email or "@" not in email:
        abort(400, "Enter a valid email.")

    payload = {
        "email": email,
        "source": (request.form.get("source") or "newsletter").strip(),
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "user_agent": request.headers.get("User-Agent", ""),
    }
    save_subscriber(payload)
    return redirect(url_for("newsletter_thanks"), code=302)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
