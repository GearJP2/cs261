# use temporary for display in frontend venuse

VENUES = [
    {
        "id": 1,
        "name": "Badminton Interzone",
        "pos": {"top": 8.2, "left": 1.9, "width": 9.6, "height": 3.7},
        "sports": [
            {"id": 1, "name": "Badminton", "emoji": "🏸", "court_count": 20, "book_first": True},
        ],
    },
    {
        "id": 2,
        "name": "Tennis Court",
        "pos": {"top": 59.9, "left": 10.2, "width": 14.4, "height": 2.9},
        "sports": [
            {"id": 2, "name": "Tennis", "emoji": "🎾", "court_count": 9, "book_first": True},
            {"id": 3, "name": "Pickleball", "emoji": "🥒", "court_count": 2, "book_first": True},
        ],
    },
    {
        "id": 3,
        "name": "Futsal Court",
        "pos": {"top": 59.1, "left": 38.0, "width": 3.6, "height": 3.1},
        "sports": [
            {"id": 4, "name": "Futsal", "emoji": "⚽", "court_count": None, "book_first": False},
        ],
    },
    {
        "id": 4,
        "name": "Gym 7",
        "pos": {"top": 59.1, "left": 43.0, "width": 12.9, "height": 7.3},
        "sports": [
            {"id": 5, "name": "Squash", "emoji": "🎾", "court_count": 2, "book_first": True},
            {
                "id": 6,
                "name": "Basketball",
                "emoji": "🏀",
                "court_count": None,
                "book_first": False,
            },
            {
                "id": 7,
                "name": "Rock Climbing",
                "emoji": "⛰️",
                "court_count": None,
                "book_first": False,
            },
            {"id": 8, "name": "Ping Pong", "emoji": "🏓", "court_count": None, "book_first": False},
        ],
    },
    {
        "id": 5,
        "name": "Football Court",
        "pos": {"top": 67.6, "left": 43.0, "width": 7.6, "height": 4.1},
        "sports": [
            {"id": 9, "name": "Football", "emoji": "⚽", "court_count": None, "book_first": False},
        ],
    },
    {
        "id": 6,
        "name": "Tu Xtreme",
        "pos": {"top": 67.6, "left": 51.8, "width": 3.7, "height": 4.1},
        "sports": [
            {"id": 10, "name": "Extreme", "emoji": "🛹", "court_count": None, "book_first": False},
        ],
    },
    {
        "id": 7,
        "name": "Aquatic Center",
        "pos": {"top": 88.0, "left": 62.2, "width": 4.5, "height": 4.8},
        "sports": [
            {"id": 11, "name": "Swimming", "emoji": "💧", "court_count": None, "book_first": False},
        ],
    },
    {
        "id": 8,
        "name": "Gym 4",
        "pos": {"top": 91.0, "left": 72.7, "width": 6.6, "height": 4.2},
        "sports": [
            {"id": 1, "name": "Badminton", "emoji": "🏸", "court_count": 13, "book_first": True},
        ],
    },
]


def get_venues():
    return VENUES


def get_venue(venue_id):
    for venue in VENUES:
        if venue["id"] == venue_id:
            return venue
    return None


SPORT_IMAGES = {  # (venue_id, sport_id)
    (1, 1): "interzone.jpg",
    (2, 2): "tennis.jpg",
    (2, 3): "pickleball.jpg",
    (4, 5): "squash.jpg",
    (7, 11): "aquatic.jpg",
    (8, 1): "gym4.jpg",
    (6, 10): "Xtreme.jpg",
}


def get_sport(venue_id, sport_id):
    """Return (venue, sport); sport is None when not found."""
    venue = get_venue(venue_id)
    if venue is None:
        return None, None
    for sport in venue["sports"]:
        if sport["id"] == sport_id:
            count = sport["court_count"]
            if count:
                courts = [f"{sport['name']} Court {i:02d}" for i in range(1, count + 1)]
            else:
                courts = [sport["name"]]
            image = SPORT_IMAGES.get((venue_id, sport_id))
            return venue, {**sport, "courts": courts, "image": image}
    return venue, None
