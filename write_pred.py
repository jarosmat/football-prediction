import argparse
import pandas as pd
from pathlib import Path



def dataframe_to_markdown(df: pd.DataFrame) -> list[str]:
    """
    Serializes a DataFrame as a GitHub-flavored Markdown table.

    Args:
        df (pd.DataFrame): DataFrame to serialize.

    Returns:
        str: Markdown table.
    """
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + " --- |" * len(cols)]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join("" if pd.isna(value) else str(value) for value in row) + " |")
    return lines

def markdown_to_dataframe(markdown: str, accuracy: int) -> pd.DataFrame:
    """
    Converts a multiline string containing Markdown table into DataFrame.

    Args:
        markdown (str): Multiline string containing Markdown table.
        accuracy (int): Number of decimal places to display for match result probabilities.

    Returns:
        pd.DataFrame: Resulting DataFrame
    """
    lines = markdown.strip('\n').split('\n')
    header = lines[0].strip('|').split('|')

    data = []
    for line in lines[2:]:
        if not line:
            break

        cols = line.strip('|').split('|')

        row = dict(zip(header, cols))
        data.append(row)


    df = pd.DataFrame(data).round(accuracy)

    return df





def update_predictions_md(path: Path, day: str, predictions: pd.DataFrame, accuracy: int):
    """
    Writes predictions for a day into the Markdown file.

    Creates the file if it does not exist. Otherwise, replaces the section for
    `day` if one is present and keeps all other sections.

    Args:
        path (Path): Markdown file to update.
        day (str): Day the predictions are for, in ISO format (YYYY-MM-DD).
        predictions (pd.DataFrame): Predictions for the day.
        accuracy (int): Number of decimal places to display for match result probabilities.
    """

    sections: dict[str, list[str]] = {}
    preamble: list[str] = []
    if path.exists():
        current: str | None = None
        for line in path.read_text().splitlines():
            if line.startswith("## "):
                current = line[3:].strip()
                if current is not None:
                    sections[current] = []
            elif current is None:
                preamble.append(line)
            else:
                sections[current].append(line)
    else:
        preamble = ["# Prediction results", "", "Automatically generated after inference run.", ""]

    dfs: dict[str, pd.DataFrame] = {}

    for d, section in sections.items():
        dfs[d] = markdown_to_dataframe('\n'.join(section), accuracy)

    dfs[day] = predictions.round(accuracy)



    body = "\n\n".join(f"## {d}\n\n" + "\n".join(dataframe_to_markdown(frame)).strip("\n")
                   for d, frame in sorted(dfs.items(), reverse=True))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(preamble).rstrip() + "\n\n" + body + "\n")

def parse_args() -> argparse.Namespace:
    """
    Parse the CLI args.

    Returns:
        argparse.Namespace: Parsed CLI args.

    """
    p = argparse.ArgumentParser(description="Append predictions from a file to end of specified Markdown file.")
    p.add_argument("--predictions", type=Path, default=Path("predictions.csv"),
                   help="CSV file to write predictions to.")
    p.add_argument("--dest", type=Path, default=Path("docs/Predictions.md"),
                   help="Markdown file to write the predictions table to.")
    p.add_argument("--accuracy", type=int, default=5,
                   help="Number of decimal places to display for match result probabilities.")
    return p.parse_args()



def main(args: argparse.Namespace):
    df = pd.read_csv(args.predictions)

    if not isinstance(df, pd.DataFrame):
       raise SystemExit("Valid CSV file needed.")

    day = str(df["Date"].iloc[0])
    update_predictions_md(args.dest, day, df, args.accuracy)
    print(f"predictions for {day} written to {args.dest}")

if __name__ == "__main__":
    main(parse_args())


