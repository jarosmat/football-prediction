"""
Train a logistic regression on a sliding window of match results.

The experiment is defined by a TOML config (see Config). CLI flags only override
verbosity and parallelism. For each window size a model is trained and validated,
and the best one (by validation log loss) is pickled to Config.output_path.
"""

import argparse
import lzma
import pickle
import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path

import sklearn as sk

import create_train_data
import window_model


@dataclass
class GridConfig:
    """
    Settings for the grid search over polynomial degrees.

    Attributes:
        poly_degrees (list[int]): degrees for the PolynomialFeatures of both teams
        cv_splits (int): number of StratifiedKFold splits used in GridSearchCV
        scoring (str): scoring metric for the grid search (default: neg_log_loss)
        n_jobs (int): parallel jobs for GridSearchCV (-1 = all cores)
        verbose (int): verbosity of GridSearchCV
    """
    poly_degrees: list[int] = field(default_factory=lambda: [2, 3])
    cv_splits: int = 5
    scoring: str = "neg_log_loss"
    n_jobs: int = -1
    verbose: int = 0


@dataclass
class ModelConfig:
    """
    Settings for the LogisticRegressionCV model.

    Attributes:
        cs (int): number of candidate regularization strengths (log-spaced)
        l1_ratios (list[float]): candidate L1 ratios for the elastic net penalty
        cv (int): cross-validation folds inside LogisticRegressionCV
        solver (str): solver for LogisticRegressionCV (default: saga, supports l1/elasticnet)
        max_iter (int): maximum number of solver iterations
        n_jobs (int): parallel jobs for LogisticRegressionCV (-1 = all cores)
        verbose (int): verbosity of LogisticRegressionCV
    """
    cs: int = 10
    l1_ratios: list[float] = field(default_factory=lambda: [0.0, 0.5, 1.0])
    cv: int = 5
    solver: str = "saga"
    max_iter: int = 2000
    n_jobs: int = 8
    verbose: int = 0


@dataclass
class Config:
    """
    Full experiment definition for training the window model.

    Attributes:
        window_sizes (list[int]): candidate window sizes, each is trained and validated separately
        leagues (list[str]): football-data.co.uk league codes to train on
        seasons (list[int]): seasons to train on, as in football-data.co.uk URLs
        seed (int): random seed for the train/validation split and cross-validation
        test_size (float): fraction of the data used for validation
        verbose (int): 0 = silent, 1 = per-window log loss and a final summary
        output_path (str): file the best WindowModel is pickled to (lzma-compressed)
        grid (GridConfig): grid search settings
        model (ModelConfig): model settings
    """
    window_sizes: list[int] = field(default_factory=lambda: [3, 4, 5])
    leagues: list[str] = field(default_factory=lambda: ["E0", "D1"])
    seasons: list[int] = field(default_factory=lambda: [2021, 2122, 2223, 2324, 2425, 2526])

    seed: int = 42
    test_size: float = 0.2
    verbose: int = 1
    output_path: str = "log_reg_window.model"

    grid: GridConfig = field(default_factory=GridConfig)
    model: ModelConfig = field(default_factory=ModelConfig)

    @classmethod
    def from_toml(cls, path: Path) -> Config:
        """
        Load a Config from a TOML file.

        Parameters:
            path (Path): TOML file with the experiment definition; the [grid] and [model]
                tables override the nested configs, all other keys map to Config fields

        Returns:
            Config: the loaded config
        """
        data = tomllib.loads(path.read_text())
        grid_data = data.pop("grid", {})
        model_data = data.pop("model", {})
        cfg = cls(**{k: v for k, v in data.items() if k in _field_names(cls)})
        cfg.grid = GridConfig(**{k: v for k, v in grid_data.items() if k in _field_names(GridConfig)})
        cfg.model = ModelConfig(**{k: v for k, v in model_data.items() if k in _field_names(ModelConfig)})
        return cfg


def _field_names(dc) -> set[str]:
    """Field names of a dataclass, used to filter TOML keys."""
    return {f.name for f in fields(dc)}


def parse_args() -> Config:
    """
    Parse CLI arguments into a Config.

    The TOML config (--config) defines the experiment; the CLI flags only override
    verbosity and parallelism on top of it.

    Returns:
        Config: experiment config, built-in defaults if --config is omitted
    """
    p = argparse.ArgumentParser(
        description="Train logistic regression on sliding window of match results. Everything that affects the model is defined in the TOML config, only verbosity and parallelism can be set from the CLI.")
    p.add_argument("--config", type=Path, default=None,
                   help="TOML config file with the experiment definition (built-in defaults if omitted).")
    p.add_argument("--verbose", type=int, default=None, help="0 = silent, 1 = per-window log loss.")
    p.add_argument("--grid-verbose", type=int, default=None, help="Verbosity of GridSearchCV.")
    p.add_argument("--grid-n-jobs", type=int, default=None, help="Number of jobs for GridSearchCV.")
    p.add_argument("--model-verbose", type=int, default=None, help="Verbosity of LogisticRegressionCV.")
    p.add_argument("--model-n-jobs", type=int, default=None, help="Number of jobs for LogisticRegressionCV.")
    args = p.parse_args()

    cfg = Config.from_toml(args.config) if args.config and args.config.exists() else Config()

    if args.verbose is not None:
        cfg.verbose = args.verbose

    grid_overrides = {"verbose": args.grid_verbose, "n_jobs": args.grid_n_jobs}
    for key, value in grid_overrides.items():
        if value is not None:
            setattr(cfg.grid, key, value)

    model_overrides = {"verbose": args.model_verbose, "n_jobs": args.model_n_jobs}
    for key, value in model_overrides.items():
        if value is not None:
            setattr(cfg.model, key, value)

    return cfg


def main(cfg: Config):
    """
    Train and validate a window model for each window size, save the best one.

    For every window size in cfg.window_sizes a training matrix is built, split into
    train/validation, and a GridSearchCV over the polynomial degrees is fitted. The
    model with the lowest validation log loss is pickled (lzma-compressed) to
    cfg.output_path.

    Parameters:
        cfg (Config): experiment definition
    """
    best_model = None
    best_log_loss = float("inf")

    for sz in cfg.window_sizes:
        X_data, y_data = create_train_data.create_windows_train_data(cfg.leagues, cfg.seasons, window=sz)
        X_train, X_validate, y_train, y_validate = sk.model_selection.train_test_split(
            X_data, y_data, test_size=cfg.test_size, shuffle=True, random_state=cfg.seed
        )

        col_transform = sk.compose.ColumnTransformer([
            ("one_hot_home", sk.preprocessing.OneHotEncoder(), slice(0, sz)),
            ("poly_home", sk.preprocessing.PolynomialFeatures(degree=2, interaction_only=True), slice(0, sz)),
            ("one_hot_away", sk.preprocessing.OneHotEncoder(), slice(sz, 2 * sz)),
            ("poly_away", sk.preprocessing.PolynomialFeatures(degree=2, interaction_only=True), slice(sz, 2 * sz))
        ])

        pipe = sk.pipeline.Pipeline([
            ("transformer", col_transform),
            ("model", sk.linear_model.LogisticRegressionCV(
                Cs=cfg.model.cs, l1_ratios=tuple(cfg.model.l1_ratios), cv=cfg.model.cv,
                scoring=cfg.grid.scoring, n_jobs=cfg.model.n_jobs, solver=cfg.model.solver,
                max_iter=cfg.model.max_iter, random_state=cfg.seed, verbose=cfg.model.verbose,
                use_legacy_attributes=True))
        ])

        param_grid = {
            "transformer__poly_home__degree": cfg.grid.poly_degrees,
            "transformer__poly_away__degree": cfg.grid.poly_degrees
        }
        cv = sk.model_selection.StratifiedKFold(n_splits=cfg.grid.cv_splits, shuffle=True, random_state=cfg.seed)
        grid = sk.model_selection.GridSearchCV(pipe, param_grid, cv=cv, scoring=cfg.grid.scoring,
                                               n_jobs=cfg.grid.n_jobs, verbose=cfg.grid.verbose)

        grid.fit(X_train, y_train)

        pred = grid.predict_proba(X_validate)
        log_loss = sk.metrics.log_loss(y_validate, pred)

        if cfg.verbose >= 1:
            print(f"window size {sz}, log loss: {log_loss}")

        if log_loss < best_log_loss:
            best_model = window_model.WindowModel(sz, grid.best_estimator_)
            best_log_loss = log_loss

    if best_model is not None:
        with lzma.open(cfg.output_path, "wb") as f:
            pickle.dump(best_model, f)
        if cfg.verbose >= 1:
            print(f"best log loss: {best_log_loss}, model saved to {cfg.output_path}")


if __name__ == "__main__":
    main(parse_args())
