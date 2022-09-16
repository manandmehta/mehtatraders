from operator import truediv
import sqlite3, config
from urllib.request import Request
from datetime import date,datetime
import alpaca_trade_api as tradeapi
from polygon import RESTClient as polygonapi
import pandas as pd




polygon_client = polygonapi(config.POLYGON_API_SECRET)
minute_bars = polygon_client.get_aggs('INTC',1,'hour','2022-09-13','2022-09-13')
#print(minute_bars)

df = pd.DataFrame(minute_bars)
#print(df)


df['date'] = pd.to_datetime(df['timestamp'],unit='ms')
#df['local1'] = df['date'].dt.tz_convert('America/Los_Angeles')
#df['local2'] = df['date'].dt.tz_convert('US/Pacific')
#df['tz'] = df['local'].dt.tz
df['date'].dt.tz_localize('US/Pacific')
df['tz'] = df['date'].dt.tz
print(df)
