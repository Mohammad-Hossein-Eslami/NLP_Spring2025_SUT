import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import re

# -------- change ----------
url = "https://roostanet.ir/fa/6080"
province_name = "اردبیل"
province_name_english = "Ardebil"

api_key = "AIzaSyC1e-ZiJEm5x2-w70FkvtSsQd89KYieEXY"
cse_id = "9479afbc6f34c465c"
# --------------------------

def convert_persian_numbers(text):
    persian_to_english = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    return text.translate(persian_to_english)

def number_to_persian(num):
    english_to_persian = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return str(num).translate(english_to_persian)

def word_to_number(word):
    words_map = {
        "نیم": 0.5,
        "نصف": 0.5,
        "یک‌چهارم": 0.25,
        "سه‌چهارم": 0.75,
        "یک": 1,
        "دو": 2,
        "سه": 3,
        "چهار": 4,
        "پنج": 5,
        "شش": 6,
        "هفت": 7,
        "هشت": 8,
        "نه": 9,
        "ده": 10
    }
    return words_map.get(word.strip(), None)

def get_food_image_url(query):
    search_url = "https://www.googleapis.com/customsearch/v1"
    try:
        params = {
            "q": query,
            "cx": cse_id,
            "key": api_key,
            "searchType": "image",
            "num": 1
        }
        res = requests.get(search_url, params=params)
        data = res.json()
        if "items" in data:
            return data["items"][0]["link"]
    except Exception as e:
        print("Image fetch error:", e)
    return None

response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

foods = []
tables = soup.find_all('table')

for table in tables:
    rows = table.find_all('tr')
    if len(rows) < 5:
        continue

    entry = {
        "title": "",
        "location": {
            "province": province_name,
            "city": "",
            "coordinates": {
                "latitude": None,
                "longitude": None
            }
        },
        "ingredients": [],
        "instructions": [],
        "meal_type": [],
        "occasion": [],
        "images": {}
    }

    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 2:
            continue

        label = cols[0].get_text(strip=True)
        value_text = cols[1].get_text(strip=True)

        if "نام غذا" in label:
            entry["title"] = value_text

        elif "شهر" in label:
            entry["location"]["city"] = value_text.strip()

        elif "گروه" in label:
            entry["meal_type"] = [value_text.strip()] if value_text.strip() else []

        elif "مواد لازم" in label:
            html_raw = cols[1].decode_contents()
            html_raw = html_raw.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
            lines = html_raw.split('\n')

            for line in lines:
                clean_line = BeautifulSoup(line, 'html.parser').get_text().strip()
                if not clean_line or clean_line.replace('-', '').strip() == '':
                    continue

                clean_line = convert_persian_numbers(clean_line)
                clean_line = re.sub(r'(\d)([^\s\d])', r'\1 \2', clean_line)
                clean_line = re.sub(r'([^\s\d])(\d)', r'\1 \2', clean_line)
                clean_line = re.sub(r'\s{2,}', ' ', clean_line).strip()

                match = re.match(
                    r'^(.+?)\s+(\d+(?:\.\d+)?|نیم|نصف|یک‌چهارم|سه‌چهارم|یک|دو|سه|چهار|پنج|شش|هفت|هشت|نه|ده)\s+(.+)$',
                    clean_line
                )

                if match:
                    name = match.group(1).strip()
                    amount_str = match.group(2).strip()
                    unit = match.group(3).strip()

                    amount = word_to_number(amount_str)
                    if amount is None:
                        try:
                            amount = float(amount_str)
                        except:
                            amount = None

                    if amount is not None:
                        amount_fa = number_to_persian(amount).replace(".۰", "")
                        ingredient_text = f"{amount_fa} {unit} {name}"
                    else:
                        ingredient_text = clean_line

                    entry["ingredients"].append(ingredient_text)
                else:
                    entry["ingredients"].append(clean_line)

        elif "طرز تهیه" in label:
            fixed_value = cols[1].decode_contents().replace('<br>', '.').replace('<br/>', '.').replace('<br />', '.')
            text = BeautifulSoup(fixed_value, 'html.parser').get_text()
            text = text.replace('\n', ' ')
            text = re.sub(r'\s{2,}', ' ', text).strip()
            sentences = [s.strip() for s in re.split(r'[.!؟]\s*', text) if s.strip()]
            entry["instructions"] = sentences

    image_url = get_food_image_url(entry["title"])
    if image_url:
        entry["images"]["تصویر نهایی"] = image_url

    foods.append(entry)

foods = [food for food in foods if food["title"].strip()]

with open(f"{province_name_english}_foods.json", "w", encoding='utf-8') as f:
    json.dump(foods, f, ensure_ascii=False, indent=2)

flat_rows = []
for food in foods:
    flat_rows.append({
        "title": food["title"],
        "province": food["location"]["province"],
        "city": food["location"]["city"],
        "latitude": food["location"]["coordinates"]["latitude"],
        "longitude": food["location"]["coordinates"]["longitude"],
        "ingredients": json.dumps(food["ingredients"], ensure_ascii=False),
        "instructions": json.dumps(food["instructions"], ensure_ascii=False),
        "meal_type": ", ".join(food["meal_type"]) if food["meal_type"] else "",
        "occasion": ", ".join(food["occasion"]) if food["occasion"] else "",
        "image_url": food["images"].get("تصویر نهایی", "")
    })

df = pd.DataFrame(flat_rows)
df.to_csv(f"{province_name_english}_foods.csv", index=False, encoding='utf-8-sig')
