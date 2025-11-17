# ARCHIVED_FILES Index

**Archive Created**: November 17, 2025  
**Last Updated**: November 17, 2025 (Final cleanup - optimization scripts moved)  
**Total Files Archived**: 167  
**Archive Reason**: Cleanup of one-off troubleshooting, experimental, and temporary artifacts

---

## 📊 Summary by Category

| Category | Count | Location |
|----------|-------|----------|
| Debug Scripts | 15 | `debug_scripts/` |
| Integration Tests | 28 | `integration_tests/` |
| Optimization & Backtest | 25 | `optimization_backtest/` |
| Troubleshooting Notes | 74 | `troubleshooting_notes/` |
| Reference Guides | 25 | `reference_guides/` |
| **TOTAL** | **167** | |

---

## 🔍 DEBUG_SCRIPTS (15 files)

One-off scripts created to inspect SDK methods, debug authentication, and test API responses.

| File | Purpose | Type |
|------|---------|------|
| `check_equity_class.py` | Inspect Tastytrade Equity class methods | debug_script |
| `check_equity_methods.py` | List Equity class methods | debug_script |
| `check_instruments_funcs.py` | Check instrument functions available | debug_script |
| `check_option_chain_structure.py` | Inspect option chain data structure | debug_script |
| `check_quote_attributes.py` | Debug quote object attributes | debug_script |
| `check_quote_methods.py` | List quote methods | debug_script |
| `check_session_sig.py` | Verify session signature | debug_script |
| `check_tastytrade_sdk.py` | Verify SDK installation and version | debug_script |
| `debug_tastytrade_accounts.py` | Debug account retrieval from API | debug_script |
| `debug_tastytrade_auth.py` | Debug authentication response format | debug_script |
| `debug_yfinance.py` | Debug yfinance provider | debug_script |
| `test_json_file.py` | Test JSON file parsing | debug_script |
| `test_massive_api.py` | Test API with large payloads | debug_script |
| `test_session_format.py` | Validate session format | debug_script |
| `FIX_ANALYST.py` | One-off script to clean HTML garbage from analyst.html | debug_script |

**Key Insight**: These were used to understand SDK structure and debug integration issues. Most findings are now incorporated into main codebase.

---

## 🧪 INTEGRATION_TESTS (28 files)

Test files for specific phases, integrations, and features. Not part of maintained test suite.

| File | Purpose | Type |
|------|---------|------|
| `test_agbot_backtest.py` | Validate backtest results | debug_script |
| `test_agbot_matching_tradingview.py` | Verify TradingView signal matching | debug_script |
| `test_agbot_tradingview_params.py` | Validate TradingView parameter mapping | debug_script |
| `test_consistency_check.py` | Data consistency validation | debug_script |
| `test_dxlink_correct.py` | DXLink subscription test | debug_script |
| `test_dxlink_subscription.py` | DXLink quote streaming with options | debug_script |
| `test_dxlink_subscription2.py` | DXLink variant 2 | debug_script |
| `test_dxlink_subscription3.py` | DXLink variant 3 | debug_script |
| `test_hedge_fund_features.py` | Hedge fund feature validation | debug_script |
| `test_optimizer_1d.py` | 1D optimizer test | debug_script |
| `test_optimizer_4h.py` | 4H optimizer test | debug_script |
| `test_optimizer_direct.py` | Direct optimizer test | debug_script |
| `test_optimizer_fix.py` | Optimizer fix validation | debug_script |
| `test_optimizer_full.py` | Full optimizer test | debug_script |
| `test_optimizer_quick.py` | Quick optimizer test | debug_script |
| `test_phase2_integration.py` | Phase 2 integration test | debug_script |
| `test_phase3_4_integration.py` | Phase 3/4 integration test | debug_script |
| `test_phase3_phase4.py` | Phase 3/4 test | debug_script |
| `test_polygon_api.py` | Polygon API test | debug_script |
| `test_rbi_rl_implementation.py` | RBI + RL integration test | debug_script |
| `test_rl_implementation.py` | RL implementation test | debug_script |
| `test_simple_strategy.py` | Simple strategy test | debug_script |
| `test_strategy_optimizer.py` | Strategy optimizer test | debug_script |
| `test_tastytrade_auth.py` | Tastytrade auth test | debug_script |
| `test_tastytrade_oauth.py` | OAuth flow test | debug_script |
| `test_tastytrade_options.py` | Options API test | debug_script |
| `test_tastytrade_qqq_quotes.py` | QQQ quotes test | debug_script |
| `test_tastytrade_rest_endpoints.py` | REST endpoint test | debug_script |

**Key Insight**: These tests were created during phase development and integration. Most functionality is now covered by main test suite or integrated into core code.

---

## 📝 TROUBLESHOOTING_NOTES (74 files)

Status updates, fix documentation, and technical deep-dives from development iterations.

### Status/Completion Notes (Superseded)
- `ALL_5_ISSUES_FIXED.md`
- `ALL_ISSUES_ADDRESSED.md`
- `ALL_PHASES_COMPLETE.md`
- `ALL_REMAINING_ISSUES_COMPLETE.md`
- `AGENTIC_IMPLEMENTATION_COMPLETE.md`
- `ANALYST_100_PERCENT_COMPLETE.md`
- `ANALYST_ALL_FIXES_COMPLETE_NOV5.md`
- `ANALYST_ALL_FIXES_NOV4.md`
- `ANALYST_COMPLETE_NOV4_FINAL.md`
- `ANALYST_FINAL_FIXES_NOV5.md`
- `ANALYST_FINAL_IMPLEMENTATION_NOV4.md`
- `ANALYST_FINAL_STATUS_NOV4.md`
- `ANALYST_FIXES_APPLIED_NOV4.md`
- `ANALYST_FIXES_COMPLETE_NOV5.md`
- `ANALYST_IMPLEMENTATION_STATUS_NOV4.md`
- `ANALYST_PAGE_FIXES_NOV4.md`
- `ANALYST_REFINEMENTS_NOV4.md`
- `ANALYST_UX_FIXES_NOV5.md`
- `FINAL_IMPLEMENTATION_COMPLETE.md`
- `FINAL_UPDATES_COMPLETE.md`
- `FIXES_NOV5_FINAL.md`
- `FRONTEND_FIX_COMPLETE.md`
- `IMPLEMENTATION_COMPLETE_SUMMARY.md`
- `INTEGRATION_COMPLETE.md`
- `LATEST_FIX_ATTEMPT.md`
- `PHASE_2_COMPLETE.md`
- `PHASES_2_3_4_COMPLETE.md`
- `PHASE_3_4_COMPLETE.md`
- `THREE_ISSUES_FIXED.md`

### Technical Deep-Dives (Valuable Reference)
- `AGBOT_DEPLOYMENT_STRATEGY.md` – Strategy deployment patterns
- `AGBOT_DOWNTREND_SOLUTION.md` – Downtrend handling approach
- `AGBOT_EMA_FILTER_ANALYSIS.md` – EMA filter analysis
- `AGBOT_FINAL_ANSWER_DOWNTRENDS.md` – Downtrend solution
- `AGBOT_FINAL_RECOMMENDATION.md` – Final strategy recommendations
- `AGBOT_OPTIMIZATION_RESULTS.md` – Optimization results summary
- `AGBOT_SHORTS_ANALYSIS_COMPLETE.md` – Shorts strategy analysis
- `AGBOT_SWING_HIGH_BREAKTHROUGH.md` – Swing high breakthrough
- `BACKTEST_RESULTS_AGBOT_SHORTS.md` – Shorts backtest results
- `BEFORE_AFTER_COMPARISON.md` – DXLink streaming fix comparison
- `COMPREHENSIVE_REVIEW_SUMMARY.md` – Comprehensive review
- `CRITICAL_FIX_PYTHON_CACHE.md` – Python cache fix
- `CRITICAL_RECOMMENDATIONS.md` – Critical recommendations
- `DTE_ANALYSIS_12HR_HOLDS.md` – DTE analysis for 12-hour holds
- `DXLINK_FIX_SUMMARY.md` – DXLink async context manager fix
- `FINAL_DEPLOYMENT_GUIDE.md` – Deployment guide
- `FINAL_FIX_ANALYSIS.md` – Final fix analysis
- `FINAL_SUMMARY.md` – Final summary
- `INTEGRATION_CHECKLIST.md` – Integration checklist
- `MONITOR_OPTIMIZATION.md` – Optimization monitoring
- `NAN_FIX_COMPLETE.md` – NaN handling fix
- `OPTIONS_FIXES_NOV4.md` – Options fixes (Nov 4)
- `OPTIONS_FIXES_NOV5_PART2.md` – Options fixes (Nov 5 part 2)
- `OPTIONS_POSITION_BUG_FIX_NOV5.md` – Options position tracking fix
- `OPTIONS_POSITION_TRACKING_FIX.md` – Position tracking fix
- `OPTIONS_TRACKING_FIX_NOV5.md` – Options tracking fix
- `PAPER_TRADING_CLARIFICATIONS.md` – Paper trading clarifications
- `PAPER_TRADING_ENGINE_REVIEW.md` – Paper trading engine review
- `PAPER_TRADING_FIXED.md` – Paper trading fixes
- `PHASE_2_3_4_INTEGRATION.md` – Phase 2/3/4 integration
- `POLYGON_API_FIX.md` – Polygon API fix
- `PROMPT_INJECTION_EXAMPLES.md` – Prompt injection examples
- `RBI_COMPREHENSIVE_FIX_NOV10.md` – RBI comprehensive fix
- `RBI_FIXES_SUMMARY.md` – RBI fixes summary
- `RBI_V3_CRITICAL_FAILURES_ANALYSIS_NOV9.md` – RBI V3 critical failures
- `RBI_V3_CRITICAL_FIXES_NOV8.md` – RBI V3 critical fixes
- `RBI_V3_NEXT_ACTIONS_NOV9.md` – RBI V3 next actions
- `RBI_V3_TESTING_GUIDE.md` – RBI V3 testing guide
- `ROOT_CAUSE_ANALYSIS_COMPLETE.md` – Root cause analysis
- `SHORTS_OPTIMIZATION_RESULTS.md` – Shorts optimization results
- `STRATEGY_OPTIMIZER_COMPREHENSIVE_REVIEW.md` – Strategy optimizer review
- `STRATEGY_OPTIMIZER_TIMEOUT_FIX.md` – Timeout fix
- `WEBHOOK_FORMAT_CORRECTION.md` – Webhook format fix
- `VIX_COMPASS_FIXES.md` – VIX Compass fixes

**Key Insight**: These documents capture the iterative development process. Many contain valuable debugging patterns and solutions now integrated into core code.

---

## 📚 REFERENCE_GUIDES (36 files)

Guides, implementation docs, and feature documentation. Valuable for understanding system architecture.

| File | Purpose |
|------|---------|
| `AGBOT_OPTIONS_PUTS_GUIDE.md` | Options puts trading guide |
| `AGBOT_OPTIONS_QUICK_REFERENCE.md` | Quick reference for options |
| `AGBOT_TRADER_QUICK_START.md` | Quick start guide |
| `ANALYST_FRONTEND_READY.md` | Analyst frontend status |
| `FRONTEND_IMPLEMENTATION_GUIDE.md` | Frontend implementation guide |
| `HEDGE_FUND_FEATURES_IMPLEMENTATION.md` | Hedge fund features guide |
| `HOW_TO_TEST.md` | Testing guide |
| `NEXT_STEPS.md` | Next steps document |
| `OPTIMAL_QQQ_OPTIONS_STRATEGY.md` | QQQ options strategy |
| `OPTIMIZER_CONFIG_FINAL.md` | Optimizer configuration |
| `OPTIONS_TRADING_COMPLETE.md` | Options trading implementation |
| `OPTIONS_TRADING_GUIDE.md` | Options trading guide |
| `OPTIONS_TRADING_IMPLEMENTATION.md` | Options implementation |
| `PAPER_TRADING_SETUP.md` | Paper trading setup |
| `PAPER_TRADING_UPDATES_NOV9.md` | Paper trading updates |
| `PHASE_2_IMPLEMENTATION.md` | Phase 2 implementation |
| `PHASE_2_QUICK_START.md` | Phase 2 quick start |
| `PHASE_2_SUMMARY.md` | Phase 2 summary |
| `PHASE_3_4_INTEGRATION_SUMMARY.md` | Phase 3/4 integration |
| `QUICK_REFERENCE.md` | Quick reference |
| `QUICK_START_NEW_FEATURES.md` | New features quick start |
| `RISK_MANAGER_INTEGRATION.md` | Risk manager integration |
| `RL_EXECUTIVE_SUMMARY.md` | RL executive summary |
| `RL_IMPLEMENTATION_SUMMARY.md` | RL implementation |
| `RL_INTEGRATION_FIX_NOV6.md` | RL integration fix |
| `RL_INTEGRATION_ROADMAP.md` | RL integration roadmap |
| `RL_LIVE_TRADING_INTEGRATION.md` | RL live trading integration |
| `RL_OPTIMIZATION_GUIDE.md` | RL optimization guide |
| `RL_OPTIMIZER_FIX.md` | RL optimizer fix |
| `RL_TRAINING_COUNTER_FIX.md` | RL training counter fix |
| `RL_TRAINING_DEBUG.md` | RL training debug |
| `RL_UI_REFERENCE.md` | RL UI reference |
| `STRATEGY_OPTIMIZER_GUIDE.md` | Strategy optimizer guide |
| `STRATEGY_OPTIMIZER_IMPLEMENTATION.md` | Strategy optimizer implementation |
| `STRATEGY_OPTIMIZER_READY.md` | Strategy optimizer ready |
| `TASTYTRADE_OPTIONS_INTEGRATION.md` | Tastytrade options integration |
| `TRADINGVIEW_WEBHOOK_SETUP.md` | TradingView webhook setup |
| `UPDATES_NOV9_PART2.md` | Updates (Nov 9 part 2) |
| `VIX_COMPASS_FINAL.md` | VIX Compass final |
| `VIX_COMPASS_IMPLEMENTATION.md` | VIX Compass implementation |
| `WEBHOOK_TRADING_ENGINE_PLAN.md` | Webhook trading engine plan |

**Key Insight**: These guides document major features and integrations. Useful for understanding system design and troubleshooting similar issues.

---

## 📋 FILES KEPT IN ROOT (Not Archived)

### Optimization & Backtest Scripts (Category 2 - KEPT)
- `backtest_agbot_final.py`
- `backtest_agbot_shorts_optimized.py`
- `backtest_agbot_simple.py`
- `extract_shorts_parameters.py`
- `generate_modern_ui.py`
- `manual_optimize_agbot.py`
- `monitor_optimization.py`
- `optimize_agbot.py`
- `optimize_agbot_4h.py`
- `optimize_agbot_shorts_asymmetric.py`
- `optimize_agbot_shorts_only.py`
- `optimize_agbot_shorts_with_ema_filter.py`
- `optimize_bb_rsi_shorts.py`
- `optimize_longs_primary_shorts_hedge.py`
- `optimize_shorts_downtrend_swing_high.py`
- `optimize_shorts_swing_high.py`
- `run_agbot_rbi_optimization.py`

### Temporary Data (Category 5 - KEPT)
- `app_error.txt`
- `app_output.txt`
- `NEW_CARD_FUNCTION.txt`
- `agbot_optimization_results.csv`
- `agbot_4h_optimization_results.csv`
- `shorts_optimization_results.csv`
- `agbot_shorts_optimized_backtest.html`

### Pine Script Variants (Category 6 - KEPT)
- `AGBotGeneric.pine` (base strategy)
- `AGBotGeneric_DYNAMIC_REGIME.pine`
- `AGBotGeneric_EMA_Ribbon_Filter.pine`
- `AGBotGeneric_META_Optimized.pine`
- `AGBotGeneric_NVDA_Optimized.pine`
- `AGBotGeneric_OPTIONS_Puts_Strategy.pine`
- `AGBotGeneric_QQQ_Shorts_Optimized.pine`
- `AGBotGeneric_SHORTS_OPTIMIZED.pine`
- `AGBotGeneric_UNIFIED_Longs_Shorts.pine`

### Utility Scripts (Category 7 - KEPT)
- `reset_agents.ps1`
- `setup_windows.ps1`
- `restart_server.bat`

### Core Files (Always Kept)
- `requirements.txt`
- `.env` & `.env_example`
- `.gitignore`
- All files in `src/`, `docs/`, `data/`

---

## 🔗 Related Documents

- **LESSONS_LEARNED.md** – Key insights extracted from archived files
- **../README.md** – Main project documentation

---

## 📌 Notes

- All files moved using git-safe operations (rename/move, not recreate)
- Git history preserved for all archived files
- No secrets or sensitive data archived
- Archive created to reduce root directory clutter while preserving knowledge base

