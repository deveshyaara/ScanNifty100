"""Annual analytics with explicit missing-data and score explanations."""
from rest_framework import serializers
from .models import Metric


class MetricSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source="symbol_id")
    year_label = serializers.CharField(source="year.year_label")
    company_name = serializers.CharField(source="symbol.company_name", allow_null=True)

    class Meta:
        model = Metric
        fields = ["symbol", "company_name", "year_label", "overall_score", "coverage_pct", "metrics", "explanation"]
