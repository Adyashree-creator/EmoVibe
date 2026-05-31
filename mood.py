import os
import pickle
import re
import requests
from typing import Dict, Tuple, Any

# Path to the ML model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

# Core vibes mapping
CORE_VIBES = {
    "happy": ["happy", "joyful", "hopeful", "proud", "optimistic", "grateful", "cheerful", "delighted", "content", "satisfied", "ecstatic", "elated", "triumphant", "amused", "pleased", "glad"],
    "sad": ["sad", "grief-stricken", "lonely", "depressed", "heartbroken", "disappointed", "gloomy", "sorrowful", "melancholy", "regretful", "hopeless", "dejected", "unhappy", "empty", "miserable"],
    "anxious": ["anxious", "anxiety", "nervous", "stressed", "panicky", "overwhelmed", "fearful", "worried", "apprehensive", "uneasy", "restless", "insecure", "terrified", "dreadful", "tense", "shy", "embarrassed", "guilty", "ashamed"],
    "angry": ["angry", "furious", "irate", "resentful", "frustrated", "annoyed", "bitter", "livid", "indignant", "hostile", "rageful", "pissed", "mad", "irritated", "jealous", "disgusted"],
    "romantic": ["loving", "affectionate", "passionate", "smitten", "longing", "fond", "tender", "infatuated"],
    "energetic": ["energetic", "excited", "enthusiastic", "pumped", "hyper", "vibrant", "playful", "wild", "motivated", "unstoppable", "buzzing", "alive", "dating", "anticipating", "giddy", "empowered", "inspired"],
    "lazy": ["lazy", "tired", "sleepy", "exhausted", "bored", "apathetic", "lethargic", "sluggish", "fatigued"],
    "neutral": ["neutral", "calm", "indifferent", "peaceful", "thoughtful", "serene", "relaxed", "unbothered", "balanced", "stable", "nostalgic", "curious", "surprised", "shocked", "confused"]
}

# Reverse mapping from fine-grained emotion to core vibe
FINE_TO_CORE = {}
for core, fine_list in CORE_VIBES.items():
    for fine in fine_list:
        FINE_TO_CORE[fine] = core

# 100+ fine-grained emotion keywords dictionary
FINE_EMOTION_KEYWORDS = {
    # HAPPY spectrum
    "joyful": ["joyful", "joy", "glee", "happy"],
    "hopeful": ["hopeful", "hope", "optimistic about"],
    "proud": ["proud", "pride", "accomplished"],
    "optimistic": ["optimistic", "positive attitude", "bright future"],
    "grateful": ["grateful", "gratitude", "thankful", "blessed"],
    "cheerful": ["cheerful", "cheery", "sunny disposition"],
    "delighted": ["delighted", "thrilled", "overjoyed"],
    "content": ["content", "satisfied", "pleased"],
    "ecstatic": ["ecstatic", "elated", "euphoric", "over the moon"],
    "triumphant": ["triumphant", "victorious", "won", "succeeded"],
    "amused": ["amused", "funny", "laugh", "laughing"],
    
    # SAD spectrum
    "grief-stricken": ["grief", "mourning", "devastated"],
    "lonely": ["lonely", "alone", "isolated", "no one to talk to"],
    "depressed": ["depressed", "depression", "miserable", "heavy heart"],
    "heartbroken": ["heartbroken", "broken heart", "heart break"],
    "disappointed": ["disappointed", "let down", "disappointment"],
    "gloomy": ["gloomy", "dark days", "dreary"],
    "sorrowful": ["sorrowful", "sorrow", "grief"],
    "melancholy": ["melancholy", "wistful", "pensive sadness"],
    "regretful": ["regret", "regretful", "sorry about", "wish I hadn't"],
    "hopeless": ["hopeless", "giving up", "no way out"],
    "dejected": ["dejected", "downcast", "low spirits"],
    
    # ANXIOUS spectrum
    "nervous": ["nervous", "nervousness", "butterflies in my stomach", "jittery"],
    "stressed": ["stressed", "stress", "pressure", "deadlines", "deadline"],
    "panicky": ["panicky", "panic", "panicking", "racing heart"],
    "overwhelmed": ["overwhelmed", "too much", "cannot cope"],
    "fearful": ["fearful", "fear", "scared of"],
    "worried": ["worried", "worry", "worrying"],
    "apprehensive": ["apprehensive", "uneasy about", "fearful of future"],
    "uneasy": ["uneasy", "uncomfortable", "unsettled"],
    "restless": ["restless", "cannot sleep", "tossing and turning"],
    "terrified": ["terrified", "frightened", "scared to death"],
    
    # ANGRY spectrum
    "furious": ["furious", "fury", "livid", "fuming"],
    "irate": ["irate", "extremely angry", "enraged"],
    "resentful": ["resentful", "resentment", "bitter toward"],
    "frustrated": ["frustrated", "frustration", "fed up"],
    "annoyed": ["annoyed", "irritated", "bothered", "pesky"],
    "hostile": ["hostile", "aggressive", "confrontational"],
    "rageful": ["rage", "rageful", "outrage"],
    
    # ROMANTIC spectrum (deep connection, not anticipation)
    "loving": ["loving", "love my", "adore my", "in love"],
    "affectionate": ["affectionate", "warm feeling", "caring for"],
    "passionate": ["passionate", "passion", "intense love"],
    "smitten": ["smitten", "crush on", "head over heels"],
    "longing": ["longing", "yearning", "missing my partner", "miss him", "miss her"],
    "tender": ["tender", "gentle love", "soft spot"],
    
    # ENERGETIC / ANTICIPATORY spectrum
    "dating": ["going on a date", "i have a date", "date tonight", "date tonight", "first date", "second date"],
    "anticipating": ["anticipating", "looking forward to", "can't wait for", "countdown", "pumped for tonight"],
    "giddy": ["giddy", "butterflies", "so excited", "on cloud nine"],
    "excited": ["excited", "excitement", "cannot wait", "thrilled"],
    "enthusiastic": ["enthusiastic", "eager", "keen", "raring to go"],
    "pumped": ["pumped", "ready to go", "fired up", "amped up"],
    "hyper": ["hyper", "hyperactive", "too much energy"],
    "vibrant": ["vibrant", "full of life", "radiant"],
    "playful": ["playful", "mischievous", "fun-loving"],
    "wild": ["wild", "crazy night", "adventurous"],
    "motivated": ["motivated", "driven", "determined"],
    "empowered": ["empowered", "powerful", "invincible", "strong today"],
    "inspired": ["inspired", "inspiration", "creative spark", "motivated by"],
    
    # LAZY spectrum
    "tired": ["tired", "exhausted", "sleepy", "fatigued"],
    "bored": ["bored", "boredom", "nothing to do"],
    "apathetic": ["apathetic", "do not care", "indifferent"],
    "lethargic": ["lethargic", "no energy", "sluggish"],
    "fatigued": ["fatigued", "drained", "worn out"],
    
    # NEUTRAL / REFLECTIVE spectrum
    "calm": ["calm", "serene", "tranquil"],
    "indifferent": ["indifferent", "neutral", "does not matter"],
    "peaceful": ["peaceful", "at peace", "harmonious"],
    "thoughtful": ["thoughtful", "reflective", "contemplative"],
    "relaxed": ["relaxed", "relaxing", "chilled out"],
    "unbothered": ["unbothered", "carefree", "untroubled"],
    "nostalgic": ["nostalgic", "nostalgia", "reminiscing", "old memories", "throwback"],
    "curious": ["curious", "wondering about", "fascinated", "intrigued"],
    "surprised": ["surprised", "surprised me", "did not expect", "unexpected"],
    "shocked": ["shocked", "cannot believe", "mind blown", "jaw dropped"],
    "confused": ["confused", "do not understand", "lost", "unsure what"],
    
    # SOCIAL / COMPLEX emotions
    "shy": ["shy", "bashful", "embarrassed to talk", "too nervous to speak"],
    "embarrassed": ["embarrassed", "embarrassment", "so awkward", "cringe"],
    "guilty": ["guilty", "guilt", "i feel bad", "i should not have"],
    "ashamed": ["ashamed", "shame", "feel ashamed"],
    "jealous": ["jealous", "jealousy", "envious", "envy"],
    "disgusted": ["disgusted", "disgust", "gross", "revolting"]
}

# Compile regex patterns for fine-grained matching
FINE_PATTERNS = {
    emotion: re.compile(r"\b(" + "|".join(words) + r")\b", re.IGNORECASE)
    for emotion, words in FINE_EMOTION_KEYWORDS.items()
}

def translate_and_detect_language(text: str) -> Tuple[str, str]:
    """Translate text to English and detect the original language code."""
    if not text.strip():
        return "", "en"
    
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": "en",
        "dt": "t",
        "q": text
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            translated_segments = []
            if data and data[0]:
                for segment in data[0]:
                    if segment and segment[0]:
                        translated_segments.append(segment[0])
            translated_text = "".join(translated_segments)
            
            lang_code = "en"
            if len(data) > 2 and isinstance(data[2], str):
                lang_code = data[2]
            
            return translated_text, lang_code
    except Exception as e:
        print(f"Translation error: {e}")
        
    return text, "en"

def analyze_with_gemini(text: str, api_key: str) -> Dict[str, Any]:
    """Call Gemini API to perform 100+ fine-grained emotion analysis."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        "You are an empathetic wellness assistant. "
        f"Analyze the mood of this journal entry: '{text}'. "
        "Respond with a single JSON object containing exactly three fields:\n"
        "1. 'emotion': a single word representing the exact fine-grained emotion from a wide spectrum of 100+ human emotions (e.g., 'hopeful', 'nostalgic', 'apprehensive', 'lonely', 'excited', 'loving', 'frustrated').\n"
        "2. 'explanation': a brief, warm, comforting sentence acknowledging their feeling.\n"
        "3. 'core_vibe': map the emotion to exactly one of these 8 core categories: happy, sad, anxious, angry, neutral, romantic, energetic, lazy.\n"
        "Do not include any formatting markdown like ```json, just the raw JSON string."
    )
    
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    
    try:
        res = requests.post(url, headers=headers, json=data, timeout=8)
        if res.status_code == 200:
            content = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            # Clean potential markdown markers
            if content.startswith("```"):
                content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
    except Exception as e:
        print(f"Gemini API analysis failed: {e}")
        
    return {}

EXPLANATIONS = {
    # Dating / anticipatory
    "dating":       "How exciting — enjoy every moment of your date tonight! 💑",
    "anticipating": "The anticipation is half the thrill! Here's your hype-up playlist.",
    "giddy":        "You're floating on cloud nine — love that energy! 🎈",
    # Happy
    "joyful":       "Your joy is absolutely radiant — let's amplify it! 😄",
    "hopeful":      "It's wonderful to feel hopeful; keep looking forward to bright things. 🌟",
    "proud":        "You should be proud — you've earned this moment! 🏆",
    "optimistic":   "That positive outlook is your superpower. Shine on! ☀️",
    "grateful":     "Gratitude is the highest vibration. You're in a beautiful space. 🙏",
    "ecstatic":     "Pure ecstasy — let's ride this wave together! 🥳",
    "triumphant":   "You won! Celebrate this victory, you deserve it! 🎉",
    "amused":       "Laughter really is the best medicine. Keep smiling! 😂",
    "content":      "That quiet contentment is precious — let's wrap it in music. 😌",
    # Sad
    "lonely":       "Feeling lonely is hard, but you are not alone in spirit. Here's some cozy company. 🌧️",
    "heartbroken":  "A broken heart hurts deeply. Let the music hold you gently. 💔",
    "melancholy":   "Melancholy has a beauty of its own. Let's sit with it together. 🍂",
    "nostalgic":    "Nostalgia is bittersweet magic. Let the memories wash over you. ✨",
    "depressed":    "Dark days are hard. Let this music be a gentle light. 💙",
    "disappointed": "Disappointment is real and valid. Take a breath — things will shift. 😔",
    "hopeless":     "Even in the darkest moments, a song can crack a small light in. 💫",
    "grief-stricken": "Grief is love with nowhere to go. Let the music carry it. 💔",
    # Anxious
    "excited":      "Your excitement is contagious! Let's match that wonderful energy. ⚡",
    "nervous":      "Take a deep breath — you've got this. Let's calm those nerves. 😰",
    "stressed":     "Stress is a signal to pause. Let the music give you a break. 💫",
    "overwhelmed":  "One breath at a time. You're stronger than you feel right now. 🫠",
    "worried":      "It's okay to worry — but don't let it live rent-free. Here's some calm. 😌",
    "panicky":      "Breathe in, breathe out. You're safe. Let this music ground you. 💙",
    "fearful":      "Fear is a signal, not a sentence. Let's ease it with sound. 😨",
    "restless":     "That restless energy needs an outlet — here's your release. 😣",
    # Angry / frustrated
    "frustrated":   "Frustration is valid. Here's something to let it out. 🔥",
    "angry":        "It is healthy to acknowledge anger. Take your time to release it safely. 🔥",
    "furious":      "Pure fire energy — channel it into something powerful. 🤬",
    "jealous":      "Jealousy means you care. Let the music help you refocus inward. 💪",
    "annoyed":      "That little irritation is totally understandable. Let's shake it off. 🙄",
    "resentful":    "Resentment is a heavy load. Let the music help you put it down. 😤",
    # Romantic
    "loving":       "Love in full bloom — here's music to match that warmth. ❤️",
    "affectionate": "Warm and tender feelings — this playlist hugs back. 🥰",
    "passionate":   "That deep passion deserves an equally intense soundtrack. 💕",
    "smitten":      "Head over heels — let's float with you! 😍",
    "longing":      "Missing someone is its own kind of love. Here's music to hold you. 💭",
    "tender":       "That gentle, soft feeling — let the music be just as tender. 🫶",
    # Energetic
    "motivated":    "That drive is everything! Here's your power-up soundtrack. 🎯",
    "empowered":    "You're unstoppable right now — own it! 💪",
    "inspired":     "Creative energy flowing — let's keep that spark alive. 💡",
    "pumped":       "You are FIRED UP — this playlist matches your energy! 💪",
    "vibrant":      "Radiating life and light — here's your vibrant soundtrack. ✨",
    "playful":      "Keep that playful spark alive — let's dance! 🎈",
    "wild":         "Wild and free — no rules tonight. Let the music match! 🌪️",
    # Lazy
    "tired":        "It's completely okay to feel tired. Take some rest and take it easy. 😴",
    "bored":        "Boredom is just creativity waiting to happen. Let's shake things up. 🎈",
    "lethargic":    "Low energy is okay too — here's some soft, easy music. 🐌",
    "fatigued":     "Rest is not laziness. Let this music hold your tired soul. 😮‍💨",
    # Calm / Neutral
    "calm":         "You're in a beautiful state of calm. Let's maintain this peace. 🧘",
    "peaceful":     "Peace is your superpower right now. This music will deepen it. ☮️",
    "curious":      "Curiosity is the beginning of all great adventures. 🔍",
    "thoughtful":   "You're in a reflective mood — perfect for some introspective sounds. 🤔",
    "relaxed":      "Chilled out and loving it — here's your easy listening. 😎",
    "nostalgic":    "Nostalgia is bittersweet magic. Let the memories wash over you. 🎞️",
    "unbothered":   "Totally carefree — this playlist matches your vibe. 🤷",
    # Social / Complex
    "shy":          "It's okay to be shy — let the music speak for you. 🌸",
    "embarrassed":  "Everyone has those moments. Music to help you brush it off. 😊",
    "guilty":       "Acknowledging guilt takes courage. Let's give you space to breathe. 🙏",
    "ashamed":      "Shame is heavy — let this music lighten the load a little. 😔",
    "jealous":      "Jealousy means you care deeply. Redirect that energy inward. 😒",
    "disgusted":    "Sometimes you just need to vent — this playlist lets you. 🤢",
    "confused":     "It's okay not to have all the answers. Let's just feel the music. 😵‍💫",
    "surprised":    "Life loves to surprise us! Here's a playlist for the unexpected. 😲",
}

def detect_mood_probabilities(english_text: str, gemini_key: str = ""):
    """
    Analyze mood and return a LIST of (fine_emotion, explanation, core_vibe) tuples.
    The list is sorted by match strength — primary emotion first, then secondary, etc.
    This enables multi-mood blending (e.g. happy + energetic simultaneously).
    """
    # 1. If Gemini API Key is provided, use it for 100+ emotions
    if gemini_key and len(gemini_key) > 10:
        gemini_result = analyze_with_gemini(english_text, gemini_key)
        if gemini_result and "emotion" in gemini_result and "core_vibe" in gemini_result:
            fine = gemini_result["emotion"].lower()
            expl = gemini_result.get("explanation", EXPLANATIONS.get(fine, "I hear you and am here to support you."))
            core = gemini_result["core_vibe"].lower()
            return [(fine, expl, core)]

    # 2. Local keyword matching — find ALL emotions present in the text
    matched_fines = {}
    for emotion, pattern in FINE_PATTERNS.items():
        matches = len(pattern.findall(english_text))
        if matches > 0:
            matched_fines[emotion] = matches

    if matched_fines:
        # Sort all matched emotions by match count (strongest first)
        sorted_fines = sorted(matched_fines.items(), key=lambda x: x[1], reverse=True)

        results = []
        seen_cores = set()
        for fine_em, count in sorted_fines:
            core = FINE_TO_CORE.get(fine_em, "neutral")
            expl = EXPLANATIONS.get(fine_em, "Acknowledging your feeling of {}.".format(fine_em))
            # Include if: it's the first emotion, OR its core vibe hasn't been seen yet
            # (avoids showing 5 "happy" sub-emotions — keeps one per core vibe)
            if not results or core not in seen_cores:
                results.append((fine_em, expl, core))
                seen_cores.add(core)
            # Cap at 3 distinct moods max
            if len(results) >= 3:
                break

        return results

    # 3. Fallback to Local ML Model (8 classes) — return top 2 if secondary is significant
    ml_probs = {}
    if os.path.exists(MODEL_PATH):
        try:
            with open(MODEL_PATH, "rb") as f:
                model = pickle.load(f)
            proba = model.predict_proba([english_text])[0]
            classes = model.named_steps['classifier'].classes_
            ml_probs = dict(zip(classes, proba))
        except Exception as e:
            print("ML Model error: {}".format(e))

    emotions = ["happy", "sad", "anxious", "angry", "neutral", "romantic", "energetic", "lazy"]
    probs = {em: ml_probs.get(em, 1.0 / len(emotions)) for em in emotions}
    sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)

    results = []
    for core_em, prob in sorted_probs[:3]:
        if prob > 0.12 or not results:   # always include at least the top one
            expl = EXPLANATIONS.get(core_em, "Acknowledging your feeling of {}.".format(core_em))
            results.append((core_em, expl, core_em))
    return results
