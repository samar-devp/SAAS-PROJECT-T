# =====================
# 🧾 PAYROLL SYSTEM MODELS
# =====================

from django.db import models
from uuid import uuid4
from AuthN.models import *  # Import your custom BaseUserModel

# --------------------
# 3. Salary Component
# --------------------
class SalaryComponent(models.Model):
    organization = models.ForeignKey(  # 👈 Organization that owns this component
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='salary_components'
    )
    name = models.CharField(max_length=100)  # 👈 Human-readable name (e.g. Basic, HRA)
    code = models.CharField(max_length=50)  # 👈 Unique short code (e.g. BASIC, HRA)
    component_type = models.CharField(  # 👈 Whether it's earning or deduction
        choices=[('earning', 'Earning'), ('deduction', 'Deduction')],
        max_length=20
    )
    is_variable = models.BooleanField(default=False)  # 👈 If amount changes monthly
    is_compliance = models.BooleanField(default=False)  # 👈 For statutory compliance (e.g., PF, ESI)

    class Meta:
        unique_together = ('organization', 'code')  # 👈 Avoid duplicate codes in same org

    def __str__(self):
        return f"{self.code} - {self.name}"


# --------------------
# 4. Salary Structure
# --------------------
class SalaryStructure(models.Model):
    organization = models.ForeignKey(  # 👈 Organization owning this structure
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='salary_structures'
    )
    name = models.CharField(max_length=100)  # 👈 Structure name (e.g. Default Structure)
    description = models.TextField(null=True, blank=True)  # 👈 Optional description
    expected_total = models.DecimalField(  # 👈 Expected gross salary under this structure
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    created_by = models.ForeignKey(  # 👈 Admin who created this structure
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'role': 'admin'},
        related_name='payroll_structures_created'
    )
    is_default = models.BooleanField(default=False)  # 👈 If this is the default structure
    created_at = models.DateTimeField(auto_now_add=True)  # 👈 Creation timestamp


# --------------------
# 5. Structure Component
# --------------------
class StructureComponent(models.Model):
    structure = models.ForeignKey(  # 👈 Link to salary structure
        SalaryStructure, on_delete=models.CASCADE,
        related_name="components"
    )
    component = models.ForeignKey(  # 👈 Link to individual component (e.g. Basic, HRA)
        SalaryComponent, on_delete=models.PROTECT
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # 👈 Component amount

    class Meta:
        unique_together = ('structure', 'component')  # 👈 No duplicates in same structure


# --------------------
# 7. Employee Salary Structure Assignment
# --------------------
class EmployeeSalaryStructure(models.Model):
    employee = models.ForeignKey(  # 👈 Employee (user role)
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='salary_components_assigned'
    )
    structure = models.ForeignKey(  # 👈 Assigned salary structure
        SalaryStructure, on_delete=models.CASCADE
    )
    assigned_on = models.DateField(auto_now_add=True)  # 👈 Date of assignment


# --------------------
# 8. Employee Salary Components (Overrides)
# --------------------
class EmployeeSalaryComponent(models.Model):
    employee = models.OneToOneField(  # 👈 One-to-One relation with user (for custom breakdown)
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='salary_structure_assigned'
    )
    component = models.ForeignKey(  # 👈 Component (e.g. HRA)
        SalaryComponent, on_delete=models.PROTECT
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # 👈 Component value
    effective_from = models.DateField()  # 👈 Start date of this component amount
    effective_to = models.DateField(null=True, blank=True)  # 👈 Optional end date (if temporary)

    class Meta:
        unique_together = ('employee', 'component', 'effective_from')  # 👈 Ensure unique entries per period
