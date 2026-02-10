"""
Claw's Autonomous Trading Bot
Analyzes markets and executes trades based on strategy
"""

import hashlib
import hmac
import base64
import time
import urllib.parse
import urllib.request
import json
from datetime import datetime

# API Credentials
API_KEY = "GD9GEzBB8Z1koX5wVhZOmyg8XeFut0tzcOWLObh9SQGJL8ugHqteQCyz"
API_SECRET = "g+Cdxgg03P/GJlnowmUtdJ8e4tbiJ19t9UyGyCFH+dUXWa5ssOBZ/ECQQmeiBhkIk7n6gBkoifrFHviiMSVEhg=="
API_URL = "https://api.kraken.com"

# Trading parameters
MAX_POSITION_SIZE = 0.20  # Max 20% of portfolio per trade
MIN_TRADE_SIZE = 0.50     # Minimum $0.50 trade

def kraken_signature(urlpath, data, secret):
    """Generate authentication signature"""
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    return base64.b64encode(mac.digest()).decode()

def kraken_request(uri_path, data):
    """Make authenticated request to Kraken"""
    headers = {
        'API-Key': API_KEY,
        'API-Sign': kraken_signature(uri_path, data, API_SECRET)
    }
    req = urllib.request.Request(
        API_URL + uri_path,
        urllib.parse.urlencode(data).encode(),
        headers
    )
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        return {"error": str(e)}

def get_balance():
    """Get account balance"""
    return kraken_request('/0/private/Balance', {
        "nonce": str(int(1000*time.time()))
    })

def get_ticker(pair="XXBTZUSD"):
    """Get current ticker price"""
    url = f"{API_URL}/0/public/Ticker?pair={pair}"
    try:
        response = urllib.request.urlopen(url)
        return json.loads(response.read().decode())
    except Exception as e:
        return {"error": str(e)}

def get_ohlc(pair="XXBTZUSD", interval=60):
    """Get OHLC data (candlesticks)"""
    url = f"{API_URL}/0/public/OHLC?pair={pair}&interval={interval}"
    try:
        response = urllib.request.urlopen(url)
        return json.loads(response.read().decode())
    except Exception as e:
        return {"error": str(e)}

def calculate_portfolio_value():
    """Calculate total portfolio value in USD"""
    balance = get_balance()
    if 'error' in balance and balance['error']:
        return 0.0
    
    total_usd = 0.0
    balances = balance.get('result', {})
    
    # USD is already in USD
    if 'ZUSD' in balances:
        total_usd += float(balances['ZUSD'])
    
    # Convert LTC to USD (rough estimate)
    if 'XLTC' in balances:
        ltc_amount = float(balances['XLTC'])
        # Get LTC/USD price
        ltc_ticker = get_ticker("XLTCZUSD")
        if 'result' in ltc_ticker:
            ltc_price = float(ltc_ticker['result']['XLTCZUSD']['c'][0])
            total_usd += ltc_amount * ltc_price
    
    return total_usd

def analyze_market():
    """Analyze market conditions and return trading signal"""
    try:
        # Get BTC price
        ticker = get_ticker("XXBTZUSD")
        if 'error' in ticker and ticker['error']:
            print(f"Ticker error: {ticker['error']}")
            return None
        if 'result' not in ticker:
            print("No ticker result")
            return None
        
        current_price = float(ticker['result']['XXBTZUSD']['c'][0])
        
        # Get OHLC data (last 24 hours)
        ohlc = get_ohlc("XXBTZUSD", interval=60)
        if 'error' in ohlc and ohlc['error']:
            print(f"OHLC error: {ohlc['error']}")
            return None
        if 'result' not in ohlc:
            print("No OHLC result")
            return None
        
        # Simple strategy: Buy if price is near recent low, sell if near recent high
        # This is a VERY basic strategy for demonstration
        candles = ohlc['result']['XXBTZUSD'][-24:]  # Last 24 hours
        prices = [float(c[4]) for c in candles]  # Close prices
    except Exception as e:
        print(f"Error in analyze_market: {e}")
        return None
    
    avg_price = sum(prices) / len(prices)
    low_price = min(prices)
    high_price = max(prices)
    
    analysis = {
        'current_price': current_price,
        'avg_price': avg_price,
        'low_24h': low_price,
        'high_24h': high_price,
        'signal': 'HOLD'
    }
    
    # Buy signal: price is within 2% of 24h low
    if current_price <= low_price * 1.02:
        analysis['signal'] = 'BUY'
        analysis['reason'] = 'Price near 24h low'
    
    # Sell signal: price is within 2% of 24h high
    elif current_price >= high_price * 0.98:
        analysis['signal'] = 'SELL'
        analysis['reason'] = 'Price near 24h high'
    
    else:
        analysis['reason'] = 'No clear signal'
    
    return analysis

def log_analysis(analysis, portfolio_value):
    """Log market analysis to file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = f"""
### {timestamp} - Market Check
- **Portfolio Value:** ${portfolio_value:.2f}
- **BTC Price:** ${analysis['current_price']:.2f}
- **24h Low:** ${analysis['low_24h']:.2f}
- **24h High:** ${analysis['high_24h']:.2f}
- **24h Avg:** ${analysis['avg_price']:.2f}
- **Signal:** {analysis['signal']}
- **Reason:** {analysis['reason']}

"""
    
    # Append to trading log
    with open(r"C:\Users\Sya\Documents\Clawd_Brain\10_Projects\Claw_Trading\trading_log.md", "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    return log_entry

def run_market_check():
    """Main function to run during cron triggers"""
    print("=" * 60)
    print("CLAW'S MARKET CHECK")
    print("=" * 60)
    
    # Calculate portfolio value
    portfolio_value = calculate_portfolio_value()
    print(f"\nCurrent Portfolio Value: ${portfolio_value:.2f}")
    
    # Analyze market
    analysis = analyze_market()
    if not analysis:
        print("ERROR: Could not analyze market")
        return
    
    print(f"\nBTC Price: ${analysis['current_price']:.2f}")
    print(f"Signal: {analysis['signal']}")
    print(f"Reason: {analysis['reason']}")
    
    # Log analysis
    log_entry = log_analysis(analysis, portfolio_value)
    
    # Execute trade if signal is strong
    # For now, we're just logging. Actual trading will come after more testing
    if analysis['signal'] in ['BUY', 'SELL']:
        print(f"\n[SIGNAL DETECTED] {analysis['signal']} - {analysis['reason']}")
        print("[NOTE] Auto-trading not yet enabled. Logging signal only.")
    
    print("\n" + "=" * 60)
    print("MARKET CHECK COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    run_market_check()
