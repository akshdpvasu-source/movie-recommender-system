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
    recommended_overviews = []
    recommended_ratings = []

    for item in movies_list:
        idx = item[0]

        movie_id = movies.iloc[idx].movie_id
        movie_title = movies.iloc[idx].title

        recommended_movies.append(movie_title)
        poster, rating, overview = get_movie_details(movie_title)

        recommended_movies_posters.append(poster)
        recommended_ratings.append(rating)
        recommended_overviews.append(overview)


        trailer = fetch_trailer(movie_id)
        recommended_trailers.append(trailer)

        time.sleep(0.3)

    return (
        recommended_movies,
        recommended_movies_posters,
        recommended_trailers,
        recommended_ratings,
        recommended_overviews
    )
def get_movie_details(movie_title):
    try:
        response = session.get(
            "https://api.themoviedb.org/3/search/movie",
            params={
                "api_key": API_KEY,
                "query": movie_title
            },
            headers=HEADERS,
            timeout=10
        )

        data = response.json()

        if data.get("results") and len(data["results"]) > 0:
            movie = data["results"][0]

            poster_path = movie.get("poster_path")
            rating = movie.get("vote_average", "N/A")
            overview = movie.get("overview", "No description available.")


            if len(overview) > 250:
                overview = overview[:250] + "..."

            if poster_path:
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            else:
                poster_url = "https://via.placeholder.com/220x330?text=No+Poster"

            return poster_url, rating, overview

    except Exception:
        pass

    return (
        "https://via.placeholder.com/220x330?text=No+Poster",
        "N/A",
        "No description available."
    )
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



movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
import gzip

with gzip.open("similarity.pkl.gz", "rb") as f:
    similarity = pickle.load(f)

selected_movie_name = st.selectbox(
    "Tell me the Name and I will Recommend You Similar five movies",
    movies['title'].values,
    index=None,
    placeholder="Search for a movie..."
)

if selected_movie_name:
    names, posters, trailers, ratings, overviews = recommend(selected_movie_name)

    st.subheader("🎥 Selected Movie")

    col1, col2 = st.columns([1,2])

    selected_idx = movies[movies['title'] == selected_movie_name].index[0]
    selected_movie_id = movies.iloc[selected_idx].movie_id

    poster_url, rating, overview = get_movie_details(selected_movie_name)

    with col1:
        st.image(poster_url, width=220)

    with col2:
        st.markdown(f"## {selected_movie_name}")
        st.write(f"⭐ **Rating:** {rating}/10")
        st.write("**Summary**")
        st.write(overview)
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

if st.button("🎬 Recommend") and selected_movie_name:

    progress_text = "🍿 Finding the best movies for you..."
    progress = st.progress(0, text=progress_text)

    for percent in range(101):
        time.sleep(0.01)
        progress.progress(percent, text=progress_text)

    names, posters, trailers, ratings, overviews = recommend(selected_movie_name)

    progress.empty()

    st.success("✅ Recommendations Ready!")

    cols = st.columns(5)
    for i in range(5):
        with cols[i]:

            st.markdown(f"### {names[i]}")

            try:
                st.image(posters[i], width=170)

                st.write(f"⭐ **{ratings[i]}/10**")

                st.caption(overviews[i])

                if trailers[i]:
                    st.link_button("▶ Watch Trailer", trailers[i])

            except Exception:
                st.image(
                    "https://via.placeholder.com/220x330?text=No+Poster",
                    width=170
                )

                st.write("⭐ N/A")
                st.caption("No summary available.")

            if trailers[i]:
                st.video(trailers[i])