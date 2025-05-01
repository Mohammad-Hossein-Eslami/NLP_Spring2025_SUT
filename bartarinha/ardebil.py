from bs4 import BeautifulSoup
import json
import csv

with open("شیرینی_های خوشمزه اردبیل؛ از حلوای زنجبیلی تا نان برنجی.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

location_info = {
    "province": "اردبیل",
    "city": "اردبیل",
    "coordinates": {
        "latitude":  None,
        "longitude": None
    }
}

recipes = []
current = None
mode = None

skip_keywords = ["مواد لازم", "مواد اولیه", "طرز تهیه", "طرزتهیه", "دستور تهیه"]

ads_keywords = ["قیمت", "بلیط", "دانلود", "کلینیک", "زیبایی", "اجاره", "قالیشویی", "دانلود موزیک", "متد", "اندام", "سپانیا", "یخچال", "کفپوش"]

def is_valid_line(line):
    return not any(ad in line for ad in ads_keywords)

def clean_entry(entry):
    return not any(entry.strip().startswith(k) for k in skip_keywords)

for tag in soup.find_all(["p", "strong"]):
    strong = tag.find("strong")
    if strong:
        title_text = strong.get_text(strip=True)
        if not any(k in title_text for k in skip_keywords):
            if current and (current["ingredients"] or current["instructions"]):
                recipes.append(current)
            current = {
                "title": title_text,
                "location": location_info.copy(),
                "ingredients": [],
                "instructions": [],
                "images": {},
                "meal_type": ["شیرینی"],
                "occasion": []
            }
            mode = None
        elif "مواد" in title_text:
            mode = "ingredients"
        elif "طرز" in title_text or "دستور" in title_text:
            mode = "instructions"

    elif tag.find("img"):
        if current:
            img_url = tag.find("img").get("src")
            current["images"]["تصویر نهایی"] = img_url

    else:
        text = tag.get_text(strip=True)
        if not text or not current:
            continue
        if mode == "ingredients" and clean_entry(text):
            current["ingredients"].append(text)
        elif mode == "instructions" and clean_entry(text) and is_valid_line(text):
            current["instructions"].append(text)

if current and (current["ingredients"] or current["instructions"]):
    recipes.append(current)

# Save cleaned results
with open("final_ardebil_recipes.json", "w", encoding="utf-8") as f:
    json.dump(recipes, f, ensure_ascii=False, indent=2)

with open("final_ardebil_recipes.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Title", "Province", "City", "Ingredients", "Instructions", "Image"])
    for r in recipes:
        writer.writerow([
            r["title"],
            r["location"]["province"],
            r["location"]["city"],
            " | ".join(r["ingredients"]),
            " | ".join(r["instructions"]),
            r["images"].get("تصویر نهایی", "")
        ])

print("✅ خروجی تمیز و نهایی در فایل‌های: final_ardebil_recipes.json و final_ardebil_recipes.csv ذخیره شد.")
