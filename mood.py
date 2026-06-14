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

# 500+ fine-grained emotion keywords dictionary (expanded)
FINE_EMOTION_KEYWORDS = {
    # ═══════════════════ HAPPY SPECTRUM ═══════════════════
    "joyful": ["joyful", "joy", "glee", "happy", "so happy", "feeling happy", "really happy",
               "happiest", "on top of the world", "best day", "best feeling", "feel great",
               "feeling wonderful", "wonderful day", "amazing day", "perfect day", "good vibes",
               "feeling blessed", "life is good", "life is beautiful", "smiling", "can't stop smiling",
               "beaming", "walking on sunshine", "loving life", "mast hai", "maza aa gaya",
               "bohot khush", "bahut accha", "kya baat hai"],
    "hopeful": ["hopeful", "hope", "optimistic about", "things will get better", "better days ahead",
                "light at the end", "looking up", "turning around", "fingers crossed",
                "believing in myself", "keeping faith", "positive vibes", "good feeling about",
                "umeed", "umeed hai", "sab theek hoga"],
    "proud": ["proud", "pride", "accomplished", "achieved", "achievement", "nailed it",
              "crushed it", "killed it", "aced it", "made it", "did it", "so proud of myself",
              "proud moment", "parents are proud", "proved them wrong", "topped",
              "first rank", "got selected", "got promoted", "garv hai"],
    "optimistic": ["optimistic", "positive attitude", "bright future", "good things coming",
                   "everything will be fine", "sab badhiya", "acche din", "new beginnings",
                   "fresh start", "turning a new leaf", "excited about future"],
    "grateful": ["grateful", "gratitude", "thankful", "blessed", "count my blessings",
                 "so grateful", "appreciate", "lucky to have", "thank god", "shukar hai",
                 "dhanyavaad", "grateful for everything", "blessed life"],
    "cheerful": ["cheerful", "cheery", "sunny disposition", "bright mood", "upbeat",
                 "in a good mood", "feeling chirpy", "full of smiles", "lighthearted"],
    "delighted": ["delighted", "thrilled", "overjoyed", "over the moon", "couldn't be happier",
                  "absolutely thrilled", "so pleased", "made my day", "best news",
                  "good news", "great news", "amazing news"],
    "content": ["content", "satisfied", "pleased", "at ease", "comfortable", "cozy",
                "warm and fuzzy", "peaceful happiness", "quietly happy", "sukoon"],
    "ecstatic": ["ecstatic", "elated", "euphoric", "over the moon", "flying high",
                 "on cloud nine", "absolutely overjoyed", "best thing ever", "unbelievable",
                 "pagal ho gaya khushi se"],
    "triumphant": ["triumphant", "victorious", "won", "succeeded", "champion", "winner",
                   "victory", "conquered", "overcame", "beat it", "first place", "gold medal",
                   "jeet gaya", "jeet gayi"],
    "amused": ["amused", "funny", "laugh", "laughing", "hilarious", "cracking up",
               "lol", "rofl", "lmao", "can't stop laughing", "dying of laughter",
               "comedy", "joke", "haha", "hahaha", "too funny", "hasna aa raha hai",
               "bahut funny", "mazaak", "hansi nahi ruk rahi"],

    # ═══════════════════ SAD SPECTRUM ═══════════════════
    "grief-stricken": ["grief", "mourning", "devastated", "lost someone", "death",
                       "passed away", "funeral", "no more", "gone forever", "rest in peace",
                       "rip", "miss them so much", "never coming back", "kho diya"],
    "lonely": ["lonely", "alone", "isolated", "no one to talk to", "feel so alone",
               "nobody cares", "no friends", "left out", "abandoned", "ignored",
               "invisible", "no one understands", "koi nahi hai", "akela", "akeli",
               "all by myself", "nobody texts me", "sitting alone", "eating alone"],
    "depressed": ["depressed", "depression", "miserable", "heavy heart", "dark place",
                  "don't want to live", "what's the point", "nothing matters",
                  "can't get out of bed", "crying for no reason", "empty inside",
                  "numb", "feel nothing", "dead inside", "life sucks",
                  "hate my life", "broken", "shattered", "udaas"],
    "heartbroken": ["heartbroken", "broken heart", "heart break", "breakup", "broke up",
                    "dumped", "left me", "moved on", "ex", "cheated on me",
                    "trust broken", "betrayed", "dil toot gaya", "dil toota",
                    "she left me", "he left me", "relationship over", "it's over"],
    "disappointed": ["disappointed", "let down", "disappointment", "expected better",
                     "not what i expected", "failed", "failure", "didn't work out",
                     "waste of time", "all for nothing", "umeed toot gayi"],
    "gloomy": ["gloomy", "dark days", "dreary", "grey", "dull day", "bleak",
               "everything looks dark", "no sunshine", "feeling low", "down today"],
    "sorrowful": ["sorrowful", "sorrow", "grief", "deep sadness", "weeping",
                  "crying my eyes out", "tears won't stop", "sobbing"],
    "melancholy": ["melancholy", "wistful", "pensive sadness", "bittersweet",
                   "missing old times", "those days are gone", "used to be happy",
                   "things were better before", "purane din"],
    "regretful": ["regret", "regretful", "sorry about", "wish I hadn't", "if only",
                  "should have", "shouldn't have", "my mistake", "i messed up",
                  "i ruined it", "take it back", "kaash", "galti ho gayi"],
    "hopeless": ["hopeless", "giving up", "no way out", "no hope", "what's the use",
                 "pointless", "never going to work", "impossible", "stuck forever",
                 "no solution", "koi raasta nahi"],
    "dejected": ["dejected", "downcast", "low spirits", "deflated", "crushed",
                 "beaten down", "lost all hope", "totally down"],
    "homesick": ["homesick", "miss home", "miss my family", "miss my mom", "miss my dad",
                 "miss my parents", "want to go home", "far from home", "ghar ki yaad",
                 "mummy ki yaad", "papa ki yaad", "ghar jaana hai"],

    # ═══════════════════ ANXIOUS SPECTRUM ═══════════════════
    "nervous": ["nervous", "nervousness", "butterflies in my stomach", "jittery",
                "shaking", "trembling", "can't sit still", "fidgeting",
                "stomach is churning", "sweating", "heart pounding", "darr lag raha hai"],
    "stressed": ["stressed", "stress", "pressure", "deadlines", "deadline", "too much work",
                 "overloaded", "burnout", "burned out", "work pressure", "exam pressure",
                 "project deadline", "boss is angry", "submissions due", "assignment due",
                 "tension", "bahut tension", "kaam ka pressure", "padhai ka pressure"],
    "panicky": ["panicky", "panic", "panicking", "racing heart", "panic attack",
                "can't breathe", "freaking out", "losing it", "going crazy",
                "what do i do", "help me", "oh god", "oh no"],
    "overwhelmed": ["overwhelmed", "too much", "cannot cope", "drowning in work",
                    "can't handle", "everything at once", "juggling too much",
                    "losing my mind", "head is spinning", "so much to do",
                    "how will i manage", "kaise karungi", "kaise karunga", "bahut zyada"],
    "fearful": ["fearful", "fear", "scared of", "afraid", "frightened", "petrified",
                "dread", "dreading", "scared to death", "terrifying", "dar",
                "darr", "bahut dar lag raha"],
    "worried": ["worried", "worry", "worrying", "what if", "can't stop thinking",
                "overthinking", "keeps me up at night", "losing sleep over",
                "anxious about", "concerned about", "chinta", "fikar", "soch rahi hoon"],
    "apprehensive": ["apprehensive", "uneasy about", "fearful of future",
                     "not sure about", "hesitant", "second thoughts", "bad feeling about this"],
    "uneasy": ["uneasy", "uncomfortable", "unsettled", "something feels off",
               "weird feeling", "gut feeling", "doesn't feel right", "kuch gadbad hai"],
    "restless": ["restless", "cannot sleep", "tossing and turning", "insomnia",
                 "wide awake", "can't relax", "mind won't stop", "neend nahi aa rahi",
                 "chain nahi", "bechain"],
    "terrified": ["terrified", "frightened", "scared to death", "frozen with fear",
                  "nightmares", "horror", "shaking with fear"],
    "insecure": ["insecure", "not good enough", "self doubt", "compare myself",
                 "feel ugly", "feel fat", "feel stupid", "imposter", "fraud",
                 "don't belong", "not smart enough", "not pretty enough",
                 "everyone is better", "inferiority"],

    # ═══════════════════ ANGRY SPECTRUM ═══════════════════
    "furious": ["furious", "fury", "livid", "fuming", "boiling with anger",
                "blood is boiling", "seeing red", "lost my temper", "gussa"],
    "irate": ["irate", "extremely angry", "enraged", "outraged", "how dare",
              "this is unacceptable", "totally unfair"],
    "resentful": ["resentful", "resentment", "bitter toward", "holding a grudge",
                  "can't forgive", "will never forgive", "still angry about",
                  "maaf nahi karungi", "maaf nahi karunga"],
    "frustrated": ["frustrated", "frustration", "fed up", "sick of", "tired of this",
                   "had enough", "can't take it anymore", "done with this",
                   "nothing works", "why me", "tang aa gayi", "tang aa gaya",
                   "bahut ho gaya", "bas kar"],
    "annoyed": ["annoyed", "irritated", "bothered", "pesky", "getting on my nerves",
                "so annoying", "leave me alone", "stop it", "shut up",
                "pakau", "irritating", "bakwaas"],
    "hostile": ["hostile", "aggressive", "confrontational", "want to fight",
                "picking a fight", "war", "enemy"],
    "rageful": ["rage", "rageful", "outrage", "blind rage", "explosive anger",
                "smashed", "punched", "threw things", "screaming"],
    "betrayed": ["betrayed", "backstabbed", "stabbed in the back", "two-faced",
                 "fake friend", "lied to me", "used me", "took advantage",
                 "dhoka", "dhoka diya", "vishwaasghaat"],

    # ═══════════════════ ROMANTIC SPECTRUM ═══════════════════
    "loving": ["loving", "love my", "adore my", "in love", "i love you", "love you so much",
               "my love", "my everything", "soulmate", "better half", "pyaar",
               "mohabbat", "ishq", "meri jaan", "jaanu"],
    "affectionate": ["affectionate", "warm feeling", "caring for", "cuddle", "cuddling",
                     "hugging", "holding hands", "snuggling", "warm embrace",
                     "close to my heart", "dil ke kareeb"],
    "passionate": ["passionate", "passion", "intense love", "deeply in love",
                   "burning love", "fire in my heart", "crazy about", "mad about",
                   "can't live without", "obsessed with"],
    "smitten": ["smitten", "crush on", "head over heels", "falling for",
                "can't stop thinking about", "butterflies when i see",
                "love at first sight", "totally into", "pehli nazar mein"],
    "longing": ["longing", "yearning", "missing my partner", "miss him", "miss her",
                "miss you", "wish you were here", "long distance", "far away",
                "want to see you", "come back", "waiting for you",
                "tumhari yaad", "bahut yaad aa rahi hai", "tujhe miss kar raha",
                "tujhe miss kar rahi"],
    "tender": ["tender", "gentle love", "soft spot", "soft corner", "precious",
               "delicate feelings", "sweet love", "pure love"],
    "flirty": ["flirty", "flirting", "wink", "charming", "attractive", "hot",
               "handsome", "beautiful eyes", "cute smile", "checking out",
               "he's so cute", "she's so pretty", "aankhen", "nazrein mili"],

    # ═══════════════════ ENERGETIC / ANTICIPATORY SPECTRUM ═══════════════════
    "dating": ["going on a date", "i have a date", "date tonight", "first date",
               "second date", "dinner date", "coffee date", "movie date",
               "date with my crush", "getting ready for date", "what should i wear"],
    "anticipating": ["anticipating", "looking forward to", "can't wait for", "countdown",
                     "pumped for tonight", "tomorrow is the big day", "so close",
                     "almost there", "wait is killing me", "intezaar"],
    "giddy": ["giddy", "butterflies", "so excited", "on cloud nine", "squealing",
              "jumping with joy", "can't contain", "bursting with excitement"],
    "excited": ["excited", "excitement", "cannot wait", "thrilled", "yay", "woohoo",
                "let's go", "bring it on", "finally", "it's happening",
                "best news ever", "omg", "I can't believe it", "maza aayega",
                "bahut excited"],
    "enthusiastic": ["enthusiastic", "eager", "keen", "raring to go", "all in",
                     "passionate about", "love doing this", "can't wait to start"],
    "pumped": ["pumped", "ready to go", "fired up", "amped up", "let's do this",
               "game on", "beast mode", "on fire", "crushing it", "josh mein"],
    "hyper": ["hyper", "hyperactive", "too much energy", "bouncing off walls",
              "can't sit still", "wired", "buzzing", "electrified"],
    "vibrant": ["vibrant", "full of life", "radiant", "glowing", "shining",
                "sparkling", "alive", "blooming", "flourishing"],
    "playful": ["playful", "mischievous", "fun-loving", "silly", "goofing around",
                "pranking", "teasing", "having a blast", "masti", "dhamaal"],
    "wild": ["wild", "crazy night", "adventurous", "party", "partying", "dancing all night",
             "let loose", "going crazy", "living my best life", "yolo",
             "full on party", "pagalpanti"],
    "motivated": ["motivated", "driven", "determined", "focused", "goal", "hustle",
                  "grind", "working hard", "going after my dreams", "never give up",
                  "mehnat", "lage raho", "karna hai"],
    "empowered": ["empowered", "powerful", "invincible", "strong today", "unstoppable",
                  "nothing can stop me", "i am enough", "self love", "confident",
                  "queen energy", "king energy", "boss mode"],
    "inspired": ["inspired", "inspiration", "creative spark", "motivated by",
                 "idea struck", "eureka", "light bulb moment", "want to create",
                 "feeling artistic", "creative mood", "prerna"],

    # ═══════════════════ LAZY SPECTRUM ═══════════════════
    "tired": ["tired", "exhausted", "sleepy", "fatigued", "so tired", "dead tired",
              "need sleep", "need rest", "running on empty", "no energy left",
              "drained", "wiped out", "thak gayi", "thak gaya", "neend aa rahi hai"],
    "bored": ["bored", "boredom", "nothing to do", "so boring", "boring day",
              "bored to death", "killing time", "time pass", "bore ho raha",
              "bore ho rahi", "kya karoon", "kuch nahi ho raha"],
    "apathetic": ["apathetic", "do not care", "indifferent", "whatever",
                  "don't care anymore", "meh", "couldn't care less",
                  "farak nahi padta", "kuch farak nahi"],
    "lethargic": ["lethargic", "no energy", "sluggish", "dragging myself",
                  "heavy body", "can barely move", "so slow today"],
    "fatigued": ["fatigued", "drained", "worn out", "spent", "completely exhausted",
                 "running on fumes", "barely functioning", "zombie mode"],
    "lazy": ["lazy", "feeling lazy", "don't want to move", "couch potato",
             "Netflix and chill", "pajama day", "duvet day", "aalas", "aalsi"],

    # ═══════════════════ NEUTRAL / REFLECTIVE SPECTRUM ═══════════════════
    "calm": ["calm", "serene", "tranquil", "at peace", "inner peace",
             "zen", "meditation", "mindful", "centered", "grounded", "shaant"],
    "indifferent": ["indifferent", "neutral", "does not matter", "don't mind",
                    "no opinion", "neither here nor there", "kuch bhi"],
    "peaceful": ["peaceful", "at peace", "harmonious", "blissful silence",
                 "quiet evening", "nature walk", "sunset", "sunrise",
                 "birds chirping", "sukoon", "chain ki neend"],
    "thoughtful": ["thoughtful", "reflective", "contemplative", "deep thought",
                   "pondering", "wondering", "philosophical", "soul searching",
                   "thinking about life", "sochne lagi", "soch raha hoon"],
    "relaxed": ["relaxed", "relaxing", "chilled out", "laid back", "taking it easy",
                "no rush", "slow day", "easy going", "chill vibes", "chill kar raha",
                "chill kar rahi", "araam se"],
    "unbothered": ["unbothered", "carefree", "untroubled", "zero stress",
                   "not my problem", "living my life", "no drama",
                   "tension free", "bindaas"],
    "nostalgic": ["nostalgic", "nostalgia", "reminiscing", "old memories", "throwback",
                  "remember when", "those were the days", "childhood memories",
                  "old photos", "school days", "college days", "miss those days",
                  "purane din", "yaadein", "bachpan"],
    "curious": ["curious", "wondering about", "fascinated", "intrigued",
                "want to know", "interesting", "tell me more", "how does this work",
                "why is this", "jaanna hai"],
    "surprised": ["surprised", "surprised me", "did not expect", "unexpected",
                  "plot twist", "never saw that coming", "jaw dropped",
                  "i can't believe", "seriously", "for real", "sach mein"],
    "shocked": ["shocked", "cannot believe", "mind blown", "jaw dropped",
                "what just happened", "no way", "unbelievable", "kya hua",
                "yeh kaise", "hairan"],
    "confused": ["confused", "do not understand", "lost", "unsure what",
                 "makes no sense", "what is happening", "so confusing",
                 "mixed signals", "samajh nahi aa raha", "pata nahi kya ho raha"],

    # ═══════════════════ SOCIAL / COMPLEX EMOTIONS ═══════════════════
    "shy": ["shy", "bashful", "embarrassed to talk", "too nervous to speak",
            "introverted", "social anxiety", "don't want to talk to people",
            "prefer being alone", "hate crowds", "sharmili", "sharmila"],
    "embarrassed": ["embarrassed", "embarrassment", "so awkward", "cringe",
                    "cringeworthy", "mortified", "want to disappear", "face palm",
                    "how embarrassing", "sharam aa gayi"],
    "guilty": ["guilty", "guilt", "i feel bad", "i should not have",
               "conscience", "wrong thing", "hurt someone", "made a mistake",
               "feel terrible about", "galat kiya"],
    "ashamed": ["ashamed", "shame", "feel ashamed", "disgrace", "humiliated",
                "shamed", "public humiliation", "exposed"],
    "jealous": ["jealous", "jealousy", "envious", "envy", "why not me",
                "they have it all", "unfair", "comparison", "green with envy",
                "jalan", "jalti hoon", "jalta hoon"],
    "disgusted": ["disgusted", "disgust", "gross", "revolting", "nasty",
                  "yuck", "eww", "sick to my stomach", "repulsed"],
    "grateful_social": ["thank you friend", "best friends", "friendship goals",
                        "my bestie", "support system", "they were there for me",
                        "true friend", "dost", "yaar", "bhai", "saheli"],
    "overwhelmed_joy": ["tears of joy", "happy tears", "crying happy tears",
                        "so happy i could cry", "emotional", "touched",
                        "heart is full", "overwhelmed with happiness",
                        "khushi ke aansu"]
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
