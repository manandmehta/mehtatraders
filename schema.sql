CREATE TABLE IF NOT EXISTS ticker 
(
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL UNIQUE, 
    name TEXT NOT NULL,
    exchange TEXT NOT NULL
)
GO 

CREATE TABLE IF NOT EXISTS  ticker_price
(
    id INTEGER PRIMARY KEY,
    ticker_id INTEGER REFERENCES stock(id),
    date NOT NULL,
    open NOT NULL,
    high NOT NULL,
    low NOT NULL,
    close NOT NULL,
    volume NOT NULL
)

GO
CREATE TABLE IF NOT EXISTS  strategy
(
    id INTEGER PRIMARY KEY,
    name NOT NULL
)

GO
CREATE TABLE IF NOT EXISTS  stock_strategy
(
    stock_id INTEGER REFERENCES ticker(id),
    strategy_id INTEGER REFERENCES strategy(id)
)