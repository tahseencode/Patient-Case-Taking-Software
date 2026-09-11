from typing import Dict, List, Any, Optional
from backend.app.models.schemas import AyushPariksha

AYUSH_QUESTIONS = [
    {
        "id": "body_frame",
        "question": {
            "en": "How would you describe your body build and frame?",
            "hi": "आपकी शारीरिक बनावट और ढांचा कैसा है?"
        },
        "options": [
            {"value": "vata", "label_en": "Lean / Thin / Irregular bone structure", "label_hi": "पतला / दुबला / हड्डियां उभरी हुई (वात)", "score": {"vata": 1.0, "pitta": 0.0, "kapha": 0.0}},
            {"value": "pitta", "label_en": "Medium build / Muscular / Well-proportioned", "label_hi": "मध्यम गठन / सुडौल / सामान्य (पित्त)", "score": {"vata": 0.0, "pitta": 1.0, "kapha": 0.0}},
            {"value": "kapha", "label_en": "Broad / Heavy / Tendency to gain weight easily", "label_hi": "चौड़ा / भारी शरीर / आसानी से वजन बढ़ना (कफ)", "score": {"vata": 0.0, "pitta": 0.0, "kapha": 1.0}}
        ]
    },
    {
        "id": "skin_nature",
        "question": {
            "en": "What is the natural texture and feel of your skin?",
            "hi": "आपकी त्वचा की प्राकृतिक बनावट और स्पर्श कैसा रहता है?"
        },
        "options": [
            {"value": "vata", "label_en": "Dry, rough, easily cracked, cool to touch", "label_hi": "रूखी, बेजान, फटने वाली, ठंडी (वात)", "score": {"vata": 1.0, "pitta": 0.0, "kapha": 0.0}},
            {"value": "pitta", "label_en": "Warm, sensitive, reddish, prone to acne/moles", "label_hi": "गर्म, संवेदनशील, लालिमायुक्त, मुहासे (पित्त)", "score": {"vata": 0.0, "pitta": 1.0, "kapha": 0.0}},
            {"value": "kapha", "label_en": "Thick, smooth, oily, moist, soft", "label_hi": "चिकनी, तैलीय, मुलायम, चमकदार (कफ)", "score": {"vata": 0.0, "pitta": 0.0, "kapha": 1.0}}
        ]
    },
    {
        "id": "appetite_agni",
        "question": {
            "en": "How is your natural appetite and digestive power (Agni)?",
            "hi": "आपकी भूख और पाचन शक्ति (अग्नि) कैसी रहती है?"
        },
        "options": [
            {"value": "vishama", "label_en": "Irregular / Variable - hungry sometimes, not at others (Vishama Agni)", "label_hi": "अनियमित - कभी बहुत भूख कभी बिल्कुल नहीं (विषमाग्नि - वात)", "score": {"vata": 1.0, "pitta": 0.0, "kapha": 0.0}},
            {"value": "tikshna", "label_en": "Intense / Sharp - cannot tolerate hunger, acidic quickly (Tikshna Agni)", "label_hi": "तीव्र - भूख सहन नहीं होती, तुरंत खाना चाहिए (तीक्ष्णाग्नि - पित्त)", "score": {"vata": 0.0, "pitta": 1.0, "kapha": 0.0}},
            {"value": "manda", "label_en": "Slow / Sluggish - digests food slowly, feels heavy (Manda Agni)", "label_hi": "मंद - खाना देर से पचना, भारीपन (मंदाग्नि - कफ)", "score": {"vata": 0.0, "pitta": 0.0, "kapha": 1.0}},
            {"value": "sama", "label_en": "Balanced - normal steady hunger and easy digestion (Sama Agni)", "label_hi": "संतुलित - समय पर भूख और सुपाच्य (समाग्नि)", "score": {"vata": 0.33, "pitta": 0.33, "kapha": 0.34}}
        ]
    },
    {
        "id": "bowel_koshtha",
        "question": {
            "en": "What are your usual bowel habits (Koshtha)?",
            "hi": "आपका पेट साफ होने की प्रकृति (कोष्ठ) कैसी है?"
        },
        "options": [
            {"value": "krura", "label_en": "Hard stools, prone to gas and constipation (Krura Koshtha)", "label_hi": "कड़ा मल, कब्ज व गैस की प्रवृत्ति (क्रूर कोष्ठ - वात)", "score": {"vata": 1.0, "pitta": 0.0, "kapha": 0.0}},
            {"value": "mridu", "label_en": "Soft / Loose, frequent, sensitive to mild laxatives/milk (Mridu Koshtha)", "label_hi": "नरम/पतला मल, दिन में कई बार, तुरंत पेट साफ (मृदु कोष्ठ - पित्त)", "score": {"vata": 0.0, "pitta": 1.0, "kapha": 0.0}},
            {"value": "madhyama", "label_en": "Regular, well-formed, once or twice daily (Madhyama Koshtha)", "label_hi": "नियमित, बंधा हुआ, दिन में 1-2 बार (मध्यम कोष्ठ - कफ/सम)", "score": {"vata": 0.0, "pitta": 0.0, "kapha": 1.0}}
        ]
    },
    {
        "id": "sleep_pattern",
        "question": {
            "en": "How is your typical sleep pattern?",
            "hi": "आपकी नींद का स्वरूप कैसा रहता है?"
        },
        "options": [
            {"value": "vata", "label_en": "Light, broken, difficulty falling asleep, dreams of flying/running", "label_hi": "हल्की, बार-बार टूटने वाली, कम नींद (वात)", "score": {"vata": 1.0, "pitta": 0.0, "kapha": 0.0}},
            {"value": "pitta", "label_en": "Moderate (6-7 hrs), sound, vivid/passionate dreams", "label_hi": "मध्यम (6-7 घंटे), गहरी, सपने रंगीन/तेज़ (पित्त)", "score": {"vata": 0.0, "pitta": 1.0, "kapha": 0.0}},
            {"value": "kapha", "label_en": "Heavy, deep, long (>8 hrs), hard to wake up in morning", "label_hi": "बहुत गहरी, 8+ घंटे, सुबह उठने में सुस्ती (कफ)", "score": {"vata": 0.0, "pitta": 0.0, "kapha": 1.0}}
        ]
    },
    {
        "id": "climate_response",
        "question": {
            "en": "Which weather or climate do you dislike or feel uncomfortable in?",
            "hi": "आपको कौन सा मौसम सबसे ज्यादा असुविधाजनक या खराब लगता है?"
        },
        "options": [
            {"value": "vata", "label_en": "Cold, windy, and dry weather", "label_hi": "ठंड, सूखी हवा और सूखा मौसम (वात को प्रतिकूल)", "score": {"vata": 1.0, "pitta": 0.0, "kapha": 0.0}},
            {"value": "pitta", "label_en": "Hot, humid summer and direct sun", "label_hi": "तेज गर्मी, चिलचिलाती धूप, उमस (पित्त को प्रतिकूल)", "score": {"vata": 0.0, "pitta": 1.0, "kapha": 0.0}},
            {"value": "kapha", "label_en": "Damp, rainy, cloudy, and chilly weather", "label_hi": "बरसात, सीलन, बादल और ठंडी उमस (कफ को प्रतिकूल)", "score": {"vata": 0.0, "pitta": 0.0, "kapha": 1.0}}
        ]
    },
    {
        "id": "temperament_mind",
        "question": {
            "en": "What is your mental and emotional temperament?",
            "hi": "आपका स्वभाव और मानसिक व्यवहार कैसा रहता है?"
        },
        "options": [
            {"value": "vata", "label_en": "Quick thinker, creative, enthusiastic, easily anxious/worried", "label_hi": "तेज सोच, उत्साही, जल्दी घबराने या चिंता करने वाले (वात)", "score": {"vata": 1.0, "pitta": 0.0, "kapha": 0.0}},
            {"value": "pitta", "label_en": "Sharp intellect, ambitious, decisive, quick to get irritated/angry", "label_hi": "कुशाग्र बुद्धि, लक्ष्य केंद्रित, जल्दी गुस्सा/चिड़चिड़ापन (पित्त)", "score": {"vata": 0.0, "pitta": 1.0, "kapha": 0.0}},
            {"value": "kapha", "label_en": "Calm, steady, patient, forgiving, slow to react", "label_hi": "शांत, धैर्यवान, क्षमाशील, धीरे-धीरे निर्णय लेने वाले (कफ)", "score": {"vata": 0.0, "pitta": 0.0, "kapha": 1.0}}
        ]
    }
]

class AyushEngine:
    @staticmethod
    def get_ayush_questions(language: str = "hi") -> List[Dict[str, Any]]:
        result = []
        for q in AYUSH_QUESTIONS:
            q_text = q["question"].get(language, q["question"]["en"])
            options = []
            for opt in q["options"]:
                label_key = f"label_{language}" if f"label_{language}" in opt else "label_en"
                options.append({
                    "value": opt["value"],
                    "label": opt.get(label_key, opt["label_en"]),
                    "score": opt["score"]
                })
            result.append({
                "id": q["id"],
                "question": q_text,
                "options": options
            })
        return result

    @staticmethod
    def calculate_pariksha(answers: Dict[str, str], lifestyle_notes: Optional[str] = None) -> AyushPariksha:
        vata_score = 0.0
        pitta_score = 0.0
        kapha_score = 0.0
        total_q = 0

        agni_val = "Sama Agni (Balanced)"
        koshtha_val = "Madhyama Koshtha (Regular)"

        for q in AYUSH_QUESTIONS:
            qid = q["id"]
            selected_val = answers.get(qid)
            if selected_val:
                for opt in q["options"]:
                    if opt["value"] == selected_val:
                        vata_score += opt["score"]["vata"]
                        pitta_score += opt["score"]["pitta"]
                        kapha_score += opt["score"]["kapha"]
                        total_q += 1
                        
                        if qid == "appetite_agni":
                            if selected_val == "vishama": agni_val = "Vishama Agni (Irregular - Vata)"
                            elif selected_val == "tikshna": agni_val = "Tikshna Agni (Sharp/Hyperactive - Pitta)"
                            elif selected_val == "manda": agni_val = "Manda Agni (Sluggish/Slow - Kapha)"
                            elif selected_val == "sama": agni_val = "Sama Agni (Equilibrated/Normal)"

                        if qid == "bowel_koshtha":
                            if selected_val == "krura": koshtha_val = "Krura Koshtha (Hard/Costive - Vata)"
                            elif selected_val == "mridu": koshtha_val = "Mridu Koshtha (Soft/Lax - Pitta)"
                            elif selected_val == "madhyama": koshtha_val = "Madhyama Koshtha (Balanced)"

        if total_q > 0:
            sum_scores = vata_score + pitta_score + kapha_score
            v_pct = round((vata_score / sum_scores) * 100, 1) if sum_scores > 0 else 33.3
            p_pct = round((pitta_score / sum_scores) * 100, 1) if sum_scores > 0 else 33.3
            k_pct = round((kapha_score / sum_scores) * 100, 1) if sum_scores > 0 else 33.4
        else:
            v_pct, p_pct, k_pct = 33.3, 33.3, 33.4

        # Determine dominant prakriti
        scores = [("Vata", v_pct), ("Pitta", p_pct), ("Kapha", k_pct)]
        scores.sort(key=lambda x: x[1], reverse=True)

        if scores[0][1] - scores[1][1] < 8:
            dominant_str = f"{scores[0][0]}-{scores[1][0]} Dwandvaja Prakriti"
        elif scores[0][1] > 50:
            dominant_str = f"Pure {scores[0][0]} Prakriti"
        else:
            dominant_str = f"{scores[0][0]} Dominant ({scores[1][0]} Anubandha)"

        # Nidana causative mapping from lifestyle
        nidana = []
        if lifestyle_notes:
            ls = lifestyle_notes.lower()
            if "spicy" in ls or "fried" in ls or "तिखा" in ls or "तले" in ls:
                nidana.append("Vidahi & Katu Ahara Sevana (Excess spicy/pungent food)")
            if "late night" in ls or "देर रात" in ls or "जागना" in ls:
                nidana.append("Ratri Jagarana (Late night awakening aggravating Vata/Pitta)")
            if "stress" in ls or "तनाव" in ls or "चिंता" in ls:
                nidana.append("Manasika Nidana - Chinta/Shoka (Mental stress)")
            if "irregular" in ls or "अनियमित" in ls:
                nidana.append("Vishamashana (Irregular meal timing causing Agnimandya)")

        if not nidana:
            nidana.append("Asatmya Ahara-Vihara (Dietary irregularities)")

        return AyushPariksha(
            prakriti_scores={"vata": v_pct, "pitta": p_pct, "kapha": k_pct},
            dominant_prakriti=dominant_str,
            agni=agni_val,
            koshtha=koshtha_val,
            sara="Madhyama Sara (Moderate tissue vitality)",
            samhanana="Madhyama Samhanana (Balanced body compactness)",
            pramana="Madhyama Pramana (Normal proportions)",
            satmya="Madhyama Satmya",
            sattva="Madhyama Sattva",
            ahara_shakti=f"Digestive power aligned with {agni_val}",
            vyayama_shakti="Madhyama (Moderate physical endurance)",
            vaya="Madhyama Vaya (Adult)",
            ahara_vihara_notes=lifestyle_notes or "General mixed vegetarian/non-vegetarian Indian diet, regular activity.",
            nidana_causative_factors=nidana
        )

ayush_engine = AyushEngine()
