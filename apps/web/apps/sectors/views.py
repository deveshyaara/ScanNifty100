"""Sector views for web interface."""
from django.db.models import Avg, Count, F, OuterRef, Subquery
from django.shortcuts import get_object_or_404, render

from apps.web.apps.companies.models import Company, Sector
from apps.web.apps.companies.query import attach_snapshots
from apps.web.apps.scoring.models import MLScore


def sector_list(request):
    """Sector listing with aggregate latest-score metrics."""
    latest_score_ids = MLScore.objects.filter(symbol_id=OuterRef("symbol_id")).order_by(
        "-computed_at",
        "-score_id",
    ).values("score_id")[:1]
    latest_scores = MLScore.objects.filter(score_id=Subquery(latest_score_ids))

    aggregates = {
        row["symbol__sector_id"]: row
        for row in latest_scores.values("symbol__sector_id").annotate(
            avg_health=Avg("overall_score"),
            scored_count=Count("score_id"),
        )
    }
    label_counts = {
        (row["symbol__sector_id"], row["health_label"]): row["count"]
        for row in latest_scores.values("symbol__sector_id", "health_label").annotate(
            count=Count("score_id")
        )
    }
    company_counts = {
        row["sector_id"]: row["count"]
        for row in Company.objects.values("sector_id").annotate(count=Count("symbol"))
    }

    sector_data = []
    for sector in Sector.objects.all().order_by("sector_name"):
        stats = aggregates.get(sector.sector_id, {})
        sector_data.append(
            {
                "sector": sector,
                "company_count": company_counts.get(sector.sector_id, 0),
                "avg_health": stats.get("avg_health") or 0,
                "scored_count": stats.get("scored_count") or 0,
                "health_dist": {
                    "excellent": label_counts.get((sector.sector_id, "EXCELLENT"), 0),
                    "good": label_counts.get((sector.sector_id, "GOOD"), 0),
                    "average": label_counts.get((sector.sector_id, "AVERAGE"), 0),
                    "weak": label_counts.get((sector.sector_id, "WEAK"), 0),
                    "poor": label_counts.get((sector.sector_id, "POOR"), 0),
                },
            }
        )

    sector_data.sort(key=lambda row: row["avg_health"], reverse=True)
    return render(request, "pages/sectors/list.html", {"sector_data": sector_data})


def sector_detail(request, sector_code):
    """Sector deep dive with company rankings."""
    sector = get_object_or_404(Sector, sector_code=sector_code)
    companies = Company.objects.filter(sector=sector).select_related("sector").order_by(
        F("company_name").asc(nulls_last=True),
        "symbol",
    )

    companies_with_scores = attach_snapshots(companies)
    companies_with_scores.sort(
        key=lambda company: (
            company.latest_score.overall_score
            if company.latest_score and company.latest_score.overall_score is not None
            else -1
        ),
        reverse=True,
    )

    scored = [
        company.latest_score.overall_score
        for company in companies_with_scores
        if company.latest_score and company.latest_score.overall_score is not None
    ]
    context = {
        "sector": sector,
        "companies": companies_with_scores,
        "total_companies": len(companies_with_scores),
        "avg_health": sum(scored) / len(scored) if scored else 0,
        "scored_companies": len(scored),
    }
    return render(request, "pages/sectors/detail.html", context)
