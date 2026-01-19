import os
import requests
import yfinance as yf
from datetime import datetime, timezone, timedelta
from supabase import create_client

# --- CONFIGURATION ---
STOCK_DISCORD_URL = os.environ.get('STOCK_DISCORD_URL')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- FETCH STOCKS FROM DB ---
response = supabase.table('stocks').select("*").execute()
db_stocks = response.data 

bucket_a = []
bucket_b = []

for item in db_stocks:
    # Clean the data (remove spaces, make uppercase)
    bucket_val = item['bucket'].strip().upper()
    
    stock_data = {
        'symbol': item['symbol'],
        'target': float(item['target_price'])
    }
    
    if bucket_val == 'A':
        bucket_a.append(stock_data)
    else:
        bucket_b.append(stock_data)

# --- HELPER FUNCTIONS ---
def send_discord_message(message):
    data = {"content": message}
    requests.post(STOCK_DISCORD_URL, json=data)

def process_bucket(stock_list):
    report_text = ""
    alert_text = ""
    
    if not stock_list:
        return "_(Empty)_", ""

    for stock in stock_list:
        ticker = stock['symbol']
        target_price = stock['target']
        
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.fast_info
            currentPrice = info.last_price
            previousPrice = info.previous_close
            
            # Fallback
            if currentPrice is None:
                info = ticker_obj.info
                currentPrice = info.get('currentPrice')
                previousPrice = info.get('previousClose')

            if currentPrice is None:
                report_text += f"• **{ticker}**: ⚠️ No Data\n"
                continue

            # Calculate movement
            percent = ((currentPrice / previousPrice) * 100) - 100
            if currentPrice > previousPrice:
                emoji = f"🟢 +{percent:.2f}%"
            elif currentPrice < previousPrice:
                emoji = f"🔴 {percent:.2f}%"
            else:
                emoji = "⚪ 0.00%"

            # Bold the Ticker, keep price normal
            report_text += f"• **{ticker}**: {currentPrice:.2f} ({emoji})\n"

            # Check for Buy Zone
            if currentPrice < target_price:
                alert_text += f"🚨 **{ticker}** is in Buy Zone! (${currentPrice:.2f} < ${target_price})\n"

        except Exception:
            report_text += f"• **{ticker}**: ⚠️ Error\n"

    return report_text, alert_text

# --- MAIN EXECUTION ---
msg_a, alert_a = process_bucket(bucket_a)
msg_b, alert_b = process_bucket(bucket_b)

timestamp = datetime.now(tz=timezone(timedelta(hours=7))).strftime("%d %b %Y %H:%M")

final_message = f"""# 📈 Price Report ({timestamp})

### 🛡️ Proven Stocks (Bucket A)
{msg_a}

### 💎 High Risk (Bucket B)
{msg_b}

{alert_a}{alert_b}
"""

if len(final_message) > 2000:
    send_discord_message(final_message[:2000])
    send_discord_message(final_message[2000:])
else:
    send_discord_message(final_message)