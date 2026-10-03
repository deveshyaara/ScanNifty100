"""
DRF Serializers for all API endpoints.
"""
from rest_framework import serializers
from apps.web.apps.companies.models import Company, Sector
from apps.web.apps.financials.models import ProfitLoss, BalanceSheet, CashFlow
from apps.web.apps.scoring.models import MLScore, ProsCons


class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = ['sector_code', 'sector_name', 'description']


class CompanyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for company listings"""
    sector_name = serializers.CharField(source='sector.sector_name', read_only=True)
    latest_health_score = serializers.FloatField(read_only=True, allow_null=True)
    latest_health_label = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = Company
        fields = [
            'symbol', 'company_name', 'sector_name',
            'company_logo', 'latest_health_score', 'latest_health_label'
        ]

    def get_latest_health_score(self, obj):
        try:
            latest = obj.mlscore_set.latest('computed_at')
            return float(latest.overall_score)
        except MLScore.DoesNotExist:
            return None

    def get_latest_health_label(self, obj):
        try:
            latest = obj.mlscore_set.latest('computed_at')
            return latest.health_label
        except MLScore.DoesNotExist:
            return None


class CompanyDetailSerializer(serializers.ModelSerializer):
    """Full company profile with all metadata"""
    sector_name = serializers.CharField(source='sector.sector_name', read_only=True)
    
    class Meta:
        model = Company
        fields = '__all__'


class ProfitLossSerializer(serializers.ModelSerializer):
    year_label = serializers.CharField(source='year.year_label', read_only=True)
    
    class Meta:
        model = ProfitLoss
        exclude = ['symbol', 'year']


class BalanceSheetSerializer(serializers.ModelSerializer):
    year_label = serializers.CharField(source='year.year_label', read_only=True)
    
    class Meta:
        model = BalanceSheet
        exclude = ['symbol', 'year']


class CashFlowSerializer(serializers.ModelSerializer):
    year_label = serializers.CharField(source='year.year_label', read_only=True)
    
    class Meta:
        model = CashFlow
        exclude = ['symbol', 'year']


class MLScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLScore
        exclude = ['symbol']


class ProsConsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProsCons
        fields = ['is_pro', 'category', 'text', 'source', 'confidence']
