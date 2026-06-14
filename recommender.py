import requests
import random
import re

# Mapping of popular artists to related artists to diversify recommendations
RELATED_ARTISTS = {
    # Pop & Western Artists
    "ed sheeran": ["shawn mendes", "taylor swift", "lewis capaldi", "james arthur", "john mayer", "charlie puth"],
    "taylor swift": ["selena gomez", "olivia rodrigo", "sabrina carpenter", "gracie abrams", "ed sheeran", "billie eilish"],
    "billie eilish": ["finneas", "olivia rodrigo", "lorde", "lana del rey", "phoebe bridgers", "girl in red"],
    "the weeknd": ["post malone", "khalid", "frank ocean", "travis scott", "drake", "joji"],
    "coldplay": ["onerepublic", "keane", "snow patrol", "the fray", "imagine dragons", "kodaline"],
    "bts": ["blackpink", "txt", "exo", "stray kids", "twice", "seventeen"],
    
    # Bollywood & Hindi Artists
    "arijit singh": ["atif aslam", "shreya ghoshal", "jubin nautiyal", "darshan raval", "nehakakkar", "pritam", "kk", "armaan malik"],
    "pritam": ["arijit singh", "kk", "mohit chauhan", "vishal-shekhar", "amit trivedi", "shreya ghoshal"],
    "kk": ["arijit singh", "mohit chauhan", "shaan", "sonu nigam", "atif aslam", "lucky ali"],
    "mohit chauhan": ["kk", "arijit singh", "ar rahman", "amit trivedi", "lucky ali", "kailash kher"],
    "ar rahman": ["shreya ghoshal", "sid sriram", "hariharan", "amit trivedi", "arijit singh", "javed ali"],
    "anuv jain": ["local train", "zaeden", "aditya rikhari", "prateek kuhad", "kabir kathpalia", "tanishk bagchi"],
    "prateek kuhad": ["anuv jain", "local train", "karun", "taba chake", "when chai met toast"],
    "lata mangeshkar": ["kishore kumar", "mohammad rafi", "asha bhosle", "rd burman", "mukesh"],
    "kishore kumar": ["lata mangeshkar", "mohammad rafi", "rd burman", "asha bhosle", "mukesh"],
}

def clean_song_name(name):
    """Clean common suffixes like (Official Video), [Lyrics], etc."""
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"\[.*?\]", "", name)
    return name.strip()

def extract_possible_artists(song_title):
    """
    Extract possible artist names from user's song input.
    E.g. 'Perfect - Ed Sheeran' -> 'Ed Sheeran'
    """
    clean_name = clean_song_name(song_title)
    # Check for common separators
    for sep in [" - ", " by ", " – ", " : ", " | "]:
        if sep in clean_name:
            parts = clean_name.split(sep)
            # Check which part is more likely the artist
            # Typically artist is second, but could be first. Let's return both parts for search
            return [p.strip() for p in parts]
    return [clean_name]

def get_recommendations_from_itunes(user_songs, limit=6):
    """
    Generate related song recommendations based on user's added songs.
    Returns a list of dicts with name, artist, url, preview_url, and artwork.
    """
    if not user_songs:
        return []

    # 1. Pick a random song from user's library to generate recommendation for
    chosen_song = random.choice(user_songs)
    song_title = chosen_song.get("song_name", "")
    
    # Get keywords to search
    search_terms = extract_possible_artists(song_title)
    
    # 2. Search iTunes to identify the primary artist/genre of this song
    primary_artist = None
    search_url = "https://itunes.apple.com/search"
    
    for term in search_terms:
        params = {
            "term": term,
            "media": "music",
            "entity": "musicTrack",
            "limit": 3
        }
        try:
            r = requests.get(search_url, params=params, timeout=5)
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    primary_artist = results[0].get("artistName")
                    break
        except Exception as e:
            print(f"iTunes Search Error: {e}")
            
    # Fallback to search term if iTunes search failed
    if not primary_artist:
        primary_artist = search_terms[-1]
        
    # 3. Determine target artists (the artist itself + related artists)
    target_artists = [primary_artist]
    norm_artist = primary_artist.lower()
    
    # Check if we have related artists mapped
    found_related = []
    for key, related in RELATED_ARTISTS.items():
        if key in norm_artist or norm_artist in key:
            found_related = related
            break
            
    if found_related:
        target_artists.extend(found_related)
        
    # Shuffle targets to keep recommendations fresh
    random.shuffle(target_artists)
    
    recommendations = []
    already_added_names = {s.get("song_name", "").lower() for s in user_songs}
    
    # 4. Search iTunes for tracks from target artists
    for artist in target_artists[:3]:  # Try up to 3 artists
        params = {
            "term": artist,
            "media": "music",
            "entity": "musicTrack",
            "limit": 10
        }
        try:
            r = requests.get(search_url, params=params, timeout=5)
            if r.status_code == 200:
                tracks = r.json().get("results", [])
                for t in tracks:
                    track_name = t.get("trackName")
                    track_artist = t.get("artistName")
                    full_name = f"{track_name} - {track_artist}"
                    
                    # Prevent recommending songs the user already added
                    if track_name.lower() in already_added_names or full_name.lower() in already_added_names:
                        continue
                        
                    # Prevent duplicates in recommendation list
                    if any(rec["track_name"].lower() == track_name.lower() for rec in recommendations):
                        continue
                        
                    recommendations.append({
                        "track_name": track_name,
                        "artist_name": track_artist,
                        "url": t.get("trackViewUrl"),
                        "preview_url": t.get("previewUrl"),
                        "artwork": t.get("artworkUrl100"),
                        "spotify_search_url": f"https://open.spotify.com/search/{requests.utils.quote(full_name)}"
                    })
                    
                    if len(recommendations) >= limit:
                        break
        except Exception as e:
            print(f"iTunes Recommendations Fetch Error: {e}")
            
        if len(recommendations) >= limit:
            break
            
    return recommendations
