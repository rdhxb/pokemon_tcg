import requests
from bs4 import BeautifulSoup
import pandas
import json
from pathlib import Path
import re
import time
import random
from discord_notify import notify_discord


URL = 'https://www.empik.com/szukaj/produkt?qtype=facetForm&q=pokemon+tcg&mpShopIdFacet=0'

STATE_FILE = Path("state.json")

def fetch_html(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.text

def clean_text(s):
    return s.replace("\xa0", " ").strip()

def price_to_numeric(price):
    price = price.replace('zł','').strip()
    price = price.replace(',', '.').strip()
    price_float = float(price)
    return price_float

# get items with prices and names
def get_items(soup):
    results = []
    cards = soup.find_all('div', class_ = 'search-list-item-hover')

    for card in cards:

        price_el = card.find('div', class_='price ta-price-tile')
        price = clean_text(price_el.get_text(" ", strip=True)) if price_el else ""

        name_el = card.find('strong', class_ = 'ta-product-title')
        name = clean_text(name_el.get_text(" ", strip=True)) if name_el else ""

        price_numeric = price_to_numeric(price)
        if name and price_numeric:
            results.append({"name": name, "price": price, "price_numeric": price_numeric})

    return results

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return {str(k): float(v) for k, v in data.items()}
                elif isinstance(data, list):
                    return {d["name"]: float(d["price_numeric"]) for d in data if "name" in d and "price_numeric" in d}
        except Exception:
            pass
    return {}

def save_state(state_map: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state_map, f, ensure_ascii=False, indent=2)

def compare_and_report(old_map: dict, current_items: list[dict]):
    current_map = {item["name"]: item["price_numeric"] for item in current_items}

    # Detect new & removed
    old_names = set(old_map.keys())
    cur_names = set(current_map.keys())

    new_items = sorted(cur_names - old_names)
    removed_items = sorted(old_names - cur_names)

    # Detect price changes
    common = old_names & cur_names
    changes = []
    for name in common:
        old_p = old_map[name]
        new_p = current_map[name]
        # treat tiny FP variations as equal
        if abs(new_p - old_p) >= 0.001:
            diff = new_p - old_p
            direction = "↑" if diff > 0 else "↓"
            changes.append((name, old_p, new_p, diff, direction))
    changes.sort(key=lambda x: x[0])

    # --- Print report ---
    if not new_items and not removed_items and not changes:
        print("No changes since last run.")
    else:
        if changes:
            print("Price changes:")
            for name, old_p, new_p, diff, direction in changes:
                print(f"  PRICE {direction}  {name}\n    {old_p:.2f} → {new_p:.2f}  (diff {diff:+.2f})")
                notify_discord(f"  PRICE {direction}  {name}\n    {old_p:.2f} → {new_p:.2f}  (diff {diff:+.2f})")
        if new_items:
            print("\nNew items:")
            for name in new_items:
                print(f"  NEW       {name}  @ {current_map[name]:.2f}")
                notify_discord(f"  NEW       {name}  @ {current_map[name]:.2f}")
        if removed_items:
            print("\nRemoved items:")
            for name in removed_items:
                print(f"  REMOVED   {name}")
                notify_discord(f"  REMOVED   {name}")

    return current_map

def to_json(items):
    with open('state_4.json', 'w' ,encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    
    while True:
        try:
            html = fetch_html(URL)
            soup = BeautifulSoup(html, 'html.parser')
            items = get_items(soup)
            # to_json(items)
            old_state = load_state()
            new_state = compare_and_report(old_state, items)
            save_state(new_state)

        except requests.HTTPError as e:
            print(f"HTTP error: {e}")
        except requests.RequestException as e:
            print(f"Network error: {e}")

        # wait before next check
        print("Sleeping for 5/10 min...\n")
        try:
            random_time = random.randint(300,600)
            time.sleep(random_time)
        except KeyboardInterrupt:
            print("Stopped by user.")
            break