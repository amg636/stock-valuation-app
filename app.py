from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
import os
import time
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# Cache to store results and avoid hitting API repeatedly
cache = {}
CACHE_DURATION = timedelta(minutes=10)  # Cache results for 10 minutes

def get_cached_data(ticker):
    """Get cached data if available and not expired"""
    if ticker in cache:
        data, timestamp = cache[ticker]
        if datetime.now() - timestamp < CACHE_DURATION:
            print(f"Using cached data for {ticker}")
            return data
    return None

def cache_data(ticker, data):
    """Cache the analysis result"""
    cache[ticker] = (data, datetime.now())

def calculate_rational_score(ticker_data, info):
    """Calculate rational expectations score based on fundamentals"""
    score = 0
    reasons = []
    
    try:
        pe_ratio = info.get('trailingPE', None)
        forward_pe = info.get('forwardPE', None)
        industry_pe = info.get('industryPE', 25)
        
        if pe_ratio:
            if pe_ratio < industry_pe * 0.8:
                score -= 20
                reasons.append(f"Low P/E ratio ({pe_ratio:.2f} vs industry {industry_pe:.2f})")
            elif pe_ratio > industry_pe * 1.2:
                score += 20
                reasons.append(f"High P/E ratio ({pe_ratio:.2f} vs industry {industry_pe:.2f})")
        
        peg_ratio = info.get('pegRatio', None)
        if peg_ratio:
            if peg_ratio < 1:
                score -= 15
                reasons.append(f"Attractive PEG ratio ({peg_ratio:.2f})")
            elif peg_ratio > 2:
                score += 15
                reasons.append(f"High PEG ratio ({peg_ratio:.2f})")
        
        price_to_book = info.get('priceToBook', None)
        if price_to_book:
            if price_to_book < 1:
                score -= 15
                reasons.append(f"Trading below book value ({price_to_book:.2f})")
            elif price_to_book > 3:
                score += 10
                reasons.append(f"High price-to-book ({price_to_book:.2f})")
        
        profit_margin = info.get('profitMargins', None)
        if profit_margin:
            if profit_margin > 0.20:
                score -= 10
                reasons.append(f"Strong profit margins ({profit_margin*100:.1f}%)")
            elif profit_margin < 0.05:
                score += 10
                reasons.append(f"Weak profit margins ({profit_margin*100:.1f}%)")
        
    except Exception as e:
        print(f"Error in rational calculation: {e}")
    
    return max(-50, min(50, score)), reasons

def calculate_adaptive_score(ticker_data, info):
    """Calculate adaptive expectations score based on historical patterns"""
    score = 0
    reasons = []
    
    try:
        df = ticker_data.history(period="1y")
        
        if len(df) < 50:
            return 0, ["Insufficient historical data"]
        
        current_price = df['Close'].iloc[-1]
        
        ma_50 = df['Close'].rolling(window=50).mean().iloc[-1]
        ma_200 = df['Close'].rolling(window=200).mean().iloc[-1]
        
        if current_price < ma_50 * 0.95:
            score -= 15
            reasons.append(f"Trading below 50-day MA (${ma_50:.2f})")
        elif current_price > ma_50 * 1.05:
            score += 15
            reasons.append(f"Trading above 50-day MA (${ma_50:.2f})")
        
        if len(df) >= 200:
            if current_price < ma_200 * 0.90:
                score -= 20
                reasons.append(f"Significantly below 200-day MA (${ma_200:.2f})")
            elif current_price > ma_200 * 1.10:
                score += 20
                reasons.append(f"Significantly above 200-day MA (${ma_200:.2f})")
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < 30:
            score -= 15
            reasons.append(f"Oversold RSI ({current_rsi:.1f})")
        elif current_rsi > 70:
            score += 15
            reasons.append(f"Overbought RSI ({current_rsi:.1f})")
        
        week_52_high = info.get('fiftyTwoWeekHigh', df['High'].max())
        week_52_low = info.get('fiftyTwoWeekLow', df['Low'].min())
        
        range_position = (current_price - week_52_low) / (week_52_high - week_52_low)
        
        if range_position < 0.25:
            score -= 10
            reasons.append(f"Near 52-week low ({range_position*100:.1f}% of range)")
        elif range_position > 0.75:
            score += 10
            reasons.append(f"Near 52-week high ({range_position*100:.1f}% of range)")
        
    except Exception as e:
        print(f"Error in adaptive calculation: {e}")
    
    return max(-50, min(50, score)), reasons

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        ticker = data.get('ticker', '').upper().strip()
        rational_weight = float(data.get('rational_weight', 50)) / 100
        
        if not ticker:
            return jsonify({'error': 'Please enter a ticker symbol'}), 400
        
        # Check cache first
        cached_result = get_cached_data(ticker)
        if cached_result:
            # Recalculate combined score with new weight
            rational_score = cached_result['rational_score']
            adaptive_score = cached_result['adaptive_score']
            adaptive_weight = 1 - rational_weight
            combined_score = (rational_score * rational_weight) + (adaptive_score * adaptive_weight)
            
            if combined_score < -20:
                recommendation = "STRONG BUY"
                signal_class = "strong-buy"
            elif combined_score < -5:
                recommendation = "BUY"
                signal_class = "buy"
            elif combined_score > 20:
                recommendation = "STRONG SELL"
                signal_class = "strong-sell"
            elif combined_score > 5:
                recommendation = "SELL"
                signal_class = "sell"
            else:
                recommendation = "HOLD"
                signal_class = "hold"
            
            cached_result['combined_score'] = round(combined_score, 2)
            cached_result['recommendation'] = recommendation
            cached_result['signal_class'] = signal_class
            cached_result['rational_weight'] = rational_weight
            cached_result['adaptive_weight'] = adaptive_weight
            
            return jsonify(cached_result)
        
        # If not cached, fetch from API
        print(f"Fetching fresh data for {ticker}")
        time.sleep(2)  # Be nice to Yahoo Finance
        
        stock = yf.Ticker(ticker)
        info = stock.info
        
        current_price = info.get('currentPrice', info.get('regularMarketPrice', None))
        
        if not current_price:
            return jsonify({'error': f'Could not fetch data for {ticker}. Please check the ticker symbol or try again later.'}), 404
        
        rational_score, rational_reasons = calculate_rational_score(stock, info)
        adaptive_score, adaptive_reasons = calculate_adaptive_score(stock, info)
        
        adaptive_weight = 1 - rational_weight
        combined_score = (rational_score * rational_weight) + (adaptive_score * adaptive_weight)
        
        if combined_score < -20:
            recommendation = "STRONG BUY"
            signal_class = "strong-buy"
        elif combined_score < -5:
            recommendation = "BUY"
            signal_class = "buy"
        elif combined_score > 20:
            recommendation = "STRONG SELL"
            signal_class = "strong-sell"
        elif combined_score > 5:
            recommendation = "SELL"
            signal_class = "sell"
        else:
            recommendation = "HOLD"
            signal_class = "hold"
        
        response = {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'current_price': current_price,
            'rational_score': round(rational_score, 2),
            'adaptive_score': round(adaptive_score, 2),
            'combined_score': round(combined_score, 2),
            'recommendation': recommendation,
            'signal_class': signal_class,
            'rational_reasons': rational_reasons,
            'adaptive_reasons': adaptive_reasons,
            'rational_weight': rational_weight,
            'adaptive_weight': adaptive_weight,
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'forward_pe': info.get('forwardPE', 'N/A'),
            'peg_ratio': info.get('pegRatio', 'N/A'),
            'price_to_book': info.get('priceToBook', 'N/A'),
            'market_cap': info.get('marketCap', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A')
        }
        
        # Cache the result
        cache_data(ticker, response)
        
        return jsonify(response)
    
    except Exception as e:
        error_message = str(e)
        if 'rate' in error_message.lower() or '429' in error_message:
            return jsonify({'error': 'Rate limit reached. Please wait 15-20 minutes before trying again.'}), 429
        return jsonify({'error': f'Error: {error_message}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
