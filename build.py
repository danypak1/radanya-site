#!/usr/bin/env python3
import html
import json
import shutil
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
STATIC = ROOT / "static"
DIST = ROOT / "dist"
VERSION = "20261012.2"
SITE = "https://radanya.com"
GITHUB_PAGES_PATH = "/radanya-site/"


def load(name):
    return json.loads((CONTENT / name).read_text())


disciplines = load("disciplines.json")
projects = load("projects.json")
achievements = load("achievements.json")
integrations = load("integrations.json")
published = [p for p in projects if p["status"] == "published" and p["publicPermission"]]
disc_by_slug = {d["slug"]: d for d in disciplines}

if DIST.exists():
    shutil.rmtree(DIST)
DIST.mkdir()


def esc(value):
    return html.escape(str(value), quote=True)


def layout(title, description, body, path="/", extra_head=""):
    canonical = SITE + (path if path != "/" else "/")
    analytics = ""
    cf = integrations["cloudflareAnalytics"]
    if cf["enabled"]:
        analytics = f'<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon=\'{{"token":"{esc(cf["token"])}"}}\'></script>'
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<base id="site-base" href="&#47;"><script>if(location.hostname.endsWith(".github.io"))document.getElementById("site-base").setAttribute("href","{GITHUB_PAGES_PATH}");</script>
<title>{esc(title)}</title><meta name="description" content="{esc(description)}"><link rel="canonical" href="{canonical}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:type" content="website"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{SITE}/assets/og.jpg">
<meta name="theme-color" content="#132a25"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/styles.css?v={VERSION}">{extra_head}{analytics}</head>
<body><a class="skip" href="#main">Skip to content</a><header class="site-header"><div class="wrap header-inner"><a class="brand" href="/"><span>D</span> Daniil Pak</a><button class="menu-button" data-menu-button aria-label="Open navigation" aria-expanded="false">☰</button><nav data-nav><a href="/work/">Work</a><a href="/about/">About</a><a href="/services/">Services</a><a href="/notes/">Notes</a><a class="nav-cta" href="/start/">Start a project</a></nav></div></header>
<main id="main">{body}</main><footer class="footer"><div class="wrap footer-grid"><div><div class="kicker">Useful things, built clearly.</div><p>Educational products, chess and whatever earns its place next.</p></div><div><a href="mailto:hello@radanya.com">hello@radanya.com</a><br><a href="/privacy/">Privacy</a></div></div></footer><script src="/assets/app.js?v={VERSION}" defer></script></body></html>'''
    return page.replace('href="/', 'href="').replace('src="/', 'src="')


def write_page(path, content):
    target = DIST / path
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(content)


def proof_cards(items):
    return "".join(f'''<article class="proof"><strong>{esc(a["value"])}</strong><span><b>{esc(a["title"])}</b><br>{esc(a["context"])}</span><a class="verify" href="{esc(a["source"]["url"])}" target="_blank" rel="noopener">Verify ↗</a></article>''' for a in items)


def project_cards(items):
    cards = []
    for p in items:
        image = f'<div class="project-image"><img src="/{esc(p["image"])}" alt="" loading="lazy"></div>' if p["image"] else ""
        dark = " dark" if p["discipline"] == "chess" else ""
        cards.append(f'''<a class="project-card{dark}" data-project="{esc(p["discipline"])}" href="/work/{esc(p["slug"])}/">{image}<span class="project-label">{esc(disc_by_slug[p["discipline"]]["title"])}</span><h3>{esc(p["title"])}</h3><p>{esc(p["summary"])}</p><span class="arrow">View project →</span></a>''')
    return "".join(cards)


def signup_panel(default_group="build-notes"):
    ml = integrations["mailerlite"]
    if not ml["enabled"]:
        return '''<div class="panel"><span class="eyebrow">Occasional notes</span><h3>Only when there is something worth sending.</h3><p>Build notes, useful releases and selected RadChess lessons. The mailing list is being connected; until then, email me with the topic you want.</p><a class="button primary" href="mailto:hello@radanya.com?subject=Updates%20%E2%80%94%20build%20notes">Join by email</a></div>'''
    checks = "".join(f'<label><input type="checkbox" name="groups[]" value="{esc(g)}"> {esc(g.replace("-", " ").title())}</label>' for g in ml["groups"])
    return f'''<form class="panel" action="{esc(ml["formAction"])}" method="post"><span class="eyebrow">Occasional notes</span><h3>Choose what reaches you.</h3><label>Email<input required type="email" name="email" autocomplete="email"></label>{checks}<button class="button primary" type="submit">Subscribe</button></form>'''


featured = [a for a in achievements if a["featured"] and a["status"] == "verified"][:3]
featured_projects = [p for p in published if p["featured"]][:3]
home = f'''<section class="hero"><div class="wrap hero-grid"><div class="hero-copy"><div class="eyebrow">Daniil Pak · Builder & chess player</div><h1>I make hard things easier to practise.</h1><p class="lead">I build educational web products that turn dense material into clear, interactive practice — and I document the same thinking through RadChess.</p><div class="actions"><a class="button primary" href="/work/">Explore my work</a><a class="button" href="/start/">Start a project</a></div></div><div class="hero-portrait"><img src="/assets/daniil.png" alt="Daniil Pak"></div></div></section>
<section class="section"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Verified, not inflated</div><h2>Proof before pitch.</h2></div><p>Every number has a format, a date and a source. Online ratings and official ratings never share the same label.</p></div><div class="proof-grid">{proof_cards(featured)}</div><p><a class="verify" href="/achievements/">See the full verified record →</a></p></div></section>
<section class="section alt"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Selected work</div><h2>Products with a job to do.</h2></div><p>Only finished, public work appears here. New disciplines earn a place through a completed project, not an empty promise.</p></div><div class="project-grid">{project_cards(featured_projects)}</div></div></section>
<section class="section"><div class="wrap split"><div><div class="eyebrow">How I work</div><h2>One complete slice before scale.</h2><p class="lead">I turn a real learner problem into the smallest usable experience, test it on a phone, and only then expand the system.</p><a class="button" href="/services/">See the process</a></div>{signup_panel()}</div></section>'''
write_page(".", layout("Daniil Pak — Educational products and RadChess", "Daniil Pak builds clear, interactive educational products and the RadChess learning brand.", home))

active_filters = [d for d in disciplines if d["status"] == "active" and d["showInFilters"]]
filter_buttons = '<button class="filter" data-filter="all" aria-pressed="true">All</button>' + "".join(f'<button class="filter" data-filter="{esc(d["slug"])}" aria-pressed="false">{esc(d["title"])}</button>' for d in active_filters)
work = f'''<section class="case-hero"><div class="wrap"><div class="eyebrow">Work</div><h1>Finished work.<br>Clear evidence.</h1><p class="lead">A growing record of products and creative directions. Incubating ideas stay private until there is something real to use, watch or hear.</p></div></section><section class="section"><div class="wrap"><div class="filters">{filter_buttons}</div><div class="project-grid">{project_cards(published)}</div></div></section>'''
write_page("work", layout("Work — Daniil Pak", "Published educational products and chess projects by Daniil Pak.", work, "/work/"))

for p in published:
    proofs = "".join(f'<li><a href="{esc(x["url"])}" target="_blank" rel="noopener">{esc(x["label"])} ↗</a> <small>({esc(x["type"])})</small></li>' for x in p["proofs"])
    body = f'''<section class="case-hero"><div class="wrap"><div class="eyebrow">{esc(disc_by_slug[p["discipline"]]["title"])}</div><h1>{esc(p["title"])}</h1><p class="lead">{esc(p["summary"])}</p><div class="case-meta"><span><b>Role</b> · {esc(p["role"])}</span><span><b>Published</b> · {esc(p["date"])}</span></div></div></section><section class="section"><div class="wrap split"><div><h2>The result</h2><p class="lead">{esc(p["outcome"])}</p><a class="button primary" href="{esc(p["liveUrl"])}">{esc(p["cta"])} ↗</a></div><div><div class="eyebrow">Evidence</div><h3>Public proof</h3><ul>{proofs}</ul><p class="notice">Claims on this page are limited to public, verifiable outcomes. Private learner and client data stays private.</p></div></div></section>'''
    write_page(f'work/{p["slug"]}', layout(f'{p["title"]} — Daniil Pak', p["summary"], body, f'/work/{p["slug"]}/'))

achievement_rows = "".join(f'''<article class="achievement"><div class="achievement-value">{esc(a["value"])}</div><div><h3>{esc(a["title"])}</h3><p>{esc(a["context"])}</p><small>Period: {esc(a["date"])} · verified {esc(a["verifiedAt"])}</small></div><a class="verify" href="{esc(a["source"]["url"])}" target="_blank" rel="noopener">Verify ↗</a></article>''' for a in achievements if a["status"] == "verified")
achievements_page = f'''<section class="case-hero"><div class="wrap"><div class="eyebrow">Verified record</div><h1>Every claim has a source.</h1><p class="lead">Official FIDE ratings, shipped products and approved client work are labelled separately and dated.</p></div></section><section class="section"><div class="wrap achievement-list">{achievement_rows}</div></section>'''
write_page("achievements", layout("Achievements — Daniil Pak", "A dated and sourced record of chess and product achievements.", achievements_page, "/achievements/"))

services = '''<section class="case-hero"><div class="wrap"><div class="eyebrow">Services</div><h1>Educational products people can actually use.</h1><p class="lead">I help turn course material, expert knowledge and practice routines into focused web experiences.</p></div></section><section class="section"><div class="wrap"><div class="service-grid"><article class="service"><b>01</b><h3>Learning product design</h3><p>Structure the learner journey, feedback loop and smallest valuable release.</p></article><article class="service"><b>02</b><h3>Interactive course sites</h3><p>Fast, phone-ready practice with clear progress and minimal buyer effort.</p></article><article class="service"><b>03</b><h3>Protected delivery</h3><p>Keep answer keys and paid value out of the public deployment while preserving a simple experience.</p></article></div></div></section><section class="section alt"><div class="wrap split"><div><div class="eyebrow">Process</div><h2>Diagnose. Slice. Ship. Verify.</h2></div><div class="timeline"><article><small>01 · Diagnose</small><h3>Define the learner and the observable problem.</h3></article><article><small>02 · Vertical slice</small><h3>Build one complete module through content, mobile use and delivery.</h3></article><article><small>03 · Scale</small><h3>Expand only after the first slice survives real use.</h3></article></div></div></section>'''
write_page("services", layout("Educational product services — Daniil Pak", "Design and development of interactive educational web products.", services, "/services/"))

about = f'''<section class="case-hero"><div class="wrap"><div class="eyebrow">About</div><h1>I learn by building the system.</h1><p class="lead">I’m Daniil Pak — a student, chess player and product builder. I care about the moment a difficult idea becomes something a person can practise without friction.</p></div></section><section class="section"><div class="wrap split"><div><h2>What connects the work</h2></div><div class="prose"><p>Chess, educational software and future creative directions may look unrelated. The common thread is the same: make the thinking visible, reduce the distance between action and feedback, and prove claims with working results.</p><p>RadChess applies that approach to practical chess. My learning-product work applies it to courses and study systems. New directions join this site only after a finished public work exists.</p><a class="button" href="/achievements/">Verified achievements</a></div></div></section><section class="section alt"><div class="wrap"><div class="proof-grid">{proof_cards(featured)}</div></div></section>'''
write_page("about", layout("About Daniil Pak", "About Daniil Pak: product builder, student and FIDE-rated chess player.", about, "/about/"))

notes = '''<section class="case-hero"><div class="wrap"><div class="eyebrow">Notes</div><h1>Notes only when the work earns one.</h1><p class="lead">No content calendar for its own sake. This is where useful lessons from building, testing and teaching will appear.</p></div></section><section class="section"><div class="wrap"><div class="notice"><b>No public notes yet.</b><br>The page exists as a stable destination, but it will not be filled with placeholder articles.</div></div></section>'''
write_page("notes", layout("Notes — Daniil Pak", "Occasional notes about educational products and practical learning.", notes, "/notes/"))

tally = integrations["tally"]
if tally["enabled"]:
    form = f'<iframe title="Project brief" src="{esc(tally["embedUrl"])}" width="100%" height="820" frameborder="0"></iframe>'
else:
    form = '''<div class="panel"><h3>The structured brief is being connected.</h3><p>Until then, email the answers to these five questions: who is the learner, what should they be able to do, what material exists, when is it needed, and what budget range is realistic?</p><a class="button primary" href="mailto:work@radanya.com?subject=Educational%20product%20brief">Email the brief</a></div>'''
start = f'''<section class="case-hero"><div class="wrap"><div class="eyebrow">Start a project</div><h1>Bring the learner problem, not a feature list.</h1><p class="lead">A useful first conversation starts with who needs to learn what, and how we will know the product helped.</p></div></section><section class="section"><div class="wrap split"><div><h2>A good fit</h2><ul><li>A course that needs interactive practice.</li><li>Expert material that feels too dense online.</li><li>A paid learning product that needs safer delivery.</li><li>A small vertical slice before a larger build.</li></ul><p>Not a fit: speculative platforms with no identified learner or content owner.</p></div>{form}</div></section>'''
write_page("start", layout("Start a project — Daniil Pak", "Send a short brief for an educational web product.", start, "/start/"))

privacy = '''<section class="case-hero"><div class="wrap"><div class="eyebrow">Privacy</div><h1>Collect less. Explain it clearly.</h1></div></section><section class="section"><div class="wrap prose"><p>This site does not sell personal data. Newsletter subscriptions are processed by MailerLite only after the visitor selects an interest and confirms the subscription. Project briefs are processed by Tally when that integration is enabled.</p><h2>What is collected</h2><p>Email addresses and selected interests for subscriptions; the information a visitor chooses to include in a project brief; privacy-preserving aggregate site events.</p><h2>Why</h2><p>To send the requested topic, respond to a project enquiry and understand whether the site is useful.</p><h2>Your choices</h2><p>Every newsletter includes an unsubscribe link. For access or deletion requests, email <a href="mailto:privacy@radanya.com">privacy@radanya.com</a>.</p><h2>External services</h2><p>Published projects and proof links may lead to GitHub, FIDE, YouTube or other clearly labelled external services with their own privacy policies.</p></div></section>'''
write_page("privacy", layout("Privacy — Daniil Pak", "Privacy information for radanya.com.", privacy, "/privacy/"))

not_found = '''<section class="case-hero"><div class="wrap"><div class="eyebrow">404</div><h1>This path has not earned a page.</h1><p class="lead">Try the finished work instead.</p><a class="button primary" href="/work/">View work</a></div></section>'''
(DIST / "404.html").write_text(layout("Not found — Daniil Pak", "Page not found.", not_found, "/404.html"))

(DIST / "assets").mkdir()
for asset in ("styles.css", "app.js", "favicon.svg", "daniil.png", "radchess-threat-scan.jpg", "og.jpg"):
    shutil.copy2(STATIC / asset, DIST / "assets" / asset)
(DIST / "CNAME").write_text("radanya.com\n")
(DIST / ".nojekyll").write_text("")
(DIST / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://radanya.com/sitemap.xml\n")
urls = ["/", "/work/", "/achievements/", "/services/", "/notes/", "/about/", "/start/", "/privacy/"] + [f'/work/{p["slug"]}/' for p in published]
(DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f'<url><loc>{SITE}{u}</loc></url>' for u in urls) + '</urlset>')
manifest = sorted(str(p.relative_to(DIST)) for p in DIST.rglob("*") if p.is_file())
(DIST / "public-manifest.json").write_text(json.dumps(manifest, indent=2))
print(f"Built {len(manifest)} public files")

