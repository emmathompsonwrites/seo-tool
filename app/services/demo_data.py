"""
Realistic demo fixtures — mimics Etsy API responses.
Used when DEMO_MODE=True so the frontend can be built without API keys.
Flip DEMO_MODE=False in .env once real Etsy keys are configured.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# Shared fixture catalog — a dozen realistic grooming listings
_LISTING_TEMPLATES = [
    # (title, price_cents, shop_name, views, favorites, tags)
    ("Handmade Grooming Kit for Dogs", 3499, "WoofAndWhiskers", 4521, 312,
     ["dog grooming", "pet care", "handmade", "gift for dog", "grooming kit"]),
    ("Organic Pet Grooming Brush Set", 2499, "EcoPetCo", 2187, 189,
     ["pet brush", "organic", "eco friendly", "dog brush", "cat brush"]),
    ("Professional Dog Grooming Scissors", 5999, "GroomPros", 8934, 521,
     ["dog scissors", "grooming tools", "professional", "pet care", "handmade"]),
    ("Cat Grooming Glove - Self Cleaning", 1899, "PurrfectTools", 12453, 891,
     ["cat grooming", "self cleaning", "pet glove", "deshedding", "gift for cat"]),
    ("Pet Grooming Apron - Waterproof", 4299, "MakerAndPaw", 3421, 267,
     ["grooming apron", "waterproof", "pet care", "handmade", "dog grooming"]),
    ("Dog Grooming Table Arm - Adjustable", 8999, "GroomGearPro", 1189, 98,
     ["grooming table", "adjustable", "dog supplies", "professional", "pet care"]),
    ("Natural Pet Shampoo Bar - Oatmeal", 1299, "GreenPawsShop", 6721, 445,
     ["pet shampoo", "natural", "oatmeal", "organic", "eco friendly"]),
    ("Grooming Kit for Small Pets", 2799, "TinyPetCo", 2871, 214,
     ["small pet", "grooming kit", "hamster", "rabbit", "handmade"]),
    ("Pet Nail Clipper with LED Light", 1599, "PetCarePlus", 9342, 621,
     ["nail clipper", "LED", "pet care", "grooming tools", "dog nails"]),
    ("Dog Grooming Hammock - Nail Trim", 3899, "HappyHoundGoods", 5129, 389,
     ["grooming hammock", "nail trim", "dog supplies", "handmade", "pet care"]),
    ("Cat Brush for Shedding - Deshedding", 2199, "FelineFresh", 15234, 1087,
     ["cat brush", "deshedding", "shedding", "grooming", "cat supplies"]),
    ("Pet Grooming Vacuum Kit", 12999, "CleanPetCo", 892, 76,
     ["grooming vacuum", "pet vacuum", "grooming kit", "professional", "dog grooming"]),
]


def _make_listings(query: str) -> list[dict]:
    """Build a realistic list of Etsy-style listing dicts."""
    now = int(time.time())
    results = []
    for i, (title, amount, shop, views, favs, tags) in enumerate(_LISTING_TEMPLATES):
        results.append({
            "listing_id": 1000000 + i,
            "title": title,
            "description": f"Premium quality {title.lower()} — perfect for your pet.",
            "price": {"amount": amount, "divisor": 100, "currency_code": "USD"},
            "quantity": 50,
            "views": views,
            "num_favorers": favs,
            "tags": tags,
            "images": [],
            "url": f"https://www.etsy.com/listing/{1000000 + i}",
            "shop_name": shop,
            "shop_id": 5000 + i,
            "state": "active",
            "taxonomy_id": 1234,
            "original_creation_timestamp": now - (i + 1) * 86400 * 45,
            "processing_min": 1 + (i % 3),
            "processing_max": 3 + (i % 5),
        })
    return results


def demo_listings(query: str) -> dict:
    """Mimics GET /v3/application/listings/active response shape."""
    results = _make_listings(query)
    return {
        "count": 145723,
        "results": results,
    }


def demo_related_keywords(query: str) -> list[dict]:
    """Fixture for /api/keywords/related."""
    return [
        {
            "keyword": "dog grooming brush", "competition": 34, "competitionLevel": "fair",
            "difficulty": 42, "avgViews": 3200, "avgFavorites": 210, "favPerView": 6.5,
            "tagOccurrences": 18, "charCount": 18, "wordCount": 3, "googleSearches": 5400,
            "listingsByMonth": [12, 14, 11, 15, 18, 22, 25, 21, 19, 17, 20, 24],
            "trend": {"views": [], "favorites": [], "sales": []},
            "googleCompetition": "Low", "googleCompetitionIndex": 22,
            "googleCpcLow": 0.28, "googleCpcHigh": 0.95,
        },
        {
            "keyword": "cat grooming glove", "competition": 52, "competitionLevel": "mid",
            "difficulty": 58, "avgViews": 4100, "avgFavorites": 320, "favPerView": 7.8,
            "tagOccurrences": 22, "charCount": 18, "wordCount": 3, "googleSearches": 12100,
            "listingsByMonth": [15, 18, 22, 26, 31, 28, 24, 21, 19, 22, 26, 30],
            "trend": {"views": [], "favorites": [], "sales": []},
            "googleCompetition": "Medium", "googleCompetitionIndex": 48,
            "googleCpcLow": 0.42, "googleCpcHigh": 1.45,
        },
        {
            "keyword": "pet grooming kit", "competition": 78, "competitionLevel": "hard",
            "difficulty": 82, "avgViews": 8900, "avgFavorites": 512, "favPerView": 5.7,
            "tagOccurrences": 41, "charCount": 16, "wordCount": 3, "googleSearches": 33100,
            "listingsByMonth": [28, 32, 35, 41, 44, 48, 52, 49, 46, 43, 47, 51],
            "trend": {"views": [], "favorites": [], "sales": []},
            "googleCompetition": "High", "googleCompetitionIndex": 78,
            "googleCpcLow": 0.88, "googleCpcHigh": 2.30,
        },
        {
            "keyword": "pet grooming near me", "competition": 65, "competitionLevel": "warm",
            "difficulty": 71, "avgViews": 6200, "avgFavorites": 380, "favPerView": 6.1,
            "tagOccurrences": 27, "charCount": 22, "wordCount": 4, "googleSearches": 22200,
            "listingsByMonth": [22, 24, 21, 25, 28, 31, 29, 27, 24, 26, 30, 34],
            "trend": {"views": [], "favorites": [], "sales": []},
            "googleCompetition": "Medium", "googleCompetitionIndex": 61,
            "googleCpcLow": 0.65, "googleCpcHigh": 1.85,
        },
    ]


def demo_keyword_response(query: str, geo: str = "US") -> dict:
    """Full /api/keywords response with stats + analysis computed locally."""
    from app.services.scoring import (
        analyze_listings, difficulty_label, fav_per_view, heat_color,
    )

    listings = _make_listings(query)
    total = 145723

    views = [l["views"] for l in listings]
    hearts = [l["num_favorers"] for l in listings]
    avg_views = sum(views) / len(views)
    avg_hearts = sum(hearts) / len(hearts)

    density = total / len(listings)
    difficulty = min(100, max(0, 50 + (density - 5) * 2))

    prices = [l["price"]["amount"] / 100 for l in listings]
    avg_price = sum(prices) / len(prices)

    return {
        "success": True,
        "cached": False,
        "data": {
            "query": query,
            "stats": {
                "avgViews": round(avg_views, 1),
                "avgFavorites": round(avg_hearts, 1),
                "favPerView": round(fav_per_view(avg_hearts, avg_views), 2),
                "etsyCompetition": heat_color(min(100, density * 10)),
                "totalResults": total,
                "difficulty": round(difficulty, 1),
                "difficultyLabel": difficulty_label(difficulty),
                "avgPrice": round(avg_price, 2),
                "currency": "USD",
                "googleSearches": 8100,
                "googleStatus": "available",
                "googleCompetition": "Low",
                "googleCompetitionIndex": 22,
                "googleCpcLow": 0.35,
                "googleCpcHigh": 1.20,
                "googleCurrency": "USD",
            },
            "related": demo_related_keywords(query),
            "listings": listings,
            "analysis": analyze_listings(listings),
            "cachedAt": _now_iso(),
        },
        "searches": {"used": 1, "limit": 5},
        "state": {"credits": 4, "limit": 5, "usedToday": 1, "plan": "free", "bonus": 0},
    }


def demo_fx_response(frm: str, to: str) -> dict:
    """Fixture for /api/fx."""
    rates = {
        ("PKR", "USD"): 0.0036,
        ("USD", "PKR"): 278.5,
        ("EUR", "USD"): 1.08,
        ("USD", "EUR"): 0.926,
        ("GBP", "USD"): 1.27,
        ("USD", "GBP"): 0.787,
        ("CAD", "USD"): 0.74,
        ("USD", "CAD"): 1.35,
    }
    rate = rates.get((frm.upper(), to.upper()), 1.0)
    return {
        "success": True,
        "data": {"from": frm.upper(), "to": to.upper(), "rate": rate},
        "cached": False,
    }


def demo_trends_response(query: str, geo: str = "US") -> dict:
    """Fixture for /api/trends."""
    months = [
        "2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06",
        "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12",
    ]
    values = [42, 48, 55, 61, 58, 72, 80, 85, 78, 71, 82, 95]
    points = [{"month": m, "value": v} for m, v in zip(months, values)]

    return {
        "trends": [{"platform": "google", "points": points}],
        "countries": [],
        "supplyByMonth": [],
        "market": {
            "sample": 12,
            "currency": "USD",
            "priceMin": 12.99,
            "priceMax": 129.99,
            "priceMedian": 34.99,
            "priceP25": 21.99,
            "priceP75": 42.99,
            "priceBands": [
                {"label": "$0–$25", "count": 3},
                {"label": "$25–$50", "count": 5},
                {"label": "$50–$75", "count": 2},
                {"label": "$75–$100", "count": 1},
                {"label": "$100+", "count": 1},
            ],
            "viewsMedian": 4521,
            "viewsMax": 15234,
            "favMedian": 312,
            "favTotal": 5124,
            "engagementPct": 6.9,
            "topTags": [
                {"tag": "pet grooming", "count": 12, "pct": 100.0},
                {"tag": "dog grooming", "count": 7, "pct": 58.3},
                {"tag": "handmade", "count": 5, "pct": 41.7},
                {"tag": "pet care", "count": 5, "pct": 41.7},
                {"tag": "grooming kit", "count": 3, "pct": 25.0},
            ],
            "topListings": [],
        },
        "googleAvailable": True,
        "note": None,
        "googleStatus": "available",
        "marketplaceAvailable": True,
    }