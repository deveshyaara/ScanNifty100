"""Bounded-query snapshots shared by the web views."""
from types import SimpleNamespace

from django.db.models import OuterRef, Subquery

from apps.web.apps.analytics.models import Metric
from apps.web.apps.scoring.models import MLScore


def latest_metrics():
    latest = Metric.objects.filter(symbol_id=OuterRef('symbol_id')).order_by('-year__sort_order').values('id')[:1]
    return Metric.objects.filter(id=Subquery(latest)).select_related('symbol__sector', 'year')


def attach_snapshots(companies):
    companies = list(companies)
    symbols = [c.symbol for c in companies]
    scores = {
        s.symbol_id: s
        for s in MLScore.objects.filter(symbol_id__in=symbols).order_by('computed_at', 'score_id')
    }
    metrics = {m.symbol_id: m for m in latest_metrics().filter(symbol_id__in=symbols)}
    for company in companies:
        company.latest_score = scores.get(company.symbol)
        metric = metrics.get(company.symbol)
        data = dict(metric.metrics) if metric else {}
        data['opm_pct'] = data.get('operating_margin_pct')
        company.latest_pl = SimpleNamespace(**data) if metric else None
        company.latest_bs = company.latest_pl
    return companies


def parse_decimal_filter(value, name, minimum=None, maximum=None):
    """Return a float query parameter or a user-facing validation message."""
    if value in (None, ""):
        return None, None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None, f"{name} must be numeric."
    if minimum is not None and parsed < minimum:
        return None, f"{name} must be at least {minimum}."
    if maximum is not None and parsed > maximum:
        return None, f"{name} must be at most {maximum}."
    return parsed, None
