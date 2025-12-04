# =====================
# 🧾 COMPREHENSIVE INDIAN PAYROLL SYSTEM MODELS
# =====================

from django.db import models
from uuid import uuid4
from decimal import Decimal
from AuthN.models import *  # Import your custom BaseUserModel

# --------------------
# 1. Salary Component
# --------------------
class SalaryComponent(models.Model):
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='salary_components'
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    component_type = models.CharField(
        choices=[('earning', 'Earning'), ('deduction', 'Deduction')],
        max_length=20
    )
    is_variable = models.BooleanField(default=False)
    is_compliance = models.BooleanField(default=False)  # For statutory compliance
    calculation_type = models.CharField(
        max_length=50,
        choices=[
            ('fixed', 'Fixed Amount'),
            ('percentage', 'Percentage of Basic'),
            ('percentage_gross', 'Percentage of Gross'),
            ('formula', 'Custom Formula')
        ],
        default='fixed'
    )
    calculation_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Percentage or fixed amount based on calculation_type"
    )
    is_taxable = models.BooleanField(default=True)
    is_pf_applicable = models.BooleanField(default=False, help_text="If PF should be calculated on this component")
    is_esi_applicable = models.BooleanField(default=False, help_text="If ESI should be calculated on this component")
    priority = models.IntegerField(default=0, help_text="Order of calculation")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('organization', 'code')
        ordering = ['priority', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"


# --------------------
# 2. Salary Structure
# --------------------
class SalaryStructure(models.Model):
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='salary_structures'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    expected_total = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    created_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'role': 'admin'},
        related_name='payroll_structures_created'
    )
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"{self.name} - {self.organization.email}"


# --------------------
# 3. Structure Component
# --------------------
class StructureComponent(models.Model):
    structure = models.ForeignKey(
        SalaryStructure, on_delete=models.CASCADE,
        related_name="components"
    )
    component = models.ForeignKey(
        SalaryComponent, on_delete=models.PROTECT
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('structure', 'component')
        ordering = ['component__priority']

    def __str__(self):
        return f"{self.structure.name} - {self.component.name}"


# --------------------
# 4. Employee Salary Structure Assignment
# --------------------
class EmployeeSalaryStructure(models.Model):
    employee = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='salary_structure_assignments'
    )
    structure = models.ForeignKey(
        SalaryStructure, on_delete=models.CASCADE
    )
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'role': 'admin'},
        related_name='assigned_structures'
    )
    assigned_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-effective_from']

    def __str__(self):
        return f"{self.employee.email} - {self.structure.name}"


# --------------------
# 5. Employee Salary Components (Overrides)
# --------------------
class EmployeeSalaryComponent(models.Model):
    employee = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='employee_salary_components'
    )
    component = models.ForeignKey(
        SalaryComponent, on_delete=models.PROTECT
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'component', 'effective_from')
        ordering = ['-effective_from']

    def __str__(self):
        return f"{self.employee.email} - {self.component.name}"


# --------------------
# 6. Employee Bank Information
# --------------------
class EmployeeBankInfo(models.Model):
    employee = models.OneToOneField(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='bank_info'
    )
    bank_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=11)
    branch_name = models.CharField(max_length=200, null=True, blank=True)
    account_holder_name = models.CharField(max_length=200, null=True, blank=True)
    account_type = models.CharField(
        max_length=20,
        choices=[('savings', 'Savings'), ('current', 'Current')],
        default='savings'
    )
    is_primary = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.email} - {self.bank_name}"


# --------------------
# 6.1. Employee Compliance/Statutory Information
# --------------------
class EmployeeComplianceInfo(models.Model):
    """Employee Statutory Compliance Information (PF, ESIC, etc.)"""
    employee = models.OneToOneField(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='compliance_info'
    )
    
    # Provident Fund (PF)
    pf_number = models.CharField(max_length=30, blank=True, null=True, help_text="Employee PF Account Number")
    pf_uan = models.CharField(max_length=12, blank=True, null=True, help_text="Universal Account Number (UAN)")
    pf_previous_employer = models.BooleanField(default=False, help_text="If employee has PF from previous employer")
    
    # Employee State Insurance (ESI/ESIC)
    esic_number = models.CharField(max_length=30, blank=True, null=True, help_text="Employee ESIC/ESI Number")
    esic_ip_number = models.CharField(max_length=30, blank=True, null=True, help_text="ESI IP Number")
    
    # Additional Compliance Info
    pan_number = models.CharField(max_length=10, blank=True, null=True, help_text="Permanent Account Number")
    aadhaar_number = models.CharField(max_length=12, blank=True, null=True, help_text="Aadhaar Number")
    
    # Professional Tax
    professional_tax_state = models.CharField(max_length=100, blank=True, null=True, help_text="State for Professional Tax")
    
    # Other Info
    pf_nominee_name = models.CharField(max_length=255, blank=True, null=True)
    pf_nominee_relation = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Employee Compliance Information"
        verbose_name_plural = "Employee Compliance Information"
    
    def __str__(self):
        return f"{self.employee.email} - Compliance Info"


# --------------------
# 7. Payroll Settings (Organization Level)
# --------------------
class PayrollSettings(models.Model):
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='payroll_settings'
    )
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_payroll_settings',
        null=True, blank=True
    )
    
    # PF Settings
    pf_enabled = models.BooleanField(default=True)
    pf_employee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=12.00)
    pf_employer_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=12.00)
    pf_max_limit = models.DecimalField(max_digits=10, decimal_places=2, default=15000.00)
    pf_number = models.CharField(max_length=50, null=True, blank=True)
    
    # ESI Settings
    esi_enabled = models.BooleanField(default=False)
    esi_employee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.75)
    esi_employer_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=3.25)
    esi_max_limit = models.DecimalField(max_digits=10, decimal_places=2, default=21000.00)
    esi_number = models.CharField(max_length=50, null=True, blank=True)
    
    # Professional Tax Settings
    pt_enabled = models.BooleanField(default=True)
    pt_state = models.CharField(max_length=100, null=True, blank=True)
    pt_number = models.CharField(max_length=50, null=True, blank=True)
    
    # TDS Settings
    tds_enabled = models.BooleanField(default=True)
    tds_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=250000.00)
    pan_number = models.CharField(max_length=10, null=True, blank=True)
    
    # LWF Settings
    lwf_enabled = models.BooleanField(default=False)
    lwf_employee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    lwf_employer_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Gratuity Settings
    gratuity_enabled = models.BooleanField(default=True)
    gratuity_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=4.81)
    
    # Payroll Cycle
    payroll_cycle = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('biweekly', 'Bi-Weekly'),
            ('weekly', 'Weekly')
        ],
        default='monthly'
    )
    payroll_day = models.IntegerField(default=1, help_text="Day of month for payroll processing")
    
    # Other Settings
    working_days_per_month = models.IntegerField(default=26)
    overtime_enabled = models.BooleanField(default=True)
    leave_encashment_enabled = models.BooleanField(default=True)
    bonus_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('organization', 'admin')

    def __str__(self):
        return f"Payroll Settings - {self.organization.email}"


# --------------------
# 8. Advance/Loan
# --------------------
class EmployeeAdvance(models.Model):
    employee = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='advances'
    )
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='approved_advances'
    )
    advance_type = models.CharField(
        max_length=20,
        choices=[('advance', 'Advance'), ('loan', 'Loan')],
        default='advance'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2)
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_installments = models.IntegerField(default=1)
    paid_installments = models.IntegerField(default=0)
    advance_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('completed', 'Completed')
        ],
        default='pending'
    )
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-advance_date']

    def __str__(self):
        return f"{self.employee.email} - {self.advance_type} - {self.amount}"


# --------------------
# 9. Monthly Payroll Record
# --------------------
class PayrollRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    employee = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='payroll_records'
    )
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_payroll_records'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_payroll_records'
    )
    
    # Period
    payroll_month = models.IntegerField()
    payroll_year = models.IntegerField()
    payroll_date = models.DateField()
    
    # Attendance
    total_days = models.IntegerField(default=0)
    present_days = models.IntegerField(default=0)
    absent_days = models.IntegerField(default=0)
    leave_days = models.IntegerField(default=0)
    working_days = models.IntegerField(default=0)
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    
    # Earnings
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    hra = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    special_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    overtime_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    leave_encashment = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    arrears = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    other_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Deductions
    pf_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    pf_employer = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    esi_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    esi_employer = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    professional_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tds = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    lwf_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    lwf_employer = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    advance_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    loan_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Net Salary
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Additional Info
    payslip_generated = models.BooleanField(default=False)
    payslip_pdf_path = models.CharField(max_length=500, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('processed', 'Processed'),
            ('approved', 'Approved'),
            ('paid', 'Paid'),
            ('cancelled', 'Cancelled')
        ],
        default='draft'
    )
    remarks = models.TextField(null=True, blank=True)
    
    # Component breakdown (JSON)
    earnings_breakdown = models.JSONField(default=dict, null=True, blank=True)
    deductions_breakdown = models.JSONField(default=dict, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_payrolls'
    )

    class Meta:
        unique_together = ('employee', 'payroll_month', 'payroll_year')
        ordering = ['-payroll_year', '-payroll_month']
        indexes = [
            models.Index(fields=['employee', 'payroll_year', 'payroll_month']),
            models.Index(fields=['admin', 'payroll_year', 'payroll_month']),
            models.Index(fields=['organization', 'payroll_year', 'payroll_month']),
        ]

    def __str__(self):
        return f"{self.employee.email} - {self.payroll_month}/{self.payroll_year}"


# --------------------
# 10. Payroll Component Entry (Monthly Variable Components)
# --------------------
class PayrollComponentEntry(models.Model):
    payroll = models.ForeignKey(
        PayrollRecord, on_delete=models.CASCADE,
        related_name='component_entries'
    )
    component = models.ForeignKey(
        SalaryComponent, on_delete=models.PROTECT
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_earning = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('payroll', 'component')
        ordering = ['component__priority']

    def __str__(self):
        return f"{self.payroll} - {self.component.name}"


# --------------------
# 11. Professional Tax Slabs (State-wise)
# --------------------
class ProfessionalTaxSlab(models.Model):
    state = models.CharField(max_length=100)
    salary_from = models.DecimalField(max_digits=10, decimal_places=2)
    salary_to = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['state', 'salary_from']

    def __str__(self):
        return f"{self.state} - {self.salary_from} to {self.salary_to or 'Above'}"


# --------------------
# 12. TDS Slabs (Income Tax)
# --------------------
class TDSSlab(models.Model):
    financial_year = models.CharField(max_length=10)  # e.g., "2024-25"
    age_group = models.CharField(
        max_length=20,
        choices=[
            ('general', 'General'),
            ('senior', 'Senior Citizen (60-80)'),
            ('super_senior', 'Super Senior Citizen (80+)')
        ],
        default='general'
    )
    income_from = models.DecimalField(max_digits=12, decimal_places=2)
    income_to = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['financial_year', 'age_group', 'income_from']

    def __str__(self):
        return f"FY {self.financial_year} - {self.age_group} - {self.income_from} to {self.income_to or 'Above'}"
