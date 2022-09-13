import sqlite3, config
from urllib.request import Request
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from datetime import date


app = FastAPI()

templates = Jinja2Templates(directory="templates")

@app.get("/")
def index(request: Request):
    # If no filter, default is false
    stock_filter = request.query_params.get('filter',False)

    connection = sqlite3.connect(config.DB)
    
    # Return dictionary instead of rows
    connection.row_factory = sqlite3.Row
    statement = connection.cursor()

    if stock_filter == 'new_intraday_highs':
        statement.execute("""
            SELECT * FROM 
            (
	            SELECT  t.symbol,t.name,ticker_id,max(close),date
		        FROM 
			    ticker_price tp
                INNER JOIN ticker t 
                ON tp.ticker_id = t.id
                GROUP BY tp.ticker_id
                ORDER BY symbol	
	        ) WHERE date = ? 
        """,(date.today().isoformat(),)) 
    else:
        statement.execute("""
            SELECT id,symbol,name FROM ticker order by symbol
        """)
        
    rows = statement.fetchall()

    return templates.TemplateResponse("index.html", {"request": request, "stocks":rows})


@app.get("/stock/{symbol}")
def index(request: Request, symbol):
    connection = sqlite3.connect(config.DB)
    # Return dictionary instead of rows
    connection.row_factory = sqlite3.Row
    statement = connection.cursor()

    statement.execute("""
        SELECT * FROM strategy
    """)
    strategies = statement.fetchall()

    statement.execute("""
        SELECT id, symbol, name FROM ticker WHERE symbol = ?
    """, (symbol,))
    row = statement.fetchone()

    print(row['id'])

    statement.execute("""
        SELECT * FROM ticker_price WHERE ticker_id = ?
    """,(row['id'],))
    bars = statement.fetchall()

    return templates.TemplateResponse("stock_detail.html", {"request": request, "stock":row, "bars":bars, "strategies":strategies})
    
  
@app.post("/apply_strategy")
def apply_strategy(strategy_id: int = Form(...), stock_id: int = Form(...)):
    connection = sqlite3.connect(config.DB)
    statement = connection.cursor()

    statement.execute("""
        INSERT INTO stock_strategy (stock_id,strategy_id) VALUES (?,?)
        """,(stock_id,strategy_id))
    
    connection.commit()

    return RedirectResponse(url=f"strategy/{strategy_id}",status_code=303)

@app.get("/strategy/{strategy_id}")
def strategy(request: Request, strategy_id):
    connection = sqlite3.connect(config.DB)
    connection.row_factory = sqlite3.Row

    statement = connection.cursor()
    statement.execute("""
        SELECT id,name FROM strategy WHERE id = ?
    """,(strategy_id,))

    strategy = statement.fetchone()

    statement.execute("""
        SELECT t.name, t.symbol FROM
	        stock_strategy ss
	        INNER JOIN ticker t
	        ON ss.stock_id = t.id
	    WHERE ss.strategy_id = ? 
    """,(strategy_id,))

    stocks = statement.fetchall()

    return templates.TemplateResponse("strategy.html", {"request": request, "stocks":stocks, "strategy":strategy})
    

    
