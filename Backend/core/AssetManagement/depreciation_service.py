"""
Asset Depreciation Service
Implements standard depreciation methods used by companies
"""

from decimal import Decimal
from datetime import date, datetime, timedelta
from django.db import transaction
from django.utils import timezone
import logging
import calendar

logger = logging.getLogger(__name__)


class DepreciationCalculator:
    """
    Standard Depreciation Calculation Methods
    Supports: Straight-Line, Written Down Value (WDV), Units of Production
    """
    
    @staticmethod
    def calculate_straight_line(purchase_price, depreciation_rate, purchase_date, depreciation_date, useful_life_years=None):
        """
        Straight-Line Depreciation Method
        Most commonly used method - equal depreciation each year
        
        Formula: (Cost - Salvage Value) / Useful Life
        Monthly: Annual Depreciation / 12
        """
        if not purchase_price or purchase_price <= 0:
            return Decimal('0.00'), Decimal('0.00'), purchase_price or Decimal('0.00')
        
        # Calculate months between purchase and depreciation date
        months_diff = (depreciation_date.year - purchase_date.year) * 12 + (depreciation_date.month - purchase_date.month)
        
        if months_diff < 0:
            return Decimal('0.00'), Decimal('0.00'), purchase_price
        
        # If useful_life_years is provided, use it; otherwise use depreciation_rate
        if useful_life_years:
            annual_depreciation = purchase_price / Decimal(str(useful_life_years))
        else:
            # depreciation_rate is annual percentage
            annual_depreciation = (purchase_price * Decimal(str(depreciation_rate))) / Decimal('100')
        
        # Monthly depreciation
        monthly_depreciation = annual_depreciation / Decimal('12')
        
        # Calculate depreciation for the period
        depreciation_amount = monthly_depreciation * Decimal(str(months_diff))
        
        # Accumulated depreciation (total depreciation till date)
        accumulated_depreciation = depreciation_amount
        
        # Book value (current value)
        book_value = purchase_price - accumulated_depreciation
        
        # Ensure book value doesn't go negative
        if book_value < 0:
            book_value = Decimal('0.00')
            accumulated_depreciation = purchase_price
        
        return depreciation_amount, accumulated_depreciation, book_value
    
    @staticmethod
    def calculate_wdv(purchase_price, depreciation_rate, purchase_date, depreciation_date, accumulated_depreciation=Decimal('0.00')):
        """
        Written Down Value (WDV) / Declining Balance Method
        Common in India for tax purposes - higher depreciation in early years
        
        Formula: (Opening Book Value × Depreciation Rate) / 100
        Monthly: Annual Depreciation / 12
        """
        if not purchase_price or purchase_price <= 0:
            return Decimal('0.00'), Decimal('0.00'), purchase_price or Decimal('0.00')
        
        # Calculate months between purchase and depreciation date
        months_diff = (depreciation_date.year - purchase_date.year) * 12 + (depreciation_date.month - purchase_date.month)
        
        if months_diff < 0:
            return Decimal('0.00'), accumulated_depreciation, purchase_price - accumulated_depreciation
        
        # Opening book value
        opening_book_value = purchase_price - accumulated_depreciation
        
        if opening_book_value <= 0:
            return Decimal('0.00'), accumulated_depreciation, Decimal('0.00')
        
        # Annual depreciation on opening book value
        annual_depreciation = (opening_book_value * Decimal(str(depreciation_rate))) / Decimal('100')
        
        # Monthly depreciation
        monthly_depreciation = annual_depreciation / Decimal('12')
        
        # For this month's depreciation
        depreciation_amount = monthly_depreciation
        
        # Accumulated depreciation
        accumulated_depreciation = accumulated_depreciation + depreciation_amount
        
        # Book value
        book_value = purchase_price - accumulated_depreciation
        
        # Ensure book value doesn't go negative
        if book_value < 0:
            book_value = Decimal('0.00')
            accumulated_depreciation = purchase_price
        
        return depreciation_amount, accumulated_depreciation, book_value
    
    @staticmethod
    def calculate_units_of_production(purchase_price, total_units, units_used, purchase_date, depreciation_date):
        """
        Units of Production Method
        Depreciation based on actual usage
        
        Formula: (Cost - Salvage Value) × (Units Used / Total Units)
        """
        if not purchase_price or purchase_price <= 0:
            return Decimal('0.00'), Decimal('0.00'), purchase_price or Decimal('0.00')
        
        if not total_units or total_units <= 0:
            return Decimal('0.00'), Decimal('0.00'), purchase_price
        
        # Depreciation per unit
        depreciation_per_unit = purchase_price / Decimal(str(total_units))
        
        # Depreciation for units used
        depreciation_amount = depreciation_per_unit * Decimal(str(units_used))
        
        # Accumulated depreciation
        accumulated_depreciation = depreciation_amount
        
        # Book value
        book_value = purchase_price - accumulated_depreciation
        
        if book_value < 0:
            book_value = Decimal('0.00')
            accumulated_depreciation = purchase_price
        
        return depreciation_amount, accumulated_depreciation, book_value


class AssetDepreciationService:
    """
    Service to calculate and record asset depreciation
    """
    
    def __init__(self, asset):
        self.asset = asset
    
    def calculate_monthly_depreciation(self, depreciation_date=None, method='straight_line'):
        """
        Calculate monthly depreciation for an asset
        
        Args:
            depreciation_date: Date for which to calculate depreciation (default: current date)
            method: Depreciation method ('straight_line', 'wdv', 'units_of_production')
        
        Returns:
            tuple: (depreciation_amount, accumulated_depreciation, book_value)
        """
        if not depreciation_date:
            depreciation_date = date.today()
        
        if not self.asset.purchase_price or self.asset.purchase_price <= 0:
            logger.warning(f"Asset {self.asset.id} has no purchase price")
            return Decimal('0.00'), Decimal('0.00'), Decimal('0.00')
        
        if not self.asset.purchase_date:
            logger.warning(f"Asset {self.asset.id} has no purchase date")
            return Decimal('0.00'), Decimal('0.00'), self.asset.purchase_price
        
        # Get existing accumulated depreciation
        last_depreciation = self.asset.depreciation_records.order_by('-depreciation_date').first()
        accumulated_depreciation = last_depreciation.accumulated_depreciation if last_depreciation else Decimal('0.00')
        
        # Get depreciation rate
        depreciation_rate = self.asset.depreciation_rate or Decimal('10.00')  # Default 10%
        
        calculator = DepreciationCalculator()
        
        if method == 'straight_line':
            # Calculate useful life from rate (if rate is 10%, useful life is 10 years)
            useful_life_years = Decimal('100') / depreciation_rate if depreciation_rate > 0 else Decimal('10')
            depreciation_amount, accumulated_depreciation, book_value = calculator.calculate_straight_line(
                self.asset.purchase_price,
                depreciation_rate,
                self.asset.purchase_date,
                depreciation_date,
                useful_life_years
            )
        
        elif method == 'wdv':
            depreciation_amount, accumulated_depreciation, book_value = calculator.calculate_wdv(
                self.asset.purchase_price,
                depreciation_rate,
                self.asset.purchase_date,
                depreciation_date,
                accumulated_depreciation
            )
        
        elif method == 'units_of_production':
            # This requires additional fields in Asset model
            total_units = self.asset.specifications.get('total_units', 0) or 0
            units_used = self.asset.specifications.get('units_used', 0) or 0
            depreciation_amount, accumulated_depreciation, book_value = calculator.calculate_units_of_production(
                self.asset.purchase_price,
                total_units,
                units_used,
                self.asset.purchase_date,
                depreciation_date
            )
        
        else:
            # Default to straight line
            useful_life_years = Decimal('100') / depreciation_rate if depreciation_rate > 0 else Decimal('10')
            depreciation_amount, accumulated_depreciation, book_value = calculator.calculate_straight_line(
                self.asset.purchase_price,
                depreciation_rate,
                self.asset.purchase_date,
                depreciation_date,
                useful_life_years
            )
        
        return depreciation_amount, accumulated_depreciation, book_value
    
    @transaction.atomic
    def record_monthly_depreciation(self, depreciation_date=None, method='straight_line'):
        """
        Calculate and record monthly depreciation
        
        Returns:
            AssetDepreciation: Created depreciation record
        """
        from .models import AssetDepreciation
        
        if not depreciation_date:
            depreciation_date = date.today()
        
        # Check if depreciation already recorded for this month
        existing = AssetDepreciation.objects.filter(
            asset=self.asset,
            depreciation_date__year=depreciation_date.year,
            depreciation_date__month=depreciation_date.month
        ).first()
        
        if existing:
            logger.info(f"Depreciation already recorded for {self.asset.id} for {depreciation_date}")
            return existing
        
        # Calculate depreciation
        depreciation_amount, accumulated_depreciation, book_value = self.calculate_monthly_depreciation(
            depreciation_date, method
        )
        
        # Create depreciation record
        depreciation_record = AssetDepreciation.objects.create(
            asset=self.asset,
            depreciation_date=depreciation_date,
            depreciation_amount=depreciation_amount,
            accumulated_depreciation=accumulated_depreciation,
            book_value=book_value
        )
        
        # Update asset current value
        self.asset.current_value = book_value
        self.asset.save(update_fields=['current_value'])
        
        logger.info(f"Depreciation recorded for asset {self.asset.id}: Amount={depreciation_amount}, Book Value={book_value}")
        
        return depreciation_record
    
    @transaction.atomic
    def process_all_pending_depreciation(self, end_date=None, method='straight_line'):
        """
        Process all pending monthly depreciation from last recorded date to end_date
        
        Args:
            end_date: End date for depreciation processing (default: current date)
            method: Depreciation method
        
        Returns:
            list: Created depreciation records
        """
        if not end_date:
            end_date = date.today()
        
        if not self.asset.purchase_date:
            logger.warning(f"Asset {self.asset.id} has no purchase date")
            return []
        
        # Get last depreciation date
        last_depreciation = self.asset.depreciation_records.order_by('-depreciation_date').first()
        
        if last_depreciation:
            # Move to next month
            if last_depreciation.depreciation_date.month == 12:
                start_date = date(last_depreciation.depreciation_date.year + 1, 1, 1)
            else:
                start_date = date(last_depreciation.depreciation_date.year, last_depreciation.depreciation_date.month + 1, 1)
        else:
            # Start from purchase date
            start_date = self.asset.purchase_date.replace(day=1)
        
        # Process each month
        records = []
        current_date = start_date
        
        while current_date <= end_date:
            record = self.record_monthly_depreciation(current_date, method)
            if record:
                records.append(record)
            
            # Move to next month
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)
        
        return records

