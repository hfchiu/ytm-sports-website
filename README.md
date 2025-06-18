# Funding Rate Arbitrage Backtest

A comprehensive backtest implementation for cryptocurrency funding rate arbitrage strategy using historical funding rate data.

## 🎯 Strategy Overview

This backtest implements a **market-neutral funding rate arbitrage strategy** that:
- Takes long spot + short futures positions when funding rates are positive (collect funding)
- Takes short spot + long futures positions when funding rates are negative (pay less funding)
- Minimizes price risk through market-neutral hedging
- Profits from funding rate collection minus transaction costs

## 📊 Backtest Features

### Core Strategy Logic
- **Entry Threshold**: 0.05% minimum funding rate to initiate trades
- **Position Sizing**: 90% of capital per trade with 3x leverage
- **Market Neutral**: Long/short hedged positions to eliminate price risk
- **Transaction Costs**: Realistic fees including futures, spot, and spread costs

### Performance Metrics
- Portfolio value tracking over time
- Total return and annualized return calculations
- Funding collection vs transaction cost analysis
- Win rate and trade execution statistics
- Risk-adjusted performance metrics

## 🚀 Quick Start

### Prerequisites
```bash
pip install pandas numpy matplotlib
```

### Usage
1. Place your funding rate CSV file in the directory
2. Update the filename in the script if needed
3. Run the backtest:

```bash
python funding_arbitrage_backtest.py
```

## 📈 Data Format

The backtest expects CSV data with the following format:
```csv
Time,Contracts,Funding Interval,Funding Rate
2025-06-18 16:00:00,BTCUSDT Perpetual,8h,0.003694%
2025-06-18 08:00:00,BTCUSDT Perpetual,8h,-0.001752%
```

## 🏗️ Strategy Parameters

### Default Settings
- **Initial Capital**: $10,000
- **Position Size**: 90% of available capital
- **Leverage**: 3x
- **Minimum Funding Threshold**: 0.05%
- **Transaction Costs**: 0.1% total (futures + spot + spreads)

### Customizable Parameters
You can modify these in the `FundingArbitrageBacktest` class:
- `initial_capital`: Starting capital amount
- `position_size_pct`: Percentage of capital to use per trade
- `leverage`: Leverage multiplier
- `min_funding_threshold`: Minimum funding rate to trigger trades
- Commission rates for different exchanges

## 📊 Output Analysis

The backtest provides:

### 1. Data Statistics
- Funding rate distribution and statistics
- Number of tradeable opportunities
- Positive vs negative funding periods

### 2. Performance Results
- Initial vs final capital
- Total return and annualized return
- Net profit after costs
- Trade execution count

### 3. Visual Analysis
Four comprehensive charts:
- Portfolio value over time
- Funding rates with trading positions
- Cumulative funding vs transaction costs
- Portfolio returns timeline

## 🎯 Strategy Logic

### Entry Conditions
```python
if funding_rate > min_threshold:
    # Long spot + Short futures (collect positive funding)
    position = 1
    
elif funding_rate < -min_threshold:
    # Short spot + Long futures (benefit from negative funding)
    position = -1
```

### Exit Conditions
```python
if abs(funding_rate) < min_threshold * 0.5:
    # Exit when funding rate becomes too low
    position = 0
```

### Funding Collection
```python
funding_payment = position_size * funding_rate * position_direction
```

## 📁 Project Structure

```
funding-rate-arbitrage/
├── funding_arbitrage_backtest.py           # Main backtest script
├── Funding Rate History_BTCUSDT Perpetual_2025-06-18.csv  # Historical data
├── funding_arbitrage_backtest_results.png  # Generated charts
├── funding_rate_arbitrage/                 # Core library
├── requirements.txt                        # Dependencies
└── README.md                              # This file
```

## ⚠️ Risk Considerations

### Strategy Risks
- **Transaction Costs**: High fees can erode profits from small funding rates
- **Market Risk**: Price movements during position establishment
- **Liquidity Risk**: Insufficient liquidity for large positions
- **Timing Risk**: 8-hour funding cycles require precise execution

### Backtest Limitations
- Historical performance doesn't guarantee future results
- Assumes perfect execution at funding rate times
- Doesn't account for slippage or partial fills
- Market impact costs not included

## 🔧 Customization

### Adjusting Strategy Parameters
```python
# In the __init__ method
self.min_funding_threshold = 0.005  # 0.5% threshold
self.leverage = 2.0  # 2x leverage
self.position_size_pct = 0.8  # 80% position sizing
```

### Adding New Metrics
Extend the `run_backtest()` method to include:
- Sharpe ratio calculations
- Maximum drawdown analysis
- Volatility metrics
- Risk-adjusted returns

## 📞 Usage Notes

- The backtest uses realistic transaction costs based on major exchanges
- Funding rates are collected every 8 hours as per perpetual futures standard
- Market-neutral positions eliminate directional price risk
- Strategy profitability depends on funding rate volatility vs transaction costs

## 📄 License

This project is for educational and research purposes. See [LICENSE.md](LICENSE.md) for details.

---

*Backtest implementation for funding rate arbitrage strategy*  
*Based on historical BTCUSDT perpetual funding rate data*
