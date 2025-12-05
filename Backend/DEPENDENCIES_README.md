# Backend Dependencies Guide

## 📦 Overview

This document explains all Python dependencies used in the SAAS-PROJECT-T Backend.

## 🎯 Core Dependencies (Required)

### Django Framework
- **Django==5.2.8** - Main web framework
- **asgiref** - ASGI support
- **sqlparse** - SQL parsing
- **tzdata** - Timezone data

### REST API
- **djangorestframework** - REST API framework
- **djangorestframework-simplejwt** - JWT authentication
- **PyJWT** - JWT token handling

### CORS
- **django-cors-headers** - Cross-Origin Resource Sharing support

### Background Tasks
- **celery** - Distributed task queue
- **kombu, vine, billiard, amqp** - Celery dependencies

### Cache & Message Broker
- **redis** - Used for Celery broker and caching

### File Handling
- **openpyxl** - Excel file reading/writing
- **Pillow** - Image processing

## 🔧 Optional Dependencies

### OCR (Optical Character Recognition)
**Required for:** Contact Management - Business Card Scanning

You can choose ONE of the following:

#### Option 1: EasyOCR (Recommended)
- **easyocr** - Easy to use OCR library
- **Pros:** No external software needed, easier setup
- **Cons:** Larger installation size (~2GB with dependencies)
- **Dependencies:** torch, torchvision, numpy, opencv-python-headless, scikit-image, scipy, etc.

#### Option 2: Tesseract
- **pytesseract** - Python wrapper for Tesseract OCR
- **Pros:** Smaller installation size
- **Cons:** Requires Tesseract OCR software to be installed separately
- **Installation:**
  - Windows: Download from [Tesseract OCR GitHub](https://github.com/tesseract-ocr/tesseract)
  - Linux: `sudo apt-get install tesseract-ocr`
  - Mac: `brew install tesseract`

### Redis Cache Backend
- **django-redis** - Optional Redis cache backend
- **Status:** Currently using fallback to local memory cache
- **Note:** Uncomment in requirements.txt if you want Redis caching

## 📊 Package Size Analysis

### Heavy Packages (OCR-related)
- **torch** (~2GB) - PyTorch deep learning framework
- **torchvision** (~500MB) - Computer vision utilities
- **easyocr dependencies** (~500MB) - Various ML libraries

### Medium Packages
- **Django + DRF** (~50MB)
- **Celery + Redis** (~20MB)

### Light Packages
- Most other packages are < 10MB each

## 🚀 Installation Options

### Full Installation (with OCR)
```bash
pip install -r requirements.txt
```
**Size:** ~3GB
**Use when:** You need OCR functionality for business card scanning

### Minimal Installation (without OCR)
```bash
pip install -r requirements-minimal.txt
```
**Size:** ~100MB
**Use when:** You don't need OCR functionality

## ⚠️ Important Notes

1. **OCR is Optional:** The Contact Management module will work without OCR, but business card scanning won't be available.

2. **Redis is Required:** For Celery background tasks, Redis must be running.

3. **Database:** Currently using SQLite. For production, consider PostgreSQL or MySQL.

4. **Python Version:** Requires Python 3.8 or higher.

## 🔍 Unused Dependencies Check

Based on code analysis, all installed packages appear to be used:
- ✅ Django - Core framework
- ✅ DRF - REST API
- ✅ Celery - Background tasks
- ✅ Redis - Message broker
- ✅ openpyxl - Excel exports
- ✅ easyocr/pytesseract - OCR (optional)
- ✅ Pillow - Image processing

## 📝 Recommendations

1. **For Development:** Use `requirements-minimal.txt` to speed up setup
2. **For Production:** Use full `requirements.txt` if OCR is needed
3. **Consider:** Using PostgreSQL instead of SQLite for production
4. **Consider:** Adding `django-redis` if you need Redis caching

## 🛠️ Troubleshooting

### OCR Not Working?
- Check if easyocr or pytesseract is installed
- For Tesseract: Verify Tesseract OCR software is installed
- Check OCR service logs in ContactManagement module

### Celery Not Working?
- Ensure Redis is running: `redis-cli ping` should return `PONG`
- Check Celery worker logs
- Verify Redis connection in settings.py

### Import Errors?
- Ensure virtual environment is activated
- Run: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)

