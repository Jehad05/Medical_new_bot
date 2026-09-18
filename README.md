# 🏥 Medical News Bot

A Telegram bot that automatically sends medical news every hour from multiple trusted sources.

## 📰 News Sources
- **PubMed** — Latest medical research
- **WHO** — World Health Organization updates
- **BBC Health** — General health news

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/your-username/medical-news-bot.git
cd medical-news-bot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
cp .env.example .env
```
Edit `.env` and fill in your values:
```
BOT_TOKEN=your_telegram_bot_token
CHAT_ID=your_channel_or_group_id
```

#### How to get BOT_TOKEN
1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the instructions
3. Copy the token you receive

#### How to get CHAT_ID
- For a **channel**: add `@username_bot` as admin, then send a message and visit:
  `https://api.telegram.org/bot<TOKEN>/getUpdates`
- For a **group**: same steps above, the ID will be negative (e.g. `-1001234567890`)

### 4. Run locally
```bash
python main.py
```

---

## ☁️ Deploy on Railway

### Step 1 — Create a Railway account
Go to [railway.app](https://railway.app) and sign up (GitHub login recommended)

### Step 2 — Create a new project
- Click **New Project**
- Select **Deploy from GitHub repo**
- Connect your repository

### Step 3 — Add environment variables
In your Railway project, go to **Variables** tab and add:
- `BOT_TOKEN`
- `CHAT_ID`
- `DB_PATH` = `/data/seen.db`

### Step 4 — Add a Volume (required for deduplication)
1. Open your service card
2. Go to **Volumes** tab
3. Click **+ New Volume**
4. Set **Mount Path** = `/data`
5. Redeploy

> ⚠️ Without the Volume, the database resets on every deploy and the bot will send duplicate news.

### Step 5 — Deploy
Railway will automatically detect Python and deploy your bot. It will run 24/7.

---

## 📁 Project Structure

```
medical-news-bot/
├── main.py          # Entry point + Telegram + Health server
├── fetcher.py       # RSS fetching + formatting
├── scheduler.py     # Hourly job + daily cleanup
├── storage.py       # SQLite deduplication
├── config.py        # Central configuration
├── requirements.txt # Python dependencies
├── Procfile         # Process definition
├── railway.json     # Railway deploy config
├── .env.example     # Environment variables template
├── .gitignore       # Protects sensitive files
└── README.md        # This file
```

## ⚙️ Configuration

All settings are in `config.py`. Key variables:

| Variable | Default | Description |
|---|---|---|
| `MAX_PER_SOURCE` | 3 | Max articles per source per run |
| `MAX_AGE_HOURS` | 24 | Skip articles older than N hours |
| `DB_PATH` | `/data/seen.db` | SQLite database path |
| `SEEN_RETENTION_DAYS` | 7 | Days to keep dedup records |

To add or remove news sources, edit `SOURCES` in `config.py`.

## 🏥 Health Check

The bot runs a lightweight HTTP server on `PORT` (default 8080):
- `GET /` → returns `OK`
- `GET /stats` → returns DB size and total seen count

## 🗄️ Deduplication

SQLite database at `/data/seen.db` tracks sent article links.
- Automatically cleaned up after 7 days
- Hard cap at 10,000 rows
- Daily VACUUM at 03:00 UTC to reclaim disk space

> ⚠️ **Never commit `.env`** — it contains your BOT_TOKEN.
> If leaked, revoke it immediately via @BotFather → `/revoke`.

## 📄 License
MIT
