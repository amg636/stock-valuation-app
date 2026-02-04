# Stock Valuation Application

A Flask-based web application that evaluates equity investments by comparing rational expectations (fundamental analysis) with adaptive expectations (technical analysis).

## Features

- **Rational Expectations Analysis**: Evaluates stocks using fundamental metrics including P/E ratios, PEG ratios, price-to-book ratios, and profit margins
- **Adaptive Expectations Analysis**: Incorporates technical indicators including 50-day/200-day moving averages, RSI calculations, and 52-week price ranges
- **Dynamic Weighting System**: Allows users to adjust the balance between fundamental and technical analysis via interactive slider
- **Real-Time Data Integration**: Pulls live market data using yfinance API with intelligent caching to manage rate limits
- **Buy/Sell/Hold Recommendations**: Generates actionable investment signals based on composite scoring across multiple valuation metrics

## Technologies Used

- **Backend**: Python, Flask
- **Data Analysis**: pandas, yfinance
- **Frontend**: HTML, CSS, JavaScript
- **APIs**: Yahoo Finance (yfinance)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/amg636/stock-valuation-app.git
cd stock-valuation-app
```

2. Create virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file with your Flask secret key:
```
FLASK_SECRET_KEY=your-secret-key-here
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Enter a stock ticker symbol (e.g., AAPL, MSFT, GOOGL)
2. Adjust the rational/adaptive expectations weight using the slider
3. Click "Analyze" to view valuation metrics and investment recommendation
4. Review detailed scoring breakdown for both fundamental and technical factors

## Project Background

This project explores the intersection of economic theory and quantitative finance by implementing two competing models of expectations formation:

- **Rational Expectations**: Assumes markets efficiently process all available information, focusing on fundamental valuation metrics
- **Adaptive Expectations**: Incorporates historical price patterns and momentum indicators to capture market sentiment and trends

The application demonstrates how different analytical frameworks can be combined to generate more robust investment insights.

## Author

Alexander Grant  
Economics & Data Science, Rutgers University