import keyword

import streamlit as st
import pickle
import time
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()

retry = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)

adapter = HTTPAdapter(max_retries=retry)

session.mount("https://", adapter)
session.mount("http://", adapter)

API_KEY = "c68b3ea5107251e1067add4122fd29cb"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}
OFFLINE_POSTERS = {
    "action": "offline_posters/action.jpg",
    "adventure": "offline_posters/adventure.jpg",
    "comedy": "offline_posters/comedy.jpg",


    "history": "offline_posters/history.jpg",
    "horror": "offline_posters/horror.jpg",
    "batman": "offline_posters/batman.jpg",
    "science fiction": "offline_posters/scifi.jpg",
    "default": "offline_posters/default.jpg",
    "western": "offline_posters/western.jpg",

}


def search_poster_by_title(movie_title):
    try:
        headers = HEADERS

        response = session.get(
            "https://api.themoviedb.org/3/search/movie",
            params={
                "api_key": API_KEY,
                "query": movie_title
            },
            headers=headers,
            timeout=10
        )

        data = response.json()

        if data.get("results") and len(data["results"]) > 0:
            poster_path = data["results"][0].get("poster_path")

            if poster_path:
                return f"https://image.tmdb.org/t/p/w500{poster_path}"

    except Exception as e:
        print(f"Title search failed for {movie_title}: {e}")

    return "https://via.placeholder.com/500x750?text=No+Poster"
def get_offline_poster(movie_title):

    try:
        movie_row = movies[movies["title"] == movie_title]

        if movie_row.empty:
            return OFFLINE_POSTERS["default"]

        tags = str(movie_row.iloc[0]["tags"]).lower()

        for key in OFFLINE_POSTERS:
            if key != "default" and key in tags:
                return OFFLINE_POSTERS[key]

    except:
        pass

    return OFFLINE_POSTERS["default"]

def fetch_poster(movie_id, movie_title):
    try:
        headers = HEADERS

        response = session.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}",
            params={"api_key": API_KEY},
            headers=headers,
            timeout=10
        )

        data = response.json()
        print("=" * 50)
        print("Movie:", movie_title)
        print("Movie ID:", movie_id)
        print("Status Code:", response.status_code)
        print(data)


        print("Movie:", movie_title)
        print("Movie ID:", movie_id)

        poster_path = data.get("poster_path")

        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            print("Poster URL:", poster_url)
            return poster_url

        print("No poster found from movie ID, trying title search...")

        poster = search_poster_by_title(movie_title)

        if "via.placeholder.com" in poster:
            return get_offline_poster(movie_title)

        return poster

    except Exception as e:
        print(f"Poster fetch failed for {movie_title}: {e}")

        poster = search_poster_by_title(movie_title)

        if "via.placeholder.com" in poster:
            return get_offline_poster(movie_title)

        return poster
def fetch_trailer(movie_id):
    try:
        response = session.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}/videos",
            params={"api_key": API_KEY},
            headers=HEADERS,
            timeout=10
        )

        data = response.json()

        if data.get("results"):
            for video in data["results"]:
                if video["site"] == "YouTube" and video["type"] == "Trailer":
                    return f"https://www.youtube.com/watch?v={video['key']}"

    except Exception as e:
        print(e)

    return None

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]

    distances = similarity[movie_index]

    movies_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:6]

    recommended_movies = []
    recommended_movies_posters = []
    recommended_trailers = []

    for item in movies_list:
        idx = item[0]

        movie_id = movies.iloc[idx].movie_id
        movie_title = movies.iloc[idx].title

        recommended_movies.append(movie_title)

        # Fetch poster
        poster = fetch_poster(movie_id, movie_title)
        recommended_movies_posters.append(poster)

        # Fetch trailer
        trailer = fetch_trailer(movie_id)
        recommended_trailers.append(trailer)

        # Small delay to avoid connection reset
        time.sleep(0.3)

    return recommended_movies, recommended_movies_posters, recommended_trailers
def get_movie_details(movie_title):
    try:
        headers = HEADERS

        response = session.get(
            "https://api.themoviedb.org/3/search/movie",
            params={
                "api_key": API_KEY,
                "query": movie_title
            },
            headers=headers,
            timeout=10
        )

        data = response.json()

        if data.get("results") and len(data["results"]) > 0:
            movie = data["results"][0]

            poster_path = movie.get("poster_path")
            rating = movie.get("vote_average", "N/A")

            if poster_path:
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            else:
                poster_url = "https://via.placeholder.com/220x330?text=No+Poster"

            return poster_url, rating

    except Exception:
        pass

    return "https://via.placeholder.com/220x330?text=No+Poster", "N/A"
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 style='text-align:center;
color:#FF4B4B;
font-size:50px;'>
🎬 Movie Recommendation System
</h1>



<p style='text-align:center;
font-size:20px;
color:gray;'>
Find movies you'll love in seconds!
</p>
""", unsafe_allow_html=True)


# Load data
movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
import gzip

with gzip.open("similarity.pkl.gz", "rb") as f:
    similarity = pickle.load(f)

selected_movie_name = st.selectbox(
    "Tell me the Name and I will Recommend You Similar five movies",
    movies['title'].values
)

poster_url, rating = get_movie_details(selected_movie_name)


page_bg = """
<style>
[data-testid="stAppViewContainer"]{
background-image:url("https://images.unsplash.com/photo-1489599849927-2ee91cede3ba");
background-size:cover;
background-attachment:fixed;
}

[data-testid="stHeader"]{
background:rgba(0,0,0,0);
}

[data-testid="stSidebar"]{
background:rgba(0,0,0,0.7);
}
</style>
"""

st.markdown(page_bg, unsafe_allow_html=True)
st.markdown("""
<style>
div.stButton > button{
background:#ff4b4b;
color:white;
font-size:20px;
border-radius:15px;
height:55px;
width:220px;
font-weight:bold;
}

div.stButton > button:hover{
background:blue;
transform:scale(1.05);
transition:0.3s;
}
</style>
""", unsafe_allow_html=True)


if st.button("Recommend"):
    names, posters, trailers = recommend(selected_movie_name)

    cols = st.columns(5)

    for i in range(5):
        with cols[i]:
            st.text(names[i])

            try:

                st.image(posters[i], width=150)
                if trailers[i]:
                    st.link_button("▶ Watch Trailer", trailers[i])
            except:
                st.image(
                    "https://via.placeholder.com/500x750?text=No+Poster",
                    width=150
                )
            if trailers[i]:
                st.video(trailers[i])