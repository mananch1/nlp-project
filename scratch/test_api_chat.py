import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

payload = {
    'session_id': 'test_sess',
    'query': 'bahi mujhe bata yeh acidity ke liya acche he kya?',
    'language': 'hi',
    'structured_data': {
        'product_name': "Lay's India's Magic Masala",
        'brand': "Lay's",
        'ingredients': [
            "Potato",
            "Edible Vegetable Oil (Palmolein, Rice Bran Oil)",
            "Seasoning (Sugar, Maltodextrin, Salt, Black Salt, Spices, Acidity Regulators INS 330, INS 296, INS 334, Anticaking Agent INS 551, Paprika Extract INS 160c)"
        ],
        'nutrition': {
            'energy_kcal': 537.0,
            'protein_g': 6.8,
            'carbohydrates_g': 52.9,
            'total_sugars_g': 2.5,
            'added_sugars_g': 0.2,
            'total_fat_g': 33.1,
            'saturated_fat_g': 12.5,
            'trans_fat_g': 0.1,
            'sodium_mg': 993.0
        },
        'fssai_license': '10014064000435',
        'veg_nonveg': 'VEG'
    },
    'conversation_history': []
}

test_queries = [
    ("bahi mujhe bata yeh acidity ke liya acche he kya?", "en"),
    ("क्या इसमें कोई हानिकारक प्रिजर्वेटिव या एडिटिव्स हैं?", "hi"),
    ("Does this product have hidden added sugars?", "en"),
    ("Is trans fat and saturated fat within legal limits?", "en")
]

for q, lang in test_queries:
    payload['query'] = q
    payload['language'] = lang
    r = requests.post('http://localhost:8000/api/chat/message', json=payload)
    print("=" * 60)
    print(f"QUERY: {q} (lang={lang})")
    print("RESPONSE:\n" + r.json().get('response', '')[:250] + "...\n")

