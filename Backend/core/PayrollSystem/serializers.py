"""
Comprehensive Payroll System Serializers
"""

from rest_framework import serializers
from .models import (
    SalaryComponent, SalaryStructure, StructureComponent,
    EmployeeSalaryStructure, EmployeeSalaryComponent,
    EmployeeBankInfo, PayrollSettings, EmployeeAdvance,
    PayrollRecord, PayrollComponentEntry,
    ProfessionalTaxSlab, TDSSlab
)
from AuthN.models import BaseUserModel


class SalaryComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryComponent
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class StructureComponentSerializer(serializers.ModelSerializer):
    component_detail = SalaryComponentSerializer(source='component', read_only=True)
    
    class Meta:
        model = StructureComponent
        fields = '__all__'


class SalaryStructureSerializer(serializers.ModelSerializer):
    components = StructureComponentSerializer(many=True, read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    class Meta:
        model = SalaryStructure
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class EmployeeSalaryStructureSerializer(serializers.ModelSerializer):
    structure_detail = SalaryStructureSerializer(source='structure', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_name = serializers.CharField(source='employee.own_user_profile.user_name', read_only=True)
    
    class Meta:
        model = EmployeeSalaryStructure
        fields = '__all__'
        read_only_fields = ['assigned_on']


class EmployeeSalaryComponentSerializer(serializers.ModelSerializer):
    component_detail = SalaryComponentSerializer(source='component', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    
    class Meta:
        model = EmployeeSalaryComponent
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class EmployeeBankInfoSerializer(serializers.ModelSerializer):
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_name = serializers.CharField(source='employee.own_user_profile.user_name', read_only=True)
    
    class Meta:
        model = EmployeeBankInfo
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class PayrollSettingsSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    admin_email = serializers.EmailField(source='admin.email', read_only=True, allow_null=True)
    
    class Meta:
        model = PayrollSettings
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class EmployeeAdvanceSerializer(serializers.ModelSerializer):
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_name = serializers.CharField(source='employee.own_user_profile.user_name', read_only=True)
    admin_email = serializers.EmailField(source='admin.email', read_only=True)
    
    class Meta:
        model = EmployeeAdvance
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class PayrollComponentEntrySerializer(serializers.ModelSerializer):
    component_detail = SalaryComponentSerializer(source='component', read_only=True)
    
    class Meta:
        model = PayrollComponentEntry
        fields = '__all__'
        read_only_fields = ['created_at']


class PayrollRecordSerializer(serializers.ModelSerializer):
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_name = serializers.CharField(source='employee.own_user_profile.user_name', read_only=True)
    admin_email = serializers.EmailField(source='admin.email', read_only=True)
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    component_entries = PayrollComponentEntrySerializer(many=True, read_only=True)
    
    class Meta:
        model = PayrollRecord
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProfessionalTaxSlabSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalTaxSlab
        fields = '__all__'
        read_only_fields = ['created_at']


class TDSSlabSerializer(serializers.ModelSerializer):
    class Meta:
        model = TDSSlab
        fields = '__all__'
        read_only_fields = ['created_at']

