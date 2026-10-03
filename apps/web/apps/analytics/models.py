"""
Analytics fact tables.
"""
from django.db import models
from apps.web.apps.companies.models import Company
from apps.web.apps.core.models import Year


class Metric(models.Model):
    id = models.BigAutoField(primary_key=True)
    symbol = models.ForeignKey(Company, on_delete=models.CASCADE, db_column='symbol')
    year = models.ForeignKey(Year, on_delete=models.CASCADE, db_column='year_id')
    metrics = models.JSONField()
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    coverage_pct = models.DecimalField(max_digits=5, decimal_places=2)
    explanation = models.JSONField()

    class Meta:
        db_table = 'fact_metrics'
        managed = False
        unique_together = [['symbol', 'year']]
        ordering = ['-year__sort_order', 'symbol_id']


class Analysis(models.Model):
    """Fact: Growth metrics analysis"""
    id = models.BigAutoField(primary_key=True)
    symbol = models.ForeignKey(Company, on_delete=models.CASCADE, db_column='symbol')
    period_label = models.CharField(max_length=10)  # '10Y', '5Y', '3Y', 'TTM'
    compounded_sales_growth_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    compounded_profit_growth_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    stock_price_cagr_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    roe_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)

    class Meta:
        db_table = 'fact_analysis'
        managed = False
        unique_together = [['symbol', 'period_label']]
        ordering = ['symbol', 'period_label']

    def __str__(self):
        return f"{self.symbol_id} | {self.period_label}"
