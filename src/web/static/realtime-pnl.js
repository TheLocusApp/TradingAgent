/**
 * Real-Time PnL Updates via WebSocket
 * Connects to Flask-SocketIO server for live trade updates
 */

class RealtimePnLManager {
    constructor() {
        this.socket = null;
        this.pnlUpdates = {};
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000; // 3 seconds
        
        this.init();
    }
    
    init() {
        // Connect to WebSocket server
        try {
            // For Socket.IO v5+
            this.socket = io(window.location.origin, {
                reconnection: true,
                reconnectionDelay: this.reconnectDelay,
                reconnectionAttempts: this.maxReconnectAttempts,
                transports: ['websocket', 'polling']
            });
            
            this.setupEventListeners();
            console.log('🔌 WebSocket manager initialized');
        } catch (e) {
            console.warn('⚠️ WebSocket not available:', e);
        }
    }
    
    setupEventListeners() {
        if (!this.socket) return;
        
        this.socket.on('connect', () => {
            this.isConnected = true;
            this.reconnectAttempts = 0;
            console.log('✅ Connected to trading server');
            
            // Subscribe to PnL updates
            this.socket.emit('subscribe_pnl');
        });
        
        this.socket.on('disconnect', () => {
            this.isConnected = false;
            console.log('❌ Disconnected from trading server');
        });
        
        this.socket.on('pnl_update', (data) => {
            this.onPnLUpdate(data);
        });
        
        this.socket.on('subscription_response', (data) => {
            console.log('📊 PnL subscription:', data.message);
        });
        
        this.socket.on('connection_response', (data) => {
            console.log('🎯 Server response:', data.data);
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('❌ Connection error:', error);
        });
    }
    
    onPnLUpdate(data) {
        if (!data.updates) return;
        
        // Update internal state
        Object.assign(this.pnlUpdates, data.updates);
        
        // Update UI
        this.updateTradesTable();
        this.updatePositionsPanel();
    }
    
    updateTradesTable() {
        // Find all trade rows in the page
        const rows = document.querySelectorAll('[data-position-id]');
        
        rows.forEach(row => {
            const posId = row.dataset.positionId;
            if (!posId || !this.pnlUpdates[posId]) return;
            
            const update = this.pnlUpdates[posId];
            
            // Update PnL cell
            const pnlCell = row.querySelector('[data-field="pnl"]');
            if (pnlCell) {
                const pnlValue = update.pnl.toFixed(2);
                pnlCell.textContent = `$${pnlValue}`;
                pnlCell.style.color = update.pnl >= 0 ? '#22c55e' : '#ef4444';
            }
            
            // Update PnL % cell
            const pnlPercentCell = row.querySelector('[data-field="pnl_percent"]');
            if (pnlPercentCell) {
                const pnlPercent = update.pnl_percent.toFixed(2);
                pnlPercentCell.textContent = `${pnlPercent}%`;
                pnlPercentCell.style.color = update.pnl_percent >= 0 ? '#22c55e' : '#ef4444';
            }
            
            // Update mark price cell
            const markCell = row.querySelector('[data-field="mark_price"]');
            if (markCell) {
                markCell.textContent = `$${update.mark_price.toFixed(2)}`;
            }
            
            // Update timestamp
            const timeCell = row.querySelector('[data-field="update_time"]');
            if (timeCell) {
                const time = new Date(update.timestamp);
                timeCell.textContent = time.toLocaleTimeString();
            }
        });
    }
    
    updatePositionsPanel() {
        // Update position cards or summary panel
        const positionsPanel = document.getElementById('open-positions-panel');
        if (!positionsPanel) return;
        
        let totalPnL = 0;
        let totalPnLPercent = 0;
        let positionCount = 0;
        
        Object.values(this.pnlUpdates).forEach(update => {
            totalPnL += update.pnl;
            totalPnLPercent += update.pnl_percent;
            positionCount++;
        });
        
        // Update summary if element exists
        const totalPnLElement = document.getElementById('total-pnl');
        if (totalPnLElement && positionCount > 0) {
            totalPnLElement.textContent = `$${totalPnL.toFixed(2)}`;
            totalPnLElement.style.color = totalPnL >= 0 ? '#22c55e' : '#ef4444';
        }
    }
    
    getPnL(positionId) {
        return this.pnlUpdates[positionId];
    }
    
    getAllPnL() {
        return {...this.pnlUpdates};
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.isConnected = false;
        }
    }
}

// Initialize on page load
let pnlManager = null;

document.addEventListener('DOMContentLoaded', () => {
    pnlManager = new RealtimePnLManager();
    console.log('🚀 Real-time PnL manager started');
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (pnlManager) {
        pnlManager.disconnect();
    }
});

