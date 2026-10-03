"""
ML Health Scoring fact tables.
"""
from django.db import models
from apps.web.apps.companies.models import Company


class HealthLabel(models.Model):
    """Dimension: Health score band labels"""
    label_id = models.AutoField(primary_key=True)
    label_name = models.CharField(max_length=20, unique=True)
    min_score = models.IntegerField()
    max_score = models.IntegerField()
    color_hex = models.CharField(max_length=7)

    class Meta:
        db_table = 'dim_health_label'
        managed = False
        ordering = ['-min_score']

    def __str__(self):
        return f"{self.label_name} ({self.min_score}-{self.max_score})"


class MLScore(models.Model):
    """Fact: ML-generated company health scores"""
    score_id = models.AutoField(primary_key=True)
    symbol = models.ForeignKey(Company, on_delete=models.CASCADE, db_column='symbol')
    computed_at = models.DateTimeField()
    
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    coverage_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    explanation = models.JSONField(null=True)
    efficiency_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    consistency_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    profitability_score = models.DecimalField(max_digits=5, decimal_places=2)
    growth_score = models.DecimalField(max_digits=5, decimal_places=2)
    leverage_score = models.DecimalField(max_digits=5, decimal_places=2)
    cashflow_score = models.DecimalField(max_digits=5, decimal_places=2)
    dividend_score = models.DecimalField(max_digits=5, decimal_places=2)
    trend_score = models.DecimalField(max_digits=5, decimal_places=2)
    health_label = models.CharField(max_length=20)

    class Meta:
        db_table = 'fact_ml_scores'
        managed = False
        ordering = ['symbol', '-computed_at']
        get_latest_by = 'computed_at'

    def __str__(self):
        return f"{self.symbol_id} | {self.health_label} ({self.overall_score})"


class ProsCons(models.Model):
    """Fact: Pros and cons insights (manual + ML-generated)"""
    insight_id = models.AutoField(primary_key=True)
    symbol = models.ForeignKey(Company, on_delete=models.CASCADE, db_column='symbol')
    is_pro = models.BooleanField()
    category = models.CharField(max_length=100)
    text = models.TextField()
    source = models.CharField(max_length=20)  # 'MANUAL' or 'ML'
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fact_pros_cons'
        managed = False
        ordering = ['symbol', '-is_pro', 'category']
        verbose_name_plural = 'Pros and Cons'

    def __str__(self):
        flag = "PRO" if self.is_pro else "CON"
        return f"{self.symbol_id} | {flag} | {self.category}"
