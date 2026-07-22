import csv
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str = "data/songs.csv") -> List[Dict]:
    """
    Load songs from a CSV file and convert numeric fields to Python numbers.

    Each row is returned as a dictionary whose keys match the CSV headers.
    Numeric fields are converted using field-name lists so this is easy to extend.
    Malformed numeric values are handled gracefully.
    """
    numeric_float_fields = {"energy", "danceability", "valence", "acousticness"}
    numeric_int_fields = {"tempo_bpm", "duration_ms"}
    songs: List[Dict] = []

    try:
        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row_index, row in enumerate(reader, start=1):
                song: Dict = {}
                malformed = False
                for key, value in row.items():
                    value = value.strip() if isinstance(value, str) else value
                    if value == "":
                        song[key] = None
                        continue

                    if key in numeric_float_fields:
                        try:
                            song[key] = float(value)
                        except ValueError:
                            print(f"Warning: row {row_index} field '{key}' is malformed float: {value}")
                            song[key] = None
                            malformed = True
                    elif key in numeric_int_fields:
                        try:
                            song[key] = int(float(value))
                        except ValueError:
                            print(f"Warning: row {row_index} field '{key}' is malformed int: {value}")
                            song[key] = None
                            malformed = True
                    else:
                        song[key] = value

                songs.append(song)
    except FileNotFoundError:
        print(f"Error: file not found: {csv_path}")
    except Exception as exc:
        print(f"Error loading songs from {csv_path}: {exc}")

    return songs

def _proximity_score(value: Optional[float], target: float, sigma: float = 0.2) -> float:
    """Return a smooth [0,1] proximity score for a numeric feature."""
    if value is None:
        return 0.0
    diff = abs(value - target)
    return math.exp(- (diff * diff) / (2.0 * sigma * sigma))


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Score a song against a user's taste profile.

    The score is the sum of:
    - a genre bonus for exact favorite_genre match (+2.0)
    - a mood bonus for exact favorite_mood match (+1.5)
    - Gaussian proximity scores for energy, danceability, and valence,
      each weighted by a feature-specific multiplier.

    Returns:
        (total_score, reasons)
    where reasons is a list of strings describing each contribution.
    """
    reasons: List[str] = []
    total_score = 0.0

    genre_match = song.get("genre") == user_prefs.get("favorite_genre")
    genre_score = 2.0 if genre_match else 0.0
    total_score += genre_score
    reasons.append(f"genre {'match' if genre_match else 'mismatch'} (+{genre_score:.1f})")

    mood_match = song.get("mood") == user_prefs.get("favorite_mood")
    mood_score = 1.5 if mood_match else 0.0
    total_score += mood_score
    reasons.append(f"mood {'match' if mood_match else 'mismatch'} (+{mood_score:.1f})")

    sigma = 0.2
    for feature, weight in [("energy", 2.0), ("danceability", 1.5), ("valence", 2.0)]:
        song_value = song.get(feature)
        target_value = user_prefs.get(f"target_{feature}")
        if song_value is None or target_value is None:
            contribution = 0.0
        else:
            proximity = math.exp(-((song_value - float(target_value)) ** 2) / (2 * sigma ** 2))
            contribution = proximity * weight
        total_score += contribution
        reasons.append(f"{feature} proximity (+{contribution:.2f})")

    return total_score, reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, List[str]]]:
    """
    Recommend the top-k songs for a user.

    For each song, compute (total_score, reasons) with score_song(),
    then return the top-k entries sorted by score from highest to lowest.

    Returns a list of tuples: (song_dict, total_score, reasons).
    """
    scored_songs = [
        (song, *score_song(user_prefs, song))
        for song in songs
    ]

    ranked = sorted(scored_songs, key=lambda item: item[1], reverse=True)
    return ranked[:k]
