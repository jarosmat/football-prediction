import argparse
import lzma
import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

import create_train_data
import data_source.source_upcoming_matches as upcoming
import data_source.team_names as team_names
import window_model

RESULT_LETTERS = ["H", "D", "A"]

API_TO_FD_LEAGUE = {"epl": "E0"}
CURRENT_SEASON = 2627


def load_model(path: Path) -> window_model.WindowModel:
    with lzma.open(path, "rb") as f:
        return pickle.load(f)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run inference with a saved WindowModel on today's matches.")
    p.add_argument("--model", type=Path, default=Path("log_reg_window.model"),
                   help="Path to the saved model.")
    p.add_argument("--api-key", default=os.environ.get("API_NINJAS_KEY"),
                   help="API Ninjas key (or set the API_NINJAS_KEY env var).")
    p.add_argument("--leagues", nargs="+", default=["epl"],
                   help="API-Ninjas league codes to fetch today's matches for, e.g. --leagues epl")
    p.add_argument("--season", type=int, default=CURRENT_SEASON,
                   help="football-data.co.uk season code used for the match history, e.g. 2627")
    p.add_argument("--output", type=Path, default=Path("predictions.csv"),
                   help="CSV file to write predictions to.")
    return p.parse_args()


def main(args):
    if not args.api_key:
        raise SystemExit("API Ninjas key required: pass --api-key or set API_NINJAS_KEY")

    model = load_model(args.model)
    print(f"loaded {args.model}: window_size={model.window_size}")

    fixtures = upcoming.get_matches_played_today_dataframe(args.api_key, args.leagues)
    if fixtures.empty:
        print("no matches today")
        return

    fixtures["HomeTeam"] = fixtures["HomeTeam"].map(team_names.to_football_data)
    fixtures["AwayTeam"] = fixtures["AwayTeam"].map(team_names.to_football_data)

    fd_leagues = [API_TO_FD_LEAGUE.get(league, league) for league in args.leagues]
    windows = create_train_data.create_windows_for_fixtures(fd_leagues, args.season, fixtures, model.window_size)

    keys = list(windows)
    X = np.array([windows[ht_at][0] + windows[ht_at][1] for ht_at in keys])

    proba = model.predict_proba(X)

    out = fixtures[["Date", "Time", "HomeTeam", "AwayTeam"]].copy()
    out["p_home"], out["p_draw"], out["p_away"] = proba[:, 0], proba[:, 1], proba[:, 2]
    out["predicted"] = [RESULT_LETTERS[i] for i in np.argmax(proba, axis=1)]

    pd.set_option("display.width", 120)
    print(out.to_string(index=False))

    out.to_csv(args.output, index=False)
    print(f"predictions written to {args.output}")


if __name__ == "__main__":
    main(parse_args())

