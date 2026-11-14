import itertools
import os.path

import pandas as pd
import numbers as np


def _build_url(league: str, season: int) -> str:
    return str(f"https://football-data.co.uk/mmz4281/{season}/{league}.csv")


def _get_league_season(league: str, season: int, columns: list[str], include_season: bool) -> pd.DataFrame:
    url = _build_url(league, season)
    try:
        df = pd.read_csv(url, usecols=columns)
    except ValueError:
        raise ValueError("Invalid columns specified")

    if include_season:
        df['Season'] = season

    return df


def fetch_data(leagues: list[str], seasons: list[int], columns: list[str] | None = None,
                  include_season: bool = True) -> pd.DataFrame:
    if columns is None:
        columns = ['Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', ]
    data_frame_iterable = (_get_league_season(league, season, columns, include_season) for league, season in
                           itertools.product(leagues, seasons))
    return pd.concat(data_frame_iterable)

def download_data(leagues: list[str], seasons: list[int], columns: list[str] | None = None,
                  file_path: str = "football-data-co.csv",
                  force_download: bool = False,
                  include_season: bool = True):
    if not os.path.isfile(file_path) or force_download:
        res_pd = fetch_data(leagues, seasons, columns, include_season)
        res_pd.to_csv(file_path)