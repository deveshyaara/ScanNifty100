"""Root-level views (screener, etc.)."""
from django.db.models import F
from django.shortcuts import render

from apps.web.apps.companies.models import Company, Sector
from apps.web.apps.companies.query import (
    attach_snapshots,
    latest_metrics,
    parse_decimal_filter,
)


def screener(request):
    """Custom company screener with latest comparable annual metrics."""
    raw_filters = {
        "min_score": request.GET.get("min_score"),
        "min_sales": request.GET.get("min_sales"),
        "min_opm": request.GET.get("min_opm"),
        "max_de": request.GET.get("max_de"),
        "sector": request.GET.get("sector"),
    }

    numeric_filters = {}
    errors = []
    for key, label, minimum, maximum in [
        ("min_score", "Health score", 0, 100),
        ("min_sales", "Revenue", 0, None),
        ("min_opm", "Operating margin", 0, 100),
        ("max_de", "Debt-to-equity", 0, None),
    ]:
        value, error = parse_decimal_filter(raw_filters[key], label, minimum, maximum)
        numeric_filters[key] = value
        if error:
            errors.append(error)

    companies = Company.objects.select_related("sector").all()
    if raw_filters["sector"]:
        companies = companies.filter(sector__sector_name=raw_filters["sector"])

    metrics = latest_metrics()
    if numeric_filters["min_score"] is not None:
        metrics = metrics.filter(overall_score__gte=numeric_filters["min_score"])
    if numeric_filters["min_sales"] is not None:
        metrics = metrics.filter(metrics__sales__gte=numeric_filters["min_sales"])
    if numeric_filters["min_opm"] is not None:
        metrics = metrics.filter(
            metrics__operating_margin_pct__gte=numeric_filters["min_opm"]
        )
    if numeric_filters["max_de"] is not None:
        metrics = metrics.filter(metrics__debt_to_equity__lte=numeric_filters["max_de"])

    companies = companies.filter(symbol__in=metrics.values("symbol_id")).order_by(
        F("company_name").asc(nulls_last=True),
        "symbol",
    )
    companies_with_data = attach_snapshots(companies)
    companies_with_data.sort(
        key=lambda company: (
            company.latest_score.overall_score
            if company.latest_score and company.latest_score.overall_score is not None
            else -1
        ),
        reverse=True,
    )

    context = {
        "companies": companies_with_data,
        "total_results": len(companies_with_data),
        "filters": raw_filters,
        "filter_errors": errors,
        "sectors": Sector.objects.all().order_by("sector_name"),
    }
    return render(request, "pages/screener.html", context)
