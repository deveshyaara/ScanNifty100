"""
Management command to load sample warehouse data from CSV files into SQLite.
"""
import os
import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from apps.web.apps.companies.models import Company, Sector
from apps.web.apps.core.models import Year


class Command(BaseCommand):
    help = 'Load warehouse data from CSV files into SQLite database'

    def handle(self, *args, **options):
        self.stdout.write("Starting data import...")
        
        # Get data directory
        data_dir = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent / 'data' / 'clean'
        
        try:
            # Load sectors
            self.load_sectors(data_dir)
            
            # Load companies
            self.load_companies(data_dir)
            
            # Load years
            self.load_years()
            
            self.stdout.write(self.style.SUCCESS('✓ Data import completed successfully!'))
        except Exception as e:
            raise CommandError(f'Error loading data: {str(e)}')

    def load_sectors(self, data_dir):
        """Load sectors from companies.csv"""
        companies_file = data_dir / 'companies.csv'
        
        if not companies_file.exists():
            self.stdout.write(self.style.WARNING(f'Companies file not found: {companies_file}'))
            return
        
        sectors_loaded = set()
        
        with open(companies_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sector_name = row.get('sector', '').strip()
                
                if sector_name and sector_name not in sectors_loaded:
                    # Create sector_code from sector_name (e.g., "Industrials" -> "IND")
                    sector_code = ''.join([c for c in sector_name if c.isupper()]) or sector_name[:3].upper()
                    
                    Sector.objects.get_or_create(
                        sector_code=sector_code,
                        defaults={'sector_name': sector_name, 'description': ''}
                    )
                    sectors_loaded.add(sector_name)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Loaded {len(sectors_loaded)} sectors'))

    def load_companies(self, data_dir):
        """Load companies from companies.csv"""
        companies_file = data_dir / 'companies.csv'
        
        if not companies_file.exists():
            self.stdout.write(self.style.WARNING(f'Companies file not found: {companies_file}'))
            return
        
        companies_count = 0
        
        with open(companies_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                symbol = row.get('company', '').strip()
                company_name = row.get('company_name', '').strip()
                sector_name = row.get('sector', '').strip()
                
                if not symbol or not company_name:
                    continue
                
                # Get sector
                sector = None
                if sector_name:
                    # Try to find sector by name first
                    sector = Sector.objects.filter(sector_name=sector_name).first()
                    if not sector:
                        # Create it if it doesn't exist
                        sector_code = ''.join([c for c in sector_name if c.isupper()]) or sector_name[:3].upper()
                        sector, _ = Sector.objects.get_or_create(
                            sector_code=sector_code,
                            defaults={'sector_name': sector_name, 'description': ''}
                        )
                
                # Create or update company
                company, created = Company.objects.get_or_create(
                    symbol=symbol,
                    defaults={
                        'company_name': company_name,
                        'sector': sector,
                        'sub_sector': row.get('sub_sector', '').strip() or None,
                        'face_value': float(row.get('face_value', '1') or '1'),
                        'book_value': float(row.get('book_value', '0') or '0') or None,
                        'about_company': row.get('about_company', '').strip() or None,
                        'company_logo': row.get('company_logo', '').strip() or None,
                        'website': row.get('website', '').strip() or None,
                        'nse_url': row.get('nse_profile', '').strip() or None,
                    }
                )
                if created:
                    companies_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Loaded {companies_count} companies'))

    def load_years(self):
        """Load sample years for time-series data"""
        year_data = [
            {'year_label': 'TTM', 'fiscal_year': 2025, 'quarter': 4, 'is_ttm': True, 'is_half_year': False, 'sort_order': 100},
            {'year_label': 'FY2025', 'fiscal_year': 2025, 'quarter': 4, 'is_ttm': False, 'is_half_year': False, 'sort_order': 99},
            {'year_label': 'FY2024', 'fiscal_year': 2024, 'quarter': 4, 'is_ttm': False, 'is_half_year': False, 'sort_order': 98},
            {'year_label': 'FY2023', 'fiscal_year': 2023, 'quarter': 4, 'is_ttm': False, 'is_half_year': False, 'sort_order': 97},
            {'year_label': 'FY2022', 'fiscal_year': 2022, 'quarter': 4, 'is_ttm': False, 'is_half_year': False, 'sort_order': 96},
            {'year_label': 'FY2021', 'fiscal_year': 2021, 'quarter': 4, 'is_ttm': False, 'is_half_year': False, 'sort_order': 95},
            {'year_label': 'FY2020', 'fiscal_year': 2020, 'quarter': 4, 'is_ttm': False, 'is_half_year': False, 'sort_order': 94},
        ]
        
        years_loaded = 0
        for year_info in year_data:
            _, created = Year.objects.get_or_create(
                year_label=year_info['year_label'],
                defaults={
                    'fiscal_year': year_info['fiscal_year'],
                    'quarter': year_info['quarter'],
                    'is_ttm': year_info['is_ttm'],
                    'is_half_year': year_info['is_half_year'],
                    'sort_order': year_info['sort_order'],
                }
            )
            if created:
                years_loaded += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Loaded {years_loaded} years'))
