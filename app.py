import streamlit as st
import os
from groq import Groq
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import time

# Load API keys
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not GROQ_API_KEY or not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    st.error("🔑 API keys missing! Please set environment variables.")
    st.stop()

# Initialize clients
groq_client = Groq(api_key=GROQ_API_KEY)
sp = Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))

# Streamlit UI
st.set_page_config(page_title="🎵 AI Mood-Based Music Playlist", layout="wide")
st.title("🎶 AI Mood-Based Playlist Generator")

# --- User Inputs ---
mood_text = st.text_area("📝 Describe your mood in detail:", placeholder="I'm feeling a little nostalgic after watching old photos...")
activity = st.text_input("💼 What are you doing right now?", placeholder="e.g. Studying, Cooking, Driving, Relaxing...")
genre = st.multiselect("🎸 Preferred genres (optional):", ["Pop", "Rock", "Lo-fi", "Classical", "Hip-Hop", "EDM", "Indie", "Jazz", "Bollywood", "K-pop"])
language = st.selectbox("🗣️ Language Preference:", ["English", "Hindi", "Korean", "Spanish", "Instrumental", "No Preference"])
energy = st.slider("⚡ Energy Level:", 1, 10, 5)
lyrics = st.radio("🎤 Want lyrics?", ["Yes", "No", "Doesn't matter"])
explicit = st.checkbox("🔞 Allow explicit content?")

# --- Generate Prompt Function ---
def generate_prompt():
    return f"""
You are an intelligent and creative music assistant.

Your job is to analyze a user's mood, activity, and other preferences and return a **Spotify search query** that gives them the most perfect music experience right now.

Use the following detailed layers of information to decide:

1. **Mood**: "{mood_text}"
2. **Current Activity**: "{activity}"
3. **Preferred Genres**: "{', '.join(genre) if genre else 'No specific preference'}"
4. **Preferred Language**: "{language}"
5. **Energy Level**: "{energy}"
6. **Lyrics or Instrumental**: "{lyrics}"
7. **Explicit Content Allowed**: {"Yes" if explicit else "No"}
8. **Mental state tone**: calm, anxious, excited, nostalgic, etc.
9. **Time of day**: Assume it's based on user mood context (morning, night, late night).
10. **Musical instruments preferred**: Implicitly infer if user may like guitar, piano, synths, etc.
11. **Goal of music**: (focus, relax, get hyped, feel emotions, background)
12. **Weather feel**: Infer based on mood text (rainy, sunny, wintery, foggy)
13. **Social context**: Alone, with friends, romantic partner, etc.
14. **Listening environment**: Using headphones? speaker? party? infer tone.
15. **Lyrics tone**: poetic, sad, happy, upbeat, dark, etc.
16. **Temporal memory**: Does mood indicate something nostalgic, futuristic or timeless?
17. **Beat style**: Lo-fi, trap, acoustic, ambient, etc.
18. **Sound complexity**: Simple melodies or rich layered sounds.
19. **Cultural influences**: Pop culture, retro, K-pop, Bollywood, indie scene.
20. **Any other intuitive guess from user description.**

---
💡 **Output Format (STRICTLY)**:
Detected Mood: <one word or short phrase summarizing the mood>

Spotify Search Query: <Your best creative and smart Spotify search query using the above 20 details>
---
DO NOT write anything else, only this 2-line format.
"""

# --- Mood + Music Query ---
def analyze_mood_and_generate_query():
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": generate_prompt()}
            ],
            timeout=15, 
            max_tokens=10000, 
            temperature=1
        )
        ai_output = response.choices[0].message.content.strip()
        lines = ai_output.splitlines()

        if len(lines) >= 2:
            mood = lines[0].replace("Detected Mood:", "").strip().lower()
            music_query = lines[1].replace("Spotify Search Query:", "").strip()
            return mood, music_query
        else:
            raise ValueError("Unexpected AI output format.")
    except Exception as e:
        st.error(f"❌ Mood analysis failed: {e}")
        return "neutral", "chill music"

# --- Spotify Playlist ---
def get_playlist(music_query):
    try:
        results = sp.search(q=music_query, type="playlist", limit=3)
        playlists = results.get("playlists", {}).get("items", [])
        if playlists:
            selected = playlists[0]
            return selected["name"], selected["external_urls"]["spotify"], selected["id"]
        return None, None, None
    except Exception as e:
        st.error(f"❌ Spotify API error: {e}")
        return None, None, None

# --- Main Action Button ---
if st.button("🎧 Generate Playlist"):
    if mood_text:
        with st.spinner("🧠 Analyzing mood and generating magic..."):
            mood, music_query = analyze_mood_and_generate_query()
            st.subheader(f"🎭 Detected Mood: {mood.capitalize()}")
            st.write(f"🎶 **AI Music Query:** {music_query}")

            playlist_name, playlist_url, playlist_id = None, None, None
            for _ in range(3):
                playlist_name, playlist_url, playlist_id = get_playlist(music_query)
                if playlist_id:
                    break
                time.sleep(1.5)

            if playlist_id:
                st.success(f"🎵 Playlist Found: {playlist_name}")
                st.markdown(f"[🔗 Open on Spotify]({playlist_url})")
                st.markdown(
                    f'<iframe src="https://open.spotify.com/embed/playlist/{playlist_id}" width="100%" height="380" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>',
                    unsafe_allow_html=True
                )
            else:
                st.warning("⚠️ No playlist found. Try tweaking your input!")
    else:
        st.warning("⚠️ Please enter your mood description!")

st.sidebar.info("🎵 Powered by Groq AI & Spotify\n💡 Tip: The more detailed your mood, the smarter your playlist!")
