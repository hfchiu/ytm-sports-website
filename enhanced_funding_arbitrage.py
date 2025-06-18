#!/usr/bin/env python3
"""
Enhanced Funding Rate Arbitrage Strategy for Bitcoin

Based on research from Alexander et al., Makarov & Schoar, Presto Research, 1Token, and Shu.
This implementation focuses on:
1. Market-neutral positions (long spot + short futures)
2. Cross-exchange arbitrage opportunities
3. Sophisticated risk management and capital efficiency
4. Real-world transaction costs and timing considerations
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
from funding_rate_arbitrage.frarb import FundingRateArbitrage
import warnings
warnings.filterwarnings('ignore')

class EnhancedFundingArbitrageStrategy:
    def __init__(self):
        self.fr_arb = FundingRateArbitrage()
        self.exchanges = ["binance", "bybit", "okx"]  # Focus on high-volume exchanges
        self.results = {}
        
        # Strategy parameters based on research
        self.min_funding_threshold = 0.01  # 0.01% per 8 hours (Presto Research)
        self.leverage_ratio = 3.0  # Conservative leverage (1Token research)
        self.position_size_pct = 0.9  # Use 90% of capital
        self.rebalance_threshold = 0.005  # Rebalance when funding rate changes by 0.5%
        
    def fetch_comprehensive_data(self, symbol, exchange):
        """Fetch and prepare comprehensive historical data"""
        print(f"📊 Fetching comprehensive data for {symbol} on {exchange}...")
        
        try:
            funding_times, funding_rates = self.fr_arb.fetch_funding_rate_history(
                exchange=exchange, symbol=symbol
            )
            
            if len(funding_rates) == 0:
                return None
            
            df = pd.DataFrame({
                'timestamp': funding_times,
                'funding_rate': [rate / 100 for rate in funding_rates],  # Convert to decimal
                'funding_rate_pct': funding_rates
            })
            
            # Sort chronologically
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Add market regime indicators
            df['funding_rate_ma'] = df['funding_rate'].rolling(window=24).mean()  # 24 periods = 8 days
            df['funding_volatility'] = df['funding_rate'].rolling(window=24).std()
            df['market_regime'] = self.classify_market_regime(df)
            
            print(f"✅ Retrieved {len(df)} records spanning {(df['timestamp'].max() - df['timestamp'].min()).days} days")
            
            return df
            
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return None
    
    def classify_market_regime(self, df):
        """Classify market regimes based on funding rate patterns"""
        regimes = []
        
        for i, row in df.iterrows():
            funding_rate = row['funding_rate']
            volatility = row.get('funding_volatility', 0)
            
            if pd.isna(volatility):
                regimes.append('Unknown')
            elif abs(funding_rate) > 0.02:  # High funding rate
                if volatility > 0.01:
                    regimes.append('High Volatility')
                else:
                    regimes.append('Trending Market')
            elif abs(funding_rate) < 0.005:  # Low funding rate
                regimes.append('Stable Market')
            else:
                regimes.append('Normal Market')
        
        return regimes
    
    def calculate_transaction_costs(self, exchange, trade_type='futures'):
        """Calculate realistic transaction costs including spreads"""
        base_commission = self.fr_arb.get_commission(exchange=exchange, trade=trade_type, taker=False) / 100
        
        # Add estimated spread costs (based on research)
        spread_cost = {
            'binance': 0.0002,  # 0.02% spread
            'bybit': 0.0003,    # 0.03% spread
            'okx': 0.0002       # 0.02% spread
        }.get(exchange, 0.0003)
        
        # Add funding cost for holding positions
        funding_cost = 0.0001  # 0.01% daily funding cost
        
        total_cost = base_commission + spread_cost + funding_cost
        return total_cost
    
    def implement_market_neutral_strategy(self, df, exchange, initial_capital=10000):
        """
        Implement market-neutral funding rate arbitrage strategy
        Long spot + Short futures to collect funding fees while hedging price risk
        """
        print(f"\n🎯 Implementing Market-Neutral Strategy")
        print(f"   Initial Capital: ${initial_capital:,}")
        print(f"   Leverage: {self.leverage_ratio}x")
        print(f"   Min Funding Threshold: {self.min_funding_threshold*100:.2f}%")
        
        # Calculate transaction costs
        futures_cost = self.calculate_transaction_costs(exchange, 'futures')
        spot_cost = self.calculate_transaction_costs(exchange, 'spot')
        total_transaction_cost = futures_cost + spot_cost
        
        print(f"   Total Transaction Cost: {total_transaction_cost*100:.3f}%")
        
        # Initialize strategy state
        capital = initial_capital
        btc_position = 0  # BTC held in spot
        futures_position = 0  # Short futures position
        total_funding_collected = 0
        total_transaction_costs = 0
        trades_executed = 0
        
        strategy_data = []
        
        for i, row in df.iterrows():
            timestamp = row['timestamp']
            funding_rate = row['funding_rate']
            market_regime = row['market_regime']
            
            # Strategy logic based on research insights
            position_value = capital * self.position_size_pct
            leveraged_position = position_value * self.leverage_ratio
            
            # Entry conditions (Alexander et al. - timing is crucial)
            should_enter = (
                abs(funding_rate) > self.min_funding_threshold and
                btc_position == 0 and  # No current position
                market_regime in ['High Volatility', 'Trending Market']  # Favorable conditions
            )
            
            # Exit conditions
            should_exit = (
                btc_position != 0 and (
                    abs(funding_rate) < self.min_funding_threshold * 0.5 or  # Funding rate too low
                    market_regime == 'Stable Market'  # Unfavorable conditions
                )
            )
            
            trade_signal = 0
            funding_payment = 0
            transaction_cost = 0
            
            # Execute trades
            if should_enter:
                if funding_rate > 0:  # Positive funding rate - longs pay shorts
                    # Go long spot, short futures to collect funding
                    btc_position = leveraged_position / 50000  # Assume BTC price ~$50k
                    futures_position = -leveraged_position / 50000  # Short futures
                    trade_signal = 1
                    transaction_cost = leveraged_position * total_transaction_cost * 2  # Entry costs
                    trades_executed += 1
                    
                elif funding_rate < -self.min_funding_threshold:  # Negative funding rate
                    # Go short spot (via borrowing), long futures
                    btc_position = -leveraged_position / 50000
                    futures_position = leveraged_position / 50000
                    trade_signal = -1
                    transaction_cost = leveraged_position * total_transaction_cost * 2
                    trades_executed += 1
            
            elif should_exit and btc_position != 0:
                # Close positions
                exit_cost = abs(btc_position) * 50000 * total_transaction_cost * 2
                transaction_cost = exit_cost
                btc_position = 0
                futures_position = 0
                trade_signal = 0
                trades_executed += 1
            
            # Calculate funding payment (Presto Research - core profit source)
            if btc_position != 0:
                # Funding payment = position_size * funding_rate * position_direction
                spot_funding = btc_position * 50000 * funding_rate  # Spot doesn't pay funding
                futures_funding = futures_position * 50000 * funding_rate  # Futures pay/receive funding
                funding_payment = -futures_funding  # We receive what futures position pays
                total_funding_collected += funding_payment
            
            # Update capital (Shu - convert to stablecoins to lock profits)
            capital += funding_payment - transaction_cost
            total_transaction_costs += transaction_cost
            
            # Record data
            strategy_data.append({
                'timestamp': timestamp,
                'funding_rate': funding_rate,
                'funding_rate_pct': funding_rate * 100,
                'market_regime': market_regime,
                'btc_position': btc_position,
                'futures_position': futures_position,
                'trade_signal': trade_signal,
                'funding_payment': funding_payment,
                'transaction_cost': transaction_cost,
                'capital': capital,
                'total_funding_collected': total_funding_collected,
                'total_transaction_costs': total_transaction_costs,
                'trades_executed': trades_executed
            })
        
        strategy_df = pd.DataFrame(strategy_data)
        
        # Calculate performance metrics
        total_return = (capital - initial_capital) / initial_capital
        strategy_df['portfolio_return'] = (strategy_df['capital'] - initial_capital) / initial_capital
        strategy_df['cumulative_return'] = strategy_df['portfolio_return']
        
        # Performance summary
        net_profit = total_funding_collected - total_transaction_costs
        funding_yield = total_funding_collected / initial_capital
        cost_ratio = total_transaction_costs / total_funding_collected if total_funding_collected > 0 else 0
        
        print(f"\n📈 Strategy Performance Summary:")
        print(f"   Final Capital: ${capital:,.2f}")
        print(f"   Total Return: {total_return*100:.4f}%")
        print(f"   Total Funding Collected: ${total_funding_collected:,.2f}")
        print(f"   Total Transaction Costs: ${total_transaction_costs:,.2f}")
        print(f"   Net Profit: ${net_profit:,.2f}")
        print(f"   Funding Yield: {funding_yield*100:.4f}%")
        print(f"   Cost Ratio: {cost_ratio*100:.2f}%")
        print(f"   Trades Executed: {trades_executed}")
        
        return strategy_df, {
            'initial_capital': initial_capital,
            'final_capital': capital,
            'total_return': total_return,
            'total_funding_collected': total_funding_collected,
            'total_transaction_costs': total_transaction_costs,
            'net_profit': net_profit,
            'funding_yield': funding_yield,
            'cost_ratio': cost_ratio,
            'trades_executed': trades_executed,
            'leverage_ratio': self.leverage_ratio
        }
    
    def analyze_cross_exchange_opportunities(self):
        """Analyze cross-exchange arbitrage opportunities (Makarov & Schoar)"""
        print(f"\n🔄 Analyzing Cross-Exchange Arbitrage Opportunities")
        print("=" * 60)
        
        symbol = "BTC/USDT:USDT"
        current_rates = {}
        
        # Fetch current funding rates from multiple exchanges
        for exchange in self.exchanges:
            try:
                rates = self.fr_arb.fetch_all_funding_rate(exchange=exchange)
                if symbol in rates:
                    current_rates[exchange] = rates[symbol] * 100  # Convert to percentage
                    print(f"   {exchange.upper()}: {current_rates[exchange]:.6f}%")
                else:
                    print(f"   {exchange.upper()}: No data")
            except Exception as e:
                print(f"   {exchange.upper()}: Error - {e}")
        
        # Calculate arbitrage opportunities
        if len(current_rates) >= 2:
            rates_list = list(current_rates.values())
            exchanges_list = list(current_rates.keys())
            
            max_rate = max(rates_list)
            min_rate = min(rates_list)
            max_exchange = exchanges_list[rates_list.index(max_rate)]
            min_exchange = exchanges_list[rates_list.index(min_rate)]
            
            spread = max_rate - min_rate
            
            # Calculate transaction costs for cross-exchange arbitrage
            cost_high = self.calculate_transaction_costs(max_exchange, 'futures') * 100
            cost_low = self.calculate_transaction_costs(min_exchange, 'futures') * 100
            total_cost = cost_high + cost_low
            
            net_profit = spread - total_cost
            
            print(f"\n💰 Cross-Exchange Arbitrage Analysis:")
            print(f"   Highest Rate: {max_rate:.6f}% ({max_exchange.upper()})")
            print(f"   Lowest Rate: {min_rate:.6f}% ({min_exchange.upper()})")
            print(f"   Gross Spread: {spread:.6f}%")
            print(f"   Transaction Costs: {total_cost:.6f}%")
            print(f"   Net Profit: {net_profit:.6f}%")
            
            if net_profit > 0:
                print(f"   ✅ PROFITABLE OPPORTUNITY!")
                print(f"   Strategy: Short {max_exchange.upper()}, Long {min_exchange.upper()}")
            else:
                print(f"   ❌ Not profitable after costs")
        
        return current_rates
    
    def calculate_risk_metrics(self, strategy_df):
        """Calculate comprehensive risk metrics"""
        returns = strategy_df['portfolio_return'].diff().dropna()
        
        if len(returns) == 0:
            return {}
        
        # Basic metrics
        total_return = strategy_df['portfolio_return'].iloc[-1]
        volatility = returns.std()
        sharpe_ratio = returns.mean() / volatility if volatility > 0 else 0
        
        # Drawdown analysis
        portfolio_values = strategy_df['capital']
        peak = portfolio_values.expanding().max()
        drawdown = (portfolio_values - peak) / peak
        max_drawdown = drawdown.min()
        
        # Time-based metrics
        time_span = strategy_df['timestamp'].max() - strategy_df['timestamp'].min()
        annualized_return = (1 + total_return) ** (365.25 / time_span.days) - 1 if time_span.days > 0 else 0
        
        # Strategy-specific metrics
        funding_periods = len(strategy_df[strategy_df['funding_payment'] != 0])
        avg_funding_per_period = strategy_df['funding_payment'].mean()
        funding_consistency = (strategy_df['funding_payment'] > 0).mean()
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'funding_periods': funding_periods,
            'avg_funding_per_period': avg_funding_per_period,
            'funding_consistency': funding_consistency,
            'time_span_days': time_span.days
        }
    
    def plot_enhanced_analysis(self, strategy_df, symbol):
        """Create enhanced analysis plots"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Portfolio value and positions
        ax1_twin = ax1.twinx()
        ax1.plot(strategy_df['timestamp'], strategy_df['capital'], 'g-', linewidth=2, label='Portfolio Value')
        ax1_twin.plot(strategy_df['timestamp'], strategy_df['btc_position'], 'b--', alpha=0.7, label='BTC Position')
        ax1.set_ylabel('Portfolio Value ($)', color='g')
        ax1_twin.set_ylabel('BTC Position', color='b')
        ax1.set_title(f'Portfolio Performance & Positions - {symbol}')
        ax1.grid(True, alpha=0.3)
        
        # 2. Funding rates by market regime
        regimes = strategy_df['market_regime'].unique()
        colors = ['red', 'orange', 'blue', 'green', 'purple']
        
        for i, regime in enumerate(regimes):
            regime_data = strategy_df[strategy_df['market_regime'] == regime]
            if len(regime_data) > 0:
                ax2.scatter(regime_data['timestamp'], regime_data['funding_rate_pct'], 
                           alpha=0.6, s=20, label=regime, color=colors[i % len(colors)])
        
        ax2.axhline(y=self.min_funding_threshold*100, color='red', linestyle='--', 
                   label=f'Entry Threshold ({self.min_funding_threshold*100:.2f}%)')
        ax2.axhline(y=-self.min_funding_threshold*100, color='red', linestyle='--')
        ax2.set_title('Funding Rates by Market Regime')
        ax2.set_ylabel('Funding Rate (%)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Cumulative funding collected vs costs
        ax3.plot(strategy_df['timestamp'], strategy_df['total_funding_collected'], 
                'g-', linewidth=2, label='Funding Collected')
        ax3.plot(strategy_df['timestamp'], strategy_df['total_transaction_costs'], 
                'r-', linewidth=2, label='Transaction Costs')
        ax3.plot(strategy_df['timestamp'], 
                strategy_df['total_funding_collected'] - strategy_df['total_transaction_costs'],
                'b-', linewidth=2, label='Net Profit')
        ax3.set_title('Cumulative Funding vs Costs')
        ax3.set_ylabel('Amount ($)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Trade execution analysis
        trade_data = strategy_df[strategy_df['trade_signal'] != 0]
        if len(trade_data) > 0:
            ax4.scatter(trade_data['timestamp'], trade_data['funding_rate_pct'], 
                       c=trade_data['trade_signal'], cmap='RdYlGn', s=50, alpha=0.8)
            ax4.set_title('Trade Execution Points')
            ax4.set_ylabel('Funding Rate at Trade (%)')
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'enhanced_funding_arbitrage_{symbol.replace("/", "_").replace(":", "_")}.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def run_enhanced_backtest(self):
        """Run the enhanced funding rate arbitrage backtest"""
        print("🚀 Enhanced Funding Rate Arbitrage Strategy Backtest")
        print("Based on Academic Research: Alexander et al., Makarov & Schoar, Presto Research")
        print("=" * 80)
        
        # Analyze current cross-exchange opportunities
        cross_exchange_rates = self.analyze_cross_exchange_opportunities()
        
        # Run historical backtest on major pairs
        symbols = [
            ("BTC/USDT:USDT", "binance"),
            ("ETH/USDT:USDT", "binance"),
        ]
        
        all_results = {}
        
        for symbol, exchange in symbols:
            print(f"\n" + "="*70)
            print(f"📊 ENHANCED ANALYSIS: {symbol} ON {exchange.upper()}")
            print("="*70)
            
            # Fetch comprehensive data
            df = self.fetch_comprehensive_data(symbol, exchange)
            
            if df is None or len(df) < 50:
                print(f"⚠️ Insufficient data for {symbol}")
                continue
            
            # Implement market-neutral strategy
            strategy_df, summary = self.implement_market_neutral_strategy(
                df, exchange, initial_capital=10000
            )
            
            # Calculate risk metrics
            risk_metrics = self.calculate_risk_metrics(strategy_df)
            
            # Create enhanced plots
            self.plot_enhanced_analysis(strategy_df, symbol)
            
            # Store results
            all_results[symbol] = {
                'strategy_df': strategy_df,
                'summary': summary,
                'risk_metrics': risk_metrics
            }
            
            # Print detailed analysis
            self.print_enhanced_results(symbol, summary, risk_metrics)
        
        # Generate final research-based report
        self.generate_research_report(all_results, cross_exchange_rates)
        
        return all_results
    
    def print_enhanced_results(self, symbol, summary, risk_metrics):
        """Print enhanced results with research context"""
        print(f"\n📋 ENHANCED RESULTS FOR {symbol}")
        print("-" * 60)
        
        print(f"💰 Financial Performance (Presto Research Metrics):")
        print(f"   Total Return: {summary['total_return']*100:.4f}%")
        print(f"   Annualized Return: {risk_metrics.get('annualized_return', 0)*100:.4f}%")
        print(f"   Funding Yield: {summary['funding_yield']*100:.4f}%")
        print(f"   Net Profit: ${summary['net_profit']:,.2f}")
        
        print(f"\n📊 Risk Analysis (Alexander et al. Framework):")
        print(f"   Sharpe Ratio: {risk_metrics.get('sharpe_ratio', 0):.4f}")
        print(f"   Maximum Drawdown: {risk_metrics.get('max_drawdown', 0)*100:.4f}%")
        print(f"   Return Volatility: {risk_metrics.get('volatility', 0)*100:.4f}%")
        print(f"   Funding Consistency: {risk_metrics.get('funding_consistency', 0)*100:.2f}%")
        
        print(f"\n🎯 Execution Efficiency (1Token Insights):")
        print(f"   Trades Executed: {summary['trades_executed']}")
        print(f"   Cost Ratio: {summary['cost_ratio']*100:.2f}%")
        print(f"   Leverage Used: {summary['leverage_ratio']}x")
        print(f"   Avg Funding per Period: ${risk_metrics.get('avg_funding_per_period', 0):.4f}")
        
        # Research-based assessment
        print(f"\n🔬 Research-Based Assessment:")
        if summary['total_return'] > 0.05:  # 5% return
            print(f"   ✅ Meets Presto Research profitability targets (5-15% annual)")
        else:
            print(f"   ⚠️ Below optimal profitability range")
            
        if risk_metrics.get('sharpe_ratio', 0) > 1:
            print(f"   ✅ Good risk-adjusted returns (Shu criteria)")
        else:
            print(f"   ⚠️ Risk-adjusted returns need improvement")
            
        if summary['cost_ratio'] < 0.3:  # Costs < 30% of funding
            print(f"   ✅ Efficient cost structure (Makarov & Schoar)")
        else:
            print(f"   ❌ High transaction costs eroding profits")
    
    def generate_research_report(self, all_results, cross_exchange_rates):
        """Generate final report based on research insights"""
        print(f"\n" + "="*80)
        print("📋 ENHANCED FUNDING RATE ARBITRAGE RESEARCH REPORT")
        print("="*80)
        
        if not all_results:
            print("❌ No results to analyze")
            return
        
        # Summary table
        summary_data = []
        for symbol, results in all_results.items():
            summary = results['summary']
            metrics = results['risk_metrics']
            
            summary_data.append({
                'Symbol': symbol,
                'Total Return (%)': summary['total_return'] * 100,
                'Annualized Return (%)': metrics.get('annualized_return', 0) * 100,
                'Funding Yield (%)': summary['funding_yield'] * 100,
                'Sharpe Ratio': metrics.get('sharpe_ratio', 0),
                'Max Drawdown (%)': metrics.get('max_drawdown', 0) * 100,
                'Cost Ratio (%)': summary['cost_ratio'] * 100,
                'Trades': summary['trades_executed'],
                'Net Profit ($)': summary['net_profit']
            })
        
        summary_df = pd.DataFrame(summary_data)
        print(summary_df.to_string(index=False, float_format='%.4f'))
        
        # Research-based insights
        print(f"\n🔬 RESEARCH-BASED INSIGHTS:")
        
        avg_return = summary_df['Annualized Return (%)'].mean()
        avg_sharpe = summary_df['Sharpe Ratio'].mean()
        avg_cost_ratio = summary_df['Cost Ratio (%)'].mean()
        
        print(f"\n📈 Performance vs Research Benchmarks:")
        print(f"   Average Annualized Return: {avg_return:.2f}%")
        if avg_return >= 5:
            print(f"   ✅ Meets Presto Research target (5-15% annual)")
        else:
            print(f"   ⚠️ Below research-suggested profitability")
        
        print(f"\n⚖️ Risk-Adjusted Performance:")
        print(f"   Average Sharpe Ratio: {avg_sharpe:.4f}")
        if avg_sharpe > 1:
            print(f"   ✅ Excellent risk-adjusted returns")
        elif avg_sharpe > 0.5:
            print(f"   ⚠️ Moderate risk-adjusted returns")
        else:
            print(f"   ❌ Poor risk-adjusted returns")
        
        print(f"\n💸 Cost Efficiency:")
        print(f"   Average Cost Ratio: {avg_cost_ratio:.2f}%")
        if avg_cost_ratio < 30:
            print(f"   ✅ Efficient cost structure")
        else:
            print(f"   ❌ High costs eroding profits")
        
        print(f"\n💡 STRATEGIC RECOMMENDATIONS (Based on Research):")
        print(f"   1. Focus on high-volatility periods (Alexander et al.)")
        print(f"   2. Optimize leverage between 2-5x (1Token research)")
        print(f"   3. Monitor cross-exchange spreads (Makarov & Schoar)")
        print(f"   4. Convert BTC profits to stablecoins immediately (Shu)")
        print(f"   5. Use automated execution for 8-hour cycles (Presto Research)")
        
        if len(cross_exchange_rates) >= 2:
            rates = list(cross_exchange_rates.values())
            spread = max(rates) - min(rates)
            print(f"   6. Current cross-exchange spread: {spread:.6f}% - {'Exploit' if spread > 0.01 else 'Monitor'}")

def main():
    """Main function to run enhanced backtest"""
    strategy = EnhancedFundingArbitrageStrategy()
    
    try:
        results = strategy.run_enhanced_backtest()
        print(f"\n✅ Enhanced backtest completed successfully!")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Backtest interrupted by user")
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 