import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
import joblib
import os
import logging
import warnings

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.makedirs('ai_models', exist_ok=True)

# --- 1. CONVERT CSV TO PARQUET ---
def convert_and_clean_data():
    files = {
        "Movies": "movies.csv", 
        "TV Shows": "tv_shows.csv", 
        "Anime": "anime.csv"
    }
    
    for category_name, file_path in files.items():
        if not os.path.exists(file_path):
            logger.warning(f"Missing {file_path}. Skipping.")
            continue
            
        logger.info(f"Converting and cleaning {file_path}...")
        df = pd.read_csv(file_path, on_bad_lines='skip', engine='c')
        df.columns = [str(c).strip() for c in df.columns]

        if category_name == "Anime":
            if 'title_english' in df.columns and 'title' in df.columns:
                df['title_english'] = df['title_english'].replace('', pd.NA)
                df['title'] = df['title_english'].fillna(df['title'])
            
            if 'rating' in df.columns:
                df = df.rename(columns={'rating': 'age_rating'})

        rename_map = {}
        if category_name == "Anime":
            rename_map = {'score': 'rating', 'synopsis': 'overview', 'studios': 'director'}
        elif category_name == "Movies":
            rename_map = {'primaryTitle': 'title', 'averageRating': 'rating', 'directors': 'director', 'startYear': 'year', 'runtimeMinutes': 'runtime'} 
        elif category_name == "TV Shows":
            rename_map = {'primaryTitle': 'title', 'averageRating': 'rating', 'directors': 'director', 'startYear': 'year', 'endYear': 'end_year'}

        df = df.rename(columns=rename_map)
        df = df.loc[:, ~df.columns.duplicated()]

        essential = ['title', 'rating', 'overview', 'genres', 'director']
        for col in essential:
            if col not in df.columns:
                df[col] = 0.0 if col == 'rating' else "Unknown"

        df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0.0)
        df['overview'] = df['overview'].fillna("No synopsis available.").astype(str)
        df['genres'] = df['genres'].fillna("N/A").astype(str).str.replace(r'[|,\-]', ' ', regex=True)
        df['director'] = df['director'].fillna("Unknown").astype(str)
        df['category_type'] = category_name 
        
        if category_name == "Anime" and 'aired' in df.columns:
            df['year'] = df['aired'].astype(str).str.extract(r'(\d{4})')[0]
        
        df['year'] = pd.to_numeric(df.get('year'), errors='coerce').fillna(2000).astype(int)
        df = df.drop_duplicates(subset=['title', 'year'], keep='first').reset_index(drop=True)
        
        parquet_path = file_path.replace('.csv', '.parquet')
        df.to_parquet(parquet_path, engine='pyarrow', index=False)
        logger.info(f"Saved optimized dataset to {parquet_path}")

# --- 2. BUILD AI MATRICES ---
def load_parquet_data(category):
    files = {"Movies": "movies.parquet", "TV Shows": "tv_shows.parquet", "Anime": "anime.parquet"}
    if category == "All Collections (Crossover)":
        dfs = []
        for cat, f in files.items():
            if os.path.exists(f):
                dfs.append(pd.read_parquet(f, engine='pyarrow'))
        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    else:
        file_path = files.get(category)
        if file_path and os.path.exists(file_path):
            return pd.read_parquet(file_path, engine='pyarrow')
        return pd.DataFrame()

def build_ai_models():
    categories = ["Movies", "TV Shows", "Anime", "All Collections (Crossover)"]

    for cat in categories:
        logger.info(f"Building AI matrices for {cat}...")
        df = load_parquet_data(cat)
        
        if df.empty:
            continue

        features = df['genres'] + " " + df['overview']
        if 'themes' in df.columns: features += " " + df['themes'].fillna("").astype(str)
        if 'writers' in df.columns: features += " " + df['writers'].fillna("").astype(str)

        # N-Grams added to capture phrases
        vectorizer = TfidfVectorizer(stop_words='english', max_features=6000, ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(features)
        
        svd = TruncatedSVD(n_components=2, random_state=42)
        coords = svd.fit_transform(matrix)
        
        safe_name = cat.replace(" ", "_").replace("(", "").replace(")", "").lower()
        joblib.dump(vectorizer, f'ai_models/vectorizer_{safe_name}.joblib')
        joblib.dump(matrix, f'ai_models/matrix_{safe_name}.joblib')
        joblib.dump(coords, f'ai_models/coords_{safe_name}.joblib')
        
        logger.info(f"Successfully saved AI models for {cat}!\n")

if __name__ == "__main__":
    print("Step 1: Converting CSVs to Parquet...")
    convert_and_clean_data()
    print("\nStep 2: Pre-calculating AI Matrices...")
    build_ai_models()
    print("\n✅ Setup Complete! You can now run your Streamlit app.")