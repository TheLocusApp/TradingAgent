#!/usr/bin/env python3
"""
🌙 Moon Dev's Trading Agent Web UI
Simple Flask interface for configuration and monitoring
Built with love by Moon Dev 🚀
"""

import os
import sys
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from threading import Thread
import time
from datetime import datetime, timedelta
from termcolor import cprint

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.config.trading_config import (
    TradingConfig, AVAILABLE_MODELS, CRYPTO_TICKERS, 
    STOCK_TICKERS, OPTIONS_TICKERS, TIMEFRAMES
)
from src.agents.universal_trading_agent import UniversalTradingAgent
from src.config.trading_config import TradingConfig
from src.agents.agent_manager import agent_manager

# Legacy support (for backward compatibility)
current_agent = None
agent_running = False
agent_thread = None
current_agent_id = None  # Track which agent is "current"
agent_running = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'moon-dev-trading-agent'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Initialize optimization results storage
app.optimization_results = {}
app.optimization_results_by_ticker = {}

def load_latest_optimization_results():
    """Load the latest optimization results from disk on startup"""
    try:
        opt_dir = Path(__file__).parent.parent / 'data' / 'optimizations'
        if not opt_dir.exists():
            return
        
        # Find all optimization JSON files
        json_files = sorted(opt_dir.glob('optimization_*.json'), reverse=True)
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    results = json.load(f)
                
                # Extract ticker and trade_type from filename
                # Format: optimization_TSLA_swing_20251107_083502.json
                parts = json_file.stem.replace('optimization_', '').split('_')
                if len(parts) >= 2:
                    ticker = parts[0]
                    trade_type = parts[1]
                    key = f"{ticker}_{trade_type}"
                    
                    # Store by ticker_tradetype
                    if key not in app.optimization_results_by_ticker:
                        app.optimization_results_by_ticker[key] = {
                            'all_results': results,
                            'symbol': ticker,
                            'trade_type': trade_type,
                            'timestamp': json_file.stat().st_mtime
                        }
                        cprint(f"✅ Loaded optimization: {ticker} ({trade_type})", "green")
            except Exception as e:
                cprint(f"⚠️  Error loading {json_file.name}: {e}", "yellow")
    
    except Exception as e:
        cprint(f"⚠️  Error loading optimization results: {e}", "yellow")

# Load optimization results on startup
load_latest_optimization_results()

@app.route('/')
def index():
    """Main dashboard - Multi-Agent Trading"""
    return render_template('index_multiagent.html')

@app.route('/strategy-optimizer')
def strategy_optimizer():
    """Strategy Optimizer dashboard"""
    return render_template('strategy_optimizer.html')

@app.route('/rbi')
def rbi_dashboard():
    """RBI Agent dashboard"""
    return render_template('rbi.html')

@app.route('/agents')
def agents_dashboard():
    """All agents overview"""
    return render_template('agents.html')

@app.route('/strategy-lab')
def strategy_lab():
    """Strategy Lab page"""
    return render_template('strategy_lab.html')

@app.route('/screener')
def screener():
    """Market Screener page"""
    return render_template('screener.html')

@app.route('/analyst')
def analyst():
    """Market Analyst page - Deep dive bull/bear analysis"""
    return render_template('analyst.html')

@app.route('/swarm')
def swarm_page():
    """Swarm Consensus - Multi-model analysis"""
    return render_template('swarm.html')

@app.route('/api/rbi/submit', methods=['POST'])
def submit_rbi_strategy():
    """Submit trading idea to RBI agent - runs complete pipeline"""
    try:
        data = request.json
        trading_idea = data.get('trading_idea', '').strip()
        rbi_agent_version = data.get('rbi_agent_version', 'v3')  # Default to V3
        ai_model = data.get('ai_model', 'deepseek')  # Default to DeepSeek
        
        if not trading_idea:
            return jsonify({'status': 'error', 'message': 'Trading idea is required'})
        
        cprint(f"\n🔬 RBI {rbi_agent_version.upper()}: Processing trading idea with {ai_model} model...", "cyan")
        
        strategy_name = None
        
        # Route to appropriate RBI agent version
        if rbi_agent_version == 'v3':
            from src.agents.rbi_agent_v3 import process_trading_idea_with_execution
            from src.agents.rbi_agent_v3 import FINAL_BACKTEST_DIR
            
            # Set model for V3
            os.environ['RBI_AI_MODEL'] = ai_model
            
            try:
                process_trading_idea_with_execution(trading_idea)
                # Support both _BTFinal.py and _BTFinal_WORKING.py patterns
                backtest_files = list(FINAL_BACKTEST_DIR.glob("*_BTFinal*.py"))
                if not backtest_files:
                    raise ValueError("No backtest files found after V3 processing")
                latest_file = max(backtest_files, key=lambda p: p.stat().st_mtime)
                # Remove all BTFinal variants from name
                strategy_name = latest_file.stem.replace("_BTFinal_WORKING", "").replace("_BTFinal", "").split("_v")[0]
            except Exception as e:
                cprint(f"❌ V3 Processing Error: {e}", "red")
                strategy_name = None
                
        elif rbi_agent_version == 'v2':
            from src.agents.rbi_agent_v2 import process_trading_idea_with_execution as v2_process
            from src.agents.rbi_agent_v2 import FINAL_BACKTEST_DIR as v2_final_dir
            
            # Set model for V2
            os.environ['RBI_AI_MODEL'] = ai_model
            
            try:
                v2_process(trading_idea)
                # Support both _BTFinal.py and _BTFinal_WORKING.py patterns
                backtest_files = list(v2_final_dir.glob("*_BTFinal*.py"))
                if not backtest_files:
                    raise ValueError("No backtest files found after V2 processing")
                latest_file = max(backtest_files, key=lambda p: p.stat().st_mtime)
                # Remove all BTFinal variants from name
                strategy_name = latest_file.stem.replace("_BTFinal_WORKING", "").replace("_BTFinal", "").split("_v")[0]
            except Exception as e:
                cprint(f"❌ V2 Processing Error: {e}", "red")
                strategy_name = None
                
        elif rbi_agent_version == 'v2_simple':
            from src.agents.rbi_agent_v2_simple import create_backtest, research_strategy
            
            # Set model for V2 Simple
            os.environ['RBI_AI_MODEL'] = ai_model
            
            try:
                strategy, strategy_name = research_strategy(trading_idea)
                create_backtest(strategy, strategy_name)
            except Exception as e:
                cprint(f"❌ V2 Simple Processing Error: {e}", "red")
                strategy_name = None
                
        elif rbi_agent_version == 'v1':
            from src.agents.rbi_agent import process_trading_idea
            
            # Set model for V1
            os.environ['RBI_AI_MODEL'] = ai_model
            
            try:
                process_trading_idea(trading_idea)
                # V1 uses different directory structure
                from src.agents.rbi_agent import FINAL_BACKTEST_DIR as v1_final_dir
                # Support both _BTFinal.py and _BTFinal_WORKING.py patterns
                backtest_files = list(v1_final_dir.glob("*_BTFinal*.py"))
                if not backtest_files:
                    raise ValueError("No backtest files found after V1 processing")
                latest_file = max(backtest_files, key=lambda p: p.stat().st_mtime)
                # Remove all BTFinal variants from name
                strategy_name = latest_file.stem.replace("_BTFinal_WORKING", "").replace("_BTFinal", "").split("_v")[0]
            except Exception as e:
                cprint(f"❌ V1 Processing Error: {e}", "red")
                strategy_name = None
        
        if not strategy_name:
            return jsonify({
                'status': 'error',
                'message': 'Failed to process strategy - RBI pipeline failed'
            })
        
        # Save to recent strategies
        strategy_file = Path(project_root) / "src" / "data" / "rbi_strategies.json"
        strategy_file.parent.mkdir(parents=True, exist_ok=True)
        
        strategies = []
        if strategy_file.exists():
            with open(strategy_file, 'r') as f:
                strategies = json.load(f)
        
        strategies.insert(0, {
            'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'idea': trading_idea,
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'strategy_name': strategy_name,
            'rbi_version': rbi_agent_version  # Track which RBI version was used
        })
        
        # Keep only last 10
        strategies = strategies[:10]
        
        with open(strategy_file, 'w') as f:
            json.dump(strategies, f, indent=2)
        
        # Read research content to return to frontend
        research_content = ""
        
        # Determine research directory based on agent version
        if rbi_agent_version == 'v3':
            research_dir = Path(project_root) / "src" / "data" / "rbi_v3" / datetime.now().strftime('%m_%d_%Y') / "research"
        elif rbi_agent_version == 'v2':
            research_dir = Path(project_root) / "src" / "data" / "rbi_v2" / datetime.now().strftime('%m_%d_%Y') / "research"
        elif rbi_agent_version == 'v2_simple':
            research_dir = Path(project_root) / "src" / "data" / "rbi_v2" / datetime.now().strftime('%m_%d_%Y') / "research"
        else:  # v1
            research_dir = Path(project_root) / "src" / "data" / "rbi" / datetime.now().strftime('%m_%d_%Y') / "research"
        
        research_file = research_dir / f"{strategy_name}_strategy.txt"
        if research_file.exists():
            with open(research_file, 'r', encoding='utf-8') as f:
                research_content = f.read()
        
        return jsonify({
            'status': 'success',
            'message': 'Strategy processed successfully - backtest generated',
            'result': {
                'strategy_name': strategy_name,
                'message': 'Complete RBI pipeline executed',
                'strategy_writeup': research_content  # Add research content for frontend
            }
        })
        
    except Exception as e:
        cprint(f"❌ RBI Error: {e}", "red")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Failed to process strategy: {str(e)}'
        })

@app.route('/api/rbi/strategies', methods=['GET'])
def get_rbi_strategies():
    """Get recent RBI strategies"""
    try:
        strategy_file = Path(project_root) / "src" / "data" / "rbi_strategies.json"
        
        if not strategy_file.exists():
            return jsonify({'strategies': []})
        
        with open(strategy_file, 'r') as f:
            strategies = json.load(f)
        
        return jsonify({'strategies': strategies})
        
    except Exception as e:
        return jsonify({'strategies': []})

@app.route('/api/rbi/backtest', methods=['POST'])
def run_rbi_backtest():
    """Execute backtest for a strategy with optional RL optimization"""
    try:
        data = request.json
        strategy_name = data.get('strategy_name', '').strip()
        enable_rl = data.get('enable_rbi_rl', False)
        
        if not strategy_name:
            return jsonify({'status': 'error', 'message': 'Strategy name is required'})
        
        # Import backtest executor
        from src.agents.backtest_executor import run_single_backtest
        
        cprint(f"\n📊 Running backtest for: {strategy_name}", "cyan")
        if enable_rl:
            cprint(f"🤖 RL Optimization enabled", "yellow")
        
        # Run the backtest
        result = run_single_backtest(strategy_name)
        
        # Initialize RL optimizer if enabled
        rl_status = None
        if enable_rl and result and result.get('status') == 'success':
            try:
                from src.agents.rbi_agent_rl import RBIBacktestResult
                from src.agents.rbi_rl_manager import get_rbi_rl_manager
                
                # Get RL manager
                rl_manager = get_rbi_rl_manager()
                
                # Extract backtest results
                backtest_results = result.get('results', {})
                
                # Create backtest result object
                backtest_result = RBIBacktestResult(
                    strategy_name=strategy_name,
                    win_rate=float(backtest_results.get('win_rate', 50)),
                    sharpe_ratio=float(backtest_results.get('sharpe_ratio', 0)),
                    total_return=float(backtest_results.get('total_return', 0)),
                    total_trades=int(backtest_results.get('total_trades', 0)),
                    max_drawdown=float(backtest_results.get('max_drawdown', 0))
                )
                
                # Record the backtest result
                rl_status = rl_manager.record_backtest(strategy_name, backtest_result)
                
                cprint(f"✅ RL Status: {rl_status['label']}", "green")
            except Exception as rl_error:
                cprint(f"⚠️ RL Integration error: {rl_error}", "yellow")
                # Continue without RL if there's an error
        
        if result and result.get('status') == 'success':
            response = {
                'status': 'success',
                'message': 'Backtest completed',
                'results': result.get('results', {})
            }
            if rl_status:
                response['rl_status'] = rl_status
            return jsonify(response)
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('error', 'Backtest failed')
            })
        
    except Exception as e:
        cprint(f"❌ Backtest Error: {e}", "red")
        return jsonify({
            'status': 'error',
            'message': f'Failed to run backtest: {str(e)}'
        })

@app.route('/api/swarm/analyze', methods=['POST'])
def swarm_analyze():
    """Analyze using swarm agent (multi-model consensus) with optional RL optimization"""
    try:
        data = request.json
        prompt = data.get('prompt', '').strip()
        enable_rl = data.get('enable_rl', False)
        
        if not prompt:
            return jsonify({'status': 'error', 'message': 'Prompt is required'})
        
        # Import swarm agent
        from src.agents.swarm_agent import SwarmAgent
        
        # Create swarm instance
        swarm = SwarmAgent()
        
        # Run query
        cprint(f"\n🐝 Swarm: Analyzing with multiple models...", "cyan")
        if enable_rl:
            cprint(f"🤖 RL Optimization enabled", "yellow")
        result = swarm.query(prompt)
        
        # Extract consensus
        consensus = result.get('consensus_summary', 'Analysis complete')
        models_count = len([r for r in result.get('responses', {}).values() if r.get('success')])
        
        # Handle RL optimization if enabled
        rl_status = None
        rl_weights = None
        if enable_rl and result and result.get('responses'):
            try:
                from src.agents.swarm_agent_rl import TradeOutcome
                from src.agents.swarm_rl_manager import get_swarm_rl_manager
                
                # Get RL manager
                rl_manager = get_swarm_rl_manager()
                
                # Create trade outcome from consensus
                agent_names = list(result.get('responses', {}).keys())
                trade_outcome = TradeOutcome(
                    consensus_signal='CONSENSUS',
                    entry_price=0.0,
                    exit_price=0.0,
                    pnl=0.0,
                    pnl_pct=0.0,
                    contributing_agents=agent_names
                )
                
                # Record with RL manager
                swarm_name = "consensus_swarm"
                rl_status = rl_manager.record_trade(swarm_name, agent_names, trade_outcome)
                rl_weights = rl_manager.get_weights(swarm_name)
                
                cprint(f"✅ RL Status: {rl_status['label']}", "green")
            except Exception as rl_error:
                cprint(f"⚠️ RL Integration error: {rl_error}", "yellow")
                # Continue without RL if there's an error
        
        response_data = {
            'status': 'success',
            'consensus': consensus,
            'models_count': models_count,
            'full_result': result
        }
        
        # Add RL data if available
        if rl_status:
            response_data['rl_status'] = rl_status
        if rl_weights:
            response_data['rl_weights'] = rl_weights
        
        return jsonify(response_data)
        
    except Exception as e:
        cprint(f"❌ Swarm Error: {e}", "red")
        return jsonify({
            'status': 'error',
            'message': f'Failed to analyze: {str(e)}'
        })

@app.route('/api/market-intel/liquidations', methods=['GET'])
def get_liquidations():
    """Get current liquidation data"""
    try:
        # Try to get real liquidation data from liquidation_agent
        try:
            from src.agents.liquidation_agent import LiquidationAgent
            agent = LiquidationAgent()
            # Get latest liquidation data
            liq_data = agent.get_latest_liquidations()
            return jsonify({
                'long_liquidations': liq_data.get('long_liquidations', 0),
                'short_liquidations': liq_data.get('short_liquidations', 0),
                'spike_detected': liq_data.get('spike_detected', False),
                'pct_change': liq_data.get('pct_change', 0),
                'timestamp': datetime.now().isoformat(),
                'is_live': True
            })
        except Exception as agent_error:
            cprint(f"⚠️ Liquidation agent not available: {agent_error}", "yellow")
            # Fallback to sample data
            return jsonify({
                'long_liquidations': 2500000,
                'short_liquidations': 1200000,
                'spike_detected': False,
                'pct_change': 5.2,
                'timestamp': datetime.now().isoformat(),
                'is_live': False
            })
    except Exception as e:
        cprint(f"❌ Liquidations Error: {e}", "red")
        return jsonify({'error': str(e)})

@app.route('/api/market-intel/funding', methods=['GET'])
def get_funding():
    """Get current funding rates"""
    try:
        # Placeholder data - will be replaced with real agent data
        # TODO: Integrate with funding_agent.py
        return jsonify({
            'BTC': 0.0005,
            'ETH': -0.0002,
            'SPY': 0.0000,  # Stocks don't have funding rates
            'QQQ': 0.0000,  # Stocks don't have funding rates
            'extreme_detected': False,
            'timestamp': datetime.now().isoformat(),
            'is_live': False  # Mark as dummy data
        })
    except Exception as e:
        cprint(f"❌ Funding Error: {e}", "red")
        return jsonify({'error': str(e)})

@app.route('/api/market-intel/risk', methods=['POST'])
def calculate_risk():
    """Calculate position risk metrics"""
    try:
        data = request.json
        symbol = data.get('symbol', 'BTC')
        position_size = data.get('position_size', 1000)
        
        # Placeholder calculation - will be replaced with real agent data
        # TODO: Integrate with risk_agent.py
        
        # Simple risk calculation based on position size
        if position_size < 500:
            grade = 'A'
            recommended_pct = 2.0
        elif position_size < 1000:
            grade = 'B'
            recommended_pct = 3.0
        elif position_size < 2000:
            grade = 'C'
            recommended_pct = 5.0
        elif position_size < 5000:
            grade = 'D'
            recommended_pct = 8.0
        else:
            grade = 'F'
            recommended_pct = 10.0
        
        return jsonify({
            'grade': grade,
            'position_pct': recommended_pct,
            'stop_loss': -3.0,
            'risk_reward': 2.5,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        cprint(f"❌ Risk Calculation Error: {e}", "red")
        return jsonify({'error': str(e)})

@app.route('/api/market-data/prices', methods=['POST'])
def get_market_prices():
    """Get current prices and 24h changes for multiple symbols"""
    try:
        data = request.json
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({})
        
        # Try to get real prices from CoinGecko/yfinance
        prices = {}
        try:
            import yfinance as yf
            for symbol in symbols:
                try:
                    # Determine if crypto or stock
                    if symbol in ['BTC', 'ETH', 'SOL', 'DOGE', 'XRP', 'ADA', 'DOT', 'MATIC', 'AVAX', 'LINK']:
                        ticker_symbol = f"{symbol}-USD"
                    else:
                        ticker_symbol = symbol
                    
                    ticker = yf.Ticker(ticker_symbol)
                    hist = ticker.history(period='2d')
                    
                    if not hist.empty and len(hist) >= 2:
                        current_price = hist['Close'].iloc[-1]
                        prev_price = hist['Close'].iloc[-2]
                        change_pct = ((current_price - prev_price) / prev_price) * 100
                        
                        prices[symbol] = {
                            'price': float(current_price),
                            'change': float(change_pct)
                        }
                    else:
                        # Fallback to mock data
                        prices[symbol] = {
                            'price': 100.0,
                            'change': 0.0
                        }
                except Exception as symbol_error:
                    cprint(f"⚠️ Error fetching {symbol}: {symbol_error}", "yellow")
                    prices[symbol] = {
                        'price': 100.0,
                        'change': 0.0
                    }
        except Exception as e:
            cprint(f"⚠️ yfinance not available: {e}", "yellow")
            # Return mock data
            for symbol in symbols:
                prices[symbol] = {
                    'price': 100.0,
                    'change': 0.0
                }
        
        return jsonify(prices)
    except Exception as e:
        cprint(f"❌ Market Prices Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-intel/sentiment', methods=['GET'])
def get_sentiment():
    """Get market sentiment analysis"""
    try:
        # Try to get real sentiment data from sentiment_agent
        try:
            from src.agents.sentiment_agent import SentimentAgent
            agent = SentimentAgent()
            # Get sentiment for tracked tokens
            sentiment_data = agent.get_current_sentiment()
            
            def format_sentiment(score):
                if score > 0.5:
                    return {'emoji': '😊', 'label': 'Very Bullish', 'color': '#22c55e'}
                elif score > 0.2:
                    return {'emoji': '🙂', 'label': 'Bullish', 'color': '#84cc16'}
                elif score > -0.2:
                    return {'emoji': '😐', 'label': 'Neutral', 'color': '#eab308'}
                elif score > -0.5:
                    return {'emoji': '😕', 'label': 'Bearish', 'color': '#f97316'}
                else:
                    return {'emoji': '😞', 'label': 'Very Bearish', 'color': '#ef4444'}
            
            result = {}
            for asset in ['BTC', 'ETH', 'SPY', 'QQQ']:
                if asset in sentiment_data:
                    score = sentiment_data[asset]['score']
                    result[asset] = {
                        'score': score,
                        **format_sentiment(score),
                        'mentions': sentiment_data[asset].get('mentions', 0)
                    }
                else:
                    result[asset] = {
                        'score': 0,
                        'emoji': '—',
                        'label': 'N/A',
                        'color': '#6b7280',
                        'mentions': 0
                    }
            
            result['timestamp'] = datetime.now().isoformat()
            result['is_live'] = True
            return jsonify(result)
            
        except Exception as agent_error:
            cprint(f"⚠️ Sentiment agent not available: {agent_error}", "yellow")
            # Fallback to N/A
            return jsonify({
                'BTC': {'score': 0, 'emoji': '—', 'label': 'N/A', 'color': '#6b7280', 'mentions': 0},
                'ETH': {'score': 0, 'emoji': '—', 'label': 'N/A', 'color': '#6b7280', 'mentions': 0},
                'SPY': {'score': 0, 'emoji': '—', 'label': 'N/A', 'color': '#6b7280', 'mentions': 0},
                'QQQ': {'score': 0, 'emoji': '—', 'label': 'N/A', 'color': '#6b7280', 'mentions': 0},
                'timestamp': datetime.now().isoformat(),
                'is_live': False
            })
    except Exception as e:
        cprint(f"❌ Sentiment Error: {e}", "red")
        return jsonify({'error': str(e)})

@app.route('/api/market-intel/whale-alerts', methods=['GET'])
def get_whale_alerts():
    """Get whale activity alerts"""
    try:
        # Try to get real whale data from whale_agent
        try:
            from src.agents.whale_agent import WhaleAgent
            agent = WhaleAgent()
            # Get recent whale alerts
            alerts = agent.get_recent_alerts()
            return jsonify({
                'alerts': alerts,
                'timestamp': datetime.now().isoformat(),
                'is_live': True
            })
        except Exception as agent_error:
            cprint(f"⚠️ Whale agent not available: {agent_error}", "yellow")
            # Fallback to sample data
            return jsonify({
                'alerts': [],
                'timestamp': datetime.now().isoformat(),
                'is_live': False
            })
    except Exception as e:
        cprint(f"❌ Whale Alerts Error: {e}", "red")
        return jsonify({'error': str(e)})

@app.route('/api/social-feed', methods=['GET'])
def get_social_feed():
    """Get social media feed for monitored symbols"""
    try:
        # Get symbols from query or use defaults
        symbols_param = request.args.get('symbols', 'BTC,ETH,SOL')
        symbols = [s.strip() for s in symbols_param.split(',')]
        
        # Mock social feed data (would integrate with Twitter API)
        feed_items = []
        
        for symbol in symbols[:3]:  # Limit to 3 symbols
            # Generate mock tweets with sentiment
            feed_items.extend([
                {
                    'symbol': symbol,
                    'text': f'Breaking: {symbol} showing strong momentum on high volume. Technical indicators align for potential breakout.',
                    'sentiment': 'bullish',
                    'source': 'CryptoWhale',
                    'timestamp': (datetime.now() - timedelta(minutes=5)).isoformat(),
                    'engagement': {'likes': 234, 'retweets': 89}
                },
                {
                    'symbol': symbol,
                    'text': f'Watching {symbol} closely. RSI approaching oversold levels, could be a good entry point for swing traders.',
                    'sentiment': 'neutral',
                    'source': 'TradingPro',
                    'timestamp': (datetime.now() - timedelta(minutes=15)).isoformat(),
                    'engagement': {'likes': 156, 'retweets': 43}
                },
                {
                    'symbol': symbol,
                    'text': f'{symbol} consolidating near support. Volume declining suggests potential reversal incoming.',
                    'sentiment': 'bearish',
                    'source': 'MarketAnalyst',
                    'timestamp': (datetime.now() - timedelta(minutes=25)).isoformat(),
                    'engagement': {'likes': 98, 'retweets': 31}
                }
            ])
        
        # Sort by timestamp (newest first)
        feed_items.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'feed': feed_items[:10],  # Return top 10
            'symbols': symbols,
            'timestamp': datetime.now().isoformat(),
            'is_live': False  # Set to True when real API integrated
        })
    except Exception as e:
        cprint(f"❌ Social Feed Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

@app.route('/api/research/<symbol>', methods=['GET'])
def get_research(symbol):
    """Get fundamental research for a symbol"""
    try:
        import yfinance as yf
        
        # Check if crypto
        is_crypto = symbol in ['BTC', 'ETH', 'SOL', 'DOGE', 'XRP', 'ADA', 'DOT', 'MATIC', 'AVAX', 'LINK']
        ticker_symbol = f"{symbol}-USD" if is_crypto else symbol
        
        # Get real data from yfinance
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        if is_crypto:
            market_cap = info.get('marketCap', 0)
            volume = info.get('volume24Hr', info.get('volume', 0))
            
            research = {
                'symbol': symbol,
                'name': info.get('name', f'{symbol} Cryptocurrency'),
                'type': 'crypto',
                'overview': info.get('description', f'{symbol} is a leading cryptocurrency with strong fundamentals and growing adoption.'),
                'metrics': {
                    'market_cap': f'${market_cap/1e9:.1f}B' if market_cap else 'N/A',
                    'volume_24h': f'${volume/1e9:.1f}B' if volume else 'N/A',
                    'circulating_supply': info.get('circulatingSupply', 'N/A'),
                    'all_time_high': f"${info.get('fiftyTwoWeekHigh', 0):,.0f}" if info.get('fiftyTwoWeekHigh') else 'N/A'
                },
                'fundamentals': {
                    'technology': 'Blockchain technology',
                    'adoption': 'Growing institutional and retail adoption',
                    'development': 'Active development community',
                    'use_cases': 'Digital asset, store of value'
                },
                'news': [
                    {'title': f'{symbol} market update', 'date': 'Recent'},
                    {'title': f'{symbol} trading activity', 'date': 'Recent'},
                    {'title': f'{symbol} network status', 'date': 'Recent'}
                ],
                'analyst_rating': 'Hold',
                'price_target': 'Monitor market conditions',
                'timestamp': datetime.now().isoformat()
            }
        else:
            market_cap = info.get('marketCap', 0)
            pe_ratio = info.get('trailingPE', 0)
            eps = info.get('trailingEps', 0)
            dividend = info.get('dividendYield', 0)
            
            research = {
                'symbol': symbol,
                'name': info.get('longName', f'{symbol} Inc.'),
                'type': 'stock',
                'overview': info.get('longBusinessSummary', f'{symbol} is a leading company in its sector.')[:300] + '...',
                'metrics': {
                    'market_cap': f'${market_cap/1e9:.1f}B' if market_cap else 'N/A',
                    'pe_ratio': f'{pe_ratio:.2f}' if pe_ratio else 'N/A',
                    'eps': f'${eps:.2f}' if eps else 'N/A',
                    'dividend_yield': f'{dividend*100:.2f}%' if dividend else 'N/A'
                },
                'fundamentals': {
                    'revenue_growth': info.get('revenueGrowth', 'N/A'),
                    'profit_margin': f"{info.get('profitMargins', 0)*100:.1f}%" if info.get('profitMargins') else 'N/A',
                    'debt_to_equity': f"{info.get('debtToEquity', 0):.2f}" if info.get('debtToEquity') else 'N/A',
                    'roe': f"{info.get('returnOnEquity', 0)*100:.1f}%" if info.get('returnOnEquity') else 'N/A'
                },
                'news': [
                    {'title': f'{symbol} market update', 'date': 'Recent'},
                    {'title': f'{symbol} financial performance', 'date': 'Recent'},
                    {'title': f'{symbol} analyst coverage', 'date': 'Recent'}
                ],
                'analyst_rating': info.get('recommendationKey', 'hold').title(),
                'price_target': f"${info.get('targetMeanPrice', 0):.2f}" if info.get('targetMeanPrice') else 'N/A',
                'timestamp': datetime.now().isoformat()
            }
        
        return jsonify(research)
    except Exception as e:
        cprint(f"❌ Research Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    if current_agent:
        return jsonify(current_agent.config.to_dict())
    return jsonify(TradingConfig().to_dict())

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration"""
    global current_agent
    
    data = request.json
    config = TradingConfig.from_dict(data)
    
    # Save config
    config_path = Path(project_root) / "src" / "config" / "current_config.json"
    config.save(str(config_path))
    
    return jsonify({'status': 'success', 'config': config.to_dict()})

@app.route('/api/start', methods=['POST'])
def start_agent():
    """Start trading agent"""
    global current_agent, agent_thread, agent_running
    
    # Check if thread is actually running and alive
    if agent_thread and agent_thread.is_alive():
        return jsonify({'status': 'error', 'message': 'Agent already running'})
    
    # Reset state completely
    agent_running = False
    agent_thread = None
    
    try:
        # Load config
        config_path = Path(project_root) / "src" / "config" / "current_config.json"
        if config_path.exists():
            config = TradingConfig.load(str(config_path))
        else:
            config = TradingConfig()
        
        # Validate we have at least one model selected
        if not config.models or len(config.models) == 0:
            return jsonify({
                'status': 'error', 
                'message': 'No AI models selected. Please select at least one model.'
            })
        
        # Create agent
        try:
            current_agent = UniversalTradingAgent(config)
        except RuntimeError as e:
            return jsonify({
                'status': 'error',
                'message': f'Failed to initialize models: {str(e)}. Check your API keys in .env'
            })
        
        # Start in background thread
        agent_running = True
        agent_thread = Thread(target=run_agent_background)
        agent_thread.daemon = True
        agent_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': 'Agent started',
            'session_id': current_agent.session_id
        })
        
    except Exception as e:
        agent_running = False
        return jsonify({'status': 'error', 'message': f'Unexpected error: {str(e)}'})

@app.route('/api/stop', methods=['POST'])
def stop_agent():
    """Stop trading agent"""
    global agent_running
    
    agent_running = False
    return jsonify({'status': 'success', 'message': 'Agent stopping...'})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get agent status"""
    if current_agent and agent_running:
        portfolio = current_agent.get_portfolio_status()
        
        # Calculate metrics from actual trades (BUY/SELL only, not HOLD)
        trades = [d for d in current_agent.session_decisions if d.get('signal') in ['BUY', 'SELL']]
        total_trades = len(trades)
        
        # Calculate win rate (only if we have trades)
        win_rate = 0
        if total_trades > 0:
            wins = sum(1 for t in trades if t.get('confidence', 0) > 70)
            win_rate = (wins / total_trades) * 100
        
        return jsonify({
            'running': agent_running,
            'session_id': current_agent.session_id,
            'config': current_agent.config.to_dict(),
            'current_balance': portfolio['capital'],
            'free_capital': portfolio['free_capital'],
            'allocated_capital': portfolio['allocated_capital'],
            'position_count': portfolio['position_count'],
            'max_positions': portfolio['max_positions'],
            'total_pnl': portfolio['total_pnl'],
            'total_pnl_pct': portfolio['total_pnl_pct'],
            'win_rate': win_rate,
            'total_trades': total_trades,
            'win_loss_ratio': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0
        })
    return jsonify({
        'running': False,
        'session_id': None,
        'config': TradingConfig().to_dict()
    })

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get detailed portfolio information"""
    if current_agent:
        portfolio = current_agent.get_portfolio_status()
        return jsonify(portfolio)
    return jsonify({'error': 'No active agent'})

# ==================== MULTI-AGENT ENDPOINTS ====================

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get all agents"""
    agents = agent_manager.get_all_agents()
    return jsonify(agents)

@app.route('/api/agents', methods=['POST'])
def create_agent():
    """Create a new agent"""
    try:
        data = request.json
        config = TradingConfig.from_dict(data)
        agent_id = agent_manager.create_agent(config)
        return jsonify({'status': 'success', 'agent_id': agent_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/agents/<agent_id>/start', methods=['POST'])
def start_agent_by_id(agent_id):
    """Start a specific agent"""
    success = agent_manager.start_agent(agent_id)
    if success:
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Failed to start agent'}), 400

@app.route('/api/agents/<agent_id>/stop', methods=['POST'])
def stop_agent_by_id(agent_id):
    """Stop a specific agent"""
    success = agent_manager.stop_agent(agent_id)
    if success:
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Failed to stop agent'}), 400

@app.route('/api/agents/<agent_id>', methods=['DELETE'])
def delete_agent_by_id(agent_id):
    """Delete a specific agent"""
    success = agent_manager.delete_agent(agent_id)
    if success:
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Failed to delete agent'}), 400

@app.route('/api/agents/stats', methods=['GET'])
def get_agents_stats():
    """Get comparison stats for all agents"""
    stats = agent_manager.get_agent_stats()
    return jsonify(stats)

@app.route('/api/agents/performance', methods=['GET'])
def get_agents_performance():
    """Get performance history for chart"""
    history = agent_manager.get_performance_history()
    return jsonify(history)

@app.route('/api/agents/<agent_id>/decisions', methods=['GET'])
def get_agent_decisions(agent_id):
    """Get decisions for a specific agent"""
    agent = agent_manager.get_agent(agent_id)
    if agent:
        return jsonify({'decisions': agent.session_decisions})
    return jsonify({'decisions': []}), 404

@app.route('/api/agents/<agent_id>/positions', methods=['GET'])
def get_agent_positions(agent_id):
    """Get open positions for a specific agent with current prices"""
    if agent_id not in agent_manager.agents:
        return jsonify([]), 404
    
    agent_info = agent_manager.agents[agent_id]
    trading_engine = agent_info['trading_engine']
    config = agent_info['config']
    
    # Get current prices for all monitored assets
    current_prices = agent_manager._get_current_prices(config.monitored_assets, config.asset_type)
    
    # For options, also fetch current option quotes for open positions
    if config.asset_type == "options":
        agent = agent_info['agent']
        for option_ticker in trading_engine.positions.keys():
            try:
                option_quote = agent.options_provider.get_option_quote(option_ticker)
                if option_quote and 'mid' in option_quote:
                    current_prices[option_ticker] = option_quote['mid']
            except Exception as e:
                pass  # Silently fail for status checks
    
    # Update positions with current prices
    trading_engine.update_position_prices(current_prices)
    
    # Return updated positions with current prices
    positions = trading_engine.get_open_positions(current_prices)
    return jsonify(positions)

@app.route('/api/agents/<agent_id>/trades', methods=['GET'])
def get_agent_trades(agent_id):
    """Get completed trades for a specific agent"""
    if agent_id not in agent_manager.agents:
        return jsonify([]), 404
    
    trading_engine = agent_manager.agents[agent_id]['trading_engine']
    limit = request.args.get('limit', 50, type=int)
    trades = trading_engine.get_completed_trades(limit=limit)
    return jsonify(trades)

# ==================== CHART ANALYSIS ENDPOINTS ====================

@app.route('/api/chart-analysis/<symbol>', methods=['GET'])
def get_chart_analysis(symbol):
    """Generate chart analysis for a symbol"""
    try:
        timeframe = request.args.get('timeframe', '15m')
        
        # Import and run chart analysis
        from src.agents.chartanalysis_agent import ChartAnalysisAgent
        
        agent = ChartAnalysisAgent()
        result = agent.analyze_symbol(symbol, timeframe)
        
        if result:
            return jsonify({
                'symbol': symbol,
                'timeframe': timeframe,
                'signal': result.get('signal', 'NOTHING'),
                'reasoning': result.get('reasoning', ''),
                'confidence': result.get('confidence', 0),
                'chart_path': result.get('chart_path', ''),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'Analysis failed'}), 500
            
    except Exception as e:
        cprint(f"❌ Chart Analysis Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chart-image/<filename>')
def get_chart_image(filename):
    """Serve chart images"""
    try:
        charts_dir = Path(__file__).parent.parent / "data" / "charts"
        return send_from_directory(charts_dir, filename)
    except Exception as e:
        cprint(f"❌ Chart Image Error: {e}", "red")
        return jsonify({'error': str(e)}), 404

# ==================== SCREENER ENDPOINTS ====================

@app.route('/api/screener/opportunities', methods=['GET'])
def get_screener_opportunities():
    """Get top trading opportunities with comprehensive analysis (Phases 1-3)"""
    try:
        trade_type = request.args.get('type', 'all')  # day, swing, investment, all
        custom_tickers = request.args.get('custom_tickers', '')  # comma-separated custom tickers
        
        opportunities = []
        
        # Try to fetch real data with enhanced provider (automatic fallbacks)
        try:
            from src.data_providers.enhanced_market_data import EnhancedMarketDataProvider
            from src.data_providers.screener_data_provider import ScreenerDataProvider
            from src.agents.chartanalysis_agent import ChartAnalysisAgent
            import yfinance as yf
            import pandas as pd
            import numpy as np
            
            # Initialize providers
            enhanced_provider = EnhancedMarketDataProvider()
            screener_provider = ScreenerDataProvider()
            chart_agent = ChartAnalysisAgent()
            
            from src.data_providers.alphavantage_provider import AlphaVantageProvider
            av_provider = AlphaVantageProvider()
            
            # DYNAMIC STOCK DISCOVERY (not hardcoded!)
            symbols = {'stocks': [], 'crypto': []}
            
            # Get top movers from Alpha Vantage
            cprint("🔍 Discovering top market movers...", "cyan")
            top_movers = av_provider.get_top_gainers_losers()
            
            # Extract symbols from top movers (price > $5, volume > 500K)
            for stock in top_movers.get('top_gainers', []):
                try:
                    price = float(stock.get('price', 0))
                    volume = int(stock.get('volume', 0))
                    ticker = stock.get('ticker', '')
                    if price > 5.0 and volume > 500000 and ticker:
                        symbols['stocks'].append(ticker)
                except:
                    continue
            
            for stock in top_movers.get('most_actively_traded', []):
                try:
                    price = float(stock.get('price', 0))
                    volume = int(stock.get('volume', 0))
                    ticker = stock.get('ticker', '')
                    if price > 5.0 and volume > 500000 and ticker and ticker not in symbols['stocks']:
                        symbols['stocks'].append(ticker)
                except:
                    continue
            
            # Expanded sector-based ticker universe for better coverage
            SECTOR_LEADERS = {
                'Technology': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMD', 'INTC', 'CRM', 'ORCL', 'ADBE', 'CSCO', 'AVGO', 'QCOM', 'TXN', 'AMAT', 'MU', 'LRCX', 'KLAC', 'SNPS', 'CDNS'],
                'Healthcare': ['UNH', 'JNJ', 'PFE', 'ABBV', 'TMO', 'ABT', 'DHR', 'BMY', 'LLY', 'AMGN', 'GILD', 'CVS', 'CI', 'HUM', 'ISRG', 'VRTX', 'REGN', 'ZTS', 'BIIB', 'IDXX'],
                'Financials': ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'SCHW', 'AXP', 'USB', 'PNC', 'TFC', 'COF', 'BK', 'STT', 'CME', 'ICE', 'SPGI', 'MCO', 'AON'],
                'Consumer': ['AMZN', 'TSLA', 'HD', 'NKE', 'MCD', 'SBUX', 'TGT', 'LOW', 'TJX', 'COST', 'WMT', 'DIS', 'CMCSA', 'NFLX', 'BKNG', 'MAR', 'YUM', 'CMG', 'ORLY', 'AZO'],
                'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'HAL', 'KMI', 'WMB', 'OKE', 'PXD', 'DVN'],
                'Industrials': ['BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'RTX', 'LMT', 'DE', 'UNP', 'CSX', 'NSC', 'FDX', 'EMR', 'ETN'],
                'Materials': ['LIN', 'APD', 'SHW', 'ECL', 'DD', 'NEM', 'FCX', 'NUE', 'VMC', 'MLM'],
                'Real Estate': ['AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'DLR', 'O', 'WELL', 'AVB', 'EQR']
            }
            
            # Add sector leaders (diversified coverage)
            for sector, tickers in SECTOR_LEADERS.items():
                for ticker in tickers:
                    if ticker not in symbols['stocks']:
                        symbols['stocks'].append(ticker)
            
            # Crypto symbols (limited to avoid rate limits)
            symbols['crypto'] = ['BTC', 'ETH', 'SOL']
            
            cprint(f"✅ Discovered {len(symbols['stocks'])} stocks and {len(symbols['crypto'])} cryptos", "green")
            
            # Track candidates with scores for ranking
            candidates = []
            
            # Add custom tickers
            if custom_tickers:
                custom_list = [t.strip().upper() for t in custom_tickers.split(',') if t.strip()]
                for ticker in custom_list:
                    if ticker in ['BTC', 'ETH', 'SOL', 'DOGE', 'XRP', 'ADA', 'DOT', 'MATIC', 'AVAX', 'LINK', 'BNB']:
                        if ticker not in symbols['crypto']:
                            symbols['crypto'].append(ticker)
                    else:
                        if ticker not in symbols['stocks']:
                            symbols['stocks'].append(ticker)
            
            # Helper function for safe rounding
            import math
            def safe_round(value, decimals):
                if value is None or math.isnan(value) or math.isinf(value):
                    return 0.0
                return round(float(value), decimals)
            
            # Process stocks with PHASE 1-3 enhancements
            for symbol in symbols['stocks']:
                try:
                    # Get basic price data
                    quote_data = enhanced_provider.get_stock_price(symbol)
                    
                    if quote_data['price'] == 0:
                        cprint(f"⚠️ No data for {symbol}, skipping", "yellow")
                        continue
                    
                    # Get historical data for technical analysis
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='60d')  # 60 days for better analysis
                    
                    if hist.empty or len(hist) < 20:
                        cprint(f"⚠️ Insufficient data for {symbol}, skipping", "yellow")
                        continue
                    
                    # Basic metrics
                    current_price = float(hist['Close'].iloc[-1])
                    prev_price = float(hist['Close'].iloc[-2])
                    change_pct = ((current_price - prev_price) / prev_price) * 100
                    volume = float(hist['Volume'].iloc[-1])
                    avg_volume = float(hist['Volume'].mean())
                    volume_ratio = volume / avg_volume if avg_volume > 0 else 1
                    
                    # Calculate RSI
                    delta = hist['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    current_rsi = float(rsi.iloc[-1]) if not rsi.empty and not pd.isna(rsi.iloc[-1]) else 50.0
                    
                    # PHASE 3: Advanced technicals (ROC, Stochastic, ADX, etc.)
                    technicals = screener_provider.calculate_advanced_technicals(hist)
                    
                    # PHASE 1: Get fundamentals for investment scoring
                    fundamentals = screener_provider.get_fundamentals(symbol)
                    investment_score, investment_rating, investment_reasons = screener_provider.calculate_investment_score(fundamentals, current_price)
                    
                    # PHASE 3: Get news sentiment
                    news_sentiment = screener_provider.get_news_sentiment(symbol)
                    
                    # Determine trade types - a ticker can qualify for multiple categories
                    # Day trade: High momentum + high volume + strong technicals
                    # Swing trade: Moderate momentum + good technicals
                    # Investment: Strong fundamentals + good valuation
                    
                    qualified_types = []
                    
                    # Check day trade criteria
                    if change_pct > 2 and volume_ratio > 1.5 and technicals['roc'] > 5:
                        qualified_types.append(('day', 85))
                    
                    # Check swing trade criteria
                    if abs(change_pct) > 1 or volume_ratio > 1.2:
                        qualified_types.append(('swing', 70))
                    
                    # Check investment criteria
                    if investment_score >= 65 and fundamentals['pe_ratio'] > 0:
                        qualified_types.append(('investment', investment_score))
                    
                    # If no criteria met, default to investment
                    if not qualified_types:
                        qualified_types.append(('investment', max(60, investment_score)))
                    
                    # Enhanced sentiment combining price action + news
                    sentiment_score = (change_pct / 10) + (news_sentiment['score'] * 0.5)
                    if sentiment_score > 0.3:
                        sentiment = {'label': 'Very Bullish', 'score': sentiment_score, 'class': 'positive'}
                    elif sentiment_score > 0.1:
                        sentiment = {'label': 'Bullish', 'score': sentiment_score, 'class': 'positive'}
                    elif sentiment_score > -0.1:
                        sentiment = {'label': 'Neutral', 'score': sentiment_score, 'class': 'neutral'}
                    elif sentiment_score > -0.3:
                        sentiment = {'label': 'Bearish', 'score': sentiment_score, 'class': 'negative'}
                    else:
                        sentiment = {'label': 'Very Bearish', 'score': sentiment_score, 'class': 'negative'}
                    
                    # Generate comprehensive AI reasoning
                    reasoning_parts = []
                    
                    # Technical analysis
                    if volume_ratio > 1.5:
                        reasoning_parts.append(f"High volume ({volume_ratio:.1f}x avg)")
                    if current_rsi > 70:
                        reasoning_parts.append("RSI overbought")
                    elif current_rsi < 30:
                        reasoning_parts.append("RSI oversold")
                    
                    # Advanced technicals
                    if technicals['roc'] > 5:
                        reasoning_parts.append(f"Strong momentum (ROC: {technicals['roc']:.1f}%)")
                    if technicals['adx'] > 25:
                        reasoning_parts.append("Strong trend")
                    if technicals['stochastic_k'] > 80:
                        reasoning_parts.append("Stochastic overbought")
                    elif technicals['stochastic_k'] < 20:
                        reasoning_parts.append("Stochastic oversold")
                    
                    # News sentiment
                    if news_sentiment['article_count'] > 0:
                        reasoning_parts.append(f"News: {news_sentiment['label']} ({news_sentiment['article_count']} articles)")
                    
                    # Create an opportunity for each qualified trade type
                    for trade_type_val, confidence in qualified_types:
                        # Add fundamentals to reasoning for investment category
                        type_reasoning_parts = reasoning_parts.copy()
                        if trade_type_val == 'investment' and fundamentals['pe_ratio'] > 0:
                            type_reasoning_parts.append(f"P/E: {fundamentals['pe_ratio']:.1f}")
                            if fundamentals['profit_margin'] > 0.15:
                                type_reasoning_parts.append(f"Profit margin: {fundamentals['profit_margin']*100:.1f}%")
                            if investment_reasons:
                                type_reasoning_parts.extend(investment_reasons[:2])  # Top 2 reasons
                        
                        ai_reasoning = ". ".join(type_reasoning_parts) + "." if type_reasoning_parts else "Neutral market conditions."
                        
                        # Calculate entry, target, stop based on trade type
                        if trade_type_val == 'day':
                            entry_price = current_price
                            target_price = current_price * 1.03  # 3% target for day trades
                            stop_loss = current_price * 0.98  # 2% stop
                        elif trade_type_val == 'swing':
                            entry_price = current_price
                            target_price = current_price * 1.05  # 5% target for swing
                            stop_loss = current_price * 0.97  # 3% stop
                        else:  # investment
                            entry_price = current_price
                            target_price = current_price * 1.15  # 15% target for long-term
                            stop_loss = current_price * 0.92  # 8% stop
                        
                        # Enhanced scoring with all factors
                        score = (
                            confidence * 0.4 +
                            (volume_ratio * 10) * 0.2 +
                            abs(change_pct) * 0.15 +
                            (technicals['roc'] if technicals['roc'] > 0 else 0) * 0.15 +
                            (news_sentiment['score'] * 50 + 50) * 0.1  # Convert -1 to 1 scale to 0-100
                        )
                        
                        candidate = {
                            'symbol': symbol.replace('-USD', ''),
                            'price': safe_round(current_price, 2),
                            'change': safe_round(change_pct, 2),
                            'volume_ratio': safe_round(volume_ratio, 2),
                            'rsi': safe_round(current_rsi, 1),
                            'sentiment': sentiment,
                            'ai_reasoning': ai_reasoning,
                            'confidence': int(confidence),
                            'trade_type': trade_type_val,
                            'entry_price': safe_round(entry_price, 2),
                            'target_price': safe_round(target_price, 2),
                            'stop_loss': safe_round(stop_loss, 2),
                            'score': safe_round(score, 2),
                            # Phase 1: Fundamentals
                            'fundamentals': {
                                'pe_ratio': safe_round(fundamentals['pe_ratio'], 2),
                                'market_cap': fundamentals['market_cap'],
                                'sector': fundamentals['sector'],
                                'investment_score': safe_round(investment_score, 0),
                                'investment_rating': investment_rating
                            },
                            # Phase 3: Advanced technicals
                            'technicals': {
                                'roc': safe_round(technicals['roc'], 2),
                                'stochastic': safe_round(technicals['stochastic_k'], 1),
                                'adx': safe_round(technicals['adx'], 1),
                                'obv_trend': technicals['obv_trend']
                            },
                            # Phase 3: News sentiment
                            'news': {
                                'sentiment': news_sentiment['label'],
                                'score': safe_round(news_sentiment['score'], 3),
                                'articles': news_sentiment['article_count']
                            }
                        }
                        candidates.append(candidate)
                    
                except Exception as symbol_error:
                    cprint(f"⚠️ Error analyzing {symbol}: {symbol_error}", "yellow")
                    import traceback
                    traceback.print_exc()
                    continue
            
            # Process crypto with CoinGecko → Alpha Vantage fallback
            for symbol in symbols['crypto']:
                try:
                    # Try CoinGecko first (primary)
                    quote_data = enhanced_provider.get_crypto_price(symbol)
                    
                    # Fallback to Alpha Vantage if CoinGecko fails
                    if quote_data['price'] == 0:
                        cprint(f"⚠️ CoinGecko failed for {symbol}, trying Alpha Vantage...", "yellow")
                        quote_data = av_provider.get_crypto_price(symbol)
                        if not quote_data or quote_data.get('price', 0) == 0:
                            cprint(f"⚠️ No data for {symbol}, skipping", "yellow")
                            continue
                    
                    current_price = quote_data['price']
                    change_pct = quote_data['change']
                    volume_ratio = 1.2  # Default for crypto (CoinGecko free tier doesn't provide volume)
                    current_rsi = 50.0  # Default neutral RSI
                    
                    # Determine sentiment and trade type
                    if change_pct > 2 and volume_ratio > 1.5:
                        sentiment = {'label': 'Very Bullish', 'score': 0.8, 'class': 'positive'}
                        confidence = 85
                        trade_type_val = 'day'
                    elif change_pct > 1 and volume_ratio > 1.2:
                        sentiment = {'label': 'Bullish', 'score': 0.65, 'class': 'positive'}
                        confidence = 75
                        trade_type_val = 'swing'
                    elif change_pct < -2:
                        sentiment = {'label': 'Bearish', 'score': -0.6, 'class': 'negative'}
                        confidence = 70
                        trade_type_val = 'swing'
                    elif abs(change_pct) < 0.5:
                        sentiment = {'label': 'Neutral', 'score': 0.0, 'class': 'neutral'}
                        confidence = 60
                        trade_type_val = 'swing'
                    else:
                        sentiment = {'label': 'Bullish', 'score': 0.5, 'class': 'positive'}
                        confidence = 65
                        trade_type_val = 'swing'
                    
                    # Generate AI reasoning
                    reasoning_parts = []
                    if current_rsi > 70:
                        reasoning_parts.append("RSI overbought - momentum strong but watch for reversal")
                    elif current_rsi < 30:
                        reasoning_parts.append("RSI oversold - potential bounce opportunity")
                    else:
                        reasoning_parts.append(f"RSI at {current_rsi:.0f} - neutral momentum")
                    
                    if change_pct > 2:
                        reasoning_parts.append("Strong upward momentum with breakout potential")
                    elif change_pct < -2:
                        reasoning_parts.append("Significant pullback - potential reversal or continuation")
                    
                    ai_reasoning = ". ".join(reasoning_parts) + "."
                    
                    # Calculate entry, target, stop
                    if change_pct > 0:
                        entry_price = current_price
                        target_price = current_price * 1.05
                        stop_loss = current_price * 0.97
                    else:
                        entry_price = current_price
                        target_price = current_price * 1.03
                        stop_loss = current_price * 0.98
                    
                    # Ensure all numeric values are valid
                    import math
                    def safe_round(value, decimals):
                        if value is None or math.isnan(value) or math.isinf(value):
                            return 0.0
                        return round(float(value), decimals)
                    
                    # Calculate screening score
                    score = confidence * 0.6 + (volume_ratio * 10) * 0.3 + abs(change_pct) * 0.1
                    
                    candidate = {
                        'symbol': symbol,
                        'price': safe_round(current_price, 2),
                        'change': safe_round(change_pct, 2),
                        'volume_ratio': safe_round(volume_ratio, 2),
                        'rsi': safe_round(current_rsi, 1),
                        'sentiment': sentiment,
                        'ai_reasoning': ai_reasoning,
                        'confidence': int(confidence),
                        'trade_type': trade_type_val,
                        'entry_price': safe_round(entry_price, 2),
                        'target_price': safe_round(target_price, 2),
                        'stop_loss': safe_round(stop_loss, 2),
                        'score': safe_round(score, 2)
                    }
                    candidates.append(candidate)
                    
                except Exception as symbol_error:
                    cprint(f"⚠️ Error analyzing {symbol}: {symbol_error}", "yellow")
                    continue
            
            # Separate by trade type
            day_trades = [c for c in candidates if c['trade_type'] == 'day']
            swing_trades = [c for c in candidates if c['trade_type'] == 'swing']
            investment_trades = [c for c in candidates if c['trade_type'] == 'investment']
            
            # Sort by score
            day_trades.sort(key=lambda x: x['score'], reverse=True)
            swing_trades.sort(key=lambda x: x['score'], reverse=True)
            investment_trades.sort(key=lambda x: x['score'], reverse=True)
            
            # Filter based on requested type (NO LIMITS - show all qualifying opportunities)
            if trade_type == 'day':
                opportunities = day_trades  # All day trades
            elif trade_type == 'swing':
                opportunities = swing_trades  # All swing trades
            elif trade_type == 'investment':
                opportunities = investment_trades  # All investment opportunities
            else:  # 'all'
                # Show all opportunities, sorted by score
                opportunities = day_trades + swing_trades + investment_trades
                opportunities.sort(key=lambda x: x['score'], reverse=True)
            
            # PHASE 2: Add chart analysis for top candidates
            cprint(f"📊 Running chart analysis on top {min(len(opportunities), 5)} opportunities...", "cyan")
            for i, opp in enumerate(opportunities[:5]):  # Analyze top 5 only to save time
                try:
                    # Determine timeframe based on trade type
                    if opp['trade_type'] == 'day':
                        timeframe = '15m'
                    elif opp['trade_type'] == 'swing':
                        timeframe = '1h'
                    else:  # investment
                        timeframe = '1d'
                    
                    # Run chart analysis
                    chart_result = chart_agent.analyze_symbol(opp['symbol'], timeframe)
                    
                    if chart_result:
                        opp['chart_analysis'] = {
                            'signal': chart_result.get('signal', 'HOLD'),
                            'reasoning': chart_result.get('reasoning', ''),
                            'confidence': chart_result.get('confidence', 50),
                            'chart_path': chart_result.get('chart_path', '')
                        }
                        cprint(f"  ✅ Chart analysis for {opp['symbol']}: {chart_result.get('signal', 'HOLD')}", "green")
                    else:
                        opp['chart_analysis'] = None
                        
                except Exception as chart_error:
                    cprint(f"  ⚠️ Chart analysis failed for {opp['symbol']}: {str(chart_error)[:50]}", "yellow")
                    opp['chart_analysis'] = None
            
        except Exception as e:
            cprint(f"⚠️ Real data unavailable, using fallback: {e}", "yellow")
            # Fallback to enhanced mock data
            opportunities = [
                {
                    'symbol': 'NVDA', 'price': 485.20, 'change': 3.2, 'volume_ratio': 2.1, 'rsi': 68,
                    'sentiment': {'label': 'Very Bullish', 'score': 0.8, 'class': 'positive'},
                    'ai_reasoning': 'High volume (2.1x average) confirms strong interest. RSI at 68 - neutral momentum. Strong upward momentum with breakout potential.',
                    'confidence': 85, 'trade_type': 'day', 'entry_price': 485, 'target_price': 509, 'stop_loss': 471
                },
                {
                    'symbol': 'TSLA', 'price': 245.50, 'change': 2.8, 'volume_ratio': 1.8, 'rsi': 72,
                    'sentiment': {'label': 'Very Bullish', 'score': 0.75, 'class': 'positive'},
                    'ai_reasoning': 'High volume (1.8x average) confirms strong interest. RSI overbought - momentum strong but watch for reversal. Strong upward momentum with breakout potential.',
                    'confidence': 82, 'trade_type': 'day', 'entry_price': 245, 'target_price': 258, 'stop_loss': 238
                },
                {
                    'symbol': 'BTC', 'price': 67500, 'change': 2.5, 'volume_ratio': 1.6, 'rsi': 65,
                    'sentiment': {'label': 'Bullish', 'score': 0.7, 'class': 'positive'},
                    'ai_reasoning': 'High volume (1.6x average) confirms strong interest. RSI at 65 - neutral momentum. Strong upward momentum with breakout potential.',
                    'confidence': 80, 'trade_type': 'day', 'entry_price': 67500, 'target_price': 70875, 'stop_loss': 65475
                },
                {
                    'symbol': 'AMD', 'price': 142.30, 'change': 1.9, 'volume_ratio': 1.4, 'rsi': 58,
                    'sentiment': {'label': 'Bullish', 'score': 0.65, 'class': 'positive'},
                    'ai_reasoning': 'High volume (1.4x average) confirms strong interest. RSI at 58 - neutral momentum. Strong upward momentum with breakout potential.',
                    'confidence': 75, 'trade_type': 'swing', 'entry_price': 142, 'target_price': 149, 'stop_loss': 138
                },
                {
                    'symbol': 'ETH', 'price': 2450, 'change': 1.5, 'volume_ratio': 1.3, 'rsi': 55,
                    'sentiment': {'label': 'Bullish', 'score': 0.6, 'class': 'positive'},
                    'ai_reasoning': 'High volume (1.3x average) confirms strong interest. RSI at 55 - neutral momentum. Strong upward momentum with breakout potential.',
                    'confidence': 72, 'trade_type': 'swing', 'entry_price': 2450, 'target_price': 2573, 'stop_loss': 2377
                },
                {
                    'symbol': 'AAPL', 'price': 178.50, 'change': 1.2, 'volume_ratio': 1.2, 'rsi': 52,
                    'sentiment': {'label': 'Bullish', 'score': 0.55, 'class': 'positive'},
                    'ai_reasoning': 'Strong fundamentals with P/E of 28.5. Excellent ROE of 147%. Market leader in consumer electronics.',
                    'confidence': 85, 'trade_type': 'investment', 'entry_price': 178, 'target_price': 200, 'stop_loss': 165,
                    'fundamentals': {'pe_ratio': 28.5, 'market_cap': '2.8T', 'sector': 'Technology', 'investment_score': 85, 'investment_rating': 'Strong Buy'},
                    'technicals': {'roc': 12.5, 'stochastic': 55, 'adx': 28, 'obv_trend': 'rising'},
                    'news': {'sentiment': 'Positive', 'score': 0.75, 'articles': 45}
                },
                {
                    'symbol': 'MSFT', 'price': 378.90, 'change': 0.9, 'volume_ratio': 1.1, 'rsi': 50,
                    'sentiment': {'label': 'Bullish', 'score': 0.5, 'class': 'positive'},
                    'ai_reasoning': 'Cloud leader with Azure growth. Strong P/E of 32.1. Excellent dividend history.',
                    'confidence': 82, 'trade_type': 'investment', 'entry_price': 379, 'target_price': 420, 'stop_loss': 350,
                    'fundamentals': {'pe_ratio': 32.1, 'market_cap': '2.9T', 'sector': 'Technology', 'investment_score': 82, 'investment_rating': 'Buy'},
                    'technicals': {'roc': 10.2, 'stochastic': 50, 'adx': 25, 'obv_trend': 'rising'},
                    'news': {'sentiment': 'Positive', 'score': 0.70, 'articles': 38}
                },
                {
                    'symbol': 'UNH', 'price': 512.30, 'change': 0.5, 'volume_ratio': 1.0, 'rsi': 48,
                    'sentiment': {'label': 'Neutral', 'score': 0.5, 'class': 'neutral'},
                    'ai_reasoning': 'Healthcare leader with defensive characteristics. P/E of 24.5. Strong ROE of 28%.',
                    'confidence': 78, 'trade_type': 'investment', 'entry_price': 512, 'target_price': 560, 'stop_loss': 480,
                    'fundamentals': {'pe_ratio': 24.5, 'market_cap': '475B', 'sector': 'Healthcare', 'investment_score': 78, 'investment_rating': 'Buy'},
                    'technicals': {'roc': 8.5, 'stochastic': 48, 'adx': 22, 'obv_trend': 'stable'},
                    'news': {'sentiment': 'Neutral', 'score': 0.50, 'articles': 28}
                },
                {
                    'symbol': 'SOL', 'price': 145.20, 'change': 2.1, 'volume_ratio': 1.5, 'rsi': 62,
                    'sentiment': {'label': 'Bullish', 'score': 0.68, 'class': 'positive'},
                    'ai_reasoning': 'High volume (1.5x average) confirms strong interest. RSI at 62 - neutral momentum. Strong upward momentum with breakout potential.',
                    'confidence': 76, 'trade_type': 'day', 'entry_price': 145, 'target_price': 152, 'stop_loss': 141
                },
                {
                    'symbol': 'META', 'price': 485.60, 'change': 1.4, 'volume_ratio': 1.2, 'rsi': 56,
                    'sentiment': {'label': 'Bullish', 'score': 0.6, 'class': 'positive'},
                    'ai_reasoning': 'High volume (1.2x average) confirms strong interest. RSI at 56 - neutral momentum. Strong upward momentum with breakout potential.',
                    'confidence': 71, 'trade_type': 'swing', 'entry_price': 486, 'target_price': 510, 'stop_loss': 471
                },
                {
                    'symbol': 'GOOGL', 'price': 142.80, 'change': 0.7, 'volume_ratio': 1.0, 'rsi': 48,
                    'sentiment': {'label': 'Neutral', 'score': 0.3, 'class': 'neutral'},
                    'ai_reasoning': 'Volume at 1.0x average. RSI at 48 - neutral momentum.',
                    'confidence': 65, 'trade_type': 'swing', 'entry_price': 143, 'target_price': 150, 'stop_loss': 140
                },
                {
                    'symbol': 'SPY', 'price': 565.80, 'change': 0.8, 'volume_ratio': 1.1, 'rsi': 51,
                    'sentiment': {'label': 'Bullish', 'score': 0.5, 'class': 'positive'},
                    'ai_reasoning': 'Volume at 1.1x average. RSI at 51 - neutral momentum.',
                    'confidence': 67, 'trade_type': 'swing', 'entry_price': 566, 'target_price': 594, 'stop_loss': 549
                },
                {
                    'symbol': 'QQQ', 'price': 478.20, 'change': 1.0, 'volume_ratio': 1.1, 'rsi': 53,
                    'sentiment': {'label': 'Bullish', 'score': 0.52, 'class': 'positive'},
                    'ai_reasoning': 'Volume at 1.1x average. RSI at 53 - neutral momentum.',
                    'confidence': 69, 'trade_type': 'swing', 'entry_price': 478, 'target_price': 502, 'stop_loss': 464
                }
            ]
        
        # Filter by trade type
        if trade_type != 'all':
            opportunities = [opp for opp in opportunities if opp['trade_type'] == trade_type]
        
        return jsonify(opportunities)
    except Exception as e:
        cprint(f"❌ Screener Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

@app.route('/api/screener/deploy', methods=['POST'])
def deploy_screener_opportunity():
    """Deploy opportunity to an agent"""
    try:
        data = request.json
        agent_id = data.get('agent_id')
        symbol = data.get('symbol')
        
        if not agent_id or not symbol:
            return jsonify({'status': 'error', 'message': 'Missing agent_id or symbol'}), 400
        
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            return jsonify({'status': 'error', 'message': 'Agent not found'}), 404
        
        # Add symbol to monitored assets if not already there
        if symbol not in agent.config.monitored_assets:
            agent.config.monitored_assets.append(symbol)
            cprint(f"✅ Added {symbol} to {agent.config.agent_name}", "green")
        
        return jsonify({'status': 'success', 'message': f'{symbol} deployed to agent'})
    except Exception as e:
        cprint(f"❌ Deploy Error: {e}", "red")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==================== ANALYST ENDPOINTS ====================

@app.route('/api/analyst/analyze', methods=['POST'])
def analyze_market():
    """Analyze tickers with bull/bear cases and recommendations"""
    try:
        from src.agents.market_analyst_agent import MarketAnalystAgent
        
        data = request.json
        tickers = data.get('tickers', [])
        depth = data.get('depth', 'standard')
        
        if not tickers:
            return jsonify({'error': 'No tickers provided'}), 400
        
        if len(tickers) > 10:
            return jsonify({'error': 'Maximum 10 tickers allowed'}), 400
        
        cprint(f"\n🔍 Analyst analyzing: {', '.join(tickers)}", "cyan")
        
        # Initialize analyst
        analyst = MarketAnalystAgent()
        
        # Analyze each ticker (AI determines timeframe)
        results = []
        for ticker in tickers:
            try:
                result = analyst.analyze_ticker(ticker)
                # Filter out None results ($0 prices)
                if result:
                    results.append(result)
                    cprint(f"✅ Analyzed {ticker}: {result.get('signal', 'N/A')} ({result.get('timeframe', 'swing')} trade)", "green")
                else:
                    cprint(f"⚠️ Skipped {ticker}: Invalid price data", "yellow")
            except Exception as e:
                cprint(f"❌ Error analyzing {ticker}: {e}", "red")
                results.append({
                    'symbol': ticker,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return jsonify({'results': results})
        
    except Exception as e:
        cprint(f"❌ Analyst Error: {e}", "red")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== PORTFOLIO ENDPOINTS ====================

@app.route('/portfolio')
def portfolio_page():
    """Portfolio management page"""
    return render_template('portfolio.html')

@app.route('/api/portfolio/holdings', methods=['GET'])
def get_portfolio_holdings():
    """Get current portfolio holdings"""
    try:
        portfolio_file = Path("src/data/portfolio.json")
        if portfolio_file.exists():
            with open(portfolio_file, 'r') as f:
                portfolio = json.load(f)
        else:
            portfolio = {'holdings': [], 'last_updated': None}
        
        return jsonify(portfolio)
    except Exception as e:
        cprint(f"❌ Portfolio Error: {e}", "red")
        return jsonify({'holdings': [], 'last_updated': None}), 500

@app.route('/api/portfolio/add', methods=['POST'])
def add_to_portfolio():
    """Add stock to portfolio"""
    try:
        data = request.json
        symbol = data.get('symbol')
        sector = data.get('sector', 'Unknown')
        weight = data.get('weight', 0)
        
        if not symbol:
            return jsonify({'status': 'error', 'message': 'Missing symbol'}), 400
        
        # Load existing portfolio
        portfolio_file = Path("src/data/portfolio.json")
        if portfolio_file.exists():
            with open(portfolio_file, 'r') as f:
                portfolio = json.load(f)
        else:
            portfolio = {'holdings': [], 'last_updated': None}
        
        # Check if already in portfolio
        existing = next((h for h in portfolio['holdings'] if h['symbol'] == symbol), None)
        if existing:
            return jsonify({'status': 'error', 'message': f'{symbol} already in portfolio'}), 400
        
        # Add to portfolio
        portfolio['holdings'].append({
            'symbol': symbol,
            'sector': sector,
            'weight': weight,
            'added_date': datetime.now().isoformat()
        })
        portfolio['last_updated'] = datetime.now().isoformat()
        
        # Save portfolio
        portfolio_file.parent.mkdir(parents=True, exist_ok=True)
        with open(portfolio_file, 'w') as f:
            json.dump(portfolio, f, indent=2)
        
        cprint(f"✅ Added {symbol} to portfolio", "green")
        return jsonify({'status': 'success', 'message': f'{symbol} added to portfolio'})
    except Exception as e:
        cprint(f"❌ Add to Portfolio Error: {e}", "red")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/portfolio/remove', methods=['POST'])
def remove_from_portfolio():
    """Remove stock from portfolio"""
    try:
        data = request.json
        symbol = data.get('symbol')
        
        if not symbol:
            return jsonify({'status': 'error', 'message': 'Missing symbol'}), 400
        
        # Load portfolio
        portfolio_file = Path("src/data/portfolio.json")
        if not portfolio_file.exists():
            return jsonify({'status': 'error', 'message': 'Portfolio not found'}), 404
        
        with open(portfolio_file, 'r') as f:
            portfolio = json.load(f)
        
        # Remove from portfolio
        portfolio['holdings'] = [h for h in portfolio['holdings'] if h['symbol'] != symbol]
        portfolio['last_updated'] = datetime.now().isoformat()
        
        # Save portfolio
        with open(portfolio_file, 'w') as f:
            json.dump(portfolio, f, indent=2)
        
        cprint(f"✅ Removed {symbol} from portfolio", "green")
        return jsonify({'status': 'success', 'message': f'{symbol} removed from portfolio'})
    except Exception as e:
        cprint(f"❌ Remove from Portfolio Error: {e}", "red")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/portfolio/update-weight', methods=['POST'])
def update_portfolio_weight():
    """Update weight for a stock in portfolio"""
    try:
        data = request.json
        symbol = data.get('symbol')
        weight = data.get('weight', 0)
        
        if not symbol:
            return jsonify({'status': 'error', 'message': 'Missing symbol'}), 400
        
        # Load portfolio
        portfolio_file = Path("src/data/portfolio.json")
        if not portfolio_file.exists():
            return jsonify({'status': 'error', 'message': 'Portfolio not found'}), 404
        
        with open(portfolio_file, 'r') as f:
            portfolio = json.load(f)
        
        # Find and update weight
        holding = next((h for h in portfolio['holdings'] if h['symbol'] == symbol), None)
        if not holding:
            return jsonify({'status': 'error', 'message': f'{symbol} not found in portfolio'}), 404
        
        holding['weight'] = float(weight)
        portfolio['last_updated'] = datetime.now().isoformat()
        
        # Save portfolio
        with open(portfolio_file, 'w') as f:
            json.dump(portfolio, f, indent=2)
        
        cprint(f"✅ Updated {symbol} weight to {weight}%", "green")
        return jsonify({'status': 'success', 'message': f'{symbol} weight updated to {weight}%'})
    except Exception as e:
        cprint(f"❌ Update Weight Error: {e}", "red")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Macro dashboard cache (24 hours)
macro_cache = {'data': None, 'timestamp': None}
MACRO_CACHE_DURATION = 24 * 60 * 60  # 24 hours in seconds

@app.route('/api/portfolio/macro', methods=['GET'])
def get_macro_dashboard():
    """Get macro indicators and economic cycle using FRED API as PRIMARY source with 24-hour caching"""
    try:
        # Check cache first
        if macro_cache['data'] and macro_cache['timestamp']:
            age = time.time() - macro_cache['timestamp']
            if age < MACRO_CACHE_DURATION:
                cprint(f"✅ Returning cached macro data (age: {age/3600:.1f} hours)", "green")
                return jsonify(macro_cache['data'])
        
        from src.data_providers.fred_provider import FREDProvider
        from src.data_providers.alphavantage_provider import AlphaVantageProvider
        
        # FRED is SOURCE OF TRUTH - call it FIRST
        cprint("📊 Fetching fresh macro data from FRED (source of truth)...", "cyan")
        fred_provider = FREDProvider()
        fred_indicators = fred_provider.get_economic_cycle_indicators()
        
        cprint(f"✅ FRED data fetched: {len(fred_indicators)} indicators", "green")
        
        # Use AI agent for economic cycle detection
        from src.agents.economic_cycle_agent import EconomicCycleAgent
        from src.models import model_factory
        
        cycle_agent = EconomicCycleAgent(model_factory)
        phase, confidence = cycle_agent.detect_cycle(fred_indicators)
        
        # Get sector allocation from Alpha Vantage
        av_provider = AlphaVantageProvider()
        
        # Use FRED data exclusively for all indicators
        combined_indicators = {
            'cpi': fred_indicators.get('cpi', {'value': 0, 'trend': 0}),
            'fed_rate': fred_indicators.get('fed_rate', {'value': 0, 'trend': 0}),
            'vix': fred_indicators.get('vix', {'value': 0, 'trend': 0}),
            'pmi': fred_indicators.get('pmi', {'value': 50, 'trend': 0}),
            'yield_curve': fred_indicators.get('yield_curve', {'value': 0, 'trend': 0}),
            'consumer_confidence': fred_indicators.get('consumer_confidence', {'value': 0, 'trend': 0})
        }
        
        # Log what we're returning
        cprint(f"📈 CPI: {combined_indicators['cpi']['value']:.2f}% (trend: {combined_indicators['cpi']['trend']:.2f}%)", "cyan")
        cprint(f"📈 Fed Rate: {combined_indicators['fed_rate']['value']:.2f}% (trend: {combined_indicators['fed_rate']['trend']:.2f}%)", "cyan")
        cprint(f"📈 VIX: {combined_indicators['vix']['value']:.2f} (trend: {combined_indicators['vix']['trend']:.2f}%)", "cyan")
        
        # Get sector allocation recommendation
        allocation = av_provider.get_sector_allocation_recommendation(phase)
        
        result = {
            'cycle': {
                'phase': phase,
                'confidence': confidence,
                'indicators': combined_indicators
            },
            'recommended_allocation': allocation
        }
        
        # Cache the result for 24 hours
        macro_cache['data'] = result
        macro_cache['timestamp'] = time.time()
        cprint("✅ Macro data cached for 24 hours", "green")
        
        return jsonify(result)
    except Exception as e:
        cprint(f"❌ Macro Dashboard Error: {e}", "red")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/decisions', methods=['GET'])
def get_decisions():
    """Get recent decisions"""
    if current_agent:
        return jsonify({
            'decisions': current_agent.session_decisions[-10:],  # Last 10
            'total': len(current_agent.session_decisions)
        })
    return jsonify({'decisions': [], 'total': 0})

@app.route('/api/options', methods=['GET'])
def get_options():
    """Get available options for dropdowns"""
    return jsonify({
        'models': AVAILABLE_MODELS,
        'crypto_tickers': CRYPTO_TICKERS,
        'stock_tickers': STOCK_TICKERS,
        'options_tickers': OPTIONS_TICKERS,
        'timeframes': TIMEFRAMES,
        'asset_types': ['crypto', 'stock', 'options']
    })

@app.route('/api/strategy/deploy', methods=['POST'])
def deploy_strategy():
    """Deploy a backtest strategy to live trading"""
    try:
        data = request.json
        strategy_name = data.get('strategy_name')
        strategy_prompt = data.get('strategy_prompt', '')  # Original trading idea
        strategy_file = data.get('strategy_file')
        symbol = data.get('symbol', 'BTC')
        timeframe = data.get('timeframe', '1D')
        
        if not strategy_name:
            return jsonify({'status': 'error', 'message': 'Strategy name is required'})
        
        # Create a new trading agent with the strategy
        agent_id = f"strategy_{int(time.time())}"
        
        # Determine asset type
        crypto_symbols = ['BTC', 'ETH', 'SOL', 'DOGE', 'ADA', 'DOT', 'LINK', 'UNI', 'AVAX', 'MATIC']
        asset_type = 'crypto' if symbol in crypto_symbols else 'stock'
        
        # Create agent configuration
        agent_config = {
            'name': f"{strategy_name}",
            'asset_type': asset_type,
            'monitored_assets': [symbol],
            'timeframe': timeframe,
            'model': 'deepseek',
            'strategy_prompt': strategy_prompt,  # Store original idea
            'strategy_file': strategy_file,
            'running': False,  # Start paused
            'created_at': datetime.now().isoformat(),
            'deployed_from': 'strategy_lab'
        }
        
        # Add to agent manager
        from src.agents.agent_manager import agent_manager
        agent_manager.agents[agent_id] = agent_config
        agent_manager.save_agents()
        
        cprint(f"✅ Deployed strategy '{strategy_name}' as agent {agent_id}", "green")
        cprint(f"   🎯 Ticker: {symbol} | Timeframe: {timeframe} | Type: {asset_type}", "cyan")
        cprint(f"   📝 Prompt: {strategy_prompt[:100]}...", "cyan")
        
        return jsonify({
            'status': 'success',
            'message': f'Strategy deployed successfully',
            'agent_id': agent_id,
            'agent_name': agent_config['name'],
            'symbol': symbol,
            'timeframe': timeframe
        })
        
    except Exception as e:
        cprint(f"❌ Deploy Strategy Error: {e}", "red")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/ticker-prices', methods=['GET'])
def get_ticker_prices():
    """Get current prices using free data sources (CoinGecko + yfinance)"""
    try:
        from src.data_providers.free_market_data import FreeMarketDataProvider
        
        prices = {}
        try:
            provider = FreeMarketDataProvider()
            
            # Get BTC (crypto from CoinGecko - 100% free)
            btc_quote = provider.get_crypto_price('BTC')
            prices['BTC/USD'] = {
                'price': btc_quote.get('price', 0),
                'change': btc_quote.get('change', 0)
            }
            
            # Get QQQ (stock from yfinance - free)
            qqq_quote = provider.get_stock_price('QQQ')
            prices['QQQ'] = {
                'price': qqq_quote.get('price', 0),
                'change': qqq_quote.get('change', 0)
            }
            
            # Get SPY (stock from yfinance - free)
            spy_quote = provider.get_stock_price('SPY')
            prices['SPY'] = {
                'price': spy_quote.get('price', 0),
                'change': spy_quote.get('change', 0)
            }
            
            # If any price is 0, use placeholders
            if prices['BTC/USD']['price'] == 0:
                prices['BTC/USD'] = {'price': 67500.00, 'change': 2.5}
            if prices['QQQ']['price'] == 0:
                prices['QQQ'] = {'price': 485.20, 'change': 1.2}
            if prices['SPY']['price'] == 0:
                prices['SPY'] = {'price': 565.80, 'change': 0.8}
            
        except Exception as e:
            print(f"⚠️ Free market data error: {e}")
            # Fallback to placeholder data
            prices = {
                'BTC/USD': {'price': 67500.00, 'change': 2.5},
                'QQQ': {'price': 485.20, 'change': 1.2},
                'SPY': {'price': 565.80, 'change': 0.8}
            }
        
        return jsonify(prices)
        
    except Exception as e:
        # Return placeholder data on any error
        return jsonify({
            'BTC/USD': {'price': 67500.00, 'change': 2.5},
            'QQQ': {'price': 485.20, 'change': 1.2},
            'SPY': {'price': 565.80, 'change': 0.8}
        })

# ==================== PORTFOLIO MANAGEMENT ENDPOINTS ====================

@app.route('/api/portfolio/summary', methods=['GET'])
def get_portfolio_summary():
    """Get portfolio-level summary with all agents"""
    try:
        from src.agents.portfolio_manager import get_portfolio_manager
        
        # Get all agent stats
        agent_stats = agent_manager.get_all_agents()
        
        # Get portfolio manager
        portfolio_mgr = get_portfolio_manager()
        
        # Update performance for each agent
        for agent_id, stats in agent_stats.items():
            portfolio_mgr.update_agent_performance(agent_id, stats)
        
        # Get portfolio summary
        summary = portfolio_mgr.get_portfolio_summary(agent_stats)
        
        return jsonify(summary)
        
    except Exception as e:
        cprint(f"❌ Portfolio Summary Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio/rebalance', methods=['POST'])
def rebalance_portfolio():
    """Trigger portfolio rebalancing"""
    try:
        from src.agents.portfolio_manager import get_portfolio_manager
        
        # Get all agent stats
        agent_stats = agent_manager.get_all_agents()
        
        # Get portfolio manager
        portfolio_mgr = get_portfolio_manager()
        
        # Rebalance
        new_allocations = portfolio_mgr.rebalance_portfolio(agent_stats)
        
        return jsonify({
            'status': 'success',
            'message': 'Portfolio rebalanced',
            'new_allocations': new_allocations
        })
        
    except Exception as e:
        cprint(f"❌ Rebalance Error: {e}", "red")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==================== RBI DEPLOYMENT ENDPOINTS ====================

@app.route('/api/rbi/deploy', methods=['POST'])
def deploy_rbi_strategy():
    """Deploy RBI backtest strategy to live trading"""
    try:
        from src.agents.rbi_deployment_pipeline import get_deployment_pipeline
        from pathlib import Path
        
        data = request.json
        strategy_name = data.get('strategy_name')
        backtest_results = data.get('backtest_results', {})
        
        if not strategy_name:
            return jsonify({'status': 'error', 'message': 'Strategy name required'})
        
        # Find backtest file
        backtest_dir = Path(project_root) / "src" / "data" / "rbi" / "FINAL_WINNING_STRATEGIES"
        backtest_file = backtest_dir / f"{strategy_name}_BT.py"
        
        if not backtest_file.exists():
            # Try alternative naming
            backtest_file = backtest_dir / f"{strategy_name}_BTFinal.py"
        
        if not backtest_file.exists():
            return jsonify({'status': 'error', 'message': f'Backtest file not found: {strategy_name}'})
        
        # Deploy
        pipeline = get_deployment_pipeline()
        deployment = pipeline.deploy_strategy(backtest_file, backtest_results)
        
        if deployment:
            # Create agent from deployment config
            config = TradingConfig.from_dict(deployment['config'])
            agent_id = agent_manager.create_agent(config)
            
            return jsonify({
                'status': 'success',
                'message': 'Strategy deployed to live trading',
                'deployment_id': deployment['deployment_id'],
                'agent_id': agent_id
            })
        else:
            return jsonify({'status': 'error', 'message': 'Deployment failed'})
        
    except Exception as e:
        cprint(f"❌ RBI Deploy Error: {e}", "red")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/rbi/deployments', methods=['GET'])
def get_rbi_deployments():
    """Get all RBI deployments"""
    try:
        from src.agents.rbi_deployment_pipeline import get_deployment_pipeline
        
        pipeline = get_deployment_pipeline()
        deployments = pipeline.get_all_deployments()
        
        return jsonify({'deployments': deployments})
        
    except Exception as e:
        cprint(f"❌ Get Deployments Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

# ==================== REGIME DETECTION ENDPOINTS ====================

@app.route('/api/regime/current', methods=['GET'])
def get_current_regime():
    """Get current market regime with VIX compass"""
    try:
        from src.agents.regime_detector import get_regime_detector
        from src.agents.vix_compass import get_vix_compass
        
        detector = get_regime_detector()
        regime_info = detector.detect_regime()
        display_info = detector.get_regime_display()
        
        # Get VIX compass reading
        vix_compass = get_vix_compass()
        vix_reading = vix_compass.get_compass_reading()
        
        return jsonify({
            'regime_info': regime_info,
            'display': display_info,
            'vix_compass': vix_reading
        })
        
    except Exception as e:
        cprint(f"❌ Regime Detection Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

# ==================== MOMENTUM ROTATION ENDPOINTS ====================

@app.route('/api/momentum/rankings', methods=['GET'])
def get_momentum_rankings():
    """Get momentum rankings for all assets"""
    try:
        from src.agents.momentum_rotator import get_momentum_rotator
        
        rotator = get_momentum_rotator()
        rankings = rotator.rank_assets()
        
        return jsonify({'rankings': rankings[:20]})  # Top 20
        
    except Exception as e:
        cprint(f"❌ Momentum Rankings Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

@app.route('/api/momentum/recommendations', methods=['GET'])
def get_momentum_recommendations():
    """Get top momentum recommendations"""
    try:
        from src.agents.momentum_rotator import get_momentum_rotator
        
        rotator = get_momentum_rotator()
        summary = rotator.get_rotation_summary()
        
        return jsonify(summary)
        
    except Exception as e:
        cprint(f"❌ Momentum Recommendations Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

# ==================== RISK GUIDANCE ENDPOINTS ====================

@app.route('/api/risk/guidance', methods=['POST'])
def get_risk_guidance_endpoint():
    """Get risk guidance for a trade (agentic approach)"""
    try:
        from src.agents.advanced_risk_manager import get_risk_manager
        from src.agents.regime_detector import get_regime_detector
        
        data = request.json
        
        # Get regime info
        detector = get_regime_detector()
        regime_info = detector.detect_regime()
        
        # Get risk manager
        rm = get_risk_manager()
        
        # Generate guidance
        guidance = rm.get_risk_guidance(
            balance=data.get('balance', 100000),
            entry_price=data.get('entry_price'),
            direction=data.get('direction', 'LONG'),
            confidence=data.get('confidence', 70),
            win_rate=data.get('win_rate', 0.50),
            atr=data.get('atr', data.get('entry_price', 50000) * 0.02),
            regime_info=regime_info,
            news_context=data.get('news_context', '')
        )
        
        return jsonify(guidance)
        
    except Exception as e:
        cprint(f"❌ Risk Guidance Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk/override-stats', methods=['GET'])
def get_override_stats():
    """Get statistics on risk guidance overrides"""
    try:
        from src.agents.advanced_risk_manager import get_risk_manager
        
        rm = get_risk_manager()
        agent_id = request.args.get('agent_id')
        
        stats = rm.get_override_success_rate(agent_id)
        
        return jsonify(stats)
        
    except Exception as e:
        cprint(f"❌ Override Stats Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

# ===== STRATEGY OPTIMIZER ENDPOINTS =====

@app.route('/api/optimizer/start', methods=['POST'])
def start_optimization():
    """Start strategy optimization for a ticker"""
    try:
        from src.agents.strategy_optimizer import optimize_strategy
        
        data = request.json
        symbol = data.get('symbol', 'TSLA').upper()
        trade_type = data.get('trade_type', 'swing')  # 'daytrade' or 'swing'
        max_bars = int(data.get('max_bars', 2000))  # Backtesting period in bars
        
        # Check if optimization already exists
        key = f"{symbol}_{trade_type}"
        if key in app.optimization_results_by_ticker:
            cprint(f"✅ Using cached results for {symbol} ({trade_type})", "green")
            # Set as current results
            persisted = app.optimization_results_by_ticker[key]
            app.optimization_results = {
                'all_results': persisted['all_results'],
                'symbol': persisted['symbol'],
                'trade_type': persisted['trade_type'],
                'timestamp': persisted['timestamp'],
                'source': 'cached'
            }
            return jsonify({
                'status': 'complete',
                'symbol': symbol,
                'trade_type': trade_type,
                'message': f'Using cached results for {symbol} ({trade_type})'
            })
        
        # Start optimization in background
        def run_optimization():
            try:
                result = optimize_strategy(symbol, trade_type, max_bars)
                # Store result in session
                app.optimization_results = result
                
                # Reload persisted results to include this new optimization
                load_latest_optimization_results()
                cprint(f"✅ Optimization complete for {symbol} ({trade_type})", "green")
            except Exception as e:
                print(f"❌ Optimization error: {e}")
                app.optimization_results = {'error': str(e)}
        
        thread = Thread(target=run_optimization, daemon=True)
        thread.start()
        
        return jsonify({
            'status': 'started',
            'symbol': symbol,
            'trade_type': trade_type,
            'message': f'Optimization started for {symbol} ({trade_type})'
        })
    
    except Exception as e:
        cprint(f"❌ Optimization Start Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimizer/results', methods=['GET'])
def get_optimization_results():
    """Get optimization results - checks in-memory first, then persisted"""
    try:
        # Get ticker and trade_type from query params
        ticker = request.args.get('ticker', '').upper()
        trade_type = request.args.get('trade_type', 'swing').lower()
        
        # First check in-memory results (current optimization)
        if hasattr(app, 'optimization_results') and app.optimization_results:
            return jsonify(app.optimization_results)
        
        # Then check persisted results by ticker
        if ticker and trade_type:
            key = f"{ticker}_{trade_type}"
            if key in app.optimization_results_by_ticker:
                persisted = app.optimization_results_by_ticker[key]
                # Convert to same format as in-memory results
                return jsonify({
                    'all_results': persisted['all_results'],
                    'symbol': persisted['symbol'],
                    'trade_type': persisted['trade_type'],
                    'timestamp': persisted['timestamp'],
                    'source': 'persisted'
                })
        
        return jsonify({'status': 'no_results', 'message': 'No optimization results available'})
    
    except Exception as e:
        cprint(f"❌ Results Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimizer/status', methods=['GET'])
def get_optimization_status():
    """Get optimization status"""
    try:
        if hasattr(app, 'optimization_results'):
            results = app.optimization_results
            if 'error' in results:
                return jsonify({'status': 'error', 'error': results['error']})
            else:
                return jsonify({'status': 'complete', 'results_available': True})
        else:
            return jsonify({'status': 'running', 'message': 'Optimization in progress'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimizer/best-combinations', methods=['GET'])
def get_best_combinations():
    """Get top parameter combinations from last optimization"""
    try:
        if hasattr(app, 'optimization_results') and 'best_combinations' in app.optimization_results:
            best = app.optimization_results['best_combinations']
            return jsonify({
                'combinations': best,
                'count': len(best),
                'symbol': app.optimization_results.get('symbol'),
                'trade_type': app.optimization_results.get('trade_type')
            })
        else:
            return jsonify({'error': 'No optimization results available'}), 404
    
    except Exception as e:
        cprint(f"❌ Best Combinations Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimizer/all-results', methods=['GET'])
def get_all_results():
    """Get all results grouped by timeframe"""
    try:
        if hasattr(app, 'optimization_results') and 'all_results' in app.optimization_results:
            all_results = app.optimization_results['all_results']
            
            # Convert to format suitable for frontend
            formatted = {}
            for timeframe, results in all_results.items():
                formatted[timeframe] = {
                    'count': len(results),
                    'top_3': results[:3] if results else [],
                    'best_sharpe': max([r['sharpe'] for r in results]) if results else 0,
                    'best_return': max([r['return'] for r in results]) if results else 0
                }
            
            return jsonify(formatted)
        else:
            return jsonify({'error': 'No optimization results available'}), 404
    
    except Exception as e:
        cprint(f"❌ All Results Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimizer/available-tickers', methods=['GET'])
def get_available_tickers():
    """Get list of all tickers that have been optimized"""
    try:
        tickers = {}
        for key, data in app.optimization_results_by_ticker.items():
            ticker = data['symbol']
            trade_type = data['trade_type']
            
            if ticker not in tickers:
                tickers[ticker] = []
            
            tickers[ticker].append({
                'trade_type': trade_type,
                'timestamp': data['timestamp']
            })
        
        return jsonify({
            'tickers': tickers,
            'count': len(tickers)
        })
    
    except Exception as e:
        cprint(f"❌ Available Tickers Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimizer/all-saved-results', methods=['GET'])
def get_all_saved_results():
    """Get TOP 1 combination for each saved ticker (best across all timeframes)"""
    try:
        cprint(f"\n{'='*70}", "cyan")
        cprint(f"📊 GET /api/optimizer/all-saved-results", "cyan")
        cprint(f"{'='*70}", "cyan")
        cprint(f"[DEBUG] Total tickers in cache: {len(app.optimization_results_by_ticker)}", "yellow")
        
        all_saved = []
        
        for key, data in app.optimization_results_by_ticker.items():
            ticker = data['symbol']
            trade_type = data['trade_type']
            all_results = data['all_results']
            
            cprint(f"\n🔍 Processing {ticker} ({trade_type})", "blue")
            timeframe_items = None
            if isinstance(all_results, dict):
                cprint(f"   Timeframes: {list(all_results.keys())}", "blue")
                timeframe_items = list(all_results.items())
            elif isinstance(all_results, list):
                cprint(
                    f"   Timeframes: Legacy list format detected (treating as 'all')",
                    "yellow",
                )
                timeframe_items = [("all", all_results)]
            else:
                cprint(
                    f"   ❌ SKIPPED: Unsupported results structure ({type(all_results).__name__})",
                    "red",
                )
                continue
            
            # Collect ALL valid combinations across ALL timeframes
            all_combinations = []
            for timeframe, results in timeframe_items:
                cprint(f"   ├─ {timeframe}: {len(results) if results else 0} results", "blue")
                
                if results and len(results) > 0:
                    valid_count = 0
                    for result in results:
                        # Only include if has trades AND sharpe is not None
                        trades = result.get('trades', 0)
                        sharpe = result.get('sharpe')
                        
                        if trades > 0 and sharpe is not None:
                            valid_count += 1
                            all_combinations.append({
                                'ticker': ticker,
                                'trade_type': trade_type,
                                'timeframe': timeframe,
                                'ma_length': result.get('ma_length'),
                                'key_value': result.get('key_value'),
                                'adaptive_atr_mult': result.get('adaptive_atr_mult'),
                                'tp1_rr_long': result.get('tp1_rr_long'),
                                'tp1_percent': result.get('tp1_percent'),
                                'sharpe': result.get('sharpe'),
                                'return': result.get('return'),
                                'win_rate': result.get('win_rate'),
                                'trades': result.get('trades'),
                                'max_dd': result.get('max_dd'),
                                'avg_trade': result.get('avg_trade'),
                                'buy_hold_return': result.get('buy_hold_return'),
                                'alpha': result.get('alpha'),
                                'duration_days': result.get('duration_days')
                            })
                    cprint(f"      ✅ Valid: {valid_count}/{len(results)}", "green")
            
            # Get TOP 1 for this ticker (best sharpe across all timeframes)
            if all_combinations:
                cprint(f"   Total combinations: {len(all_combinations)}", "yellow")
                # Sort by sharpe, handling None values
                all_combinations.sort(key=lambda x: x.get('sharpe') if x.get('sharpe') is not None else -999, reverse=True)
                # Only add if the best result has a valid sharpe
                best = all_combinations[0]
                if best.get('sharpe') is not None:
                    cprint(f"   ✅ ADDED: {ticker} ({best['timeframe']}) Sharpe={best['sharpe']:.2f}", "green")
                    all_saved.append(best)  # Only take the best one
                else:
                    cprint(f"   ❌ SKIPPED: Best result has no sharpe", "red")
            else:
                cprint(f"   ❌ SKIPPED: No valid combinations", "red")
        
        # Sort all tickers by sharpe ratio
        all_saved.sort(key=lambda x: x.get('sharpe', 0) or 0, reverse=True)
        
        cprint(f"\n{'='*70}", "cyan")
        cprint(f"📊 FINAL RESULT: {len(all_saved)} tickers to display", "cyan")
        cprint(f"{'='*70}\n", "cyan")
        
        return jsonify({
            'results': all_saved,
            'count': len(all_saved)
        })
    
    except Exception as e:
        cprint(f"❌ All Saved Results Error: {e}", "red")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimizer/delete/<symbol>/<trade_type>', methods=['DELETE'])
def delete_optimization(symbol, trade_type):
    """Delete optimization results for a ticker"""
    try:
        symbol = symbol.upper()
        trade_type = trade_type.lower()
        key = f"{symbol}_{trade_type}"
        
        # Remove from in-memory cache
        if key in app.optimization_results_by_ticker:
            del app.optimization_results_by_ticker[key]
            cprint(f"✅ Removed {symbol} ({trade_type}) from cache", "green")
        
        # Delete JSON files
        optimizations_dir = os.path.join(
            os.path.dirname(__file__),
            '..',
            'agents',
            '..',
            'data',
            'optimizations'
        )
        
        deleted_files = []
        if os.path.exists(optimizations_dir):
            for filename in os.listdir(optimizations_dir):
                if filename.startswith(f'optimization_{symbol}_{trade_type}_'):
                    filepath = os.path.join(optimizations_dir, filename)
                    os.remove(filepath)
                    deleted_files.append(filename)
                    cprint(f"✅ Deleted file: {filename}", "green")
        
        return jsonify({
            'status': 'success',
            'symbol': symbol,
            'trade_type': trade_type,
            'deleted_files': deleted_files
        })
    
    except Exception as e:
        cprint(f"❌ Delete Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

def run_agent_background():
    """Run agent in background"""
    global agent_running
    
    try:
        cycle = 0
        print(f"\n✨ Agent background loop started")
        while agent_running:
            cycle += 1
            try:
                # Get market state and make decision
                market_state = current_agent.get_market_state()
                decision = current_agent.make_decision(market_state)
                print(f"✅ Cycle {cycle}: {decision['signal']} ({decision['confidence']}%)")
                
            except Exception as cycle_error:
                print(f"⚠️ Error in cycle {cycle}: {str(cycle_error)[:100]}")
                # Continue running even if one cycle fails
            
            # Wait for next cycle
            if agent_running:
                time.sleep(current_agent.config.cycle_interval)
                
    except Exception as e:
        print(f"❌ Fatal error in agent background: {e}")
        agent_running = False

# ============================================================================
# OPTIONS PAPER TRADING ROUTES
# ============================================================================

import json
import os

# Path for persisting trades
TRADES_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'agbot_trades.json')
STATE_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'agbot_trading_state.json')

# Ensure data directory exists
os.makedirs(os.path.dirname(TRADES_FILE), exist_ok=True)

# Initialize Paper Trading Engine
from src.trading.paper_trading_engine import PaperTradingEngine

trading_engine = PaperTradingEngine(initial_balance=10000.00)

# Load persisted state on startup
if os.path.exists(STATE_FILE):
    trading_engine.load_state(STATE_FILE)
    cprint("✅ Loaded persisted trading state", "green")
else:
    cprint("✅ Initialized new trading engine with single $10k account", "green")
    cprint("   Trades will be tagged with timeframe for later filtering", "green")

@app.route('/agbot-trader')
def agbot_trader():
    """AGBot Trader - TradingView webhook integration"""
    return render_template('options_paper_trading.html')

@app.route('/api/paper-trading/state', methods=['GET'])
def get_paper_trading_state():
    """Get current paper trading state with unrealized PnL calculated"""
    try:
        state = trading_engine.get_account_state()
        
        # Calculate unrealized PnL for open positions
        # For now, use a simple estimate: assume price moved 1% from entry
        for pos in state.get('open_positions', []):
            if pos['status'] == 'OPEN':
                # Estimate current price (1% move from entry)
                current_price = pos['entry_price'] * 1.01
                contracts = pos.get('contracts', 1)
                
                # Calculate unrealized PnL
                # For options: (current_price - entry_price) * contracts * 100
                unrealized_pnl = (current_price - pos['entry_price']) * contracts * 100
                pos['unrealizedPnl'] = unrealized_pnl
        
        return jsonify(state)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/paper-trading/webhook', methods=['POST'])
def receive_webhook():
    """Receive webhook from TradingView and execute trades"""
    try:
        data = request.get_json()
        
        # Add timestamp
        data['timestamp'] = datetime.now().isoformat()
        
        # Check for duplicate webhooks (same action/ticker/contracts within 1 second)
        if trading_engine.account['webhooks']:
            last_webhook = trading_engine.account['webhooks'][0]
            last_time = datetime.fromisoformat(last_webhook.get('timestamp', '2000-01-01'))
            curr_time = datetime.fromisoformat(data['timestamp'])
            time_diff = (curr_time - last_time).total_seconds()
            
            # If same action/ticker/contracts within 1 second, skip
            if (time_diff < 1.0 and 
                last_webhook.get('action') == data.get('action') and
                last_webhook.get('ticker') == data.get('ticker') and
                last_webhook.get('contracts') == data.get('contracts')):
                cprint(f"⏭️ Skipping duplicate webhook (received {time_diff:.2f}s after previous)", "yellow")
                return jsonify({'success': True, 'message': 'Duplicate webhook skipped'}), 200
        
        # Execute trade using the paper trading engine
        result = trading_engine.execute_trade(data)
        
        # Store webhook in account
        trading_engine.account['webhooks'].insert(0, data)
        
        # Keep only last 100 webhooks
        if len(trading_engine.account['webhooks']) > 100:
            trading_engine.account['webhooks'] = trading_engine.account['webhooks'][:100]
        
        # Persist state
        trading_engine.save_state(STATE_FILE)
        
        # Return result
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'trade': result['trade'],
                'account_balance': result['account_balance'],
                'timeframe': result.get('timeframe', 'unknown')
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message'],
                'error': result['error'],
                'account_balance': result['account_balance']
            }), 400
    
    except Exception as e:
        cprint(f"❌ Webhook Error: {e}", "red")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/paper-trading/trade', methods=['POST'])
def add_paper_trade():
    """Manually add a trade (for testing or manual entry)"""
    try:
        trade_data = request.get_json()
        timeframe = trade_data.get('timeframe', 'manual')
        
        # Validate trade data
        required_fields = ['type', 'ticker', 'price', 'contracts', 'pnl']
        for field in required_fields:
            if field not in trade_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Add timestamp and timeframe
        trade_data['timestamp'] = datetime.now().isoformat()
        trade_data['exit_time'] = datetime.now().strftime('%b %d, %Y, %H:%M')
        trade_data['timeframe'] = timeframe
        
        # Update account balance
        trading_engine.account['account_balance'] += trade_data['pnl']
        
        # Add to trades list
        trading_engine.account['trades'].append(trade_data)
        
        # Persist state
        trading_engine.save_state(STATE_FILE)
        
        cprint(f"✅ Trade added: {trade_data['type']} {trade_data['ticker']} = {trade_data['pnl']:+.2f}", "green")
        
        return jsonify({
            'success': True,
            'trade': trade_data,
            'account_balance': trading_engine.account['account_balance'],
            'timeframe': timeframe
        })
    
    except Exception as e:
        cprint(f"❌ Add Trade Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

@app.route('/api/paper-trading/reset', methods=['POST'])
def reset_paper_trading():
    """Reset paper trading account"""
    try:
        # Reset single account
        trading_engine.account = {
            'account_balance': 10000.00,
            'initial_balance': 10000.00,
            'trades': [],
            'open_positions': [],
            'webhooks': []
        }
        
        cprint("🔄 Paper trading account reset", "yellow")
        
        trading_engine.save_state(STATE_FILE)
        
        return jsonify({
            'success': True,
            'message': 'Account reset to $10,000'
        })
    
    except Exception as e:
        cprint(f"❌ Reset Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

@app.route('/api/paper-trading/option-chain', methods=['GET'])
def get_option_chain():
    """Get option chain data from TastyTrade"""
    try:
        symbol = request.args.get('symbol', 'QQQ')
        dte = int(request.args.get('dte', 5))
        
        if not tastytrade_provider:
            return jsonify({
                'error': 'TastyTrade provider not initialized',
                'message': 'Add TASTYTRADE_OAUTH_TOKEN and TASTYTRADE_ACCOUNT_NUMBER to .env'
            }), 503
        
        # Get underlying price
        underlying_price = tastytrade_provider.get_underlying_price(symbol)
        
        if not underlying_price:
            return jsonify({'error': f'Could not get price for {symbol}'}), 500
        
        # Get option chain (this will need to be implemented in the provider)
        # For now, return mock data structure
        option_chain = {
            'symbol': symbol,
            'underlying_price': underlying_price,
            'dte': dte,
            'calls': [],
            'puts': []
        }
        
        cprint(f"📊 Option chain requested: {symbol} @ ${underlying_price:.2f}", "cyan")
        
        return jsonify(option_chain)
    
    except Exception as e:
        cprint(f"❌ Option Chain Error: {e}", "red")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🌙 Moon Dev's Trading Agent Web UI")
    print("="*70)
    print("\n🚀 Starting server...")
    print("📱 Open http://localhost:5000 in your browser\n")
    
    # Use use_reloader=False to prevent watchdog from interrupting requests
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
