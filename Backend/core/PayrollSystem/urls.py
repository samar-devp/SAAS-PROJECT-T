"""
Payroll System URLs
All payroll-related endpoints
"""

from django.urls import path
from .views import (
    SalaryStructureCRUD,
    EmployeeAssignStructure,
    EmployeeAssignPay,
    GetAssignStructure,
    AdvanceFormAPIView,
    EmployeeBankInfoAPIView,
    PayrollDownloadInfo,
    PayrollMonthlyReport,
    PayrollComponentsAPIView,
    PayrollSettingsAPIView,
    GeneratePayrollAPIView
)
from .additional_views import (
    UpdatePayrollReportView,
    BIPayrollReportView,
    DownloadAdvanceIncomeTaxSampleExcel,
    UploadAdvanceIncomeTaxExcel,
    DownloadDeductionSampleExcel,
    UploadDeductionExcel,
    DownloadEarningSampleExcel,
    UploadEarningExcel,
    GenerateCustomPayableSheet,
    EmployeePayslipAPI
)
from .additional_utility_views import (
    PayrollDashboardAPIView,
    EmployeePayrollHistoryAPIView,
    PayrollSummaryAPIView,
    EmployeeAdvanceListAPIView,
    EmployeeBankInfoListAPIView
)

urlpatterns = [
    # SALARY-STRUCTURE-CRUD
    path('salary-structure/<str:org_id>', SalaryStructureCRUD.as_view()),
    path('salary-structure/<str:org_id>/<int:id>', SalaryStructureCRUD.as_view()),
    
    # ASSIGNED-STRUCTURE
    path('employee-assigned-structure/<str:org_id>', EmployeeAssignStructure.as_view()),
    
    # ASSIGNED-PAY
    path('employee-assigned-pay/<str:org_id>', EmployeeAssignPay.as_view()),
    
    # UPDATE PAYROLL YEARLY WISE
    path('update_payroll/<str:clnID>/<str:uid>', UpdatePayrollReportView.as_view(), name='update_payroll_report'),
    
    # GET-ASSIGNED-STRUCTURE
    path('get-assign-structure/<str:admin_id>', GetAssignStructure.as_view()),
    path('get-assign-structure/<str:admin_id>/<str:emp_id>', GetAssignStructure.as_view()),
    
    # ADVANCED-FORM
    path('advance-form/<str:admin_id>', AdvanceFormAPIView.as_view(), name='advance-form'),
    path('advance-form/<str:admin_id>/<str:emp_id>', AdvanceFormAPIView.as_view(), name='advance-form'),
    
    # BANK-INFO
    path('employee-bank-info/<str:admin_id>', EmployeeBankInfoAPIView.as_view(), name='employee-bank-info'),
    path('employee-bank-info/<str:admin_id>/<str:emp_id>', EmployeeBankInfoAPIView.as_view(), name='employee-bank-info'),
    
    # DOWNLOAD-INFO
    path('payroll-download-info/<str:org_id>/<int:month>/<int:year>', PayrollDownloadInfo.as_view(), name='payroll-download-info'),
    
    # PAYROLL GENERATION
    path('generate-payroll/<str:org_id>', GeneratePayrollAPIView.as_view(), name='generate-payroll'),
    
    # PAYROLL-MONTHLY-REPORT
    path('payroll-monthly-report/<str:org_id>/<int:month>/<int:year>', PayrollMonthlyReport.as_view(), name='payroll-monthly-report'),
    path('payroll-monthly-report/<str:org_id>/<str:admin_id>/<int:month>/<int:year>', PayrollMonthlyReport.as_view(), name='payroll-monthly-report'),
    
    # BI-PAYROLL-MONTHLY-REPORT
    path('BI-payroll-report/<str:OrgID>/<int:month>/<int:year>', BIPayrollReportView.as_view(), name='BI-payroll-report'),
    path('BI-payroll-report/<str:OrgID>/<str:clnID>/<int:month>/<int:year>', BIPayrollReportView.as_view(), name='BI-payroll-report'),
    path('BI-payroll-report/<str:OrgID>/<str:clnID>/<str:uid>/<int:month>/<int:year>', BIPayrollReportView.as_view(), name='BI-payroll-report'),
    
    # DOWNLOAD-SAMPLE-EXCEL-REPORT
    path('download-sample-excel/', DownloadAdvanceIncomeTaxSampleExcel.as_view(), name='download_sample_excel'),
    
    # UPLOAD-EXCEL-REPORT
    path('upload-advanced-income-tax-excel/<str:clnID>/<int:month>/<int:year>', UploadAdvanceIncomeTaxExcel.as_view(), name='upload_income_tax_excel'),
    
    # PAYROLL-COMPONENTS
    path('payroll-components/<str:org_id>', PayrollComponentsAPIView.as_view(), name='payroll_components_list'),
    
    # PAYROLL-SETTINGS
    path('payroll_settings/<str:org_id>', PayrollSettingsAPIView.as_view(), name='payroll_settings_list'),
    path('payroll_settings/<str:org_id>/<str:admin_id>', PayrollSettingsAPIView.as_view(), name='payroll_settings_list'),
    path('payroll_settings/<str:org_id>/<str:admin_id>/<int:pk>', PayrollSettingsAPIView.as_view(), name='payroll_settings_detail'),
    
    # CUSTOM-PAYROLL-SHEET
    path('demo_custom_payload_sheet/<str:org_id>/<str:admin_id>/', GenerateCustomPayableSheet.as_view(), name='demo_custom_payload_sheet'),
    path('custom-payroll-monthly-report/<str:org_id>/<str:admin_id>/<int:month>/<int:year>', GenerateCustomPayableSheet.as_view(), name='custom-payroll-monthly-report'),
    
    # DEDUCTION-EXCEL
    path('download-deduction-sample-excel', DownloadDeductionSampleExcel.as_view(), name='download_deduction_sample_excel'),
    path('upload-deduction-excel/<str:clnID>/<int:month>/<int:year>', UploadDeductionExcel.as_view(), name='upload_deduction_excel'),
    
    # EARNING-EXCEL
    path('download-earning-sample-excel', DownloadEarningSampleExcel.as_view(), name='download-earning-sample-excel'),
    path('upload-earning-excel/<str:clnID>/<int:month>/<int:year>', UploadEarningExcel.as_view(), name='upload-earning-excel'),
    
    # EMPLOYEE-PAYSLIPS
    path('employee-payslips/<str:admin_id>/<int:month>/<int:year>', EmployeePayslipAPI.as_view(), name='employee-payslips-by-admin'),
    path('employee-payslips/<str:admin_id>/<str:uniqueID>/<int:month>/<int:year>', EmployeePayslipAPI.as_view(), name='employee-payslips-by-admin-and-uid'),
    
    # ADDITIONAL UTILITY APIS
    path('dashboard/<str:org_id>', PayrollDashboardAPIView.as_view(), name='payroll-dashboard'),
    path('employee-history/<str:org_id>/<str:employee_id>', EmployeePayrollHistoryAPIView.as_view(), name='employee-payroll-history'),
    path('summary/<str:org_id>', PayrollSummaryAPIView.as_view(), name='payroll-summary'),
    path('advances/<str:org_id>', EmployeeAdvanceListAPIView.as_view(), name='employee-advances-list'),
    path('advances/<str:org_id>/<str:employee_id>', EmployeeAdvanceListAPIView.as_view(), name='employee-advances-list-by-employee'),
    path('bank-info-list/<str:org_id>', EmployeeBankInfoListAPIView.as_view(), name='bank-info-list'),
]

