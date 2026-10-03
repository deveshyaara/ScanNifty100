"""
Financial statement fact tables.
"""
from django.db import models
from apps.web.apps.companies.models import Company
from apps.web.apps.core.models import Year


class ProfitLoss(models.Model):
    """Fact: Profit & Loss statement (1 row per company per year)"""
    id = models.BigAutoField(primary_key=True)
    symbol = models.ForeignKey(Company, on_delete=models.CASCADE, db_column='symbol')
    year = models.ForeignKey(Year, on_delete=models.CASCADE, db_column='year_id')
    
    sales = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    expenses = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    operating_profit = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    opm_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    other_income = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    interest = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    depreciation = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    profit_before_tax = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    tax_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    net_profit = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    eps = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    dividend_payout_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    
    # Computed metrics
    net_profit_margin_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    expense_ratio_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    interest_coverage = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    class Meta:
        db_table = 'fact_profit_loss'
        managed = False
        unique_together = [['symbol', 'year']]
        ordering = ['symbol', '-year__sort_order']

    def __str__(self):
        return f"{self.symbol_id} | {self.year.year_label} | ₹{self.sales}Cr"


class BalanceSheet(models.Model):
    """Fact: Balance Sheet (1 row per company per year)"""
    id = models.BigAutoField(primary_key=True)
    symbol = models.ForeignKey(Company, on_delete=models.CASCADE, db_column='symbol')
    year = models.ForeignKey(Year, on_delete=models.CASCADE, db_column='year_id')
    
    equity_capital = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    reserves = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    borrowings = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    other_liabilities = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    total_liabilities = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    fixed_assets = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    cwip = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    investments = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    other_assets = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    total_assets = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    
    # Computed metrics
    debt_to_equity = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    equity_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    book_value_per_share = models.DecimalField(max_digits=12, decimal_places=2, null=True)

    class Meta:
        db_table = 'fact_balance_sheet'
        managed = False
        unique_together = [['symbol', 'year']]
        ordering = ['symbol', '-year__sort_order']

    def __str__(self):
        return f"{self.symbol_id} | {self.year.year_label}"


class CashFlow(models.Model):
    """Fact: Cash Flow Statement"""
    id = models.BigAutoField(primary_key=True)
    symbol = models.ForeignKey(Company, on_delete=models.CASCADE, db_column='symbol')
    year = models.ForeignKey(Year, on_delete=models.CASCADE, db_column='year_id')
    
    operating_activity = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    investing_activity = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    financing_activity = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    net_cash_flow = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    
    # Computed metrics
    free_cash_flow = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    cash_conversion_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True)

    class Meta:
        db_table = 'fact_cash_flow'
        managed = False
        unique_together = [['symbol', 'year']]
        ordering = ['symbol', '-year__sort_order']

    def __str__(self):
        return f"{self.symbol_id} | {self.year.year_label}"
