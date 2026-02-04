document.addEventListener('DOMContentLoaded', function() {
    const tickerInput = document.getElementById('tickerInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const modelSlider = document.getElementById('modelSlider');
    const sliderLabel = document.getElementById('sliderLabel');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const errorMessage = document.getElementById('errorMessage');
    const resultsSection = document.getElementById('resultsSection');

    // Update slider label
    modelSlider.addEventListener('input', function() {
        const rational = this.value;
        const adaptive = 100 - this.value;
        sliderLabel.textContent = `${rational}% Rational / ${adaptive}% Adaptive`;
    });

    // Allow Enter key to trigger analysis
    tickerInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            analyzeBtn.click();
        }
    });

    // Analyze button click
    analyzeBtn.addEventListener('click', async function() {
        const ticker = tickerInput.value.trim().toUpperCase();
        
        if (!ticker) {
            showError('Please enter a ticker symbol');
            return;
        }

        // Show loading, hide results and errors
        loadingSpinner.classList.remove('hidden');
        resultsSection.classList.add('hidden');
        errorMessage.classList.add('hidden');

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ticker: ticker,
                    rational_weight: modelSlider.value
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Analysis failed');
            }

            displayResults(data);
            
        } catch (error) {
            showError(error.message);
        } finally {
            loadingSpinner.classList.add('hidden');
        }
    });

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
        resultsSection.classList.add('hidden');
    }

    function displayResults(data) {
        // Hide error, show results
        errorMessage.classList.add('hidden');
        resultsSection.classList.remove('hidden');

        // Stock header
        document.getElementById('companyName').textContent = data.company_name;
        document.getElementById('tickerSymbol').textContent = data.ticker;
        document.getElementById('currentPrice').textContent = `$${data.current_price.toFixed(2)}`;

        // Recommendation
        const recommendationBadge = document.getElementById('recommendationBadge');
        recommendationBadge.textContent = data.recommendation;
        recommendationBadge.className = 'recommendation-badge ' + data.signal_class;
        document.getElementById('combinedScore').textContent = data.combined_score.toFixed(2);

        // Scores
        document.getElementById('rationalScore').textContent = data.rational_score.toFixed(2);
        document.getElementById('adaptiveScore').textContent = data.adaptive_score.toFixed(2);
        
        document.getElementById('rationalWeight').textContent = 
            `${(data.rational_weight * 100).toFixed(0)}% weight`;
        document.getElementById('adaptiveWeight').textContent = 
            `${(data.adaptive_weight * 100).toFixed(0)}% weight`;

        // Reasons
        displayReasons('rationalReasons', data.rational_reasons);
        displayReasons('adaptiveReasons', data.adaptive_reasons);

        // Fundamentals
        document.getElementById('peRatio').textContent = formatValue(data.pe_ratio);
        document.getElementById('forwardPE').textContent = formatValue(data.forward_pe);
        document.getElementById('pegRatio').textContent = formatValue(data.peg_ratio);
        document.getElementById('priceToBook').textContent = formatValue(data.price_to_book);
        document.getElementById('marketCap').textContent = formatMarketCap(data.market_cap);
        document.getElementById('sector').textContent = data.sector || 'N/A';

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function displayReasons(elementId, reasons) {
        const list = document.getElementById(elementId);
        list.innerHTML = '';
        
        if (reasons.length === 0) {
            const li = document.createElement('li');
            li.textContent = 'No significant factors detected';
            list.appendChild(li);
            return;
        }

        reasons.forEach(reason => {
            const li = document.createElement('li');
            li.textContent = reason;
            list.appendChild(li);
        });
    }

    function formatValue(value) {
        if (value === 'N/A' || value === null || value === undefined) {
            return 'N/A';
        }
        if (typeof value === 'number') {
            return value.toFixed(2);
        }
        return value;
    }

    function formatMarketCap(value) {
        if (value === 'N/A' || value === null || value === undefined) {
            return 'N/A';
        }
        if (typeof value === 'number') {
            if (value >= 1e12) {
                return `$${(value / 1e12).toFixed(2)}T`;
            } else if (value >= 1e9) {
                return `$${(value / 1e9).toFixed(2)}B`;
            } else if (value >= 1e6) {
                return `$${(value / 1e6).toFixed(2)}M`;
            }
        }
        return value;
    }
});
