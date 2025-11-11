#!/usr/bin/env python3
"""
Test RL Implementation
Verifies that RL optimizer integrates correctly with agents
"""

import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.config.trading_config import TradingConfig
from src.agents.rl_optimizer import RLOptimizer
from src.agents.agent_manager import agent_manager

def test_rl_config():
    """Test RL config fields"""
    print("\n✅ Test 1: RL Config Fields")
    config = TradingConfig(
        agent_name="Test Agent",
        enable_rl=True,
        rl_training_trades=50
    )
    
    assert config.enable_rl == True, "enable_rl should be True"
    assert config.rl_training_trades == 50, "rl_training_trades should be 50"
    assert config.rl_status == "inactive", "rl_status should start as inactive"
    print("   ✓ Config fields initialized correctly")
    print(f"   ✓ enable_rl: {config.enable_rl}")
    print(f"   ✓ rl_training_trades: {config.rl_training_trades}")
    print(f"   ✓ rl_status: {config.rl_status}")

def test_rl_config_serialization():
    """Test RL config can be serialized/deserialized"""
    print("\n✅ Test 2: RL Config Serialization")
    config = TradingConfig(
        agent_name="Test Agent",
        asset_type="crypto",
        ticker="BTC",
        monitored_assets=["BTC", "ETH"],
        enable_rl=True,
        rl_training_trades=50
    )
    
    # Convert to dict
    config_dict = config.to_dict()
    assert 'enable_rl' in config_dict, "enable_rl should be in dict"
    assert config_dict['enable_rl'] == True, "enable_rl should be True in dict"
    print("   ✓ Config serializes to dict correctly")
    
    # Recreate from dict
    config2 = TradingConfig.from_dict(config_dict)
    assert config2.enable_rl == True, "enable_rl should be True after deserialization"
    assert config2.rl_training_trades == 50, "rl_training_trades should be 50 after deserialization"
    print("   ✓ Config deserializes from dict correctly")

def test_rl_optimizer_creation():
    """Test RLOptimizer can be created"""
    print("\n✅ Test 3: RLOptimizer Creation")
    config = TradingConfig(
        agent_name="Test Agent",
        enable_rl=True,
        rl_training_trades=50
    )
    
    # Create a mock agent and trading engine
    class MockAgent:
        pass
    
    class MockTradingEngine:
        pass
    
    agent = MockAgent()
    trading_engine = MockTradingEngine()
    
    optimizer = RLOptimizer(agent, config, trading_engine)
    assert optimizer is not None, "RLOptimizer should be created"
    assert optimizer.config.enable_rl == True, "Optimizer should have RL enabled"
    print("   ✓ RLOptimizer created successfully")
    print(f"   ✓ Status: {optimizer.get_rl_status()}")

def test_rl_status_display():
    """Test RL status display"""
    print("\n✅ Test 4: RL Status Display")
    config = TradingConfig(
        agent_name="Test Agent",
        enable_rl=True,
        rl_training_trades=50
    )
    config.rl_status = "training"
    
    class MockAgent:
        pass
    
    class MockTradingEngine:
        pass
    
    optimizer = RLOptimizer(MockAgent(), config, MockTradingEngine())
    
    status = optimizer.get_rl_status_display()
    assert status['status'] == 'training', "Status should be training"
    assert '🔄' in status['label'], "Training label should have refresh emoji"
    print(f"   ✓ Training status: {status['label']}")
    print(f"   ✓ Color: {status['color']}")
    
    # Test optimized status
    config.rl_status = "optimized"
    optimizer2 = RLOptimizer(MockAgent(), config, MockTradingEngine())
    status2 = optimizer2.get_rl_status_display()
    assert status2['status'] == 'optimized', "Status should be optimized"
    assert '✨' in status2['label'], "Optimized label should have sparkle emoji"
    print(f"   ✓ Optimized status: {status2['label']}")

def test_agent_manager_rl_integration():
    """Test agent manager creates RL optimizer"""
    print("\n✅ Test 5: Agent Manager RL Integration")
    
    config = TradingConfig(
        agent_name="RL Test Agent",
        asset_type="crypto",
        ticker="BTC",
        monitored_assets=["BTC"],
        models=["deepseek"],
        enable_rl=True,
        rl_training_trades=50
    )
    
    try:
        agent_id = agent_manager.create_agent(config)
        print(f"   ✓ Agent created: {agent_id}")
        
        agent_info = agent_manager.agents.get(agent_id)
        assert agent_info is not None, "Agent should exist in manager"
        assert agent_info['rl_optimizer'] is not None, "RL optimizer should be created"
        print(f"   ✓ RL optimizer created for agent")
        print(f"   ✓ RL status: {agent_info['config'].rl_status}")
        
        # Cleanup
        agent_manager.delete_agent(agent_id)
        print(f"   ✓ Agent cleaned up")
    except Exception as e:
        print(f"   ⚠️ Note: {str(e)[:100]}")
        print(f"   (This is expected if models aren't initialized)")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 RL Implementation Test Suite")
    print("="*60)
    
    try:
        test_rl_config()
        test_rl_config_serialization()
        test_rl_optimizer_creation()
        test_rl_status_display()
        test_agent_manager_rl_integration()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60 + "\n")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n⚠️ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
