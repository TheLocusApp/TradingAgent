"""
Real-time Quote Streaming Service using DXLink
Maintains a persistent connection for live price updates
"""

import asyncio
import os
from typing import Dict, List, Optional, Callable
from datetime import datetime, date
from termcolor import cprint
import threading
from tastytrade.dxfeed import EventType


class RealtimeQuoteStreamer:
    """Maintains persistent DXLink connection for real-time quotes"""
    
    def __init__(self):
        self.session = None
        self.streamer = None
        self.symbols_to_watch = set()  # Symbols currently subscribed
        self.pending_symbols = []  # Symbols waiting to be subscribed
        self.latest_quotes = {}  # {symbol: {bid, ask, mid, time}}
        self.is_running = False
        self.callbacks = []
        self.username = os.getenv('TASTYTRADE_USERNAME')
        self.password = os.getenv('TASTYTRADE_PASSWORD')
        self._quote_count = 0
        
    def _init_session(self):
        """Initialize Tastytrade session (called synchronously in thread)"""
        try:
            from tastytrade import Session
            
            if not self.username or not self.password:
                cprint("⚠️ TASTYTRADE_USERNAME or TASTYTRADE_PASSWORD not set in .env", "yellow")
                return False
            
            if not self.session:
                self.session = Session(login=self.username, password=self.password)
                cprint("✅ Tastytrade session authenticated", "green")
            return True
            
        except Exception as e:
            cprint(f"❌ Failed to initialize Tastytrade session: {e}", "red")
            return False
    
    async def _maintain_connection(self):
        """Maintain persistent DXLink connection with automatic reconnection"""
        try:
            if not self._init_session():
                cprint("⚠️ Cannot start streaming without Tastytrade session", "yellow")
                return
            
            from tastytrade import DXLinkStreamer
            from tastytrade.dxfeed import EventType
            
            reconnect_delay = 5
            
            while self.is_running:
                try:
                    cprint("📡 Establishing DXLink persistent connection...", "cyan")
                    
                    async with DXLinkStreamer(self.session) as streamer:
                        self.streamer = streamer
                        cprint("✅ DXLink connection established", "green")
                        
                        # Allow context manager async initialization to complete
                        await asyncio.sleep(0.1)  # Small delay for internal setup
                        
                        # Follow documented pattern strictly: subscribe first, then listen
                        if self.pending_symbols:
                            cprint("   📡 Subscribing to initial symbols...", "cyan")
                            await self._subscribe_pending()
                        
                        cprint("   👂 Starting quote listener...", "cyan")
                        await asyncio.gather(
                            self._quote_receiver(),
                            self._subscription_manager()
                        )
                
                except asyncio.CancelledError:
                    cprint("🛑 DXLink connection cancelled", "yellow")
                    break
                except Exception as e:
                    if self.is_running:
                        cprint(f"❌ DXLink connection error: {e}", "red")
                        cprint(f"   Reconnecting in {reconnect_delay}s...", "yellow")
                        await asyncio.sleep(reconnect_delay)
                        reconnect_delay = min(reconnect_delay * 2, 60)  # Exponential backoff, max 60s
                    else:
                        break
        
        except Exception as e:
            cprint(f"❌ Fatal streaming error: {e}", "red")
        finally:
            self.streamer = None
            self.is_running = False
            cprint(f"🛑 DXLink streaming stopped ({self._quote_count} total quotes)", "yellow")
    
    async def _subscription_manager(self):
        """Periodically check for new symbols to subscribe"""
        from tastytrade.dxfeed import EventType
        
        while self.is_running and self.streamer:
            try:
                await asyncio.sleep(1.0)  # Check every second
                
                if self.pending_symbols:
                    await self._subscribe_pending()
            
            except Exception as e:
                cprint(f"⚠️ Subscription manager error: {e}", "yellow")
    
    async def _subscribe_pending(self):
        """Subscribe to all pending symbols"""
        if not self.pending_symbols or not self.streamer:
            return
        
        # Defensive import in case module reload happens before global import executes
        from tastytrade.dxfeed import EventType as DXEventType
        
        # Get symbols that aren't already subscribed
        new_subs = [s for s in self.pending_symbols if s not in self.symbols_to_watch]
        self.pending_symbols.clear()
        
        if new_subs:
            try:
                cprint(f"📡 Subscribing to {len(new_subs)} symbols: {new_subs[:3]}...", "cyan")
                await self.streamer.subscribe(DXEventType.QUOTE, new_subs)
                self.symbols_to_watch.update(new_subs)
                cprint(f"✅ Subscribed successfully. Now tracking {len(self.symbols_to_watch)} symbols", "green")
            
            except KeyError as ke:
                # KeyError means channels don't exist - re-raise so caller can handle
                cprint(f"⚠️ KeyError during subscription (channels not ready): {ke}", "yellow")
                # Put symbols back in pending queue
                self.pending_symbols.extend(new_subs)
                raise  # Re-raise so caller knows to initialize channels
            except Exception as e:
                cprint(f"⚠️ Error subscribing to symbols: {e}", "yellow")
                import traceback
                traceback.print_exc()
                # Put symbols back in pending queue to retry
                self.pending_symbols.extend(new_subs)
    
    def _process_quote(self, quote):
        """Process a single quote - extract data and notify callbacks"""
        try:
            # Get symbol (try both attribute naming conventions)
            symbol = getattr(quote, 'eventSymbol', None) or getattr(quote, 'event_symbol', None)
            if not symbol:
                return
            
            self._quote_count += 1
            
            # Log first quote and every 50th
            if self._quote_count == 1 or self._quote_count % 50 == 0:
                cprint(f"📊 Received {self._quote_count} quotes (latest: {symbol})", "cyan")
            
            # Extract prices safely (try both naming conventions)
            bid = None
            ask = None
            
            bid_price = getattr(quote, 'bidPrice', None) or getattr(quote, 'bid_price', None)
            ask_price = getattr(quote, 'askPrice', None) or getattr(quote, 'ask_price', None)
            
            if bid_price:
                bid = float(bid_price)
            if ask_price:
                ask = float(ask_price)
            
            # Store quote
            self.latest_quotes[symbol] = {
                'bid': bid,
                'ask': ask,
                'mid': float((bid + ask) / 2) if bid and ask else None,
                'time': datetime.now().isoformat()
            }
            
            # Notify callbacks
            for callback in self.callbacks:
                try:
                    callback(symbol, self.latest_quotes[symbol])
                except Exception as cb_err:
                    cprint(f"⚠️ Callback error: {cb_err}", "yellow")
        except Exception as quote_err:
            cprint(f"⚠️ Error processing quote: {quote_err}", "yellow")
    
    async def _quote_receiver(self):
        """Listen for quotes after subscriptions are in place"""
        from tastytrade.dxfeed import EventType
        
        try:
            cprint("👂 Listening for quotes...", "cyan")
            async for quote in self.streamer.listen(EventType.QUOTE):
                self._process_quote(quote)
        except Exception as e:
            cprint(f"❌ Quote receiver error: {e}", "red")
    
    def subscribe_to_symbols(self, symbols: List[str]):
        """Add symbols to subscription queue (thread-safe)"""
        new_symbols = [s for s in symbols if s and s not in self.symbols_to_watch and s not in self.pending_symbols]
        if new_symbols:
            self.pending_symbols.extend(new_symbols)
            cprint(f"📋 Queued {len(new_symbols)} symbols for subscription", "cyan")
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get latest quote for a symbol"""
        return self.latest_quotes.get(symbol)
    
    def register_callback(self, callback: Callable):
        """Register callback for quote updates"""
        self.callbacks.append(callback)
    
    def start_streaming_thread(self):
        """Start streaming in background thread"""
        if self.is_running:
            cprint("⚠️ Streaming already running", "yellow")
            return
        
        self.is_running = True
        thread = threading.Thread(
            target=self._run_streaming_loop,
            daemon=True
        )
        thread.start()
        cprint("✅ DXLink streaming thread started", "green")
    
    def _run_streaming_loop(self):
        """Run event loop in thread"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._maintain_connection())
        except Exception as e:
            cprint(f"❌ Streaming thread error: {e}", "red")
        finally:
            self.is_running = False
    
    def stop_streaming(self):
        """Stop streaming"""
        self.is_running = False
        cprint("🛑 Stopping streaming...", "yellow")


class MarkToMarketEngine:
    """Calculate real-time PnL for open positions"""
    
    def __init__(self, quote_streamer: RealtimeQuoteStreamer):
        self.streamer = quote_streamer
        self.open_positions = []
        self.pnl_updates = {}
    
    def set_open_positions(self, positions: List[Dict]):
        """Set positions to track (filters expired options)"""
        self.open_positions = positions
        
        # Filter and subscribe to active symbols only
        symbols = []
        today = date.today()
        expired_count = 0
        
        for pos in positions:
            if pos.get('asset_type') == 'OPTION' and pos.get('option_symbol'):
                # Check if expired
                expiry_str = pos.get('expiry')
                if expiry_str:
                    try:
                        expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()
                        if expiry_date >= today:
                            symbols.append(pos.get('option_symbol'))
                        else:
                            expired_count += 1
                    except:
                        symbols.append(pos.get('option_symbol'))
                else:
                    symbols.append(pos.get('option_symbol'))
            elif pos.get('ticker'):
                symbols.append(pos.get('ticker'))
        
        if expired_count > 0:
            cprint(f"   ⏭️ Filtered {expired_count} expired options", "yellow")
        
        if symbols:
            # Remove duplicates
            unique_symbols = list(set(symbols))
            self.streamer.subscribe_to_symbols(unique_symbols)
            cprint(f"📊 MtM Engine: Tracking {len(unique_symbols)} active symbols from {len(positions)} positions", "green")
        else:
            cprint(f"⚠️ No active symbols to track", "yellow")
    
    def update_quote(self, symbol: str, quote: Dict):
        """Called when quote arrives - calculate PnL"""
        mid_price = quote.get('mid')
        if not mid_price:
            bid = quote.get('bid')
            ask = quote.get('ask')
            if bid and ask:
                mid_price = (bid + ask) / 2
            else:
                return
        
        # Find positions with this symbol
        for pos in self.open_positions:
            pos_symbol = pos.get('option_symbol') if pos.get('asset_type') == 'OPTION' else pos.get('ticker')
            
            if pos_symbol == symbol:
                self._calculate_pnl(pos, mid_price)
    
    def _calculate_pnl(self, position: Dict, current_price: float):
        """Calculate PnL for position"""
        try:
            pos_id = position.get('id')
            entry_price = position.get('entry_price', 0)
            contracts = position.get('contracts', 0)
            pos_type = position.get('type')  # BUY or SELL
            asset_type = position.get('asset_type')
            
            # Calculate PnL
            if asset_type == 'OPTION':
                # Options: 1 contract = 100 shares
                price_diff = current_price - entry_price
                if pos_type == 'BUY':
                    pnl = price_diff * contracts * 100
                else:  # SELL (short)
                    pnl = -price_diff * contracts * 100
            else:  # STOCK
                price_diff = current_price - entry_price
                if pos_type == 'BUY':
                    pnl = price_diff * contracts
                else:  # SELL (short)
                    pnl = -price_diff * contracts
            
            # Calculate PnL %
            cost_basis = position.get('cost_basis', 1)
            pnl_percent = (pnl / abs(cost_basis) * 100) if cost_basis else 0
            
            # Store update
            self.pnl_updates[pos_id] = {
                'pnl': round(pnl, 2),
                'pnl_percent': round(pnl_percent, 2),
                'mark_price': round(current_price, 2),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            cprint(f"⚠️ PnL calc error for {position.get('id')}: {e}", "yellow")
    
    def get_pnl_update(self, position_id: str) -> Optional[Dict]:
        """Get PnL for position"""
        return self.pnl_updates.get(position_id)
    
    def get_all_pnl_updates(self) -> Dict:
        """Get all PnL updates"""
        return self.pnl_updates.copy()


# Global instances
quote_streamer = None
mtm_engine = None


def initialize_realtime():
    """Initialize global realtime components"""
    global quote_streamer, mtm_engine
    
    quote_streamer = RealtimeQuoteStreamer()
    mtm_engine = MarkToMarketEngine(quote_streamer)
    
    # Register callback
    quote_streamer.register_callback(mtm_engine.update_quote)
    
    return quote_streamer, mtm_engine


def start_realtime_streaming():
    """Start the streaming service"""
    global quote_streamer
    
    if quote_streamer:
        quote_streamer.start_streaming_thread()
