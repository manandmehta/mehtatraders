import sqlite3, config
from urllib.request import Request
from datetime import date
import alpaca_trade_api as tradeapi
from polygon import RESTClient as polygonapi
import pandas as pd
import tulipy as ti

connection = sqlite3.connect(config.DB)
connection.row_factory = sqlite3.Row
statement = connection.cursor()

statement.execute(""" 
    SELECT ss.stock_id, t.name,  t.symbol
    FROM stock_strategy ss
    INNER JOIN strategy s
	INNER JOIN ticker t
    ON ss.strategy_id = s.id AND ss.stock_id = t.id
     WHERE s.name = 'bollinger_bands'
""")
stocks = statement.fetchall()
symbols = [stock['symbol'] for stock in stocks]
#print(symbols)

api = tradeapi.REST(config.API_KEY,config.API_SECRET,config.API_BASE_URL)

current_date= '2022-09-15' 
start_minute_bar = f"{current_date} 06:30:00"
end_minute_bar = f"{current_date} 08:58:00"

symbol = 'INTC'

polygon_client = polygonapi(config.POLYGON_API_SECRET)
minute_bars = polygon_client.get_aggs(symbol,1,'minute','2022-09-15','2022-09-15')
minute_bars_df = pd.DataFrame(minute_bars)

minute_bars_df['date'] = pd.to_datetime(minute_bars_df['timestamp'],unit='ms',utc=True).dt.tz_convert('US/Pacific')
#print(minute_bars_df)

# Filter pre market
market_open_mask = (minute_bars_df['date'] >= start_minute_bar) & (minute_bars_df.date <= end_minute_bar)
market_open_bars = minute_bars_df.loc[market_open_mask]
print(market_open_bars)

orders = api.list_orders(status='all',limit = 500) # TODO: Place after date here
existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']

# Bollinger bands need 20 frames at least
if len(market_open_bars) >= 20:
    closes = market_open_bars.close.values
    print(closes)

    # standard is 2 deviation
    lower,middle,upper = ti.bbands(closes,20,2)

    print(lower)


    current_candle = market_open_bars.iloc[-1]  # last candle
    previous_candle = market_open_bars.iloc[-2] # second to last candle
    
    # Trade enter criteria
    # Current candle closed above lower bollinger band (Green Candle)
    # Previous candle closed below lower bollinger band (Red Candle)
    if current_candle.close > lower[-1] and previous_candle.close < lower[-2]:
        print(f" {symbol} Closed above the lower bollinger band")
        print(current_candle)

        if symbol not in existing_order_symbols:
            limit_price  = round(current_candle.close,2)
            candle_range = current_candle.high - current_candle.low

            try:
                print('--------')
                print(f"candle range is {candle_range}")
                print(f"placing order for [INTCl at limit_price [{limit_price}]")
                print(f"takeProfit [{round(limit_price + (candle_range * 3),2)}]")
                print(f"stop_loss [{round(previous_candle.low,2)}]")

                api.submit_order (
                    symbol=symbol,
                    side='buy',
                    type='limit',
                    qty='100',
                    time_in_force='day',
                    order_class='bracket',
                    limit_price=limit_price,
                    take_profit=dict(
                        limit_price=round(limit_price + (candle_range * 3),2)
                    ),
                    stop_loss = dict(
                        stop_price=round(previous_candle.low,2)
                    )
                )
            except Exception as e:
                print(f"Could not submit order {e}")
        else:
            print(f"Already an order for [{symbol}], skipping")

"""
print("------- opening range bars -------")
print(opening_range_bars)
opening_range_low = round(opening_range_bars['low'].min(),2)
opening_range_high = round(opening_range_bars['high'].max(),2)
opening_range = round(opening_range_high - opening_range_low,2)

print(f"Opening Range Low [{opening_range_low}]")
print(f"Opening Range high [{opening_range_high}]")
print(f"Opening Range [{opening_range}]")

after_opening_range_mask = minute_bars_df.date >= end_minute_bar
after_opening_range_bars = minute_bars_df.loc[after_opening_range_mask]
print("------- After opening range bars -------")
print(after_opening_range_bars)

after_opening_range_breakout = after_opening_range_bars[after_opening_range_bars['close'] > opening_range_high]

orders = api.list_orders(status='all',limit = 500) # TODO: Place after date here
existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']

if not after_opening_range_breakout.empty:
    print("------- Opening Range Breakout Bars -------")
    print(after_opening_range_breakout)
    # First entry where we found opening range breakout occuring
    # We will make the closing price as stop loss limit
    limit_price = after_opening_range_breakout.iloc[0]['close']

    #print(f"Placing order for {limit_price}, closed_above {opening_range_high} at {after_opening_range_breakout.iloc[0]}")

    if symbol not in existing_order_symbols:
        try:
            print(f"limit_price [{limit_price}]")
            print(f"takeProfit [{limit_price + opening_range}]")
            print(f"stop_loss [{limit_price - opening_range}]")

            api.submit_order (
                symbol=symbol,
                side='buy',
                type='limit',
                qty='100',
                time_in_force='day',
                order_class='bracket',
                limit_price=limit_price,
                take_profit=dict(
                    limit_price=round(limit_price + opening_range,2)
                ),
                stop_loss = dict(
                    stop_price=round(limit_price-opening_range,2)
                )
            )
        except Exception as e:
            print(f"Could not submit order {e}")
    else:
        print(f"Already an order for [{symbol}], skipping")
"""