import os
import asyncio
from dotenv import load_dotenv
from nostr_sdk import Keys, Client, EventBuilder, NostrSigner, RelayUrl
from tmdb_api.movie_request import get_genre_names

# Load environment variables
load_dotenv()

async def post_to_nostr(movie):
    # Get the private key from .env
    nsec = os.getenv("NOSTR_PRIVET_KEY")
    if not nsec:
        print("NOSTR_PRIVET_KEY not found in .env file, skipping Nostr post.")
        return

    try:
        keys = Keys.parse(nsec)
        signer = NostrSigner.keys(keys)
        client = Client(signer)
        
        # Add relays
        # Try to load from relays.txt, otherwise default
        relays_file = os.path.join(os.path.dirname(__file__), "relays.txt")
        if os.path.exists(relays_file):
            with open(relays_file, "r") as f:
                relays = [line.strip() for line in f if line.strip()]
            for relay in relays:
                await client.add_relay(RelayUrl.parse(relay))
        else:
            await client.add_relay(RelayUrl.parse("wss://relay.damus.io"))
            await client.add_relay(RelayUrl.parse("wss://nostr.wine"))
        
        await client.connect()

        # Prepare content
        title = movie.get("title", "No title")
        date = movie.get("release_date", "No date")
        overview = movie.get("overview", "")
        rating = movie.get("vote_average", 0)
        votes = movie.get("vote_count", 0)
        id = movie.get("id")
        trailer_url = movie.get("trailer_url")
        backdrop = movie.get("backdrop_path")
        
        genre_ids = movie.get("genre_ids", [])
        genres = get_genre_names()
        genre_names = [genres.get(genre_id) for genre_id in genre_ids if genres and genres.get(genre_id)]
        genre_hashtags = " ".join([f"#{genre.replace(' ', '')}" for genre in genre_names])
        
        content = f"🎬 {title} ({date[:4]})\n\n"
        if backdrop:
            content += f"https://image.tmdb.org/t/p/original{backdrop}\n"
        content += f"📄Overview: {overview}\n"
        content += f"⭐Rating: {rating} ({votes} votes)\n"
        if trailer_url:
            content += f"\nTrailer (link below) {trailer_url}\n"
        content += f"🎥Watch here (link below) https://www.vidking.net/embed/movie/{id}\n"
        content += f"Search Movies Telegram (link below) https://t.me/Movies4Free21Bot\n"
        content += f"#movies #free #hd {genre_hashtags}"

        print(f"Posting to Nostr: {title}")
        event = await EventBuilder.text_note(content).sign(signer)
        output = await client.send_event(event)
        print(f"Nostr Event sent: {output}")

    except Exception as e:
        print(f"Error posting to Nostr: {e}")
