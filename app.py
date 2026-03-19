import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import urllib.parse
import urllib.request
import plotly.express as px
import plotly.graph_objects as go
import os
import logging
import requests
from bs4 import BeautifulSoup
import re
import time
from fpdf import FPDF
import joblib

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Entertainment Recommendation System",
    page_icon="🍿",
    layout="wide",
    initial_sidebar_state="expanded"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. PROFESSIONAL NEON STYLING ---
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;600;700&display=swap');
        
        :root {
            --neon-cyan: #00f3ff;
            --neon-purple: #bc13fe;
            --neon-pink: #ff0055;
            --bg-base: #07070a;
            --bg-surface: rgba(15, 15, 20, 0.7);
            --panel-border: rgba(0, 243, 255, 0.3);
            --text-main: #f0f4f8;
            --text-muted: #8892b0;
        }

        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-base);
            color: var(--text-main);
        }

        .stApp { 
            background-color: var(--bg-base);
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(188, 19, 254, 0.08), transparent 30%),
                radial-gradient(circle at 85% 30%, rgba(0, 243, 255, 0.08), transparent 30%),
                linear-gradient(rgba(0, 243, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 243, 255, 0.03) 1px, transparent 1px);
            background-size: 100% 100%, 100% 100%, 40px 40px, 40px 40px;
            background-position: center top;
            background-attachment: fixed;
        }

        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg-base); }
        ::-webkit-scrollbar-thumb { background: #1a1a24; border-radius: 10px; border: 1px solid var(--neon-cyan); box-shadow: 0 0 5px var(--neon-cyan); }
        ::-webkit-scrollbar-thumb:hover { background: var(--neon-cyan); }

        /* Sidebar & Tabs */
        [data-testid="stSidebar"] { background: linear-gradient(180deg, rgba(5, 5, 8, 0.95) 0%, rgba(10, 10, 15, 0.98) 100%) !important; border-right: 1px solid var(--panel-border); box-shadow: 5px 0 30px rgba(0, 243, 255, 0.1); }
        div[data-testid="stTabs"] { background: rgba(10, 10, 15, 0.6); padding: 10px 20px 0 20px; border-radius: 16px; border: 1px solid rgba(188, 19, 254, 0.2); margin-bottom: 20px; }
        div[data-baseweb="tab-highlight"] { background-color: var(--neon-cyan) !important; height: 4px; border-radius: 4px 4px 0 0; box-shadow: 0 -2px 15px var(--neon-cyan); }
        div[data-testid="stTabs"] button { font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 600; color: var(--text-muted); letter-spacing: 0.5px; transition: all 0.3s ease; }
        div[data-testid="stTabs"] button[aria-selected="true"] { color: #ffffff !important; text-shadow: 0 0 10px var(--neon-cyan), 0 0 20px var(--neon-cyan); }
        
        /* Hero & Cards */
        .hero-title { font-family: 'Space Grotesk', sans-serif; font-size: 4.5rem; font-weight: 800; letter-spacing: -2px; text-transform: uppercase; color: #ffffff; text-shadow: 0 0 5px #fff, 0 0 10px #fff, 0 0 20px var(--neon-cyan), 0 0 40px var(--neon-cyan); margin-bottom: 0; text-align: center; }
        .hero-subtitle { text-align: center; color: var(--neon-purple); font-size: 1.3rem; font-weight: 600; letter-spacing: 3px; margin-bottom: 4rem; text-transform: uppercase; text-shadow: 0 0 10px rgba(188, 19, 254, 0.5); }
        
        .movie-card { background: linear-gradient(145deg, rgba(25, 25, 30, 0.8) 0%, rgba(10, 10, 12, 0.9) 100%); border-radius: 16px 16px 0 0 !important; border: 1px solid rgba(0, 243, 255, 0.1); overflow: hidden; display: flex; flex-direction: column; position: relative; margin-bottom: 0px !important; transition: all 0.4s ease; }
        .movie-card::before { content: ''; position: absolute; top: 0; left: -100%; width: 50%; height: 100%; background: linear-gradient(90deg, transparent, rgba(0, 243, 255, 0.1), transparent); transform: skewX(-20deg); transition: 0.5s; z-index: 1; }
        .movie-card:hover::before { left: 200%; }
        .movie-card:hover { border-color: var(--neon-cyan); box-shadow: 0 15px 35px rgba(0,0,0,0.8), inset 0 0 20px rgba(0, 243, 255, 0.2); transform: translateY(-8px); }
        
        div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stButton"]) { margin-top: -12px !important; }
        div[data-testid="stButton"] > button { border-radius: 0 0 16px 16px !important; background: rgba(15, 15, 20, 0.9) !important; color: #ffffff !important; font-family: 'Space Grotesk', sans-serif !important; font-weight: 700 !important; border: 1px solid rgba(0, 243, 255, 0.2) !important; padding: 16px !important; transition: all 0.3s ease; }
        div[data-testid="stButton"] > button:hover { transform: translateY(-4px); background: linear-gradient(90deg, #0055ff 0%, var(--neon-cyan) 100%) !important; border-color: var(--neon-cyan) !important; box-shadow: 0 10px 20px rgba(0, 243, 255, 0.3); text-shadow: 0 2px 4px rgba(0,0,0,0.5); }

        .rating-badge { position: absolute; top: 12px; right: 12px; background: rgba(0, 0, 0, 0.8); backdrop-filter: blur(8px); padding: 6px 12px; border-radius: 8px; font-weight: 700; font-size: 0.85rem; border: 1px solid rgba(188, 19, 254, 0.5); z-index: 10; }
        .rating-badge span { color: var(--neon-purple); margin-right: 4px; }
        .category-badge { position: absolute; top: 12px; left: 12px; background: rgba(0, 243, 255, 0.1); backdrop-filter: blur(8px); padding: 4px 10px; border-radius: 4px; font-weight: 700; font-size: 0.7rem; color: var(--neon-cyan); border: 1px solid var(--neon-cyan); z-index: 10; }
        .genre-tag { background: rgba(255, 255, 255, 0.03); color: #a1a1aa; padding: 4px 10px; border-radius: 4px; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; margin-right: 6px; margin-bottom: 6px; display: inline-block; border: 1px solid rgba(255, 255, 255, 0.05); }
        .ai-reasoning { font-family: 'Space Grotesk', sans-serif; background: rgba(0, 243, 255, 0.05); color: var(--neon-cyan); border-left: 2px solid var(--neon-cyan); margin-top: 8px; border-radius: 0 4px 4px 0; text-transform: uppercase; letter-spacing: 0.5px; box-shadow: inset 5px 0 15px rgba(0, 243, 255, 0.05); }

        /* --- HORIZONTAL CAST & CREW SCROLL --- */
        .cast-container { display: flex; overflow-x: auto; gap: 15px; padding-bottom: 15px; margin-bottom: 20px; scroll-behavior: smooth; }
        .cast-card { min-width: 140px; max-width: 140px; background: rgba(20, 20, 25, 0.6); border: 1px solid rgba(0, 243, 255, 0.15); border-radius: 12px; overflow: hidden; display: flex; flex-direction: column; box-shadow: 0 5px 15px rgba(0,0,0,0.5); transition: all 0.3s ease; }
        .cast-card:hover { border-color: var(--neon-purple); transform: translateY(-5px); box-shadow: 0 8px 20px rgba(188, 19, 254, 0.2); }
        .cast-img { width: 100%; height: 180px; object-fit: cover; filter: brightness(0.9) contrast(1.1); }
        .cast-info { padding: 10px; text-align: center; }
        .cast-name { font-family: 'Space Grotesk', sans-serif; font-size: 0.85rem; font-weight: 700; color: #fff; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .cast-role { font-size: 0.75rem; color: var(--neon-cyan); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .cast-sub-role { font-size: 0.65rem; color: #8892b0; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .stSelectbox > div > div { background: rgba(20, 20, 25, 0.8); border: 1px solid rgba(0, 243, 255, 0.2); border-radius: 8px; color: #fff; }
        .stSelectbox > div > div:focus-within { border-color: var(--neon-cyan); box-shadow: 0 0 15px rgba(0, 243, 255, 0.4); }
        .stSlider > div > div > div { background-color: var(--neon-cyan) !important; }
        </style>
    """, unsafe_allow_html=True)


# --- 3. IMPROVED HELPER FUNCTIONS & SCRAPERS ---

def get_initials(name):
    parts = str(name).strip().split()
    if len(parts) >= 2: return (parts[0][0] + parts[1][0]).upper()
    elif len(parts) == 1 and len(parts[0]) > 0: return parts[0][:2].upper()
    return "??"

@st.cache_data(show_spinner=False, ttl=86400)
def get_wiki_person_image(name, role_color="bc13fe"):
    try:
        search_query = urllib.parse.quote(f"{name} actor")
        url = f"https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch={search_query}&gsrlimit=1&prop=pageimages&pithumbsize=180&format=json"
        
        resp = requests.get(url, headers={"User-Agent": "PopcornAI_Project/1.0"}, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            pages = data.get('query', {}).get('pages', {})
            if pages:
                page_id = list(pages.keys())[0]
                thumb_url = pages[page_id].get('thumbnail', {}).get('source')
                if thumb_url: return thumb_url
    except Exception as e:
        logger.warning(f"Failed to fetch image for {name}: {e}")
    
    return f"https://placehold.co/140x180/1a1a24/{role_color}?text={get_initials(name)}"

def extract_wiki_names(td_element):
    if not td_element: return []
    for sup in td_element.find_all('sup'): sup.decompose()
    for hidden in td_element.find_all(style=re.compile(r'display:\s*none', re.I)): hidden.decompose()
    
    names = []
    lis = td_element.find_all('li')
    if lis:
        names = [li.get_text(strip=True) for li in lis]
    else:
        for br in td_element.find_all(['br', 'hr']): br.replace_with(", ")
        text = td_element.get_text()
        raw_names = re.split(r',|\n', text)
        names = [n.strip() for n in raw_names if n.strip()]
    
    clean_names = [re.sub(r'\[.*?\]', '', n).strip() for n in names if len(n) > 1]
    return clean_names[:8]

def get_character_name(soup, actor_name):
    """
    ADVANCED WIKIPEDIA PARSER: 
    Finds the exact character name by scanning lists and wikitables under the Cast section.
    """
    cast_headings = [h for h in soup.find_all(['h2', 'h3']) if re.search(r'Cast|Characters', h.get_text(), re.I)]
    actor_clean = re.sub(r'\s+', ' ', actor_name).strip().lower()
    
    for heading in cast_headings:
        curr = heading.find_next_sibling()
        while curr and curr.name not in ['h2', 'h3']:
            
            # 1. Search in Bullet Points & Lists (Common for Movies)
            for item in curr.find_all(['li', 'dd', 'p']):
                text = item.get_text(" ", strip=True)
                if actor_clean in text.lower():
                    parts = re.split(r'\s+as\s+|\s+[-–—]\s+|\s*:\s*', text, maxsplit=1, flags=re.IGNORECASE)
                    if len(parts) >= 2:
                        char_raw = parts[1] if actor_clean in parts[0].lower() else parts[0]
                        char_clean = re.sub(r'\[.*?\]', '', char_raw).strip()
                        char_clean = re.split(r'\(|,|\.|:', char_clean)[0].strip()
                        if char_clean and len(char_clean) < 40: return char_clean
            
            # 2. Search in Tables (Common for TV Shows)
            for tr in curr.find_all('tr'):
                tds = tr.find_all(['td', 'th'])
                texts = [td.get_text(" ", strip=True) for td in tds]
                for i, txt in enumerate(texts):
                    if actor_clean in txt.lower():
                        if i + 1 < len(texts):
                            char_clean = re.sub(r'\[.*?\]', '', texts[i+1]).strip()
                            char_clean = re.split(r'\(|\n', char_clean)[0].strip()
                            if char_clean and len(char_clean) < 40 and char_clean.lower() not in ["main", "recurring", "guest"]: 
                                return char_clean
                        if i - 1 >= 0:
                            char_clean = re.sub(r'\[.*?\]', '', texts[i-1]).strip()
                            char_clean = re.split(r'\(|\n', char_clean)[0].strip()
                            if char_clean and len(char_clean) < 40 and char_clean.lower() not in ["main", "recurring", "guest"]: 
                                return char_clean

            curr = curr.find_next_sibling()
            
    return "Character" 

def show_custom_loader(placeholder, message="Loading Recommendations..."):
    loader_html = f"""<style>.cyber-loader-container {{ display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 80px 20px; background: rgba(10, 10, 12, 0.6); backdrop-filter: blur(20px); border-radius: 20px; border: 1px solid rgba(0, 243, 255, 0.3); margin: 30px 0; }} .radar {{ width: 60px; height: 60px; border-radius: 50%; border: 2px solid rgba(0, 243, 255, 0.3); position: relative; overflow: hidden; }} .radar::before {{ content: ''; position: absolute; top: 50%; left: 50%; width: 100%; height: 100%; background: conic-gradient(transparent, transparent, transparent, rgba(0, 243, 255, 0.8)); animation: scan 2s linear infinite; }} @keyframes scan {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }} .loader-text {{ margin-top: 24px; color: #fff; font-family: 'Space Grotesk', sans-serif; font-size: 1.2rem; font-weight: 600; text-transform: uppercase; }}</style><div class="cyber-loader-container"><div class="radar"></div><div class="loader-text">{message}</div></div>"""
    placeholder.markdown(loader_html, unsafe_allow_html=True)

@st.cache_data(show_spinner=False, ttl=86400)
def get_youtube_trailer_url(title, year):
    try:
        query = urllib.parse.quote(f"{title} {year} official trailer")
        url = f"https://www.youtube.com/results?search_query={query}"
        html = urllib.request.urlopen(url, timeout=2)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        if video_ids: return f"https://www.youtube.com/watch?v={video_ids[0]}"
        return None
    except: return None

@st.cache_data(show_spinner=False, ttl=86400)
def fetch_info_from_internet(title, year, category_type, tconst=None):
    safe_title = urllib.parse.quote(str(title))
    fallback_img = f"https://placehold.co/500x750/0a0a0f/00f3ff?text={safe_title}"
    result = {"poster": fallback_img, "director": "Unknown", "synopsis": "No synopsis available.", "cast": []}

    try:
        if category_type == "Anime":
            time.sleep(0.4) 
            url = f"https://api.jikan.moe/v4/anime?q={safe_title}&limit=1"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json().get('data', [])
                if data:
                    anime = data[0]
                    anime_id = anime.get('mal_id')
                    
                    if anime.get('images', {}).get('jpg', {}).get('large_image_url'):
                        result["poster"] = anime['images']['jpg']['large_image_url']
                    if anime.get('synopsis'):
                        result["synopsis"] = anime['synopsis'].replace("[Written by MAL Rewrite]", "").strip()
                    if anime.get('studios'):
                        result["director"] = anime['studios'][0].get('name', 'Unknown')
                    
                    time.sleep(0.4) 
                    char_url = f"https://api.jikan.moe/v4/anime/{anime_id}/characters"
                    char_resp = requests.get(char_url, timeout=5)
                    
                    if char_resp.status_code == 200:
                        char_data = char_resp.json().get('data', [])[:8]
                        for item in char_data:
                            char = item.get('character', {})
                            va = next((v.get('person') for v in item.get('voice_actors', []) if v.get('language') == 'Japanese'), {})
                            img_url = char.get('images', {}).get('jpg', {}).get('image_url', '')
                            
                            if not img_url or "questionmark" in img_url: 
                                img_url = f"https://placehold.co/140x180/0a0a0f/00f3ff?text={urllib.parse.quote(char.get('name', 'N/A'))}"
                            
                            result["cast"].append({
                                'name': char.get('name', 'Unknown'),
                                'role': item.get('role', 'Character'),
                                'sub_role': va.get('name', 'Unknown VA'),
                                'image': img_url
                            })

        else:
            formatted_title = str(title).replace(" ", "_")
            suffixes = [
                f"{formatted_title}_(film)", 
                f"{formatted_title}_({int(year)}_film)", 
                formatted_title
            ] if category_type == "Movies" else [
                f"{formatted_title}_(TV_series)", 
                f"{formatted_title}_(American_TV_series)", 
                formatted_title
            ]
            
            headers = {"User-Agent": "PopcornAI_Project/1.0"}
            
            for suffix in suffixes:
                api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(suffix)}"
                response = requests.get(api_url, headers=headers, timeout=4)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('type') != 'disambiguation':
                        if 'extract' in data: result["synopsis"] = data['extract']
                        if 'originalimage' in data: result["poster"] = data['originalimage']['source']
                        
                        wiki_html_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(suffix)}"
                        html_resp = requests.get(wiki_html_url, headers=headers, timeout=4)
                        
                        if html_resp.status_code == 200:
                            soup = BeautifulSoup(html_resp.text, 'html.parser')
                            infobox = soup.find('table', class_='infobox')
                            
                            if infobox:
                                dir_th = infobox.find('th', string=re.compile("Directed by|Created by|Based on", re.IGNORECASE))
                                if dir_th and dir_th.find_next_sibling('td'):
                                    creators = extract_wiki_names(dir_th.find_next_sibling('td'))
                                    for c in creators:
                                        img_url = get_wiki_person_image(c, role_color="00f3ff")
                                        result["cast"].append({'name': c, 'role': 'Crew', 'sub_role': dir_th.text.strip(), 'image': img_url})
                                        result["director"] = creators[0]
                                
                                star_th = infobox.find('th', string=re.compile("Starring|Voices of", re.IGNORECASE))
                                if star_th and star_th.find_next_sibling('td'):
                                    stars = extract_wiki_names(star_th.find_next_sibling('td'))
                                    for s in stars:
                                        img_url = get_wiki_person_image(s, role_color="bc13fe")
                                        character_name = get_character_name(soup, s)
                                        result["cast"].append({'name': s, 'role': character_name, 'sub_role': 'Actor', 'image': img_url})
                        break 

    except Exception as e:
        logger.error(f"Scraper Error for {title}: {e}")
    
    return result

# --- 4. DATA LOADER & AI MODELS ---
class DataLoader:
    @staticmethod
    @st.cache_data(show_spinner=False)
    def load(category: str) -> pd.DataFrame:
        files = {"Movies": "movies.parquet", "TV Shows": "tv_shows.parquet", "Anime": "anime.parquet"}
        if category == "All Collections (Crossover)":
            dfs = [pd.read_parquet(f, engine='pyarrow') for f in files.values() if os.path.exists(f)]
            return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
        else:
            file_path = files.get(category)
            if file_path and os.path.exists(file_path):
                return pd.read_parquet(file_path, engine='pyarrow')
            return pd.DataFrame()

@st.cache_resource(show_spinner=False)
def load_ai_models(category):
    safe_name = category.replace(" ", "_").replace("(", "").replace(")", "").lower()
    try:
        return joblib.load(f'ai_models/vectorizer_{safe_name}.joblib'), joblib.load(f'ai_models/matrix_{safe_name}.joblib'), joblib.load(f'ai_models/coords_{safe_name}.joblib')
    except: st.stop()

def get_recommendations_by_title(title, df, matrix, top_n=15):
    try:
        idx = df[df['title'] == title].index[0]
        indices = cosine_similarity(matrix[idx], matrix).flatten().argsort()[-top_n-1:-1][::-1]
        return df.iloc[indices].copy()
    except: return pd.DataFrame()

# --- 5. MODAL DIALOG WITH CAST SECTION ---
@st.dialog("🎬 Title Details", width="large")
def show_movie_modal(row):
    cat_type = row.get('category_type', '')
    tconst_id = row.get('tconst', None)
    
    web_data = fetch_info_from_internet(row['title'], row['year'], cat_type, tconst_id)
    
    poster_url = row.get('poster_path', None)
    if pd.notna(poster_url) and str(poster_url).strip() != "" and str(poster_url) != "nan":
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_url}" if str(poster_url).startswith('/') else poster_url
    else:
        poster_url = web_data["poster"]

    synopsis = web_data["synopsis"] if "No synopsis available." not in web_data["synopsis"] else str(row.get('overview', ''))

    c1, c2 = st.columns([1, 2.2])
    with c1:
        fallback_img = f"https://placehold.co/500x750/0a0a0f/00f3ff?text={urllib.parse.quote(row['title'])}"
        st.markdown(f'<img src="{poster_url}" style="width:100%; border-radius:12px; border: 1px solid rgba(0, 243, 255, 0.3); box-shadow: 0 0 30px rgba(0, 243, 255, 0.2);" onerror="this.src=\'{fallback_img}\';">', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("➕ Add to Watchlist", key=f"modal_fav_{row['title']}", use_container_width=True):
            if row['title'] not in st.session_state.watchlist:
                st.session_state.watchlist.append(row['title'])
                st.rerun()

    with c2:
        st.markdown(f"<h2 style='margin-bottom:0; font-family: \"Space Grotesk\", sans-serif; font-size:2.5rem; letter-spacing:-1px; text-shadow: 0 0 15px rgba(255,255,255,0.3);'>{row['title']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#a1a1aa; font-size:1.1rem; margin-bottom:15px; font-weight:500;'>{row['year']} &nbsp;•&nbsp; <span style='color:#bc13fe; text-shadow: 0 0 5px #bc13fe;'>★ {row['rating']}</span> &nbsp;•&nbsp; <span style='color:#00f3ff;'>{cat_type}</span></p>", unsafe_allow_html=True)
        
        row_genres = str(row['genres']).split()
        genres_html = "".join([f'<span class="genre-tag" style="background: rgba(0, 243, 255, 0.1); border-color: rgba(0, 243, 255, 0.3); color: #fff;">{g}</span>' for g in row_genres])
        st.markdown(f"<div style='margin-bottom:20px;'>{genres_html}</div>", unsafe_allow_html=True)
        
        creator_lbl = "Studio" if cat_type == "Anime" else "Creator" 
        dir_val = web_data.get('director', 'Unknown')
        if dir_val in ["Unknown", "nan", "\\N", "", "0.0"]: dir_val = str(row.get('director', 'Not Listed'))
        st.markdown(f"<p style='font-size: 0.95rem; color: #fff;'>**{creator_lbl}:** <span style='color:#00f3ff;'>{dir_val}</span></p>", unsafe_allow_html=True)

        st.markdown(f"<p style='color:#d4d4d8; font-size:1.05rem; line-height:1.7; margin-top:10px; margin-bottom:20px; background: rgba(0,0,0,0.4); padding: 15px; border-radius: 8px; border-left: 3px solid #00f3ff; box-shadow: inset 0 0 20px rgba(0, 243, 255, 0.05);'>{synopsis}</p>", unsafe_allow_html=True)
        
        # --- NEW: NOTABLE CHARACTERS SECTION ---
        characters = []
        for person in web_data.get("cast", []):
            role_name = person.get("role", "")
            if role_name and role_name.lower() not in ["actor", "crew", "character", "unknown", "director", "writer"]:
                characters.append(role_name)
                
        characters = list(dict.fromkeys(characters))
        
        if characters:
            st.markdown("<h4 style='font-family: \"Space Grotesk\", sans-serif; color: #00f3ff; margin-bottom: 10px; text-shadow: 0 0 5px rgba(0, 243, 255, 0.5);'>🦸 Notable Characters</h4>", unsafe_allow_html=True)
            char_html = "".join([f'<span class="genre-tag" style="background: rgba(188, 19, 254, 0.15); border-color: rgba(188, 19, 254, 0.4); color: #fff; border-radius: 12px; padding: 6px 14px; font-size: 0.85rem;">{c}</span>' for c in characters])
            st.markdown(f"<div style='margin-bottom:25px;'>{char_html}</div>", unsafe_allow_html=True)

        # --- CAST AND CREW SECTION ---
        cast_title = "Voice Actors" if cat_type == "Anime" else "Cast & Crew"
        st.markdown(f"<h4 style='font-family: \"Space Grotesk\", sans-serif; color: #bc13fe; margin-bottom: 10px; text-shadow: 0 0 5px rgba(188, 19, 254, 0.5);'>🎭 {cast_title}</h4>", unsafe_allow_html=True)
        
        if web_data["cast"]:
            cast_html = '<div class="cast-container">'
            for person in web_data["cast"]:
                cast_html += f'<div class="cast-card"><img src="{person["image"]}" class="cast-img" loading="lazy"><div class="cast-info"><div class="cast-name" title="{person["name"]}">{person["name"]}</div><div class="cast-role" title="{person["role"]}">{person["role"]}</div><div class="cast-sub-role" title="{person["sub_role"]}">{person["sub_role"]}</div></div></div>'
            cast_html += '</div>'
            st.markdown(cast_html, unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#8892b0; font-style:italic;'>Cast and crew data could not be extracted from Wikipedia records. Try clearing the system cache.</p>", unsafe_allow_html=True)

        st.markdown("<h4 style='font-family: \"Space Grotesk\", sans-serif; color: #bc13fe; text-shadow: 0 0 5px rgba(188, 19, 254, 0.5);'>📺 Official Trailer</h4>", unsafe_allow_html=True)
        trailer_url = get_youtube_trailer_url(row['title'], row['year'])
        if trailer_url: st.video(trailer_url)
        else: st.info("No trailer available for this title. 📡")

# --- 6. UI CARD RENDERER ---
def render_movie_card(row, source_genres_list=None):
    cat_type = row.get('category_type', '')
    tconst_id = row.get('tconst', None)
    
    web_data = fetch_info_from_internet(row['title'], row['year'], cat_type, tconst_id)
    
    poster_path = row.get('poster_path', None)
    if pd.notna(poster_path) and str(poster_path).strip() != "" and str(poster_path) != "nan": 
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if str(poster_path).startswith('/') else poster_path
    else: 
        poster_url = web_data["poster"]

    row_genres = str(row['genres']).split()
    genres_html = "".join([f'<span class="genre-tag">{g}</span>' for g in row_genres[:2]])
    fallback_img = f"https://placehold.co/500x750/0a0a0f/00f3ff?text={urllib.parse.quote('Image Missing')}"
    
    ai_reasoning_html = f'<div class="ai-reasoning" style="font-size:0.65rem; padding:4px 8px;">⚡ Match: {", ".join(list(set(source_genres_list).intersection(set(row_genres)))[:2])}</div>' if source_genres_list and list(set(source_genres_list).intersection(set(row_genres))) else ""
    cat_badge = f'<div class="category-badge">{cat_type}</div>' if cat_type else ""

    html_card = f"""<div class="movie-card">{cat_badge}<div class="rating-badge"><span>★</span> {row['rating']:.1f}</div><div style="position: relative; overflow: hidden;"><img src="{poster_url}" style="width:100%; height:360px; object-fit:cover; filter: brightness(0.9) contrast(1.1);" onerror="this.src='{fallback_img}';"><div style="position: absolute; bottom: 0; left: 0; right: 0; height: 50%; background: linear-gradient(to top, rgba(7,7,10,1), transparent);"></div></div><div style="padding:16px; flex:1; display:flex; flex-direction:column; position: relative; z-index: 2; margin-top: -30px;"><h4 style="margin:0 0 10px 0; font-family: 'Space Grotesk', sans-serif; font-size:1.2rem; font-weight:700; line-height:1.2; min-height:2.4rem; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; text-shadow: 0 2px 4px rgba(0,0,0,0.8);">{row['title']}</h4><div style="margin-bottom:4px;">{genres_html}</div>{ai_reasoning_html}</div></div>"""
    return html_card

# --- 7. MAIN APPLICATION LOOP ---
def main():
    inject_custom_css()
    
    if 'watchlist' not in st.session_state: st.session_state.watchlist = []
    if 'tm_recs' not in st.session_state: st.session_state.tm_recs = None
    if 'tm_source' not in st.session_state: st.session_state.tm_source = None
    
    with st.sidebar:
        st.markdown("<h1 style='color:#ffffff; font-family: \"Space Grotesk\", sans-serif; font-size:2.2rem; font-weight:800; line-height:1; margin-bottom:-5px; letter-spacing:-1px; text-shadow: 0 0 5px #00f3ff, 0 0 10px #00f3ff, 0 0 20px #00f3ff;'>POPCORN AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#bc13fe; font-family: \"Space Grotesk\", sans-serif; font-size:0.8rem; margin-bottom:20px; letter-spacing: 1px; text-transform: uppercase; text-shadow: 0 0 5px rgba(188, 19, 254, 0.8);'>Entertainment Recommendation System</p>", unsafe_allow_html=True)
        
        if st.button("🔄 Clear System Cache", use_container_width=True, help="Click this if images or cast members stop loading."):
            st.cache_data.clear()
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        
        category = st.radio("Select Category", ["Movies", "TV Shows", "Anime", "All Collections (Crossover)"])
        st.markdown("---")
        
        df = DataLoader.load(category)
        
        st.subheader("⚙️ Search Filters")
        if not df.empty:
            df['filter_end_year'] = pd.to_numeric(df.get('end_year', df['year']), errors='coerce').fillna(2026)
            min_y, max_y = int(df['year'].min()), int(df['year'].max())
            year_range = st.slider("Release Year Range", min_y, max_y, (max(min_y, 2010), max_y))
            
            all_genres_raw = " ".join(df['genres'].dropna().astype(str).tolist()).split()
            unique_genres = [g for g in sorted(list(set(all_genres_raw))) if g not in ["N/A", "Unknown", "nan"]]
            selected_genres = st.multiselect("Select Genres", unique_genres, default=[])
        else:
            year_range, selected_genres = (2000, 2026), []
            
        min_rating = st.slider("Minimum Rating", 0.0, 10.0, 5.0, 0.5)
        st.markdown("---")
        
        if st.button("🎲 Random Pick", use_container_width=True):
            if not df.empty:
                filtered = df[(df['year'] <= year_range[1]) & (df['filter_end_year'] >= year_range[0]) & (df['rating'] >= min_rating)]
                if selected_genres: filtered = filtered[filtered['genres'].str.contains('|'.join([re.escape(g) for g in selected_genres]), case=False, na=False)]
                if not filtered.empty: show_movie_modal(filtered.sample(1).iloc[0])
                else: st.warning("No titles match your current filters.")

    if df.empty:
        st.error(f"Error: Please run setup_ai.py first to initialize the data files for {category}.")
        return

    vectorizer, matrix, pca_coords = load_ai_models(category)
    
    st.markdown('<div class="hero-title">Entertainment Recommendation System</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Discover your next favorite movie, TV show, or anime.</div>', unsafe_allow_html=True)

    tab_match, tab_universe, tab_profile, tab_analytics = st.tabs(["⚡ Recommendations", "🌌 Explore Database", "👤 My Profile", "📈 Analytics"])

    with tab_match:
        st.markdown("<br>", unsafe_allow_html=True)
        col_search, col_btn_det, col_btn_gen = st.columns([2, 1, 1])
        with col_search: selected_movie = st.selectbox("Select a title to get recommendations:", df['title'].values, label_visibility="collapsed")
        with col_btn_det:
            if st.button("▶ View Details", use_container_width=True) and selected_movie: show_movie_modal(df[df['title'] == selected_movie].iloc[0])
        with col_btn_gen: 
            if st.button("Find Similar Titles", use_container_width=True):
                loader_placeholder = st.empty()
                show_custom_loader(loader_placeholder, "Finding similar titles...")
                time.sleep(0.6) 
                st.session_state.tm_recs, st.session_state.tm_source = get_recommendations_by_title(selected_movie, df, matrix), selected_movie
                loader_placeholder.empty()

        if st.session_state.tm_recs is not None and st.session_state.tm_source == selected_movie:
            recs = st.session_state.tm_recs
            if not recs.empty:
                recs = recs[(recs['year'] <= year_range[1]) & (recs['filter_end_year'] >= year_range[0]) & (recs['rating'] >= min_rating)]
                if selected_genres: recs = recs[recs['genres'].str.contains('|'.join([re.escape(g) for g in selected_genres]), case=False, na=False)]
            
            if not recs.empty:
                st.markdown(f"<h3 style='margin-top:40px; margin-bottom:20px; font-weight:300; font-family: \"Space Grotesk\", sans-serif;'>Titles similar to <b style='color:#00f3ff; text-shadow: 0 0 10px rgba(0,243,255,0.6);'>{selected_movie}</b></h3>", unsafe_allow_html=True)
                source_genres = str(df[df['title'] == selected_movie].iloc[0]['genres']).split()
                cols = st.columns(4)
                for i, (_, row) in enumerate(recs.iterrows()):
                    with cols[i % 4]:
                        with st.container():
                            st.markdown(render_movie_card(row, source_genres), unsafe_allow_html=True)
                            if st.button("View Details", key=f"det_tm_{i}_{row['title']}", use_container_width=True): show_movie_modal(row)
                            st.markdown("<br>", unsafe_allow_html=True)
            else: st.warning("No similar titles found with the current filters.")

    with tab_universe:
        st.markdown("<br><h3 style='font-family: \"Space Grotesk\", sans-serif; text-shadow: 0 0 10px rgba(188, 19, 254, 0.5);'>Explore the Database</h3>", unsafe_allow_html=True)
        if len(df) >= 3 and pca_coords.shape[1] >= 2:
            df_plot = df.sample(min(len(df), 5000), random_state=42).copy()
            df_plot['x'], df_plot['y'] = pca_coords[df_plot.index, 0], pca_coords[df_plot.index, 1]
            fig_scatter = px.scatter(df_plot, x='x', y='y', hover_name='title', color='rating', color_continuous_scale=["#001111", "#00f3ff", "#ffffff"], hover_data=['year', 'category_type'], template="plotly_dark", opacity=0.8)
            fig_scatter.update_traces(marker=dict(size=6, line=dict(width=0)))
            fig_scatter.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_visible=False, yaxis_visible=False, coloraxis_showscale=False)
            st.plotly_chart(fig_scatter, use_container_width=True)
        else: st.warning("Not enough data to map on a 2D chart.")

    with tab_profile:
        st.markdown("<br><h3 style='font-family: \"Space Grotesk\", sans-serif; text-shadow: 0 0 10px rgba(0, 243, 255, 0.5);'>User Profile & Stats</h3>", unsafe_allow_html=True)
        if len(st.session_state.watchlist) >= 3:
            watch_df = df[df['title'].isin(st.session_state.watchlist)]
            st.columns(3)[0].metric("Watchlist Items", len(watch_df))
            st.columns(3)[1].metric("Average Rating", f"★ {watch_df['rating'].mean():.1f}")
            st.columns(3)[2].metric("Average Release Year", int(watch_df['year'].mean()))
            
            st.markdown("---")
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                genre_counts = pd.Series(" ".join(watch_df['genres'].tolist()).split()).value_counts().head(5)
                fig_radar = go.Figure(data=go.Scatterpolar(r=genre_counts.values, theta=genre_counts.index, fill='toself', marker_color='#00f3ff'))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=False), bgcolor='rgba(20,20,25,0.5)'), showlegend=False, template="plotly_dark", title="Top Genres", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_radar, use_container_width=True)
            with col_chart2:
                cat_counts = watch_df.get('category_type', pd.Series(["Movies"]*len(watch_df))).value_counts()
                fig_pie = px.pie(names=cat_counts.index, values=cat_counts.values, hole=0.5, title="Category Distribution", template="plotly_dark", color_discrete_sequence=['#00f3ff', '#bc13fe', '#ff0055'])
                fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_pie, use_container_width=True)
        else: st.info("Add at least 3 titles to your Watchlist to unlock your profile stats!")

    with tab_analytics:
        st.markdown("<br><h3 style='font-family: \"Space Grotesk\", sans-serif;'>Database Analytics</h3>", unsafe_allow_html=True)
        col_left, col_right = st.columns(2)
        with col_left:
            fig_hist = px.histogram(df, x="rating", title="Global Rating Distribution", template="plotly_dark", color_discrete_sequence=['#00f3ff'])
            fig_hist.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_hist, use_container_width=True)
        with col_right:
            st.write("<h4 style='font-family: \"Space Grotesk\", sans-serif; color: #bc13fe;'>🏆 Top Rated Titles</h4>", unsafe_allow_html=True)
            st.dataframe(df.nlargest(10, 'rating')[['title', 'category_type', 'rating', 'year']], use_container_width=True, hide_index=True)

    with st.sidebar:
        st.markdown("---")
        st.subheader("📋 Your Watchlist")
        if st.session_state.watchlist:
            for movie in st.session_state.watchlist: st.markdown(f"<div style='border-left: 2px solid #00f3ff; padding-left: 10px; margin-bottom: 5px; background: rgba(0,243,255,0.05); text-shadow: 0 0 5px rgba(255,255,255,0.2);'>🍿 <i>{movie}</i></div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            def create_pdf(watchlist):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "Entertainment Recommendation System", ln=True, align='C')
                pdf.set_font("Arial", 'I', 12)
                pdf.cell(0, 10, "Watchlist Items", ln=True, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", size=12)
                for idx, title in enumerate(watchlist, 1): pdf.cell(0, 10, f"{idx}. {title.encode('latin-1', 'replace').decode('latin-1')}", ln=True)
                return pdf.output(dest='S').encode('latin-1')

            col_a, col_b = st.columns(2)
            with col_a: st.download_button(label="📄 Export PDF", data=create_pdf(st.session_state.watchlist), file_name="Popcorn_Data.pdf", mime="application/pdf", use_container_width=True)
            with col_b:
                if st.button("🗑️ Clear", use_container_width=True):
                    st.session_state.watchlist = []
                    st.rerun()
        else: st.info("Your watchlist is empty. Add some titles to get started.")

if __name__ == "__main__":
    main()