from lib2to3.pygram import Symbols
import sqlite3, config
import alpaca_trade_api as tradeapi


connection = sqlite3.connect(config.DB)
statement = connection.cursor()

api = tradeapi.REST(config.API_KEY,config.API_SECRET,config.API_BASE_URL)


connection = sqlite3.connect(config.DB)
connection.row_factory = sqlite3.Row
statement = connection.cursor()

assets = api.list_assets()

statement.execute(""" SELECT id,symbol,name FROM ticker order by symbol """)
rows = statement.fetchall()

insert_statement = connection.cursor()

symbols=[]
stock_dict = {}
for row in rows:
    symbol = row['symbol']
    symbols.append(symbol)
    stock_dict[symbol] = row['id']

chunk_size = 200
for i in range(0,len(symbols),chunk_size):
    symbol_chunk = symbols[i:i+chunk_size]
    
    bars = api.get_bars(symbol_chunk,'1Day',start='2021-09-14',end='2022-09-14')

    for bar in bars:
        print(f"Processing symbol {bar.S}")
        stock_id = stock_dict[bar.S]
        try:
         insert_statement.execute(
            """INSERT INTO ticker_price(ticker_id,date,open,high,low,close,volume) values (?,?,?,?,?,?,?)"""
         , (stock_dict[bar.S],bar.t.date(),bar.o,bar.h,bar.l,bar.c,bar.v))
        except Exception as e:
            print(bar.S)
            print(e)
        
    connection.commit()