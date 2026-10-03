"""Returns use average opening and closing balances for matching annual periods."""
from .common import number, ratio


def return_on_average(profit, opening, closing):
    opening, closing = number(opening), number(closing)
    if opening is None or closing is None or opening <= 0 or closing <= 0:
        return None
    return ratio(profit, (opening + closing) / 2)
