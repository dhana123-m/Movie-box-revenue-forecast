"""Canonical list of movie genres accepted by the API.

This mirrors the genre vocabulary observed in the TMDB 5000 training data.
The model multi-hot encodes these genres (unknown genres are ignored).
"""

GENRE_NAMES: list[str] = [
    "Action",
    "Adventure",
    "Animation",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Family",
    "Fantasy",
    "History",
    "Horror",
    "Music",
    "Mystery",
    "Romance",
    "Science Fiction",
    "Thriller",
    "War",
    "Western",
]
