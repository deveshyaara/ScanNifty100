"""Scalar financial arithmetic; unavailable inputs remain unavailable."""
import math


def number(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def ratio(numerator, denominator, positive_denominator=True):
    numerator, denominator = number(numerator), number(denominator)
    if numerator is None or denominator is None or denominator == 0:
        return None
    if positive_denominator and denominator < 0:
        return None
    return numerator / denominator
