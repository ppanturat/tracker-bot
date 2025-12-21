# 📈 Automated Stock Monitor

An automated monitoring system that tracks specific market assets and delivers a daily performance snapshot directly to Facebook Messenger. Designed to run completely in the cloud using **GitHub Actions**.

## 🚀 Features

* **Automated Daily Reporting:** Runs automatically every morning (09:00 UTC+7) via CI/CD pipelines.
* **Smart Categorization:** Splits assets into "Bucket A" (Stable/Proven) and "Bucket B" (High Growth/Risk) for clearer analysis.
* **Trend Analysis:** Calculates daily movement (UP/DOWN percentages) against the previous close.
* **Buy Zone Alerts:** Triggers a special alarm if a stock drops below a predefined target price.
* **Mobile Push:** Uses CallMeBot API to bridge Python logic with Facebook Messenger.

## 🛠️ Tech Stack

* **Language:** Python 3.9
* **Data Source:** `yfinance` (Yahoo Finance API)
* **Automation:** GitHub Actions (Cron Scheduler)
* **Notification:** REST API (CallMeBot / Messenger)
* **Data Handling:** JSON & Pandas

## ⚙️ How It Works

1.  **Trigger:** GitHub Actions wakes up the virtual machine on a schedule (Cron).
2.  **Fetch:** The Python script queries live market data for the defined watchlist.
3.  **Analyze:** Logic checks current prices against target thresholds and previous close.
4.  **Report:** The system compiles a formatted summary and pushes it via HTTP Request to the user's device.

## 📂 Project Structure
```text
├── .github/workflows/daily_run.yml  # The Automation Logic (Cron)
├── script.py                        # The Core Python Script
├── requirements.txt                 # Dependencies (yfinance, etc.)
└── README.md                        # Documentation
```

## ⚠️ Disclaimer
This tool is for educational and personal tracking purposes only. It does not constitute financial advice.
