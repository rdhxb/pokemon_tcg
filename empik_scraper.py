import requests
from bs4 import BeautifulSoup
import pandas
import json


URL = 'https://www.empik.com/szukaj/produkt?qtype=facetForm&q=pokemon+tcg&mpShopIdFacet=0'



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

        if name and price is not None:

            price_numeric = price_to_numeric(price)
            results.append({"name": name, "price": price, "price_numeric": price_numeric})

    return results


def create_snapshot():
    pass

# compare price from snapshot and json file
def compare_price():
    pass

def to_json(items):
    with open('items.json', 'w' ,encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    try:
        html = fetch_html(URL)
        soup = BeautifulSoup(html, 'html.parser')
        items = get_items(soup)
        to_json(items)
    except requests.HTTPError as e:
        print(f"HTTP error: {e}")
    except requests.RequestException as e:
        print(f"Network error: {e}")
        
        

