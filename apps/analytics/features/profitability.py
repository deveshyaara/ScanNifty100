"""
Analytics features - Profitability metrics
"""


from .common import ratio, number


def calculate_gross_margin(revenue, cost_of_goods_sold):
    """Calculate gross profit margin"""
    revenue, cost_of_goods_sold = number(revenue), number(cost_of_goods_sold)
    if revenue is None or cost_of_goods_sold is None:
        return None
    return ratio(revenue - cost_of_goods_sold, revenue)


def calculate_operating_margin(operating_income, revenue):
    """Calculate operating profit margin"""
    return ratio(operating_income, revenue)


def calculate_net_margin(net_income, revenue):
    """Calculate net profit margin"""
    return ratio(net_income, revenue)
