#!/usr/bin/env python3
"""
build.py – Liest templates/style.json + templates/index.html + templates/viewer.html,
scannt docs/, generiert catalog.json und die statische Website in site/.
"""

import json
import shutil
import pathlib
import re
from datetime import datetime

ROOT       = pathlib.Path(__file__).parent
DOCS_DIR   = ROOT / "docs"
SITE_DIR   = ROOT / "site"
CATALOG    = ROOT / "catalog.json"
STYLE_FILE = ROOT / "templates" / "style.json"
INDEX_TMPL = ROOT / "templates" / "index.html"
VIEWER_TMPL= ROOT / "templates" / "viewer.html"


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def slug(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name)


def load_style() -> dict:
    with open(STYLE_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    # Kommentar-Keys herausfiltern
    return {k: v for k, v in raw.items() if not k.startswith("/")}


def style_vars(style: dict) -> dict:
    """Flacht style.json in ein einfaches Platzhalter-Dict um."""
    c = style["colors"]
    f = style["fonts"]
    s = style["spacing"]
    t = style["typography"]
    a = style["animation"]
    n = style["noise"]
    return {
        "FONT_URL":            f["google_fonts_url"],
        "FONT_DISPLAY":        f["display"],
        "FONT_MONO":           f["mono"],
        "COLOR_BG":            c["bg"],
        "COLOR_SURFACE":       c["surface"],
        "COLOR_BORDER":        c["border"],
        "COLOR_ACCENT":        c["accent"],
        "COLOR_ACCENT2":       c["accent2"],
        "COLOR_TEXT":          c["text"],
        "COLOR_MUTED":         c["muted"],
        "COLOR_HOVER_SURFACE": c["hover_surface"],
        "FONT_SIZE_BODY":      t["body_size"],
        "FONT_SIZE_H1":        t["h1_size"],
        "FONT_SIZE_H2":        t["h2_size"],
        "FONT_SIZE_LABEL":     t["label_size"],
        "FONT_SIZE_SUMMARY":   t["summary_size"],
        "FONT_SIZE_BADGE":     t["badge_size"],
        "FONT_SIZE_NAV_TITLE": t["nav_title_size"],
        "HEADER_PADDING":      s["header_padding"],
        "MAIN_PADDING":        s["main_padding"],
        "MAX_WIDTH":           s["max_width"],
        "ITEM_PADDING":        s["item_padding"],
        "BLOCK_GAP":           s["block_gap"],
        "ANIM_DURATION":       a["duration"],
        "ANIM_EASING":         a["easing"],
        "ANIM_DELAY_STEP":     a["delay_step"],
        "NOISE_OPACITY":       n["opacity"],
    }


def render(template_path: pathlib.Path, variables: dict) -> str:
    """Ersetzt alle {{PLATZHALTER}} im Template."""
    text = template_path.read_text(encoding="utf-8")
    for key, value in variables.items():
        text = text.replace(f"{{{{{key}}}}}", str(value))
    return text


def load_description(versuch_path: pathlib.Path, versuch: str) -> dict:
    desc_file = versuch_path / "description.json"
    if desc_file.exists():
        with open(desc_file, encoding="utf-8") as f:
            return json.load(f)
    return {"title": versuch, "summary": ""}


# ── Catalog aufbauen ──────────────────────────────────────────────────────────

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

def build_content_html(catalog: list) -> str:
    if not catalog:
        return """
    <div class="empty-state">
      <h2>Noch keine Versuche</h2>
      <p>Lege Ordner in <code>docs/</code> an und füge <code>protokoll.pdf</code> hinzu.</p>
    </div>"""

    blocks = []
    for p in catalog:
        items = []
        for v in p["versuche"]:
            summary_text = v["description"].get("summary", "")
            summary_html = f'<div class="versuch-summary">{summary_text}</div>' if summary_text else ""
            items.append(f"""
        <li class="versuch-item">
          <div>
            <div class="versuch-name">
              <a href="viewer/{p['slug']}/{v['slug']}/">{v['name']}</a>
            </div>
            {summary_html}
          </div>
          <span class="versuch-badge">PDF</span>
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

    return "\n".join(blocks)


def generate_site(catalog: list, vars: dict):
    SITE_DIR.mkdir(exist_ok=True)

    total_versuche = sum(len(p["versuche"]) for p in catalog)
    total_praktika = len(catalog)

    # ── index.html ────────────────────────────────────────────────────────────
    index_vars = {
        **vars,
        "UPDATED":         datetime.now().strftime("%d.%m.%Y"),
        "TOTAL_VERSUCHE":  str(total_versuche),
        "TOTAL_PRAKTIKA":  str(total_praktika),
        "CONTENT":         build_content_html(catalog),
    }
    index_html = render(INDEX_TMPL, index_vars)
    (SITE_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print("✓ index.html geschrieben")

    # ── Viewer-Seiten ─────────────────────────────────────────────────────────
    for p in catalog:
        for v in p["versuche"]:
            viewer_dir = SITE_DIR / "viewer" / p["slug"] / v["slug"]
            viewer_dir.mkdir(parents=True, exist_ok=True)

            summary = v["description"].get("summary", "") or "Kein Beschreibungstext vorhanden."
            viewer_vars = {
                **vars,
                "PRAKTIKUM_NAME": p["praktikum"],
                "VERSUCH_NAME":   v["name"],
                "SUMMARY":        summary,
            }
            viewer_html = render(VIEWER_TMPL, viewer_vars)
            (viewer_dir / "index.html").write_text(viewer_html, encoding="utf-8")
            print(f"  ✓ Viewer: {p['praktikum']}/{v['name']}")


# ── Einstiegspunkt ────────────────────────────────────────────────────────────

def main():
    print("\n🔨 Starte Build-Prozess …\n")

    print("🎨 Lade style.json …")
    style = load_style()
    vars = style_vars(style)

    if SITE_DIR.exists():
        for item in SITE_DIR.iterdir():
            if item.name != "pdfs":
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

    print("📂 Scanne docs/ …")
    catalog = build_catalog()

    print("\n📋 Schreibe catalog.json …")
    with open(CATALOG, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print("\n🌐 Generiere Website …")
    generate_site(catalog, vars)

    total = sum(len(p["versuche"]) for p in catalog)
    print(f"\n✅ Fertig – {total} Versuche in {len(catalog)} Praktika\n")


if __name__ == "__main__":
    main()
