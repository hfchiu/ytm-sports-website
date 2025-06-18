#!/usr/bin/env python3
"""
Funding Rate Arbitrage Strategy Backtest

This script backtests a funding rate arbitrage strategy using historical funding rate data.
The strategy involves taking market-neutral positions to collect funding fees while hedging price risk.

Strategy Logic:
1. Long spot position + Short futures position when funding rate is positive (collect funding)
2. Short spot position + Long futures position when funding rate is negative (pay less funding)
3. Market-neutral approach minimizes price risk
4. Profit comes from funding rate collection minus transaction costs
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class FundingArbitrageBacktest:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.data = None
        self.results = None
        
        # Strategy parameters
        self.initial_capital = 10000  # $10,000 starting capital
        self.position_size_pct = 0.9  # Use 90% of capital per trade
        self.leverage = 3.0  # 3x leverage
        self.min_funding_threshold = 0.0005  # 0.05% (5 basis points) minimum funding rate to trade
        
        # Transaction costs (realistic estimates)
        self.futures_commission = 0.0002  # 0.02% futures maker fee
        self.spot_commission = 0.0001  # 0.01% spot maker fee
        self.spread_cost = 0.0002  # 0.02% bid-ask spread
        self.total_transaction_cost = (self.futures_commission + self.spot_commission + self.spread_cost) * 2  # Round trip
        
        print(f"🎯 Funding Rate Arbitrage Backtest Initialized")
        print(f"   Initial Capital: ${self.initial_capital:,}")
        print(f"   Position Size: {self.position_size_pct*100}%")
        print(f"   Leverage: {self.leverage}x")
        print(f"   Min Funding Threshold: {self.min_funding_threshold*100}%")
        print(f"   Total Transaction Cost: {self.total_transaction_cost*100:.3f}%")
    
    def load_data(self):
        """Load and prepare the funding rate data"""
        print(f"\n📊 Loading funding rate data from {self.csv_file}")
        
        # Load CSV data
        self.data = pd.read_csv(self.csv_file)
        
        # Clean and prepare data
        self.data['Time'] = pd.to_datetime(self.data['Time'])
        self.data['Funding_Rate'] = self.data['Funding Rate'].str.rstrip('%').astype(float) / 100
        
        # Sort by time (oldest first for chronological backtest)
        self.data = self.data.sort_values('Time').reset_index(drop=True)
        
        print(f"✅ Loaded {len(self.data)} funding rate records")
        print(f"   Date Range: {self.data['Time'].min()} to {self.data['Time'].max()}")
        print(f"   Time Span: {(self.data['Time'].max() - self.data['Time'].min()).days} days")
        
        # Display basic statistics
        print(f"\n📈 Funding Rate Statistics:")
        print(f"   Mean: {self.data['Funding_Rate'].mean()*100:.4f}%")
        print(f"   Std: {self.data['Funding_Rate'].std()*100:.4f}%")
        print(f"   Min: {self.data['Funding_Rate'].min()*100:.4f}%")
        print(f"   Max: {self.data['Funding_Rate'].max()*100:.4f}%")
        print(f"   Positive Rates: {(self.data['Funding_Rate'] > 0).sum()} ({(self.data['Funding_Rate'] > 0).mean()*100:.1f}%)")
        print(f"   Above Threshold: {(abs(self.data['Funding_Rate']) > self.min_funding_threshold).sum()} records")
        
        return self.data
    
    def run_backtest(self):
        """Execute the funding rate arbitrage backtest"""
        if self.data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        print(f"\n🚀 Running Funding Rate Arbitrage Backtest")
        print("=" * 60)
        
        # Initialize portfolio
        capital = self.initial_capital
        position = 0  # 0 = no position, 1 = long funding collection, -1 = short funding payment
        position_size = 0
        total_funding_collected = 0
        total_transaction_costs = 0
        trades_executed = 0
        
        # Track detailed trade metrics
        completed_trades = []  # Track individual completed trades
        current_trade = None   # Track current open trade
        
        # Track results
        results = []
        
        for i, row in self.data.iterrows():
            timestamp = row['Time']
            funding_rate = row['Funding_Rate']
            
            # Calculate position value
            available_capital = capital * self.position_size_pct
            leveraged_position_value = available_capital * self.leverage
            
            # Strategy decision logic
            trade_signal = 0
            funding_payment = 0
            transaction_cost = 0
            
            # Entry conditions
            if position == 0:  # No current position
                if funding_rate > self.min_funding_threshold:
                    # Enter long position to collect positive funding
                    # Long spot + Short futures
                    position = 1
                    position_size = leveraged_position_value
                    trade_signal = 1
                    transaction_cost = position_size * self.total_transaction_cost
                    total_transaction_costs += transaction_cost
                    trades_executed += 1
                    
                    # Start tracking new trade
                    current_trade = {
                        'entry_time': timestamp,
                        'entry_funding_rate': funding_rate,
                        'position_type': 'LONG',
                        'position_size': position_size,
                        'entry_cost': transaction_cost,
                        'funding_collected': 0,
                        'periods_held': 0
                    }
                    
                elif funding_rate < -self.min_funding_threshold:
                    # Enter short position to benefit from negative funding
                    # Short spot + Long futures
                    position = -1
                    position_size = leveraged_position_value
                    trade_signal = -1
                    transaction_cost = position_size * self.total_transaction_cost
                    total_transaction_costs += transaction_cost
                    trades_executed += 1
                    
                    # Start tracking new trade
                    current_trade = {
                        'entry_time': timestamp,
                        'entry_funding_rate': funding_rate,
                        'position_type': 'SHORT',
                        'position_size': position_size,
                        'entry_cost': transaction_cost,
                        'funding_collected': 0,
                        'periods_held': 0
                    }
            
            # Collect funding if in position
            if position != 0 and current_trade is not None:
                # Calculate funding payment
                # When long (position = 1): collect positive funding, pay negative funding
                # When short (position = -1): pay positive funding, collect negative funding
                funding_payment = position_size * funding_rate * position
                total_funding_collected += funding_payment
                
                # Update current trade tracking
                current_trade['funding_collected'] += funding_payment
                current_trade['periods_held'] += 1
                
                # Exit conditions
                if abs(funding_rate) < self.min_funding_threshold * 0.5:
                    # Exit when funding rate becomes too low
                    exit_transaction_cost = position_size * self.total_transaction_cost
                    total_transaction_costs += exit_transaction_cost
                    transaction_cost += exit_transaction_cost
                    
                    # Complete the trade record
                    current_trade['exit_time'] = timestamp
                    current_trade['exit_funding_rate'] = funding_rate
                    current_trade['exit_cost'] = exit_transaction_cost
                    current_trade['total_cost'] = current_trade['entry_cost'] + exit_transaction_cost
                    current_trade['net_profit'] = current_trade['funding_collected'] - current_trade['total_cost']
                    current_trade['is_profitable'] = current_trade['net_profit'] > 0
                    
                    completed_trades.append(current_trade)
                    current_trade = None
                    
                    position = 0
                    position_size = 0
                    trades_executed += 1
            
            # Update capital
            capital += funding_payment - transaction_cost
            
            # Record results
            results.append({
                'timestamp': timestamp,
                'funding_rate': funding_rate,
                'funding_rate_pct': funding_rate * 100,
                'position': position,
                'trade_signal': trade_signal,
                'position_size': position_size,
                'funding_payment': funding_payment,
                'transaction_cost': transaction_cost,
                'capital': capital,
                'total_funding_collected': total_funding_collected,
                'total_transaction_costs': total_transaction_costs,
                'portfolio_return': (capital - self.initial_capital) / self.initial_capital,
                'trades_executed': trades_executed
            })
        
        # Convert to DataFrame
        self.results = pd.DataFrame(results)
        self.completed_trades = completed_trades
        
        # Calculate final metrics
        final_capital = capital
        total_return = (final_capital - self.initial_capital) / self.initial_capital
        net_profit = total_funding_collected - total_transaction_costs
        
        print(f"\n📈 BACKTEST RESULTS")
        print("=" * 40)
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Final Capital: ${final_capital:,.2f}")
        print(f"Total Return: {total_return*100:.4f}%")
        print(f"Net Profit: ${net_profit:,.2f}")
        print(f"Total Funding Collected: ${total_funding_collected:,.2f}")
        print(f"Total Transaction Costs: ${total_transaction_costs:,.2f}")
        print(f"Total Trade Executions: {trades_executed}")
        
        # Additional metrics
        time_span_days = (self.data['Time'].max() - self.data['Time'].min()).days
        annualized_return = (1 + total_return) ** (365 / time_span_days) - 1 if time_span_days > 0 else 0
        
        print(f"\n📊 PERFORMANCE METRICS")
        print("=" * 40)
        print(f"Time Span: {time_span_days} days")
        print(f"Annualized Return: {annualized_return*100:.4f}%")
        print(f"Funding Yield: {total_funding_collected/self.initial_capital*100:.4f}%")
        print(f"Cost Ratio: {total_transaction_costs/total_funding_collected*100:.2f}%" if total_funding_collected > 0 else "Cost Ratio: N/A")
        
        # Corrected trade analysis
        total_periods_in_position = len(self.results[self.results['position'] != 0])
        profitable_funding_periods = len(self.results[self.results['funding_payment'] > 0])
        
        # Completed trades analysis
        total_completed_trades = len(completed_trades)
        profitable_trades = len([t for t in completed_trades if t['is_profitable']])
        correct_win_rate = (profitable_trades / total_completed_trades * 100) if total_completed_trades > 0 else 0
        
        print(f"\n🎯 TRADE ANALYSIS")
        print("=" * 40)
        print(f"Total Periods in Position: {total_periods_in_position}")
        print(f"Profitable Funding Periods: {profitable_funding_periods}")
        print(f"Completed Trades: {total_completed_trades}")
        print(f"Profitable Trades: {profitable_trades}")
        print(f"Win Rate (Correct): {correct_win_rate:.2f}%")
        
        if total_completed_trades > 0:
            avg_periods_per_trade = sum([t['periods_held'] for t in completed_trades]) / total_completed_trades
            avg_profit_per_trade = sum([t['net_profit'] for t in completed_trades]) / total_completed_trades
            print(f"Average Periods per Trade: {avg_periods_per_trade:.1f}")
            print(f"Average Profit per Trade: ${avg_profit_per_trade:.2f}")
        
        return self.results
    
    def analyze_funding_opportunities(self):
        """Analyze funding rate opportunities in the data"""
        if self.data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        print(f"\n🔍 FUNDING RATE OPPORTUNITY ANALYSIS")
        print("=" * 50)
        
        # Categorize funding rates
        high_positive = self.data[self.data['Funding_Rate'] > self.min_funding_threshold]
        high_negative = self.data[self.data['Funding_Rate'] < -self.min_funding_threshold]
        tradeable_opportunities = self.data[abs(self.data['Funding_Rate']) > self.min_funding_threshold]
        
        print(f"Total Periods: {len(self.data)}")
        print(f"High Positive Funding (>{self.min_funding_threshold*100}%): {len(high_positive)} ({len(high_positive)/len(self.data)*100:.1f}%)")
        print(f"High Negative Funding (<{-self.min_funding_threshold*100}%): {len(high_negative)} ({len(high_negative)/len(self.data)*100:.1f}%)")
        print(f"Total Tradeable Opportunities: {len(tradeable_opportunities)} ({len(tradeable_opportunities)/len(self.data)*100:.1f}%)")
        
        if len(high_positive) > 0:
            print(f"\nHigh Positive Funding Stats:")
            print(f"   Mean: {high_positive['Funding_Rate'].mean()*100:.4f}%")
            print(f"   Max: {high_positive['Funding_Rate'].max()*100:.4f}%")
            
        if len(high_negative) > 0:
            print(f"\nHigh Negative Funding Stats:")
            print(f"   Mean: {high_negative['Funding_Rate'].mean()*100:.4f}%")
            print(f"   Min: {high_negative['Funding_Rate'].min()*100:.4f}%")
    
    def plot_results(self):
        """Create comprehensive plots of the backtest results"""
        if self.results is None:
            raise ValueError("Backtest not run. Call run_backtest() first.")
        
        # Create subplot figure
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Portfolio value over time
        ax1.plot(self.results['timestamp'], self.results['capital'], linewidth=2, color='green')
        ax1.axhline(y=self.initial_capital, color='red', linestyle='--', alpha=0.7, label='Initial Capital')
        ax1.set_title('Portfolio Value Over Time')
        ax1.set_ylabel('Portfolio Value ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Funding rates and positions
        ax2.plot(self.results['timestamp'], self.results['funding_rate_pct'], alpha=0.7, label='Funding Rate')
        
        # Highlight trading positions
        long_positions = self.results[self.results['position'] == 1]
        short_positions = self.results[self.results['position'] == -1]
        
        if len(long_positions) > 0:
            ax2.scatter(long_positions['timestamp'], long_positions['funding_rate_pct'], 
                       color='green', alpha=0.8, s=30, label='Long Positions', marker='^')
        if len(short_positions) > 0:
            ax2.scatter(short_positions['timestamp'], short_positions['funding_rate_pct'], 
                       color='red', alpha=0.8, s=30, label='Short Positions', marker='v')
        
        ax2.axhline(y=self.min_funding_threshold*100, color='red', linestyle='--', 
                   label=f'Entry Threshold ({self.min_funding_threshold*100}%)')
        ax2.axhline(y=-self.min_funding_threshold*100, color='red', linestyle='--')
        ax2.set_title('Funding Rates and Trading Positions')
        ax2.set_ylabel('Funding Rate (%)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Cumulative funding vs costs
        ax3.plot(self.results['timestamp'], self.results['total_funding_collected'], 
                linewidth=2, label='Funding Collected', color='green')
        ax3.plot(self.results['timestamp'], self.results['total_transaction_costs'], 
                linewidth=2, label='Transaction Costs', color='red')
        ax3.plot(self.results['timestamp'], 
                self.results['total_funding_collected'] - self.results['total_transaction_costs'],
                linewidth=2, label='Net Profit', color='blue')
        ax3.set_title('Cumulative Funding vs Costs')
        ax3.set_ylabel('Amount ($)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Portfolio returns
        ax4.plot(self.results['timestamp'], self.results['portfolio_return'] * 100, 
                linewidth=2, color='purple')
        ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        ax4.set_title('Portfolio Returns Over Time')
        ax4.set_ylabel('Return (%)')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('funding_arbitrage_backtest_results.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"\n📊 Charts saved as 'funding_arbitrage_backtest_results.png'")

    def print_trade_conditions(self):
        """Print detailed trading conditions and signals"""
        print(f"\n📋 DETAILED TRADING CONDITIONS & SIGNALS")
        print("=" * 60)
        
        print(f"💡 STRATEGY OVERVIEW:")
        print(f"   Market-Neutral Funding Rate Arbitrage")
        print(f"   Goal: Collect funding fees while hedging price risk")
        print(f"   Approach: Long spot + Short futures (or vice versa)")
        
        print(f"\n🎯 ENTRY CONDITIONS:")
        print(f"   Condition 1: LONG FUNDING COLLECTION")
        print(f"   ├─ Trigger: Funding Rate > +{self.min_funding_threshold*100:.3f}%")
        print(f"   ├─ Action: Long Spot + Short Futures")
        print(f"   ├─ Signal: trade_signal = +1")
        print(f"   ├─ Position: position = +1")
        print(f"   └─ Logic: Collect positive funding from shorts")
        print(f"")
        print(f"   Condition 2: SHORT FUNDING BENEFIT")
        print(f"   ├─ Trigger: Funding Rate < -{self.min_funding_threshold*100:.3f}%")
        print(f"   ├─ Action: Short Spot + Long Futures")
        print(f"   ├─ Signal: trade_signal = -1")
        print(f"   ├─ Position: position = -1")
        print(f"   └─ Logic: Pay less negative funding via longs")
        
        print(f"\n🚪 EXIT CONDITIONS:")
        print(f"   Condition: FUNDING RATE TOO LOW")
        print(f"   ├─ Trigger: |Funding Rate| < {self.min_funding_threshold*0.5*100:.3f}%")
        print(f"   ├─ Action: Close all positions")
        print(f"   ├─ Signal: trade_signal = 0")
        print(f"   ├─ Position: position = 0")
        print(f"   └─ Logic: Insufficient funding to cover costs")
        
        print(f"\n💰 FUNDING PAYMENT CALCULATION:")
        print(f"   Formula: funding_payment = position_size × funding_rate × position_direction")
        print(f"   ├─ Long Position (+1): Collect positive funding, pay negative funding")
        print(f"   ├─ Short Position (-1): Pay positive funding, collect negative funding")
        print(f"   └─ Position Size: {self.position_size_pct*100}% × capital × {self.leverage}x leverage")
        
        print(f"\n💸 TRANSACTION COSTS:")
        print(f"   Entry Cost: {self.total_transaction_cost*100:.3f}% of position size")
        print(f"   ├─ Futures Commission: {self.futures_commission*100:.3f}%")
        print(f"   ├─ Spot Commission: {self.spot_commission*100:.3f}%")
        print(f"   └─ Spread Cost: {self.spread_cost*100:.3f}%")
        print(f"   Exit Cost: {self.total_transaction_cost*100:.3f}% of position size")
        print(f"   Total Round-Trip: {self.total_transaction_cost*2*100:.3f}%")
        
        print(f"\n🎲 SIGNAL MEANINGS:")
        print(f"   trade_signal = +1: Enter long funding collection position")
        print(f"   trade_signal = -1: Enter short funding benefit position")
        print(f"   trade_signal = 0: No new position (hold or exit)")
        print(f"   position = +1: Currently long (collecting positive funding)")
        print(f"   position = -1: Currently short (benefiting from negative funding)")
        print(f"   position = 0: No current position")
        
        print(f"\n⚖️ RISK MANAGEMENT:")
        print(f"   ├─ Market Neutral: Long/short hedge eliminates price risk")
        print(f"   ├─ Position Sizing: Limited to {self.position_size_pct*100}% of capital")
        print(f"   ├─ Leverage Control: Maximum {self.leverage}x leverage")
        print(f"   ├─ Threshold Filter: Only trade when funding > {self.min_funding_threshold*100:.3f}%")
        print(f"   └─ Cost Awareness: Exit when funding insufficient to cover costs")

def main():
    """Main function to run the funding arbitrage backtest"""
    # Initialize backtest
    csv_file = "Funding Rate History_BTCUSDT Perpetual_2025-06-18.csv"
    backtest = FundingArbitrageBacktest(csv_file)
    
    try:
        # Load data
        backtest.load_data()
        
        # Analyze opportunities
        backtest.analyze_funding_opportunities()
        
        # Run backtest
        results = backtest.run_backtest()
        
        # Create plots
        backtest.plot_results()
        
        # Print trade conditions
        backtest.print_trade_conditions()
        
        print(f"\n✅ Funding Rate Arbitrage Backtest Completed Successfully!")
        
        return results
        
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    results = main() 