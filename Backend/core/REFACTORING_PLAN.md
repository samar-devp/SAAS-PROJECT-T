# Backend Refactoring Plan - Advanced Folder Structure

## Overview
Reorganizing all backend files into a proper, advanced-level folder structure with all utility functions in `utils` folder.

## Folder Structure

```
Backend/core/
├── utils/
│   ├── services/
│   │   ├── leave/
│   │   │   ├── __init__.py
│   │   │   ├── leave_calculator.py (moved from LeaveControl/)
│   │   │   └── leave_excel_service.py (moved from LeaveControl/)
│   │   ├── payroll/
│   │   │   ├── __init__.py
│   │   │   ├── payroll_calculator.py (moved from PayrollSystem/)
│   │   │   ├── attendance_calculation_service.py (moved from PayrollSystem/)
│   │   │   └── payroll_excel_service.py (moved from PayrollSystem/)
│   │   ├── asset/
│   │   │   ├── __init__.py
│   │   │   └── depreciation_service.py (moved from AssetManagement/)
│   │   ├── attendance/
│   │   │   ├── __init__.py
│   │   │   ├── attendance_utils.py (already exists)
│   │   │   ├── attendance_edit_service.py (already exists)
│   │   │   └── attendance_excel_export_service.py (already exists)
│   │   └── excel/
│   │       └── __init__.py
│   ├── helpers/
│   │   ├── __init__.py
│   │   ├── model_helpers.py (moved from common_utils.py)
│   │   ├── pagination_helpers.py (moved from pagination_utils.py)
│   │   └── session_helpers.py (moved from session_utils.py)
│   ├── validators/
│   │   └── __init__.py
│   ├── exceptions/
│   │   └── __init__.py
│   ├── constants/
│   │   └── __init__.py
│   ├── decorators/
│   │   └── __init__.py
│   ├── mixins/
│   │   └── __init__.py
│   └── __init__.py
```

## Files to Move

### Services
1. `LeaveControl/leave_calculator.py` → `utils/services/leave/leave_calculator.py`
2. `LeaveControl/leave_excel_service.py` → `utils/services/excel/leave_excel_service.py`
3. `PayrollSystem/payroll_calculator.py` → `utils/services/payroll/payroll_calculator.py`
4. `PayrollSystem/attendance_calculation_service.py` → `utils/services/payroll/attendance_calculation_service.py`
5. `PayrollSystem/payroll_excel_service.py` → `utils/services/excel/payroll_excel_service.py`
6. `AssetManagement/depreciation_service.py` → `utils/services/asset/depreciation_service.py`

### Helpers
1. `utils/common_utils.py` → `utils/helpers/model_helpers.py` (rename function)
2. `utils/pagination_utils.py` → `utils/helpers/pagination_helpers.py`
3. `utils/session_utils.py` → `utils/helpers/session_helpers.py`

## Import Updates Required

### Service Imports
- `from .leave_calculator import LeaveCalculator` → `from utils.services.leave.leave_calculator import LeaveCalculator`
- `from .payroll_calculator import PayrollCalculator` → `from utils.services.payroll.payroll_calculator import PayrollCalculator`
- `from .attendance_calculation_service import AttendanceCalculationService` → `from utils.services.payroll.attendance_calculation_service import AttendanceCalculationService`
- `from .depreciation_service import AssetDepreciationService` → `from utils.services.asset.depreciation_service import AssetDepreciationService`
- `from .leave_excel_service import LeaveExcelService` → `from utils.services.excel.leave_excel_service import LeaveExcelService`
- `from .payroll_excel_service import PayrollExcelService` → `from utils.services.excel.payroll_excel_service import PayrollExcelService`

### Helper Imports
- `from utils.pagination_utils import CustomPagination` → `from utils.helpers.pagination_helpers import CustomPagination`
- `from utils.common_utils import *` → `from utils.helpers.model_helpers import *`
- `from utils.session_utils import *` → `from utils.helpers.session_helpers import *`

## Files to Update

1. PayrollSystem/views.py
2. PayrollSystem/payroll_calculator.py
3. PayrollSystem/additional_views.py
4. LeaveControl/advanced_views.py
5. core/tasks.py
6. All files using pagination_utils, common_utils, session_utils (34 files)

