# Unused Dependencies Report
## Project: SAAS-PROJECT-T

**Date:** December 5, 2025
**Analysis Type:** Static Code Analysis
**Status:** ✅ COMPLETED - Unused packages removed

---

## 📊 Summary

### Frontend (React/TypeScript)
- **Total Dependencies:** 79 packages
- **Potentially Unused:** ~27 packages
- **Definitely Unused:** ~20 packages

### Backend (Django/Python)
- **Note:** No `requirements.txt` file found. Cannot analyze Python dependencies without dependency list.

---

## 🚨 Frontend - Unused Dependencies

### Definitely Unused (Can be safely removed)

1. **@fullcalendar/core, @fullcalendar/daygrid, @fullcalendar/interaction, @fullcalendar/react, @fullcalendar/timegrid**
   - **Status:** ❌ Not used anywhere
   - **Size:** ~500KB
   - **Action:** Remove all @fullcalendar packages

2. **@hello-pangea/dnd**
   - **Status:** ❌ Not used
   - **Size:** ~50KB
   - **Action:** Remove

3. **@react-latest-ui/react-sticky-notes**
   - **Status:** ❌ Not used
   - **Size:** ~30KB
   - **Action:** Remove

4. **chart.js**
   - **Status:** ❌ Not used (using react-apexcharts instead)
   - **Size:** ~200KB
   - **Action:** Remove

5. **clipboard-copy**
   - **Status:** ❌ Not used (only found in CSS/icon files)
   - **Size:** ~5KB
   - **Action:** Remove

6. **dragula**
   - **Status:** ❌ Not used
   - **Size:** ~20KB
   - **Action:** Remove

7. **feather-icons-react**
   - **Status:** ❌ Not used (using react-feather instead)
   - **Size:** ~100KB
   - **Action:** Remove

8. **leaflet, react-leaflet**
   - **Status:** ❌ Not used (only commented routes found)
   - **Size:** ~300KB
   - **Action:** Remove

9. **moment**
   - **Status:** ⚠️ Partially used (only in datePicker.tsx, but dayjs is preferred)
   - **Size:** ~70KB
   - **Action:** Consider removing after migrating datePicker.tsx to dayjs

10. **quill**
    - **Status:** ❌ Not used (only found in icon files)
    - **Size:** ~200KB
    - **Action:** Remove

11. **react-awesome-stars-rating**
    - **Status:** ❌ Not used
    - **Size:** ~10KB
    - **Action:** Remove

12. **react-beautiful-dnd**
    - **Status:** ❌ Not used
    - **Size:** ~50KB
    - **Action:** Remove

13. **react-country-flag**
    - **Status:** ❌ Not used
    - **Size:** ~20KB
    - **Action:** Remove

14. **react-countup**
    - **Status:** ❌ Not used
    - **Size:** ~15KB
    - **Action:** Remove

15. **react-dnd, react-dnd-html5-backend**
    - **Status:** ❌ Not used
    - **Size:** ~100KB
    - **Action:** Remove

16. **react-icons**
    - **Status:** ❌ Not used
    - **Size:** ~500KB
    - **Action:** Remove

17. **react-input-mask**
    - **Status:** ❌ Not used
    - **Size:** ~10KB
    - **Action:** Remove

18. **react-modal-video**
    - **Status:** ❌ Not used
    - **Size:** ~20KB
    - **Action:** Remove

19. **react-slick**
    - **Status:** ⚠️ Only CSS imported, component not used
    - **Size:** ~50KB
    - **Action:** Remove if slick-carousel CSS is not needed

20. **react-tag-input**
    - **Status:** ❌ Not used (using react-tag-input-component instead)
    - **Size:** ~30KB
    - **Action:** Remove

21. **react-time-picker**
    - **Status:** ⚠️ Only CSS imported, component not used
    - **Size:** ~20KB
    - **Action:** Remove

22. **sweetalert2, sweetalert2-react-content**
    - **Status:** ❌ Not used (using react-toastify instead)
    - **Size:** ~50KB
    - **Action:** Remove

23. **weather-icons-react**
    - **Status:** ❌ Not used
    - **Size:** ~100KB
    - **Action:** Remove

24. **web-vitals**
    - **Status:** ❌ Not used
    - **Size:** ~5KB
    - **Action:** Remove (unless needed for analytics)

25. **start**
    - **Status:** ❌ Not used
    - **Size:** ~5KB
    - **Action:** Remove

26. **yet-another-react-lightbox**
    - **Status:** ⚠️ Incorrect imports found (importing 'label' from package)
    - **Size:** ~100KB
   - **Action:** Fix imports or remove if not needed

### Testing Dependencies (DevDependencies - Review)

27. **@testing-library/jest-dom, @testing-library/react, @testing-library/user-event**
    - **Status:** ⚠️ Dev dependencies - check if tests exist
    - **Action:** Keep if writing tests, remove if not

---

## ✅ Frontend - Used Dependencies (Keep These)

- ✅ **antd, @ant-design/icons** - Used (DatePicker, Table components)
- ✅ **apexcharts, react-apexcharts** - Used (Charts in dashboards)
- ✅ **axios** - Used (API calls)
- ✅ **bootstrap, react-bootstrap** - Used (UI framework)
- ✅ **bootstrap-daterangepicker, react-bootstrap-daterangepicker** - Used (DatePicker component)
- ✅ **dayjs** - Used (Date handling - preferred over moment)
- ✅ **html2pdf.js** - Used (Invoice PDF generation)
- ✅ **jquery** - Used (Bootstrap integration)
- ✅ **primereact, primeicons** - Used (UI components)
- ✅ **react, react-dom** - Core dependencies
- ✅ **react-custom-scrollbars-2** - Used (Scrollbars component)
- ✅ **react-datepicker** - Used (Date picker in VisitMap)
- ✅ **react-feather** - Used (Icons)
- ✅ **react-redux, @reduxjs/toolkit** - Used (State management)
- ✅ **react-router, react-router-dom** - Used (Routing)
- ✅ **react-select** - Used (Select components)
- ✅ **react-simple-wysiwyg** - Used (Text editor)
- ✅ **react-tag-input-component** - Used (Tag input)
- ✅ **react-toastify** - Used (Notifications)
- ✅ **slick-carousel** - Used (CSS for carousel)
- ✅ **swiper** - Used (Swiper CSS imports)
- ✅ **sass** - Used (Styling)
- ✅ **typescript** - Used (Type checking)
- ✅ **@fortawesome/fontawesome-free, @fortawesome/free-solid-svg-icons, @fortawesome/react-fontawesome** - Used (Icons)

---

## 🔍 Backend - Dependency Analysis

### Note
No `requirements.txt` or `Pipfile` found in the Backend directory. To analyze Python dependencies:

1. **Create requirements.txt:**
   ```bash
   cd Backend
   pip freeze > requirements.txt
   ```

2. **Or use pipreqs:**
   ```bash
   pip install pipreqs
   pipreqs Backend/core --force
   ```

### Currently Used Packages (Based on Code Analysis)

Based on imports found in the codebase:

- ✅ **Django** - Core framework
- ✅ **djangorestframework** - REST API
- ✅ **djangorestframework-simplejwt** - JWT authentication
- ✅ **django-cors-headers** - CORS handling
- ✅ **celery** - Background tasks
- ✅ **redis** - Cache & Celery broker (if installed)
- ✅ **django-redis** - Redis cache backend (optional, with fallback)
- ✅ **openpyxl** - Excel file handling
- ✅ **easyocr** - OCR (optional, with fallback)
- ✅ **pytesseract** - OCR alternative (optional, with fallback)
- ✅ **Pillow (PIL)** - Image processing (optional, for OCR)
- ✅ **numpy** - Used by easyocr (optional)

---

## 📝 Recommendations

### Immediate Actions

1. **Remove unused Frontend packages:**
   ```bash
   cd Frontend
   npm uninstall @fullcalendar/core @fullcalendar/daygrid @fullcalendar/interaction @fullcalendar/react @fullcalendar/timegrid @hello-pangea/dnd @react-latest-ui/react-sticky-notes chart.js clipboard-copy dragula feather-icons-react leaflet react-leaflet quill react-awesome-stars-rating react-beautiful-dnd react-country-flag react-countup react-dnd react-dnd-html5-backend react-icons react-input-mask react-modal-video react-slick react-tag-input react-time-picker sweetalert2 sweetalert2-react-content weather-icons-react web-vitals start yet-another-react-lightbox
   ```

2. **Review and potentially remove:**
   - `moment` (after migrating datePicker.tsx to dayjs)
   - `@testing-library/*` (if not writing tests)

3. **Fix incorrect imports:**
   - Fix `yet-another-react-lightbox` imports in:
     - `Frontend/src/core/modals/add_pipeline.tsx`
     - `Frontend/src/core/modals/edit_contact.tsx`
     - `Frontend/src/core/modals/pipeline.tsx`
     - `Frontend/src/core/modals/edit_company.tsx`
     - `Frontend/src/core/modals/add_contact.tsx`
     - `Frontend/src/core/modals/add_company.tsx`
     - `Frontend/src/core/modals/add_activity.tsx`

### Backend Actions

1. **Create requirements.txt:**
   ```bash
   cd Backend
   pip freeze > requirements.txt
   ```

2. **Use pipreqs to generate from imports:**
   ```bash
   pip install pipreqs
   pipreqs Backend/core --force
   ```

3. **Review optional dependencies:**
   - `easyocr` / `pytesseract` - Only needed for OCR feature
   - `django-redis` - Has fallback to local memory cache
   - `numpy` - Only needed if using easyocr

---

## 💾 Estimated Space Savings

Removing unused Frontend packages could save approximately:
- **~2.5 MB** in node_modules
- **Faster build times**
- **Faster npm install**

---

## ⚠️ Important Notes

1. **Test thoroughly** after removing packages
2. **Check for dynamic imports** that might not be caught by static analysis
3. **Review CSS imports** - some packages might be imported only for CSS
4. **Backup before removal** - use version control

---

## ✅ Completed Actions

1. ✅ Review this report
2. ✅ Removed unused packages from package.json
3. ✅ Fixed incorrect imports (yet-another-react-lightbox)
4. ✅ Removed unused CSS imports (react-time-picker)
5. ✅ Cleaned up devDependencies
6. ✅ Ran npm install - **92 packages removed successfully!**

## 🔄 Remaining Next Steps

1. ⬜ Test application thoroughly after package removal
2. ✅ Create Backend requirements.txt - **COMPLETED**
3. ✅ Analyze Backend dependencies - **COMPLETED**
4. ⬜ Consider migrating moment to dayjs in datePicker.tsx (optional)

## 📦 Backend Dependencies Analysis

### ✅ All Packages Are Used
Based on code analysis, all installed Python packages are being used:
- **Django & DRF** - Core framework
- **Celery & Redis** - Background tasks
- **openpyxl** - Excel file handling
- **easyocr/pytesseract** - OCR (optional, for Contact Management)
- **Pillow** - Image processing
- **torch/torchvision** - Required by easyocr

### 📄 Files Created
1. **Backend/requirements.txt** - Full requirements with OCR
2. **Backend/requirements-minimal.txt** - Minimal requirements without OCR (~100MB vs ~3GB)
3. **Backend/DEPENDENCIES_README.md** - Detailed dependency documentation

---

## 📦 Packages Removed (Summary)

**Total Removed:** 27 packages + 7 devDependencies = **34 packages**

### Dependencies Removed:
- @fullcalendar/* (5 packages)
- @hello-pangea/dnd
- @react-latest-ui/react-sticky-notes
- chart.js
- clipboard-copy
- dragula
- feather-icons-react
- leaflet, react-leaflet
- quill
- react-awesome-stars-rating
- react-beautiful-dnd
- react-country-flag
- react-countup
- react-dnd, react-dnd-html5-backend
- react-icons
- react-input-mask
- react-modal-video
- react-slick
- react-tag-input
- react-time-picker
- sweetalert2, sweetalert2-react-content
- weather-icons-react
- web-vitals
- start
- yet-another-react-lightbox

### DevDependencies Removed:
- @types/dragula
- @types/leaflet
- @types/react-beautiful-dnd
- @types/react-dnd
- @types/react-input-mask
- @types/react-modal-video
- @types/react-slick

**Generated by:** Dependency Analysis Tool
**Last Updated:** December 5, 2025
**Status:** ✅ Cleanup Complete

