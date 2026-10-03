"""
Company dimension models.
Maps to warehouse dim_company and dim_sector tables.
"""
from django.db import models


class Sector(models.Model):
    """Dimension: Sector classification"""
    sector_id = models.AutoField(primary_key=True)
    sector_name = models.CharField(max_length=100, unique=True)
    sector_code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'dim_sector'
        managed = False  # Table already exists in warehouse
        ordering = ['sector_name']

    def __str__(self):
        return self.sector_name


class Company(models.Model):
    """Dimension: Company master"""
    symbol = models.CharField(max_length=20, primary_key=True)
    company_name = models.CharField(max_length=255, null=True)
    identity_status = models.CharField(max_length=40)
    source = models.CharField(max_length=100)
    is_active = models.BooleanField(null=True)
    sector = models.ForeignKey(
        Sector, 
        on_delete=models.PROTECT, 
        db_column='sector',
        to_field='sector_name', null=True
    )
    sub_sector = models.CharField(max_length=100, blank=True, null=True)
    company_logo = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    nse_url = models.URLField(blank=True, null=True)
    bse_url = models.URLField(blank=True, null=True)
    face_value = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    book_value = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    about_company = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'dim_company'
        managed = False
        ordering = ['company_name']
        verbose_name_plural = 'Companies'

    def __str__(self):
        return f"{self.symbol} - {self.company_name}"
