"""
Scoring algorithm — mirrors RankKW's difficulty, competition, and analysis metrics.
All thresholds extracted from RankKW chunks (see handoff doc).
"""
from __future__ import annotations

import statistics
from typing import Any


# ---- Difficulty ----

def difficulty_label(difficulty: float) -> str:
    if difficulty < 35:
        return "Low"
    if difficulty < 55:
        return "Medium"
    return "High"


# ---- Competition heat ----

def heat_color(x: float) -> str:
    if x < 20:
        return "good"
    if x < 40:
        return "fair"
    if x < 60:
        return "mid"
    if x < 80:
        return "warm"
    return "hard"


HEAT_HEX = {
    "good": "#1F8A4C",
    "fair": "#4E9A3F",
    "mid": "#C08A12",
    "warm": "#D9702B",
    "hard": "#CF463A",
}


# ---- Formatters ----

def format_number(n: float) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(int(n))


def format_percent(x: float) -> str:
    return f"{x:.1f}%"


def shop_age_days(created_timestamp: int, now: int | None = None) -> int:
    import time
    now = now or int(time.time())
    return max(0, (now - created_timestamp) // 86400)


def shop_age_label(created_timestamp: int) -> str:
    days = shop_age_days(created_timestamp)
    if days < 30:
        return "under a month"
    if days < 365:
        return f"{days // 30} mo"
    return f"{days // 365} yr"


# ---- Listing analysis ----

def fav_per_view(num_favorers: int, views: int) -> float:
    if views <= 0:
        return 0.0
    return num_favorers / views * 100


def analyze_listings(listings: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute the `analysis` block from a list of ShopListing dicts.
    Mirrors RankKW's GET /api/keywords analysis shape.
    """
    if not listings:
        return {
            "listingsAnalyzed": 0,
            "averagePrice": 0,
            "medianPrice": 0,
            "averageHearts": 0,
            "totalViews": 0,
            "avgViews": 0,
            "avgDailyViews": 0,
            "avgWeeklyViews": 0,
            "currency": "USD",
            "priceSample": [],
            "tagCloud": [],
            "categories": [],
            "categoriesPending": True,
            "priceBuckets": [],
            "medianBucket": None,
            "priceOutliers": [],
            "ages": [],
            "medianAgeDays": 0,
            "processing": [],
            "avgProcessing": 0,
        }

    # Prices (amount / divisor)
    prices: list[float] = []
    for l in listings:
        p = l.get("price", {})
        amount = p.get("amount")
        divisor = p.get("divisor", 100)
        if amount is not None:
            prices.append(amount / divisor)

    currency = "USD"
    for l in listings:
        c = l.get("price", {}).get("currency_code")
        if c:
            currency = c
            break

    views = [l.get("views", 0) or 0 for l in listings]
    hearts = [l.get("num_favorers", 0) or 0 for l in listings]
    total_views = sum(views)
    avg_views = total_views / len(views) if views else 0

    # Ages
    import time
    now = int(time.time())
    ages_days = [
        shop_age_days(l.get("original_creation_timestamp") or l.get("creation_timestamp", now), now)
        for l in listings
    ]

    # Processing
    processing = [
        (l.get("processing_min", 0) or 0, l.get("processing_max", 0) or 0)
        for l in listings
    ]
    avg_processing = (
        sum((mn + mx) / 2 for mn, mx in processing) / len(processing)
        if processing else 0
    )

    # Tag cloud
    tag_counts: dict[str, int] = {}
    for l in listings:
        for tag in (l.get("tags") or []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    total_tag_occurrences = sum(tag_counts.values()) or 1
    tag_cloud = [
        {"tag": tag, "count": count, "pct": round(count / total_tag_occurrences * 100, 1)}
        for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])[:50]
    ]

    # Price buckets (simple quintiles over range)
    buckets = []
    median_bucket = None
    if prices:
        min_p, max_p = min(prices), max(prices)
        if max_p > min_p:
            step = (max_p - min_p) / 5
            for i in range(5):
                lo = min_p + i * step
                hi = min_p + (i + 1) * step
                label = f"${lo:.0f}–${hi:.0f}"
                count = sum(1 for p in prices if lo <= p < hi or (i == 4 and p == hi))
                buckets.append({"label": label, "value": (lo + hi) / 2, "count": count})
            median_bucket = buckets[2]["label"] if len(buckets) == 5 else None

    return {
        "listingsAnalyzed": len(listings),
        "averagePrice": round(statistics.mean(prices), 2) if prices else 0,
        "medianPrice": round(statistics.median(prices), 2) if prices else 0,
        "averageHearts": round(statistics.mean(hearts), 1) if hearts else 0,
        "totalViews": total_views,
        "avgViews": round(avg_views, 1),
        "avgDailyViews": round(avg_views / max(1, statistics.mean(ages_days)), 2) if ages_days else 0,
        "avgWeeklyViews": round(avg_views / max(1, statistics.mean(ages_days)) * 7, 1) if ages_days else 0,
        "currency": currency,
        "priceSample": sorted(prices)[:100],
        "tagCloud": tag_cloud,
        "categories": [],
        "categoriesPending": True,
        "priceBuckets": buckets,
        "medianBucket": median_bucket,
        "priceOutliers": [],
        "ages": [
            {"label": "under 1 mo", "count": sum(1 for d in ages_days if d < 30)},
            {"label": "1–6 mo", "count": sum(1 for d in ages_days if 30 <= d < 180)},
            {"label": "6–12 mo", "count": sum(1 for d in ages_days if 180 <= d < 365)},
            {"label": "1–2 yr", "count": sum(1 for d in ages_days if 365 <= d < 730)},
            {"label": "2+ yr", "count": sum(1 for d in ages_days if d >= 730)},
        ],
        "medianAgeDays": int(statistics.median(ages_days)) if ages_days else 0,
        "processing": [
            {"label": "1–3 days", "count": sum(1 for mn, mx in processing if mx <= 3)},
            {"label": "4–7 days", "count": sum(1 for mn, mx in processing if 3 < mx <= 7)},
            {"label": "8–14 days", "count": sum(1 for mn, mx in processing if 7 < mx <= 14)},
            {"label": "15+ days", "count": sum(1 for mn, mx in processing if mx > 14)},
        ],
        "avgProcessing": round(avg_processing, 1),
    }