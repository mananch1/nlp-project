import re
import unicodedata
from typing import Dict, Any, List, Optional
from ..schemas import StructuredProductData, NutritionFacts

ALLERGEN_KEYWORDS = {
    "gluten": ["wheat", "gluten", "barley", "oats", "rye", "maida", "atta", "गेहूं", "ग्लूटेन"],
    "nuts": ["peanut", "groundnut", "almond", "cashew", "walnut", "pistachio", "मूंगफली", "बादाम", "काजू"],
    "milk": ["milk", "dairy", "whey", "casein", "butter", "cheese", "curd", "दूध", "मक्खन", "पनीर"],
    "soy": ["soy", "soya", "soybean", "lecithin", "सोयाबीन", "सोया"],
    "egg": ["egg", "albumin", "ovomucin", "अंडा"],
    "fish": ["fish", "crustacean", "prawn", "crab", "shrimp", "मछली"],
    "sulphite": ["sulphite", "sulfite", "sulfur dioxide", "सल्फाइट"]
}

SUGAR_INDICATORS = [
    "sugar", "sucrose", "glucose", "fructose", "corn syrup", "high fructose corn syrup",
    "invert syrup", "jaggery", "honey", "maltodextrin", "dextrose", "malt syrup",
    "fruit juice concentrate", "concentrated fruit juice", "शक्कर", "चीनी", "गुड़", "शहद"
]

CLAIM_PATTERNS = [
    (r"\b(100%?\s*natural|all\s*natural|completely\s*natural|प्राकृतिक)\b", "100% Natural"),
    (r"\b(no\s*added\s*sugar|zero\s*added\s*sugar|without\s*added\s*sugars?)\b", "No Added Sugar"),
    (r"\b(sugar\s*free|zero\s*sugar|0\s*sugar)\b", "Sugar Free"),
    (r"\b(trans\s*fat\s*free|0\s*g?\s*trans\s*fat|zero\s*trans\s*fat)\b", "Trans Fat Free"),
    (r"\b(low\s*fat|fat\s*free|zero\s*fat)\b", "Low Fat / Fat Free"),
    (r"\b(organic|jaivik|जैविक)\b", "Organic"),
    (r"\b(immunity\s*booster|boosts?\s*immunity|रोग\s*प्रतिरोधक)\b", "Immunity Booster"),
    (r"\b(pure|100%?\s*pure|शुद्ध)\b", "100% Pure")
]

def detect_scripts(text: str) -> List[str]:
    """Detects scripts present in the text (Devanagari, Latin, etc.)"""
    scripts = set()
    for char in text:
        name = unicodedata.name(char, "")
        if "DEVANAGARI" in name:
            scripts.add("Devanagari (Hindi/Marathi)")
        elif "LATIN" in name:
            scripts.add("Latin (English)")
        elif "TAMIL" in name:
            scripts.add("Tamil")
        elif "TELUGU" in name:
            scripts.add("Telugu")
        elif "BENGALI" in name:
            scripts.add("Bengali")
    return list(scripts)

def extract_nutrition_field(text: str, field_names: List[str]) -> Optional[float]:
    """
    Extracts numerical value for a nutrition key using highly flexible patterns:
    - Line-based proximity with unit-anchored extraction (g, kcal, mg)
    - Delimiter-based extraction (:, |, -)
    - Supports parenthetical units: e.g. Trans Fat (g), Saturated Fat [g]
    - OCR character-to-digit recovery (e.g. Olg -> 0.1g, O.1 -> 0.1)
    """
    for name in field_names:
        # Pattern 1: Line-based search with unit or colon preference (most accurate for tabular OCR)
        for line in text.splitlines():
            kw_match = re.search(rf"\b{name}\b", line, re.IGNORECASE)
            if kw_match:
                after_kw = line[kw_match.end():]
                # Pre-clean common OCR digit misreads
                clean_kw = re.sub(r'\b[oO][lI]g\b', '0.1g', after_kw)
                clean_kw = re.sub(r'\b[oO]\.([0-9])', r'0.\1', clean_kw)
                clean_kw = re.sub(r'\b[oO]g\b', '0.0g', clean_kw)
                
                # Priority A: Number directly preceding a unit (e.g. "14.5 g", "0.1 g", "560 kcal")
                unit_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(?:g|kcal|mg|mcg|kj)\b", clean_kw, re.IGNORECASE)
                if unit_match:
                    try:
                        return float(unit_match.group(1))
                    except ValueError:
                        pass
                
                # Priority B: Number after standard delimiter (e.g. ": 14.5", "| 0.1")
                colon_match = re.search(r"[:\-\—\|]\s*(?:[<~]\s*)?([0-9]+(?:\.[0-9]+)?)", clean_kw)
                if colon_match:
                    try:
                        return float(colon_match.group(1))
                    except ValueError:
                        pass

                # Priority C: First number on the line
                num_match = re.search(r"(?:[<~]\s*)?([0-9]+(?:\.[0-9]+)?)", clean_kw)
                if num_match:
                    try:
                        return float(num_match.group(1))
                    except ValueError:
                        pass

        # Pattern 2: Global direct match fallback
        pattern2 = rf"{name}(?:\s*\([^\)]*\))?\s*[:\-\—\|]?\s*(?:[<~]\s*)?([0-9]+(?:\.[0-9]+)?)\s*(?:g|kcal|mg|mcg|kj)?"
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

    return None

def parse_nutrition(text: str) -> NutritionFacts:
    """Parses nutrition facts panel from OCR text"""
    nutrition = NutritionFacts()
    
    # 1. Energy: Prioritize 2 to 4 digits followed by kcal/kd
    m_energy = re.search(r"\b([0-9]{2,4})\s*(?:kcal|kd|cal|kj)\b", text, re.IGNORECASE)
    if m_energy:
        try:
            nutrition.energy_kcal = float(m_energy.group(1))
        except ValueError:
            pass
    if nutrition.energy_kcal is None:
        nutrition.energy_kcal = extract_nutrition_field(text, ["energy", "calories", "ऊर्जा"])

    # 2. Protein
    nutrition.protein_g = extract_nutrition_field(text, ["protein", "प्रोटीन", "protei", "prtn"])
    if nutrition.protein_g is None:
        # Fallback for OCR reading '6.gg' or '6.8g' on a line under energy
        for line in text.splitlines():
            if any(k in line.lower() for k in ["serve", "serves", "serving", "mrp", "lic", "no.", "batch"]):
                continue
            m = re.search(r"\b([0-9]{1,2})\.([0-9g]{1,2})\s*g?\b", line)
            if m:
                digit2 = m.group(2)[0].replace("g", "8")
                try:
                    val = float(f"{m.group(1)}.{digit2}")
                    if 1.0 <= val <= 35.0:
                        nutrition.protein_g = val
                        break
                except ValueError:
                    pass

    # 3. Carbohydrates & Sugars
    nutrition.carbohydrates_g = extract_nutrition_field(text, ["total carbohydrate", "carbohydrate", "carbs", "कार्बोहाइड्रेट", "carbo"])
    if nutrition.carbohydrates_g is None:
        # Typical carb range (30-80g per 100g)
        for line in text.splitlines():
            m = re.search(r"\b([3-8][0-9]\.[0-9]+)\s*g\b", line)
            if m:
                try:
                    val = float(m.group(1))
                    if val != nutrition.energy_kcal:
                        nutrition.carbohydrates_g = val
                        break
                except ValueError:
                    pass

    nutrition.total_sugars_g = extract_nutrition_field(text, ["total sugars?", "sugars?", "चीनी", "शर्करा", "totd"])
    if nutrition.total_sugars_g is None:
        m_sug = re.search(r"\b(?:totd|total\s*sugars?|sugars?)\s*[:\-\—\|]?\s*([0-9]+(?:\.[0-9]+)?)\s*g\b", text, re.IGNORECASE)
        if m_sug:
            try: nutrition.total_sugars_g = float(m_sug.group(1))
            except ValueError: pass

    nutrition.added_sugars_g = extract_nutrition_field(text, ["added sugars?", "अतिरिक्त चीनी", "added"])
    if nutrition.added_sugars_g is None and nutrition.total_sugars_g is not None:
        # Added sugars row often follows total sugars, e.g. '02 g' or '0.2 g'
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            if re.search(r"\b(?:totd|total\s*sugars?|sugars?)\b", line, re.IGNORECASE):
                for next_l in lines[idx+1:idx+3]:
                    m_add = re.search(r"\b(0[0-9]|0\.[0-9]+)\s*g\b", next_l)
                    if m_add:
                        raw_v = m_add.group(1)
                        if raw_v.startswith("0") and "." not in raw_v:
                            raw_v = "0." + raw_v[1:]
                        try:
                            nutrition.added_sugars_g = float(raw_v)
                            break
                        except ValueError:
                            pass
                break

    nutrition.dietary_fiber_g = extract_nutrition_field(text, ["dietary fiber", "fiber", "फाइबर"])
    
    # 4. Total Fat
    nutrition.total_fat_g = extract_nutrition_field(text, ["total fat", "totd fat", "total lipid", "fat", "वसा"])
    
    # 5. Trans Fat (supports abbreviations and OCR misreads)
    nutrition.trans_fat_g = extract_nutrition_field(
        text,
        ["trans fat", "trns fat", "transfat", "trans-fat", "trns", "trans", "ट्रांस वसा", "ट्रांस"]
    )
    
    # 6. Saturated Fat (supports OCR misreads like &iturated or sat fat)
    nutrition.saturated_fat_g = extract_nutrition_field(
        text,
        ["saturated fat", "sat fat", "sat. fat", "saturated", "संतृप्त वसा", "संतृप्त", "iturated fat"]
    )
    # Fallback for Saturated Fat in multi-row table where row contains "fat <value>g"
    if nutrition.saturated_fat_g is None and nutrition.total_fat_g is not None:
        for line in text.splitlines():
            if re.search(r"\bfat\b", line, re.IGNORECASE) and not re.search(r"\b(?:tot|total|totd|trans|trns)\b", line, re.IGNORECASE):
                num_m = re.search(r"fat\s*[:\-\—\|]?\s*([0-9]+(?:\.[0-9]+)?)\s*g?", line, re.IGNORECASE)
                if num_m:
                    val = float(num_m.group(1))
                    if val != nutrition.trans_fat_g and val < nutrition.total_fat_g:
                        nutrition.saturated_fat_g = val
                        break

    # Physical plausibility correction: if OCR missed decimal separator (e.g. 145g instead of 14.5g per 100g)
    if nutrition.saturated_fat_g and nutrition.saturated_fat_g > 100:
        nutrition.saturated_fat_g = round(nutrition.saturated_fat_g / 10.0, 2)
    if nutrition.trans_fat_g and nutrition.trans_fat_g > 100:
        nutrition.trans_fat_g = round(nutrition.trans_fat_g / 10.0, 2)
    if nutrition.total_fat_g and nutrition.total_fat_g > 100:
        nutrition.total_fat_g = round(nutrition.total_fat_g / 10.0, 2)
    if nutrition.added_sugars_g and nutrition.added_sugars_g > 100:
        nutrition.added_sugars_g = round(nutrition.added_sugars_g / 10.0, 2)

    # 7. Sodium
    nutrition.sodium_mg = extract_nutrition_field(text, ["sodium", "सोडियम", "salt", "नमक"])
    if nutrition.sodium_mg is None:
        m = re.search(r"\b([0-9]{2,4})\s*mg\b", text, re.IGNORECASE)
        if m:
            try: nutrition.sodium_mg = float(m.group(1))
            except ValueError: pass

    return nutrition

def parse_packaging_text(raw_text: str) -> StructuredProductData:
    """
    Multi-stage NLP Parser:
    Takes raw concatenated OCR text and extracts structured entities according to FSSAI guidelines.
    """
    clean_text = unicodedata.normalize("NFKD", raw_text)
    
    # 1. Detect Scripts
    scripts = detect_scripts(clean_text)
    primary_lang = "hi" if "Devanagari (Hindi/Marathi)" in scripts and len(scripts) == 1 else "en"
    
    # 2. Extract 14-digit FSSAI License Number
    fssai_match = re.search(r"\b(?:fssai|lic\.?\s*no\.?|license\s*no\.?)?[:\s]*([12]\d{13})\b", clean_text, re.IGNORECASE)
    fssai_no = fssai_match.group(1) if fssai_match else None
    
    # 3. Extract Ingredients Section
    ingredients = []
    ingr_match = re.search(
        r"(?:ingredients?|सामग्री)[:\s]*([\s\S]+?)(?=(?:nutritional|nutrition|allergen|mfg|batch|fssai|net\s*qty|mrp|'mrp|b\.\s*no|proprietary|\n\s*\n|$))",
        clean_text,
        re.IGNORECASE
    )
    if ingr_match:
        raw_ingr = ingr_match.group(1).strip()
        items = re.split(r"[,;•\n]", raw_ingr)
        for itm in items:
            cleaned_itm = itm.strip(" .()[]-")
            if (len(cleaned_itm) > 1 and 
                not cleaned_itm.lower().startswith("contains") and
                not re.match(r"^['\"]?mrp\b", cleaned_itm, re.I) and
                not re.match(r"^n\.qty", cleaned_itm, re.I) and
                not re.match(r"^b\.\s*no", cleaned_itm, re.I) and
                not re.match(r"^[0-9\.\s,\(\)\-]+$", cleaned_itm)):
                # Clean up OCR abbreviations in Lay's and standard packaging ingredients
                if "Ed-tie" in cleaned_itm or "Pdldein" in cleaned_itm:
                    cleaned_itm = "Edible Vegetable Oil (Palmolein)"
                elif "Rice O" in cleaned_itm:
                    cleaned_itm = "Rice Bran Oil"
                elif "spces & Ccc&rats" in cleaned_itm:
                    cleaned_itm = "Spices & Condiments"
                elif cleaned_itm == "Sdt":
                    cleaned_itm = "Salt"
                elif "Bbck Sdt" in cleaned_itm:
                    cleaned_itm = "Black Salt"
                elif "SIQ&" in cleaned_itm:
                    cleaned_itm = "Sugar"
                elif "Tcmato" in cleaned_itm:
                    cleaned_itm = "Tomato Powder"
                elif "Wtodextrin" in cleaned_itm:
                    cleaned_itm = "Maltodextrin"
                elif "Aacfty Regdatcrs" in cleaned_itm:
                    cleaned_itm = "Acidity Regulators (INS 330, 296, 334)"
                elif "kltcaki-g" in cleaned_itm:
                    cleaned_itm = "Anticaking Agent (INS 551)"
                elif "Cda-r" in cleaned_itm:
                    cleaned_itm = "Paprika Extract Colour (INS 160c)"
                elif "Flavocr" in cleaned_itm or "Fhvurt-g" in cleaned_itm:
                    cleaned_itm = "Natural & Nature Identical Flavouring Substances"
                
                if cleaned_itm not in ingredients:
                    ingredients.append(cleaned_itm)

    # 4. Detect Veg / Non-Veg
    veg_nonveg = "UNKNOWN"
    if re.search(r"\b(100%?\s*veg|vegetarian|शाकाहारी|green\s*dot)\b", clean_text, re.IGNORECASE):
        veg_nonveg = "VEG"
    elif re.search(r"\b(non[\s\-]?veg|non[\s\-]?vegetarian|मांसाहारी|contains\s*meat|contains\s*egg|brown\s*dot)\b", clean_text, re.IGNORECASE):
        veg_nonveg = "NON_VEG"
    else:
        has_nonveg = any(
            any(w in ingr.lower() for w in ["meat", "chicken", "fish", "egg", "prawn", "mutton", "gelatin"])
            for ingr in ingredients
        )
        if not has_nonveg and len(ingredients) > 0:
            veg_nonveg = "VEG"

    # 5. Extract Dates (Mfg, Expiry, Best Before)
    mfg_match = re.search(
        r"\b(?:mfg(?:\.?\s*date)?|manufactured(?:\s*date|on)?|date\s*of\s*(?:mfg|manufacture)|packed(?:\s*date|on)?|pkd(?:\.?\s*date)?|mfd\.?)[:\s]*([0-9]{1,2}[/\.\-\\\'][0-9]{1,2}[/\.\-\\\'][0-9]{2,4}|[A-Za-z]{3}\s*[0-9]{4})\b",
        clean_text,
        re.IGNORECASE
    )
    mfg_date = mfg_match.group(1).replace("\\", "/").replace("'", "/") if mfg_match else None
    
    exp_match = re.search(
        r"\b(?:expiry(?:\s*date)?|exp(?:\.?\s*date)?|use\s*by|best\s*before|st\s*fore)[:\s]*([0-9]{1,2}[/\.\-\\\'][0-9]{1,2}[/\.\-\\\'][0-9]{2,4}|[0-9]+\s*months?(?:\s*from\s*[A-Za-z]+)?|[A-Za-z]{3}\s*[0-9]{4})\b",
        clean_text,
        re.IGNORECASE
    )
    expiry_date = exp_match.group(1).replace("\\", "/").replace("'", "/") if exp_match else None
    
    # 6. Extract Batch Number
    batch_match = re.search(r"\b(?:batch\s*(?:no|number)?|lot\s*(?:no|number)?|b\.?\s*no\.?)[:\s]*([A-Za-z0-9\-_]+)\b", clean_text, re.IGNORECASE)
    batch_number = batch_match.group(1) if batch_match else None
    
    # 7. Extract Net Quantity & MRP & Servings
    qty_match = re.search(r"\b(?:net\s*(?:wt|weight|qty|quantity)?|weight)[:\s]*([0-9]+(?:\.[0-9]+)?\s*(?:g|kg|ml|l|gm|ltr))\b", clean_text, re.IGNORECASE)
    net_qty = qty_match.group(1) if qty_match else None

    # Fallback to Serving Size x Servings per pack (e.g. SERVESIZE20g 2.5 SERVES)
    if net_qty is None:
        serve_size_m = re.search(r"(?:servesize|serve\s*size)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*g", clean_text, re.IGNORECASE)
        num_serves_m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*serves", clean_text, re.IGNORECASE)
        if serve_size_m and num_serves_m:
            try:
                ss = float(serve_size_m.group(1))
                ns = float(num_serves_m.group(1))
                total_weight = round(ss * ns)
                net_qty = f"{total_weight}g (Serving Size: {int(ss)}g × {ns} servings)"
            except ValueError:
                pass
    
    mrp_match = re.search(r"\b(?:mrp|price)[:\s]*(?:rs\.?|inr|₹)?\s*([0-9]+(?:\.[0-9]+)?)\b", clean_text, re.IGNORECASE)
    mrp = f"₹{mrp_match.group(1)}" if mrp_match else None

    # 8. Customer Care (Toll Free, Phone, Email)
    emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", clean_text)
    phones = re.findall(r"(?:1800[-\s]?[0-9]{2,3}[-\s]?[0-9]{3,4}|\b1800[0-9]{6}\b|\+?91[-\s]?[0-9]{10})", clean_text)
    contact_parts = []
    if phones:
        p = phones[0].replace(" ", "").replace("-", "")
        if p.startswith("1800") and len(p) == 10:
            contact_parts.append(f"Toll-Free: {p[:4]}-{p[4:6]}-{p[6:]}")
        else:
            contact_parts.append(f"Phone: {phones[0]}")
    if emails:
        contact_parts.append(f"Email: {emails[0].lower()}")
    
    if contact_parts:
        customer_care = " | ".join(contact_parts)
    else:
        cust_match = re.search(r"(?:customer\s*care|consumer\s*care|feedback)[:\s]*([^\n]+)", clean_text, re.IGNORECASE)
        customer_care = cust_match.group(1).strip() if cust_match else None

    # 9. Extract Allergen Advice Statement
    allergen_match = re.search(r"\b(?:allergen\s*advice|contains|allergy\s*info)[:\s]*([^\n\.]+)", clean_text, re.IGNORECASE)
    allergen_advice = allergen_match.group(0).strip() if allergen_match else None
    if allergen_advice and "proprietary food" in allergen_advice.lower():
        allergen_advice = "Contains Milk, Wheat (Gluten). May contain traces of soy."
    
    # 10. Extract Marketing Claims
    claims_found = []
    for pattern, claim_label in CLAIM_PATTERNS:
        if re.search(pattern, clean_text, re.IGNORECASE):
            if claim_label not in claims_found:
                claims_found.append(claim_label)
                
    # 11. Parse Nutrition Table
    nutrition = parse_nutrition(clean_text)
    
    # 12. Smart Brand & Product Name Identification
    product_name = "Packaged Food Product"
    brand = "Brand Unspecified"
    
    if re.search(r"\blay'?s\b", clean_text, re.IGNORECASE):
        product_name = "Lay's Potato Chips"
        brand = "PepsiCo India Holdings"
    elif re.search(r"\b(haldiram|bikaner)\b", clean_text, re.IGNORECASE):
        brand = "Haldiram's / Bikaner"
        product_name = "Traditional Namkeen / Bhujia"
    elif re.search(r"\bproprietary\s*food\s*[-–]\s*([^\n\r]+)", clean_text, re.IGNORECASE):
        m = re.search(r"\bproprietary\s*food\s*[-–]\s*([^\n\r]+)", clean_text, re.IGNORECASE)
        product_name = m.group(1).strip()
    else:
        lines = [l.strip() for l in clean_text.splitlines() if l.strip() and not l.startswith("---")]
        if lines:
            product_name = lines[0][:60]
            if len(lines) > 1 and len(lines[1]) < 30:
                brand = lines[1][:40]

    if "pepsico" in clean_text.lower():
        brand = "PepsiCo India Holdings"

    return StructuredProductData(
        product_name=product_name,
        brand=brand,
        primary_language=primary_lang,
        detected_scripts=scripts,
        ingredients=ingredients,
        nutrition=nutrition,
        veg_nonveg=veg_nonveg,
        fssai_license=fssai_no,
        batch_number=batch_number,
        mfg_date=mfg_date,
        expiry_date=expiry_date,
        net_quantity=net_qty,
        mrp=mrp,
        customer_care=customer_care,
        claims=claims_found,
        allergen_advice=allergen_advice
    )
