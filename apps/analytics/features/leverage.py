"""Balance-sheet ratios without proxy inputs."""
from .common import ratio, number


def debt_to_equity(debt, equity):
    return ratio(debt, equity)


def current_ratio(current_assets, current_liabilities):
    return ratio(current_assets, current_liabilities)


def net_debt(debt, cash):
    debt, cash = number(debt), number(cash)
    return debt - cash if debt is not None and cash is not None else None
