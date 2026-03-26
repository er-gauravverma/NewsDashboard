"""
News Scraper - Find latest news links for any keyword from any website.

Usage:
    python news_scraper.py "crude oil"
    python news_scraper.py "crude oil" --source investing.com
    python news_scraper.py "gold price" --source reuters.com --limit 20
    python news_scraper.py "nifty 50" --direct-url https://example.com/markets

Requirements:
    pip install requests beautifulsoup4 duckduckgo_search
"""

import argparse
import re
import sys
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_direct(url: str, keyword: str, limit: int) -> list[dict]:
    """Scrape a specific URL for links matching the keyword."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    keyword_lower = keyword.lower()
    pattern = re.compile(re.escape(keyword_lower))
    results = []
    seen = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href or href.startswith(("#", "javascript:")):
            continue

        full_url = urljoin(url, href)
        link_text = tag.get_text(separator=" ", strip=True)
        title_attr = tag.get("title", "") or ""
        searchable = f"{link_text} {href} {title_attr}".lower()

        if pattern.search(searchable) and full_url not in seen:
            seen.add(full_url)
            results.append({"title": link_text[:150] or "(no text)", "url": full_url})
            if len(results) >= limit:
                break

    return results


def search_news(keyword: str, source: str | None, limit: int) -> list[dict]:
    """Search for news using DuckDuckGo News API."""
    query = keyword
    if source:
        query = f"{keyword} site:{source}"

    results = []
    try:
        with DDGS() as ddgs:
            for item in ddgs.news(query, max_results=limit):
                results.append({
                    "title": item.get("title", "(no title)"),
                    "url": item.get("url", ""),
                    "date": item.get("date", ""),
                    "source": item.get("source", ""),
                    "body": item.get("body", ""),
                })
    except Exception as e:
        print(f"  News search error: {e}")

    # Fallback to regular web search if news search returns nothing
    if not results:
        print("  News API returned no results, trying web search...")
        try:
            with DDGS() as ddgs:
                for item in ddgs.text(query + " latest news", max_results=limit):
                    results.append({
                        "title": item.get("title", "(no title)"),
                        "url": item.get("href", ""),
                        "date": "",
                        "source": "",
                        "body": item.get("body", ""),
                    })
        except Exception as e:
            print(f"  Web search error: {e}")

    return results


def print_results(results: list[dict], keyword: str):
    """Pretty-print the results."""
    if not results:
        print(f"\n  No results found for '{keyword}'.")
        return

    print(f"\n  Found {len(results)} result(s):\n")
    for i, item in enumerate(results, 1):
        title = item["title"]
        url = item["url"]
        date = item.get("date", "")
        source = item.get("source", "")
        body = item.get("body", "")

        meta_parts = []
        if source:
            meta_parts.append(source)
        if date:
            meta_parts.append(date[:16])
        meta = " | ".join(meta_parts)

        print(f"  {i:2d}. {title}")
        if meta:
            print(f"      [{meta}]")
        if body:
            print(f"      {body[:120]}...")
        print(f"      {url}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape news links related to a keyword",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python news_scraper.py "crude oil"
  python news_scraper.py "crude oil" --source investing.com
  python news_scraper.py "gold price" --source reuters.com --limit 20
  python news_scraper.py "nifty 50" --direct-url https://example.com/markets
        """,
    )
    parser.add_argument("keyword", help="Keyword to search for (e.g. 'crude oil')")
    parser.add_argument("--source", default=None,
                        help="Restrict results to a specific site (e.g. investing.com)")
    parser.add_argument("--direct-url", default=None,
                        help="Directly scrape this URL instead of using search")
    parser.add_argument("--limit", type=int, default=15,
                        help="Max number of results (default: 15)")
    args = parser.parse_args()

    print(f"\n  Keyword: '{args.keyword}'")
    if args.source:
        print(f"  Source:  {args.source}")
    print("  " + "-" * 60)

    if args.direct_url:
        print(f"\n  Scraping: {args.direct_url}")
        results = scrape_direct(args.direct_url, args.keyword, args.limit)
    else:
        print("\n  Searching for latest news...")
        results = search_news(args.keyword, args.source, args.limit)

    print_results(results, args.keyword)


if __name__ == "__main__":
    main()
