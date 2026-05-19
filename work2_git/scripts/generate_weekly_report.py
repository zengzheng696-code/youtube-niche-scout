#!/usr/bin/env python3
"""Generate a weekly UK pet product sniffing report from YouTube Data API.

The report uses YouTube as a content-demand signal, not as proof of sales.
Missing API credentials disable live collection instead of fabricating data.
Use --fixture for local tests and demos.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import math
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "sample_signals.json"

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_COMMENTS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"

EXCLUDED_TERMS = (
    "food",
    "treat",
    "treats",
    "supplement",
    "supplements",
    "medicine",
    "medication",
    "drug",
    "vitamin",
    "freeze-dried",
    "freeze dried",
    "raw diet",
)

PAIN_WORDS = (
    "problem",
    "need",
    "wish",
    "help",
    "mess",
    "smell",
    "mud",
    "dirty",
    "stress",
    "anxiety",
    "bored",
    "leak",
    "hard to clean",
    "small flat",
    "renter",
    "replacement",
)

SEED_QUERIES = [
    "pet gadgets",
    "dog gadgets",
    "cat gadgets",
    "pet cleaning hacks",
    "dog cleaning routine",
    "cat enrichment ideas",
    "small apartment cat setup",
    "dog travel accessories",
    "pet product review",
    "amazon pet finds",
    "pet organization hacks",
    "new pet products",
]

PRODUCT_TERMS = (
    "washer",
    "cleaner",
    "brush",
    "comb",
    "mat",
    "lick mat",
    "slow feeder",
    "fountain",
    "filter",
    "dispenser",
    "bag",
    "cover",
    "hammock",
    "seat",
    "carrier",
    "leash",
    "harness",
    "collar",
    "toy",
    "puzzle",
    "perch",
    "shelf",
    "bed",
    "stairs",
    "ramp",
    "gate",
    "camera",
    "tracker",
    "vacuum",
    "litter box",
    "scoop",
    "spray",
    "dryer",
    "towel",
    "bowl",
)

GENERIC_PRODUCT_TERMS = {
    "mat",
    "toy",
    "cover",
    "seat",
    "brush",
    "cleaner",
    "hammock",
    "bed",
    "bag",
    "bowl",
    "towel",
    "spray",
    "shelf",
}

PRODUCT_MODIFIERS = {
    "dog",
    "cat",
    "puppy",
    "kitten",
    "paw",
    "muddy",
    "litter",
    "car",
    "seat",
    "back",
    "travel",
    "water",
    "fountain",
    "filter",
    "wall",
    "scratch",
    "scratcher",
    "grooming",
    "steam",
    "slow",
    "feeder",
    "lick",
    "enrichment",
    "indoor",
    "apartment",
    "balcony",
    "catio",
    "automatic",
    "smart",
    "waterproof",
    "hair",
    "fur",
    "odor",
    "odour",
    "training",
    "safety",
    "carrier",
    "harness",
}

COMPOUND_PATTERNS = (
    ("cat", "litter", "mat"),
    ("cat", "litter", "box"),
    ("dog", "paw", "washer"),
    ("paw", "washer"),
    ("paw", "cleaner"),
    ("dog", "car", "seat", "cover"),
    ("car", "seat", "cover"),
    ("dog", "car", "hammock"),
    ("cat", "wall", "shelf"),
    ("cat", "wall", "perch"),
    ("cat", "scratcher"),
    ("cardboard", "cat", "scratcher"),
    ("slow", "feeder"),
    ("lick", "mat"),
    ("water", "fountain", "filter"),
    ("pet", "water", "fountain"),
    ("steam", "brush"),
    ("pet", "hair", "brush"),
    ("dog", "harness"),
    ("pet", "carrier"),
)

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "your",
    "you",
    "are",
    "best",
    "review",
    "reviews",
    "amazon",
    "finds",
    "haul",
    "tiktok",
    "shorts",
    "viral",
    "new",
    "top",
    "must",
    "have",
    "need",
    "pet",
    "pets",
    "gadget",
    "gadgets",
    "thing",
    "things",
}


def load_env() -> dict[str, str]:
    env = dict(os.environ)
    env_file = ROOT / ".env.local"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            clean = line.strip()
            if not clean or clean.startswith("#") or "=" not in clean:
                continue
            key, value = clean.split("=", 1)
            env.setdefault(key.strip(), value.strip().strip('"'))
    return env


def week_id(today: dt.date | None = None) -> str:
    date = today or dt.date.today()
    year, week, _ = date.isocalendar()
    return f"{year}-W{week:02d}"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def clamp_score(value: float) -> int:
    return max(0, min(100, round(value)))


def parse_rfc3339(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def days_since(value: str) -> float:
    try:
        delta = dt.datetime.now(dt.timezone.utc) - parse_rfc3339(value)
        return max(delta.total_seconds() / 86400, 1)
    except ValueError:
        return 30


def http_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{url}?{query}", timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def source_disabled(missing: list[str]) -> dict[str, Any]:
    return {
        "source": "youtube",
        "status": {
            "status": "disabled_missing_credentials",
            "records": 0,
            "note": "missing " + ", ".join(missing),
        },
        "products": [],
    }


def source_error(error: Exception) -> dict[str, Any]:
    return {
        "source": "youtube",
        "status": {"status": "error", "records": 0, "note": str(error)[:180]},
        "products": [],
    }


def source_from_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    products = fixture.get("products", [])
    return {
        "source": "youtube",
        "status": {
            "status": "fixture",
            "records": len(products),
            "note": "local fixture data for tests and demos",
        },
        "products": products,
    }


def fetch_youtube(env: dict[str, str], fixture: dict[str, Any] | None) -> dict[str, Any]:
    if fixture is not None:
        return source_from_fixture(fixture)
    api_key = env.get("YOUTUBE_API_KEY")
    if not api_key:
        return source_disabled(["YOUTUBE_API_KEY"])

    max_profiles = int(env.get("YOUTUBE_MAX_PROFILES", "10"))
    max_results = int(env.get("YOUTUBE_MAX_RESULTS_PER_QUERY", "8"))
    comments_per_video = int(env.get("YOUTUBE_COMMENTS_PER_VIDEO", "5"))
    lookback_days = int(env.get("YOUTUBE_LOOKBACK_DAYS", "30"))
    seed_queries = load_seed_queries(env)[: int(env.get("YOUTUBE_MAX_SEED_QUERIES", "8"))]
    published_after = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=lookback_days)).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    try:
        discovered_videos = []
        for query in seed_queries:
            search_payload = http_json(
                YOUTUBE_SEARCH_URL,
                {
                    "key": api_key,
                    "part": "snippet",
                    "q": query,
                    "type": "video",
                    "maxResults": max_results,
                    "order": "relevance",
                    "regionCode": env.get("YOUTUBE_REGION_CODE", "GB"),
                    "relevanceLanguage": env.get("YOUTUBE_RELEVANCE_LANGUAGE", "en"),
                    "safeSearch": "moderate",
                    "publishedAfter": published_after,
                    "topicId": "/m/068hy",
                },
            )
            ids = [item["id"]["videoId"] for item in search_payload.get("items", []) if item.get("id", {}).get("videoId")]
            if not ids:
                continue
            video_payload = http_json(
                YOUTUBE_VIDEOS_URL,
                {
                    "key": api_key,
                    "part": "snippet,statistics",
                    "id": ",".join(ids),
                    "maxResults": len(ids),
                },
            )
            for item in video_payload.get("items", []):
                discovered_videos.append(normalize_video(item, query))

        products = []
        for cluster in discover_clusters(discovered_videos, max_profiles):
            comments = []
            for video in cluster["videos"][:3]:
                comments.extend(fetch_comments(api_key, video["video_id"], comments_per_video))
            products.append(build_product(cluster["profile"], cluster["videos"], comments))
        return {
            "source": "youtube",
            "status": {
                "status": "live",
                "records": sum(len(product.get("evidence", [])) for product in products),
                "note": f"YouTube Data API auto discovery, {len(seed_queries)} seed queries, lookback {lookback_days} days",
            },
            "products": [product for product in products if product["score"] > 0],
        }
    except Exception as error:  # pragma: no cover - network/API dependent
        return source_error(error)


def normalize_video(item: dict[str, Any], query: str) -> dict[str, Any]:
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    return {
        "video_id": item.get("id", ""),
        "query": query,
        "title": snippet.get("title", ""),
        "description": snippet.get("description", ""),
        "channel_id": snippet.get("channelId", ""),
        "channel_title": snippet.get("channelTitle", ""),
        "published_at": snippet.get("publishedAt", ""),
        "url": f"https://www.youtube.com/watch?v={item.get('id', '')}",
        "views": int(stats.get("viewCount", 0)),
        "likes": int(stats.get("likeCount", 0)),
        "comments": int(stats.get("commentCount", 0)),
    }


def load_seed_queries(env: dict[str, str]) -> list[str]:
    custom = env.get("YOUTUBE_SEED_QUERIES", "").strip()
    if custom:
        return [item.strip() for item in custom.split("|") if item.strip()]
    return SEED_QUERIES


def clean_text(value: str) -> str:
    return re.sub(r"[^a-z0-9\s-]", " ", value.lower())


def keyword_tokens(text: str) -> list[str]:
    return [token for token in clean_text(text).split() if len(token) > 2 and token not in STOPWORDS]


def extract_candidate_phrases(video: dict[str, Any]) -> list[str]:
    text = f"{video.get('title', '')} {video.get('description', '')}"
    cleaned = clean_text(text)
    tokens = keyword_tokens(text)
    phrases: list[str] = []
    token_text = " ".join(tokens)
    for pattern in COMPOUND_PATTERNS:
        pattern_text = " ".join(pattern)
        if pattern_text in token_text and pattern_text not in phrases:
            phrases.append(pattern_text)

    for term in PRODUCT_TERMS:
        if term in cleaned:
            term_tokens = term.split()
            for index in range(len(tokens)):
                if tokens[index] not in term_tokens:
                    continue
                window = tokens[max(0, index - 3) : min(len(tokens), index + len(term_tokens) + 3)]
                if term_tokens[-1] in window:
                    phrase = refine_phrase(window, term)
                    if is_specific_phrase(phrase) and phrase not in phrases:
                        phrases.append(phrase)
                        break
            if is_specific_phrase(term) and term not in phrases:
                phrases.append(term)
    return phrases[:5]


def refine_phrase(window: list[str], term: str) -> str:
    if not window:
        return term
    term_last = term.split()[-1]
    if term_last in window:
        term_index = window.index(term_last)
        start = max(0, term_index - 3)
        end = min(len(window), term_index + 2)
        words = window[start:end]
    else:
        words = window[-4:]
    words = trim_phrase(words)
    return " ".join(words)


def trim_phrase(words: list[str]) -> list[str]:
    while words and words[0] not in PRODUCT_MODIFIERS and words[0] not in PRODUCT_TERMS:
        words = words[1:]
    while words and words[-1] not in PRODUCT_TERMS and words[-1] not in PRODUCT_MODIFIERS:
        words = words[:-1]
    return words[-5:]


def is_specific_phrase(phrase: str) -> bool:
    tokens = keyword_tokens(phrase)
    if len(tokens) < 2:
        return False
    if phrase in GENERIC_PRODUCT_TERMS:
        return False
    has_product = any(term in phrase for term in PRODUCT_TERMS)
    has_modifier = any(token in PRODUCT_MODIFIERS for token in tokens)
    return has_product and has_modifier


def normalize_product_key(phrase: str) -> str:
    tokens = keyword_tokens(phrase)
    if not tokens:
        tokens = keyword_tokens(phrase)
    return "-".join(tokens[:4]) or "youtube-pet-opportunity"


def infer_pet(videos: list[dict[str, Any]], phrase: str) -> str:
    text = clean_text(" ".join([phrase, *[video.get("title", "") for video in videos]]))
    has_dog = "dog" in text or "puppy" in text
    has_cat = "cat" in text or "kitten" in text
    if has_dog and not has_cat:
        return "Dog"
    if has_cat and not has_dog:
        return "Cat"
    return "Multi"


def infer_category(phrase: str, videos: list[dict[str, Any]]) -> str:
    text = clean_text(" ".join([phrase, *[video.get("title", "") for video in videos]]))
    if any(word in text for word in ("clean", "washer", "scoop", "litter", "vacuum", "spray", "dryer", "towel")):
        return "Cleaning & Hygiene"
    if any(word in text for word in ("travel", "car", "seat", "carrier", "hammock", "leash", "harness")):
        return "Travel & Outdoor"
    if any(word in text for word in ("toy", "puzzle", "enrichment", "bored", "mat")):
        return "Enrichment"
    if any(word in text for word in ("shelf", "perch", "bed", "stairs", "ramp", "furniture")):
        return "Home & Furniture"
    if any(word in text for word in ("fountain", "filter", "camera", "tracker", "automatic")):
        return "Smart Care"
    return "Pet Accessories"


def infer_problem(phrase: str, videos: list[dict[str, Any]]) -> str:
    text = clean_text(" ".join(video.get("title", "") for video in videos))
    if any(word in text for word in ("clean", "mud", "dirty", "smell", "litter")):
        return f"用户在宠物清洁、异味或脏乱场景下频繁观看 {phrase} 相关内容。"
    if any(word in text for word in ("travel", "car", "walk", "outdoor")):
        return f"用户在宠物出行、遛宠或车内场景下寻找 {phrase} 类解决方案。"
    if any(word in text for word in ("bored", "stress", "anxiety", "enrichment")):
        return f"用户在宠物无聊、紧张或室内消耗精力场景下关注 {phrase}。"
    return f"YouTube 宠物内容中出现多条 {phrase} 相关视频，值得作为新品假设测试。"


def infer_creative_angles(phrase: str) -> list[str]:
    return [
        f"{phrase} before/after demo",
        f"{phrase} problem-solution short",
        f"{phrase} buyer checklist",
    ]


def discover_clusters(videos: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    clusters: dict[str, dict[str, Any]] = {}
    seen_video_ids: set[str] = set()
    for video in videos:
        if video["video_id"] in seen_video_ids:
            continue
        seen_video_ids.add(video["video_id"])
        for phrase in extract_candidate_phrases(video):
            key = normalize_product_key(phrase)
            cluster = clusters.setdefault(key, {"phrase": phrase, "videos": []})
            cluster["videos"].append(video)

    ranked = sorted(clusters.values(), key=cluster_rank_key, reverse=True)
    output = []
    for cluster in ranked[:limit]:
        phrase = cluster["phrase"]
        videos_for_cluster = cluster["videos"]
        name = phrase.title()
        output.append(
            {
                "profile": {
                    "product_key": normalize_product_key(phrase),
                    "name": name,
                    "pet": infer_pet(videos_for_cluster, phrase),
                    "category": infer_category(phrase, videos_for_cluster),
                    "problem": infer_problem(phrase, videos_for_cluster),
                    "suggested_price": "TBD",
                    "landing_page_angle": f"围绕 YouTube 上升温的 {name} 内容做痛点落地页，并用视频证据验证测试角度。",
                    "creative_angles": infer_creative_angles(phrase),
                    "test_plan": [
                        "用证据视频拆 3 个短视频脚本",
                        "做 1 个轻量落地页验证 CTR 和 ATC",
                        "人工核查供应价、MOQ、体积重和合规风险",
                    ],
                    "risks": ["自动发现主题需人工复核产品定义", "YouTube 是内容需求代理，不代表真实销量"],
                },
                "videos": videos_for_cluster,
            }
        )
    return output


def cluster_rank_key(cluster: dict[str, Any]) -> tuple[int, int, int]:
    phrase = cluster["phrase"]
    videos = cluster["videos"]
    specificity = len(keyword_tokens(phrase))
    return (
        specificity,
        len({video["channel_id"] for video in videos}),
        sum(video["views"] for video in videos),
    )


def fetch_comments(api_key: str, video_id: str, limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    try:
        payload = http_json(
            YOUTUBE_COMMENTS_URL,
            {
                "key": api_key,
                "part": "snippet",
                "videoId": video_id,
                "maxResults": min(limit, 100),
                "order": "relevance",
                "textFormat": "plainText",
            },
        )
    except Exception:
        return []
    comments = []
    for item in payload.get("items", []):
        top = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
        comments.append(
            {
                "video_id": video_id,
                "text": top.get("textDisplay", ""),
                "likes": int(top.get("likeCount", 0)),
            }
        )
    return comments


def pain_comment_count(comments: list[dict[str, Any]]) -> int:
    count = 0
    for comment in comments:
        text = comment.get("text", "").lower()
        if any(word in text for word in PAIN_WORDS):
            count += 1
    return count


def build_product(profile: dict[str, Any], videos: list[dict[str, Any]], comments: list[dict[str, Any]]) -> dict[str, Any]:
    total_views = sum(video["views"] for video in videos)
    total_likes = sum(video["likes"] for video in videos)
    total_comments = sum(video["comments"] for video in videos)
    unique_channels = len({video["channel_id"] for video in videos if video["channel_id"]})
    avg_velocity = sum(video["views"] / days_since(video["published_at"]) for video in videos) / max(len(videos), 1)
    engagement_rate = (total_likes + total_comments) / max(total_views, 1)
    pain_comments = pain_comment_count(comments)

    search_score = clamp_score(len(videos) * 7 + min(unique_channels * 4, 24))
    velocity_score = clamp_score(18 * math.log10(avg_velocity + 1))
    engagement_score = clamp_score(engagement_rate * 1800)
    comment_score = clamp_score(pain_comments * 14 + min(len(comments) * 2, 20))
    creator_score = clamp_score(unique_channels * 10)
    score = clamp_score(
        search_score * 0.22
        + velocity_score * 0.28
        + engagement_score * 0.18
        + comment_score * 0.17
        + creator_score * 0.15
    )

    evidence = sorted(videos, key=lambda video: video["views"], reverse=True)[:5]
    confidence = "high" if score >= 70 and unique_channels >= 4 else "medium" if score >= 45 else "low"
    excluded = is_excluded(profile)
    return {
        "product_key": profile["product_key"],
        "name": profile["name"],
        "pet": profile["pet"],
        "category": profile["category"],
        "problem": profile["problem"],
        "risk": "Medium" if excluded else "Low",
        "suggested_price": profile["suggested_price"],
        "supply_price": "TBD",
        "moq": "TBD",
        "landing_page_angle": profile["landing_page_angle"],
        "creative_angles": profile["creative_angles"],
        "test_plan": profile["test_plan"],
        "risks": profile["risks"] + (["YouTube 是内容需求代理，不代表真实销量"] if not excluded else ["默认排除食品/药品/保健品或高合规声明"]),
        "scores": {
            "youtube_search": search_score,
            "youtube_velocity": velocity_score,
            "youtube_engagement": engagement_score,
            "youtube_comments": comment_score,
            "creator_diversity": creator_score,
        },
        "score": score,
        "confidence": confidence,
        "signals": {
            "youtube_search": {
                "enabled": True,
                "score": search_score,
                "summary": f"{len(videos)} videos across {unique_channels} channels",
                "metric": "search coverage",
            },
            "youtube_velocity": {
                "enabled": True,
                "score": velocity_score,
                "summary": f"avg {round(avg_velocity)} views/day",
                "metric": "view velocity",
            },
            "youtube_engagement": {
                "enabled": True,
                "score": engagement_score,
                "summary": f"{engagement_rate:.2%} like/comment engagement proxy",
                "metric": "engagement proxy",
            },
            "youtube_comments": {
                "enabled": True,
                "score": comment_score,
                "summary": f"{pain_comments} pain comments from {len(comments)} sampled comments",
                "metric": "comment pain proxy",
            },
            "creator_diversity": {
                "enabled": True,
                "score": creator_score,
                "summary": f"{unique_channels} unique channels",
                "metric": "creator diversity",
            },
        },
        "evidence": [
            {
                "source": "youtube",
                "title": video["title"],
                "url": video["url"],
                "summary": f"{video['views']} views · {video['likes']} likes · {video['comments']} comments · {video['channel_title']}",
                "metric": video["query"],
            }
            for video in evidence
        ],
        "excluded": excluded,
    }


def is_excluded(record: dict[str, Any]) -> bool:
    text = " ".join(str(record.get(key, "")) for key in ("name", "category", "problem")).lower()
    return any(term in text for term in EXCLUDED_TERMS)


def build_products(products: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    included = [product for product in products if not product.get("excluded")]
    excluded = [product for product in products if product.get("excluded")]
    included.sort(key=lambda item: item["score"], reverse=True)
    excluded.sort(key=lambda item: item["score"], reverse=True)
    return included[:10], excluded


def report_summary(products: list[dict[str, Any]], status: dict[str, Any]) -> str:
    if not products:
        return "本周没有生成可测新品。请配置 YOUTUBE_API_KEY，或用 --fixture 生成演示报告验证链路。"
    top = products[0]
    return (
        f"本周基于 YouTube 内容信号识别到 {len(products)} 个可测宠物用品机会；最高分是 "
        f"{top['name']} ({top['score']}/100, {top['confidence']})。数据源状态: {status.get('status')}。"
    )


def make_report(source_result: dict[str, Any], week: str) -> dict[str, Any]:
    products, excluded = build_products(source_result["products"])
    return {
        "meta": {
            "generated_at": utc_now(),
            "week_id": week,
            "market": "UK",
            "summary": report_summary(products, source_result["status"]),
            "category_policy": "Exclude pet food, treats, supplements, medicine and drug-like claims by default.",
            "source_policy": "Use YouTube Data API as a content-demand signal: search.list, videos.list, commentThreads.list.",
        },
        "source_status": {"youtube": source_result["status"]},
        "products": products,
        "excluded_products": excluded,
        "next_week_actions": [
            "配置 YOUTUBE_API_KEY 并控制每周查询预算。",
            "对 Top 3 产品各做 1 个落地页和 3 条短视频素材。",
            "用独立站 CTR、ATC、询盘价和样品物流成本回填下周评分。",
        ],
    }


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        f"# YouTube 宠物选品嗅探报告 {report['meta']['week_id']}",
        "",
        f"- 生成时间: {report['meta']['generated_at']}",
        f"- 市场: {report['meta']['market']}",
        f"- 摘要: {report['meta']['summary']}",
        f"- 数据源策略: {report['meta'].get('source_policy', '')}",
        "",
        "## 数据源状态",
    ]
    for source, status in report["source_status"].items():
        lines.append(f"- {source}: {status.get('status')} · {status.get('records', 0)} records · {status.get('note', '')}")

    lines.extend(["", "## Top 10 可测新品"])
    if not report["products"]:
        lines.append("暂无候选品。数据源未启用时不会生成假候选。")
    for index, product in enumerate(report["products"], start=1):
        scores = product["scores"]
        lines.extend(
            [
                "",
                f"### {index}. {product['name']} ({product['score']}/100, {product['confidence']})",
                f"- 宠物/品类: {product['pet']} · {product['category']}",
                f"- 用户痛点: {product['problem']}",
                f"- 建议售价/供应: {product.get('suggested_price', 'TBD')} · {product.get('supply_price', 'TBD')} · MOQ {product.get('moq', 'TBD')}",
                f"- 落地页角度: {product.get('landing_page_angle', '')}",
                f"- YouTube 信号: Search {scores['youtube_search']}, Velocity {scores['youtube_velocity']}, Engagement {scores['youtube_engagement']}, Comments {scores['youtube_comments']}, Creator {scores['creator_diversity']}",
                f"- 7 天测试: {'; '.join(product.get('test_plan', []))}",
                f"- 素材方向: {'; '.join(product.get('creative_angles', []))}",
                f"- 风险: {'; '.join(product.get('risks', [])) or product.get('risk', 'Low')}",
            ]
        )
        for evidence in product.get("evidence", []):
            title = evidence.get("title") or evidence.get("source")
            url = evidence.get("url") or "no-url"
            lines.append(f"  - 证据 {evidence.get('source')}: {title} · {url} · {evidence.get('summary', '')}")

    lines.extend(["", "## 趋势上升痛点"])
    lines.extend([f"- {product['problem']} ({product['name']})" for product in report["products"][:5]] or ["暂无。"])

    lines.extend(["", "## 排除/高风险品"])
    lines.extend([f"- {product['name']}: 默认排除食品/药品/保健品或高合规声明。" for product in report.get("excluded_products", [])] or ["本周没有被规则排除的高风险品。"])

    lines.extend(["", "## 下周测试建议"])
    lines.extend([f"- {item}" for item in report.get("next_week_actions", [])])
    return "\n".join(lines) + "\n"


def html_report(report: dict[str, Any], markdown: str) -> str:
    body = html.escape(markdown)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>YouTube 宠物选品嗅探报告 {html.escape(report['meta']['week_id'])}</title>
  <style>
    body {{ margin: 0; padding: 32px; color: #17211b; background: #f7faf6; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    main {{ max-width: 980px; margin: 0 auto; padding: 28px; border: 1px solid #dfe7df; border-radius: 8px; background: white; }}
    pre {{ white-space: pre-wrap; line-height: 1.6; font: inherit; }}
  </style>
</head>
<body><main><pre>{body}</pre></main></body>
</html>
"""


def write_outputs(report: dict[str, Any]) -> Path:
    week_dir = REPORTS_DIR / report["meta"]["week_id"]
    week_dir.mkdir(parents=True, exist_ok=True)
    markdown = markdown_report(report)
    json_text = json.dumps(report, ensure_ascii=False, indent=2)
    js_text = "window.__PET_SCOUT_REPORT__ = " + json.dumps(report, ensure_ascii=False, indent=2) + ";\n"

    (week_dir / "report.md").write_text(markdown, encoding="utf-8")
    (week_dir / "report.html").write_text(html_report(report, markdown), encoding="utf-8")
    (week_dir / "evidence.json").write_text(json_text, encoding="utf-8")
    (week_dir / "latest.json").write_text(json_text, encoding="utf-8")
    (REPORTS_DIR / "latest.json").write_text(json_text, encoding="utf-8")
    (REPORTS_DIR / "latest.js").write_text(js_text, encoding="utf-8")
    (REPORTS_DIR / "latest.md").write_text(markdown, encoding="utf-8")
    (REPORTS_DIR / "latest.html").write_text(html_report(report, markdown), encoding="utf-8")
    write_csv(week_dir / "products.csv", report["products"])
    write_csv(REPORTS_DIR / "latest.csv", report["products"])
    return week_dir


def write_error_without_overwriting_latest(report: dict[str, Any]) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    error_path = REPORTS_DIR / "last_error.json"
    error_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return error_path


def should_preserve_latest(report: dict[str, Any], fixture: bool) -> bool:
    if fixture:
        return False
    status = report.get("source_status", {}).get("youtube", {}).get("status")
    return status in {"error", "disabled_missing_credentials"} and not report.get("products")


def write_csv(path: Path, products: list[dict[str, Any]]) -> None:
    fields = ["rank", "name", "pet", "category", "score", "confidence", "risk", "suggested_price", "problem"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, product in enumerate(products, start=1):
            row = {field: product.get(field, "") for field in fields}
            row["rank"] = index
            writer.writerow(row)


def load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the weekly YouTube pet product sniffing report.")
    parser.add_argument("--fixture", action="store_true", help="Use local fixture data for tests and demos.")
    parser.add_argument("--week", default=week_id(), help="Override ISO week id, for example 2026-W21.")
    args = parser.parse_args()

    REPORTS_DIR.mkdir(exist_ok=True)
    env = load_env()
    fixture = load_fixture() if args.fixture else None
    source_result = fetch_youtube(env, fixture)
    report = make_report(source_result, args.week)
    if should_preserve_latest(report, args.fixture):
        error_path = write_error_without_overwriting_latest(report)
        print(f"Report generation failed; preserved existing latest report")
        print(report["meta"]["summary"])
        print(error_path)
        return 1
    output_dir = write_outputs(report)
    print(f"Generated {report['meta']['week_id']} report")
    print(report["meta"]["summary"])
    print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
