import streamlit as st
import json
import os
import random
import requests
import hashlib

# Import translation & mood detection
import i18n
from i18n import t
import mood

st.set_page_config(page_title="EmoVibe – Your Mood, Your Vibe, Your Song", page_icon="🎵", layout="wide")

# ─── Supabase Config ─────────────────────────────────────────────────────────
SUPABASE_URL = "https://zzpbpnuoviifncksixbb.supabase.co"
SUPABASE_KEY = "sb_publishable_mwh9ejRv09TnEs368nMLUg_iv7iRimp"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ─── Helper Functions ─────────────────────────────────────────────────────────
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    check = requests.get(
        f"{SUPABASE_URL}/rest/v1/users",
        headers=HEADERS,
        params={"username": f"eq.{username}"}
    )
    if check.json():
        return False, "Username already taken. Please choose another."
    res = requests.post(
        f"{SUPABASE_URL}/rest/v1/users",
        headers=HEADERS,
        json={"username": username, "password_hash": hash_password(password)}
    )
    if res.status_code in [200, 201]:
        return True, "Account created successfully!"
    return False, "Something went wrong. Please try again."

def login_user(username, password):
    res = requests.get(
        f"{SUPABASE_URL}/rest/v1/users",
        headers=HEADERS,
        params={"username": f"eq.{username}", "password_hash": f"eq.{hash_password(password)}"}
    )
    return len(res.json()) > 0

def get_user_songs(username):
    res = requests.get(
        f"{SUPABASE_URL}/rest/v1/user_songs",
        headers=HEADERS,
        params={"username": f"eq.{username}", "order": "id.asc"}
    )
    return res.json() if res.status_code == 200 else []

def add_user_song(username, emotion, song_name, song_url):
    res = requests.post(
        f"{SUPABASE_URL}/rest/v1/user_songs",
        headers=HEADERS,
        json={"username": username, "emotion": emotion, "song_name": song_name, "song_url": song_url}
    )
    return res.status_code in [200, 201]

def delete_user_song(song_id):
    res = requests.delete(
        f"{SUPABASE_URL}/rest/v1/user_songs",
        headers=HEADERS,
        params={"id": f"eq.{song_id}"}
    )
    return res.status_code in [200, 204]

# ─── Load Local Config ────────────────────────────────────────────────────────
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "music_config.json")

def load_default_songs():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

# ─── Session State Init ───────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "lang_code" not in st.session_state:
    st.session_state.lang_code = "en"
if "detected_lang" not in st.session_state:
    st.session_state.detected_lang = ""

# Migration guard: clear stale healing_results if from old format
if "healing_results" in st.session_state and st.session_state.healing_results:
    if "primary_emotion" in st.session_state.healing_results:
        st.session_state.healing_results = None

# Apply locale initially
i18n.set_locale(st.session_state.lang_code)

# ─── LOGIN / REGISTER SCREEN ──────────────────────────────────────────────────
if not st.session_state.logged_in:
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #121214, #1a1a24);
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("🎵 EmoVibe")
    st.write("Your Mood, Your Vibe, Your Song — sign in to get your private playlist!")
    st.write("---")

    auth_option = st.radio("Select an option / Seleccione una opción / Choisissez une option / विकल्प चुनें", ["Login", "Create Account"], horizontal=True)

    if auth_option == "Login":
        st.subheader("Welcome back!")
        login_user_input = st.text_input("Username", key="login_user")
        login_pass_input = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if login_user(login_user_input, login_pass_input):
                st.session_state.logged_in = True
                st.session_state.username = login_user_input
                st.success(f"Welcome back, {login_user_input}! 🎉")
                st.rerun()
            else:
                st.error("Incorrect username or password.")
    else:
        st.subheader("Create your free account!")
        new_username = st.text_input("Choose a Username", key="reg_user")
        new_password = st.text_input("Choose a Password", type="password", key="reg_pass")
        if st.button("Create Account"):
            if new_username and new_password:
                success, msg = register_user(new_username, new_password)
                if success:
                    st.success(msg + " You can now login!")
                else:
                    st.error(msg)
            else:
                st.warning("Please fill in both fields.")

    st.stop()

# ─── MAIN APP (Logged In) ──────────────────────────────────────────────────────

# ─── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.title(f"👋 {t('welcome')} {st.session_state.username}!")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.lang_code = "en"
    st.session_state.detected_lang = ""
    st.rerun()

st.sidebar.write("---")

# UI Language Configuration
st.sidebar.subheader(f"🌐 {t('language')}")
lang_options = {
    "Auto-Detect": "auto",
    "English": "en",
    "Español": "es",
    "Français": "fr",
    "हिन्दी (Hindi)": "hi"
}
selected_lang_name = st.sidebar.selectbox(
    t("select_language"),
    list(lang_options.keys()),
    index=0 if st.session_state.lang_code == "en" else list(lang_options.values()).index(st.session_state.lang_code) if st.session_state.lang_code in lang_options.values() else 0
)
lang_val = lang_options[selected_lang_name]
if lang_val != "auto":
    st.session_state.lang_code = lang_val
    i18n.set_locale(lang_val)

if st.session_state.detected_lang:
    st.sidebar.caption(f"Detected writing language: **{st.session_state.detected_lang.upper()}**")

st.sidebar.write("---")

# Manual Weather Selector (Directly drives CSS colors & playlist blending)
st.sidebar.subheader("🌤️ Weather Mood")
weather_choice = st.sidebar.selectbox(
    "Current Weather Vibe",
    ["None", "Sunny ☀️", "Rainy 🌧️", "Cloudy ☁️", "Snowy ❄️", "Stormy ⛈️"]
)

weather_mappings = {
    "None": {"theme": "linear-gradient(135deg, #1e1e2f, #121214)", "key": None},
    "Sunny ☀️": {"theme": "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)", "key": "sunny"},
    "Rainy 🌧️": {"theme": "linear-gradient(135deg, #3a7bd5 0%, #3a6073 100%)", "key": "rainy"},
    "Cloudy ☁️": {"theme": "linear-gradient(135deg, #bdc3c7 0%, #2c3e50 100%)", "key": "cloudy"},
    "Snowy ❄️": {"theme": "linear-gradient(135deg, #e6e9f0 0%, #eef1f5 100%)", "key": "snowy"},
    "Stormy ⛈️": {"theme": "linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)", "key": "stormy"}
}

active_weather = weather_mappings.get(weather_choice, weather_mappings["None"])

st.sidebar.write("---")

# Define lists of Categories for adding songs
default_songs = load_default_songs()
# Load songs specifically for the currently logged-in user to maintain isolated private music spaces
user_songs_raw = get_user_songs(st.session_state.username)

emotion_moods = ["happy", "sad", "anxious", "angry", "neutral", "romantic", "energetic", "lazy"]
weather_moods = ["sunny", "rainy", "cloudy", "snowy", "stormy"]
all_categories = emotion_moods + weather_moods

# Private Music section in Sidebar (visible to all logged-in users, isolated to their own account)
st.sidebar.subheader(f"🎵 {t('add_song')}")
with st.sidebar.expander(f"➕ {t('add_song')}"):
    category_type = st.radio("Category Type", ["Emotion Mood", "Weather Vibe"])
    if category_type == "Emotion Mood":
        selected_category = st.selectbox("Select Mood", emotion_moods)
    else:
        selected_category = st.selectbox("Select Weather Vibe", weather_moods)
        
    new_song_name = st.text_input(t("song_title"), placeholder="e.g. The Night We Met")
    new_song_link = st.text_input("Paste Spotify Link", placeholder="https://open.spotify.com/track/...")
    
    if st.button(t("submit")):
        if new_song_name and new_song_link:
            if add_user_song(st.session_state.username, selected_category, new_song_name, new_song_link):
                st.success("Song saved to your private list!")
                st.rerun()
            else:
                st.error("Could not save. Please try again.")
        else:
            st.error("Please fill in both fields.")

# View and delete private songs
with st.sidebar.expander("👀 View & Delete My Songs"):
    view_category_type = st.radio("Category Type to View", ["Emotion Mood", "Weather Vibe"], key="view_category_type_radio")
    if view_category_type == "Emotion Mood":
        view_category = st.selectbox("Select Mood", emotion_moods, key="view_mood_select")
    else:
        view_category = st.selectbox("Select Weather Vibe", weather_moods, key="view_weather_select")
        
    my_songs = [s for s in user_songs_raw if s["emotion"].lower() == view_category.lower()]
    if my_songs:
        for s in my_songs:
            st.write(f"🎵 [{s['song_name']}]({s['song_url']})")
        st.write("---")
        delete_options = ["(None)"] + [s["song_name"] for s in my_songs]
        to_delete = st.selectbox("Select song to remove:", delete_options, key="delete_song_selectbox")
        if st.button("🗑️ Delete", key="delete_song_btn"):
            if to_delete != "(None)":
                song_id = next(s["id"] for s in my_songs if s["song_name"] == to_delete)
                delete_user_song(song_id)
                st.success("Deleted! Refreshing...")
                st.rerun()
    else:
        st.write("No private songs saved under this category yet.")

# Helper to load default & private songs
def get_merged_songs(category):
    defaults = default_songs.get(category, [])
    private = [{"name": s["song_name"], "url": s["song_url"], "id": s["id"]} for s in user_songs_raw if s["emotion"].lower() == category.lower()]
    return defaults + private

# ─── Dynamic Color Theming ────────────────────────────────────────────────────
bg_style = active_weather["theme"]
# Determine contrasting text color based on weather
text_color = "#ffffff" if weather_choice in ["None", "Rainy 🌧️", "Stormy ⛈️", "Cloudy ☁️"] else "#1e272e"

st.markdown(f"""
<style>
    .stApp {{
        background: {bg_style};
        background-attachment: fixed;
        transition: background 0.8s ease-in-out;
    }}
    .block-container h1, .block-container h2, .block-container h3, .block-container p, .block-container label, .block-container span, .block-container div {{
        color: {text_color} !important;
    }}
    .stTextArea textarea {{
        background: rgba(255, 255, 255, 0.15) !important;
        color: {text_color} !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
        backdrop-filter: blur(10px);
    }}
    .stRadio, div[data-testid="stRadio"], div[role="radiogroup"] {{
        background: rgba(255, 255, 255, 0.1) !important;
        padding: 15px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
        margin-bottom: 20px !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.15);
    }}
    .weather-widget {{
        background: rgba(255, 255, 255, 0.2);
        padding: 12px 20px;
        border-radius: 15px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        margin-bottom: 25px;
        display: inline-block;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
    }}
    .emotion-box {{
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
        color: white !important;
        font-size: 24px;
        font-weight: bold;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        text-shadow: 1px 1px 3px rgba(0,0,0,0.2);
    }}
    .stButton button {{
        background: linear-gradient(135deg, #ff758c 0%, #ff7eb3 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 10px 24px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(255, 117, 140, 0.4) !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
    }}
    .stButton button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(255, 117, 140, 0.6) !important;
    }}
</style>
""", unsafe_allow_html=True)

# ─── Main UI ──────────────────────────────────────────────────────────────────
st.title(f"🎵 {t('title')}")

# Display Glassmorphic Weather Widget
if weather_choice != "None":
    st.markdown(f"""
    <div class="weather-widget">
        <span style="font-size: 1.5rem; font-weight: bold;">
            {weather_choice} • Active Weather Vibe playlist is ON
        </span>
    </div>
    """, unsafe_allow_html=True)

st.write("Share your thoughts, feelings, or journal entry below, and EmoVibe will create a customized healing experience matching both your mood and weather vibes.")

selection_mode = st.radio(
    "How should I select your music?",
    ["Surprise Me (Automatically pick 1 song)", "Let Me Choose (Show all songs for my mood)"],
    horizontal=True
)

user_input = st.text_area(t("journal_placeholder"), height=150)

# Load color schemes for visual emotion feedback (keyed by core vibe)
color_schemes = {
    "happy":    "linear-gradient(135deg, #f6d365 0%, #fda085 100%)",
    "sad":      "linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%)",
    "anxious":  "linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%)",
    "angry":    "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)",
    "neutral":  "linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)",
    "romantic": "linear-gradient(135deg, #ff758c 0%, #ff7eb3 100%)",
    "energetic":"linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    "lazy":     "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)"
}

# Emoji map for fine-grained emotions
emotion_emojis = {
    "joyful": "😄", "hopeful": "🌟", "proud": "🏆", "optimistic": "☀️",
    "grateful": "🙏", "cheerful": "😊", "delighted": "🤩", "content": "😌",
    "ecstatic": "🥳", "triumphant": "🎉", "amused": "😂",
    "grief-stricken": "💔", "lonely": "🌧️", "depressed": "😞",
    "heartbroken": "💔", "disappointed": "😔", "gloomy": "🌫️",
    "sorrowful": "😢", "melancholy": "🍂", "regretful": "😟",
    "hopeless": "😶", "dejected": "😞",
    "nervous": "😰", "stressed": "😤", "panicky": "😱", "overwhelmed": "🫠",
    "fearful": "😨", "worried": "😟", "apprehensive": "😬",
    "uneasy": "😕", "restless": "😣", "terrified": "😱",
    "furious": "🤬", "irate": "😡", "resentful": "😤",
    "frustrated": "😤", "annoyed": "🙄", "hostile": "😠", "rageful": "🔥",
    "jealous": "😒", "disgusted": "🤢",
    "loving": "❤️", "affectionate": "🥰", "passionate": "💕",
    "smitten": "😍", "longing": "💭", "tender": "🫶",
    "dating": "💑", "anticipating": "⏳", "giddy": "🥹",
    "excited": "⚡", "enthusiastic": "🙌", "pumped": "💪", "hyper": "🚀",
    "vibrant": "✨", "playful": "🎈", "wild": "🌪️", "motivated": "🎯",
    "empowered": "💥", "inspired": "💡",
    "tired": "😴", "bored": "😑", "apathetic": "🥱",
    "lethargic": "🐌", "fatigued": "😮‍💨",
    "calm": "🧘", "indifferent": "😐", "peaceful": "☮️",
    "thoughtful": "🤔", "relaxed": "😎", "unbothered": "🤷",
    "nostalgic": "🎞️", "curious": "🔍", "surprised": "😲",
    "shocked": "😱", "confused": "😵‍💫",
    "shy": "🌸", "embarrassed": "😳", "guilty": "😟",
    "ashamed": "😔",
    # 8 core fallbacks
    "happy": "😊", "sad": "😢", "anxious": "😰", "angry": "😡",
    "neutral": "😐", "romantic": "💕", "energetic": "⚡", "lazy": "😴"
}

# Persist healing results in session state so they don't disappear on language changes or page reruns
if "healing_results" not in st.session_state:
    st.session_state.healing_results = None

# Migration guard: clear stale healing_results from old single-emotion format
if "healing_results" in st.session_state and st.session_state.healing_results:
    if not isinstance(st.session_state.healing_results.get("emotion_list"), list):
        st.session_state.healing_results = None

if st.button("Generate Healing Experience 🌟"):
    if not user_input.strip():
        st.warning("Please enter your thoughts first!")
    else:
        with st.spinner("Analyzing your thoughts..."):
            # 1. Translation and Language Detection
            english_text, lang_code = mood.translate_and_detect_language(user_input)
            st.session_state.detected_lang = lang_code

            # Auto-update UI locale if set to Auto-Detect
            run_rerun = False
            if selected_lang_name == "Auto-Detect" and st.session_state.lang_code != lang_code:
                st.session_state.lang_code = lang_code
                i18n.set_locale(lang_code)
                run_rerun = True

            # 2. Get ALL detected emotions — list of (fine_emotion, explanation, core_vibe)
            emotion_list = mood.detect_mood_probabilities(english_text)

            # 3. Build blended playlist from ALL unique core vibes detected
            blended_playlist = []
            seen_cores = set()
            for fine_em, expl, core in emotion_list:
                if core not in seen_cores:
                    songs = get_merged_songs(core)
                    # Tag each song with which mood it belongs to
                    for s in songs:
                        blended_playlist.append({
                            "name": s["name"],
                            "url":  s["url"],
                            "tag":  fine_em.capitalize()
                        })
                    seen_cores.add(core)

            # 4. Add weather vibe songs if active
            if active_weather["key"]:
                w_key = active_weather["key"]
                for s in get_merged_songs(w_key):
                    blended_playlist.append({
                        "name": "🌦️ {} Vibe: {}".format(weather_choice.split()[0], s["name"]),
                        "url":  s["url"],
                        "tag":  "Weather"
                    })

            # Store in session state
            st.session_state.healing_results = {
                "emotion_list":    emotion_list,
                "blended_playlist": blended_playlist
            }

            if run_rerun:
                st.rerun()

# ─── Render Persisted Healing Results ─────────────────────────────────────────
if st.session_state.healing_results:
    res             = st.session_state.healing_results
    emotion_list    = res["emotion_list"]
    blended_playlist = res["blended_playlist"]

    # ── Emotion Cards (one per detected mood) ─────────────────────────────────
    num_emotions = len(emotion_list)
    if num_emotions == 1:
        cols = [st.container()]   # single card, full width
    else:
        cols = st.columns(num_emotions)

    for idx, (fine_em, expl, core) in enumerate(emotion_list):
        emoji  = emotion_emojis.get(fine_em, emotion_emojis.get(core, "🎵"))
        bg     = color_schemes.get(core, "linear-gradient(135deg, #667eea, #764ba2)")
        label  = "🎯 Primary Mood" if idx == 0 else "✨ Also Feeling"
        size   = "24px" if idx == 0 else "18px"

        card_html = """
        <div class="emotion-box" style="background: {bg}; font-size:{size};">
            <div style="font-size:11px; font-weight:600; opacity:0.8; letter-spacing:1px; margin-bottom:6px;">{label}</div>
            {emoji} {name}
            <div style="font-size:13px; font-weight:normal; margin-top:8px; opacity:0.92;">{expl}</div>
            <div style="font-size:11px; font-weight:normal; margin-top:5px; opacity:0.7;">Vibe → {core}</div>
        </div>
        """.format(bg=bg, size=size, label=label, emoji=emoji,
                   name=fine_em.capitalize(), expl=expl, core=core.capitalize())

        if num_emotions == 1:
            cols[0].markdown(card_html, unsafe_allow_html=True)
        else:
            cols[idx].markdown(card_html, unsafe_allow_html=True)

    # ── Mixed Mood Banner ──────────────────────────────────────────────────────
    if num_emotions > 1:
        vibe_names = " + ".join(e[0].capitalize() for e in emotion_list)
        st.markdown(
            '<div style="text-align:center; color:#aaa; font-size:13px; margin: -8px 0 16px 0;">'
            '🎨 Mixed mood detected: <strong>{}</strong></div>'.format(vibe_names),
            unsafe_allow_html=True
        )

    # ── Playlist ───────────────────────────────────────────────────────────────
    if blended_playlist:
        st.subheader("🎧 Your Personalized Healing Playlist")
        if num_emotions > 1:
            st.caption("Songs blended from all your detected moods 🎨")

        # Surprise Me picks one random, Let Me Choose shows all
        display_songs = [random.choice(blended_playlist)] if "Surprise" in selection_mode else blended_playlist

        for s in display_songs:
            song_name = s["name"]
            song_url  = s["url"]
            tag       = s.get("tag", "")

            # Convert standard Spotify link to embed link
            embed_url = song_url
            if "open.spotify.com" in song_url and "embed" not in song_url:
                embed_url = song_url.replace("open.spotify.com/", "open.spotify.com/embed/")

            if tag:
                st.caption("🏷️ {}".format(tag))
            st.components.v1.iframe(src=embed_url, width=300, height=80, scrolling=False)
            st.write("🔗 [{}]({})".format(song_name, song_url))
    else:
        st.info("No songs found for your mood(s) yet. Add your songs in the sidebar! ➕")

    st.write("---")
    st.write("🔒 Your thoughts are processed securely and your privacy is fully protected.")


