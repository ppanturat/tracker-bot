# 📈 Automated Stock Tracker (Discord Integration)

An automated financial monitoring tool that tracks a personalized stock watchlist and delivers daily performance snapshots directly to a private **Discord Server**. 
Designed to run autonomously in the cloud using **GitHub Actions** CI/CD pipelines, removing the need for a dedicated server or local machine.

Demo Screenshot:
![Demo Screenshot](images/demo-pic.png)

## 🚀 Key Features

* **Automated Daily Reporting:** Executes every morning (09:00 UTC+7) via a scheduled Cron job on GitHub Actions.
* **Risk-Based Categorization:**
    * **Bucket A:** Proven/Stable Stocks (Core Portfolio)
    * **Bucket B:** High-Growth/Speculative Stocks (Satellite Portfolio)
* **Trend Analysis:** Calculates real-time percentage movement (UP/DOWN) relative to the previous market close.
* **Buy Zone Alerts:** Triggers a high-priority alert if a stock drops below a specific target price.
* **Discord Integration:** Uses Webhooks for instant, reliable, and formatted push notifications without complex API keys.

## 🛠️ Tech Stack

* **Language:** Python 3.9
* **Market Data:** `yfinance` (Yahoo Finance API)
* **Automation:** GitHub Actions (Ubuntu VM)
* **Notifications:** Discord Webhook API
* **Data Handling:** Pandas & JSON

## ⚙️ Logic & Architecture

1.  **Trigger:** GitHub Actions initializes a virtual environment on a daily schedule.
2.  **Fetch:** The Python script pulls real-time market data for the defined watchlist.
3.  **Analyze:** * Compares `Current Price` vs `Target Price`.
    * Calculates day-over-day percentage change.
    * Sorts assets into Risk Buckets.
4.  **Broadcast:** Formats the data into a clean report and POSTs it to the specific Discord Channel via Webhook.

## 📦 Installation & Setup

If you want to run this yourself:

1.  **Clone the Repo**
    ```bash
    git clone [https://github.com/your-username/watchlist-stock-tracker.git](https://github.com/your-username/watchlist-stock-tracker.git)
    ```

2.  **Get a Discord Webhook**
    * Go to your Discord Server settings → Integrations → Webhooks.
    * Create a new Webhook and copy the **Webhook URL**.

3.  **Configure Secrets (for GitHub Actions)**
    * Go to Repo Settings → Secrets and variables → Actions.
    * Create a new secret named `DISCORD_URL`.
    * Paste your Webhook URL there.

4.  **Run Locally (Optional)**
    * Install dependencies: `pip install yfinance requests`
    * Set the environment variable and run:
    ```bash
    export DISCORD_URL="your_webhook_url_here"
    python watchlist.py
    ```

## ⚠️ Disclaimer
This project is for educational purposes and personal tracking only. It is not financial advice.
