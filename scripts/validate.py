#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
errors = []


def fail(message):
    errors.append(message)


def load(name):
    try:
        return json.loads((ROOT / "content" / name).read_text())
    except Exception as exc:
        fail(f"cannot read {name}: {exc}")
        return []


def validate_schema(value, schema, where):
    expected = schema.get("type")
    types = expected if isinstance(expected, list) else ([expected] if expected else [])
    checks = {"array": list, "object": dict, "string": str, "integer": int, "boolean": bool, "null": type(None)}
    if types and not any(isinstance(value, checks[t]) and not (t == "integer" and isinstance(value, bool)) for t in types):
        fail(f"schema type mismatch at {where}: expected {types}")
        return
    if "enum" in schema and value not in schema["enum"]: fail(f"schema enum mismatch at {where}")
    if "const" in schema and value != schema["const"]: fail(f"schema const mismatch at {where}")
    if isinstance(value, str) and "pattern" in schema and not re.match(schema["pattern"], value): fail(f"schema pattern mismatch at {where}")
    if isinstance(value, (list, str)) and len(value) < schema.get("minItems", schema.get("minLength", 0)): fail(f"schema length mismatch at {where}")
    if isinstance(value, int) and value < schema.get("minimum", value): fail(f"schema minimum mismatch at {where}")
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value): validate_schema(item, schema["items"], f"{where}[{index}]")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value: fail(f"schema required field missing at {where}.{key}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties: fail(f"schema additional field at {where}.{key}")
        for key, child in properties.items():
            if key in value: validate_schema(value[key], child, f"{where}.{key}")


disciplines = load("disciplines.json")
projects = load("projects.json")
achievements = load("achievements.json")
integrations = load("integrations.json")
discipline_slugs = {d.get("slug") for d in disciplines}

for stem, value in (("disciplines", disciplines), ("projects", projects), ("achievements", achievements)):
    schema = json.loads((ROOT / "schemas" / f"{stem}.schema.json").read_text())
    validate_schema(value, schema, stem)

for d in disciplines:
    required = {"slug","title","shortDescription","status","publishedWorkCount","showInFilters","showInNavigation","landingPage","externalDomain"}
    if set(d) != required: fail(f"discipline {d.get('slug')} schema mismatch")
    if d.get("status") not in {"incubating","active","archived"}: fail(f"bad discipline status: {d.get('slug')}")
    if d.get("status") == "incubating" and (d.get("showInFilters") or d.get("showInNavigation")): fail(f"incubating discipline exposed: {d.get('slug')}")
    if d.get("showInNavigation") and d.get("publishedWorkCount", 0) < 3: fail(f"navigation discipline has fewer than 3 works: {d.get('slug')}")

for p in projects:
    if p.get("discipline") not in discipline_slugs: fail(f"unknown discipline in {p.get('slug')}")
    if p.get("status") == "published":
        if not p.get("publicPermission"): fail(f"published project lacks public permission: {p.get('slug')}")
        if not p.get("liveUrl") or not p.get("proofs"): fail(f"published project lacks result/proof: {p.get('slug')}")
    if p.get("featured") and p.get("status") != "published": fail(f"non-published project is featured: {p.get('slug')}")

for a in achievements:
    for key in ("date","context","verifiedAt","source"):
        if not a.get(key): fail(f"achievement {a.get('id')} lacks {key}")
    if a.get("featured") and a.get("status") != "verified": fail(f"unverified achievement is featured: {a.get('id')}")
    if "fide" in a.get("title", "").lower() and "FIDE" not in a.get("title", ""): fail(f"FIDE format missing in {a.get('id')}")

if integrations:
    ml = integrations["mailerlite"]
    if ml["enabled"] and not ml["formAction"].startswith("https://"): fail("MailerLite enabled without HTTPS form action")
    tally = integrations["tally"]
    if tally["enabled"] and "tally.so" not in tally["embedUrl"]: fail("Tally enabled without tally.so embed")
    cf = integrations["cloudflareAnalytics"]
    if cf["enabled"] and not cf["token"]: fail("Cloudflare Analytics enabled without token")

if not DIST.exists(): fail("dist does not exist; run build.py")
manifest_path = DIST / "public-manifest.json"
if not manifest_path.exists(): fail("public manifest missing")
else:
    manifest = set(json.loads(manifest_path.read_text()))
    actual = {str(p.relative_to(DIST)) for p in DIST.rglob("*") if p.is_file() and p.name != "public-manifest.json"}
    listed = manifest - {"public-manifest.json"}
    if actual != listed:
        fail(f"manifest mismatch: unlisted={sorted(actual-listed)} missing={sorted(listed-actual)}")

for path in DIST.rglob("*") if DIST.exists() else []:
    if not path.is_file(): continue
    if path.suffix.lower() not in {".html",".css",".js",".json",".xml",".txt",".svg",".png",".jpg",".jpeg",""}: fail(f"unexpected public file type: {path}")
    if path.suffix.lower() in {".html",".css",".js",".json",".xml",".txt",".svg",""}:
        text = path.read_text(errors="ignore")
        if re.search(r"\bSAT\b|1609", text, re.I): fail(f"excluded SAT content in {path.relative_to(DIST)}")
        if re.search(r"TODO|REPLACE_ME|YOUR_[A-Z_]", text): fail(f"placeholder in {path.relative_to(DIST)}")
        if path.suffix == ".html":
            if '<link rel="canonical"' not in text: fail(f"canonical missing: {path.relative_to(DIST)}")
            for asset in re.findall(r'(?:src|href)="/?(assets/(?:styles\.css|app\.js))([^"]*)"', text):
                if "?v=" not in asset[1]: fail(f"cache version missing in {path.relative_to(DIST)}: {asset[0]}")
            for link in re.findall(r'(?:src|href)="([^"]*)"', text):
                parsed = urlparse(link)
                if parsed.scheme or parsed.netloc or link.startswith(("#", "mailto:")):
                    continue
                clean = parsed.path.lstrip("/")
                if clean.startswith("assets/"):
                    target = DIST / clean
                elif clean.endswith("/"):
                    target = DIST / clean / "index.html" if clean else DIST / "index.html"
                else:
                    continue
                if not target.exists(): fail(f"broken local link {clean} in {path.relative_to(DIST)}")

if errors:
    print("VALIDATION FAILED")
    for error in errors: print(f"- {error}")
    sys.exit(1)
print(f"VALIDATION OK: {len(list(DIST.rglob('*')))} paths checked")

