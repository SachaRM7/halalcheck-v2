# HalalCheck

HalalCheck is a community halal verification platform built as a FastAPI backend with a lightweight Telegram Mini App / PWA frontend.

## What is included

- FastAPI API for products, restaurants, personal tracker, alerts, and moderation
- SQLite database with WAL mode and seeded demo data
- Ingredient parser with E-number and Arabic label dictionaries
- MiniMax-compatible AI explainer fallback for ingredient analysis
- Lightweight web client suitable for Telegram Mini App or PWA delivery
- Telegram bot entry point that opens the web app

## Project layout

```
app/        FastAPI app, routes, services, SQLite setup
web/        Vanilla HTML/CSS/JS frontend + service worker
telegram/   Telegram bot launcher
tests/      API smoke tests
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open http://localhost:8000 or http://localhost:8000/web/index.html

## Run tests

```bash
python -m pytest tests/test_api.py -q
```

## Telegram bot

```bash
export TELEGRAM_BOT_TOKEN=your_token
export HALALCHECK_WEBAPP_URL=https://your-domain/web/index.html
python telegram/bot.py
```

## Seed/import more products

```bash
python app/data/seed/fssai_mui_import.py data.csv
```

Expected CSV headers:

```
barcode,name,brand,ingredients,halal_status,certification_body,cert_number,source_url
```
