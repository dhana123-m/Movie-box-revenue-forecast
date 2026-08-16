"""Currency and number formatting helpers for API responses."""

from __future__ import annotations

from ..config import settings


def format_usd(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f} B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:,.2f} M"
    if value >= 1_000:
        return f"${value / 1_000:,.1f} K"
    return f"${value:,.0f}"


def format_million(value: float) -> str:
    return f"${value / 1_000_000:,.2f}M"


def format_crore(value: float, inr_per_usd: float | None = None) -> str:
    """Convert USD to Indian crore (₹) for display convenience."""
    rate = inr_per_usd or settings.INR_PER_USD
    crore = value * rate / 10_000_000
    return f"₹{crore:,.2f} Cr"


def format_lakh(value: float, inr_per_usd: float | None = None) -> str:
    rate = inr_per_usd or settings.INR_PER_USD
    lakh = value * rate / 100_000
    return f"₹{lakh:,.2f} L"
