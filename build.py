#!/usr/bin/env python3
"""
build.py – Liest die docs/-Ordnerstruktur, generiert catalog.json
und die statische Website in site/.
"""

import json
import shutil
import pathlib
import re
from datetime import datetime

# ── Pfade ────────────────────────────────────────────────────────────────────
ROOT      = pathlib.Path(__file__).parent
DOCS_DIR  = ROOT / "docs"
SITE_DIR  = ROOT / "site"
CATALOG   = ROOT / "catalog.json"

# ── Hilfsfunktionen ──────────────────────────────────────────────────────────

def slug(name: str) -> str:
    """Erstellt einen URL-sicheren Dateinamen."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name)


def load_description(versuch_path: pathlib.Path, versuch: str) -> dict:
    """Lädt description.json, falls vorhanden – sonst leere Beschreibung."""
    desc_file = versuch_path / "description.json"
    if desc_file.exists():
        with open(desc_file, encoding="utf-8") as f:
            return json.load(f)
    return {"title": versuch, "summary": ""}


# ── Catalog aufbauen ─────────────────────────────────────────────────────────

def build_catalog() -> list:
    catalog = []

    if not DOCS_DIR.exists():
        print(f"⚠ docs/-Ordner nicht gefunden: {DOCS_DIR}")
        return catalog

    for praktikum_dir in sorted(DOCS_DIR.iterdir()):
        if not praktikum_dir.is_dir():
            continue

        praktikum_name = praktikum_dir.name
        versuche = []

        for versuch_dir in sorted(praktikum_dir.iterdir()):
            if not versuch_dir.is_dir():
                continue

            versuch_name = versuch_dir.name
            pdf_file = versuch_dir / "protokoll.pdf"

            if not pdf_file.exists():
                print(f"  ⚠ Kein protokoll.pdf in {versuch_dir} – übersprungen")
                continue

            print(f"  → {praktikum_name} / {versuch_name}")
            description = load_description(versuch_dir, versuch_name)

            # PDF in site/ kopieren
            dest_dir = SITE_DIR / "pdfs" / slug(praktikum_name) / slug(versuch_name)
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pdf_file, dest_dir / "protokoll.pdf")

            versuche.append({
                "name": versuch_name,
                "slug": slug(versuch_name),
                "pdf": f"pdfs/{slug(praktikum_name)}/{slug(versuch_name)}/protokoll.pdf",
                "description": description
            })

        if versuche:
            catalog.append({
                "praktikum": praktikum_name,
                "slug": slug(praktikum_name),
                "versuche": versuche
            })

    return catalog


# ── HTML generieren ───────────────────────────────────────────────────────────

INDEX_HTML = """\
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Praktikumsarchiv</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:       #0e0f0f;
      --surface:  #161718;
      --border:   #2a2b2d;
      --accent:   #c8f06e;
      --accent2:  #6ec8f0;
      --text:     #e8e6e1;
      --muted:    #7a7872;
      --font-display: 'DM Serif Display', Georgia, serif;
      --font-mono:    'DM Mono', monospace;
    }

    html { scroll-behavior: smooth; }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-mono);
      font-size: 14px;
      line-height: 1.7;
      min-height: 100vh;
    }

    /* Noise overlay */
    body::before {
      content: '';
      position: fixed;
      inset: 0;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
      pointer-events: none;
      z-index: 9999;
      opacity: 0.4;
    }

    header {
      padding: 4rem 2rem 2rem;
      max-width: 900px;
      margin: 0 auto;
      border-bottom: 1px solid var(--border);
    }

    header .label {
      font-size: 11px;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: var(--accent);
      margin-bottom: 0.75rem;
    }

    header h1 {
      font-family: var(--font-display);
      font-size: clamp(2.5rem, 6vw, 4.5rem);
      font-weight: 400;
      line-height: 1.1;
      color: var(--text);
      letter-spacing: -0.02em;
    }

    header h1 em {
      font-style: italic;
      color: var(--accent);
    }

    header .meta {
      margin-top: 1rem;
      color: var(--muted);
      font-size: 12px;
    }

    main {
      max-width: 900px;
      margin: 0 auto;
      padding: 3rem 2rem 6rem;
    }

    .praktikum-block {
      margin-bottom: 3.5rem;
      animation: fadeUp 0.5s ease both;
    }

    .praktikum-block:nth-child(1) { animation-delay: 0.05s; }
    .praktikum-block:nth-child(2) { animation-delay: 0.10s; }
    .praktikum-block:nth-child(3) { animation-delay: 0.15s; }
    .praktikum-block:nth-child(4) { animation-delay: 0.20s; }
    .praktikum-block:nth-child(5) { animation-delay: 0.25s; }

    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(16px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    .praktikum-header {
      display: flex;
      align-items: baseline;
      gap: 1rem;
      margin-bottom: 1rem;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid var(--border);
    }

    .praktikum-header h2 {
      font-family: var(--font-display);
      font-size: 1.6rem;
      font-weight: 400;
      color: var(--text);
    }

    .praktikum-header .count {
      font-size: 11px;
      color: var(--muted);
      letter-spacing: 0.1em;
    }

    .versuch-list {
      list-style: none;
      display: grid;
      gap: 2px;
    }

    .versuch-item {
      display: grid;
      grid-template-columns: 1fr auto;
      align-items: start;
      gap: 1rem;
      padding: 0.75rem 1rem;
      background: var(--surface);
      border: 1px solid transparent;
      border-radius: 4px;
      transition: border-color 0.15s, background 0.15s;
    }

    .versuch-item:hover {
      border-color: var(--border);
      background: #1c1d1f;
    }

    .versuch-name a {
      color: var(--accent2);
      text-decoration: none;
      font-weight: 500;
      font-size: 13px;
      letter-spacing: 0.02em;
      transition: color 0.15s;
    }

    .versuch-name a:hover {
      color: var(--accent);
    }

    .versuch-name a::before {
      content: '↗ ';
      font-size: 10px;
      opacity: 0.6;
    }

    .versuch-summary {
      margin-top: 0.25rem;
      font-size: 12px;
      color: var(--muted);
      line-height: 1.5;
      max-width: 60ch;
    }

    .versuch-badge {
      font-size: 10px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
      padding: 2px 6px;
      border: 1px solid var(--border);
      border-radius: 2px;
      white-space: nowrap;
      margin-top: 2px;
    }

    .versuch-badge.ai {
      color: var(--accent);
      border-color: var(--accent);
      opacity: 0.7;
    }

    footer {
      text-align: center;
      padding: 2rem;
      color: var(--muted);
      font-size: 11px;
      border-top: 1px solid var(--border);
      letter-spacing: 0.05em;
    }

    .empty-state {
      text-align: center;
      padding: 5rem 2rem;
      color: var(--muted);
    }

    .empty-state h2 {
      font-family: var(--font-display);
      font-size: 2rem;
      font-weight: 400;
      margin-bottom: 1rem;
    }
  </style>
</head>
<body>

<header>
  <div class="label">Persönliches Archiv</div>
  <h1>Praktikums<em>archiv</em></h1>
  <div class="meta">Zuletzt aktualisiert: {updated} &nbsp;·&nbsp; {total_versuche} Versuche in {total_praktika} Praktika</div>
</header>

<main>
{content}
</main>

<footer>
  Generiert von build.py &nbsp;·&nbsp; Gehostet auf Cloudflare Pages
</footer>

</body>
</html>
"""

VIEWER_HTML = """\
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{versuch_name} – {praktikum_name}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:      #0e0f0f;
      --surface: #161718;
      --border:  #2a2b2d;
      --accent:  #c8f06e;
      --accent2: #6ec8f0;
      --text:    #e8e6e1;
      --muted:   #7a7872;
      --font-display: 'DM Serif Display', Georgia, serif;
      --font-mono:    'DM Mono', monospace;
    }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-mono);
      font-size: 14px;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }

    nav {
      display: flex;
      align-items: center;
      gap: 1.5rem;
      padding: 0.75rem 1.5rem;
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      flex-shrink: 0;
    }

    nav a.back {
      color: var(--muted);
      text-decoration: none;
      font-size: 12px;
      letter-spacing: 0.05em;
      transition: color 0.15s;
    }

    nav a.back:hover { color: var(--accent); }
    nav a.back::before { content: '← '; }

    nav .breadcrumb {
      font-size: 12px;
      color: var(--muted);
    }

    nav .breadcrumb span {
      color: var(--text);
    }

    nav .title {
      margin-left: auto;
      font-family: var(--font-display);
      font-size: 1.1rem;
      color: var(--accent2);
    }

    .info-bar {
      padding: 0.6rem 1.5rem;
      background: var(--bg);
      border-bottom: 1px solid var(--border);
      font-size: 12px;
      color: var(--muted);
      flex-shrink: 0;
      display: flex;
      gap: 2rem;
      align-items: center;
    }

    .info-bar .summary {
      flex: 1;
      line-height: 1.5;
    }

    .info-bar a.dl {
      color: var(--accent);
      text-decoration: none;
      white-space: nowrap;
      border: 1px solid var(--accent);
      padding: 4px 10px;
      border-radius: 3px;
      font-size: 11px;
      letter-spacing: 0.08em;
      transition: background 0.15s;
    }

    .info-bar a.dl:hover {
      background: var(--accent);
      color: var(--bg);
    }

    iframe {
      flex: 1;
      width: 100%;
      border: none;
      background: #fff;
    }
  </style>
</head>
<body>

<nav>
  <a class="back" href="../../..">Zurück zur Übersicht</a>
  <div class="breadcrumb">{praktikum_name} &nbsp;/&nbsp; <span>{versuch_name}</span></div>
  <div class="title">{versuch_name}</div>
</nav>

<div class="info-bar">
  <div class="summary">{summary}</div>
  <a class="dl" href="protokoll.pdf" download>↓ PDF</a>
</div>

<iframe src="protokoll.pdf" title="Protokoll {versuch_name}"></iframe>

</body>
</html>
"""


def generate_site(catalog: list):
    SITE_DIR.mkdir(exist_ok=True)

    total_versuche = sum(len(p["versuche"]) for p in catalog)
    total_praktika = len(catalog)

    # ── index.html ────────────────────────────────────────────────────────────
    if not catalog:
        content_html = """
        <div class="empty-state">
          <h2>Noch keine Versuche</h2>
          <p>Lege Ordner in <code>docs/</code> an und füge <code>protokoll.pdf</code> hinzu.</p>
        </div>"""
    else:
        blocks = []
        for p in catalog:
            items = []
            for v in p["versuche"]:
                desc = v["description"]
                summary_text = desc.get("summary", "")
                is_ai = desc.get("generated", False)
                badge = '<span class="versuch-badge ai">KI</span>' if is_ai else '<span class="versuch-badge">Protokoll</span>'
                summary_html = f'<div class="versuch-summary">{summary_text}</div>' if summary_text else ""
                items.append(f"""
            <li class="versuch-item">
              <div>
                <div class="versuch-name">
                  <a href="viewer/{p['slug']}/{v['slug']}/">{v['name']}</a>
                </div>
                {summary_html}
              </div>
              {badge}
            </li>""")

            count = len(p["versuche"])
            noun = "Versuch" if count == 1 else "Versuche"
            blocks.append(f"""
      <div class="praktikum-block">
        <div class="praktikum-header">
          <h2>{p['praktikum']}</h2>
          <span class="count">{count} {noun}</span>
        </div>
        <ul class="versuch-list">{''.join(items)}
        </ul>
      </div>""")

        content_html = "\n".join(blocks)

    index_out = SITE_DIR / "index.html"
    index_out.write_text(
        INDEX_HTML.format(
            updated=datetime.now().strftime("%d.%m.%Y"),
            total_versuche=total_versuche,
            total_praktika=total_praktika,
            content=content_html
        ),
        encoding="utf-8"
    )
    print(f"✓ index.html geschrieben")

    # ── Viewer-Seiten ─────────────────────────────────────────────────────────
    for p in catalog:
        for v in p["versuche"]:
            viewer_dir = SITE_DIR / "viewer" / p["slug"] / v["slug"]
            viewer_dir.mkdir(parents=True, exist_ok=True)

            summary = v["description"].get("summary", "")
            html = VIEWER_HTML.format(
                praktikum_name=p["praktikum"],
                versuch_name=v["name"],
                summary=summary if summary else "Kein Beschreibungstext vorhanden."
            )
            (viewer_dir / "index.html").write_text(html, encoding="utf-8")
            print(f"  ✓ Viewer: {p['praktikum']}/{v['name']}")


# ── Einstiegspunkt ────────────────────────────────────────────────────────────

def main():
    print("\n🔨 Starte Build-Prozess …\n")

    # Altes site/ aufräumen (außer pdfs/)
    if SITE_DIR.exists():
        for item in SITE_DIR.iterdir():
            if item.name != "pdfs":
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

    print("📂 Scanne docs/ …")
    catalog = build_catalog()

    print(f"\n📋 Schreibe catalog.json …")
    with open(CATALOG, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"\n🌐 Generiere Website …")
    generate_site(catalog)

    total = sum(len(p["versuche"]) for p in catalog)
    print(f"\n✅ Fertig – {total} Versuche in {len(catalog)} Praktika\n")


if __name__ == "__main__":
    main()
