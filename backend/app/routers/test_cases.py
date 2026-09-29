from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter(prefix="/test-cases", tags=["Showcase Test Cases"])

SHOWCASE_CASES = [
    {
        "id": "case-sugar-violation",
        "title": "Case 1: Deceptive 'No Added Sugar' Fruit Juice",
        "product_name": "Pure Apple Crunch Fruit Juice",
        "brand": "Orchard Harvest",
        "image_url": "/static/test_samples/sample_sugar_violation.jpg",
        "description": "Boldly claims '100% Real Fruit Juice • No Added Sugar' on the front, but ingredients contain High Fructose Corn Syrup, Invert Sugar, Liquid Glucose, and synthetic food additives.",
        "sample_ocr_text": """ORCHARD HARVEST
PURE APPLE CRUNCH FRUIT JUICE
100% Real Fruit Juice • No Added Sugar • 100% Pure & Natural
FSSAI Lic. No. 10019022008432
Batch No: OH-2026-X1 | Mfg Date: 10/08/2026
Best Before: 6 Months from packaging
Net Quantity: 200 ml | MRP: Rs. 45.00 (Incl. of all taxes)
LIST OF INGREDIENTS:
Water, Reconstituted Apple Juice Concentrate (30%), High Fructose Corn Syrup, Invert Sugar, Liquid Glucose, Acidity Regulator (INS 330), Preservative (INS 211), Permitted Synthetic Food Colour (INS 150d), Nature Identical Flavour.
NUTRITIONAL INFORMATION (Per 100 ml):
Energy: 68.0 kcal
Protein: 0.2 g
Total Carbohydrates: 17.0 g
Total Sugars: 16.2 g
Added Sugars: 13.5 g
Total Fat: 0.0 g
Saturated Fat: 0.0 g
Trans Fat: 0.0 g
Sodium: 15 mg
Marketed by: Orchard Harvest India Pvt Ltd, Mumbai - 400001
Consumer Care: feedback@orchardharvest.in | Toll-Free: 1800-444-222""",
        "expected_violations": [
            "Deceptive 'No Added Sugar' claim (ingredients disclose High Fructose Corn Syrup & Invert Sugar; 13.5g added sugars)",
            "Misleading '100% Pure & Natural' claim (contains synthetic color INS 150d and preservative INS 211)"
        ]
    },
    {
        "id": "case-allergen-violation",
        "title": "Case 2: High-Protein Bar (Missing Allergen Advisory)",
        "product_name": "Almond Peanut Crunch Protein Bar",
        "brand": "Nutri-Force Fuel",
        "image_url": "/static/test_samples/sample_allergen_violation.jpg",
        "description": "High-protein snack bar containing rolled oats (gluten), cow milk whey, roasted peanuts, almonds, and soy lecithin, with NO mandatory Allergen Advice statement.",
        "sample_ocr_text": """NUTRI-FORCE FUEL
ALMOND PEANUT CRUNCH PROTEIN BAR
20g High Protein • Clean Energy Snack • Rich in Fiber
FSSAI Lic. No. 10021044001928
Batch No: NF-BAR-89 | Mfg Date: 05/09/2026
Best Before: 9 Months from packaging
Net Weight: 60g | MRP: Rs. 99.00 (Incl. of all taxes)
INGREDIENTS:
Rolled Oats (Gluten), Whey Protein Isolate (Cow Milk), Roasted Peanuts (22%), California Almonds (14%), Dates Paste, Raw Honey, Soya Lecithin (INS 322).
NUTRITIONAL FACTS (Per 60g Serving):
Energy: 245.0 kcal
Protein: 20.0 g
Total Carbohydrates: 28.0 g
Total Sugars: 8.0 g
Added Sugars: 0.0 g
Total Fat: 9.5 g
Saturated Fat: 1.8 g
Trans Fat: 0.0 g
Sodium: 65 mg
Manufactured by: Nutri-Force Wellness Pvt Ltd, Bengaluru - 560001
Helpline: 1800-999-111 | Email: care@nutriforce.in""",
        "expected_violations": [
            "Mandatory Allergen Declaration missing (contains Peanuts, Almonds, Milk/Whey, Soy, Oats/Gluten with no 'ALLERGEN ADVICE' statement)"
        ]
    },
    {
        "id": "case-missing-fssai-fat",
        "title": "Case 3: Cookies (Missing 14-Digit FSSAI License & Fat Rows)",
        "product_name": "Rich Butter Cookies",
        "brand": "Grandma's Bakery",
        "image_url": "/static/test_samples/sample_missing_fssai_fat.jpg",
        "description": "States 'FSSAI Approved' without valid 14-digit license number; completely omits mandatory Saturated Fat and Trans Fat rows in nutrition table.",
        "sample_ocr_text": """GRANDMA's BAKERY
RICH BUTTER COOKIES
Baked with Love & Traditional Goodness
FSSAI License: FSSAI Approved [MISSING 14-DIGIT NUMBER]
Batch No: GB-77 | Mfg Date: 20/08/2026
Best Before: 6 Months from packaging
Net Weight: 150g | MRP: Rs. 50.00
INGREDIENTS:
Refined Wheat Flour (Maida), Butter (18%), Sugar, Hydrogenated Vegetable Fat, Milk Solids, Invert Syrup, Raising Agents [INS 500(ii), INS 503(ii)].
ALLERGEN ADVICE: Contains Wheat (Gluten) and Milk.
NUTRITIONAL FACTS (Per 100g):
Energy: 490.0 kcal
Protein: 6.5 g
Total Carbohydrates: 65.0 g
Total Sugars: 24.0 g
Total Fat: 22.0 g
Sodium: 180 mg
Manufactured by: Grandma Bakery Confectionery, Pune - 411001
Customer Helpline: support@grandmabakery.in""",
        "expected_violations": [
            "Missing 14-digit FSSAI License Number (FSSAI Labelling 2020 Clause 5(1))",
            "Missing Saturated Fat and Trans Fat declarations (FSSAI Labelling 2020 Clause 5(3)(b))"
        ]
    },
    {
        "id": "case-misleading-natural",
        "title": "Case 4: Mango Drink (Misleading '100% Pure & Natural' Claim)",
        "product_name": "Royal Mango Delight",
        "brand": "Royal Agro Beverages",
        "image_url": "/static/test_samples/sample_misleading_natural.jpg",
        "description": "Markets beverage as '100% Pure & Natural' while ingredients contain synthetic food colour (INS 110 Sunset Yellow) and chemical preservative (INS 211).",
        "sample_ocr_text": """ROYAL MANGO DELIGHT
100% PURE & NATURAL MANGO DRINK
Farm Fresh Alphonso • 100% Natural Guarantee
FSSAI Lic. No. 10017011003456
Batch No: RM-882 | Mfg Date: 12/09/2026
Best Before: 6 Months from packaging
Net Quantity: 250 ml | MRP: Rs. 35.00 (Incl. of all taxes)
INGREDIENTS:
Water, Mango Pulp (19%), Sugar, Acidity Regulator (INS 330), Synthetic Food Colour (INS 110 Sunset Yellow), Class II Preservative (INS 211 Sodium Benzoate), Added Flavours.
NUTRITION FACTS (Per 100 ml):
Energy: 62.0 kcal
Protein: 0.1 g
Total Carbohydrates: 15.5 g
Total Sugars: 15.0 g
Added Sugars: 12.0 g
Total Fat: 0.0 g
Saturated Fat: 0.0 g
Trans Fat: 0.0 g
Sodium: 12 mg
Royal Agro Beverages Ltd, Ratnagiri, Maharashtra - 415612
Feedback Helpline: info@royalbeverages.in""",
        "expected_violations": [
            "Misleading '100% Pure & Natural' claim (prohibited under FSSAI Advertising & Claims 2018 when chemical additives/colours are added)"
        ]
    },
    {
        "id": "case-bilingual-compliant",
        "title": "Case 5: Traditional Namkeen / Bhujia (Fully Compliant)",
        "product_name": "पारंपरिक बेसन भुजिया (Besan Bhujia)",
        "brand": "बीकानेर स्वाद (Bikaner Swad)",
        "image_url": "/static/test_samples/sample_bilingual_compliant.jpg",
        "description": "Benchmark compliant bilingual (Hindi & English) packaging: valid FSSAI license, statutory green dot, date markings, allergen advice, and complete nutrition panel.",
        "sample_ocr_text": """बीकानेर स्वाद • BIKANER SWAD
पारंपरिक बेसन भुजिया • BESAN BHUJIA
100% शाकाहारी नमकीन / Traditional Vegetarian Snack
FSSAI Lic. No. 10020011000452
Batch No: BS-AUG-44 | Mfg Date: 15/08/2026
Best Before: 4 Months from manufacture
Net Weight: 200g | MRP: Rs. 65.00 (Inclusive of all taxes)
सामग्री / INGREDIENTS:
चना बेसन (Bengal Gram Flour 48%), खाद्य वनस्पति तेल (Edible Vegetable Oil), आयोडीन युक्त नमक (Iodized Salt), लाल मिर्च पाउडर (Red Chilli), काली मिर्च, हींग।
ALLERGEN ADVICE: Contains Gluten. May contain traces of peanut and sesame.
NUTRITIONAL FACTS (प्रति 100 ग्राम / Per 100g):
Energy (ऊर्जा): 560.0 kcal
Protein (प्रोटीन): 13.5 g
Total Carbohydrates (कार्बोहाइड्रेट): 42.0 g
Total Sugars (कुल शर्करा): 1.2 g
Added Sugars (अतिरिक्त चीनी): 0.0 g
Total Fat (कुल वसा): 38.0 g
Saturated Fat (संतृप्त वसा): 14.5 g
Trans Fat (ट्रांस वसा): 0.1 g
Sodium (सोडियम): 680 mg
Manufactured by: Bikaner Swad Foods Pvt Ltd, Bikaner, Rajasthan - 334001
Consumer Helpline: care@bikanerswad.com | Phone: +91-11-23456789""",
        "expected_violations": []
    },
    {
        "id": "case-real-lays-chips",
        "title": "Case 6: Lay's India's Magic Masala (Real Packaging Back Panel)",
        "product_name": "Lay's Potato Chips - Magic Masala",
        "brand": "PepsiCo India Holdings",
        "image_url": "/static/uploads/f36860e5-26f3-45c6-b0aa-9bdaffd1d491/image_1.png",
        "description": "User-uploaded back panel photograph of real Lay's chips showing 14-digit license, green dot, and two-column nutrition facts with 0.1g trans fat.",
        "sample_ocr_text": """Lay's India's Magic Masala Potato Chips
100% Vegetarian [Green Dot]
FSSAI Lic. No. 10014064000435
Proprietary Food - Potato Chips
Ingredients: Potato (52%), Edible Vegetable Oil (Palmolein), Seasoning (Spices and Condiments, Iodized Salt, Sugar, Black Salt, Acidity Regulator 330).
Nutritional Information Per 100 g:
Energy: 537 kcal
Protein: 6.8 g
Carbohydrate: 53.0 g
Total Sugars: 4.0 g
Total Fat: 33.1 g
Saturated Fat: 12.5 g
Trans Fat: 0.1 g
Sodium: 877 mg
Customer Care: consumer.feedback@pepsico.com | 1800-22-4020""",
        "expected_violations": []
    }
]

@router.get("", response_model=List[Dict[str, Any]])
def get_showcase_test_cases():
    """Returns curated showcase test cases with ground-truth packaging scenarios"""
    return SHOWCASE_CASES

@router.get("/{case_id}", response_model=Dict[str, Any])
def get_single_test_case(case_id: str):
    """Retrieves a single showcase test case by ID"""
    for c in SHOWCASE_CASES:
        if c["id"] == case_id:
            return c
    return SHOWCASE_CASES[0]
