import itertools
import os.path

import numpy as np
import pandas as pd


def _build_url(league: str, season: int) -> str:
    """
    Builds the URL of csv containing data about season of league from football-data.co.uk

    Args:
        league (str): League to source
        season (int): Season of the league to source

    Returns:
        str: The URL of the csv file

    """
    return str(f"https://football-data.co.uk/mmz4281/{season}/{league}.csv")


def _get_league_season(league: str, season: int, columns: list[str], include_season: bool) -> pd.DataFrame:
    """
    Downloads specified data about league from season.

    Args:
        league (str): League to download the data for.
        season (int): Season of league to download.
        columns (list[str]): What columns to include in the resulting DataFrame.
        include_season (bool): If the season should be included as a column of the DataFrame.

    Returns:
        pd.DataFrame: DataFrame containing requested information.

    """
    url = _build_url(league, season)
    try:
        df = pd.read_csv(url, usecols=columns)
    except ValueError:
        raise ValueError("Invalid columns specified")

    if include_season:
        df['Season'] = season

    return df


def fetch_data(leagues: list[str], seasons: list[int], file_path: str, columns: list[str], include_season: bool = True):
    """
    Fetches specified columns about leagues in seasons from football-data.co.uk and saves the data into file.

    Args:
        leagues (list[str]): Leagues to fetch the data about.
        seasons (list[int]): Seasons of the leagues to fetch the data about.
        file_path (str): Where to save the downloaded data.
        columns (list[str]): What columns to include in the resulting DataFrame.
        include_season (bool): If the season should be included as a column of the DataFrame.

    Returns:
        Does not return, save the downloaded data into file_path

    """
    data_frame_iterable = (_get_league_season(league, season, columns, include_season) for league, season in
                           itertools.product(leagues, seasons))
    pd.concat(data_frame_iterable).to_csv(file_path, index=False)


def download_data(leagues: list[str], seasons: list[int], columns: list[str] | None = None,
                  file_path: str = "football-data-co.csv",
                  force_download: bool = False,
                  include_season: bool = True) -> pd.DataFrame:
    """
   Fetches specified columns about leagues in seasons from football-data.co.uk and saves the data into file.
   First checks whether a specified file_path is already present and contains requested data, if it does, just read the
   existing data, otherwise fetches the data from the internet.

    Args:
        leagues (list[str]): Leagues to fetch the data about.
        seasons (list[int]): Seasons of the leagues to fetch the data about.
        file_path (str): Where to save the downloaded data.
        columns (list[str]): What columns to include in the resulting DataFrame.
        force_download (bool): If set to True data is downloaded even if the csv file containing specified data exists.
        include_season (bool): If the season should be included as a column of the DataFrame.

    Returns:
        pd.DataFrame: DataFrame containing the specified data.

    """
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
