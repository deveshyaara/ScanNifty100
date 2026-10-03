"""
Company views for web interface.
"""
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator

from .models import Company, Sector
from apps.web.apps.scoring.models import MLScore, ProsCons
from apps.web.apps.financials.models import ProfitLoss, BalanceSheet, CashFlow
from .query import attach_snapshots


def home(request):
    """Homepage with market overview"""
    
    # Get total companies
    total_companies = Company.objects.count()
    
    # SQLite doesn't support DISTINCT ON, so we'll use a subquery approach
    from django.db.models import F, Max, OuterRef, Subquery
    
    latest_score_ids = MLScore.objects.filter(
        symbol=OuterRef('symbol')
    ).order_by('-computed_at').values('score_id')[:1]
    
    latest_scores = list(MLScore.objects.filter(
        score_id__in=Subquery(latest_score_ids)
    ).select_related('symbol__sector'))
    
    # Get health distribution
    health_distribution = {
        'EXCELLENT': sum(1 for s in latest_scores if s.health_label == 'EXCELLENT'),
        'GOOD': sum(1 for s in latest_scores if s.health_label == 'GOOD'),
        'AVERAGE': sum(1 for s in latest_scores if s.health_label == 'AVERAGE'),
        'WEAK': sum(1 for s in latest_scores if s.health_label == 'WEAK'),
        'POOR': sum(1 for s in latest_scores if s.health_label == 'POOR'),
    }
    
    # Get sector distribution
    sector_distribution = list(
        Sector.objects.annotate(
            company_count=Count('company')
        ).values('sector_name', 'company_count').order_by('-company_count')
    )
    
    # Top performers (by health score)
    top_performers = sorted([s for s in latest_scores if s.overall_score is not None], key=lambda s: s.overall_score, reverse=True)[:10]
    
    context = {
        'total_companies': total_companies,
        'health_distribution': health_distribution,
        'sector_distribution': sector_distribution,
        'top_performers': top_performers,
        'unscored_count': max(0, total_companies - sum(health_distribution.values())),
    }
    
    return render(request, 'pages/home.html', context)


def company_list(request):
    """Filterable company listing"""
    
    # Base queryset
    companies = Company.objects.select_related('sector').all().order_by('company_name')
    
    # Filters
    sector_filter = request.GET.get('sector')
    search_query = request.GET.get('q')
    health_filter = request.GET.get('health')
    
    if sector_filter:
        companies = companies.filter(sector__sector_name=sector_filter)
    
    if search_query:
        companies = companies.filter(
            Q(symbol__icontains=search_query) | 
            Q(company_name__icontains=search_query)
        )
    
    # Attach latest health score to each company
    companies_with_scores = []
    for company in attach_snapshots(companies):
        if health_filter and (company.latest_score is None or company.latest_score.health_label != health_filter):
            continue
        companies_with_scores.append(company)
    
    # Pagination
    paginator = Paginator(companies_with_scores, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'sectors': Sector.objects.all().order_by('sector_name'),
        'selected_sector': sector_filter,
        'search_query': search_query,
        'selected_health': health_filter,
    }
    
    return render(request, 'pages/companies/list.html', context)


def company_detail(request, symbol):
    """Company detail page with financial charts"""
    
    company = get_object_or_404(Company.objects.select_related('sector'), symbol=symbol)
    
    # Get financial data
    profit_loss_data = ProfitLoss.objects.filter(
        symbol=company
    ).select_related('year').order_by('year__sort_order')
    
    balance_sheet_data = BalanceSheet.objects.filter(
        symbol=company
    ).select_related('year').order_by('year__sort_order')
    
    cash_flow_data = CashFlow.objects.filter(
        symbol=company
    ).select_related('year').order_by('year__sort_order')
    
    # Get latest health score
    try:
        latest_score = company.mlscore_set.latest('computed_at')
    except MLScore.DoesNotExist:
        latest_score = None
    
    # Get pros/cons
    from apps.web.apps.scoring.models import ProsCons
    proscons = ProsCons.objects.filter(symbol=company).order_by('-is_pro', 'category')
    
    context = {
        'company': company,
        'latest_score': latest_score,
        'profit_loss_data': profit_loss_data,
        'balance_sheet_data': balance_sheet_data,
        'cash_flow_data': cash_flow_data,
        'chart_data': list(profit_loss_data.values('year__year_label', 'sales', 'net_profit', 'net_profit_margin_pct', 'opm_pct')),
        'proscons': proscons,
    }
    
    return render(request, 'pages/companies/detail.html', context)
