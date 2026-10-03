"""Cash generation metrics. Capex is a positive cash-outflow amount."""
from .common import number, ratio


def free_cash_flow(cfo, capex):
    cfo, capex = number(cfo), number(capex)
    return cfo - capex if cfo is not None and capex is not None and capex >= 0 else None


def cash_conversion(cfo, net_profit):
    return ratio(cfo, net_profit)
