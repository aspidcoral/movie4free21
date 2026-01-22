import asyncio
import logging
import time
import itertools
import threading
import os
import random
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from bot.handlers import router
from nostr.main import post_to_nostr

load_dotenv()
TOKEN = os.getenv("TOKEN_TG_BOT_MOVIES")
from tmdb_api.movie_request import (
    request_trending_movies, 
    pick_unique_trending, 
    request_random_movie,
    pick_unique_random, 
    register_post,
    post_to_telegram
)

def content_loop():
    tasks = itertools.cycle(["trending", "random"])  # alternating forever
    
    while True:
        task = next(tasks)
        
        if task == "trending":
            movies = request_trending_movies()
            if movies:
                movie = pick_unique_trending(movies)
            else:
                continue
        else:
            movie = pick_unique_random()
        
        if movie:
            asyncio.run(post_to_telegram(movie))
            asyncio.run(post_to_nostr(movie))
            register_post(movie["id"])
        
        # Sleep for 3 hours +/- 15 minutes
        sleep_duration = 3 * 60 * 60 + random.randint(-15 * 60, 15 * 60)
        time.sleep(sleep_duration)

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # content_thread = threading.Thread(target=content_loop)
    # content_thread.start()

    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('exit')
