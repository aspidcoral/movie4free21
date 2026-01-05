from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram import Router, F
from tmdb_api.search import search_movie
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from bot.keyboards import get_pagination_keyboard
import math
from datetime import datetime
import re

router = Router()

class SearchState(StatesGroup):
    results = State()
    page = State()
    waiting_for_movie_name = State()

def log_message(user, action, bot_message=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if bot_message:
        print(f"[{timestamp}] [{user}] [{action}]\n[{timestamp}] [bot] [{bot_message}]")
    else:
        print(f"[{timestamp}] [{user}] [{action}]")

def escape_markdown(text):
    """Escapes special characters for MarkdownV2."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def format_movies(movies):
    result_string = ""
    for i, movie in enumerate(movies):
        title = escape_markdown(f"{movie['title']} ({movie.get('release_date', 'N/A')[:4]})")
        overview = escape_markdown(movie['overview'])
        rating = escape_markdown(f"{movie['vote_average']}({movie['vote_count']} votes)")
        original_language = escape_markdown(movie['original_language'])
        movie_id = movie['id']

        result_string += f"*{i+1}\\.* __{title}__\n"
        result_string += f"*Overview:* _{overview}_\n"
        result_string += f"*Rating:* {rating}\n"
        result_string += f"*Original language:* {original_language}\n"
        result_string += f"[Watch here](https://www.vidking.net/embed/movie/{movie_id}) \\| [TG Channel](https://t.me/movies4free21)\n\n"
    return result_string

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user.username
    action = "/start"
    log_message(user, action)
    bot_message = f"Hello, *{escape_markdown(message.from_user.first_name)}*, You’re using a bot for searching movies 🎬\nTo start searching, send the /search command, then enter the movie name"
    await message.answer(text=bot_message, parse_mode='MarkdownV2')
    log_message(user, action, bot_message)


@router.message(Command("search"))
async def search_start(message: Message, state: FSMContext):
    user = message.from_user.username
    action = "/search"
    log_message(user, action)
    bot_message = "Please enter the name of the movie you’re looking for: 🎥\n(Movie title only)"
    await message.answer(bot_message)
    log_message(user, action, bot_message)
    await state.set_state(SearchState.waiting_for_movie_name)


@router.message(SearchState.waiting_for_movie_name)
async def search_process_name(message: Message, state: FSMContext):
    user = message.from_user.username
    movie_name = message.text
    action = f"search for '{movie_name}'"
    log_message(user, action)

    results = search_movie(movie_name)

    if isinstance(results, list) and results:
        await state.update_data(results=results, page=0)
        await state.set_state(None)

        total_pages = math.ceil(len(results) / 5)
        bot_message = format_movies(results[:5])
        await message.answer(bot_message,
                             reply_markup=get_pagination_keyboard(page=0, total_pages=total_pages),
                             parse_mode='MarkdownV2')
        log_message(user, action, bot_message)
    elif isinstance(results, list) and not results:
        bot_message = "No movies were found with that name 😕\nPlease make sure you didn’t include the year or any extra information 🎬✨"
        await message.answer(bot_message)
        log_message(user, action, bot_message)
        await state.clear()
    else:
        await message.answer(results)
        log_message(user, action, results)
        await state.clear()

@router.callback_query(F.data.startswith("next_"))
async def next_page(callback: CallbackQuery, state: FSMContext):
    user = callback.from_user.username
    action = "next_page callback"
    log_message(user, action)
    page = int(callback.data.split("_")[1])
    data = await state.get_data()
    results = data.get("results")
    if results:
        await state.update_data(page=page)
        total_pages = math.ceil(len(results) / 5)
        start = page * 5
        end = start + 5
        bot_message = format_movies(results[start:end])
        await callback.message.edit_text(bot_message,
                                         reply_markup=get_pagination_keyboard(page=page, total_pages=total_pages),
                                         parse_mode='MarkdownV2')
        log_message(user, action, bot_message)
    await callback.answer()

@router.callback_query(F.data.startswith("prev_"))
async def prev_page(callback: CallbackQuery, state: FSMContext):
    user = callback.from_user.username
    action = "prev_page callback"
    log_message(user, action)
    page = int(callback.data.split("_")[1])
    data = await state.get_data()
    results = data.get("results")
    if results:
        await state.update_data(page=page)
        total_pages = math.ceil(len(results) / 5)
        start = page * 5
        end = start + 5
        bot_message = format_movies(results[start:end])
        await callback.message.edit_text(bot_message,
                                         reply_markup=get_pagination_keyboard(page=page, total_pages=total_pages),
                                         parse_mode='MarkdownV2')
        log_message(user, action, bot_message)
    await callback.answer()

