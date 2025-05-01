from bs4 import BeautifulSoup
import json
import re
import csv

# Load the HTML file
with open("شیرینی_های محلی استان گیلان+ طرزتهیه.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

recipes = []
paragraphs = soup.find_all("p")

current = None
mode = None

location_info = {
    "province": "گیلان",
    "city": None,  
    "coordinates": {
        "latitude": None,
        "longitude": None
    }
}

for p in paragraphs:
    text = p.get_text(strip=True).replace('\u200e', '').replace('\u200f', '')

    if "color: #0000ff" in str(p):
        if current:
            full_text = current["title"] + " " + " ".join(current["ingredients"]) + " " + " ".join(current["instructions"])
            current["location"]["city"] = "فومن" if "فومن" in full_text else "رشت"
            recipes.append(current)
        current = {
            "title": text,
            "location": location_info.copy(),
            "ingredients": [],
            "instructions": [],
            "meal_type": ["شیرینی"],
            "occasion": [],
            "images": {}
        }
        mode = None

    elif "مواد لازم" in text:
        mode = "ingredients"

    elif "طرز تهیه" in text:
        mode = "instructions"

    elif p.find("img"):
        img_tag = p.find("img")
        img_url = img_tag.get("data-src") or img_tag.get("src")
        if current:
            current["images"]["تصویر نهایی"] = img_url

    else:
        if current and mode == "ingredients":
            ingredients = re.split(r'<br\s*/?>|\n', str(p))
            for item in ingredients:
                clean = BeautifulSoup(item, "html.parser").get_text().strip()
                if clean:
                    current["ingredients"].append(clean)

        elif current and mode == "instructions":
            lines = re.split(r'\n|<br\s*/?>', str(p))
            for item in lines:
                step = BeautifulSoup(item, "html.parser").get_text().strip()
                if re.match(r'^\d+\.', step):
                    current["instructions"].append(step)


if current:
    full_text = current["title"] + " " + " ".join(current["ingredients"]) + " " + " ".join(current["instructions"])
    current["location"]["city"] = "فومن" if "فومن" in full_text else "رشت"
    recipes.append(current)


with open("recipes_with_dynamic_city.json", "w", encoding="utf-8") as f_json:
    json.dump(recipes, f_json, ensure_ascii=False, indent=2)


with open("recipes_with_dynamic_city.csv", "w", newline="", encoding="utf-8") as f_csv:
    writer = csv.writer(f_csv)
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

print(len(recipes))
print("   • 'recipes_with_dynamic_city.json'")
print("   • 'recipes_with_dynamic_city.csv'")
