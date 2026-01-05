import requests
import os
import socket
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

def get_env_variable(key: str, default: str = None) -> str:
    """
    Safely retrieves an environment variable.
    Raises an error if the variable is not found and no default is provided.
    """
    value = os.getenv(key)
    if value is None:
        if default is not None:
            return default
        raise ValueError(f"Environment variable '{key}' not set.")
    return value

# --- DNS Workaround ---
# This patches the socket library to manually resolve api.themoviedb.org to a known correct IP.
# This is required to bypass a persistent local DNS issue.
original_getaddrinfo = socket.getaddrinfo
def patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host == 'api.themoviedb.org':
        # Return the address information for a known good IP.
        return original_getaddrinfo('3.164.230.99', port, family, type, proto, flags)
    # For all other hosts, use the original function
    return original_getaddrinfo(host, port, family, type, proto, flags)
socket.getaddrinfo = patched_getaddrinfo
# --- End DNS Workaround ---

def search_movie(keyword: str):
    """
    Searches for a movie using the TMDB API.
    """
    access_token = get_env_variable("TMDB_ACCESS_TOKEN")
    url = f"https://api.themoviedb.org/3/search/movie?query={keyword}&page=1"

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        data = response.json()
        if data['results']:
            return data['results']
        else:
            return "No movies found for that keyword."

    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}"
    except requests.exceptions.RequestException as req_err:
        return f"An error occurred: {req_err}"
    except ValueError:
        return "Failed to decode JSON response."

if __name__ == "__main__":
    print(search_movie("filth"))
    

