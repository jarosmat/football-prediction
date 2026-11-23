# Football Predictions

This project contains data-aggregation, training and inference modules for predicting the outcomes of football matches.

# Environment

Environment and dependencies are managed via Nix and devenv.sh. To install
dependencies, first install Nix and devenv, then run:

```shell
devenv shell
```

At the moment following dependencies are used:

- [Football-Data.co.uk](https://football-data.co.uk/) for sourcing data about
  results of past matches, used for training
- [API Ninjas](https://api-ninjas.com/api/football) for sourcing information
  about upcoming matches
- `Python`
- `Python` packages:
    - `pandas`
    - `numpy`
    - `matplotlib`
    - `scikit-learn`
    - `requests`

# Documentation

# Deployment

Training is done locally and inference is running as a cron job in GitHub Actions. Each day in the morning a prediction
on currently supported leagues is run. At the moment only Premier League predictions are run.