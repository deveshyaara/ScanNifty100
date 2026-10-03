"""
Shared dimension models.
"""
from django.db import models


class Year(models.Model):
    """Dimension: Fiscal year and period"""
    year_id = models.AutoField(primary_key=True)
    year_label = models.CharField(max_length=20)
    fiscal_year = models.IntegerField(null=True)
    quarter = models.CharField(max_length=5, blank=True, null=True)
    is_ttm = models.BooleanField(default=False)
    is_half_year = models.BooleanField(default=False)
    sort_order = models.IntegerField()

    class Meta:
        db_table = 'dim_year'
        managed = False
        ordering = ['sort_order']

    def __str__(self):
        return self.year_label
