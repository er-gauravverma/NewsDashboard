#!/usr/bin/env python3
"""
Fetch BTC/USDT price from MEXC Futures API
"""

import requests
import json
from datetime import datetime

def get_btcusdt_price():
    """Fetch BTC/USDT price from MEXC futures market endpoints"""
    
    # symbol = 'BTC_USDT'
    symbol = 'OIL(WTI)USDT'  # Example for a different contract, change as needed
    url = f'https://api.mexc.com/api/v1/contract/ticker?symbol={symbol}'
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            ticker = data['data']
            
            print('\n' + '='*40)
            print('   BTC/USDT Price Information')
            print('='*40)
            print(f"Symbol:              {ticker['symbol']}")
            print(f"Last Price:          ${ticker['lastPrice']}")
            print(f"Bid Price (Best):    ${ticker['bid1']}")
            print(f"Ask Price (Best):    ${ticker['ask1']}")
            print(f"24h High:            ${ticker['high24Price']}")
            print(f"24h Low:             ${ticker['lower24Price']}")
            print(f"24h Volume:          {ticker['volume24']:,.0f} contracts")
            print(f"24h Turnover:        ${ticker['amount24']:,.2f}")
            print(f"Change Rate (24h):   {ticker['riseFallRate']*100:.2f}%")
            print(f"Change Amount:       ${ticker['riseFallValue']}")
            print(f"Index Price:         ${ticker['indexPrice']}")
            print(f"Fair Price:          ${ticker['fairPrice']}")
            print(f"Funding Rate:        {ticker['fundingRate']}")
            print(f"Open Interest:       {ticker['holdVol']:,.0f} contracts")
            print(f"Timestamp:           {datetime.fromtimestamp(ticker['timestamp']/1000).isoformat()}")
            print('='*40 + '\n')
            
            return ticker
        else:
            print(f"API Error: Code {data.get('code')}, Message: {data.get('msg')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Network Error: {e}")
        return None
    except json.JSONDecodeError:
        print("Error: Invalid JSON response from API")
        return None

if __name__ == '__main__':
    get_btcusdt_price()
