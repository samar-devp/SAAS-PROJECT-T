# Contact Management Module

A comprehensive contact management system with OCR/AI-powered business card scanning capabilities.

## Features

1. **Business Card Scanning**: Upload a business card image and automatically extract contact information using OCR
2. **Manual Entry**: Enter contact details manually with full form support
3. **Contact Management**: Full CRUD operations for contacts
4. **Search & Filter**: Search contacts by name, company, phone, email, state, city
5. **Statistics**: View contact statistics and analytics

## Installation

### Backend Dependencies

The OCR functionality requires additional dependencies:

1. **Install Python packages:**
   ```bash
   pip install pytesseract pillow
   ```

2. **Install Tesseract OCR:**
   - **Windows**: Download and install from [Tesseract OCR GitHub](https://github.com/tesseract-ocr/tesseract)
   - **Linux**: `sudo apt-get install tesseract-ocr` (Ubuntu/Debian) or `sudo yum install tesseract` (CentOS/RHEL)
   - **macOS**: `brew install tesseract`

3. **Configure Tesseract path (if needed):**
   If Tesseract is not in your system PATH, you may need to set the path in your Django settings:
   ```python
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows example
   ```

### Database Migration

After installing dependencies, run migrations:

```bash
python manage.py makemigrations ContactManagement
python manage.py migrate
```

## API Endpoints

- `GET /api/contact/contacts/` - List all contacts (with search/filter support)
- `POST /api/contact/contacts/` - Create a new contact
- `GET /api/contact/contacts/<id>/` - Get contact details
- `PUT /api/contact/contacts/<id>/` - Update contact
- `DELETE /api/contact/contacts/<id>/` - Delete contact
- `POST /api/contact/contacts/extract/` - Extract contact info from business card image
- `GET /api/contact/contacts/stats/` - Get contact statistics

## Usage

### Scanning Business Cards

1. Navigate to Contact Management
2. Click "Add" button
3. Select "Scan Business Card" mode
4. Upload a business card image
5. Click "Extract Contact Information"
6. Review and edit the extracted data
7. Save the contact

### Manual Entry

1. Navigate to Contact Management
2. Click "Add" button
3. Select "Manual Entry" mode
4. Fill in the contact form
5. Optionally upload a business card image
6. Save the contact

## Extracted Fields

The OCR service extracts the following fields from business cards:

- Full Name
- Company Name
- Job Title / Position
- Department
- Mobile Number
- Alternate Phone Number
- Office Landline
- Fax Number
- Email Address
- Alternate Email Address
- Website
- LinkedIn URL
- Instagram URL
- Facebook URL
- WhatsApp Number
- Full Address
- State
- City
- Country
- Pincode/Zip code
- Additional Notes

## Notes

- The OCR service uses pattern matching and heuristics to identify fields
- Extraction accuracy depends on image quality and card layout
- Users can always edit extracted data before saving
- The system stores both scanned and manually entered contacts
- Business card images are stored in the `media/business_cards/` directory

