from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

out_dir = Path(__file__).parent
out_dir.mkdir(parents=True, exist_ok=True)

def draw_veg_logo(draw, x, y, size=30):
    # Green square outline + green filled circle
    draw.rectangle([x, y, x + size, y + size], outline=(34, 139, 34), width=3)
    margin = size * 0.25
    draw.ellipse([x + margin, y + margin, x + size - margin, y + size - margin], fill=(34, 139, 34))

# 1. Sample 1: Deceptive Sugar Juice
img1 = Image.new("RGB", (700, 900), color=(255, 250, 240))
d1 = ImageDraw.Draw(img1)
draw_veg_logo(d1, 620, 30, size=40)

d1.text((40, 40), "NATUREFRESH ORCHARDS", fill=(160, 40, 40))
d1.text((40, 80), "PUREBERRY APPLE JUICE", fill=(20, 20, 20))
d1.text((40, 120), "100% Real Fruit Juice - No Added Sugar", fill=(34, 139, 34))

d1.line([(40, 160), (660, 160)], fill=(200, 200, 200), width=2)
d1.text((40, 180), "FSSAI Lic. No. 10018022007891", fill=(30, 30, 30))
d1.text((40, 210), "Batch No: NF-2026-B4 | Mfg Date: 12/08/2026", fill=(30, 30, 30))
d1.text((40, 240), "Best Before 6 months from packaging", fill=(30, 30, 30))
d1.text((40, 270), "Net Quantity: 200 ml | MRP: Rs. 40.00", fill=(30, 30, 30))

d1.line([(40, 310), (660, 310)], fill=(200, 200, 200), width=2)
d1.text((40, 330), "INGREDIENTS:", fill=(100, 20, 20))
d1.text((40, 360), "Water, Reconstituted Apple Juice (35%),", fill=(40, 40, 40))
d1.text((40, 390), "High Fructose Corn Syrup, Invert Sugar,", fill=(40, 40, 40))
d1.text((40, 420), "Acidity Regulator (INS 330), Preservative (INS 211),", fill=(40, 40, 40))
d1.text((40, 450), "Synthetic Apple Flavour.", fill=(40, 40, 40))

d1.line([(40, 500), (660, 500)], fill=(200, 200, 200), width=2)
d1.text((40, 520), "NUTRITIONAL INFORMATION (per 100 ml):", fill=(20, 20, 20))
d1.text((40, 550), "Energy: 65 kcal", fill=(40, 40, 40))
d1.text((40, 580), "Protein: 0.2 g", fill=(40, 40, 40))
d1.text((40, 610), "Carbohydrates: 16.0 g", fill=(40, 40, 40))
d1.text((40, 640), "Total Sugars: 15.5 g", fill=(40, 40, 40))
d1.text((40, 670), "Added Sugars: 12.0 g", fill=(40, 40, 40))
d1.text((40, 700), "Total Fat: 0.0 g", fill=(40, 40, 40))
d1.text((40, 730), "Saturated Fat: 0.0 g | Trans Fat: 0.0 g", fill=(40, 40, 40))
d1.text((40, 760), "Sodium: 18 mg", fill=(40, 40, 40))
d1.text((40, 810), "Customer Care: support@naturefreshfoods.in", fill=(60, 60, 60))

img1.save(out_dir / "sample_sugar_violation.jpg", quality=95)

# 2. Sample 2: Compliant Snack
img2 = Image.new("RGB", (700, 900), color=(255, 255, 250))
d2 = ImageDraw.Draw(img2)
draw_veg_logo(d2, 620, 30, size=40)

d2.text((40, 40), "BIKANER SWAD", fill=(180, 50, 20))
d2.text((40, 80), "TRADITIONAL BESAN BHUJIA", fill=(20, 20, 20))
d2.text((40, 120), "100% Vegetarian Snack", fill=(34, 139, 34))

d2.line([(40, 160), (660, 160)], fill=(200, 200, 200), width=2)
d2.text((40, 180), "FSSAI Lic. No. 10020011000452", fill=(30, 30, 30))
d2.text((40, 210), "Batch No: BS-AUG-44 | Mfg Date: 15/08/2026", fill=(30, 30, 30))
d2.text((40, 240), "Best Before: 4 Months from packaging", fill=(30, 30, 30))
d2.text((40, 270), "Net Wt: 200g | MRP: Rs. 65.00", fill=(30, 30, 30))

d2.line([(40, 310), (660, 310)], fill=(200, 200, 200), width=2)
d2.text((40, 330), "INGREDIENTS:", fill=(100, 20, 20))
d2.text((40, 360), "Bengal Gram Flour (48%), Edible Vegetable Oil,", fill=(40, 40, 40))
d2.text((40, 390), "Iodized Salt, Red Chilli, Black Pepper, Spices.", fill=(40, 40, 40))
d2.text((40, 430), "ALLERGEN ADVICE: Contains Gluten. May contain traces of peanut.", fill=(160, 80, 20))

d2.line([(40, 480), (660, 480)], fill=(200, 200, 200), width=2)
d2.text((40, 500), "NUTRITIONAL FACTS (per 100g):", fill=(20, 20, 20))
d2.text((40, 530), "Energy: 560 kcal", fill=(40, 40, 40))
d2.text((40, 560), "Protein: 13.5 g", fill=(40, 40, 40))
d2.text((40, 590), "Carbohydrate: 42.0 g", fill=(40, 40, 40))
d2.text((40, 620), "Total Sugars: 1.2 g | Added Sugars: 0.0 g", fill=(40, 40, 40))
d2.text((40, 650), "Total Fat: 38.0 g", fill=(40, 40, 40))
d2.text((40, 680), "Saturated Fat: 14.5 g | Trans Fat: 0.1 g", fill=(40, 40, 40))
d2.text((40, 710), "Sodium: 680 mg", fill=(40, 40, 40))
d2.text((40, 760), "Customer Care: customercare@bikanerswad.com", fill=(60, 60, 60))

img2.save(out_dir / "sample_bilingual_compliant.jpg", quality=95)

print("Generated sample packaging images in backend/data/test_samples/")
