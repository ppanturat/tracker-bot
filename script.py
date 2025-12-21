import os
import yfinance as yf
import requests
import urllib.parse
from datetime import datetime, timezone, timedelta

APIKEY = os.environ.get('APIKEY')     #CallMeBot API Key
LOGFILE = 'sent_log.json'       #Json file to remember alerts

#list of stocks i want to keep track of (K = stock symbol | V = target price)
#first 5 i classify in Bucket A, and the other 5 is B <<< u can edit this, but dont forget to edit the code below
watchlist = {'ETN': 225.00, 'SYM': 30.00, 'ISRG': 275.00, 'PLTR': 80.00, 'CDNS': 220.00,
             'SDGR': 15.00, 'PACB': 1.50, 'RKLB': 20.00, 'S': 7.00, 'IONQ': 15.00}

#function to send message to messenger using CallMeBot
def send_alert_message(message):
    quote = urllib.parse.quote(message)
    url = f'https://api.callmebot.com/facebook/send.php?apikey={APIKEY}&text={quote}'
    try:
        requests.get(url)
        print('message sent')
    except Exception as e:
        print(f'ERROR: {e}')

messages = ['', '']    #for price report (index 0 = Bucket A, index 1 = Bucket B)
alert = ""             #for alert message
count = 0              #count index

#check each stock current price, and create a message to send
for ticker, targetPrice in watchlist.items():
    stock = yf.Ticker(ticker)
    info = stock.info
    currentPrice = info.get('currentPrice')
    previousPrice = info.get('previousClose')

    #check whether the price is going up or down
    text = f"{ticker}: {currentPrice}   "
    if currentPrice > previousPrice:        #price go up
        percent = ((currentPrice / previousPrice) * 100) - 100
        text += f"🔼{percent:.2f}%\n"
    elif currentPrice < previousPrice:      #go down
        percent = ((previousPrice / currentPrice) * 100) - 100
        text += f"🔽{percent:.2f}%\n"

    #check whether the stock is in bucket A or B
    if(count < 5):
        messages[0] += text
    else:
        messages[1] += text

    #make an alert message if the stock is in the buyzone
    if currentPrice < watchlist[ticker]:
        alert += f"""Alert!🚨 {ticker} is in the Buy Zone now. 
        Current Price: {currentPrice} 
        Buy Zone: {watchlist[ticker]}
        """
    
    count += 1

#compile final message
final_message = f"""Price Report ({datetime.now(tz=timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M")})
\n----------------- Bucket A: Proven Stocks (No Risk) ------------------
{messages[0]}
----------------- Bucket B: Diamonds(?) (High-Risk) ------------------
{messages[1]}
""" + alert

#send the message to user
send_alert_message(final_message)