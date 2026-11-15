import itertools
import os.path

import numpy as np
import pandas as pd


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


def fetch_data(leagues: list[str], seasons: list[int], file_path: str, columns: list[str], include_season: bool = True):
    data_frame_iterable = (_get_league_season(league, season, columns, include_season) for league, season in
                           itertools.product(leagues, seasons))
    pd.concat(data_frame_iterable).to_csv(file_path)


def download_data(leagues: list[str], seasons: list[int], columns: list[str] | None = None,
                  file_path: str = "football-data-co.csv",
                  force_download: bool = False,
                  include_season: bool = True) -> pd.DataFrame:
    if columns is None:
        columns = ['Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']

    if not os.path.isfile(file_path) or force_download:
        fetch_data(leagues, seasons, file_path, columns, include_season)
        res_pd = pd.read_csv(file_path)
        return res_pd
    else:
        res_pd = pd.read_csv(file_path)
        wanted = pd.Index(columns)
        present = wanted.isin(res_pd.columns)
        if np.all(present):
            res_pd = res_pd[columns]
        else:
            fetch_data(leagues, seasons, file_path, columns + res_pd.columns, include_season)
            res_pd = pd.read_csv(file_path, usecols=columns)

        return res_pd
