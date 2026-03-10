# Praktikumsarchiv

Persönliches Archiv aller Laborpraktika – statisch gebaut mit `build.py`, gehostet auf Cloudflare Pages.

## Ordnerstruktur

```
docs/
└── ThermischeGrundoperationen/
    ├── Destillation/
    │   ├── protokoll.pdf          ← Pflicht
    │   └── description.json       ← Optional (wird von KI generiert, falls fehlt)
    └── Kristallisation/
        └── protokoll.pdf
```

## Neuen Versuch hinzufügen

1. Ordner `docs/<Praktikum>/<VersuchsName>/` anlegen
2. `protokoll.pdf` hineinkopieren
3. Optional: `description.json` anlegen (sonst KI-generiert beim nächsten Build)
4. Committen & pushen → GitHub Actions baut und deployed automatisch

## description.json Format

```json
{
  "title": "Destillation",
  "summary": "In diesem Versuch wurde eine binäre Mischung durch einfache Destillation getrennt...",
  "generated": false
}
```

## Setup

### 1. GitHub Secrets setzen

Im GitHub Repo unter *Settings → Secrets and variables → Actions*:

| Secret | Beschreibung |
|--------|-------------|
| `CLOUDFLARE_API_TOKEN` | Cloudflare Dashboard → API Tokens |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Dashboard → Overview |
| `GOOGLE_API_KEY` | Google AI Studio → API Keys *(optional)* |

### 2. Cloudflare Pages Projekt anlegen

- Cloudflare Dashboard → Pages → *Create a project*
- Mit GitHub verbinden, **kein** Build-Command nötig (GitHub Actions übernimmt das)
- Projektname muss mit `projectName` in `build.yml` übereinstimmen

### 3. Lokal testen

```bash
pip install google-generativeai
python build.py
# → site/ enthält die fertige Website
```
