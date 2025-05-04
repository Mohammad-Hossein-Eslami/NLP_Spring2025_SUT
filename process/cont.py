import json
from collections import Counter
import pandas as pd

# بارگذاری فایل JSON
with open("porsche2_location_updated.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# استخراج استان‌ها
provinces = [item["location"].get("province") for item in data if item.get("location")]

# شمارش تعداد غذا در هر استان
province_counts = Counter(provinces)

# تبدیل به DataFrame برای نمایش یا ذخیره
df = pd.DataFrame(province_counts.items(), columns=["استان", "تعداد غذا"])
df = df.sort_values(by="تعداد غذا", ascending=False)

# نمایش نتیجه
print(df)
