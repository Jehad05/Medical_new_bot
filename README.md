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
In your Railway project:
- Go to **Variables** tab
- Add `BOT_TOKEN` and `CHAT_ID`

### Step 4 — Deploy
Railway will automatically detect Python and deploy your bot. It will run 24/7.

---

## 📁 Project Structure

```
medical-news-bot/
├── main.py          # Entry point + Telegram sender
├── fetcher.py       # RSS fetching from all sources
├── scheduler.py     # Hourly job runner
├── requirements.txt # Python dependencies
├── .env.example     # Environment variables template
├── .gitignore       # Protects sensitive files
└── README.md        # This file
```

## ⚙️ Configuration

To add or remove news sources, edit the `SOURCES` dictionary in `fetcher.py`:

```python
SOURCES = {
    "PubMed": "https://pubmed.ncbi.nlm.nih.gov/rss/...",
    "WHO": "https://www.who.int/rss-feeds/news-english.xml",
    "BBC Health": "https://feeds.bbci.co.uk/news/health/rss.xml",
    # Add more sources here
}
```

To change the sending interval, edit `scheduler.py`:
```python
schedule.every(1).hours.do(job_func)   # Every hour
schedule.every(30).minutes.do(job_func) # Every 30 minutes
schedule.every().day.at("08:00").do(job_func) # Every day at 8 AM
```

## 📄 License
MIT
