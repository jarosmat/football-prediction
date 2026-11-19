"""
Translation layer between club name conventions:
- API-Ninjas (ESPN-style, e.g. "Manchester United", "Nottingham Forest")
- football-data.co.uk (e.g. "Man United", "Nott'm Forest")
"""

# canonical (API-Ninjas) name -> football-data.co.uk name
TO_FOOTBALL_DATA: dict[str, str] = {
    "AFC Bournemouth": "Bournemouth",
    "Arsenal": "Arsenal",
    "Aston Villa": "Aston Villa",
    "Brentford": "Brentford",
    "Brighton & Hove Albion": "Brighton",
    "Chelsea": "Chelsea",
    "Coventry City": "Coventry",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Hull City": "Hull",
    "Ipswich Town": "Ipswich",
    "Leeds United": "Leeds",
    "Liverpool": "Liverpool",
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Sunderland": "Sunderland",
    "Tottenham Hotspur": "Tottenham",
}

# football-data.co.uk name -> canonical (API-Ninjas) name
TO_API_NINJAS: dict[str, str] = {v: k for k, v in TO_FOOTBALL_DATA.items()}


def to_football_data(name: str) -> str:
    """Translate an API-Ninjas club name to the football-data.co.uk convention."""
    return TO_FOOTBALL_DATA.get(name, name)


def to_api_ninjas(name: str) -> str:
    """Translate a football-data.co.uk club name to the API-Ninjas convention."""
    return TO_API_NINJAS.get(name, name)
