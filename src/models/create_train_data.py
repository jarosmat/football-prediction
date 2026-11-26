from collections import deque
from typing import Literal

import numpy as np
import pandas as pd

import data_source.source_football_data_co_uk as fd


class MatchesIterator:
    """
    Iterates over matches in date order, yielding the form window of both teams and the match result.

    Parameters:
        df (pd.DataFrame): match data, must contain the `columns` columns
        window (int): how many previous matches per team are kept in the window
        reverse (bool): if True, iterate from the newest match backwards

    Attributes:
        columns (list[str]): columns read from the data frame
        window (int): window size, see Parameters
        df (pd.DataFrame): the data frame, sorted by date
        team_deque_dict (dict[str, deque[int]]): per-team deque with the last `window` results
            (-1 = not enough previous matches, 0 = won, 1 = draw, 2 = lost)

    Yields:
        (tuple[np.ndarray, np.float64 | int]): (X, y) where X is the concatenated home/away form
            windows and y is the target result (0 = home won, 1 = draw, 2 = away won)
    """
    columns = ['Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTR']
    def __init__(self, df: pd.DataFrame, window: int, reverse: bool = False):
        self.window = window
        self.df = df.sort_values(by=['Date']).reset_index(drop=True)
        self.team_deque_dict: dict[str, deque[int]] = dict()
        self.update = 1
        self.i = 0
        if reverse:
            self.update = -1
            self.i = len(df) - 1

    def __iter__(self):
        return self

    def __next__(self) -> tuple[np.ndarray, np.float64 | int]:
        div, date, ht, at, ftr = self.df[self.columns].iloc[self.i]

        if ht not in self.team_deque_dict:
            self.team_deque_dict[ht] = deque([-1 for _ in range(self.window)])
        if at not in self.team_deque_dict:
            self.team_deque_dict[at] = deque([-1 for _ in range(self.window)])

        res_X = np.array(list(self.team_deque_dict[ht]) + list(self.team_deque_dict[at]))
        res_y = convert_res_val_target(ftr)

        self.team_deque_dict[ht].popleft()
        self.team_deque_dict[ht].append(convert_res_val(True, ftr))
        self.team_deque_dict[at].popleft()
        self.team_deque_dict[at].append(convert_res_val(False, ftr))

        self.i += self.update

        if self.i < 0 or self.i >= len(self.df):
            raise StopIteration

        return res_X, res_y


def convert_res_val(home: bool, res: Literal['H', 'D', 'A']) -> int:
    
    """
    Parameters:
        home (bool): whether the team was playing home
        res (Literal['H', 'D', 'A']): literal from football-data.co.uk specifying who won

    Returns:
        int: 0 the team won, 1 draw, 2 the team lost
    """

    if res == 'D':
        return 1
    if home:
        match res:
            case 'H':
                return 0
            case 'A':
                return 2
    match res:
        case 'H':
            return 2
        case 'A':
            return 0


def convert_res_val_target(res: Literal['H', 'D', 'A']) -> int:
    """
    Parameters:
        res (Literal['H', 'D', 'A']): result of a match

    Returns:
        int: 0 if home won, 1 if drawn, 2 if away won
    """
    match res:
        case 'H':
            return 0
        case 'D':
            return 1
        case 'A':
            return 2


def create_windows_train_data(leagues: list[str], seasons: list[int], window: int = 5) -> tuple[np.ndarray, np.ndarray]:
    """
    Creates training data for just last n matches results.

    Parameters:
        leagues (list[str]): what leagues to query.
        seasons (list[int]): what seasons to query.
        window (int): how many last matches to include.

    Returns:
        tuple[np.ndarray, np.ndarray]: train values and targets, values are first n values for window of
            home team, then n values for window of away team, values are:
            -1 did not play - only for windows where there weren't enough previous matches played
            0 team won
            1 draw
            2 team lost
            Targets have values of results of those matches, values are:
            0 home won
            1 draw
            2 away won
    """
    df = fd.download_data(leagues, seasons, MatchesIterator.columns, include_season=False)
    df['Date'] = df['Date'].transform(lambda time: pd.to_datetime(time, format='%d/%m/%Y'))

    res_X, res_y = _build_team_form(df, window)
    return res_X, res_y


def _build_team_form(df: pd.DataFrame, window: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Build training data from specified data frame.

    Parameters:
        df (pd.DataFrame): match data to process
        window (int): number of previous matches to include

    Returns:
        tuple[np.ndarray, np.ndarray]: training data
    """
    n_rows = len(df)
    n_features = window * 2
    res_X = np.zeros((n_rows, n_features))
    res_y = np.zeros((n_rows,))

    for i, (X, y) in enumerate(MatchesIterator(df, window, False)):
        res_X[i] = X
        res_y[i] = y

    return res_X, res_y


def create_windows_for_fixtures(leagues: list[str], season: int, fixtures: pd.DataFrame,
                                window: int = 5) -> dict[tuple[str,str], tuple[list[int], list[int]]]:
    """
    Creates feature rows for matches that have not been played yet.

    Parameters:
        leagues (list[str]): what leagues need history
        season (int): what season to use for creating the history
        fixtures (pd.DataFrame): DataFrame with at least HomeTeam and AwayTeam columns (e.g. upcoming matches).
        window (int): how many last matches per team to include.

    Returns:
        dict[tuple[str, str], tuple[list[int], list[int]]]: data for inference
    """
    columns = ['Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTR']
    df = fd.download_data(leagues, [season], columns, include_season=False, force_download=True)
    df['Date'] = df['Date'].transform(lambda time: pd.to_datetime(time, format='%d/%m/%Y'))

    mati = MatchesIterator(df, window)
    for _ in mati:
        pass

    team_deque_dict = mati.team_deque_dict

    res = {}
    for ht, at in fixtures[['HomeTeam', 'AwayTeam']].itertuples(index=False):
        home_form = team_deque_dict.get(ht, deque([-1] * window))
        away_form = team_deque_dict.get(at, deque([-1] * window))
        res[(ht, at)] = (list(home_form), list(away_form))
    return res
