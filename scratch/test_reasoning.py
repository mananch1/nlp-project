import sys
import io
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.schemas import StructuredProductData, NutritionFacts
from backend.app.services.reasoning_service import answer_product_doubt

data = StructuredProductData(
    product_name="Lay's India's Magic Masala",
    brand="Lay's",
    ingredients=[
        "Potato",
        "Edible Vegetable Oil (Palmolein, Rice Bran Oil)",
        "Seasoning (Sugar, Maltodextrin, Salt, Black Salt, Spices, Acidity Regulators INS 330, INS 296, INS 334, Anticaking Agent INS 551, Paprika Extract INS 160c)"
    ],
    nutrition=NutritionFacts(
        energy_kcal=537.0,
        protein_g=6.8,
        carbohydrates_g=52.9,
        total_sugars_g=2.5,
        added_sugars_g=0.2,
        total_fat_g=33.1,
        saturated_fat_g=12.5,
        trans_fat_g=0.1,
        sodium_mg=993.0
    ),
    fssai_license="10014064000435",
    veg_nonveg="VEG"
)

test_queries = [
    "bahi mujhe bata yeh acidity ke liya acche he kya?",
    "क्या इसमें कोई हानिकारक प्रिजर्वेटिव या एडिटिव्स हैं?",
    "Is the trans-fat and saturated fat within legal limits?",
    "Does this product have hidden added sugars?",
    "Can kids eat this snack?",
    "Namak kitna hai?"
]

print("=" * 70)
q = test_queries[0]
print("QUERY:", q)
resp, is_viol, item, clauses = answer_product_doubt(q, data, [])
print("RESPONSE:\n" + resp)
print("CLAUSES RETRIEVED:", [c["section"] + ": " + c["title"] for c in clauses[:2]])
