#!/usr/bin/env python3
"""
🚀 AGBot Quick Start Script with UI
Starts ngrok tunnel and trading agent with status monitoring and control.
"""

import subprocess
import time
import sys
import os
from pathlib import Path
import requests
from termcolor import cprint
import threading
from datetime import datetime

# Add project root to path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)


class AGBotController:
    def __init__(self):
        self.ngrok_process = None
        self.agent_process = None
        self.webhook_url = None
        self.running = True
        self.ngrok_running = False
        self.agent_running = False
        self.lock = threading.Lock()
        
    def start_ngrok(self):
        """Start ngrok tunnel on port 5000"""
        if self.ngrok_running:
            cprint("⚠️  ngrok is already running", "yellow")
            return False
            
        try:
            cprint("🌐 Starting ngrok tunnel on port 5000...", "cyan")
            
            self.ngrok_process = subprocess.Popen(
                ["ngrok", "http", "5000"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give ngrok time to start
            time.sleep(3)
            
            # Get ngrok URL from API
            try:
                response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
                tunnels = response.json()["tunnels"]
                
                if tunnels:
                    public_url = tunnels[0]["public_url"]
                    self.webhook_url = f"{public_url}/api/paper-trading/webhook"
                    self.ngrok_running = True
                    cprint("✅ ngrok tunnel started successfully", "green")
                    return True
                else:
                    cprint("⚠️  No tunnels found in ngrok API response", "yellow")
                    self.ngrok_process.terminate()
                    self.ngrok_process = None
                    return False
                    
            except Exception as e:
                cprint(f"⚠️  Could not retrieve ngrok URL: {e}", "yellow")
                self.ngrok_process.terminate()
                self.ngrok_process = None
                return False
                
        except FileNotFoundError:
            cprint("❌ ngrok not found! Please install ngrok first.", "red")
            return False
        except Exception as e:
            cprint(f"❌ Error starting ngrok: {e}", "red")
            return False
    
    def stop_ngrok(self):
        """Stop ngrok tunnel"""
        if not self.ngrok_running:
            cprint("⚠️  ngrok is not running", "yellow")
            return False
            
        try:
            if self.ngrok_process:
                self.ngrok_process.terminate()
                self.ngrok_process.wait(timeout=5)
            self.ngrok_running = False
            self.webhook_url = None
            cprint("✅ ngrok tunnel stopped", "green")
            return True
        except Exception as e:
            cprint(f"❌ Error stopping ngrok: {e}", "red")
            return False
    
    def start_agent(self):
        """Start the Flask trading agent app"""
        if self.agent_running:
            cprint("⚠️  Trading Agent is already running", "yellow")
            return False
            
        try:
            cprint("🤖 Starting Trading Agent App...", "cyan")
            
            app_path = Path(__file__).parent / "src" / "web" / "app.py"
            
            if not app_path.exists():
                cprint(f"❌ App file not found: {app_path}", "red")
                return False
            
            self.agent_process = subprocess.Popen(
                [sys.executable, str(app_path)],
                cwd=str(Path(__file__).parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give app time to start
            time.sleep(2)
            
            if self.agent_process.poll() is None:
                self.agent_running = True
                cprint("✅ Trading Agent App started", "green")
                return True
            else:
                cprint("❌ Trading Agent failed to start", "red")
                return False
                
        except Exception as e:
            cprint(f"❌ Error starting trading agent: {e}", "red")
            return False
    
    def stop_agent(self):
        """Stop the trading agent app"""
        if not self.agent_running:
            cprint("⚠️  Trading Agent is not running", "yellow")
            return False
            
        try:
            if self.agent_process:
                self.agent_process.terminate()
                self.agent_process.wait(timeout=5)
            self.agent_running = False
            cprint("✅ Trading Agent stopped", "green")
            return True
        except Exception as e:
            cprint(f"❌ Error stopping Trading Agent: {e}", "red")
            return False
    
    def get_status(self):
        """Get current status"""
        status = {
            'ngrok': '🟢 RUNNING' if self.ngrok_running else '🔴 STOPPED',
            'agent': '🟢 RUNNING' if self.agent_running else '🔴 STOPPED',
            'webhook': self.webhook_url or 'N/A',
            'timestamp': datetime.now().strftime("%H:%M:%S")
        }
        return status
    
    def display_ui(self):
        """Display the main UI"""
        while self.running:
            os.system('cls' if os.name == 'nt' else 'clear')
            
            status = self.get_status()
            
            cprint("\n" + "="*80, "cyan")
            cprint("🚀 AGBot Controller", "cyan", attrs=["bold"])
            cprint("="*80 + "\n", "cyan")
            
            # Status section
            cprint("📊 STATUS", "white", attrs=["bold"])
            cprint("-" * 80, "white")
            cprint(f"  ngrok Tunnel:      {status['ngrok']}", "white")
            cprint(f"  Trading Agent:     {status['agent']}", "white")
            cprint(f"  Last Updated:      {status['timestamp']}", "white")
            
            # Webhook URL section
            if self.ngrok_running:
                cprint("\n🔗 WEBHOOK URL", "white", attrs=["bold"])
                cprint("-" * 80, "white")
                cprint(f"  {status['webhook']}", "yellow", attrs=["bold"])
                cprint("\n  💡 Copy this URL to your TradingView alert webhook field", "cyan")
            
            # Controls section
            cprint("\n⌨️  CONTROLS", "white", attrs=["bold"])
            cprint("-" * 80, "white")
            cprint("  [1] Start ngrok tunnel", "white")
            cprint("  [2] Stop ngrok tunnel", "white")
            cprint("  [3] Start Trading Agent", "white")
            cprint("  [4] Stop Trading Agent", "white")
            cprint("  [5] Start Both (tunnel + agent)", "white")
            cprint("  [6] Stop Both", "white")
            cprint("  [q] Quit", "white")
            cprint("\n" + "="*80 + "\n", "cyan")
            
            # Get user input
            try:
                choice = input("Enter command: ").strip().lower()
                
                if choice == '1':
                    self.start_ngrok()
                elif choice == '2':
                    self.stop_ngrok()
                elif choice == '3':
                    self.start_agent()
                elif choice == '4':
                    self.stop_agent()
                elif choice == '5':
                    self.start_ngrok()
                    time.sleep(1)
                    self.start_agent()
                elif choice == '6':
                    self.stop_agent()
                    time.sleep(0.5)
                    self.stop_ngrok()
                elif choice == 'q':
                    self.shutdown()
                    break
                else:
                    cprint("❌ Invalid command", "red")
                
                if choice in ['1', '2', '3', '4', '5', '6']:
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                self.shutdown()
                break
            except Exception as e:
                cprint(f"❌ Error: {e}", "red")
                time.sleep(1)
    
    def shutdown(self):
        """Shutdown all services"""
        cprint("\n\n🛑 Shutting down...", "yellow")
        
        if self.agent_running:
            self.stop_agent()
            time.sleep(0.5)
        
        if self.ngrok_running:
            self.stop_ngrok()
        
        self.running = False
        cprint("👋 Goodbye!\n", "cyan")


def main():
    """Main entry point"""
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    cprint(f"📁 Working directory: {os.getcwd()}\n", "cyan")
    
    controller = AGBotController()
    
    try:
        controller.display_ui()
    except KeyboardInterrupt:
        controller.shutdown()
    except Exception as e:
        cprint(f"❌ Fatal error: {e}", "red")
        controller.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()
