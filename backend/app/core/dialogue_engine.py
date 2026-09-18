import re
from typing import Dict, List, Any, Optional
from backend.app.models.schemas import SocratesResponse, LanguageEnum

# Master list of Chief Complaints mapped to anatomical regions & specialties
CHIEF_COMPLAINTS = [
    {
        "id": "chest_pain",
        "name_en": "Chest Pain / Discomfort",
        "name_hi": "छाती में दर्द / भारीपन",
        "name_mr": "छातीत दुखणे",
        "name_ta": "மார்பு வலி",
        "name_te": "ఛాతీ నొప్పి",
        "name_bn": "বুকে ব্যথা",
        "name_gu": "છાતીમાં દુખાવો",
        "name_kn": "ಎದೆ ನೋವು",
        "body_part": "chest",
        "specialty": "Cardiology / Medicine",
        "is_high_risk": True
    },
    {
        "id": "breathlessness",
        "name_en": "Breathlessness / Difficulty Breathing",
        "name_hi": "सांस लेने में तकलीफ / घबराहट",
        "name_mr": "श्वास घेण्यास त्रास",
        "name_ta": "மூச்சுத் திணறல்",
        "name_te": "శ్వాస ఆడకపోవడం",
        "name_bn": "শ্বাসকষ্ট",
        "name_gu": "શ્વાસ લેવામાં તકલીફ",
        "name_kn": "ಉಸಿರಾಟದ ತೊಂದರೆ",
        "body_part": "chest",
        "specialty": "Pulmonology / Cardiology",
        "is_high_risk": True
    },
    {
        "id": "fever",
        "name_en": "Fever & Body Chills",
        "name_hi": "बुखार और कंपकंपी",
        "name_mr": "ताप आणि थंडी",
        "name_ta": "காய்ச்சல் மற்றும் குளிர்",
        "name_te": "జ్వరం మరియు చలి",
        "name_bn": "জ্বর ও কাঁপুনি",
        "name_gu": "તાવ અને ધ્રુજારી",
        "name_kn": "ಜ್ವರ ಮತ್ತು ನಡುಕ",
        "body_part": "whole_body",
        "specialty": "General Medicine",
        "is_high_risk": False
    },
    {
        "id": "abdominal_pain",
        "name_en": "Abdominal / Stomach Pain",
        "name_hi": "पेट में दर्द या मरोड़",
        "name_mr": "पोटात दुखणे",
        "name_ta": "வயிற்று வலி",
        "name_te": "కడుపు నొప్పి",
        "name_bn": "পেটে ব্যথা",
        "name_gu": "પેટમાં દુખાવો",
        "name_kn": "ಹೊಟ್ಟೆ ನೋವು",
        "body_part": "abdomen",
        "specialty": "Gastroenterology / Surgery",
        "is_high_risk": False
    },
    {
        "id": "headache_dizziness",
        "name_en": "Severe Headache / Dizziness / Slurred Speech",
        "name_hi": "तेज सिरदर्द / चक्कर / बोलने में दिक्कत",
        "name_mr": "तीव्र डोकेदुखी / चक्कर",
        "name_ta": "கடுமையான தலைவலி / தலைச்சுற்றல்",
        "name_te": "తీవ్రమైన తలనొప్పి / మైకం",
        "name_bn": "তীব্র মাথাব্যথা / মাথা ঘোরা",
        "name_gu": "માથાનો દુખાવો / ચક્કર",
        "name_kn": "ತೀವ್ರ ತಲೆನೋವು / ತಲೆತಿರುಗುವಿಕೆ",
        "body_part": "head",
        "specialty": "Neurology",
        "is_high_risk": True
    },
    {
        "id": "joint_pain",
        "name_en": "Joint Pain & Stiffness (Knee/Back)",
        "name_hi": "जोड़ों या कमर में दर्द / अकड़न",
        "name_mr": "सांधेदुखी / कंबरदुखी",
        "name_ta": "மூட்டு வலி",
        "name_te": "కీళ్ల నొప్పులు",
        "name_bn": "জয়েন্টে ব্যথা",
        "name_gu": "સાંધાનો દુખાવો",
        "name_kn": "ಕೀಲು ನೋವು",
        "body_part": "joints",
        "specialty": "Orthopaedics / Rheumatology",
        "is_high_risk": False
    },
    {
        "id": "diabetes_followup",
        "name_en": "Diabetes / Blood Sugar & BP Checkup",
        "name_hi": "शुगर (डायबिटीज) और बीपी की नियमित जांच",
        "name_mr": "मधुमेह आणि रक्तदाब तपासणी",
        "name_ta": "நீரிழிவு மற்றும் ரத்த அழுத்தம்",
        "name_te": "మధుమేహం మరియు రక్తపోటు",
        "name_bn": "ডায়াবেটিস ও রক্তচাপ পরীক্ষা",
        "name_gu": "ડાયાબિટીસ અને બ્લડ પ્રેશર",
        "name_kn": "ಮಧುಮೇಹ ಮತ್ತು ರಕ್ತದೊತ್ತಡ",
        "body_part": "whole_body",
        "specialty": "Endocrinology / General Medicine",
        "is_high_risk": False
    },
    {
        "id": "cough_cold",
        "name_en": "Persistent Cough & Throat Pain",
        "name_hi": "लगातार खांसी, बलगम या गले में दर्द",
        "name_mr": "खोकला आणि घसादुखी",
        "name_ta": "இருமல் மற்றும் தொண்டை வலி",
        "name_te": "దగ్గు మరియు గొంతు నొప్పి",
        "name_bn": "কাশি ও গলা ব্যথা",
        "name_gu": "ખાંસી અને ગળામાં દુખાવો",
        "name_kn": "ಕೆಮ್ಮು ಮತ್ತು ಗಂಟಲು ನೋವು",
        "body_part": "chest",
        "specialty": "ENT / Pulmonology",
        "is_high_risk": False
    },
    {
        "id": "skin_rash",
        "name_en": "Skin Rash, Itching or Boils",
        "name_hi": "त्वचा पर दाने, खुजली या चकत्ते",
        "name_mr": "त्वचेवर खाज आणि पुरळ",
        "name_ta": "தோல் அரிப்பு / தடிப்பு",
        "name_te": "చర్మం దురద / దద్దుర్లు",
        "name_bn": "চুলকানি ও ফুসকুড়ি",
        "name_gu": "ચામડીની ખંજવાળ",
        "name_kn": "ಚರ್ಮದ ತುರಿಕೆ",
        "body_part": "skin",
        "specialty": "Dermatology",
        "is_high_risk": False
    },
    {
        "id": "urinary_issues",
        "name_en": "Burning Urine / Frequent Urination",
        "name_hi": "पेशाब में जलन या बार-बार पेशाब आना",
        "name_mr": "लघवी करताना जळजळ",
        "name_ta": "சிறுநீர் எரிச்சல்",
        "name_te": "మూత్ర విసర్జనలో మంట",
        "name_bn": "প্রস্রাবে জ্বালাপোড়া",
        "name_gu": "પેશાબમાં બળતરા",
        "name_kn": "ಮೂತ್ರದಲ್ಲಿ ಉರಿ",
        "body_part": "pelvis",
        "specialty": "Urology / Nephrology",
        "is_high_risk": False
    }
]

# SOCRATES Interview Steps with full Multilingual Translations
SOCRATES_STEPS = [
    {
        "step_id": "site",
        "clinical_field": "site",
        "question": {
            "en": "Where exactly is your discomfort located?",
            "hi": "आपको परेशानी या दर्द शरीर के किस हिस्से में हो रहा है?",
            "mr": "तुम्हाला त्रास किंवा वेदना शरीराच्या कोणत्या भागात होत आहे?",
            "ta": "உங்கள் வலி அல்லது அசௌகரியம் சரியாக எந்த இடத்தில் உள்ளது?",
            "te": "మీ అసౌకర్యం లేదా నొప్పి ఖచ్చితంగా ఎక్కడ ఉంది?",
            "bn": "আপনার অস্বস্তি বা ব্যথা ঠিক কোন জায়গায় হচ্ছে?",
            "gu": "તમારી તકલીફ કે દુખાવો શરીરના કયા ભાગમાં છે?",
            "kn": "ನಿಮ್ಮ ತೊಂದರೆ ಅಥವಾ ನೋವು ನಿಖರವಾಗಿ ಎಲ್ಲಿ ಇದೆ?"
        },
        "options": [
            {"value": "left_chest", "label_en": "Left Side of Chest", "label_hi": "छाती के बाएं हिस्से में"},
            {"value": "center_chest", "label_en": "Center / Retro-sternal", "label_hi": "छाती के बिल्कुल बीच में"},
            {"value": "upper_abdomen", "label_en": "Upper Stomach / Epigastric", "label_hi": "पेट के ऊपरी हिस्से में"},
            {"value": "lower_abdomen", "label_en": "Lower Abdomen", "label_hi": "पेट के निचले हिस्से में"},
            {"value": "head_forehead", "label_en": "Head / Forehead", "label_hi": "सिर / माथे पर"},
            {"value": "knees_joints", "label_en": "Knees / Joints", "label_hi": "घुटने / जोड़ों में"},
            {"value": "throat_neck", "label_en": "Throat / Neck", "label_hi": "गले या गर्दन में"},
            {"value": "lower_back", "label_en": "Lower Back / Spine", "label_hi": "कमर या पीठ में"}
        ]
    },
    {
        "step_id": "onset",
        "clinical_field": "onset",
        "question": {
            "en": "When and how did this symptom start?",
            "hi": "यह लक्षण कब और कैसे शुरू हुआ था?",
            "mr": "हा त्रास कधी आणि कसा सुरू झाला?",
            "ta": "இந்த அறிகுறி எப்போது, எப்படி தொடங்கியது?",
            "te": "ఈ లక్షణం ఎప్పుడు, ఎలా ప్రారంభమైంది?",
            "bn": "এই লক্ষণটি কখন এবং কীভাবে শুরু হয়েছিল?",
            "gu": "આ લક્ષણ ક્યારે અને કેવી રીતે શરૂ થયું?",
            "kn": "ಈ ಲಕ್ಷಣ ಯಾವಾಗ ಮತ್ತು ಹೇಗೆ ಪ್ರಾರಂಭವಾಯಿತು?"
        },
        "options": [
            {"value": "sudden_today", "label_en": "Sudden (Within last 2-6 hours)", "label_hi": "अचानक आज (पिछले 2-6 घंटों में)"},
            {"value": "last_24_hours", "label_en": "Yesterday (Within 24 hours)", "label_hi": "कल से (पिछले 24 घंटों में)"},
            {"value": "few_days", "label_en": "2 to 5 days ago", "label_hi": "2 से 5 दिन पहले से"},
            {"value": "few_weeks", "label_en": "1 to 3 weeks ago", "label_hi": "1 से 3 हफ़्ते पहले से"},
            {"value": "chronic_months", "label_en": "Long-standing (> 1 month)", "label_hi": "काफी समय से (1 महीने से अधिक)"}
        ]
    },
    {
        "step_id": "character",
        "clinical_field": "character",
        "question": {
            "en": "How would you describe the feeling or type of pain?",
            "hi": "आप दर्द या परेशानी की प्रकृति को कैसा महसूस करते हैं?",
            "mr": "वेदना कशा प्रकारची जाणवते?",
            "ta": "வலியின் தன்மை எப்படி இருக்கிறது?",
            "te": "నొప్పి లేదా అనుభూతి ఎలాంటి రకమైనది?",
            "bn": "ব্যথার ধরনটা কেমন অনুভূত হয়?",
            "gu": "દુખાવાનો પ્રકાર કેવો લાગે છે?",
            "kn": "ನೋವಿನ ಸ್ವರೂಪ ಹೇಗಿದೆ?"
        },
        "options": [
            {"value": "heavy_crushing", "label_en": "Heavy Pressure / Squeezing / Tightness", "label_hi": "भारीपन / जकड़न / भारी दबाव"},
            {"value": "sharp_stabbing", "label_en": "Sharp / Stabbing / Pricking", "label_hi": "तेज़ सुई जैसी चुभन या कांटे जैसा दर्द"},
            {"value": "burning_acidic", "label_en": "Burning / Acidic sensation", "label_hi": "जलन / तेज़ाब जैसी जलन"},
            {"value": "dull_aching", "label_en": "Dull continuous ache", "label_hi": "धीमा-धीमा लगातार दर्द"},
            {"value": "throbbing_pulsing", "label_en": "Throbbing / Pulsating", "label_hi": "धड़कता हुआ / टीस मारने वाला दर्द"},
            {"value": "cramping_colicky", "label_en": "Twisting / Cramping / Spasm", "label_hi": "मरोड़ या ऐंठन जैसा दर्द"}
        ]
    },
    {
        "step_id": "radiation",
        "clinical_field": "radiation",
        "question": {
            "en": "Does the pain or sensation travel or spread to any other part?",
            "hi": "क्या यह दर्द शरीर के किसी अन्य हिस्से में फैलता या जा रहा है?",
            "mr": "वेदना इतर कोणत्याही भागात पसरत आहेत का?",
            "ta": "வலி உடலின் வேறு பகுதிக்கு பரவுகிறதா?",
            "te": "నొప్పి శరీరంలోని ఇతర భాగాలకు వ్యాపిస్తుందా?",
            "bn": "ব্যথা কি অন্য কোনো অংশে ছড়িয়ে পড়ছে?",
            "gu": "શું દુખાવો શરીરના અન્ય ભાગમાં ફેલાય છે?",
            "kn": "ನೋವು ಬೇರೆ ಭಾಗಗಳಿಗೆ ಹರಡುತ್ತಿದೆಯೇ?"
        },
        "options": [
            {"value": "radiates_left_arm_jaw", "label_en": "Spreads to Left Arm, Shoulder or Jaw", "label_hi": "बाएं हाथ, कंधे या जबड़े की तरफ फैलता है"},
            {"value": "radiates_back", "label_en": "Spreads to Back / Shoulder blades", "label_hi": "पीठ या दोनों कंधों के बीच फैलता है"},
            {"value": "radiates_groin_thigh", "label_en": "Spreads downward to Groin or Leg", "label_hi": "नीचे जांघ या पैर की तरफ फैलता है"},
            {"value": "no_radiation", "label_en": "No, stays in one place only", "label_hi": "नहीं, केवल एक ही जगह रहता है"}
        ]
    },
    {
        "step_id": "associations",
        "clinical_field": "associations",
        "question": {
            "en": "Are you experiencing any other accompanying symptoms?",
            "hi": "क्या आपको साथ में इनमें से कोई अन्य परेशानी भी हो रही है?",
            "mr": "सोबत इतर कोणती लक्षणे आहेत का?",
            "ta": "இதனுடன் வேறு ஏதேனும் அறிகுறிகள் உள்ளதா?",
            "te": "దీనితో పాటు ఇతర లక్షణాలు ఏమైనా ఉన్నాయా?",
            "bn": "এর সাথে অন্য কোনো উপসর্গ আছে কি?",
            "gu": "સાથે અન્ય કોઈ લક્ષણો છે?",
            "kn": "ಇದರ ಜೊತೆಗೆ ಬೇರೆ ತೊಂದರೆಗಳಿವೆಯೇ?"
        },
        "options": [
            {"value": "profuse_sweating", "label_en": "Profuse Cold Sweating", "label_hi": "ठंडा पसीना आना"},
            {"value": "shortness_of_breath", "label_en": "Breathlessness / Panting", "label_hi": "सांस फूलना या घबराहट"},
            {"value": "nausea_vomiting", "label_en": "Nausea / Vomiting", "label_hi": "उल्टी या जी मिचलाना"},
            {"value": "dizziness_blackout", "label_en": "Dizziness / Feeling of Fainting", "label_hi": "चक्कर आना या आंखों के आगे अंधेरा"},
            {"value": "fever_chills", "label_en": "High Fever or Shivering", "label_hi": "तेज़ बुखार या कंपकंपी"},
            {"value": "palpitations", "label_en": "Fast Heart Racing (Palpitations)", "label_hi": "दिल की धड़कन बहुत तेज़ होना"},
            {"value": "none_associated", "label_en": "None of these", "label_hi": "इनमें से कोई नहीं"}
        ]
    },
    {
        "step_id": "timing",
        "clinical_field": "timing",
        "question": {
            "en": "Is the problem continuous or does it come and go at specific times?",
            "hi": "क्या यह तकलीफ लगातार बनी रहती है या बीच-बीच में आती-जाती है?",
            "mr": "त्रास सतत होतो की थांबून थांबून होतो?",
            "ta": "பிரச்சனை தொடர்ச்சியாக உள்ளதா அல்லது விட்டு விட்டு வருகிறதா?",
            "te": "సమస్య నిరంతరంగా ఉందా లేదా వచ్చిపోతుందా?",
            "bn": "সমস্যাটি কি সবসময় থাকে নাকি আসা-যাওয়া করে?",
            "gu": "તકલીફ સતત રહે છે કે વચમાં વચમાં થાય છે?",
            "kn": "ತೊಂದರೆ ನಿರಂತರವಾಗಿದೆಯೇ ಅಥವಾ ಬಂದು ಹೋಗುತ್ತಿದೆಯೇ?"
        },
        "options": [
            {"value": "continuous_nonstop", "label_en": "Continuous without relief", "label_hi": "लगातार बिना रुके बनी हुई है"},
            {"value": "intermittent_waves", "label_en": "Comes and goes in waves/spasms", "label_hi": "रुक-रुक कर लहरों की तरह आती है"},
            {"value": "worse_morning", "label_en": "Worse in morning on waking up", "label_hi": "सुबह उठने पर ज्यादा होती है"},
            {"value": "worse_night", "label_en": "Worse at night or while sleeping", "label_hi": "रात में या सोने पर ज्यादा होती है"},
            {"value": "post_meals", "label_en": "Occurs mostly after eating food", "label_hi": "खाना खाने के बाद ज्यादा होती है"}
        ]
    },
    {
        "step_id": "exacerbating_relieving",
        "clinical_field": "exacerbating_relieving",
        "question": {
            "en": "What makes it worse, and what gives you relief?",
            "hi": "किस चीज़ से तकलीफ बढ़ती है और किससे आराम मिलता है?",
            "mr": "कशाने त्रास वाढतो आणि कशाने आराम मिळतो?",
            "ta": "எதனால் அதிகரிக்கிறது மற்றும் எதனால் குறைகிறது?",
            "te": "దేని వలన పెరుగుతుంది, దేని వలన తగ్గుతుంది?",
            "bn": "কিসে বাড়ে এবং কিসে উপশম হয়?",
            "gu": "શેનાથી વધે છે અને શેનાથી રાહત મળે છે?",
            "kn": "ಯಾವುದರಿಂದ ಹೆಚ್ಚಾಗುತ್ತದೆ ಮತ್ತು ಯಾವುದರಿಂದ ಕಡಿಮೆಯಾಗುತ್ತದೆ?"
        },
        "options": [
            {"value": "worse_walking_climbing", "label_en": "Worse on walking/stairs; relieved by resting", "label_hi": "चलने या सीढ़ियां चढ़ने पर बढ़ता है; आराम करने पर कम होता है"},
            {"value": "worse_deep_breath", "label_en": "Worse on deep breathing or coughing", "label_hi": "गहरी सांस लेने या खांसने पर बढ़ता है"},
            {"value": "worse_lying_flat", "label_en": "Worse when lying flat; better sitting up", "label_hi": "सीधे लेटने पर बढ़ता है; बैठ जाने पर आराम मिलता है"},
            {"value": "relieved_food_antacid", "label_en": "Relieved by eating food or taking antacids", "label_hi": "कुछ खाने या एंटासिड दवा लेने से आराम मिलता है"},
            {"value": "worse_movement_joints", "label_en": "Worse on joint movement; better with warmth/rest", "label_hi": "हिलने-डुलने पर बढ़ता है; सिकाई या आराम से ठीक होता है"},
            {"value": "no_specific_factor", "label_en": "No clear pattern or change", "label_hi": "कोई खास फर्क नहीं पड़ता"}
        ]
    },
    {
        "step_id": "severity",
        "clinical_field": "severity_score",
        "question": {
            "en": "On a scale of 1 to 10, how severe is your pain/discomfort right now?",
            "hi": "1 से 10 के पैमाने पर, अभी आपकी तकलीफ कितनी गंभीर है? (10 = असहनीय)",
            "mr": "1 ते 10 च्या स्केलवर, तुमची वेदना किती तीव्र आहे?",
            "ta": "1 முதல் 10 வரையிலான அளவில், உங்கள் வலி எவ்வளவு தீவிரமானது?",
            "te": "1 నుండి 10 స్కేలులో, మీ నొప్పి ఎంత తీవ్రంగా ఉంది?",
            "bn": "১ থেকে ১০ এর স্কেলে আপনার ব্যথা কতটা তীব্র?",
            "gu": "1 થી 10 ના સ્કેલ પર તમારો દુખાવો કેટલો તીવ્ર છે?",
            "kn": "1 ರಿಂದ 10 ರ ಪ್ರಮಾಣದಲ್ಲಿ ನಿಮ್ಮ ನೋವು ಎಷ್ಟು ತೀವ್ರವಾಗಿದೆ?"
        },
        "options": [
            {"value": "2", "label_en": "Mild (1 - 3): Noticeable but easy to bear", "label_hi": "हल्का (1 - 3): हल्का फुल्का, सहने योग्य"},
            {"value": "5", "label_en": "Moderate (4 - 6): Distracting, interferes with tasks", "label_hi": "मध्यम (4 - 6): कामकाज में रुकावट डालने वाला"},
            {"value": "8", "label_en": "Severe (7 - 8): Very painful, hard to focus", "label_hi": "गंभीर (7 - 8): बहुत तेज, बर्दाश्त से बाहर"},
            {"value": "10", "label_en": "Critical / Excruciating (9 - 10): Worst pain imaginable", "label_hi": "अत्यंत गंभीर (9 - 10): जीवन का सबसे असहनीय दर्द"}
        ]
    }
]

class DialogueEngine:
    @staticmethod
    def get_chief_complaints(language: str = "en") -> List[Dict[str, Any]]:
        result = []
        for c in CHIEF_COMPLAINTS:
            lang_key = f"name_{language}" if f"name_{language}" in c else "name_en"
            item = dict(c)
            item["name"] = c.get(lang_key, c["name_en"])
            result.append(item)
        return result

    @staticmethod
    def get_socrates_question(step_index: int, language: str = "en") -> Optional[Dict[str, Any]]:
        if 0 <= step_index < len(SOCRATES_STEPS):
            step = SOCRATES_STEPS[step_index]
            q_text = step["question"].get(language, step["question"]["en"])
            
            # Formatted options for the requested language with full multilingual labels preserved
            formatted_options = []
            for opt in step["options"]:
                label_key = f"label_{language}" if f"label_{language}" in opt else "label_en"
                opt_dict = dict(opt)
                opt_dict["label"] = opt.get(label_key, opt["label_en"])
                formatted_options.append(opt_dict)

            return {
                "step_index": step_index,
                "total_steps": len(SOCRATES_STEPS),
                "step_id": step["step_id"],
                "clinical_field": step["clinical_field"],
                "question": step["question"],
                "question_text": q_text,
                "options": formatted_options
            }
        return None

    @staticmethod
    def parse_voice_transcript(transcript: str, chief_complaint: Optional[str] = None) -> Dict[str, Any]:
        """
        Extracts SOCRATES clinical elements from raw spoken Indian voice transcript (Hindi/English/Hinglish).
        """
        text = transcript.lower()
        extracted: Dict[str, Any] = {
            "raw_transcript": transcript,
            "detected_keywords": [],
            "socrates_updates": {}
        }
        
        # 1. Onset patterns
        if re.search(r"(आज|today|सुबह से|morning|अचानक|sudden|2 घंटे|hour)", text):
            extracted["socrates_updates"]["onset"] = "Sudden onset today / recent hours"
            extracted["detected_keywords"].append("Recent/Sudden Onset")
        elif re.search(r"(2 दिन|दो दिन|2 days|कल से|yesterday|3 दिन|3 days)", text):
            extracted["socrates_updates"]["onset"] = "2 to 3 days duration"
            extracted["detected_keywords"].append("2-3 Days Duration")
        elif re.search(r"(हफ्ते|week|महीने|month|साल|years)", text):
            extracted["socrates_updates"]["onset"] = "Sub-acute or chronic duration"
            extracted["detected_keywords"].append("Chronic Duration")

        # 2. Character patterns
        if re.search(r"(भारी|भारीपन|heavy|tight|दबाव|pressure|जकड़न|squeez)", text):
            extracted["socrates_updates"]["character"] = "Heavy pressure / Tightness / Squeezing"
            extracted["detected_keywords"].append("Heavy/Tight Character")
        elif re.search(r"(तेज़|sharp|चुभन|stab|कांटा|needle)", text):
            extracted["socrates_updates"]["character"] = "Sharp / Stabbing / Pricking"
            extracted["detected_keywords"].append("Sharp Character")
        elif re.search(r"(जलन|burn|acid|खट्टी|tezaab)", text):
            extracted["socrates_updates"]["character"] = "Burning / Acidic sensation"
            extracted["detected_keywords"].append("Burning Character")
        elif re.search(r"(धड़क|throbbing|टीस|pulse)", text):
            extracted["socrates_updates"]["character"] = "Throbbing / Pulsatile"
            extracted["detected_keywords"].append("Throbbing Character")

        # 3. Radiation patterns
        if re.search(r"(बाएं हाथ|बायां हाथ|left arm|shoulder|कंधा|जबड़ा|jaw|गर्दन|neck)", text):
            extracted["socrates_updates"]["radiation"] = "Radiates to left arm, shoulder, or jaw"
            extracted["detected_keywords"].append("Radiation to Left Arm/Jaw")
        elif re.search(r"(पीठ|कमर|back|spine)", text):
            extracted["socrates_updates"]["radiation"] = "Radiates to back"
            extracted["detected_keywords"].append("Radiation to Back")

        # 4. Association patterns
        associations = []
        if re.search(r"(पसीना|sweat|sweating)", text):
            associations.append("Profuse sweating")
            extracted["detected_keywords"].append("Sweating")
        if re.search(r"(सांस फूल|घबराहट|breathless|dyspnea|short of breath)", text):
            associations.append("Shortness of breath")
            extracted["detected_keywords"].append("Breathlessness")
        if re.search(r"(उल्टी|जी मिचलाना|vomit|nausea)", text):
            associations.append("Nausea/Vomiting")
            extracted["detected_keywords"].append("Nausea/Vomiting")
        if re.search(r"(चक्कर|dizzy|giddiness|बेहोशी|faint)", text):
            associations.append("Dizziness/Giddiness")
            extracted["detected_keywords"].append("Dizziness")
        if re.search(r"(बुखार|fever|ताप|कंपकंपी|chill)", text):
            associations.append("Fever with chills")
            extracted["detected_keywords"].append("Fever")
            
        if associations:
            extracted["socrates_updates"]["associations"] = associations

        # 5. Severity patterns
        if re.search(r"(बहुत ज्यादा|असहनीय|unbearable|severe|10|9|8)", text):
            extracted["socrates_updates"]["severity_score"] = 9
            extracted["detected_keywords"].append("Severe Pain (Score 9/10)")
        elif re.search(r"(मध्यम|moderate|5|6|7)", text):
            extracted["socrates_updates"]["severity_score"] = 6
        elif re.search(r"(हल्का|mild|thoda|1|2|3)", text):
            extracted["socrates_updates"]["severity_score"] = 3

        # Promote socrates_updates to top-level extracted keys for easy access
        for k, v in extracted["socrates_updates"].items():
            extracted[k] = v

        return extracted

dialogue_engine = DialogueEngine()
