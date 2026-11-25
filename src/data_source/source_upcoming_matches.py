from datetime import date
from utils.protocols import Stringable

import pandas as pd
import requests


def get_matches_played_today(api_key: str, leagues: list[str], day: date | None = None) -> dict[str, list[dict]]:
    """
    Fetches matches that are played on given day in specified leagues.

    Parameters:
        api_key (str): API Ninjas API key.
        leagues (list[str]): A list of league codes.
        day (date | None): Day to fetch matches for, default is today.

    Returns:
        dict[str, list[dict]]: league code -> list of raw match dicts from the API.
    """
    url = "https://api.api-ninjas.com/v1/soccermatches"
    headers = {
        'X-Api-Key': api_key
    }
    day = (day or date.today()).isoformat()

    all_matches = {}

    for league in leagues:
        params = {
            'league': league,
            'date': day
        }
        try:
            response = requests.get(url, headers=headers, params=params)

            response.raise_for_status()

            matches = response.json()
            all_matches[league] = matches

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for league '{league}': {e}")
            all_matches[league] = []

    return all_matches


def _team_name(team: dict[str, str] | Stringable) -> str:
    """
    Extracts team name from specified team.

    Args:
        team (dict[str, str] | Stringable): Team object to extract the data about.

    Returns:
        str: Either team name extracted from dictionary under key "name" or str representation of team parameter.

    """
    return team["name"] if isinstance(team, dict) else str(team)


def get_matches_played_today_dataframe(api_key: str, leagues: list[str],
                                       day: date | None = None) -> pd.DataFrame:
    """
    Returns matches played on the given day.

    Args:
        api_key (str): API Ninjas API key.
        leagues (list[str]): A list of league codes.
        day (date | None): Day to fetch matches for, default is today.

    Notes:
          - Team names are returned in the API Ninjas format.
          - Returns the same values as `get_matches_played_today` but serialized in DataFrame.

    Returns:
        pd.DataFrame: DataFrame with columns:
            - League
            - Date
            - Time
            - HomeTeam
            - AwayTeam
    """
    rows = []
    for league, matches in get_matches_played_today(api_key, leagues, day).items():
        for match in matches:
            rows.append({
                "League": league,
                "Date": match.get("date"),
                "Time": match.get("time"),
                "HomeTeam": _team_name(match.get("home_team", "")),
                "AwayTeam": _team_name(match.get("away_team", "")),
            })
    return pd.DataFrame(rows, columns=["League", "Date", "Time", "HomeTeam", "AwayTeam"])
