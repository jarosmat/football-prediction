from datetime import date

import pandas as pd
import requests


def get_matches_played_today(api_key: str, leagues: list[str], day: date | None = None) -> dict[str, list[dict]]:
    """
    Fetches matches that are played on this day in specified leagues

    Parameters:
    - api_key (str): API Ninjas API key.
    - leagues (list): A list of league codes.
    - day (date): Day to fetch matches for, default is today.

    Returns:
    - dict: league code -> list of raw match dicts from the API.
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


def _team_name(team) -> str:
    return team["name"] if isinstance(team, dict) else str(team)


def get_matches_played_today_dataframe(api_key: str, leagues: list[str],
                                       day: date | None = None) -> pd.DataFrame:
    """
    Returns matches played on the given day (default: today) as a DataFrame with columns:
    League, Date, Time, HomeTeam, AwayTeam (team names as returned by the API).
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
