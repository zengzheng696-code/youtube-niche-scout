#!/usr/bin/env python3
"""Build compact LLM context from a YouTube product-sniffing report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def line(text: str = "") -> str:
    return text.rstrip() + "\n"


def build_context(report: dict, max_products: int) -> str:
    chunks: list[str] = []
    meta = report.get("meta", {})
    chunks.append(line(f"# YouTube Product Sniffing Context {meta.get('week_id', '')}"))
    chunks.append(line(f"Market: {meta.get('market', 'UK')}"))
    chunks.append(line(f"Summary: {meta.get('summary', '')}"))
    chunks.append(line("Rule: YouTube is content-demand evidence, not sales proof."))
    chunks.append(line())

    products = report.get("products", [])[:max_products]
    for index, product in enumerate(products, start=1):
        scores = product.get("scores", {})
        chunks.append(line(f"## {index}. {product.get('name', '')}"))
        chunks.append(line(f"Pet/category: {product.get('pet', '')} / {product.get('category', '')}"))
        chunks.append(line(f"Score/confidence: {product.get('score', '')} / {product.get('confidence', '')}"))
        chunks.append(line(f"Problem: {product.get('problem', '')}"))
        chunks.append(line(f"Landing angle: {product.get('landing_page_angle', '')}"))
        chunks.append(line(
            "Scores: "
            f"search={scores.get('youtube_search', 0)}, "
            f"velocity={scores.get('youtube_velocity', 0)}, "
            f"engagement={scores.get('youtube_engagement', 0)}, "
            f"comments={scores.get('youtube_comments', 0)}, "
            f"creators={scores.get('creator_diversity', 0)}"
        ))
        chunks.append(line("Evidence:"))
        for evidence in product.get("evidence", [])[:5]:
            chunks.append(line(f"- {evidence.get('title', '')} | {evidence.get('summary', '')} | {evidence.get('url', '')}"))
        chunks.append(line(f"Risks: {'; '.join(product.get('risks', []))}"))
        chunks.append(line())

    excluded = report.get("excluded_products", [])
    if excluded:
        chunks.append(line("## Excluded or High-Risk"))
        for product in excluded[:10]:
            chunks.append(line(f"- {product.get('name', '')}: {product.get('category', '')}, {product.get('problem', '')}"))
    return "".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report_json")
    parser.add_argument("--out")
    parser.add_argument("--max-products", type=int, default=10)
    args = parser.parse_args()

    report_path = Path(args.report_json)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    context = build_context(report, args.max_products)

    if args.out:
        Path(args.out).write_text(context, encoding="utf-8")
    else:
        print(context)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
