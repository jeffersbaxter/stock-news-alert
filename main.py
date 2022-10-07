import math
import os
import requests as requests
import datetime as dt
from twilio.rest import Client

STOCK = "TSLA"
COMPANY_NAME = "Tesla Inc"
ALPHA_VANTAGE_KEY = os.environ.get("ALPHA_VANTAGE_KEY")

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

parameters = {
    "function": "TIME_SERIES_DAILY",
    "symbol": STOCK,
    "apikey": ALPHA_VANTAGE_KEY
}
res = requests.get(STOCK_ENDPOINT, params=parameters)
res.raise_for_status()
data = res.json()
today = dt.datetime.today()
yesterday = f"{today - dt.timedelta(days=1)}".split(" ")[0]
day_before = f"{today - dt.timedelta(days=2)}".split(" ")[0]
day_before_close = float(data["Time Series (Daily)"][day_before]["4. close"])
yesterday_close = float(data["Time Series (Daily)"][yesterday]["4. close"])
delta_close = yesterday_close / day_before_close
delta_close_float = float('{:.2f}'.format(100 * (delta_close - 1)))
abs_close = math.fabs(delta_close_float)

# TWILIO
account_sid = "AC8b7e43c80171723d09f130606303abf6"
auth_token = os.environ.get("AUTH_TOKEN")
client = Client(account_sid, auth_token)
from_phone = os.environ.get("FROM_TWILIO_PHONE")
to_phone = os.environ.get("TO_TWILIO_PHONE")

if delta_close_float > 0:
    trend = f"{STOCK}: 🔺{abs_close}%"
elif delta_close_float < 0:
    trend = f"{STOCK}: 🔻{abs_close}%"
else:
    trend = f"{STOCK}: has not changed"


def create_message(msg_title, msg_description):
    return client.messages.create(
        body=f"{trend}\n{msg_title}\n\n{msg_description}",
        from_=from_phone,
        to=to_phone
    )


news_key = os.environ.get("NEWS_KEY")

if delta_close >= 1.05 or delta_close <= .95:
    news_params = {
        "q": STOCK,
        "from": today - dt.timedelta(days=2),
        "language": "en",
        "apiKey": news_key
    }
    news_res = requests.get(NEWS_ENDPOINT, params=news_params)
    news_res.raise_for_status()
    news_data = news_res.json()

    [create_message(a["title"], a["description"]) for a in news_data["articles"][:3]]
