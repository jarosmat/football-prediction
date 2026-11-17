from collections import deque
from typing import Literal

import numpy as np
import pandas as pd

import data_source.source_football_data_co_uk as fd


def convert_res_val(home: bool, res: Literal['H', 'D', 'A']) -> int:
    """

    Parameters
    ----------
    home - whether the team was playing home
    res - literal from football-data-co.uk specifying who won

    Returns
    -------
    0 the team won
    1 draw
    2 the team lost

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

    Parameters
    ----------
    res - result of a match

    Returns
    -------
    return 0 if home won, 1 if drawn, 2 if away won

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

    Parameters
    ----------
    leagues: what leagues to query.
    seasons: what seasons to query.
    window: how many last matches to include.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Train values and targets, values are first n values for window of home team, then n values for window
        of away team, values are:
            -1 did not play - only for windows where there weren't enough previous matches played
            0 team won
            1 draw
            2 team lost
        Targets have values of results of those matches, values are:
            0 home won
            1 draw
            2 away won

    """
    columns = ['Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTR']
    df = fd.download_data(leagues, seasons, columns, include_season=False)
    df['Date'] = df['Date'].transform(lambda time: pd.to_datetime(time, format='%d/%m/%Y'))
    df.sort_values(by=['Date'])

    n_rows = len(df)
    n_features = window * 2
    res_X = np.zeros((n_rows, n_features))
    res_y = np.zeros((n_rows,))
    team_deque_dict: dict[str, deque[int]] = dict()

    for i, (div, date, ht, at, ftr) in enumerate(df[columns].itertuples(index=False)):
        if ht not in team_deque_dict:
            team_deque_dict[ht] = deque([-1 for _ in range(window)])
            # team_deque_dict[ht].append(convert_res_val(True, ftr))
        if at not in team_deque_dict:
            team_deque_dict[at] = deque([-1 for _ in range(window)])
            # team_deque_dict[at].append(convert_res_val(False, ftr))

        res_X[i] = np.array(list(team_deque_dict[ht]) + list(team_deque_dict[at]))
        res_y[i] = convert_res_val_target(ftr)

        team_deque_dict[ht].popleft()
        team_deque_dict[ht].append(convert_res_val(True, ftr))
        team_deque_dict[at].popleft()
        team_deque_dict[at].append(convert_res_val(False, ftr))

    return res_X, res_y
