import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out_dir = Path(__file__).parent
out_dir.mkdir(parents=True, exist_ok=True)

# Load high-quality TrueType fonts
font_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 24)
font_sub = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 17)
font_body = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 15)
font_bold = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 15)
font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 13)
font_hindi_title = ImageFont.truetype("C:/Windows/Fonts/Nirmala.ttc", 22)
font_hindi_body = ImageFont.truetype("C:/Windows/Fonts/Nirmala.ttc", 15)

def draw_veg_logo(draw, x, y, size=36, is_veg=True):
    color = (34, 139, 34) if is_veg else (139, 69, 19)
    # Square outline
    draw.rectangle([x, y, x + size, y + size], outline=color, width=2)
    if is_veg:
        # Green circle
        margin = size * 0.22
        draw.ellipse([x + margin, y + margin, x + size - margin, y + size - margin], fill=color)
    else:
        # Brown triangle
        pad = size * 0.2
        p1 = (x + size / 2, y + pad)
        p2 = (x + pad, y + size - pad)
        p3 = (x + size - pad, y + size - pad)
        draw.polygon([p1, p2, p3], fill=color)

def draw_barcode(draw, x, y, width=180, height=45):
    draw.rectangle([x, y, x + width, y + height], fill=(255, 255, 255))
    bar_x = x + 8
    import random
    random.seed(42)
    while bar_x < x + width - 15:
        w = random.choice([1, 2, 3])
        draw.rectangle([bar_x, y + 4, bar_x + w, y + height - 14], fill=(0, 0, 0))
        bar_x += w + random.choice([2, 3])
    draw.text((x + 20, y + height - 12), "8 901491 884729", fill=(0, 0, 0), font=font_small)

# -------------------------------------------------------------
# IMAGE 1: Deceptive "No Added Sugar" Fruit Juice (Violation)
# -------------------------------------------------------------
img1 = Image.new("RGB", (850, 1050), color=(255, 253, 248))
d1 = ImageDraw.Draw(img1)
draw_veg_logo(d1, 760, 35, size=40, is_veg=True)

d1.text((45, 35), "ORCHARD HARVEST", fill=(180, 40, 30), font=font_title)
d1.text((45, 72), "PURE APPLE CRUNCH FRUIT JUICE", fill=(20, 20, 20), font=font_sub)
d1.text((45, 105), "100% Real Fruit Juice • No Added Sugar • 100% Pure & Natural", fill=(34, 139, 34), font=font_bold)

d1.line([(45, 140), (805, 140)], fill=(210, 210, 210), width=2)
d1.text((45, 155), "FSSAI Lic. No. 10019022008432", fill=(40, 40, 40), font=font_bold)
d1.text((45, 185), "Batch No: OH-2026-X1   |   Mfg Date: 10/08/2026", fill=(40, 40, 40), font=font_body)
d1.text((45, 215), "Best Before: 6 Months from packaging", fill=(40, 40, 40), font=font_body)
d1.text((45, 245), "Net Quantity: 200 ml   |   MRP: Rs. 45.00 (Incl. of all taxes)", fill=(40, 40, 40), font=font_body)

d1.line([(45, 280), (805, 280)], fill=(210, 210, 210), width=2)
d1.text((45, 295), "LIST OF INGREDIENTS:", fill=(140, 30, 20), font=font_bold)
d1.text((45, 325), "Water, Reconstituted Apple Juice Concentrate (30%), High Fructose Corn Syrup,", fill=(40, 40, 40), font=font_body)
d1.text((45, 355), "Invert Sugar, Liquid Glucose, Acidity Regulator (INS 330), Preservative (INS 211),", fill=(40, 40, 40), font=font_body)
d1.text((45, 385), "Permitted Synthetic Food Colour (INS 150d), Nature Identical Flavour.", fill=(40, 40, 40), font=font_body)

d1.line([(45, 425), (805, 425)], fill=(210, 210, 210), width=2)
d1.text((45, 440), "NUTRITIONAL INFORMATION (Per 100 ml):", fill=(20, 20, 20), font=font_bold)

# Nutrition rows (clean, readable table lines)
y_offset = 475
nutrients_1 = [
    ("Energy", "68.0 kcal"),
    ("Protein", "0.2 g"),
    ("Total Carbohydrates", "17.0 g"),
    ("Total Sugars", "16.2 g"),
    ("Added Sugars", "13.5 g"),
    ("Total Fat", "0.0 g"),
    ("Saturated Fat", "0.0 g"),
    ("Trans Fat", "0.0 g"),
    ("Sodium", "15 mg")
]
for item, val in nutrients_1:
    d1.text((55, y_offset), f"{item}:", fill=(40, 40, 40), font=font_body)
    d1.text((320, y_offset), val, fill=(40, 40, 40), font=font_bold)
    y_offset += 30

d1.line([(45, y_offset + 10), (805, y_offset + 10)], fill=(210, 210, 210), width=1)
draw_barcode(d1, 45, y_offset + 30)
d1.text((260, y_offset + 35), "Marketed by: Orchard Harvest India Pvt Ltd, Mumbai - 400001", fill=(70, 70, 70), font=font_small)
d1.text((260, y_offset + 60), "Consumer Care: feedback@orchardharvest.in | Toll-Free: 1800-444-222", fill=(70, 70, 70), font=font_small)

img1.save(out_dir / "sample_sugar_violation.jpg", quality=95)

# -------------------------------------------------------------
# IMAGE 2: High-Protein Bar (Missing Allergen Advisory)
# -------------------------------------------------------------
img2 = Image.new("RGB", (850, 1050), color=(252, 255, 252))
d2 = ImageDraw.Draw(img2)
draw_veg_logo(d2, 760, 35, size=40, is_veg=True)

d2.text((45, 35), "NUTRI-FORCE FUEL", fill=(20, 100, 40), font=font_title)
d2.text((45, 72), "ALMOND PEANUT CRUNCH PROTEIN BAR", fill=(20, 20, 20), font=font_sub)
d2.text((45, 105), "20g High Protein • Clean Energy Snack • Rich in Fiber", fill=(50, 50, 50), font=font_bold)

d2.line([(45, 140), (805, 140)], fill=(210, 210, 210), width=2)
d2.text((45, 155), "FSSAI Lic. No. 10021044001928", fill=(40, 40, 40), font=font_bold)
d2.text((45, 185), "Batch No: NF-BAR-89   |   Mfg Date: 05/09/2026", fill=(40, 40, 40), font=font_body)
d2.text((45, 215), "Best Before: 9 Months from packaging", fill=(40, 40, 40), font=font_body)
d2.text((45, 245), "Net Weight: 60g   |   MRP: Rs. 99.00 (Incl. of all taxes)", fill=(40, 40, 40), font=font_body)

d2.line([(45, 280), (805, 280)], fill=(210, 210, 210), width=2)
d2.text((45, 295), "INGREDIENTS:", fill=(20, 80, 30), font=font_bold)
d2.text((45, 325), "Rolled Oats (Gluten), Whey Protein Isolate (Cow Milk), Roasted Peanuts (22%),", fill=(40, 40, 40), font=font_body)
d2.text((45, 355), "California Almonds (14%), Dates Paste, Raw Honey, Soya Lecithin (INS 322).", fill=(40, 40, 40), font=font_body)
d2.text((45, 385), "[Note: No Allergen Advisory is printed on this package]", fill=(180, 30, 20), font=font_small)

d2.line([(45, 425), (805, 425)], fill=(210, 210, 210), width=2)
d2.text((45, 440), "NUTRITIONAL FACTS (Per 60g Serving):", fill=(20, 20, 20), font=font_bold)

y_offset = 475
nutrients_2 = [
    ("Energy", "245.0 kcal"),
    ("Protein", "20.0 g"),
    ("Total Carbohydrates", "28.0 g"),
    ("Total Sugars", "8.0 g"),
    ("Added Sugars", "0.0 g"),
    ("Total Fat", "9.5 g"),
    ("Saturated Fat", "1.8 g"),
    ("Trans Fat", "0.0 g"),
    ("Sodium", "65 mg")
]
for item, val in nutrients_2:
    d2.text((55, y_offset), f"{item}:", fill=(40, 40, 40), font=font_body)
    d2.text((320, y_offset), val, fill=(40, 40, 40), font=font_bold)
    y_offset += 30

d2.line([(45, y_offset + 10), (805, y_offset + 10)], fill=(210, 210, 210), width=1)
draw_barcode(d2, 45, y_offset + 30)
d2.text((260, y_offset + 35), "Manufactured by: Nutri-Force Wellness Pvt Ltd, Bengaluru - 560001", fill=(70, 70, 70), font=font_small)
d2.text((260, y_offset + 60), "Helpline: 1800-999-111 | Email: care@nutriforce.in", fill=(70, 70, 70), font=font_small)

img2.save(out_dir / "sample_allergen_violation.jpg", quality=95)

# -------------------------------------------------------------
# IMAGE 3: Missing FSSAI License & Missing Saturated/Trans Fat
# -------------------------------------------------------------
img3 = Image.new("RGB", (850, 1050), color=(255, 250, 245))
d3 = ImageDraw.Draw(img3)
draw_veg_logo(d3, 760, 35, size=40, is_veg=True)

d3.text((45, 35), "GRANDMA's BAKERY", fill=(140, 70, 20), font=font_title)
d3.text((45, 72), "RICH BUTTER COOKIES", fill=(20, 20, 20), font=font_sub)
d3.text((45, 105), "Baked with Love & Traditional Goodness", fill=(100, 100, 100), font=font_bold)

d3.line([(45, 140), (805, 140)], fill=(210, 210, 210), width=2)
d3.text((45, 155), "FSSAI License: FSSAI Approved [MISSING 14-DIGIT NUMBER]", fill=(180, 30, 20), font=font_bold)
d3.text((45, 185), "Batch No: GB-77   |   Mfg Date: 20/08/2026", fill=(40, 40, 40), font=font_body)
d3.text((45, 215), "Best Before: 6 Months from packaging", fill=(40, 40, 40), font=font_body)
d3.text((45, 245), "Net Weight: 150g   |   MRP: Rs. 50.00", fill=(40, 40, 40), font=font_body)

d3.line([(45, 280), (805, 280)], fill=(210, 210, 210), width=2)
d3.text((45, 295), "INGREDIENTS:", fill=(120, 60, 20), font=font_bold)
d3.text((45, 325), "Refined Wheat Flour (Maida), Butter (18%), Sugar, Hydrogenated Vegetable Fat,", fill=(40, 40, 40), font=font_body)
d3.text((45, 355), "Milk Solids, Invert Syrup, Raising Agents [INS 500(ii), INS 503(ii)].", fill=(40, 40, 40), font=font_body)
d3.text((45, 385), "ALLERGEN ADVICE: Contains Wheat (Gluten) and Milk.", fill=(40, 40, 40), font=font_body)

d3.line([(45, 425), (805, 425)], fill=(210, 210, 210), width=2)
d3.text((45, 440), "NUTRITIONAL FACTS (Per 100g):", fill=(20, 20, 20), font=font_bold)

y_offset = 475
nutrients_3 = [
    ("Energy", "490.0 kcal"),
    ("Protein", "6.5 g"),
    ("Total Carbohydrates", "65.0 g"),
    ("Total Sugars", "24.0 g"),
    ("Total Fat", "22.0 g"),
    # Saturated Fat and Trans Fat deliberately omitted!
    ("Sodium", "180 mg")
]
for item, val in nutrients_3:
    d3.text((55, y_offset), f"{item}:", fill=(40, 40, 40), font=font_body)
    d3.text((320, y_offset), val, fill=(40, 40, 40), font=font_bold)
    y_offset += 30

d3.text((55, y_offset + 10), "[Saturated Fat & Trans Fat rows omitted by manufacturer]", fill=(180, 30, 20), font=font_small)

d3.line([(45, y_offset + 40), (805, y_offset + 40)], fill=(210, 210, 210), width=1)
draw_barcode(d3, 45, y_offset + 55)
d3.text((260, y_offset + 60), "Manufactured by: Grandma Bakery Confectionery, Pune - 411001", fill=(70, 70, 70), font=font_small)
d3.text((260, y_offset + 85), "Customer Helpline: support@grandmabakery.in", fill=(70, 70, 70), font=font_small)

img3.save(out_dir / "sample_missing_fssai_fat.jpg", quality=95)

# -------------------------------------------------------------
# IMAGE 4: Bilingual Compliant Haldiram-style Bhujia
# -------------------------------------------------------------
img4 = Image.new("RGB", (850, 1080), color=(255, 255, 250))
d4 = ImageDraw.Draw(img4)
draw_veg_logo(d4, 760, 35, size=40, is_veg=True)

d4.text((45, 35), "बीकानेर स्वाद  •  BIKANER SWAD", fill=(180, 50, 20), font=font_hindi_title)
d4.text((45, 75), "पारंपरिक बेसन भुजिया  •  BESAN BHUJIA", fill=(20, 20, 20), font=font_hindi_title)
d4.text((45, 115), "100% शाकाहारी नमकीन / Traditional Vegetarian Snack", fill=(34, 139, 34), font=font_hindi_body)

d4.line([(45, 150), (805, 150)], fill=(210, 210, 210), width=2)
d4.text((45, 165), "FSSAI Lic. No. 10020011000452", fill=(40, 40, 40), font=font_bold)
d4.text((45, 195), "Batch No: BS-AUG-44   |   Mfg Date: 15/08/2026", fill=(40, 40, 40), font=font_body)
d4.text((45, 225), "Best Before: 4 Months from manufacture", fill=(40, 40, 40), font=font_body)
d4.text((45, 255), "Net Weight: 200g   |   MRP: Rs. 65.00 (Inclusive of all taxes)", fill=(40, 40, 40), font=font_body)

d4.line([(45, 290), (805, 290)], fill=(210, 210, 210), width=2)
d4.text((45, 305), "सामग्री / INGREDIENTS:", fill=(140, 40, 20), font=font_hindi_title)
d4.text((45, 340), "चना बेसन (Bengal Gram Flour 48%), खाद्य वनस्पति तेल (Edible Vegetable Oil),", fill=(40, 40, 40), font=font_hindi_body)
d4.text((45, 370), "आयोडीन युक्त नमक (Iodized Salt), लाल मिर्च पाउडर (Red Chilli), काली मिर्च, हींग।", fill=(40, 40, 40), font=font_hindi_body)
d4.text((45, 405), "ALLERGEN ADVICE: Contains Gluten. May contain traces of peanut and sesame.", fill=(30, 30, 30), font=font_bold)

d4.line([(45, 440), (805, 440)], fill=(210, 210, 210), width=2)
d4.text((45, 455), "NUTRITIONAL FACTS (प्रति 100 ग्राम / Per 100g):", fill=(20, 20, 20), font=font_bold)

y_offset = 490
nutrients_4 = [
    ("Energy (ऊर्जा)", "560.0 kcal"),
    ("Protein (प्रोटीन)", "13.5 g"),
    ("Total Carbohydrates (कार्बोहाइड्रेट)", "42.0 g"),
    ("Total Sugars (कुल शर्करा)", "1.2 g"),
    ("Added Sugars (अतिरिक्त चीनी)", "0.0 g"),
    ("Total Fat (कुल वसा)", "38.0 g"),
    ("Saturated Fat (संतृप्त वसा)", "14.5 g"),
    ("Trans Fat (ट्रांस वसा)", "0.1 g"),
    ("Sodium (सोडियम)", "680 mg")
]
for item, val in nutrients_4:
    d4.text((55, y_offset), f"{item}:", fill=(40, 40, 40), font=font_body)
    d4.text((400, y_offset), val, fill=(40, 40, 40), font=font_bold)
    y_offset += 30

d4.line([(45, y_offset + 10), (805, y_offset + 10)], fill=(210, 210, 210), width=1)
draw_barcode(d4, 45, y_offset + 25)
d4.text((260, y_offset + 30), "Manufactured by: Bikaner Swad Foods Pvt Ltd, Bikaner, Rajasthan - 334001", fill=(70, 70, 70), font=font_small)
d4.text((260, y_offset + 55), "Consumer Helpline: care@bikanerswad.com | Phone: +91-11-23456789", fill=(70, 70, 70), font=font_small)

img4.save(out_dir / "sample_bilingual_compliant.jpg", quality=95)

# -------------------------------------------------------------
# IMAGE 5: Misleading "100% Pure & Natural" Mango Drink
# -------------------------------------------------------------
img5 = Image.new("RGB", (850, 1050), color=(255, 253, 240))
d5 = ImageDraw.Draw(img5)
draw_veg_logo(d5, 760, 35, size=40, is_veg=True)

d5.text((45, 35), "ROYAL MANGO DELIGHT", fill=(210, 120, 20), font=font_title)
d5.text((45, 72), "100% PURE & NATURAL MANGO DRINK", fill=(20, 20, 20), font=font_sub)
d5.text((45, 105), "Farm Fresh Alphonso • 100% Natural Guarantee", fill=(34, 139, 34), font=font_bold)

d5.line([(45, 140), (805, 140)], fill=(210, 210, 210), width=2)
d5.text((45, 155), "FSSAI Lic. No. 10017011003456", fill=(40, 40, 40), font=font_bold)
d5.text((45, 185), "Batch No: RM-882   |   Mfg Date: 12/09/2026", fill=(40, 40, 40), font=font_body)
d5.text((45, 215), "Best Before: 6 Months from packaging", fill=(40, 40, 40), font=font_body)
d5.text((45, 245), "Net Quantity: 250 ml   |   MRP: Rs. 35.00 (Incl. of all taxes)", fill=(40, 40, 40), font=font_body)

d5.line([(45, 280), (805, 280)], fill=(210, 210, 210), width=2)
d5.text((45, 295), "INGREDIENTS:", fill=(160, 80, 20), font=font_bold)
d5.text((45, 325), "Water, Mango Pulp (19%), Sugar, Acidity Regulator (INS 330),", fill=(40, 40, 40), font=font_body)
d5.text((45, 355), "Synthetic Food Colour (INS 110 Sunset Yellow),", fill=(40, 40, 40), font=font_body)
d5.text((45, 385), "Class II Preservative (INS 211 Sodium Benzoate), Added Flavours.", fill=(40, 40, 40), font=font_body)

d5.line([(45, 425), (805, 425)], fill=(210, 210, 210), width=2)
d5.text((45, 440), "NUTRITION FACTS (Per 100 ml):", fill=(20, 20, 20), font=font_bold)

y_offset = 475
nutrients_5 = [
    ("Energy", "62.0 kcal"),
    ("Protein", "0.1 g"),
    ("Total Carbohydrates", "15.5 g"),
    ("Total Sugars", "15.0 g"),
    ("Added Sugars", "12.0 g"),
    ("Total Fat", "0.0 g"),
    ("Saturated Fat", "0.0 g"),
    ("Trans Fat", "0.0 g"),
    ("Sodium", "12 mg")
]
for item, val in nutrients_5:
    d5.text((55, y_offset), f"{item}:", fill=(40, 40, 40), font=font_body)
    d5.text((320, y_offset), val, fill=(40, 40, 40), font=font_bold)
    y_offset += 30

d5.line([(45, y_offset + 10), (805, y_offset + 10)], fill=(210, 210, 210), width=1)
draw_barcode(d5, 45, y_offset + 25)
d5.text((260, y_offset + 30), "Royal Agro Beverages Ltd, Ratnagiri, Maharashtra - 415612", fill=(70, 70, 70), font=font_small)
d5.text((260, y_offset + 55), "Feedback Helpline: info@royalbeverages.in", fill=(70, 70, 70), font=font_small)

img5.save(out_dir / "sample_misleading_natural.jpg", quality=95)

print("Successfully generated 5 high-resolution test packaging label images in:", out_dir)
