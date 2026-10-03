"""DRF ViewSets for REST API."""
import json
from pathlib import Path

from django.conf import settings
from django.db.models import OuterRef, Subquery, F
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.web.apps.analytics.models import Metric
from apps.web.apps.analytics.serializers import MetricSerializer

from apps.web.apps.companies.models import Company, Sector
from apps.web.apps.financials.models import ProfitLoss, BalanceSheet, CashFlow
from apps.web.apps.scoring.models import MLScore, ProsCons

from .serializers import (
    CompanyListSerializer, CompanyDetailSerializer, SectorSerializer,
    ProfitLossSerializer, BalanceSheetSerializer, CashFlowSerializer,
    MLScoreSerializer, ProsConsSerializer
)


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for companies.
    
    list: GET /api/v1/companies/
    retrieve: GET /api/v1/companies/<symbol>/
    financials: GET /api/v1/companies/<symbol>/financials/
    health: GET /api/v1/companies/<symbol>/health/
    proscons: GET /api/v1/companies/<symbol>/proscons/
    """
    queryset = Company.objects.select_related('sector').all()
    lookup_field = 'symbol'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sector__sector_name']
    search_fields = ['symbol', 'company_name']
    ordering_fields = ['symbol', 'company_name']

    def get_queryset(self):
        latest = MLScore.objects.filter(symbol_id=OuterRef('pk')).order_by('-computed_at', '-score_id')
        return super().get_queryset().annotate(
            latest_health_score=Subquery(latest.values('overall_score')[:1]),
            latest_health_label=Subquery(latest.values('health_label')[:1]),
        )

    def statement(self, model, serializer):
        query = model.objects.filter(symbol=self.get_object()).select_related('year')
        year = self.request.query_params.get('year')
        if year:
            query = query.filter(year__year_label=year)
        page = self.paginate_queryset(query)
        return self.get_paginated_response(serializer(page, many=True).data)

    @action(detail=True, methods=['get'], url_path='profit-loss')
    def profit_loss(self, request, symbol=None):
        return self.statement(ProfitLoss, ProfitLossSerializer)

    @action(detail=True, methods=['get'], url_path='balance-sheet')
    def balance_sheet(self, request, symbol=None):
        return self.statement(BalanceSheet, BalanceSheetSerializer)

    @action(detail=True, methods=['get'], url_path='cash-flow')
    def cash_flow(self, request, symbol=None):
        return self.statement(CashFlow, CashFlowSerializer)

    @action(detail=True, methods=['get'])
    def score(self, request, symbol=None):
        query = Metric.objects.filter(symbol=self.get_object()).select_related('symbol', 'year')
        if request.query_params.get('year'):
            query = query.filter(year__year_label=request.query_params['year'])
        metric = query.order_by('-year__sort_order').first()
        if metric is None:
            return Response({'detail': 'No comparable annual metrics available.'}, status=404)
        return Response(MetricSerializer(metric).data)

    def get_serializer_class(self):
        if self.action == 'list':
            return CompanyListSerializer
        return CompanyDetailSerializer

    @action(detail=True, methods=['get'])
    def financials(self, request, symbol=None):
        """
        GET /api/v1/companies/<symbol>/financials/
        Returns time-series P&L, balance sheet, and cash flow for all years.
        """
        company = self.get_object()
        
        pl_data = ProfitLoss.objects.filter(symbol=company).select_related('year')
        bs_data = BalanceSheet.objects.filter(symbol=company).select_related('year')
        cf_data = CashFlow.objects.filter(symbol=company).select_related('year')
        
        return Response({
            'symbol': symbol,
            'company_name': company.company_name,
            'profit_loss': ProfitLossSerializer(pl_data, many=True).data,
            'balance_sheet': BalanceSheetSerializer(bs_data, many=True).data,
            'cash_flow': CashFlowSerializer(cf_data, many=True).data,
        })

    @action(detail=True, methods=['get'])
    def health(self, request, symbol=None):
        """
        GET /api/v1/companies/<symbol>/health/
        Returns ML health score breakdown (all 6 sub-dimensions).
        """
        company = self.get_object()
        try:
            latest_score = MLScore.objects.filter(symbol=company).latest('computed_at')
            return Response(MLScoreSerializer(latest_score).data)
        except MLScore.DoesNotExist:
            return Response({'detail': 'No health score available for this company.'}, status=404)

    @action(detail=True, methods=['get'])
    def proscons(self, request, symbol=None):
        """
        GET /api/v1/companies/<symbol>/proscons/
        Returns structured pros and cons list.
        """
        company = self.get_object()
        proscons = ProsCons.objects.filter(symbol=company)
        return Response(ProsConsSerializer(proscons, many=True).data)

    @action(detail=False, methods=['get'])
    def compare(self, request):
        """
        GET /api/v1/companies/compare/?symbols=RELIANCE,TCS
        Returns latest comparable annual metrics for 2-10 companies.
        """
        symbols = [
            value.strip().upper()
            for value in request.query_params.get('symbols', '').split(',')
            if value.strip()
        ]
        if not 2 <= len(symbols) <= 10:
            raise ValidationError({'symbols': 'Provide 2 to 10 comma-separated symbols.'})
        latest = Metric.objects.filter(symbol_id=OuterRef('symbol_id')).order_by(
            '-year__sort_order'
        ).values('id')[:1]
        metrics = Metric.objects.filter(
            symbol_id__in=symbols,
            id=Subquery(latest),
        ).select_related('symbol', 'year')
        found = {metric.symbol_id for metric in metrics}
        return Response({
            'symbols': symbols,
            'missing': [symbol for symbol in symbols if symbol not in found],
            'results': MetricSerializer(metrics, many=True).data,
        })


class SectorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for sectors.
    
    list: GET /api/v1/sectors/
    retrieve: GET /api/v1/sectors/<code>/
    companies: GET /api/v1/sectors/<code>/companies/
    """
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
    lookup_field = 'sector_code'

    @action(detail=True, methods=['get'])
    def companies(self, request, sector_code=None):
        """
        GET /api/v1/sectors/<code>/companies/
        Returns all companies in this sector with health scores.
        """
        sector = self.get_object()
        latest = MLScore.objects.filter(symbol_id=OuterRef('pk')).order_by('-computed_at')
        companies = Company.objects.filter(sector=sector).select_related('sector').annotate(latest_health_score=Subquery(latest.values('overall_score')[:1]), latest_health_label=Subquery(latest.values('health_label')[:1]))
        page = self.paginate_queryset(companies)
        return self.get_paginated_response(CompanyListSerializer(page, many=True).data)


class MetricViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MetricSerializer
    queryset = Metric.objects.select_related('symbol', 'year')
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['symbol', 'symbol__sector', 'year__year_label']
    ordering_fields = ['overall_score', 'coverage_pct', 'symbol']

    def get_queryset(self):
        query = super().get_queryset()
        for param, field in [('min_score', 'overall_score__gte'), ('max_score', 'overall_score__lte'), ('min_coverage', 'coverage_pct__gte')]:
            if param in self.request.query_params:
                try:
                    value = float(self.request.query_params[param])
                    if not 0 <= value <= 100:
                        raise ValueError()
                except ValueError:
                    raise ValidationError({param: 'Must be a number between 0 and 100.'})
                query = query.filter(**{field: value})
        return query


class RankingViewSet(MetricViewSet):
    def get_queryset(self):
        query = super().get_queryset()
        if not self.request.query_params.get('year__year_label'):
            latest = Metric.objects.filter(symbol_id=OuterRef('symbol_id')).order_by('-year__sort_order').values('id')[:1]
            query = query.filter(id=Subquery(latest))
        return query.order_by(F('overall_score').desc(nulls_last=True), 'symbol_id')


class DataQualityView(APIView):
    """Expose the generated ETL reconciliation report to the deployment API."""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        report_path = Path(settings.BASE_DIR).parents[1] / 'reports' / 'data_quality.json'
        if not report_path.exists():
            return Response({'detail': 'Data quality report has not been generated.'}, status=404)
        with report_path.open(encoding='utf-8') as handle:
            return Response(json.load(handle))
