"""Shared sports vocabulary for fixtures and input validation."""

CITIES = {
    "Delhi": "North", "Chandigarh": "North", "Lucknow": "North",
    "Mumbai": "West", "Pune": "West", "Ahmedabad": "West",
    "Bengaluru": "South", "Chennai": "South", "Kochi": "South",
    "Kolkata": "East", "Bhubaneswar": "East", "Guwahati": "North East",
}
SPORTS = {
    "football": {
        "goalkeeper": ("shot stopping", "distribution", "handling", "communication"),
        "centre back": ("tackling", "heading", "positioning", "passing"),
        "full back": ("tackling", "crossing", "pace", "stamina"),
        "defensive midfielder": ("tackling", "passing", "positioning", "stamina"),
        "central midfielder": ("passing", "vision", "ball control", "stamina"),
        "attacking midfielder": ("vision", "passing", "dribbling", "finishing"),
        "winger": ("dribbling", "pace", "crossing", "finishing"),
        "striker": ("finishing", "heading", "pace", "positioning"),
    },
    "cricket": {
        "batter": ("batting", "footwork", "fielding", "fitness"),
        "bowler": ("pace bowling", "spin bowling", "fielding", "fitness"),
        "all rounder": ("batting", "spin bowling", "fielding", "fitness"),
        "wicket keeper": ("keeping", "batting", "footwork", "fitness"),
    },
    "basketball": {
        "point guard": ("ball handling", "passing", "shooting", "defense"),
        "shooting guard": ("shooting", "ball handling", "passing", "defense"),
        "small forward": ("shooting", "defense", "rebounding", "passing"),
        "power forward": ("rebounding", "defense", "vertical", "screening"),
        "center": ("rebounding", "screening", "vertical", "defense"),
    },
    "athletics": {
        "sprinter": ("speed", "explosiveness", "race starts", "technique"),
        "hurdler": ("speed", "technique", "mobility", "explosiveness"),
        "middle distance": ("endurance", "pacing", "speed", "technique"),
        "long jumper": ("explosiveness", "approach rhythm", "speed", "technique"),
        "thrower": ("strength", "technique", "mobility", "explosiveness"),
    },
    "badminton": {
        "singles": ("footwork", "net play", "endurance", "shot placement"),
        "doubles": ("rotation", "smash", "net play", "serve return"),
        "mixed doubles": ("rotation", "net play", "serve return", "shot placement"),
    },
}
TYPES = {
    "trial": "Academy trial", "scholarship": "Sports scholarship",
    "tournament": "Tournament", "camp": "Training camp", "scouting": "Scout showcase",
    "club": "Club intake", "development": "Development programme",
}
DEMO_ACCOUNTS = {
    "football": ("Football athlete", "a001"),
    "cricket": ("Cricket athlete", "a002"),
    "basketball": ("Basketball athlete", "a003"),
    "limited": ("Athlete with no eligible opportunities", "a004"),
    "organisation": ("Organisation administrator", "o001"),
}
