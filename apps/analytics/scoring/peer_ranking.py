"""Rank only scored observations, with equal scores sharing ranks."""
import pandas as pd


def rank_companies(frame):
    frame = frame.copy()
    frame["rank"] = frame.overall_score.rank(method="min", ascending=False)
    count = frame.overall_score.notna().sum()
    frame["percentile"] = (count - frame["rank"]) / (count - 1) * 100 if count > 1 else frame.overall_score.map(lambda x: 100.0 if pd.notna(x) else float("nan"))
    frame["sector_rank"] = frame.groupby("sector", dropna=True).overall_score.rank(method="min", ascending=False)
    return frame.sort_values(["rank", "company"], na_position="last")
