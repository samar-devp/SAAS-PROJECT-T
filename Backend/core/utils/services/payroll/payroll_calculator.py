"""
Comprehensive Indian Payroll Calculation Service
Handles all statutory calculations: PF, ESI, TDS, Professional Tax, etc.
Enhanced with advanced attendance, leave, proration, and custom deductions/earnings
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from django.utils import timezone
from django.db.models import Q, Sum
from .models import (
    PayrollSettings, PayrollRecord, EmployeeSalaryStructure,
    EmployeeSalaryComponent, SalaryComponent, StructureComponent,
    ProfessionalTaxSlab, TDSSlab, EmployeeAdvance
)
from AuthN.models import BaseUserModel, UserProfile
from .attendance_calculation_service import AttendanceCalculationService


class PayrollCalculator:
    """Main payroll calculation service with advanced features"""
    
    def __init__(self, employee, month, year, admin=None, organization=None):
        self.employee = employee
        self.month = month
        self.year = year
        self.admin = admin
        self.organization = organization
        self.settings = None
        self.attendance_data = None
        self.earnings = {}
        self.deductions = {}
        self.user_profile = None
        
        # Load settings
        self._load_settings()
        # Load employee profile
        self._load_employee_profile()
        # Load attendance using advanced service
        self._load_attendance()
    
    def _load_settings(self):
        """Load payroll settings"""
        if self.organization:
            self.settings = PayrollSettings.objects.filter(
                organization=self.organization,
                admin=self.admin
            ).first()
            if not self.settings:
                self.settings = PayrollSettings.objects.filter(
                    organization=self.organization
                ).first()
    
    def _load_employee_profile(self):
        """Load employee profile"""
        try:
            self.user_profile = self.employee.own_user_profile
        except UserProfile.DoesNotExist:
            self.user_profile = None
    
    def _load_attendance(self):
        """Load attendance data using advanced calculation service"""
        try:
            attendance_service = AttendanceCalculationService(
                self.employee, self.month, self.year, 
                self.organization, self.admin
            )
            detailed_attendance = attendance_service.calculate_detailed_attendance()
            
            # Map to expected format
            self.attendance_data = {
                'total_days': detailed_attendance['total_calendar_days'],
                'working_days': detailed_attendance['working_days'],
                'present_days': detailed_attendance['present_days'],
                'absent_days': detailed_attendance['absent_days'],
                'leave_days': float(detailed_attendance['leave_days']),
                'lop_days': float(detailed_attendance['lop_days']),
                'half_day_leaves': float(detailed_attendance['half_day_leaves']),
                'week_off_days': detailed_attendance['week_off_days'],
                'holiday_days': detailed_attendance['holiday_days'],
                'sandwich_absent_days': detailed_attendance['sandwich_absent_days'],
                'payable_days': float(detailed_attendance['payable_days']),
                'late_days': detailed_attendance['late_days'],
                'early_exit_days': detailed_attendance['early_exit_days'],
                'total_late_minutes': detailed_attendance['total_late_minutes'],
                'total_early_exit_minutes': detailed_attendance['total_early_exit_minutes'],
                'overtime_hours': float(detailed_attendance['overtime_hours']),
                'day_wise_data': detailed_attendance['day_wise_data']
            }
        except Exception as e:
            # Default values if attendance calculation fails
            working_days = self.settings.working_days_per_month if self.settings else 26
            self.attendance_data = {
                'total_days': 0,
                'working_days': working_days,
                'present_days': 0,
                'absent_days': 0,
                'leave_days': 0.0,
                'lop_days': 0.0,
                'half_day_leaves': 0.0,
                'week_off_days': 0,
                'holiday_days': 0,
                'sandwich_absent_days': 0,
                'payable_days': Decimal('0.00'),
                'late_days': 0,
                'early_exit_days': 0,
                'total_late_minutes': 0,
                'total_early_exit_minutes': 0,
                'overtime_hours': Decimal('0.00'),
                'day_wise_data': []
            }
    
    def calculate_payroll(self):
        """Main method to calculate complete payroll with all enhanced features"""
        # Get employee salary structure
        salary_structure = self._get_employee_salary_structure()
        
        if not salary_structure:
            raise ValueError("No salary structure assigned to employee")
        
        # Calculate earnings
        self._calculate_earnings(salary_structure)
        
        # Calculate deductions
        self._calculate_deductions()
        
        # Calculate net salary
        gross_salary = sum([e['amount'] for e in self.earnings.values()])
        total_deductions = sum([d['amount'] for d in self.deductions.values()])
        net_salary = gross_salary - total_deductions
        
        # Calculate Gratuity (for reference, not deducted)
        basic_salary = self.earnings.get('BASIC', {}).get('amount', Decimal('0.00'))
        payable_days = Decimal(str(self.attendance_data.get('payable_days', 0)))
        working_days = Decimal(str(self.attendance_data.get('working_days', 26)))
        gratuity_amount = self._calculate_gratuity(basic_salary, payable_days, working_days)
        
        return {
            'earnings': self.earnings,
            'deductions': self.deductions,
            'gross_salary': gross_salary,
            'total_deductions': total_deductions,
            'net_salary': net_salary,
            'attendance_data': self.attendance_data,
            'gratuity_amount': float(gratuity_amount),
            'calculation_summary': {
                'payable_days': float(payable_days),
                'working_days': int(working_days),
                'proration_factor': float(payable_days / working_days) if working_days > 0 else 0.0,
                'basic_salary': float(basic_salary),
                'gross_salary': float(gross_salary),
                'net_salary': float(net_salary)
            }
        }
    
    def _get_employee_salary_structure(self):
        """Get active salary structure for employee"""
        payroll_date = date(self.year, self.month, 1)
        
        structure_assignment = EmployeeSalaryStructure.objects.filter(
            employee=self.employee,
            effective_from__lte=payroll_date,
            is_active=True
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=payroll_date)
        ).order_by('-effective_from').first()
        
        return structure_assignment.structure if structure_assignment else None
    
    def _calculate_earnings(self, salary_structure):
        """Calculate all earnings components with advanced proration"""
        # Get structure components
        structure_components = StructureComponent.objects.filter(
            structure=salary_structure,
            component__component_type='earning',
            is_active=True
        ).select_related('component').order_by('component__priority')
        
        # Get employee overrides
        payroll_date = date(self.year, self.month, 1)
        employee_overrides = EmployeeSalaryComponent.objects.filter(
            employee=self.employee,
            component__component_type='earning',
            effective_from__lte=payroll_date,
            is_active=True
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=payroll_date)
        ).select_related('component')
        
        override_dict = {override.component.id: override.amount for override in employee_overrides}
        
        # Calculate basic salary first (needed for percentage calculations)
        basic_salary = Decimal('0.00')
        for comp in structure_components:
            if comp.component.code.upper() == 'BASIC':
                basic_salary = override_dict.get(comp.component.id, comp.amount)
                break
        
        # Get payable days for proration
        payable_days = Decimal(str(self.attendance_data.get('payable_days', 0)))
        working_days = Decimal(str(self.attendance_data.get('working_days', 26)))
        
        # Calculate proration factor
        if working_days > 0:
            proration_factor = payable_days / working_days
        else:
            proration_factor = Decimal('1.00')
        
        # Calculate all earnings with component-wise proration
        for comp in structure_components:
            component = comp.component
            amount = override_dict.get(component.id, comp.amount)
            
            # Apply calculation type
            if component.calculation_type == 'percentage':
                amount = (basic_salary * component.calculation_value) / 100
            elif component.calculation_type == 'percentage_gross':
                # Will be calculated after gross is known (second pass)
                continue
            
            # Apply proration based on component settings
            # Basic is usually not prorated, others are prorated based on payable days
            if component.code.upper() != 'BASIC':
                # Check if component should be prorated
                # Most components are prorated, but can be configured
                amount = amount * proration_factor
            
            self.earnings[component.code] = {
                'name': component.name,
                'amount': amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                'is_prorated': component.code.upper() != 'BASIC'
            }
        
        # Second pass for percentage_gross calculations (after gross is known)
        gross_before_percentage = sum([e['amount'] for e in self.earnings.values()])
        for comp in structure_components:
            component = comp.component
            if component.calculation_type == 'percentage_gross':
                amount = (gross_before_percentage * component.calculation_value) / 100
                if component.code.upper() != 'BASIC':
                    amount = amount * proration_factor
                self.earnings[component.code] = {
                    'name': component.name,
                    'amount': amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                    'is_prorated': component.code.upper() != 'BASIC'
                }
        
        # Calculate overtime
        if self.settings and self.settings.overtime_enabled:
            overtime_hours = Decimal(str(self.attendance_data.get('overtime_hours', 0)))
            if overtime_hours > 0 and working_days > 0:
                hourly_rate = basic_salary / (working_days * Decimal('8'))
                overtime_amount = hourly_rate * Decimal('1.5') * overtime_hours
                self.earnings['OVERTIME'] = {
                    'name': 'Overtime',
                    'amount': overtime_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                    'is_prorated': False
                }
        
        # Calculate variable earnings (bonus, leave encashment, arrears, awards)
        self._calculate_variable_earnings(basic_salary, payable_days, working_days)
    
    def _calculate_variable_earnings(self, basic_salary, payable_days, working_days):
        """Calculate variable earnings like bonus, leave encashment, arrears, awards"""
        # Leave Encashment
        if self.settings and self.settings.leave_encashment_enabled:
            # This would typically come from leave encashment records
            # For now, placeholder - can be enhanced
            pass
        
        # Bonus (Diwali, Annual, etc.)
        if self.settings and self.settings.bonus_enabled:
            # Check for bonus components in salary structure
            bonus_components = StructureComponent.objects.filter(
                structure=self._get_employee_salary_structure(),
                component__code__in=['BONUS', 'DIWALI_BONUS', 'ANNUAL_BONUS'],
                is_active=True
            ).select_related('component')
            
            for bonus_comp in bonus_components:
                component = bonus_comp.component
                amount = bonus_comp.amount
                
                # Bonus may or may not be prorated based on policy
                # Typically, bonus is not prorated, but can be configured
                if component.code not in self.earnings:
                    self.earnings[component.code] = {
                        'name': component.name,
                        'amount': amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        'is_prorated': False
                    }
        
        # Arrears (from previous months)
        # This would typically come from arrears records
        # Placeholder for future implementation
        
        # Impact Award / Performance Bonus
        # This would typically come from performance records
        # Placeholder for future implementation
    
    def _calculate_deductions(self):
        """Calculate all deductions including statutory with enhanced features"""
        gross_salary = sum([e['amount'] for e in self.earnings.values()])
        basic_salary = self.earnings.get('BASIC', {}).get('amount', Decimal('0.00'))
        
        # PF Calculation with component selection
        if self.settings and self.settings.pf_enabled:
            # Calculate PF base from selected components
            pf_base = self._calculate_pf_base(basic_salary)
            pf_employee = (pf_base * self.settings.pf_employee_percentage) / 100
            pf_employer = (pf_base * self.settings.pf_employer_percentage) / 100
            
            self.deductions['PF_EMPLOYEE'] = {
                'name': 'Provident Fund (Employee)',
                'amount': pf_employee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            }
            # Employer PF is not deducted from employee, but tracked separately
        
        # ESI Calculation with component selection
        if self.settings and self.settings.esi_enabled:
            # Calculate ESI base from selected components
            esi_base = self._calculate_esi_base(gross_salary)
            if esi_base <= self.settings.esi_max_limit:
                esi_employee = (esi_base * self.settings.esi_employee_percentage) / 100
                esi_employer = (esi_base * self.settings.esi_employer_percentage) / 100
                
                self.deductions['ESI_EMPLOYEE'] = {
                    'name': 'Employee State Insurance (Employee)',
                    'amount': esi_employee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                }
        
        # Professional Tax (enhanced with gender and month-wise calculation)
        if self.settings and self.settings.pt_enabled:
            pt_amount = self._calculate_professional_tax(gross_salary)
            if pt_amount > 0:
                self.deductions['PROFESSIONAL_TAX'] = {
                    'name': 'Professional Tax',
                    'amount': pt_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                }
        
        # TDS Calculation
        if self.settings and self.settings.tds_enabled:
            annual_income = gross_salary * 12  # Simplified
            if annual_income > self.settings.tds_threshold:
                tds_amount = self._calculate_tds(annual_income) / 12
                self.deductions['TDS'] = {
                    'name': 'Tax Deducted at Source',
                    'amount': tds_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                }
        
        # LWF
        if self.settings and self.settings.lwf_enabled:
            self.deductions['LWF'] = {
                'name': 'Labour Welfare Fund',
                'amount': self.settings.lwf_employee_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            }
        
        # Custom Deductions (Late Mark, Penalty, Uniform, Canteen, etc.)
        self._calculate_custom_deductions(basic_salary, gross_salary)
        
        # Advance/Loan Deductions
        self._calculate_advance_deductions()
        
        # Other deductions from structure
        self._calculate_other_deductions()
    
    def _calculate_pf_base(self, basic_salary):
        """Calculate PF base from selected components"""
        # Default: PF is calculated on Basic only, up to max limit
        pf_base = min(basic_salary, self.settings.pf_max_limit)
        
        # Check if other components are marked for PF calculation
        salary_structure = self._get_employee_salary_structure()
        if salary_structure:
            structure_components = StructureComponent.objects.filter(
                structure=salary_structure,
                component__is_pf_applicable=True,
                component__component_type='earning',
                is_active=True
            ).select_related('component')
            
            # Sum all PF applicable components
            pf_applicable_amount = Decimal('0.00')
            for comp in structure_components:
                component = comp.component
                amount = comp.amount
                
                # Get from earnings if already calculated
                if component.code in self.earnings:
                    amount = self.earnings[component.code]['amount']
                
                pf_applicable_amount += amount
            
            # Apply max limit
            pf_base = min(pf_applicable_amount, self.settings.pf_max_limit)
        
        return pf_base
    
    def _calculate_esi_base(self, gross_salary):
        """Calculate ESI base from selected components"""
        # Default: ESI is calculated on Gross Salary
        esi_base = gross_salary
        
        # Check if specific components are marked for ESI calculation
        salary_structure = self._get_employee_salary_structure()
        if salary_structure:
            structure_components = StructureComponent.objects.filter(
                structure=salary_structure,
                component__is_esi_applicable=True,
                component__component_type='earning',
                is_active=True
            ).select_related('component')
            
            if structure_components.exists():
                # Sum all ESI applicable components
                esi_applicable_amount = Decimal('0.00')
                for comp in structure_components:
                    component = comp.component
                    amount = comp.amount
                    
                    # Get from earnings if already calculated
                    if component.code in self.earnings:
                        amount = self.earnings[component.code]['amount']
                    
                    esi_applicable_amount += amount
                
                esi_base = esi_applicable_amount
        
        return esi_base
    
    def _calculate_custom_deductions(self, basic_salary, gross_salary):
        """Calculate custom deductions like late mark, penalty, uniform, canteen"""
        # Late Mark Deduction
        late_days = self.attendance_data.get('late_days', 0)
        if late_days > 0 and self.settings:
            # Check if late mark deduction is enabled in settings
            # This would typically come from payroll settings or policy
            # For now, placeholder - can be enhanced
            pass
        
        # Penalty Deduction
        # This would typically come from penalty records
        # Placeholder for future implementation
        
        # Uniform Deduction
        # This would typically come from uniform issue records
        # Placeholder for future implementation
        
        # Canteen Deduction
        # This would typically come from canteen usage records
        # Placeholder for future implementation
    
    def _calculate_professional_tax(self, gross_salary):
        """Calculate professional tax based on state, salary, gender, and month"""
        if not self.settings or not self.settings.pt_state:
            return Decimal('0.00')
        
        # Get employee gender for gender-based PT calculation
        gender = None
        if self.user_profile:
            gender = self.user_profile.gender
        
        # Get month for month-wise PT calculation (some states have different rates)
        # For annual PT, divide by 12; for monthly PT, use as is
        # This depends on state policy - Maharashtra has monthly PT
        
        # Query PT slab
        slab_query = ProfessionalTaxSlab.objects.filter(
            state=self.settings.pt_state,
            salary_from__lte=gross_salary,
            is_active=True
        ).filter(
            Q(salary_to__isnull=True) | Q(salary_to__gte=gross_salary)
        )
        
        # Filter by gender if applicable (some states have different rates for women)
        # This would require a gender field in ProfessionalTaxSlab model
        # For now, we'll use the general slab
        
        slab = slab_query.order_by('-salary_from').first()
        
        if slab:
            pt_amount = slab.tax_amount
            
            # Some states have reduced PT for women (e.g., Maharashtra)
            # This would typically be configured in the slab or settings
            # For now, placeholder - can be enhanced based on state rules
            
            return pt_amount
        
        return Decimal('0.00')
    
    def _calculate_gratuity(self, basic_salary, payable_days, working_days):
        """Calculate Gratuity (typically for full & final settlement)"""
        if not self.settings or not self.settings.gratuity_enabled:
            return Decimal('0.00')
        
        # Gratuity is typically calculated as: (Basic Ã— 15/26) Ã— Years of Service
        # For monthly payroll, it's usually not deducted but tracked separately
        # This method is for reference/calculation purposes
        
        # Get years of service
        years_of_service = Decimal('0.00')
        if self.user_profile and self.user_profile.date_of_joining:
            joining_date = self.user_profile.date_of_joining
            payroll_date = date(self.year, self.month, 1)
            years_of_service = Decimal(str((payroll_date - joining_date).days)) / Decimal('365.25')
        
        # Gratuity formula: (Basic Ã— 15/26) Ã— Years of Service
        # 15/26 = 0.5769 (approximately)
        gratuity_per_year = (basic_salary * Decimal('15')) / Decimal('26')
        gratuity_amount = gratuity_per_year * years_of_service
        
        # For monthly payroll, gratuity is not deducted but can be tracked
        # This would typically be part of full & final settlement
        
        return gratuity_amount
    
    def _calculate_tds(self, annual_income):
        """Calculate TDS based on income tax slabs with age-based calculation"""
        # Get current financial year
        current_date = date.today()
        if current_date.month >= 4:
            financial_year = f"{current_date.year}-{str(current_date.year + 1)[-2:]}"
        else:
            financial_year = f"{current_date.year - 1}-{str(current_date.year)[-2:]}"
        
        # Get age group based on employee's date of birth
        age_group = 'general'
        if self.user_profile and self.user_profile.date_of_birth:
            dob = self.user_profile.date_of_birth
            age = (current_date - dob).days // 365
            
            if age >= 80:
                age_group = 'super_senior'
            elif age >= 60:
                age_group = 'senior'
            else:
                age_group = 'general'
        
        slabs = TDSSlab.objects.filter(
            financial_year=financial_year,
            age_group=age_group,
            income_from__lte=annual_income,
            is_active=True
        ).order_by('income_from')
        
        total_tax = Decimal('0.00')
        remaining_income = annual_income
        
        for slab in slabs:
            if remaining_income <= 0:
                break
            
            # Calculate taxable income for this slab
            slab_max = slab.income_to if slab.income_to else annual_income
            slab_min = slab.income_from
            
            if remaining_income <= slab_min:
                break
            
            slab_income = min(remaining_income, slab_max) - slab_min + 1
            if slab_income <= 0:
                continue
            
            tax_on_slab = (slab_income * slab.tax_rate) / 100
            total_tax += tax_on_slab
            remaining_income -= slab_income
        
        return total_tax
    
    def _calculate_advance_deductions(self):
        """Calculate advance and loan deductions"""
        payroll_date = date(self.year, self.month, 1)
        
        advances = EmployeeAdvance.objects.filter(
            employee=self.employee,
            status='approved',
            remaining_amount__gt=0
        )
        
        total_advance_deduction = Decimal('0.00')
        total_loan_deduction = Decimal('0.00')
        
        for advance in advances:
            if advance.advance_type == 'advance':
                # Deduct full remaining or installment
                deduction = min(advance.remaining_amount, advance.installment_amount or advance.remaining_amount)
                total_advance_deduction += deduction
            elif advance.advance_type == 'loan':
                deduction = advance.installment_amount or advance.remaining_amount
                total_loan_deduction += deduction
        
        if total_advance_deduction > 0:
            self.deductions['ADVANCE'] = {
                'name': 'Advance Deduction',
                'amount': total_advance_deduction.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            }
        
        if total_loan_deduction > 0:
            self.deductions['LOAN'] = {
                'name': 'Loan Deduction',
                'amount': total_loan_deduction.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            }
    
    def _calculate_other_deductions(self):
        """Calculate other deductions from salary structure"""
        salary_structure = self._get_employee_salary_structure()
        if not salary_structure:
            return
        
        structure_components = StructureComponent.objects.filter(
            structure=salary_structure,
            component__component_type='deduction',
            is_active=True
        ).select_related('component')
        
        payroll_date = date(self.year, self.month, 1)
        employee_overrides = EmployeeSalaryComponent.objects.filter(
            employee=self.employee,
            component__component_type='deduction',
            effective_from__lte=payroll_date,
            is_active=True
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=payroll_date)
        ).select_related('component')
        
        override_dict = {override.component.id: override.amount for override in employee_overrides}
        basic_salary = self.earnings.get('BASIC', {}).get('amount', Decimal('0.00'))
        
        for comp in structure_components:
            component = comp.component
            # Skip statutory deductions (already calculated)
            if component.code in ['PF_EMPLOYEE', 'ESI_EMPLOYEE', 'PROFESSIONAL_TAX', 'TDS', 'LWF']:
                continue
            
            amount = override_dict.get(component.id, comp.amount)
            
            if component.calculation_type == 'percentage':
                amount = (basic_salary * component.calculation_value) / 100
            
            self.deductions[component.code] = {
                'name': component.name,
                'amount': amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            }

