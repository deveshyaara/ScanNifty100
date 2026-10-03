"""
Analytics features - Growth metrics
"""


from .common import ratio, number


def calculate_revenue_growth(current_revenue, previous_revenue):
    """Calculate year-over-year revenue growth"""
    result = ratio(current_revenue, previous_revenue)
    return result - 1 if result is not None else None


def calculate_cagr(beginning_value, ending_value, num_years):
    """Calculate compound annual growth rate"""
    beginning_value, ending_value, num_years = map(number, (beginning_value, ending_value, num_years))
    if beginning_value is None or ending_value is None or num_years is None:
        return None
    if beginning_value <= 0 or ending_value < 0 or num_years <= 0:
        return None
    return (ending_value / beginning_value) ** (1 / num_years) - 1
