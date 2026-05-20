#!/usr/bin/env python3
"""
网页抓取模板：给出战斗详情页 URL 与简单的 CSS selector 映射，输出一行 CSV。

注意：根据目标网站政策与版权/使用条款，抓取前请确认允许抓取。

示例用法（mapping.json 为 {"攻击方武力": ".atk-power", ...}）：
  python scripts/scraper_template.py --url "https://..." --mapping mapping.json
"""
import argparse
import json
import requests
from bs4 import BeautifulSoup
import csv
from pathlib import Path


def fetch_soup(url: str):
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return BeautifulSoup(r.text, 'lxml')


def parse_with_mapping(soup, mapping: dict):
    row = {}
    for key, sel in mapping.items():
        try:
            el = soup.select_one(sel)
            row[key] = el.get_text(strip=True) if el is not None else ''
        except Exception:
            row[key] = ''
    return row


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--url', required=True)
    p.add_argument('--mapping', required=True, help='JSON 文件，字段->CSS selector')
    p.add_argument('--out', default='data/scraped_rows.csv')
    args = p.parse_args()

    mapping = json.loads(Path(args.mapping).read_text(encoding='utf-8'))
    soup = fetch_soup(args.url)
    row = parse_with_mapping(soup, mapping)

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    exists = outp.exists()
    with open(outp, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(mapping.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    print('已抓取并追加到', outp)


if __name__ == '__main__':
    main()
