import asyncio
from aiogram import Bot
from dotenv import load_dotenv, find_dotenv
import requests
import os
import time
import datetime
import random

recent_posts = []
MAX_HISTORY = 20
RECENT_POSTS_FILE = "tmdb_api/recent_posts.txt"
genre_cache = None

def get_genre_names():
    global genre_cache
    if genre_cache:
        return genre_cache
    API_KEY = os.getenv("TMDB_API_KEY")
    url = "https://api.themoviedb.org/3/genre/movie/list"
    params = {
        "api_key": API_KEY,
        "language": "en-US",
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        genre_cache = {genre['id']: genre['name'] for genre in data.get('genres', [])}
        print(f"{get_timestamp()} Loaded genres: {genre_cache}")
        return genre_cache
    except requests.exceptions.RequestException as e:
        print(f"{get_timestamp()} Error fetching genres: {e}")
    return None

def get_timestamp():
    return datetime.datetime.now().strftime("[%d.%m.%Y %H:%M:%S]")

def load_recent_posts():
    global recent_posts
    if os.path.exists(RECENT_POSTS_FILE):
        with open(RECENT_POSTS_FILE, "r") as f:
            ids = [int(line.strip()) for line in f if line.strip().isdigit()]
            recent_posts.extend(ids[-MAX_HISTORY:])
        print(f"{get_timestamp()} Loaded recent posts: {recent_posts}")
    else:
        print(f"{get_timestamp()} Recent posts file not found, starting with empty history.")

def save_recent_posts():
    with open(RECENT_POSTS_FILE, "w") as f:
        for movie_id in recent_posts:
            f.write(str(movie_id) + "\n")
    print(f"{get_timestamp()} Saved recent posts: {recent_posts}")

load_recent_posts()

def get_movie_trailer(movie_id):
    API_KEY = os.getenv("TMDB_API_KEY")
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos"
    params = {
        "api_key": API_KEY,
        "language": "en-US",
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        for video in data.get('results', []):
            if video['type'] == 'Trailer' and video['site'] == 'YouTube':
                return f"https://www.youtube.com/watch?v={video['key']}"
    except requests.exceptions.RequestException as e:
        print(f"{get_timestamp()} Error fetching trailer for movie {movie_id}: {e}")
    return None

def register_post(movie_id):
    print(f"{get_timestamp()} Registering post with ID: {movie_id}")
    recent_posts.append(movie_id)
    if len(recent_posts) > MAX_HISTORY:
        recent_posts.pop(0)
    print(f"{get_timestamp()} Recent posts: {recent_posts}")
    save_recent_posts()

def request_trending_movies():
    # Get a list of trending movies
    API_KEY = os.getenv("TMDB_API_KEY")
    url = "https://api.themoviedb.org/3/trending/movie/day"
    params = {
        "api_key": API_KEY,
        "language": "en-US",
    }
    try:
        print(f"{get_timestamp()} Sending request to TMDB for trending movies")
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()
        movies = data.get('results', [])
        print(f"{get_timestamp()} Got {len(movies)} trending movies")
        for movie in movies:
            movie['trailer_url'] = get_movie_trailer(movie['id'])
        return movies
    except requests.exceptions.HTTPError as http_err:
        print(f"{get_timestamp()} HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"{get_timestamp()} An error occurred: {req_err}")
    except ValueError:
        print(f"{get_timestamp()} Failed to decode JSON response.")
    return None

def request_random_movie():
    # Get a random movie
    API_KEY = os.getenv("TMDB_API_KEY")
    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "api_key": API_KEY,
        "language": "en-US",
        "sort_by": "popularity.desc",
        "include_adult": "false",
        "page": 1
    }
    try:
        print(f"{get_timestamp()} Sending request to TMDB for a random movie (getting total pages)")
        response = requests.get(url, params=params)
        response.raise_for_status()
        total_pages = response.json().get('total_pages')
        if not total_pages:
            print(f"{get_timestamp()} Could not get total pages for random movie.")
            return None

        random_page = random.randint(1, min(total_pages, 500)) # TMDB limits to 500 pages
        params["page"] = random_page
        print(f"{get_timestamp()} Sending request to TMDB for a random movie (page {random_page})")
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if not data.get('results'):
            print(f"{get_timestamp()} No results found for random movie.")
            return None
        
        random_movie = random.choice(data['results'])
        random_movie['trailer_url'] = get_movie_trailer(random_movie['id'])
        print(f"{get_timestamp()} Got random movie: {random_movie.get('title')}")
        return random_movie
    except requests.exceptions.HTTPError as http_err:
        print(f"{get_timestamp()} HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"{get_timestamp()} An error occurred: {req_err}")
    except ValueError:
        print(f"{get_timestamp()} Failed to decode JSON response.")
    return None

# For trending:
def pick_unique_trending(all_movies):
    print(f"{get_timestamp()} Picking unique trending movie")
    for movie in all_movies:
        if movie["id"] not in recent_posts:
            print(f"{get_timestamp()} Found unique movie: {movie['title']}")
            return movie
    print(f"{get_timestamp()} No unique movie found, returning random from trending")
    return random.choice(all_movies)  # fallback

# For random:
def pick_unique_random():
    print(f"{get_timestamp()} Picking unique random movie")
    max_retries = 20
    for i in range(max_retries):
        movie = request_random_movie()
        if movie is None:
            print(f"{get_timestamp()} Failed to fetch random movie (API error), attempt {i+1}/{max_retries}")
            time.sleep(2) # Wait a bit before retrying
            continue

        if movie["id"] not in recent_posts:
            print(f"{get_timestamp()} Found unique movie: {movie['title']}")
            return movie
        
        print(f"{get_timestamp()} Movie '{movie['title']}' already in recent posts, trying again")
    
    print(f"{get_timestamp()} Could not find a unique random movie after {max_retries} attempts.")
    return None


async def post_to_telegram(movie):
    print(f"{get_timestamp()} Start making post")
    BOT_TOKEN = os.getenv("TOKEN_TG_BOT_POSTER")
    CHANNEL_ID = os.getenv("CHANNEL_TG")
    BASE_IMG = "https://image.tmdb.org/t/p/original"

    if not all([BOT_TOKEN, CHANNEL_ID]):
        print(f"{get_timestamp()} Bot token or channel ID is not set. Please check your environment variables.")
        return

    bot = Bot(token=BOT_TOKEN)
    
    print(f"{get_timestamp()} Making a new post")
    title = movie.get("title", "No title")
    date = movie.get("release_date", "No date")
    backdrop = movie.get("backdrop_path")
    overview = movie.get("overview")
    rating = movie.get("vote_average")
    votes = movie.get("vote_count")
    id = movie.get("id")
    trailer_url = movie.get("trailer_url")
    genre_ids = movie.get("genre_ids", [])
    genres = get_genre_names()
    genre_names = [genres.get(genre_id) for genre_id in genre_ids if genres and genres.get(genre_id)]
    genre_hashtags = " ".join([f"#{genre.replace(' ', '')}" for genre in genre_names])


    if not backdrop:
        print(f"{get_timestamp()} No picture, skip")
        return

    img_url = BASE_IMG + backdrop
    text = f"""🎬 <u><b>{title}</b></u> ({date[:4]})

📄<b>Overview:</b> <i>{overview}</i>
⭐<b>Rating:</b> {rating} ({votes} votes)\n

#movies #free #hd {genre_hashtags}

🎥<a href='https://www.vidking.net/embed/movie/{id}'>Watch here</a> | <a href='https://t.me/Movies4Free21Bot?start=1'>Search Movies</a>"""
    if trailer_url:
        text += f" | <a href='{trailer_url}'>Trailer</a>"

    await bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=img_url,
        caption=text,
        parse_mode="HTML"
    )
    print(f"{get_timestamp()} Post sent")
    await bot.session.close()

if __name__ == "__main__":
    load_dotenv(find_dotenv())
    get_genre_names()

    async def test_posts():
        print(f"{get_timestamp()} --- Testing Trending Movie Post ---")
        trending_movies = request_trending_movies()
        if trending_movies:
            trending_movie = pick_unique_trending(trending_movies)
            if trending_movie:
                register_post(trending_movie["id"])
                await post_to_telegram(trending_movie)
            else:
                print(f"{get_timestamp()} No trending movie picked.")
        else:
            print(f"{get_timestamp()} No trending movies found.")

        print(f"{get_timestamp()} --- Testing Random Movie Post ---")
        random_movie = pick_unique_random()
        if random_movie:
            register_post(random_movie["id"])
            await post_to_telegram(random_movie)
        else:
            print(f"{get_timestamp()} No random movie picked.")

    asyncio.run(test_posts())
    print(f"{get_timestamp()} --- Test Complete ---")
