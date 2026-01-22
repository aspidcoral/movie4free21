from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram import Router, F
from tmdb_api.search import search_movie, search_tv, get_tv_details
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from bot.keyboards import get_pagination_keyboard, get_seasons_keyboard, get_episodes_keyboard
import math
from datetime import datetime
import re

router = Router()

class SearchState(StatesGroup):
    results = State()
    page = State()
    waiting_for_query = State()

def log_message(user, action, bot_message=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if bot_message:
        print(f"[{timestamp}] [{user}] [{action}]\n[{timestamp}] [bot] [{bot_message}]")
    else:
        print(f"[{timestamp}] [{user}] [{action}]")

def escape_markdown(text):
    """Escapes special characters for MarkdownV2."""
    if not text:
        return ""
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

def format_results(items, item_type='movie'):
    result_string = ""
    for i, item in enumerate(items):
        if item_type == 'movie':
            title_text = item.get('title', 'N/A')
            date_text = item.get('release_date', 'N/A')
            item_id = item['id']
            link = f"[Watch here](https://www.vidking.net/embed/movie/{item_id})"
        else:
            title_text = item.get('name', 'N/A')
            date_text = item.get('first_air_date', 'N/A')
            item_id = item['id']
            link = f"Watch here: /view\_tv\_{item_id}"
        
        year = date_text[:4] if date_text and len(date_text) >= 4 else 'N/A'
        
        title = escape_markdown(f"{title_text} ({year})")
        overview = escape_markdown(item.get('overview', 'No overview'))
        rating = escape_markdown(f"{item.get('vote_average', 0)}({item.get('vote_count', 0)} votes)")
        original_language = escape_markdown(item.get('original_language', 'N/A'))

        result_string += f"*{i+1}\\.* __{title}__\n"
        result_string += f"*Overview:* _{overview}_\n"
        result_string += f"*Rating:* {rating}\n"
        result_string += f"*Original language:* {original_language}\n"
        result_string += f"{link} \\| [TG Channel](https://t.me/movies4free21)\n\n"
    return result_string

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user.username
    action = "/start"
    log_message(user, action)
    bot_message = f"Hello, *{escape_markdown(message.from_user.first_name)}*, You’re using a bot for searching movies & TV shows 🎬\nTo start searching, use /movie or /tv\_show commands"
    await message.answer(text=bot_message, parse_mode='MarkdownV2')
    log_message(user, action, bot_message)

@router.message(Command("movie"))
async def cmd_movie(message: Message, state: FSMContext):
    user = message.from_user.username
    action = "/movie"
    log_message(user, action)
    bot_message = "Please enter the name of the movie you’re looking for: 🎥\n(Movie title only)"
    await message.answer(bot_message)
    log_message(user, action, bot_message)
    await state.update_data(search_type='movie')
    await state.set_state(SearchState.waiting_for_query)

@router.message(Command("tv_show"))
async def cmd_tv(message: Message, state: FSMContext):
    user = message.from_user.username
    action = "/tv_show"
    log_message(user, action)
    bot_message = "Please enter the name of the TV show you’re looking for: 📺\n(TV show name only)"
    await message.answer(bot_message)
    log_message(user, action, bot_message)
    await state.update_data(search_type='tv')
    await state.set_state(SearchState.waiting_for_query)

@router.message(F.text.regexp(r"^/view_tv_(\d+)$"))
async def process_view_tv(message: Message):
    user = message.from_user.username
    match = re.match(r"^/view_tv_(\d+)$", message.text)
    if not match:
        return
    
    tv_id = int(match.group(1))
    action = f"view_tv_{tv_id}"
    log_message(user, action)

    tv_details = get_tv_details(tv_id)
    if tv_details:
        seasons = tv_details.get('seasons', [])
        if seasons:
            bot_message = f"Select a season for *{escape_markdown(tv_details.get('name', 'TV Show'))}*:"
            await message.answer(bot_message, reply_markup=get_seasons_keyboard(seasons, tv_id), parse_mode='MarkdownV2')
            log_message(user, action, bot_message)
        else:
            await message.answer("No seasons found for this TV show.")
    else:
        await message.answer("Failed to retrieve TV show details.")

@router.callback_query(F.data.startswith("season_"))
async def process_season_selection(callback: CallbackQuery):
    user = callback.from_user.username
    action = f"selected season callback: {callback.data}"
    log_message(user, action)
    
    # data format: season_{tv_id}_{season_number}_{episode_count}
    parts = callback.data.split("_")
    if len(parts) >= 4:
        tv_id = parts[1]
        season_number = parts[2]
        episode_count = int(parts[3])
        
        bot_message = f"Select an episode for Season {season_number}:"
        await callback.message.answer(bot_message, reply_markup=get_episodes_keyboard(tv_id, season_number, episode_count))
    elif len(parts) == 3:
         # Fallback for old buttons or if episode count is missing
        tv_id = parts[1]
        season_number = parts[2]
        link = f"https://www.vidking.net/embed/tv/{tv_id}/{season_number}/1"
        bot_message = f"You selected Season {season_number}. [Watch here]({link})"
        await callback.message.answer(bot_message, disable_web_page_preview=True)

    await callback.answer()

@router.message(SearchState.waiting_for_query)
async def process_query(message: Message, state: FSMContext):
    user = message.from_user.username
    query = message.text
    data = await state.get_data()
    search_type = data.get('search_type', 'movie')
    
    action = f"search {search_type} for '{query}'"
    log_message(user, action)

    if search_type == 'movie':
        results = search_movie(query)
    else:
        results = search_tv(query)

    if isinstance(results, list) and results:
        await state.update_data(results=results, page=0)
        await state.set_state(None)

        total_pages = math.ceil(len(results) / 5)
        bot_message = format_results(results[:5], search_type)
        await message.answer(bot_message,
                             reply_markup=get_pagination_keyboard(page=0, total_pages=total_pages),
                             parse_mode='MarkdownV2')
        log_message(user, action, bot_message)
    elif isinstance(results, list) and not results:
        bot_message = f"No {search_type}s were found with that name 😕\nPlease check your spelling 🎬✨"
        await message.answer(bot_message)
        log_message(user, action, bot_message)
        await state.clear()
    else:
        await message.answer(str(results))
        log_message(user, action, str(results))
        await state.clear()

@router.callback_query(F.data.startswith("next_"))
async def next_page(callback: CallbackQuery, state: FSMContext):
    user = callback.from_user.username
    action = "next_page callback"
    log_message(user, action)
    page = int(callback.data.split("_")[1])
    data = await state.get_data()
    results = data.get("results")
    search_type = data.get("search_type", "movie")
    
    if results:
        await state.update_data(page=page)
        total_pages = math.ceil(len(results) / 5)
        start = page * 5
        end = start + 5
        bot_message = format_results(results[start:end], search_type)
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
    search_type = data.get("search_type", "movie")
    
    if results:
        await state.update_data(page=page)
        total_pages = math.ceil(len(results) / 5)
        start = page * 5
        end = start + 5
        bot_message = format_results(results[start:end], search_type)
        await callback.message.edit_text(bot_message,
                                         reply_markup=get_pagination_keyboard(page=page, total_pages=total_pages),
                                         parse_mode='MarkdownV2')
        log_message(user, action, bot_message)
    await callback.answer()
