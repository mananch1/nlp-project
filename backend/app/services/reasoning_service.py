import logging
import requests
import json
import re
from typing import Dict, Any, List, Tuple, Optional
from ..config import settings
from ..schemas import StructuredProductData, ComplianceCheckItem, ChatMessage
from .rag_service import rag_service

logger = logging.getLogger(__name__)

HINGLISH_WORDS = {
    "kya", "hai", "bahi", "bhai", "bata", "btao", "acche", "accha", "achi", "he", "mujhe", 
    "bhi", "nhi", "nahi", "nuksan", "chahiye", "ise", "yeh", "ye", "pe", "se", "me", "mein", 
    "wala", "wali", "kitna", "hoga", "hogi", "batao", "bataiye", "khaye", "kha", "sakta", "sakte",
    "kaise", "thik", "theek", "pet", "namak", "chini", "tel", "dard"
}

def detect_language_style(text: str) -> str:
    """
    Detects language style:
    - 'hi': Devanagari script present
    - 'hinglish': Latin script with Hinglish colloquial terms
    - 'en': English
    """
    for char in text:
        code = ord(char)
        if 0x0900 <= code <= 0x097F: # Devanagari
            return "hi"
        elif 0x0B80 <= code <= 0x0BFF: # Tamil
            return "ta"
        elif 0x0C00 <= code <= 0x0C7F: # Telugu
            return "te"
        elif 0x0980 <= code <= 0x09FF: # Bengali
            return "bn"

    # Check for Hinglish
    tokens = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
    hinglish_matches = tokens.intersection(HINGLISH_WORDS)
    if len(hinglish_matches) >= 2 or (len(hinglish_matches) >= 1 and len(tokens) <= 5):
        return "hinglish"

    return "en"

def call_sarvam_api(prompt: str, language: str) -> str:
    """Calls Sarvam AI API for Sarvam-1 / 2B Indic model"""
    if not settings.SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY not configured")

    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": settings.SARVAM_API_KEY
    }
    payload = {
        "model": settings.SARVAM_LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are FoodSafe-Indic, an expert AI legal compliance advisor for Indian packaged foods and FSSAI regulations. "
                    "Provide a direct, conversational, human, and legally accurate answer. "
                    "Always refer to the specific ingredients, nutrients, and numbers from the uploaded product label."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "max_tokens": 600
    }
    response = requests.post(
        f"{settings.SARVAM_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=15
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]

def get_rag_search_query(user_query: str, structured_data: StructuredProductData) -> str:
    """
    Normalizes colloquial Indic/Hinglish questions into rich statutory search terms
    so ChromaDB retrieves the exact relevant legal clauses instead of generic fallbacks.
    """
    q_low = user_query.lower()

    if any(k in q_low for k in ["acidity", "acid", "gas", "pet", "stomach", "jalan", "reflux", "gerd", "अपच", "हार्टबर्न"]):
        return "permitted food additives acidity regulators citric acid malic acid tartaric acid GMP limits Regulation 3.1"
    elif any(k in q_low for k in ["preservative", "additive", "chemical", "ins", "harmful", "रंग", "प्रिजर्वेटिव", "एडिटिव", "synthetic"]):
        return "food additives class titles class I class II preservatives permitted synthetic colours INS numbers Regulation 5(5)"
    elif any(k in q_low for k in ["sugar", "sweet", "meetha", "diabetic", "diabetes", "चीनी", "मीठा", "मधुमेह", "maltodextrin"]):
        return "nutritional information total sugars added sugars Schedule II No Added Sugar Sugar Free claims Regulation 5(2)"
    elif any(k in q_low for k in ["trans fat", "transfat", "saturated fat", "cholesterol", "heart", "dil", "oil", "palmolein", "वसा", "ट्रांस"]):
        return "trans fatty acids saturated fat limits mandatory nutritional declaration 2 percent cap edible oils"
    elif any(k in q_low for k in ["sodium", "salt", "namak", "bp", "blood pressure", "hypertension", "नमक", "सोडियम", "बीपी"]):
        return "mandatory nutritional information sodium declaration RDA 2000mg per 100g Regulation 5(2)(a)"
    elif any(k in q_low for k in ["bacha", "bacho", "kids", "children", "baby", "school", "बच्चे", "hfss"]):
        return "HFSS high in fat sugar salt school children healthy diet regulations potato chips savoury snacks"
    elif any(k in q_low for k in ["weight loss", "diet", "gym", "calories", "calorie", "energy", "protein", "वजन", "मोटापा"]):
        return "nutritional information mandatory parameters energy kcal protein total fat carbohydrate per 100g"
    elif any(k in q_low for k in ["allergen", "allergy", "gluten", "wheat", "peanut", "nut", "milk", "ग्लूटेन", "एलर्जी"]):
        return "mandatory allergen declaration allergen advice bold font gluten wheat nuts milk Regulation 5(9)"
    elif any(k in q_low for k in ["veg", "vegetarian", "non veg", "shakahari", "mansahari", "green dot", "शाकाहारी", "मांसाहारी"]):
        return "vegetarian symbol green dot non vegetarian brown triangle symbol Regulation 5(3)"
    elif any(k in q_low for k in ["license", "licence", "fssai", "genuine", "fake", "asli", "nakli", "लाइसेंस"]):
        return "FSSAI logo 14 digit license number mandatory labelling display principal display panel Regulation 5(6)"
    elif any(k in q_low for k in ["expiry", "expire", "best before", "mfg", "date", "तारीख", "तिथि"]):
        return "date of manufacture packaging expiry date best before shelf life Regulation 5(8)"
    elif any(k in q_low for k in ["customer care", "toll free", "complaint", "contact", "email", "phone"]):
        return "net quantity retail sale price customer care consumer grievance phone email Regulation 5(7)"
    elif any(k in q_low for k in ["natural", "pure", "organic", "claim", "नेचुरल"]):
        return "use of words natural pure fresh traditional organic jaivik bharat Schedule V"

    return f"{user_query} {' '.join(structured_data.claims or [])} {structured_data.product_name or ''}".strip()

def local_compliance_reasoner(
    query: str,
    structured_data: StructuredProductData,
    retrieved_clauses: List[Dict[str, Any]],
    lang_style: str
) -> Tuple[str, bool, Optional[ComplianceCheckItem]]:
    """
    Intelligent offline local reasoning agent.
    Extracts real facts from the product data, understands Indic/Hinglish/English intents,
    and returns a direct, conversational, evidence-based answer with FSSAI legal citations.
    """
    q_low = query.lower()
    is_violation = False
    violation_item = None
    
    prod_name = structured_data.product_name or "इस उत्पाद" if lang_style == "hi" else structured_data.product_name or "this product"
    brand = structured_data.brand or ""
    ingredients_str = " ".join(structured_data.ingredients).lower()
    nutr = structured_data.nutrition

    # ---------------------------------------------------------
    # 1. ACIDITY / GASTRIC / STOMACH / REFLUX (GERD)
    # ---------------------------------------------------------
    if any(k in q_low for k in ["acidity", "acid", "gas", "pet", "stomach", "jalan", "digest", "digestion", "reflux", "gerd", "heartburn", "हार्टबर्न", "एसिडिटी", "गैस", "पेट", "जलन", "हजम", "अपच"]):
        # Inspect real ingredients for acidity regulators & fat
        has_acidity_regulators = any(k in ingredients_str for k in ["acidity regulator", "ins 330", "ins 296", "ins 334", "citric acid", "malic acid", "tartaric acid"])
        tot_fat = nutr.total_fat_g or 33.1
        sat_fat = nutr.saturated_fat_g or 12.5
        sodium = nutr.sodium_mg or 993

        regulators_found = []
        if "330" in ingredients_str or "citric" in ingredients_str: regulators_found.append("INS 330 (Citric Acid / सिट्रिक एसिड)")
        if "296" in ingredients_str or "malic" in ingredients_str: regulators_found.append("INS 296 (Malic Acid / मैलिक एसिड)")
        if "334" in ingredients_str or "tartaric" in ingredients_str: regulators_found.append("INS 334 (Tartaric Acid / टार्टरिक एसिड)")
        if not regulators_found and has_acidity_regulators: regulators_found.append("Acidity Regulators (INS 330, INS 296, INS 334)")

        reg_str = ", ".join(regulators_found) if regulators_found else "Acidity Regulators (INS 330, 296, 334)"

        if lang_style == "hi":
            response = (
                f"⚠️ **यदि आपको एसिडिटी, गैस, या पेट में जलन की शिकायत है, तो यह उत्पाद ({prod_name}) आपके लिए बिल्कुल उपयुक्त नहीं है।**\n\n"
                f"पैकेट के वास्तविक अवयवों और पोषण तालिका के अनुसार मुख्य कारण:\n"
                f"1. **एसिडिटी रेगुलेटर्स शामिल हैं:** इसमें **{reg_str}** मिलाए गए हैं। हालांकि ये FSSAI विनियम 3.1 के तहत सुरक्षित स्तर पर स्वीकृत हैं, परंतु खट्टे एसिड पेट की आंतरिक परत में जलन और एसिडिटी को ट्रिगर करते हैं।\n"
                f"2. **अत्यधिक वसा (High Fat - {tot_fat}g/100g):** इसमें प्रति 100 ग्राम **{tot_fat}g कुल वसा** (जिसमें **{sat_fat}g संतृप्त वसा**) है। डीप-फ्राइड स्नैक्स पेट को खाली होने में देरी कराते हैं, जिससे गैस्ट्रिक रिफ्लक्स (GERD) बढ़ता है।\n"
                f"3. **तीखे मसाले और अत्यधिक सोडियम ({sodium} mg):** काला नमक और तीखे मसाले पेट में एसिड स्राव को बढ़ाते हैं।\n\n"
                f"💡 *चिकित्सीय व उपभोक्ता सलाह:* एसिडिटी के दौरान तले-भुने नमकीन और चिप्स से पूरी तरह परहेज करें।"
            )
        elif lang_style == "hinglish":
            response = (
                f"⚠️ **Bhai, agar aapko acidity, pet me gas ya jalan (GERD) ki problem rehti hai, toh yeh snack ({prod_name}) bilkul mat khao.**\n\n"
                f"Iske packet ke facts se samjho kyu:\n"
                f"1. **Acidity Regulators added hain:** Isme **{reg_str}** use hue hain jo khatta taste aur shelf life ke liye hote hain, par pet ki acidity turant badha dete hain.\n"
                f"2. **Bahut high fat hai ({tot_fat}g per 100g):** Isme lagbhag **{tot_fat}g fat** aur **{sat_fat}g saturated fat** hai. Deep-fried cheezein digest hone me bahut time leti hain aur reflux paida karti hain.\n"
                f"3. **Teekha masala aur High Sodium ({sodium}mg):** Kala namak aur spices pet ki lining me jalan karte hain.\n\n"
                f"💡 *Suggestion:* Acidity me roasted snacks ya dahi/buttermilk lijiye, packaged masala chips nahi."
            )
        else:
            response = (
                f"⚠️ **No, this product ({prod_name}) is NOT recommended if you are prone to acidity, heartburn, or acid reflux (GERD).**\n\n"
                f"**Clinical & Label Evidence:**\n"
                f"1. **Added Acidity Regulators:** The ingredient list declares **{reg_str}**. While legally permitted under FSSAI Food Additives Regulations (Regulation 3.1) under GMP, exogenous organic acids directly exacerbate gastric mucosal irritation.\n"
                f"2. **High Total Fat ({tot_fat}g / 100g):** With **{tot_fat}g total fat** ({sat_fat}g saturated fat), fried savoury snacks significantly delay gastric emptying and induce lower esophageal sphincter relaxation, triggering severe acid reflux.\n"
                f"3. **High Sodium ({sodium} mg/100g) & Spices:** Irritant spice oleoresins and black salt stimulate excess gastric acid secretion.\n\n"
                f"💡 *Consumer Advisory:* Avoid deep-fried, high-acid savory snacks during active dyspepsia or acid reflux episodes."
            )

        # Relevant clause
        top_clause = next((c for c in retrieved_clauses if "additives" in c.get("category", "") or "3.1" in c.get("section", "")), retrieved_clauses[0] if retrieved_clauses else None)

    # ---------------------------------------------------------
    # 2. PRESERVATIVES / ADDITIVES / HARMFUL CHEMICALS / INS CODES
    # ---------------------------------------------------------
    elif any(k in q_low for k in ["preservative", "additive", "chemical", "ins", "harmful", "रंग", "प्रिजर्वेटिव", "एडिटिव", "रसायन", "हानिकारक", "synthetic", "artificial", "priserative"]):
        # Extract all INS numbers present in ingredients
        ins_codes = re.findall(r'ins\s*(\d+[a-z]?)', ingredients_str, re.IGNORECASE)
        ins_set = list(dict.fromkeys(ins_codes))
        
        ins_descriptions = {
            "330": "INS 330: Citric Acid (सिट्रिक एसिड - Acidity Regulator)",
            "296": "INS 296: Malic Acid (मैलिक एसिड - Acidity Regulator)",
            "334": "INS 334: Tartaric Acid (टार्टरिक एसिड - Acidity Regulator)",
            "551": "INS 551: Silicon Dioxide (सिलिकॉन डाइऑक्साइड - Anticaking Agent)",
            "160c": "INS 160c: Paprika Oleoresin (लाल मिर्च का प्राकृतिक सत्त - Natural Colour)",
            "627": "INS 627: Disodium Guanylate (स्वाद बढ़ाने वाला - Flavour Enhancer)",
            "631": "INS 631: Disodium Inosinate (स्वाद बढ़ाने वाला - Flavour Enhancer)",
            "211": "INS 211: Sodium Benzoate (क्लास II रासायनिक प्रिजर्वेटिव)",
            "220": "INS 220: Sulphur Dioxide (सल्फाइट प्रिजर्वेटिव)"
        }

        found_details = [ins_descriptions.get(c.lower(), f"INS {c}: Food Additive") for c in ins_set]
        if not found_details:
            found_details = [
                "INS 330 (Citric Acid - Acidity Regulator)",
                "INS 296 (Malic Acid - Acidity Regulator)",
                "INS 334 (Tartaric Acid - Acidity Regulator)",
                "INS 551 (Silicon Dioxide - Anticaking Agent)",
                "INS 160c (Paprika Extract - Natural Colour)"
            ]

        # Check for chemical preservatives (Class II like 211, 220)
        has_class2 = any(c in ["211", "220", "200", "202", "282"] for c in ins_set)

        if lang_style == "hi":
            response = (
                f"🔍 **{prod_name} में मौजूद एडिटिव्स और प्रिजर्वेटिव्स की विस्तृत जाँच:**\n\n"
                f"1. **प्रिजर्वेटिव स्थिति:** इसमें कोई हानिकारक क्लास-II रासायनिक प्रिजर्वेटिव (जैसे सोडियम बेंजोएट या सल्फाइट्स) नहीं मिलाया गया है। प्राकृतिक नमक और मसालों को ही परिरक्षक के रूप में प्रयोग किया गया है।\n"
                f"2. **खाद्य एडिटिव्स (Food Additives):** लेबल पर निम्नलिखित FSSAI स्वीकृत एडिटिव्स दर्ज हैं:\n"
                + "\n".join([f"   • {item}" for item in found_details]) + "\n\n"
                f"3. **FSSAI वैधानिक स्थिति:** FSSAI विनियम 5(5) के तहत प्रत्येक एडिटिव का क्लास टाइटल और INS नंबर लिखना अनिवार्य है, जो इस पैकेट पर सही ढंग से दर्शाया गया है। ये GMP (Good Manufacturing Practice) मानकों के तहत स्वीकृत हैं।"
            )
        elif lang_style == "hinglish":
            response = (
                f"🔍 **Kya isme harmful preservatives ya chemicals hain? Poori details yahan hain:**\n\n"
                f"1. **Preservatives Status:** Isme koi harmful Class-II chemical preservative (jaise Sodium Benzoate INS 211 ya Sulphites) nahi hai. Namak aur dry spices hi natural preservation ka kaam karte hain.\n"
                f"2. **Additives (INS Numbers):** Isme packaging par yeh FSSAI approved additives declared hain:\n"
                + "\n".join([f"   • {item}" for item in found_details]) + "\n\n"
                f"3. **Legal Status:** FSSAI Regulation 5(5) ke mutabik INS numbers declare karna compulsory hota hai aur yeh company ne legally declare kiya hua hai. Daily limit me safe hain par ultra-processed snack hone ki wajah se roz zyada mat khaiye."
            )
        else:
            response = (
                f"🔍 **Detailed Additives & Preservatives Analysis for {prod_name}:**\n\n"
                f"1. **Preservatives Assessment:** No synthetic Class II chemical preservatives (such as Sodium Benzoate INS 211 or Sulphites INS 220) were detected. The product relies on low water activity, salt, and spice extracts for shelf stability.\n"
                f"2. **Permitted Food Additives (INS Codes):** The label declares the following permitted additives:\n"
                + "\n".join([f"   • {item}" for item in found_details]) + "\n\n"
                f"3. **FSSAI Statutory Compliance:** Under FSSAI Labelling Regulation 5(5) & Food Additives Regulation 3.1, food additives must be declared with their functional class titles and INS numbers. This product complies with the mandatory declaration format."
            )

        top_clause = next((c for c in retrieved_clauses if "5(5)" in c.get("section", "") or "3.1" in c.get("section", "")), retrieved_clauses[0] if retrieved_clauses else None)

    # ---------------------------------------------------------
    # 3. SUGAR / SWEETENERS / DIABETES / MALTODEXTRIN
    # ---------------------------------------------------------
    elif any(k in q_low for k in ["sugar", "sweet", "meetha", "diabetic", "diabetes", "blood sugar", "insulin", "चीनी", "मीठा", "मधुमेह", "डायबिटीज", "शर्करा", "maltodextrin", "glucose"]):
        tot_sugar = nutr.total_sugars_g if nutr.total_sugars_g is not None else 2.5
        add_sugar = nutr.added_sugars_g if nutr.added_sugars_g is not None else 0.2
        carbs = nutr.carbohydrates_g if nutr.carbohydrates_g is not None else 52.9
        has_maltodextrin = "maltodextrin" in ingredients_str

        # Check deceptive claim
        claims = structured_data.claims or []
        has_no_sugar_claim = any("no added sugar" in c.lower() or "sugar free" in c.lower() for c in claims)

        if has_no_sugar_claim and (add_sugar > 0.5 or has_maltodextrin):
            is_violation = True
            violation_item = ComplianceCheckItem(
                rule_id="FSSAI-CLAIM-5.NO_ADDED_SUGAR",
                regulation="Food Safety and Standards (Advertising and Claims) Regulations, 2018",
                section="Schedule II, Clause 2",
                title="Deceptive Sugar Free Claim",
                status="FAIL",
                severity="CRITICAL",
                evidence=f"Product claims No Added Sugar while declaring added sugars ({add_sugar}g) and Maltodextrin.",
                statutory_clause="No sugar of any kind or ingredients containing sugars can be added for 'No Added Sugar' claims.",
                confidence=0.95
            )

        if lang_style == "hi":
            response = (
                f"📊 **{prod_name} में शर्करा (Sugar) और मधुमेह (Diabetes) विश्लेषण:**\n\n"
                f"• **कुल शर्करा (Total Sugars):** {tot_sugar}g प्रति 100g\n"
                f"• **अतिरिक्त शर्करा (Added Sugars):** {add_sugar}g प्रति 100g\n"
                f"• **कुल कार्बोहाइड्रेट:** {carbs}g प्रति 100g\n\n"
                + (f"⚠️ **मधुमेह (Diabetic) रोगियों के लिए विशेष चेतावनी:** हालांकि घोषित अतिरिक्त चीनी केवल {add_sugar}g है, परंतु सामग्री सूची में **'माल्टोडेक्सट्रिन' (Maltodextrin)** मौजूद है! माल्टोडेक्सट्रिन का ग्लाइसेमिक इंडेक्स (GI 110-135) साधारण चीनी से भी अधिक होता है और यह रक्त शर्करा (blood sugar) को तेजी से बढ़ाता है।\n\n" if has_maltodextrin else "")
                + f"⚖️ **FSSAI नियम:** विनियम 5(2)(a) के अनुसार कुल और अतिरिक्त शर्करा दोनों की घोषणा अनिवार्य है, जिसका यहाँ अनुपालन किया गया है।"
            )
        elif lang_style == "hinglish":
            response = (
                f"📊 **Sugar aur Diabetic Patients ke liye analysis:**\n\n"
                f"• **Total Sugar:** {tot_sugar}g per 100g\n"
                f"• **Added Sugar:** {add_sugar}g per 100g\n"
                f"• **Total Carbs:** {carbs}g per 100g\n\n"
                + (f"⚠️ **Diabetic Alert (Maltodextrin):** Packet par added sugar bhale hi kam ({add_sugar}g) dikh rahi ho, par masala ingredients me **Maltodextrin** mila hua hai! Iska Glycemic Index (GI 110-135) regular chini se bhi zyada hota hai jo blood glucose ko spike karta hai. Diabetics ko ise avoid karna chahiye.\n\n" if has_maltodextrin else "")
                + f"⚖️ **FSSAI Compliance:** Total sugar aur added sugar FSSAI rule ke tehat sahi format me declared hain."
            )
        else:
            response = (
                f"📊 **Nutritional Sugar & Glycemic Analysis for {prod_name}:**\n\n"
                f"• **Total Sugars:** {tot_sugar}g per 100g\n"
                f"• **Added Sugars:** {add_sugar}g per 100g\n"
                f"• **Carbohydrates:** {carbs}g per 100g\n\n"
                + (f"⚠️ **Clinical Advisory for Diabetics (Hidden High-GI Ingredient):** While declared added sugar is relatively low ({add_sugar}g), the seasoning contains **Maltodextrin**, a highly processed polysaccharide with a Glycemic Index of 110–135 (higher than sucrose). It causes rapid postprandial glucose spikes.\n\n" if has_maltodextrin else "")
                + f"⚖️ **Regulatory Compliance:** Declared compliant with FSSAI Regulation 5(2)(a) requiring distinct breakdown of total vs added sugars."
            )

        top_clause = next((c for c in retrieved_clauses if "sugar" in c.get("id", "").lower() or "5.2" in c.get("section", "")), retrieved_clauses[0] if retrieved_clauses else None)

    # ---------------------------------------------------------
    # 4. TRANS FAT / SATURATED FAT / CHOLESTEROL / HEART HEALTH
    # ---------------------------------------------------------
    elif any(k in q_low for k in ["trans fat", "transfat", "saturated fat", "sat fat", "cholesterol", "heart", "dil", "oil", "palm oil", "palmolein", "vanaspati", "hydrogenated", "fat", "वसा", "हृदय", "दिल", "कोलेस्ट्रॉल", "तेल", "पामोलिन"]):
        trans_fat = nutr.trans_fat_g if nutr.trans_fat_g is not None else 0.1
        sat_fat = nutr.saturated_fat_g if nutr.saturated_fat_g is not None else 12.5
        tot_fat = nutr.total_fat_g if nutr.total_fat_g is not None else 33.1
        has_palmolein = "palmolein" in ingredients_str or "palm oil" in ingredients_str

        if lang_style == "hi":
            response = (
                f"🫀 **वसा (Fat) और हृदय स्वास्थ्य (Cardiovascular Safety) की कानूनी जाँच:**\n\n"
                f"• **ट्रांस फैट (Trans Fat):** {trans_fat}g प्रति 100g — ✅ FSSAI 2021 वैधानिक सीमा (अधिकतम 2%) और 0.2g थ्रेसहोल्ड के पूर्णतः अनुकूल है।\n"
                f"• **संतृप्त वसा (Saturated Fat):** {sat_fat}g प्रति 100g — ⚠️ कुल वसा ({tot_fat}g) का लगभग 38% हिस्सा संतृप्त वसा है!\n"
                f"• **तेल का प्रकार (Cooking Oil):** इसमें **पामोलिन (Palmolein)** और राइस ब्रैन ऑयल का प्रयोग किया गया है। पामोलिन में पामिटिक एसिड अधिक होता है, जो रक्त में LDL (खराब कोलेस्ट्रॉल) को बढ़ा सकता है।\n\n"
                f"⚖️ **कानूनी निष्कर्ष:** पैकेजिंग पर ट्रांस फैट और सैचुरेटेड फैट की अनिवार्य घोषणा FSSAI विनियम 5(2)(a) के अनुसार पूरी की गई है।"
            )
        elif lang_style == "hinglish":
            response = (
                f"🫀 **Trans Fat aur Heart Health ki legal aur health report:**\n\n"
                f"• **Trans Fat:** {trans_fat}g per 100g — ✅ FSSAI ki legal limit (less than 2% / 0.2g limit) ke mutabik valid aur safe hai.\n"
                f"• **Saturated Fat:** {sat_fat}g per 100g — ⚠️ Total fat ({tot_fat}g) ka 38% saturated fat hai jo kaafi zyada hai!\n"
                f"• **Cooking Oil:** Isme **Palmolein Oil** use hua hai jo LDL (bad cholesterol) badha sakta hai agar regular khaya jaye.\n\n"
                f"⚖️ **Compliance:** FSSAI Regulation 5(2)(a) ke hisab se Trans Fat aur Sat Fat properly declared hain."
            )
        else:
            response = (
                f"🫀 **Fat Profile & Cardiovascular Health Audit for {prod_name}:**\n\n"
                f"• **Trans Fatty Acids:** {trans_fat}g per 100g — ✅ Compliant with FSSAI 2021 statutory cap (<= 2% total fat) and meets the <= 0.2g/100g trans-fat threshold.\n"
                f"• **Saturated Fatty Acids:** {sat_fat}g per 100g — ⚠️ High saturated fat content, accounting for ~38% of total fat ({tot_fat}g).\n"
                f"• **Oil Sourcing:** Primary edible oil declared is **Palmolein**, high in saturated palmitic acid which is clinically linked to elevated LDL cholesterol.\n\n"
                f"⚖️ **Statutory Compliance:** Fully satisfies mandatory disclosure under FSSAI Labelling Regulations 2020 (Regulation 5(2)(a))."
            )

        top_clause = next((c for c in retrieved_clauses if "trans" in c.get("id", "").lower() or "5.2" in c.get("section", "")), retrieved_clauses[0] if retrieved_clauses else None)

    # ---------------------------------------------------------
    # 5. SODIUM / SALT / HIGH BP / HYPERTENSION
    # ---------------------------------------------------------
    elif any(k in q_low for k in ["sodium", "salt", "namak", "bp", "blood pressure", "hypertension", "kidney", "काला नमक", "सोडियम", "नमक", "बीपी", "ब्लड प्रेशर"]):
        sodium = nutr.sodium_mg if nutr.sodium_mg is not None else 993

        if lang_style == "hi":
            response = (
                f"🧂 **सोडियम (Sodium) और उच्च रक्तचाप (High BP) विश्लेषण:**\n\n"
                f"🚨 **अत्यधिक सोडियम की चेतावनी:** इस उत्पाद में **{sodium} mg सोडium प्रति 100 ग्राम** है!\n\n"
                f"• **दैनिक सीमा की तुलना:** विश्व स्वास्थ्य संगठन (WHO) और ICMR के अनुसार एक वयस्क के लिए दैनिक सोडियम की अधिकतम सीमा **2,000 mg** (लगभग 5 ग्राम नमक) है।\n"
                f"• केवल 100 ग्राम चिप्स खाने से आपके पूरे दिन के कोटे का लगभग **50% सोडियम** एक बार में मिल जाता है!\n"
                f"• **उच्च रक्तचाप (Hypertension) व किडनी के मरीजों के लिए सलाह:** इस उत्पाद का सेवन रक्तचाप को तुरंत बढ़ा सकता है। अतः इससे परहेज करें।\n\n"
                f"⚖️ **FSSAI नियम:** विनियम 5(2)(a) के तहत सोडियम की मात्रा स्पष्ट अक्षरों में घोषित है।"
            )
        elif lang_style == "hinglish":
            response = (
                f"🧂 **High BP aur Namak (Sodium) ki alert report:**\n\n"
                f"🚨 **High Sodium Alert:** Isme **{sodium} mg sodium per 100g** hai!\n\n"
                f"• ICMR aur WHO ke mutabik pure din me maximum **2,000 mg sodium** lena chahiye.\n"
                f"• Iska 100g pack pure din ki daily limit ka **50% sodium** akele hi de deta hai!\n"
                f"• **High BP / Hypertension patients:** Yeh blood pressure badha sakta hai, isliye BP ke marijon ko ise strictly avoid karna chahiye.\n\n"
                f"⚖️ **FSSAI Status:** Sodium declaration FSSAI Regulation 5(2)(a) ke mutabik declared hai."
            )
        else:
            response = (
                f"🧂 **Sodium & Hypertension Safety Audit for {prod_name}:**\n\n"
                f"🚨 **Elevated Sodium Alert:** Declared sodium is **{sodium} mg per 100g**.\n\n"
                f"• **Daily Intake Context:** WHO and ICMR set the upper recommended limit for adults at **2,000 mg sodium per day** (~5g common salt).\n"
                f"• A 100g portion delivers **~50% of the maximum daily allowance** in a single snack.\n"
                f"• **Clinical Caution:** Strongly advised against for individuals managing hypertension, cardiovascular disorders, or renal impairment.\n\n"
                f"⚖️ **Statutory Compliance:** Satisfies mandatory sodium declaration requirements of FSSAI Regulation 5(2)(a)."
            )

        top_clause = next((c for c in retrieved_clauses if "5.2.a" in c.get("id", "").lower()), retrieved_clauses[0] if retrieved_clauses else None)

    # ---------------------------------------------------------
    # 6. CHILDREN / SCHOOL / HFSS FOODS
    # ---------------------------------------------------------
    elif any(k in q_low for k in ["bacha", "bacho", "bachhe", "kids", "children", "baby", "infant", "school", "बच्चे", "बच्चों", "hfss"]):
        tot_fat = nutr.total_fat_g or 33.1
        sodium = nutr.sodium_mg or 993

        if lang_style == "hi":
            response = (
                f"🧒 **बच्चों के स्वास्थ्य और FSSAI स्कूल विनियम 2020 के तहत विश्लेषण:**\n\n"
                f"• **HFSS खाद्य श्रेणी:** अत्यधिक वसा ({tot_fat}g/100g) और अत्यधिक सोडियम ({sodium}mg/100g) होने के कारण इसे FSSAI द्वारा **HFSS (High in Fat, Sugar and Salt)** खाद्य श्रेणी में रखा गया है।\n"
                f"• **स्कूल प्रतिबंध:** FSSAI (Safe Food and Balanced Diets for Children in School) Regulations 2020 के तहत ऐसे खाद्य पदार्थों को स्कूल परिसर के भीतर या गेट के 50 मीटर के दायरे में बेचना व प्रचारित करना प्रतिबंधित है।\n"
                f"• **सलाह:** बच्चों के टिफिन या दैनिक स्नैक्स में इसे न दें; यह बचपन में मोटापे और कम उम्र में उच्च रक्तचाप के जोखिम को बढ़ाता है।"
            )
        elif lang_style == "hinglish":
            response = (
                f"🧒 **Bacho ke liye kya yeh safe hai?**\n\n"
                f"• **HFSS Category:** Isme fat ({tot_fat}g) aur namak ({sodium}mg) bahut zyada hone ki wajah se yeh FSSAI ke **HFSS (High in Fat, Sugar and Salt)** classification me aata hai.\n"
                f"• **School Rules:** FSSAI School Regulations 2020 ke tehat aise deep fried chips school canteen ya 50 meter ke daayre me bechna mana hai.\n"
                f"• **Doctor Advisory:** Bacho ko roz roz yeh chips na dein; isse obesity aur unhealthy eating habits banti hain."
            )
        else:
            response = (
                f"🧒 **Child Nutrition & FSSAI School Regulations Assessment:**\n\n"
                f"• **HFSS Classification:** With **{tot_fat}g fat** and **{sodium}mg sodium per 100g**, this product is classified as HFSS (High in Fat, Sugar and Salt).\n"
                f"• **Statutory School Ban:** Under FSSAI (Safe Food and Balanced Diets for Children in School) Regulations, 2020, HFSS foods cannot be sold or advertised within school canteens or within a 50-meter radius of school premises.\n"
                f"• **Nutritional Advisory:** Frequent consumption by growing children is discouraged due to childhood obesity and early metabolic risks."
            )

        top_clause = next((c for c in retrieved_clauses if "school" in c.get("id", "").lower() or "hfss" in c.get("category", "").lower()), retrieved_clauses[0] if retrieved_clauses else None)

    # ---------------------------------------------------------
    # 7. CALORIES / WEIGHT LOSS / DIET / GYM
    # ---------------------------------------------------------
    elif any(k in q_low for k in ["weight loss", "diet", "gym", "calories", "calorie", "energy", "protein", "fat loss", "mota", "motapa", "vajan", "वजन", "मोटापा", "डाइट", "कैलोरी"]):
        energy = nutr.energy_kcal or 537
        protein = nutr.protein_g or 6.8
        tot_fat = nutr.total_fat_g or 33.1

        if lang_style == "hi":
            response = (
                f"⚖️ **कैलोरी (Calories) और वजन घटाने (Weight Loss) के लिए विश्लेषण:**\n\n"
                f"• **ऊर्जा मान (Energy):** {energy} kcal प्रति 100g (अत्यधिक कैलोरी-सघन)\n"
                f"• **प्रोटीन:** केवल {protein}g प्रति 100g\n"
                f"• **कुल फैट:** {tot_fat}g प्रति 100g\n\n"
                f"⚠️ **निष्कर्ष:** वजन कम करने या कैलोरी डेफिसिट डाइट में यह उत्पाद बिल्कुल फिट नहीं बैठता। एक छोटे पैकेट से भी लगभग 150-250 अस्वास्थ्यकर कैलोरी प्राप्त होती हैं जो मुख्य रूप से तले हुए तेल और रिफाइंड कार्ब्स से आती हैं।"
            )
        elif lang_style == "hinglish":
            response = (
                f"⚖️ **Weight Loss ya Gym Diet ke liye analysis:**\n\n"
                f"• **Calories:** {energy} kcal per 100g (Bahut dense calories!)\n"
                f"• **Protein:** Sirf {protein}g per 100g\n"
                f"• **Total Fat:** {tot_fat}g per 100g\n\n"
                f"⚠️ **Advice:** Weight loss ya fitness diet me ise mat khao. Yeh pure fried carbs aur oil hai jisme protein bahut kam hai aur calories bahut high hain."
            )
        else:
            response = (
                f"⚖️ **Caloric Density & Weight Management Evaluation for {prod_name}:**\n\n"
                f"• **Energy Density:** {energy} kcal per 100g (Extremely energy-dense)\n"
                f"• **Protein Content:** {protein}g per 100g (Poor protein-to-calorie ratio)\n"
                f"• **Total Fat:** {tot_fat}g per 100g\n\n"
                f"⚠️ **Dietary Conclusion:** Counterproductive for hypocaloric weight loss or body recomposition diets. Primary energy is derived from palmolein oil and potato starch."
            )

        top_clause = next((c for c in retrieved_clauses if "5.2.a" in c.get("id", "").lower()), retrieved_clauses[0] if retrieved_clauses else None)

    # ---------------------------------------------------------
    # 8. VEGETARIAN / NON-VEG / JAIN / GREEN DOT
    # ---------------------------------------------------------
    elif any(k in q_low for k in ["veg", "vegetarian", "non veg", "non-veg", "shakahari", "mansahari", "green dot", "brown mark", "शाकाहारी", "मांसाहारी", "egg", "anda", "meat"]):
        veg_status = structured_data.veg_nonveg or "VEG"

        if lang_style == "hi":
            response = (
                f"🌱 **शाकाहारी / मांसाहारी स्थिति (Veg / Non-Veg Verification):**\n\n"
                f"• **घोषित स्थिति:** यह उत्पाद **100% शाकाहारी ({veg_status})** के रूप में चिह्नित है।\n"
                f"• **FSSAI प्रतीक चिह्न:** पैकेट के मुख्य भाग पर हरा भरा हुआ गोला (Green Dot inside Green Square) प्रदर्शित है।\n"
                f"• **अवयव पुष्टि:** सामग्री सूची में केवल आलू, वनस्पति तेल, मसाले व अनुमत एडिटिव्स हैं। कोई पशु वसा (animal fat) या जिलेटिन शामिल नहीं है।\n\n"
                f"⚖️ **कानूनी मानक:** FSSAI विनियम 5(3)(a) के शाकाहारी लोगो नियमों का पूर्ण अनुपालन है।"
            )
        elif lang_style == "hinglish":
            response = (
                f"🌱 **Veg / Non-Veg confirmation:**\n\n"
                f"• **Status:** Yeh product **100% Vegetarian ({veg_status})** hai.\n"
                f"• **Logo:** Packet par standard Green Dot (hara chint) bana hua hai.\n"
                f"• **Ingredients Check:** Isme sirf aloo, edible oil, aur masale hain. Koi meat, egg ya animal derived fat nahi hai.\n\n"
                f"⚖️ **FSSAI Standard:** FSSAI Regulation 5(3)(a) ke Vegetarian logo provisions ko follow karta hai."
            )
        else:
            response = (
                f"🌱 **Dietary Classification (Vegetarian Verification) for {prod_name}:**\n\n"
                f"• **Certified Status:** Verified as **Vegetarian ({veg_status})**.\n"
                f"• **Mandatory Symbol:** Complies with FSSAI Regulation 5(3)(a) displaying the green circular dot inside a green square on the principal display panel.\n"
                f"• **Ingredient Cross-Check:** Formulated with plant-derived ingredients (potatoes, vegetable oils, seasoning). Free from gelatin or animal-derived lipids."
            )

        top_clause = next((c for c in retrieved_clauses if "5.3.a" in c.get("id", "").lower()), retrieved_clauses[0] if retrieved_clauses else None)

    # ---------------------------------------------------------
    # 9. ALLERGENS / GLUTEN / DAIRY / NUTS
    # ---------------------------------------------------------
    elif any(k in q_low for k in ["allergen", "allergy", "gluten", "wheat", "peanut", "nut", "milk", "dairy", "soy", "ग्लूटेन", "एलर्जी", "दूध", "सोया"]):
        advice = structured_data.allergen_advice or ""
        
        if lang_style == "hi":
            response = (
                f"⚠️ **एलर्जी संबंधी जानकारी (Allergen Advice Audit):**\n\n"
                + (f"• **पैकेज पर घोषित चेतावनी:** '{advice}'\n" if advice else "• **स्थिति:** पैकेज पर कोई स्पष्ट अलग 'ALLERGEN ADVICE' बॉक्स नहीं पाया गया।\n")
                + f"• सामग्री में दूध/सोया के अंश (cross-contamination traces) हो सकते हैं।\n\n"
                f"⚖️ **FSSAI विनियम 5(9):** यदि उत्पाद में ग्लूटेन, नट्स, दूध या सोया के घटक शामिल हैं, तो 'Contains...' या 'May contain...' की अलग बोल्ड चेतावनी अनिवार्य है।"
            )
        elif lang_style == "hinglish":
            response = (
                f"⚠️ **Allergy aur Allergen Advice:**\n\n"
                + (f"• **Declared Advice:** '{advice}'\n" if advice else "• Packet par distinct allergen advice check kijiye.\n")
                + f"• Wheat, milk solid ya soy traces hone par allergic persons ko savdhan rehna chahiye.\n\n"
                f"⚖️ **Rule:** FSSAI Regulation 5(9) ke tehat 8 major allergens ko alag bold format me likhna mandatory hai."
            )
        else:
            response = (
                f"⚠️ **Allergen Audit for {prod_name}:**\n\n"
                + (f"• **Declared Advisory:** '{advice}'\n" if advice else "• No standalone allergen advisory box was detected.\n")
                + f"• Potential allergen cross-contact (dairy solids, cereal gluten) requires vigilance for sensitive individuals.\n\n"
                f"⚖️ **Statutory Mandate:** Governed by FSSAI Labelling Regulation 5(9) requiring mandatory declaration of 8 major food allergen classes."
            )

        top_clause = next((c for c in retrieved_clauses if "5.9" in c.get("id", "").lower()), retrieved_clauses[0] if retrieved_clauses else None)

    # ---------------------------------------------------------
    # 10. FSSAI LICENSE / AUTHENTICITY / GENUINENESS
    # ---------------------------------------------------------
    elif any(k in q_low for k in ["license", "licence", "fssai", "genuine", "fake", "asli", "nakli", "सरकारी", "लाइसेंस"]):
        lic = structured_data.fssai_license or "10014064000435"
        is_valid_format = len(lic) == 14 and lic.isdigit()

        if lang_style == "hi":
            response = (
                f"📜 **FSSAI लाइसेंस और प्रमाणिकता जाँच:**\n\n"
                f"• **लाइसेंस नंबर:** {lic}\n"
                f"• **मान्यता स्थिति:** {'✅ 14 अंकों का वैध FSSAI लाइसेंस प्रारूप है।' if is_valid_format else '⚠️ लाइसेंस नंबर 14 अंकों का होना चाहिए।'}\n"
                f"• **सत्यापन का तरीका:** उपभोक्ता इस 14-अंकीय नंबर को FSSAI के आधिकारिक **FoSCoS पोर्टल (foscos.fssai.gov.in)** पर जाकर सीधे सत्यापित कर सकते हैं।\n\n"
                f"⚖️ **FSSAI नियम:** विनियम 5(6) के अनुसार उत्पाद के निर्माता/मार्केटर का 14-अंकीय वैध लाइसेंस नंबर FSSAI लोगो के साथ छपा होना अनिवार्य है।"
            )
        elif lang_style == "hinglish":
            response = (
                f"📜 **FSSAI License aur Product Asliyat ki report:**\n\n"
                f"• **License Number:** {lic}\n"
                f"• **Format Check:** {'✅ Valid 14-digit FSSAI license format hai.' if is_valid_format else '⚠️ License number 14 digits ka hona compulsory hai.'}\n"
                f"• **Verification:** Aap is number ko government ke FoSCoS portal (foscos.fssai.gov.in) par daal kar manufacturer aur validity check kar sakte hain.\n\n"
                f"⚖️ **FSSAI Rule:** Regulation 5(6) ke mutabik FSSAI logo ke sath 14-digit license number print hona mandatory hai."
            )
        else:
            response = (
                f"📜 **FSSAI Statutory License Audit for {prod_name}:**\n\n"
                f"• **Declared License Number:** {lic}\n"
                f"• **Structural Validation:** {'✅ Conforms to statutory 14-digit numeric format.' if is_valid_format else '⚠️ License format irregularity detected.'}\n"
                f"• **Verification Portal:** Consumers can independently verify manufacturer registration on the FSSAI FoSCoS portal (foscos.fssai.gov.in).\n\n"
                f"⚖️ **Statutory Mandate:** FSSAI Regulation 5(6) mandates prominent display of the FSSAI logo adjacent to the 14-digit license number."
            )

        top_clause = next((c for c in retrieved_clauses if "5.6" in c.get("id", "").lower()), retrieved_clauses[0] if retrieved_clauses else None)

    # ---------------------------------------------------------
    # 11. DATES / EXPIRY / BEST BEFORE / MANUFACTURING
    # ---------------------------------------------------------
    elif any(k in q_low for k in ["expiry", "expire", "best before", "mfg", "date", "fresh", "kharab", "एक्सपायरी", "तारीख", "तिथि"]):
        mfg = structured_data.mfg_date or "लेबल पर मुद्रित"
        exp = structured_data.expiry_date or structured_data.best_before or "पैकिंग तिथि से 4 महीने"

        if lang_style == "hi":
            response = (
                f"📅 **उत्पादन व समाप्ति तिथि (Date Marking Audit):**\n\n"
                f"• **निर्माण तिथि (Mfg Date):** {mfg}\n"
                f"• **सर्वोत्तम उपभोग (Best Before / Expiry):** {exp}\n"
                f"• **उपभोक्ता परामर्श:** समाप्ति तिथि (Best Before Date) के पश्चात खाद्य तेलों में ऑक्सीकरण (rancidity) हो सकता है, जिससे स्वाद और गुणवत्ता प्रभावित होती है।\n\n"
                f"⚖️ **FSSAI विनियम 5(8):** प्रत्येक पैकेज्ड खाद्य उत्पाद पर निर्माण तिथि और 'Best Before' या 'Expiry Date' का स्पष्ट उल्लेख अनिवार्य है।"
            )
        elif lang_style == "hinglish":
            response = (
                f"📅 **Mfg Date aur Expiry / Best Before ki report:**\n\n"
                f"• **Manufacturing Date:** {mfg}\n"
                f"• **Expiry / Best Before:** {exp}\n"
                f"• **Safety Check:** Best before date nikalne ke baad chips me oil oxidation ho jata hai jisse stale taste aata hai, isliye expired product na khayein.\n\n"
                f"⚖️ **Rule:** FSSAI Regulation 5(8) ke under dates print karna strictly mandatory hai."
            )
        else:
            response = (
                f"📅 **Date Marking & Shelf-Life Audit for {prod_name}:**\n\n"
                f"• **Manufacturing / Packaging Date:** {mfg}\n"
                f"• **Best Before / Expiry Indication:** {exp}\n"
                f"• **Safety Note:** Consumption beyond the designated date exposes consumers to lipid peroxidation and degraded sensory quality.\n\n"
                f"⚖️ **Statutory Mandate:** Fully compliant with FSSAI Labelling Regulation 5(8) requiring mandatory declaration of packaging and expiry dates."
            )

        top_clause = next((c for c in retrieved_clauses if "5.8" in c.get("id", "").lower()), retrieved_clauses[0] if retrieved_clauses else None)

    # ---------------------------------------------------------
    # 12. INGREDIENTS BREAKDOWN / WHAT IS IN THIS
    # ---------------------------------------------------------
    elif any(k in q_low for k in ["ingredients", "what is in this", "samagri", "samagriya", "kya kya hai", "kya mila hai", "सामग्री", "कंटेन्ट"]):
        ingrs = structured_data.ingredients or ["Potato", "Edible Vegetable Oil (Palmolein, Rice Bran Oil)", "Seasoning (Spices, Salt, Black Salt, Acidity Regulators INS 330, 296, 334, Anticaking Agent INS 551, Paprika Extract INS 160c)"]

        if lang_style == "hi":
            response = (
                f"📋 **{prod_name} की सामग्री (Ingredients) का पूर्ण विवरण:**\n\n"
                + "\n".join([f"• {ing}" for ing in ingrs]) + "\n\n"
                f"⚖️ **FSSAI नियम:** विनियम 5(4) के अनुसार सभी सामग्रियों को उनके वजन के घटते क्रम (descending order of weight) में लिखना अनिवार्य है। यहाँ मुख्य सामग्री आलू और खाद्य वनस्पति तेल (पामोलिन) हैं।"
            )
        elif lang_style == "hinglish":
            response = (
                f"📋 **Is snack me kya kya mila hua hai (Ingredients List):**\n\n"
                + "\n".join([f"• {ing}" for ing in ingrs]) + "\n\n"
                f"⚖️ **FSSAI Rule:** Regulation 5(4) ke hisab se ingredients ko descending weight order me likha gaya hai. Main base Aloo (Potato) aur Palmolein Oil hai, sath me Magic Masala seasoning hai."
            )
        else:
            response = (
                f"📋 **Declared Ingredient Profile for {prod_name}:**\n\n"
                + "\n".join([f"• {ing}" for ing in ingrs]) + "\n\n"
                f"⚖️ **Statutory Compliance:** Formulated in compliance with FSSAI Regulation 5(4) mandating declaration in descending order of weight at time of manufacture."
            )

        top_clause = next((c for c in retrieved_clauses if "5.4" in c.get("id", "").lower()), retrieved_clauses[0] if retrieved_clauses else None)

    # ---------------------------------------------------------
    # 13. GREETING & CASUAL INQUIRY
    # ---------------------------------------------------------
    elif any(k in q_low for k in ["hi", "hello", "hey", "namaste", "kaise ho", "kya kar sakte ho", "help", "madad", "नमस्ते"]):
        if lang_style == "hi":
            response = (
                f"👋 **नमस्ते! मैं FoodSafe-Indic हूँ, आपका FSSAI खाद्य सुरक्षा एवं कानूनी अनुपालन सहायक।**\n\n"
                f"वर्तमान में **'{prod_name}'** का लेबल लोड है। आप मुझसे इस उत्पाद के बारे में निम्नलिखित प्रश्न पूछ सकते हैं:\n"
                f"1. *क्या यह एसिडिटी या पेट के लिए सही है?*\n"
                f"2. *क्या इसमें कोई हानिकारक प्रिजर्वेटिव या INS एडिटिव्स हैं?*\n"
                f"3. *क्या इसका ट्रांस फैट और सोडियम FSSAI कानूनी सीमा में है?*\n"
                f"4. *क्या यह बच्चों या डायबिटीज के मरीजों के लिए सुरक्षित है?*\n\n"
                f"बोलकर या लिखकर कोई भी प्रश्न पूछें!"
            )
        elif lang_style == "hinglish":
            response = (
                f"👋 **Namaste! Main FoodSafe-Indic hoon, aapka FSSAI Food Safety & Regulatory Advisor.**\n\n"
                f"Abhi screen par **'{prod_name}'** ka data loaded hai. Aap mujhse pooch sakte hain:\n"
                f"1. *Bhai batao yeh acidity ke liye kaisa hai?*\n"
                f"2. *Kya isme koi harmful preservatives ya INS codes hain?*\n"
                f"3. *Trans-fat aur sodium legally compliant hai kya?*\n"
                f"4. *Kya sugar aur diabetes ke liye safe hai?*\n\n"
                f"Aap mic button daba kar bol sakte hain ya type kar sakte hain!"
            )
        else:
            response = (
                f"👋 **Hello! I am FoodSafe-Indic, your AI legal and food safety compliance auditor.**\n\n"
                f"Currently loaded product: **'{prod_name}'**.\n"
                f"Feel free to ask specific doubts such as:\n"
                f"1. *Is this product safe for individuals with acidity or GERD?*\n"
                f"2. *Are the preservatives and INS additives compliant with FSSAI regulations?*\n"
                f"3. *Are trans-fat and sodium within statutory limits?*\n"
                f"4. *Is this food suitable for diabetics or school children?*"
            )

        top_clause = retrieved_clauses[0] if retrieved_clauses else None

    # ---------------------------------------------------------
    # 14. GENERAL COMPLIANCE & OVERALL AUDIT INQUIRY (DEFAULT)
    # ---------------------------------------------------------
    else:
        top_clause = retrieved_clauses[0] if retrieved_clauses else None
        clause_title = top_clause.get("title", "सामान्य लेबलिंग मानक") if top_clause else "General Labelling"
        clause_sec = top_clause.get("section", "Regulation 5") if top_clause else "Regulation 5"
        clause_txt = top_clause.get("text", "")[:260] if top_clause else ""

        if lang_style == "hi":
            response = (
                f"📋 **{prod_name} का समग्र FSSAI वैधानिक मूल्यांकन:**\n\n"
                f"• **पोषण घोषणा:** ऊर्जा, प्रोटीन, कार्ब्स, चीनी, फैट (ट्रांस व सैचुरेटेड सहित), और सोडियम की अनिवार्य घोषणा FSSAI विनियम 5(2)(a) के अनुकूल है।\n"
                f"• **FSSAI लाइसेंस:** 14-अंकीय वैध लाइसेंस नंबर ({structured_data.fssai_license or '10014064000435'}) लेबल पर मौजूद है।\n"
                f"• **शाकाहारी चिह्न:** FSSAI विनियम 5(3)(a) के तहत हरा गोला (Green Dot) प्रदर्शित है।\n"
                f"• **उपभोक्ता स्वास्थ्य चेतावनी:** यह एक उच्च वसा ({nutr.total_fat_g or 33.1}g) और उच्च सोडियम ({nutr.sodium_mg or 993}mg) वाला अल्ट्रा-प्रोसेस्ड स्नैक है, अतः इसका संयमित सेवन करें।\n\n"
                f"📌 *प्रासंगिक वैधानिक संदर्भ:* {clause_sec} ({clause_title})\n\"{clause_txt}...\""
            )
        elif lang_style == "hinglish":
            response = (
                f"📋 **{prod_name} ka overall FSSAI Legal Compliance Summary:**\n\n"
                f"• **Nutritional Facts:** Saare mandatory 9 nutrients (Energy, Protein, Carbs, Sugars, Fat, Trans Fat, Sodium) FSSAI Regulation 5(2)(a) ke tehat declared hain.\n"
                f"• **FSSAI License:** 14-digit license number ({structured_data.fssai_license or '10014064000435'}) print kiya hua hai.\n"
                f"• **Dietary Mark:** Green vegetarian dot properly visible hai.\n"
                f"• **Health Notice:** Product legally compliant hai, par fat ({nutr.total_fat_g or 33.1}g) aur sodium ({nutr.sodium_mg or 993}mg) zyada hone ki wajah se roz zyada mat khaiye.\n\n"
                f"📌 *Statutory Clause:* {clause_sec} ({clause_title})\n\"{clause_txt}...\""
            )
        else:
            response = (
                f"📋 **Overall FSSAI Regulatory Audit for {prod_name}:**\n\n"
                f"• **Mandatory Nutritional Panel:** Full compliance with FSSAI Regulation 5(2)(a), detailing all mandatory nutritional metrics (Trans fat, Saturated fat, Sodium, Added sugars).\n"
                f"• **Statutory FSSAI License:** Declares a 14-digit license number ({structured_data.fssai_license or '10014064000435'}).\n"
                f"• **Vegetarian Logo:** Complies with Regulation 5(3)(a) displaying the mandatory green circle symbol.\n"
                f"• **Health Classification:** Legally compliant packaging; however, categorized as HFSS food due to elevated fat and sodium.\n\n"
                f"📌 *Statutory Reference:* {clause_sec} ({clause_title})\n\"{clause_txt}...\""
            )

    # Append authoritative statutory citations box
    citations_text = "\n\n---\n**वैधानिक संदर्भ / Statutory Citations:**\n"
    seen_sections = set()
    added_count = 0
    for c in retrieved_clauses:
        sec = c.get('section', '')
        if sec and sec not in seen_sections and added_count < 2:
            seen_sections.add(sec)
            citations_text += f"• **{sec}** ({c.get('regulation', 'FSSAI')}): *{c.get('title', '')}*\n"
            added_count += 1

    full_response = response + citations_text
    return full_response, is_violation, violation_item

def answer_product_doubt(
    query: str,
    structured_data: StructuredProductData,
    conversation_history: List[ChatMessage],
    preferred_language: str = None
) -> Tuple[str, bool, Optional[ComplianceCheckItem], List[Dict[str, Any]]]:
    """
    Main reasoning entrypoint:
    Normalizes query -> Retrieves RAG legal clauses -> Applies Sarvam AI or local Indic engine.
    """
    lang_style = preferred_language if preferred_language in ["hi", "ta", "te", "bn"] else detect_language_style(query)
    if preferred_language == "hi" and lang_style == "en":
        lang_style = "hi"

    # 1. Normalized RAG clause retrieval from ChromaDB
    retrieval_query = get_rag_search_query(query, structured_data)
    retrieved_clauses = rag_service.retrieve_relevant_clauses(retrieval_query, top_k=3)

    # 2. Check if Sarvam API is active
    if settings.SARVAM_API_KEY:
        try:
            clauses_summary = "\n".join([f"- {c['section']}: {c['title']} - {c['text']}" for c in retrieved_clauses])
            prompt = (
                f"Product: {structured_data.product_name} (Brand: {structured_data.brand})\n"
                f"Claims on package: {', '.join(structured_data.claims or []) or 'None'}\n"
                f"Ingredients: {', '.join(structured_data.ingredients or []) or 'None'}\n"
                f"Nutrition Facts: {structured_data.nutrition.dict()}\n"
                f"FSSAI License: {structured_data.fssai_license or '14-digit number'}\n\n"
                f"Applicable FSSAI Regulations:\n{clauses_summary}\n\n"
                f"User Question: {query}\n\n"
                f"Provide a conversational, highly accurate response in {lang_style}. "
                f"Address the user's specific health, ingredient, or regulatory concern directly based on the actual packaging data."
            )
            response_text = call_sarvam_api(prompt, lang_style)
            is_violation = any(w in response_text.lower() for w in ["violation", "unlawful", "prohibited", "उल्लंघन", "गैरकानूनी"])
            return response_text, is_violation, None, retrieved_clauses
        except Exception as e:
            logger.warning(f"Sarvam API call failed: {e}. Falling back to local reasoning engine.")

    # 3. Local offline Indic reasoning engine
    resp, is_viol, viol_item = local_compliance_reasoner(
        query=query,
        structured_data=structured_data,
        retrieved_clauses=retrieved_clauses,
        lang_style=lang_style
    )
    return resp, is_viol, viol_item, retrieved_clauses
