#!/usr/bin/env python3
"""
Build a consolidated JSON file with recent security news.

- Reads an OPML file containing RSS feeds (sec_feeds.xml)
- Fetches all feeds using feedparser
- Normalizes entries
- Keeps only last N days (default: 30)
- Deduplicates by link
- Writes data/news_recent.json

This script is meant to be run from the repo root (S33R).
"""

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET

import feedparser  # type: ignore

ROOT = Path(__file__).resolve().parent.parent
OPML_PATH = ROOT / "sec_feeds.xml"
OUTPUT_PATH = ROOT / "data" / "news_recent.json"
DAYS_BACK = 30

CATEGORY_KEYWORDS = {
    "crypto": ["crypto", "blockchain"],
    "cybercrime": ["cybercrime", "darknet"],
    "dfir": ["dfir", "forensics"],
    "general": ["general", "security news", "infosec"],
    "gov_cert": ["cert", "government", "gov"],
    "leaks": ["leaks", "breaches", "pwned"],
    "malware": ["malware", "ransomware"],
    "threat_intel": ["threat intel", "apt", "campaigns"],
    "malware_analysis": ["malware analysis", "reversing"],
    "osint": ["osint", "communities"],
    "podcasts": ["podcast"],
    "vendors": ["vendor"],
    "vulns": ["vulnerab", "cve"],
    "exploits": ["exploit", "0day"],
    "vuln_advisories": ["advisories", "advisory"],
}


def guess_category_from_title(title: str) -> str:
    t = title.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(k in t for k in keywords):
            return cat
    return "general"


def parse_opml(path: Path):
    tree = ET.parse(path)
    root = tree.getroot()
    body = root.find("body")
    if body is None:
        return []
    feeds = []
    seen = set()
    for elem in body.findall(".//outline"):
        xml_url = elem.attrib.get("xmlUrl")
        if not xml_url or xml_url in seen:
            continue
        seen.add(xml_url)
        title = elem.attrib.get("title") or elem.attrib.get("text") or xml_url
        cat = guess_category_from_title(
            " / ".join(
                filter(
                    None,
                    [elem.attrib.get("title") or elem.attrib.get("text") or ""],
                )
            )
        )
        feeds.append((title, xml_url, cat))
    return feeds


def parse_entry(entry, source_title: str, category: str) -> Optional[Dict[str, Any]]:
    title = getattr(entry, "title", None) or entry.get("title")
    link = getattr(entry, "link", None) or entry.get("link")
    if not title or not link:
        return None

    summary = (
        getattr(entry, "summary", None)
        or entry.get("summary")
        or entry.get("description")
        or ""
    )

    published = None
    if getattr(entry, "published_parsed", None):
        published = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
    elif getattr(entry, "updated_parsed", None):
        published = datetime.fromtimestamp(time.mktime(entry.updated_parsed), tz=timezone.utc)
    else:
        raw_date = entry.get("published") or entry.get("updated")
        if raw_date:
            try:
                published = datetime.fromisoformat(raw_date)
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
            except Exception:
                published = None

    return {
        "title": title,
        "link": link,
        "summary": summary,
        "source": source_title,
        "category": category,
        "published": published.isoformat() if published else None,
    }


def main() -> None:
    if not OPML_PATH.exists():
        raise SystemExit(f"OPML file not found: {OPML_PATH}")

    print(f"[INFO] Using OPML: {OPML_PATH}")
    feeds = parse_opml(OPML_PATH)
    print(f"[INFO] Found {len(feeds)} feeds")

    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)
    all_items: Dict[str, Dict[str, Any]] = {}

    for idx, (feed_title, xml_url, category) in enumerate(feeds, start=1):
        print(f"[{idx}/{len(feeds)}] Fetching {feed_title} :: {xml_url}")
        parsed = feedparser.parse(xml_url)
        if parsed.bozo:
            print(f"  [WARN] Problem parsing feed: {xml_url} ({parsed.bozo_exception})")

        for entry in parsed.entries:
            item = parse_entry(entry, source_title=feed_title, category=category)
            if not item:
                continue
            pub_str = item.get("published")
            if pub_str:
                try:
                    pub_dt = datetime.fromisoformat(pub_str)
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                except Exception:
                    pub_dt = None
            else:
                pub_dt = None

            if pub_dt and pub_dt < cutoff:
                continue

            link = item["link"].rstrip("/")
            existing = all_items.get(link)
            if existing:
                existing_dt = None
                if existing.get("published"):
                    try:
                        existing_dt = datetime.fromisoformat(existing["published"])
                    except Exception:
                        existing_dt = None
                if existing_dt and pub_dt and pub_dt <= existing_dt:
                    continue
            all_items[link] = item

    items_list: List[Dict[str, Any]] = list(all_items.values())

    def sort_key(x: Dict[str, Any]):
        p = x.get("published")
        if not p:
            return 0.0
        try:
            return datetime.fromisoformat(p).timestamp()
        except Exception:
            return 0.0

    items_list.sort(key=sort_key, reverse=True)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days_back": DAYS_BACK,
        "total_items": len(items_list),
        "items": items_list,
    }
    OUTPUT_PATH.write_text(json.dumps(out_data, indent=2), encoding="utf-8")
    print(f"[INFO] Wrote {len(items_list)} items to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
