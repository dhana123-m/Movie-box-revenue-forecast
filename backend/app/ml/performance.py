"""Box-office performance classification from a predicted revenue.

Classification is derived from the predicted revenue-to-budget multiplier:

    ratio = predicted_revenue / budget

The thresholds are defined in the application configuration
(``PERFORMANCE_THRESHOLDS``) and documented in feature_config.json. They are
industry heuristics, not guaranteed business rules.
"""

from typing import Any


def performance_labels(thresholds: dict[str, float]) -> list[str]:
    ordered = [
        "FLOP",
        "AVERAGE",
        "HIT",
        "SUPER_HIT",
        "BLOCKBUSTER",
    ]
    return [label for label in ordered if label in thresholds]


def classify_performance(
    predicted_revenue: float,
    budget: float,
    thresholds: dict[str, float],
) -> str:
    """Classify a predicted revenue into FLOP/AVERAGE/HIT/SUPER_HIT/BLOCKBUSTER.

    `thresholds` maps category -> revenue/budget ratio required to reach it.
    `thresholds` values must be ordered ascending by the caller.
    """
    if budget <= 0:
        budget = 1.0
    ratio = predicted_revenue / budget
    category = "FLOP"
    for label, threshold in thresholds.items():
        if ratio >= threshold:
            category = label
    return category
