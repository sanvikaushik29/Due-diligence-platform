GROUND_TRUTH = {
    "solvia": {
        "files": ["Solvia_Pitch_Deck.pdf"],
        "expected_discrepancy_metrics": ["Funding Ask"],
        "expected_unsupported_substrings": [
            "market leader",
            "reduces unnecessary spending by 40%",
            "most trusted financial coaching brand",
            "Break-even projected in Year 2",
        ],
        "min_metrics_expected": 10,
    },
    "ecocart": {
        "files": ["EcoCart_Pitch_Deck.pdf", "EcoCart_Pitch_Deck_v2.pdf"],
        "expected_discrepancy_metrics": ["Funding Ask"],
        "expected_unsupported_substrings": [
            "struggle to identify sustainable",
            "Growing grocery-tech",
            "scans products, recommends greener",
            "Barcode scanner, AI insights",
        ],
        "min_metrics_expected": 15,
    },
    "northfield_messy_scan": {
        "files": ["Northfield_Messy_Scan.pdf"],
        "expected_discrepancy_metrics": ["Funding Ask"],
        "expected_unsupported_substrings": [
            "fastest-growing last-mile platform",
            "default infrastructure",
        ],
        "min_metrics_expected": 5,
        "expect_ocr": True,
    },
}