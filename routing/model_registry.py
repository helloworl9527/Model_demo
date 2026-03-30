REGISTRY = {
    "finance_review": {
        "assigned_model": "finance-specialist-v1",
        "assigned_tools": ["ledger_checker", "expense_anomaly_detector"]
    },
    "contract_tender_check": {
        "assigned_model": "contract-specialist-v1",
        "assigned_tools": ["bid_rule_checker", "clause_diff_tool"]
    },
    "inventory_count": {
        "assigned_model": "inventory-specialist-v1",
        "assigned_tools": ["stock_reconcile_tool", "variance_detector"]
    },
    "rd_decision_eval": {
        "assigned_model": "rd-specialist-v1",
        "assigned_tools": ["meeting_minutes_checker", "approval_path_validator"]
    }
}