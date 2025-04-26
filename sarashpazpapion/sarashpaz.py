import json
import csv
import requests
from bs4 import BeautifulSoup

# You manually define the URLs here
urls = [
  "https://sarashpazpapion.com/category/64/گیلانی?page=6",
  "https://sarashpazpapion.com/category/64/گیلانی?page=5",
  "https://sarashpazpapion.com/category/64/گیلانی?page=4",
  "https://sarashpazpapion.com/category/64/گیلانی?page=3",
  "https://sarashpazpapion.com/category/64/گیلانی?page=2",
  "https://sarashpazpapion.com/category/64/گیلانی"
]

PROVINCE = "گیلان"
CITY = None

all_recipe_links = []

# Step 1: Collect all recipe links from all given URLs
for url in urls:
    try:
        response = requests.get(url)
        response.raise_for_status()
        category_soup = BeautifulSoup(response.text, "html.parser")

        for article in category_soup.select("article.recipe-preview"):
            a_tag = article.find("a", class_="recipe-link")
            if a_tag and a_tag.get("href"):
                href = a_tag["href"]
                if href.startswith("http"):
                    full_link = href
                else:
                    full_link = "https://sarashpazpapion.com" + href
                all_recipe_links.append(full_link)

        print(f"✅ Collected recipes from {url}")

    except Exception as e:
        print(f"⚠️ Failed to load {url}: {e}")

print(f"📋 Total recipe links collected: {len(all_recipe_links)}")

# Step 2: Scrape each recipe
all_recipes = []
csv_rows = []

for link in all_recipe_links:
    try:
        recipe_response = requests.get(link)
        recipe_response.raise_for_status()
        soup = BeautifulSoup(recipe_response.text, "html.parser")

        # Title
        title_tag = soup.select_one("div.r-title h2")
        title = title_tag.text.strip() if title_tag else "Unknown Title"

        # Static location
        province = PROVINCE
        city = CITY
        latitude = None
        longitude = None

        # Meal Type Detection
        meal_type = []

        occasion = []

        # Simple Ingredients (full text, not split)
        ingredients = []
        for ing in soup.select("div.recipe-ing div.ing-e"):
            title_tag = ing.select_one("div.ing-title")
            unit_tag = ing.select_one("div.ing-unit")
            if title_tag and unit_tag:
                full_text = f"{unit_tag.text.strip()} {title_tag.text.strip()}"
                full_text = " ".join(full_text.split())
                ingredients.append(full_text)

        # Instructions
        instructions = []
        for step in soup.select("div.recipe-steps div.step-t"):
            step_text = step.select_one("div.step-text")
            if step_text:
                instructions.append(step_text.text.strip())

        # Final Image
        final_image_tag = soup.select_one("div.item-pic-recipe img")
        final_image_url = final_image_tag["src"] if final_image_tag else None

        # Step Images
        step_images = {}
        step_image_tags = soup.select("div.recipe-step-pics div.pics a img")
        for idx, img_tag in enumerate(step_image_tags, start=1):
            img_url = img_tag.get("data-src") or img_tag.get("src")
            step_images[f"{idx} مرحله"] = img_url

        # Build recipe object
        recipe_data = {
            "title": title,
            "location": {
                "province": province,
                "city": city,
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude
                }
            },
            "ingredients": ingredients,
            "instructions": instructions,
            "meal_type": meal_type,
            "occasion": occasion,
            "images": {
                "نهایی تصویر": final_image_url,
                **step_images
            }
        }

        all_recipes.append(recipe_data)

        # Prepare CSV row
        csv_rows.append([
            title,
            province,
            city,
            " | ".join(ingredients),
            " | ".join(instructions),
            " | ".join(meal_type),
            " | ".join(occasion),
            final_image_url
        ])

        print(f"✅ Scraped: {title}")

    except Exception as e:
        print(f"⚠️ Failed to process {link}: {e}")

# Step 3: Save all data
with open("gilani_all_recipes.json", "w", encoding="utf-8") as f_json:
    json.dump(all_recipes, f_json, ensure_ascii=False, indent=2)

with open("gilani_all_recipes.csv", "w", newline="", encoding="utf-8") as f_csv:
    writer = csv.writer(f_csv)
    writer.writerow(["Title", "Province", "City", "Ingredients", "Instructions", "Meal Type", "Occasion", "Final Image"])
    writer.writerows(csv_rows)

# Step 4: Count and print
print(f"\n🎯 Total foods collected: {len(all_recipes)}")
print("✅ Saved to 'gilani_all_recipes.json' and 'gilani_all_recipes.csv' successfully!")
