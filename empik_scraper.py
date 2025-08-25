import requests
from bs4 import BeautifulSoup
import pandas
import json


URL = 'https://www.empik.com/szukaj/produkt?qtype=facetForm&q=pokemon+tcg&mpShopIdFacet=0'



def fetch_html(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.text

# get items with prices and names
def get_items(soup):
    items_dict = {}
    items = soup.find_all('div', class_ = 'search-list-item-hover')
    for item in items:
        price = item.find('div', class_='price ta-price-tile').text
        name = item.find('strong', class_ = 'ta-product-title').text
        if price and name:
            items_dict[name] = price
        else:
            continue

    # removing unnessesary text
    cleaned_dict = {k: v.replace('\xa0', ' ').strip() for k, v in items_dict.items()}

    return cleaned_dict



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

