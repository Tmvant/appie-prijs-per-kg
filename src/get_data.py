import pandas as pd
from bs4 import BeautifulSoup
import lxml
import requests
import math
import csv
import re
import time
from time import sleep
import os

DATA_DIR_RAW = '../data/albert_heijn/raw_data/'
DATA_DIR_PROCESSED = '../data/albert_heijn/ah_data.csv'
URL_PRODUCTS = 'https://www.ah.nl/producten'
URL_BASE = 'https://www.ah.nl'
TIMER = 0.25  # waiting time in seconds between each request to avoid being blocked by server
PRODUCT_CATEGORIES = [
    # 'aardappel-groente-fruit',  # split category to work around 1000 products per page limit
    'aardappel-groente-fruit?minPrice=0&maxPrice=2.99',
    'aardappel-groente-fruit?minPrice=3&maxPrice=99',
    'salades-pizza-maaltijden',
    'vlees-kip-vis-vega',
    # 'kaas-vleeswaren-tapas', # split category to work around 1000 products per page limit
    'kaas-vleeswaren-tapas?minPrice=0&maxPrice=2.99',
    'kaas-vleeswaren-tapas?minPrice=3&maxPrice=99',
    # 'zuivel-plantaardig-en-eieren', # split category to work around 1000 products per page limit
    'zuivel-plantaardig-en-eieren?minPrice=0&maxPrice=3.99',
    'zuivel-plantaardig-en-eieren?minPrice=4&maxPrice=99',
    'bakkerij-en-banket',
    # 'ontbijtgranen-en-beleg', # split category to work around 1000 products per page limit
    'ontbijtgranen-en-beleg?minPrice=0&maxPrice=2.60',
    'ontbijtgranen-en-beleg?minPrice=2.61&maxPrice=99',
    # 'snoep-koek-chips-en-chocolade',  # split category to work around 1000 products per page limit
    'snoep-koek-chips-en-chocolade?minPrice=0&maxPrice=1.89',
    'snoep-koek-chips-en-chocolade?minPrice=1.90&maxPrice=2.59',
    'snoep-koek-chips-en-chocolade?minPrice=2.60&maxPrice=99',
    'tussendoortjes',
    # 'frisdrank-sappen-koffie-thee', # exclude drinks
    # 'wijn-en-bubbels', # exclude drinks
    # 'bier-en-aperitieven', # exclude drinks
    # 'pasta-rijst-en-wereldkeuken', # split category to work around 1000 products per page limit
    'pasta-rijst-en-wereldkeuken?minPrice=0&maxPrice=1.99',
    'pasta-rijst-en-wereldkeuken?minPrice=2&maxPrice=3.99',
    'pasta-rijst-en-wereldkeuken?minPrice=4&maxPrice=99',
    # 'soepen-sauzen-kruiden-olie', # split category to work around 1000 products per page limit
    'soepen-sauzen-kruiden-olie?minPrice=0&maxPrice=1.79',
    'soepen-sauzen-kruiden-olie?minPrice=1.80&maxPrice=2.99',
    'soepen-sauzen-kruiden-olie?minPrice=3&maxPrice=99',
    'sport-en-dieetvoeding',
    'diepvries'
]
SPLIT_CATEGORIES = [
    # product categories that had to be split due to website's 1000 product limit per page
    'aardappel-groente-fruit',
    'kaas-vleeswaren-tapas',
    'zuivel-plantaardig-en-eieren',
    'ontbijtgranen-en-beleg',
    'pasta-rijst-en-wereldkeuken',
    'soepen-sauzen-kruiden-olie',
    'snoep-koek-chips-en-chocolade'
]
COL_MAPPING = {
    'Category': 'Category',
    'Price': 'Price',
    'Product': 'Product',
    'Subtitle': 'Subtitle',
    'NutriScore': 'NutriScore',
    'Vegan': 'Vegan',
    'Vegetarian': 'Vegetarian',
    'Url': 'Url',
    'Content': 'Content',
    'Alcohol': 'Alcohol',
    'Calcium': 'Calcium',
    'Eiwitten': 'Protein',
    'Energie': 'Energy',
    'Folaat': 'Folate',
    'Ijzer': 'Iron',
    'Jodium': 'Iodine',
    'Koolhydraten': 'Carbohydrates',
    'Koper': 'Copper',
    'Magnesium': 'Magnesium',
    'Mangaan': 'Manganese',
    'Natrium': 'Sodium',
    'Potassium': 'Potassium',
    # 'Seleen': 'xxxxxx',
    'Vet': 'Fat',
    # 'Vet1': 'Fat',
    'Vitamine A': 'Vitamin A',
    'Vitamine B1 / Thiamine': 'Vitamin B1',
    'Vitamine B11 / Foliumzuur': 'Vitamin B11',
    'Vitamine B2 / Riboflavine': 'Vitamin B2',
    'Vitamine B3 / Niacine': 'Vitamin B3',
    'Vitamine B5 / Pantotheenzuur': 'Vitamin B5',
    'Vitamine B6 / Pyridoxine': 'Vitamin B6',
    'Vitamine C': 'Vitamin C',
    'Vitamine E': 'Vitamin E',
    'Vitamine H / Biotine': 'Vitamin H',
    'Vitamine K': 'Vitamin K',
    'Voedingsvezel': 'Fiber',
    'waarvan enkelvoudig onverzadigd': 'Monounsaturated Fat',
    'waarvan meervoudig onverzadigd': 'Polyunsaturated Fat',
    'waarvan onverzadigd': 'Unsaturated Fat',
    'waarvan suikers': 'Sugars',
    'waarvan suikers1': 'Sugars',
    'waarvan suikers2': 'Sugars',
    'waarvan verzadigd': 'Saturated Fat',
    'Zink': 'Zinc',
    'Zout': 'Salt',
    'Zout1': 'Salt',
    'Zout2': 'Salt'
}


def get_product_categories(url):
    # Note: this function is not used
    product_categories = []
    res = requests.get(url)
    soup = BeautifulSoup(res.content, "html.parser")
    html = list(soup.children)[2]
    body = list(html.children)[3]
    div_app = list(body.children)[16]
    start_of_content = list(div_app.children)[1]
    div_grid_root = list(start_of_content.children)[0]
    div_row = list(div_grid_root.children)[0]
    div_column = list(div_row.children)[0]
    div_product_categories = list(div_column.children)[0]
    for item in div_product_categories:
        div_root = list(item.children)[0]
        div_category = list(div_root.children)[0]
        div_taxonomy_card = list(div_category.children)[0]
        url_product = div_taxonomy_card.parent.attrs['href']
        product_categories.append(url_product)
    return product_categories


def get_products(url):
    product_urls = []
    # Url pagination is different if filters are enabled, as in the split categories
    page_sep = '?'
    for prod in SPLIT_CATEGORIES:
        if prod in url:
            page_sep = '&'
    page = 50
    url_page = url + page_sep + 'page=' + str(page)
    res = requests.get(url_page)
    soup = BeautifulSoup(res.content, "html.parser")
    html = list(soup.children)[2]
    div_app = list(html.body.children)[16]
    div_container_root = list(div_app.children)[2]
    div_container_root_search = list(div_container_root.children)[1]
    div_search_lane_wrapper = list(div_container_root_search.children)[3]
    for div_search_lane in list(div_search_lane_wrapper.children):
        div_search_lane_class = div_search_lane.attrs['class'][0]
        if 'product-grid-lane_root' in div_search_lane_class:
            divs_products = list(div_search_lane.children)
            for div in divs_products:
                div_class = div.attrs['class'][0]
                if 'product-card-portrait' in div_class:
                    div_header_root = list(div.children)[0]
                    div_hyperlink = list(div_header_root.children)[0]
                    product_urls.append(div_hyperlink.attrs['href'])
    return product_urls


def get_product_details(url_product, cat):
    product_details = dict()
    product_details['Category'] = cat
    product_details['Url'] = url_product
    res = requests.get(url_product)
    soup = BeautifulSoup(res.content, "html.parser")
    html = list(soup.children)[2]
    div_title = soup.find_all("div", class_="product-card-header_root__1GTl1")
    product_details['Product'] = list(div_title[0].children)[0].text
    div_subtitle = soup.find_all("div", class_="product-card-header_unitInfo__2ncbP")
    product_details['Subtitle'] = div_subtitle[0].text
    div_nutriscore = soup.find_all("div", class_="nutriscore_root__cYcXV product-card-hero_nutriscore__1g_JA")
    if div_nutriscore:
        product_details['NutriScore'] = div_nutriscore[0].title.text
    table_nutrition = soup.find_all("table", class_="product-info-nutrition_table__1PDio")
    if table_nutrition:
        table_nutrition_body = list(table_nutrition[0].children)[1]
        for row in table_nutrition_body.children:
            col1 = list(row.children)[0]
            col2 = list(row.children)[1]
            product_details[col1.text] = col2.text
    price = ''
    div_price = soup.find_all("div", class_="price-amount_root__37xv2 product-card-hero-price_now__PlF9u")
    if not div_price:  ## if product has discount then container has different name
        div_price = soup.find_all("div",
                                  class_="price-amount_root__37xv2 price-amount_was__1PrUY product-card-hero-price_was__1ZNtq")
        if not div_price:  ## price is in a custom div
            div_price = soup.find_all("div",
                                      class_="price-amount_root__37xv2 price-amount_bonus__27nxZ product-card-hero-price_now__PlF9u")
        if div_price:
            for child in div_price[0].children:
                price += child.text
    else:  # regular product (no discount)
        for child in div_price[0].children:
            price += child.text
    svg_vegan = soup.find_all("svg", class_="product-meta-icon product-info-icons_icon__JL5dI svg svg--ah-vegan")
    svg_vegetarian = soup.find_all("svg",
                                   class_="product-meta-icon product-info-icons_icon__JL5dI svg svg--ah-vegetarian")
    if svg_vegan:
        product_details['Vegan'] = True
        product_details['Vegetarian'] = True
    else:
        product_details['Vegan'] = False
        if svg_vegetarian:
            product_details['Vegetarian'] = True
        else:
            product_details['Vegetarian'] = False
    product_details['Price'] = price
    div_content_weight = soup.find_all("div", class_="product-info-content-block product-info-content-block--compact")
    if div_content_weight:
        content = div_content_weight[0].text
        if 'inhoud en gewicht' in content.lower():
            product_details['Content'] = content
    return product_details


def create_raw_csv(cat, product_details, col_mapping, data_dir):
    # Map column names and create dataframe
    df = pd.DataFrame()
    col_data = dict()
    for col in col_mapping:
        col_data[col] = []  # Initialize arrays
    for product in product_details:
        for col in col_mapping:
            col_data[col].append(product_details[product].get(col, None))
    for col in col_mapping:
        df[col_mapping.get(col, col)] = col_data[col]
    df.to_csv(data_dir + cat + '.csv', index=False)


def get_subtitle_unit_amount(subtitle, price):
    # try to estimate amount based on price/kg or price/lt subtitle:
    amount_estimatable = True
    if 'prijs per kg' in subtitle.lower():
        price_kg = float(subtitle[subtitle.rfind("€") + 2:len(subtitle) - 1].replace(",", "."))
        amount_estimated = 1000 * price / price_kg
        unit = 'g'
    elif 'prijs per lt' in subtitle.lower():
        price_l = float(subtitle[subtitle.rfind("€") + 2:len(subtitle) - 1].replace(",", "."))
        amount_estimated = 1000 * price / price_l
        unit = 'ml'
    else:
        amount_estimatable = False

    # Try to find amount and unit in subtitle:
    dict_unit_position = {
        'g': subtitle.find("g"),
        'kg': subtitle.find("kg"),
        'l': subtitle.find("l"),
        'cl': subtitle.find("cl"),
        'ml': subtitle.find("ml"),
        'kilogram': subtitle.find("kilogram")
    }
    # In some cases the unit is omitted in the subtitle (e.g 1,22Prijs...)
    if re.search('[\d]Prijs',subtitle) is not None:
        dict_unit_position['g_omitted'] = re.search('[\d]Prijs',subtitle).start() + 1
    else:
        dict_unit_position['g_omitted'] = -1
    # Find unit that occurs earliest in string:
    unit_position = 99  # initialize
    for unit_i in dict_unit_position:
        if -1 < dict_unit_position[unit_i] <= unit_position:
            unit_position = dict_unit_position[unit_i]
            unit = unit_i
    if unit_position < 99:  # if a unit was found:
        amount_str = subtitle[0:unit_position].replace(',', '.').replace('ca.', '').replace('ca', '')
        if 'x' in amount_str:  # e.g 10 x 7 ml
            amount_str1 = amount_str.split('x')[0]
            amount_str2 = amount_str.split('x')[1]
            if amount_str1.replace('.', '').replace(' ', '').isnumeric() and amount_str2.replace('.', '').replace(' ', '').isnumeric() :  # check if all characters are numeric
                amount = float(amount_str.split('x')[0]) * float(amount_str.split('x')[1])
                unit_available = True
            else:
                unit_available = False
        elif amount_str.replace('.','').replace(' ','').isnumeric():  # check if all characters are numeric
                amount = float(amount_str)
                unit_available = True
        else:
            unit_available = False
    else:  # no unit found
        unit_available = False

    if unit_available:
        # Convert units to g or ml
        dict_unit_conversion = {
            'g': ('g', 1),
            'kg': ('g', 1000),
            'l': ('ml', 1000),
            'cl': ('ml', 10),
            'ml': ('ml', 1),
            'kilogram': ('g', 1000),
            'g_omitted': ('g', 1)
        }
        amount = amount * dict_unit_conversion[unit][1]
        unit = dict_unit_conversion[unit][0]
    elif amount_estimatable: # if no unit is found, estimate amount from price and price/kg
        amount = amount_estimated
    else:
        amount = None
        unit = None
    # if 'per stuk' in subtitle.lower() or 'per pakket' in subtitle.lower() or 'stuks' in subtitle.lower() or 'per pakker' in subtitle.lower() or 'tros' in subtitle.lower() or 'per bos' in subtitle.lower() or 'per bosje' in subtitle.lower() or 'per krop' in subtitle.lower() or 'los per' in subtitle.lower() or 'per kilo' in subtitle.lower():
    return unit, amount


def get_weight(label):
    if pd.isna(label):
        weight = None
    else:
        label_trim = label.replace('mg', '').replace('g', '').replace('<', '')  # assumption: '<0.1g' becomes 0.1
        weight = float(label_trim)
    return weight


def create_processed_CSV(data_dir_raw, data_dir_processed):
    df_raw = pd.DataFrame()
    for filename in os.listdir(data_dir_raw):
        if '.csv' in filename:
            file = os.path.join(data_dir_raw, filename)
            df_raw = pd.concat([df_raw,pd.read_csv(file)], ignore_index=True)
    df = pd.DataFrame()
    df['product'] = df_raw['Product']
    df['url'] = df_raw['Url']
    df['category'] = df_raw['Category']
    df['price'] = df_raw['Price']
    df['amount'] = df_raw.apply(lambda x: get_subtitle_unit_amount(x['Subtitle'], x['Price'])[1], axis=1)
    df['content'] = df_raw['Content']
    df['unit'] = df_raw.apply(lambda x: get_subtitle_unit_amount(x['Subtitle'], x['Price'])[0], axis=1)
    df['vegan'] = df_raw['Vegan']
    df['vegetarian'] = df_raw['Vegetarian']
    df['nutriscore'] = df_raw['NutriScore'].apply(lambda x: None if pd.isna(x) else x.lstrip('Nutri-Score '))
    df['carbs_100g'] = df_raw['Carbohydrates'].apply(lambda x: get_weight(x))
    df['protein_100g'] = df_raw['Protein'].apply(lambda x: get_weight(x))
    df['fat_100g'] = df_raw['Fat'].apply(lambda x: get_weight(x))
    df['alcohol_100g'] = df_raw['Alcohol'].apply(lambda x: get_weight(x))
    df.to_csv(data_dir_processed, index=False)


t = time.time()
print("START: get_data")
print("Getting Data from AH Website...")
for cat in PRODUCT_CATEGORIES:
    print('   ' + cat)
    cat_products = dict()
    product_details = dict()
    url_cat = URL_PRODUCTS + '/' + cat
    cat_products[cat] = get_products(url_cat)
    for product in cat_products[cat]:
        url_product = URL_BASE + product
        print('      ' + url_product)
        sleep(TIMER)
        product_details[product] = get_product_details(url_product, cat)
    create_raw_csv(cat, product_details, COL_MAPPING, DATA_DIR_RAW)
    print("   Created Raw CSV for " + cat)
print("Creating Processed CSV...")
create_processed_CSV(DATA_DIR_RAW, DATA_DIR_PROCESSED)
print("FINISH: get_data")
print("Time elapsed: " + str(int(time.time() - t)) + ' seconds')

# # Check unique set of labels
# labels = set()
# for product in product_details:
#     for label in product_details[product]:
#         labels.add(label)
