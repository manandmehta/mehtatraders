import sqlite3, config
from urllib.request import Request
from datetime import date
import alpaca_trade_api as tradeapi
from polygon import RESTClient as polygonapi
import pandas as pd

connection = sqlite3.connect(config.DB)
connection.row_factory = sqlite3.Row
statement = connection.cursor()

statement.execute(""" 
    SELECT ss.stock_id, t.name,  t.symbol
    FROM stock_strategy ss
    INNER JOIN strategy s
	INNER JOIN ticker t
    ON ss.strategy_id = s.id AND ss.stock_id = t.id
     WHERE s.name = 'opening_range_breakout'
""")
stocks = statement.fetchall()
symbols = [stock['symbol'] for stock in stocks]
print(symbols)

api = tradeapi.REST(config.API_KEY,config.API_SECRET,config.API_BASE_URL)

current_date= '2022-09-14' 
start_minute_bar = f"{current_date} 06:30:00"
end_minute_bar = f"{current_date} 06:45:00"

symbol = 'AAPL'

polygon_client = polygonapi(config.POLYGON_API_SECRET)
minute_bars = polygon_client.get_aggs(symbol,1,'minute','2022-09-14','2022-09-14')
minute_bars_df = pd.DataFrame(minute_bars)

minute_bars_df['date'] = pd.to_datetime(minute_bars_df['timestamp'],unit='ms',utc=True).dt.tz_convert('US/Pacific')
#print(minute_bars_df)

# Filter first 15 minutes of bars
opening_range_mask = (minute_bars_df['date'] >= start_minute_bar) & (minute_bars_df.date < end_minute_bar)
opening_range_bars = minute_bars_df.loc[opening_range_mask]

print("------- opening range bars -------")
print(opening_range_bars)
opening_range_low = opening_range_bars['low'].min()
opening_range_high = opening_range_bars['high'].max()
opening_range = opening_range_high - opening_range_low

print(f"Opening Range Low [{opening_range_low}]")
print(f"Opening Range high [{opening_range_high}]")
print(f"Opening Range [{opening_range}]")

after_opening_range_mask = minute_bars_df.date >= end_minute_bar
after_opening_range_bars = minute_bars_df.loc[after_opening_range_mask]
print("------- After opening range bars -------")
print(after_opening_range_bars)

after_opening_range_breakdown = after_opening_range_bars[after_opening_range_bars['close'] < opening_range_low]

orders = api.list_orders(status='all',limit = 500, after = f'${current_date}T13.30')
existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']

if not after_opening_range_breakdown.empty:
    print("------- Opening Range Breakout Bars -------")
    print(after_opening_range_breakdown)
    # First entry where we found opening range breakout occuring
    # We will make the closing price as stop loss limit
    limit_price = after_opening_range_breakdown.iloc[0]['close']
    print(f"Limit Price => {limit_price}")
    print(f"Selling short order for {limit_price}, closed_below {opening_range_low} at {after_opening_range_breakdown.iloc[0]}")

    if symbol not in existing_order_symbols:
        try:
            api.submit_order (
                symbol=symbol,
                side='sell',
                type='limit',
                qty='100',
                time_in_force='day',
                order_class='bracket',
                limit_price=limit_price,
                take_profit=dict(
                    limit_price=limit_price - opening_range
                ),
                stop_loss = dict(
                    stop_price=limit_price + opening_range
                )
            )
        except Exception as e:
            print(f"Could not submit order {e}")
    else:
        print(f"Already an order for [{symbol}], skipping")
