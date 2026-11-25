"""
Translation layer between club name conventions:
- API-Ninjas
- football-data.co.uk
"""

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

TO_API_NINJAS: dict[str, str] = {v: k for k, v in TO_FOOTBALL_DATA.items()}


def to_football_data(name: str) -> str:
    """
    Translate an API-Ninjas club name to the football-data.co.uk convention.

    Args:
        name (str): API Ninjas club name.

    Returns:
        str: football-data.co.uk club name
    """

    return TO_FOOTBALL_DATA.get(name, name)


def to_api_ninjas(name: str) -> str:
    """
    Translate a football-data.co.uk club name to the API-Ninjas convention.

    Args:
        name (str): football-data.co.uk club name.

    Returns:
        str: API Ninjas club name
    """

    return TO_API_NINJAS.get(name, name)
