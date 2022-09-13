import sqlite3, config
import alpaca_trade_api as tradeapi


connection = sqlite3.connect(config.DB)
statement = connection.cursor()

api = tradeapi.REST(config.API_KEY,config.API_SECRET,config.API_BASE_URL)
assets = api.list_assets()

for asset in assets:
    try:
        #print (asset.name)
        if asset.status == 'active' and asset.tradable:
            statement.execute('INSERT INTO ticker(symbol,name,exchange) values (?,?,?)',(asset.symbol,asset.name,asset.exchange))
    except Exception as e:
        print(asset.symbol)
        print(e)


connection.commit()