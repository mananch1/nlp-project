import re
from typing import List
from ..schemas import StructuredProductData, ComplianceCheckItem, AuditSummary
from .parser_service import ALLERGEN_KEYWORDS, SUGAR_INDICATORS

def run_baseline_compliance_audit(data: StructuredProductData) -> AuditSummary:
    """
    Executes automated rule-based compliance checks against FSSAI Labelling (2020)
    and Advertising & Claims (2018) regulations.
    """
    items: List[ComplianceCheckItem] = []
    
    # 1. Check FSSAI License Number (Regulation 5(6))
    if data.fssai_license and len(data.fssai_license) == 14 and data.fssai_license.isdigit():
        items.append(ComplianceCheckItem(
            rule_id="FSSAI-LABEL-5.6",
            regulation="Food Safety and Standards (Labelling and Display) Regulations, 2020",
            section="Regulation 5(6)",
            title="FSSAI Logo and 14-Digit License Number",
            status="PASS",
            severity="INFO",
            evidence=f"Valid 14-digit FSSAI License detected: {data.fssai_license}",
            statutory_clause="The FSSAI logo and 14-digit Food Safety License number shall be displayed on the label in the format 'Lic. No. XXXXXXXXXXXXXX'.",
            confidence=0.95
        ))
    else:
        items.append(ComplianceCheckItem(
            rule_id="FSSAI-LABEL-5.6",
            regulation="Food Safety and Standards (Labelling and Display) Regulations, 2020",
            section="Regulation 5(6)",
            title="FSSAI Logo and 14-Digit License Number",
            status="FAIL",
            severity="CRITICAL",
            evidence="No valid 14-digit FSSAI License Number detected on packaging images.",
            statutory_clause="Mandatory declaration of FSSAI logo and 14-digit food business operator license number under Regulation 5(6).",
            confidence=0.88
        ))

    # 2. Check Veg / Non-Veg Symbol (Regulation 5(3))
    if data.veg_nonveg in ["VEG", "NON_VEG"]:
        label = "Vegetarian (Green Dot)" if data.veg_nonveg == "VEG" else "Non-Vegetarian (Brown Triangle)"
        items.append(ComplianceCheckItem(
            rule_id="FSSAI-LABEL-5.3",
            regulation="Food Safety and Standards (Labelling and Display) Regulations, 2020",
            section="Regulation 5(3)",
            title="Mandatory Veg/Non-Veg Symbol",
            status="PASS",
            severity="INFO",
            evidence=f"Product contains statutory {label} declaration.",
            statutory_clause="Every package of Vegetarian food shall bear a green circle inside a green square; Non-Vegetarian food shall bear a brown triangle inside a brown square.",
            confidence=0.92
        ))
    else:
        items.append(ComplianceCheckItem(
            rule_id="FSSAI-LABEL-5.3",
            regulation="Food Safety and Standards (Labelling and Display) Regulations, 2020",
            section="Regulation 5(3)",
            title="Mandatory Veg/Non-Veg Symbol",
            status="WARNING",
            severity="MAJOR",
            evidence="Vegetarian/Non-Vegetarian symbol was not detected in packaging images.",
            statutory_clause="Every packaged food must prominently display the Green (Veg) or Brown (Non-Veg) logo on the principal display panel.",
            confidence=0.82
        ))

    # 3. Check Mandatory Saturated Fat & Trans Fat Declaration (Regulation 5(2)(a))
    nutr = data.nutrition
    has_sat_fat = nutr.saturated_fat_g is not None
    has_trans_fat = nutr.trans_fat_g is not None
    
    if has_sat_fat and has_trans_fat:
        items.append(ComplianceCheckItem(
            rule_id="FSSAI-LABEL-5.2.A",
            regulation="Food Safety and Standards (Labelling and Display) Regulations, 2020",
            section="Regulation 5(2)(a)",
            title="Mandatory Trans Fat & Saturated Fat Declaration",
            status="PASS",
            severity="INFO",
            evidence=f"Declared Saturated Fat: {nutr.saturated_fat_g}g, Trans Fat: {nutr.trans_fat_g}g.",
            statutory_clause="Nutritional information must explicitly declare Amounts of Saturated Fat and Trans Fat per 100g/serving.",
            confidence=0.95
        ))
    else:
        missing = []
        if not has_sat_fat: missing.append("Saturated Fat")
        if not has_trans_fat: missing.append("Trans Fat")
        items.append(ComplianceCheckItem(
            rule_id="FSSAI-LABEL-5.2.A",
            regulation="Food Safety and Standards (Labelling and Display) Regulations, 2020",
            section="Regulation 5(2)(a)",
            title="Mandatory Trans Fat & Saturated Fat Declaration",
            status="FAIL",
            severity="MAJOR",
            evidence=f"Missing mandatory nutritional parameter(s): {', '.join(missing)}.",
            statutory_clause="Declaration of saturated fat and trans fat are strictly mandatory on all prepackaged foods under Regulation 5(2)(a).",
            confidence=0.90
        ))

    # 4. Check Date Marking (Regulation 5(8))
    if data.expiry_date or data.mfg_date:
        items.append(ComplianceCheckItem(
            rule_id="FSSAI-LABEL-5.8",
            regulation="Food Safety and Standards (Labelling and Display) Regulations, 2020",
            section="Regulation 5(8)",
            title="Date Marking (Mfg / Best Before / Expiry)",
            status="PASS",
            severity="INFO",
            evidence=f"Date stamps detected: Mfg: {data.mfg_date or 'N/A'}, Expiry/Best Before: {data.expiry_date or 'N/A'}",
            statutory_clause="The date of manufacture or packaging, and Best Before or Expiry Date must be declared on the label.",
            confidence=0.90
        ))
    else:
        items.append(ComplianceCheckItem(
            rule_id="FSSAI-LABEL-5.8",
            regulation="Food Safety and Standards (Labelling and Display) Regulations, 2020",
            section="Regulation 5(8)",
            title="Date Marking (Mfg / Best Before / Expiry)",
            status="WARNING",
            severity="MAJOR",
            evidence="Neither Manufacturing date nor Expiry / Best Before date could be clearly identified.",
            statutory_clause="Mandatory declaration of date of manufacture/packaging and Best Before/Expiry Date.",
            confidence=0.85
        ))

    # 5. Check Allergen Declaration (Regulation 5(9))
    ingr_text_blob = " ".join(data.ingredients).lower()
    allergens_found = []
    for allergen, kw_list in ALLERGEN_KEYWORDS.items():
        if any(kw in ingr_text_blob for kw in kw_list):
            allergens_found.append(allergen)

    if allergens_found:
        if data.allergen_advice:
            items.append(ComplianceCheckItem(
                rule_id="FSSAI-LABEL-5.9",
                regulation="Food Safety and Standards (Labelling and Display) Regulations, 2020",
                section="Regulation 5(9)",
                title="Mandatory Allergen Declaration",
                status="PASS",
                severity="INFO",
                evidence=f"Allergen statement declared: '{data.allergen_advice}' for identified allergens ({', '.join(allergens_found)}).",
                statutory_clause="Presence of cereals with gluten, nuts, milk, soy, egg, fish, sulphite shall be declared separately under 'ALLERGEN ADVICE'.",
                confidence=0.91
            ))
        else:
            items.append(ComplianceCheckItem(
                rule_id="FSSAI-LABEL-5.9",
                regulation="Food Safety and Standards (Labelling and Display) Regulations, 2020",
                section="Regulation 5(9)",
                title="Mandatory Allergen Declaration",
                status="FAIL",
                severity="CRITICAL",
                evidence=f"Product ingredients contain recognized allergens ({', '.join(allergens_found)}) but no separate ALLERGEN ADVICE statement was declared.",
                statutory_clause="Failure to provide a separate bold Allergen Advisory statement violates Regulation 5(9).",
                confidence=0.88
            ))

    # 6. Check 'No Added Sugar' Claim vs Ingredients (Advertising Claims Schedule II)
    if any("No Added Sugar" in c for c in data.claims):
        sugars_in_ingr = [s for s in SUGAR_INDICATORS if s in ingr_text_blob]
        has_added_sugar_nutr = data.nutrition.added_sugars_g is not None and data.nutrition.added_sugars_g > 0
        if sugars_in_ingr or has_added_sugar_nutr:
            evidence_details = []
            if sugars_in_ingr:
                evidence_details.append(f"ingredients disclose sugar-yielding components: {', '.join(sugars_in_ingr)}")
            if has_added_sugar_nutr:
                evidence_details.append(f"nutrition table declares {data.nutrition.added_sugars_g}g added sugars per 100g/ml")
            items.append(ComplianceCheckItem(
                rule_id="FSSAI-CLAIM-5.NO_ADDED_SUGAR",
                regulation="Food Safety and Standards (Advertising and Claims) Regulations, 2018",
                section="Schedule II, Clause 2",
                title="Deceptive 'No Added Sugar' Claim",
                status="FAIL",
                severity="CRITICAL",
                evidence=f"Product claims 'No Added Sugar' on packaging, but {'; '.join(evidence_details)}.",
                statutory_clause="'No Added Sugar' claims are unlawful if ingredients contain added sucrose, glucose, jaggery, honey, corn syrup, or fruit concentrates.",
                confidence=0.96
            ))
        else:
            items.append(ComplianceCheckItem(
                rule_id="FSSAI-CLAIM-5.NO_ADDED_SUGAR",
                regulation="Food Safety and Standards (Advertising and Claims) Regulations, 2018",
                section="Schedule II, Clause 2",
                title="'No Added Sugar' Claim",
                status="PASS",
                severity="INFO",
                evidence="No hidden or added sugar ingredients identified in the list of ingredients.",
                statutory_clause="'No Added Sugar' claim appears substantiated by declared ingredient list.",
                confidence=0.85
            ))

    # 7. Check '100% Natural' / 'Pure' Claim vs Additives (Advertising Claims Schedule V)
    if any("Natural" in c or "Pure" in c for c in data.claims):
        additives_detected = re.findall(r"\b(ins\s*\d+|preservative|artificial\s*colour|synthetic\s*flavour|emulsifier|stabilizer|acidity\s*regulator)\b", ingr_text_blob, re.IGNORECASE)
        if additives_detected:
            items.append(ComplianceCheckItem(
                rule_id="FSSAI-CLAIM-5.NATURAL_PURE",
                regulation="Food Safety and Standards (Advertising and Claims) Regulations, 2018",
                section="Schedule V, Clause 1",
                title="Misleading 'Natural / Pure' Claim",
                status="FAIL",
                severity="MAJOR",
                evidence=f"Product claims 'Natural / Pure' but includes artificial or chemical food additives in ingredients: {', '.join(set(additives_detected))}.",
                statutory_clause="'Natural' shall only be used for single foods with no added additives, preservatives, or artificial chemicals.",
                confidence=0.94
            ))
        else:
            items.append(ComplianceCheckItem(
                rule_id="FSSAI-CLAIM-5.NATURAL_PURE",
                regulation="Food Safety and Standards (Advertising and Claims) Regulations, 2018",
                section="Schedule V, Clause 1",
                title="'Natural / Pure' Claim",
                status="PASS",
                severity="INFO",
                evidence="No chemical food additives or artificial preservatives detected in ingredients.",
                statutory_clause="Natural claim substantiated under Schedule V Clause 1.",
                confidence=0.87
            ))

    # Calculate overall audit summary
    total = len(items)
    passed = sum(1 for itm in items if itm.status == "PASS")
    failed = sum(1 for itm in items if itm.status == "FAIL")
    warnings = sum(1 for itm in items if itm.status == "WARNING")
    
    if failed > 0:
        overall_status = "NON_COMPLIANT"
    elif warnings > 0:
        overall_status = "SUSPECTED_VIOLATION"
    else:
        overall_status = "COMPLIANT"
        
    avg_conf = sum(itm.confidence for itm in items) / total if total > 0 else 0.85

    return AuditSummary(
        total_checks=total,
        passed_checks=passed,
        failed_checks=failed,
        warning_checks=warnings,
        overall_status=overall_status,
        overall_confidence=round(avg_conf, 2),
        items=items
    )
