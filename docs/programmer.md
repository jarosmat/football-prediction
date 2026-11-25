# API Reference
Generated from docstrings in Google format.
## `data_source.source_football_data_co_uk`

### `def fetch_data`

```python
def fetch_data(leagues: list[str], seasons: list[int], file_path: str, columns: list[str], include_season: bool = True)
```

Fetches specified columns about leagues in seasons from football-data.co.uk and saves the data into file.

**Parameters:**

- `leagues` (`list[str]`): Leagues to fetch the data about.
- `seasons` (`list[int]`): Seasons of the leagues to fetch the data about.
- `file_path` (`str`): Where to save the downloaded data.
- `columns` (`list[str]`): What columns to include in the resulting DataFrame.
- `include_season` (`bool`): If the season should be included as a column of the DataFrame.

### `def download_data`

```python
def download_data(leagues: list[str], seasons: list[int], columns: list[str] | None = None, file_path: str = 'football-data-co.csv', force_download: bool = False, include_season: bool = True) -> pd.DataFrame
```

Fetches specified columns about leagues in seasons from football-data.co.uk and saves the data into file.
First checks whether a specified file_path is already present and contains requested data, if it does, just read the
existing data, otherwise fetches the data from the internet.

**Parameters:**

- `leagues` (`list[str]`): Leagues to fetch the data about.
- `seasons` (`list[int]`): Seasons of the leagues to fetch the data about.
- `file_path` (`str`): Where to save the downloaded data.
- `columns` (`list[str]`): What columns to include in the resulting DataFrame.
- `force_download` (`bool`): If set to True data is downloaded even if the csv file containing specified data exists.
- `include_season` (`bool`): If the season should be included as a column of the DataFrame.

**Returns:**

- `pd.DataFrame`: DataFrame containing the specified data.

## `data_source.source_upcoming_matches`

### `def get_matches_played_today`

```python
def get_matches_played_today(api_key: str, leagues: list[str], day: date | None = None) -> dict[str, list[dict]]
```

Fetches matches that are played on given day in specified leagues.

**Parameters:**

- `api_key` (`str`): API Ninjas API key.
- `leagues` (`list[str]`): A list of league codes.
- `day` (`date | None`): Day to fetch matches for, default is today.

**Returns:**

- `dict[str, list[dict]]`: league code -> list of raw match dicts from the API.

### `def get_matches_played_today_dataframe`

```python
def get_matches_played_today_dataframe(api_key: str, leagues: list[str], day: date | None = None) -> pd.DataFrame
```

Returns matches played on the given day.

**Parameters:**

- `api_key` (`str`): API Ninjas API key.
- `leagues` (`list[str]`): A list of league codes.
- `day` (`date | None`): Day to fetch matches for, default is today.

**Notes:**

- Team names are returned in the API Ninjas format.
- Returns the same values as `get_matches_played_today` but serialized in DataFrame.

**Returns:**

- `pd.DataFrame`: DataFrame with columns:
  - League
  - Date
  - Time
  - HomeTeam
  - AwayTeam

## `data_source.team_names`

Translation layer between club name conventions:

- API-Ninjas
- football-data.co.uk

### `def to_football_data`

```python
def to_football_data(name: str) -> str
```

Translate an API-Ninjas club name to the football-data.co.uk convention.

**Parameters:**

- `name` (`str`): API Ninjas club name.

**Returns:**

- `str`: football-data.co.uk club name

### `def to_api_ninjas`

```python
def to_api_ninjas(name: str) -> str
```

Translate a football-data.co.uk club name to the API-Ninjas convention.

**Parameters:**

- `name` (`str`): football-data.co.uk club name.

**Returns:**

- `str`: API Ninjas club name

### Module attributes

- `TO_FOOTBALL_DATA: dict[str, str] = {'AFC Bournemouth': 'Bournemouth', 'Arsenal': 'Arsenal', 'Aston Villa': 'Aston Villa', 'Brentford': 'Brentford', 'Brighton & Hove Albion': 'Brighton', 'Chelsea': 'Chelsea', 'Coventry City': 'Coventry', 'Crystal Palace': 'Crystal Palace', 'Everton': 'Everton', 'Fulham': 'Fulham', 'Hull City': 'Hull', 'Ipswich Town': 'Ipswich', 'Leeds United': 'Leeds', 'Liverpool': 'Liverpool', 'Manchester City': 'Man City', 'Manchester United': 'Man United', 'Newcastle United': 'Newcastle', 'Nottingham Forest': "Nott'm Forest", 'Sunderland': 'Sunderland', 'Tottenham Hotspur': 'Tottenham'}`

- `TO_API_NINJAS: dict[str, str] = {v: k for k, v in (TO_FOOTBALL_DATA.items())}`

## `models.create_train_data`

### `class MatchesIterator`

```python
class MatchesIterator:
    def __init__(df: pd.DataFrame, window: int, reverse: bool = False)
```

Iterates over matches in date order, yielding the form window of both teams and the match result.

**Parameters:**

- `df` (`pd.DataFrame`): match data, must contain the `columns` columns
- `window` (`int`): how many previous matches per team are kept in the window
- `reverse` (`bool`): if True, iterate from the newest match backwards

**Attributes:**

- `columns` (`list[str]`): columns read from the data frame
- `window` (`int`): window size, see Parameters
- `df` (`pd.DataFrame`): the data frame, sorted by date
- `team_deque_dict` (`dict[str, deque[int]]`): per-team deque with the last `window` results
  (-1 = not enough previous matches, 0 = won, 1 = draw, 2 = lost)

**Yields:**

- `tuple[np.ndarray, np.float64 | int]`: (X, y) where X is the concatenated home/away form
  windows and y is the target result (0 = home won, 1 = draw, 2 = away won)

#### Attributes

- `columns = ['Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTR']`

- `window = window`

- `df = df.sort_values(by=['Date']).reset_index(drop=True)`

- `team_deque_dict: dict[str, deque[int]] = dict()`

- `update = 1`

- `i = 0`

#### Methods

#### `def __init__`

```python
def __init__(df: pd.DataFrame, window: int, reverse: bool = False)
```

---
### `def convert_res_val`

```python
def convert_res_val(home: bool, res: Literal['H', 'D', 'A']) -> int
```

**Parameters:**

- `home` (`bool`): whether the team was playing home
- `res` (`Literal['H', 'D', 'A']`): literal from football-data.co.uk specifying who won

**Returns:**

- `int`: 0 the team won, 1 draw, 2 the team lost

### `def convert_res_val_target`

```python
def convert_res_val_target(res: Literal['H', 'D', 'A']) -> int
```

**Parameters:**

- `res` (`Literal['H', 'D', 'A']`): result of a match

**Returns:**

- `int`: 0 if home won, 1 if drawn, 2 if away won

### `def create_windows_train_data`

```python
def create_windows_train_data(leagues: list[str], seasons: list[int], window: int = 5) -> tuple[np.ndarray, np.ndarray]
```

Creates training data for just last n matches results.

**Parameters:**

- `leagues` (`list[str]`): what leagues to query.
- `seasons` (`list[int]`): what seasons to query.
- `window` (`int`): how many last matches to include.

**Returns:**

- `tuple[np.ndarray, np.ndarray]`: train values and targets, values are first n values for window of
  home team, then n values for window of away team, values are:
  -1 did not play - only for windows where there weren't enough previous matches played
  0 team won
  1 draw
  2 team lost
  Targets have values of results of those matches, values are:
  0 home won
  1 draw
  2 away won

### `def create_windows_for_fixtures`

```python
def create_windows_for_fixtures(leagues: list[str], season: int, fixtures: pd.DataFrame, window: int = 5) -> dict[tuple[str, str], tuple[list[int], list[int]]]
```

Creates feature rows for matches that have not been played yet.

**Parameters:**

- `leagues` (`list[str]`): what leagues need history
- `season` (`int`): what season to use for creating the history
- `fixtures` (`pd.DataFrame`): DataFrame with at least HomeTeam and AwayTeam columns (e.g. upcoming matches).
- `window` (`int`): how many last matches per team to include.

**Returns:**

- `dict[tuple[str, str], tuple[list[int], list[int]]]`: data for inference

## `models.inference_window_model`

### `def load_model`

```python
def load_model(path: Path) -> window_model.WindowModel
```

Loads a WindowModel from specified file.

**Parameters:**

- `path` (`Path`): Path to WindowModel.

**Returns:**

- `window_model.WindowModel`: Loaded instance.

### `def parse_args`

```python
def parse_args() -> argparse.Namespace
```

Parse the CLI args.

**Returns:**

- `argparse.Namespace`: Parsed CLI args.

### `def main`

```python
def main(args: argparse.Namespace)
```

Run the inference on WindowModel.

Args (argparse.Namespace):
    args: Arguments specifying how to run the inference.

### Module attributes

- `RESULT_LETTERS = ['H', 'D', 'A']`

- `API_TO_FD_LEAGUE = {'epl': 'E0'}`

- `CURRENT_SEASON = 2627`

## `models.log_reg_window`

Train a logistic regression on a sliding window of match results.

The experiment is defined by a TOML config (see Config). CLI flags only override
verbosity and parallelism. For each window size a model is trained and validated,
and the best one (by validation log loss) is pickled to Config.output_path.

### `class GridConfig`

```python
class GridConfig:
    def __init__(poly_degrees: list[int] = (lambda: [2, 3])(), cv_splits: int = 5, scoring: str = 'neg_log_loss', n_jobs: int = -1, verbose: int = 0) -> None
```

Settings for the grid search over polynomial degrees.

**Attributes:**

- `poly_degrees` (`list[int]`): degrees for the PolynomialFeatures of both teams
- `cv_splits` (`int`): number of StratifiedKFold splits used in GridSearchCV
- `scoring` (`str`): scoring metric for the grid search (default: neg_log_loss)
- `n_jobs` (`int`): parallel jobs for GridSearchCV (-1 = all cores)
- `verbose` (`int`): verbosity of GridSearchCV

#### Attributes

- `poly_degrees: list[int] = field(default_factory=(lambda: [2, 3]))`

- `cv_splits: int = 5`

- `scoring: str = 'neg_log_loss'`

- `n_jobs: int = -1`

- `verbose: int = 0`

#### Methods

#### `def __init__`

```python
def __init__(poly_degrees: list[int] = (lambda: [2, 3])(), cv_splits: int = 5, scoring: str = 'neg_log_loss', n_jobs: int = -1, verbose: int = 0) -> None
```

---
### `class ModelConfig`

```python
class ModelConfig:
    def __init__(cs: int = 10, l1_ratios: list[float] = (lambda: [0.0, 0.5, 1.0])(), cv: int = 5, solver: str = 'saga', max_iter: int = 2000, n_jobs: int = 8, verbose: int = 0) -> None
```

Settings for the LogisticRegressionCV model.

**Attributes:**

- `cs` (`int`): number of candidate regularization strengths (log-spaced)
- `l1_ratios` (`list[float]`): candidate L1 ratios for the elastic net penalty
- `cv` (`int`): cross-validation folds inside LogisticRegressionCV
- `solver` (`str`): solver for LogisticRegressionCV (default: saga, supports l1/elasticnet)
- `max_iter` (`int`): maximum number of solver iterations
- `n_jobs` (`int`): parallel jobs for LogisticRegressionCV (-1 = all cores)
- `verbose` (`int`): verbosity of LogisticRegressionCV

#### Attributes

- `cs: int = 10`

- `l1_ratios: list[float] = field(default_factory=(lambda: [0.0, 0.5, 1.0]))`

- `cv: int = 5`

- `solver: str = 'saga'`

- `max_iter: int = 2000`

- `n_jobs: int = 8`

- `verbose: int = 0`

#### Methods

#### `def __init__`

```python
def __init__(cs: int = 10, l1_ratios: list[float] = (lambda: [0.0, 0.5, 1.0])(), cv: int = 5, solver: str = 'saga', max_iter: int = 2000, n_jobs: int = 8, verbose: int = 0) -> None
```

---
### `class Config`

```python
class Config:
    def __init__(window_sizes: list[int] = (lambda: [3, 4, 5])(), leagues: list[str] = (lambda: ['E0', 'D1'])(), seasons: list[int] = (lambda: [2021, 2122, 2223, 2324, 2425, 2526])(), seed: int = 42, test_size: float = 0.2, verbose: int = 1, output_path: str = 'log_reg_window.model', grid: GridConfig = GridConfig(), model: ModelConfig = ModelConfig()) -> None
```

Full experiment definition for training the window model.

**Attributes:**

- `window_sizes` (`list[int]`): candidate window sizes, each is trained and validated separately
- `leagues` (`list[str]`): football-data.co.uk league codes to train on
- `seasons` (`list[int]`): seasons to train on, as in football-data.co.uk URLs
- `seed` (`int`): random seed for the train/validation split and cross-validation
- `test_size` (`float`): fraction of the data used for validation
- `verbose` (`int`): 0 = silent, 1 = per-window log loss and a final summary
- `output_path` (`str`): file the best WindowModel is pickled to (lzma-compressed)
- `grid` (`GridConfig`): grid search settings
- `model` (`ModelConfig`): model settings

#### Attributes

- `window_sizes: list[int] = field(default_factory=(lambda: [3, 4, 5]))`

- `leagues: list[str] = field(default_factory=(lambda: ['E0', 'D1']))`

- `seasons: list[int] = field(default_factory=(lambda: [2021, 2122, 2223, 2324, 2425, 2526]))`

- `seed: int = 42`

- `test_size: float = 0.2`

- `verbose: int = 1`

- `output_path: str = 'log_reg_window.model'`

- `grid: GridConfig = field(default_factory=GridConfig)`

- `model: ModelConfig = field(default_factory=ModelConfig)`

#### Methods

#### `def from_toml`

```python
def from_toml(path: Path) -> Config
```

Load a Config from a TOML file.

**Parameters:**

- `path` (`Path`): TOML file with the experiment definition; the [grid] and [model]
  tables override the nested configs, all other keys map to Config fields

**Returns:**

- `Config`: the loaded config

#### `def __init__`

```python
def __init__(window_sizes: list[int] = (lambda: [3, 4, 5])(), leagues: list[str] = (lambda: ['E0', 'D1'])(), seasons: list[int] = (lambda: [2021, 2122, 2223, 2324, 2425, 2526])(), seed: int = 42, test_size: float = 0.2, verbose: int = 1, output_path: str = 'log_reg_window.model', grid: GridConfig = GridConfig(), model: ModelConfig = ModelConfig()) -> None
```

---
### `def parse_args`

```python
def parse_args() -> Config
```

Parse CLI arguments into a Config.

The TOML config (--config) defines the experiment; the CLI flags only override
verbosity and parallelism on top of it.

**Returns:**

- `Config`: experiment config, built-in defaults if --config is omitted

### `def main`

```python
def main(cfg: Config)
```

Train and validate a window model for each window size, save the best one.

For every window size in cfg.window_sizes a training matrix is built, split into
train/validation, and a GridSearchCV over the polynomial degrees is fitted. The
model with the lowest validation log loss is pickled (lzma-compressed) to
cfg.output_path.

**Parameters:**

- `cfg` (`Config`): experiment definition

## `models.window_model`

### `class WindowModel`

```python
class WindowModel:
    def __init__(window_size: int, pipeline)
```

Model for window of last match results.

**Attributes:**

- `window_size` (`int`): how many last matches are in the window
- `pipeline` (`sklearn Pipeline`): the fitted sklearn Pipeline.

#### Attributes

- `window_size = window_size`

- `pipeline = pipeline`

#### Methods

#### `def __init__`

```python
def __init__(window_size: int, pipeline)
```

#### `def predict`

```python
def predict(X_data)
```

#### `def predict_proba`

```python
def predict_proba(X_data)
```

---
## `utils.protocols`

### `class Stringable(Protocol)`

```python
class Stringable(Protocol):
```

Protocol for duck typing that requires the parameter to implement __str__ dunder method.

---
