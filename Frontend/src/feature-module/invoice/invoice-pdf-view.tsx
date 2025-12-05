import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { all_routes } from '../router/all_routes';
import axios from 'axios';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { getAdminIdForApi } from '../../core/utils/apiHelpers';
import dayjs from 'dayjs';
// @ts-ignore
import html2pdf from 'html2pdf.js';

const InvoicePDFView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [invoice, setInvoice] = useState<any>(null);

  const themes: { [key: string]: string } = {
    red: '#dc3545',
    orange: '#fd7e14',
    blue: '#0d6efd',
    green: '#198754',
    purple: '#6f42c1',
    pink: '#d63384',
    teal: '#20c997',
    yellow: '#ffc107',
    cyan: '#17a2b8',
    gray: '#6c757d',
    hotpink: '#e83e8c',
    indigo: '#6610f2',
    success: '#28a745',
    coral: '#ff6b6b',
    turquoise: '#4ecdc4',
    skyblue: '#45b7d1',
    gold: '#f9ca24',
    lavender: '#6c5ce7',
    lightpurple: '#a29bfe',
    rose: '#fd79a8',
    mint: '#00b894',
    aqua: '#00cec9',
    peach: '#e17055',
    ocean: '#0984e3',
    charcoal: '#2d3436',
    slate: '#636e72',
    silver: '#b2bec3',
    lightgray: '#dfe6e9'
  };

  useEffect(() => {
    // Check authentication first
    const token = sessionStorage.getItem("access_token");
    if (!token) {
      toast.error("Please login to view invoice");
      navigate('/login');
      return;
    }
    
    const admin_id = getAdminIdForApi();
    if (!admin_id) {
      const role = sessionStorage.getItem("role");
      if (role === "organization") {
        toast.error("Please select an admin first from the dashboard.");
        navigate('/index');
      } else {
        toast.error("Admin ID not found. Please login again.");
        navigate('/login');
      }
      return;
    }
    
    if (id) {
      fetchInvoice(id);
    }
  }, [id, navigate]);

  const fetchInvoice = async (invoiceId: string) => {
    try {
      setLoading(true);
      const token = sessionStorage.getItem("access_token");
      
      if (!token) {
        toast.error("Please login to view invoice");
        navigate('/login');
        return;
      }
      
      const admin_id = getAdminIdForApi();
      
      if (!admin_id) {
        const role = sessionStorage.getItem("role");
        if (role === "organization") {
          toast.error("Please select an admin first from the dashboard.");
          navigate('/index');
        } else {
          toast.error("Admin ID not found. Please login again.");
          navigate('/login');
        }
        return;
      }

      const response = await axios.get(
        `http://127.0.0.1:8000/api/invoices/${admin_id}/${invoiceId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.data && response.data.data) {
        setInvoice(response.data.data);
      }
    } catch (error: any) {
      console.error("Error fetching invoice:", error);
      if (error.response?.status === 401) {
        toast.error("Session expired. Please login again.");
        navigate('/login');
      } else {
        toast.error(error.response?.data?.message || "Failed to fetch invoice");
      }
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const handleDownloadPDF = async () => {
    try {
      const element = document.querySelector('.invoice-pdf-container') as HTMLElement;
      if (!element) {
        toast.error("Invoice content not found");
        return;
      }

      // Temporarily reduce font sizes and spacing for PDF
      const originalStyles = new WeakMap<HTMLElement, { fontSize: string; padding: string; margin: string }>();
      const styleElements = element.querySelectorAll('*') as NodeListOf<HTMLElement>;
      styleElements.forEach((el) => {
        const computedStyle = window.getComputedStyle(el);
        originalStyles.set(el, {
          fontSize: el.style.fontSize,
          padding: el.style.padding,
          margin: el.style.margin,
        });
        
        // Reduce font sizes
        if (computedStyle.fontSize) {
          const fontSize = parseFloat(computedStyle.fontSize);
          if (fontSize > 10) {
            el.style.fontSize = `${fontSize * 0.85}px`;
          }
        }
        
        // Reduce padding and margins for table cells
        if (el.tagName === 'TD' || el.tagName === 'TH') {
          el.style.padding = '4px 6px';
        }
      });

      const opt: any = {
        margin: [5, 5, 5, 5],
        filename: `${invoice.invoice_number || 'invoice'}.pdf`,
        image: { type: 'jpeg', quality: 0.92 },
        html2canvas: { 
          scale: 1.5,
          useCORS: true,
          logging: false,
          letterRendering: true,
          windowWidth: 800,
          windowHeight: 1120 // A4 height in pixels at 96 DPI
        },
        jsPDF: { 
          unit: 'mm', 
          format: 'a4', 
          orientation: 'portrait',
          compress: true
        },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
      };

      toast.info("Generating PDF...");
      
      // @ts-ignore - html2pdf.js API
      await html2pdf().set(opt).from(element).save();
      
      // Restore original styles
      styleElements.forEach((el) => {
        const saved = originalStyles.get(el);
        if (saved) {
          el.style.fontSize = saved.fontSize || '';
          el.style.padding = saved.padding || '';
          el.style.margin = saved.margin || '';
        }
      });
      
      toast.success("PDF downloaded successfully");
    } catch (error: any) {
      console.error("Error generating PDF:", error);
      toast.error("Failed to download PDF. Please try again.");
    }
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '100vh' }}>
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  if (!invoice) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '100vh' }}>
        <div className="text-center">
          <h4>Invoice not found</h4>
          <Link to={all_routes.invoices} className="btn btn-primary mt-3">
            Back to Invoices
          </Link>
        </div>
      </div>
    );
  }

  const themeColor = themes[invoice.theme_color || 'red'] || '#dc3545';

  return (
    <>
      <style>{`
        @page {
          size: A4;
          margin: 10mm;
        }
        @media print {
          /* Force show everything first */
          body * {
            visibility: visible;
          }
          * {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
            color-adjust: exact !important;
          }
          html, body {
            background: white !important;
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            height: auto !important;
            overflow: visible !important;
          }
          /* Hide page navigation elements */
          .no-print {
            display: none !important;
          }
          header, .header, #header,
          .sidebar, #sidebar, .two-col-sidebar {
            display: none !important;
          }
          /* Reset page wrapper - MUST be visible */
          .page-wrapper {
            display: block !important;
            visibility: visible !important;
            margin: 0 !important;
            padding: 0 !important;
            background: white !important;
            width: 100% !important;
            position: relative !important;
            overflow: visible !important;
          }
          .content {
            display: block !important;
            visibility: visible !important;
            margin: 0 !important;
            padding: 0 !important;
            background: white !important;
            width: 100% !important;
            overflow: visible !important;
          }
          /* Show invoice container - CRITICAL */
          .invoice-pdf-container {
            display: block !important;
            visibility: visible !important;
            position: relative !important;
            width: 100% !important;
            max-width: 100% !important;
            margin: 0 !important;
            padding: 8mm !important;
            box-shadow: none !important;
            border: none !important;
            background: white !important;
            page-break-inside: avoid;
            overflow: visible !important;
          }
          /* Ensure all invoice children are visible */
          .invoice-pdf-container * {
            visibility: visible !important;
          }
          /* Explicitly show invoice elements */
          .invoice-header,
          .invoice-body,
          .invoice-title,
          .invoice-table,
          .total-section,
          .total-row {
            display: block !important;
            visibility: visible !important;
          }
          .invoice-pdf-container .row {
            display: flex !important;
          }
          .invoice-pdf-container .col-md-6 {
            display: block !important;
            flex: 0 0 50% !important;
            max-width: 50% !important;
          }
          .invoice-pdf-container table {
            display: table !important;
          }
          .invoice-pdf-container thead {
            display: table-header-group !important;
          }
          .invoice-pdf-container tbody {
            display: table-row-group !important;
          }
          .invoice-pdf-container tr {
            display: table-row !important;
          }
          .invoice-pdf-container td,
          .invoice-pdf-container th {
            display: table-cell !important;
          }
          .invoice-pdf-container .d-flex {
            display: flex !important;
          }
          .invoice-header {
            padding: 8mm !important;
            margin-bottom: 0 !important;
            page-break-inside: avoid;
          }
          .invoice-title {
            font-size: 24px !important;
            margin: 0 !important;
          }
          .invoice-body {
            padding: 8mm !important;
            border: 1px solid #e9ecef;
            border-top: none;
            page-break-inside: avoid;
          }
          .invoice-logo {
            display: block !important;
            visibility: visible !important;
            max-height: 60px !important;
          }
          .invoice-table {
            font-size: 10px !important;
            margin: 8px 0 !important;
          }
          .invoice-table thead th {
            padding: 6px 4px !important;
            font-size: 9px !important;
          }
          .invoice-table tbody td {
            padding: 6px 4px !important;
            font-size: 9px !important;
          }
          .total-section {
            margin-top: 10px !important;
            font-size: 11px !important;
          }
          .total-row {
            padding: 4px 0 !important;
            font-size: 11px !important;
          }
          .total-row.final {
            font-size: 14px !important;
            padding: 6px 0 !important;
            margin-top: 6px !important;
          }
          h4, h6 {
            font-size: 12px !important;
            margin-bottom: 4px !important;
          }
          p {
            font-size: 10px !important;
            margin-bottom: 2px !important;
            line-height: 1.3 !important;
          }
          .mb-4 {
            margin-bottom: 8px !important;
          }
          .mt-4 {
            margin-top: 8px !important;
          }
          .mt-5 {
            margin-top: 10px !important;
          }
          .pt-4 {
            padding-top: 8px !important;
          }
        }
        .invoice-pdf-container {
          max-width: 210mm;
          margin: 0 auto;
          background: white;
          padding: 20mm;
          box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        .invoice-header {
          background: linear-gradient(135deg, ${themeColor} 0%, ${themeColor}dd 100%);
          color: white;
          padding: 30px;
          border-radius: 8px 8px 0 0;
          margin-bottom: 0;
        }
        .invoice-title {
          font-size: 36px;
          font-weight: 800;
          text-align: right;
          margin: 0;
          text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .invoice-body {
          padding: 30px;
          background: white;
          border: 1px solid #e9ecef;
          border-top: none;
        }
        .invoice-table {
          width: 100%;
          border-collapse: collapse;
          margin: 20px 0;
          font-size: 12px;
        }
        .invoice-table thead {
          background: ${themeColor};
          color: white;
        }
        .invoice-table thead th {
          padding: 12px;
          text-align: left;
          font-weight: 600;
          border: 1px solid rgba(255,255,255,0.2);
          font-size: 12px;
        }
        .invoice-table tbody td {
          padding: 12px;
          border: 1px solid #e9ecef;
          font-size: 12px;
        }
        .invoice-table tbody tr:nth-child(even) {
          background: #f8f9fa;
        }
        .total-section {
          margin-top: 20px;
          text-align: right;
        }
        .total-row {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid #e9ecef;
        }
        .total-row.final {
          font-size: 20px;
          font-weight: 700;
          color: ${themeColor};
          border-top: 2px solid ${themeColor};
          border-bottom: 2px solid ${themeColor};
          padding: 12px 0;
          margin-top: 10px;
        }
      `}</style>

      <div className="page-wrapper">
        <div className="content">
          {/* Action Buttons - Hidden on Print */}
          <div className="no-print mb-3">
            <div className="d-flex justify-content-between align-items-center">
              <Link to={all_routes.invoices} className="btn btn-outline-secondary">
                <i className="ti ti-arrow-left me-2" />
                Back to List
              </Link>
              <div className="d-flex gap-2">
                <button className="btn btn-primary" onClick={handleDownloadPDF}>
                  <i className="ti ti-download me-2" />
                  Download PDF
                </button>
              </div>
            </div>
          </div>

          {/* Invoice PDF Container */}
          <div className="invoice-pdf-container">
            {/* Header */}
            <div className="invoice-header">
              <div className="row align-items-center">
                <div className="col-md-6">
                  {(invoice.business_logo || invoice.business_logo_url) && (
                    <img 
                      className="invoice-logo"
                      src={(invoice.business_logo_url || invoice.business_logo || '').startsWith('http') 
                        ? (invoice.business_logo_url || invoice.business_logo) 
                        : `http://127.0.0.1:8000${invoice.business_logo_url || invoice.business_logo}`} 
                      alt="Logo" 
                      style={{ maxHeight: '80px', marginBottom: '10px' }}
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  )}
                  <h4 className="mb-1">{invoice.business_name || 'Company Name'}</h4>
                  {invoice.business_contact_name && (
                    <p className="mb-0 opacity-75">{invoice.business_contact_name}</p>
                  )}
                </div>
                <div className="col-md-6">
                  <h1 className="invoice-title">TAX INVOICE</h1>
                  <div className="mt-3 text-end">
                    <div className="mb-2">
                      <strong>Invoice #:</strong> {invoice.invoice_number || 'N/A'}
                    </div>
                    <div className="mb-2">
                      <strong>Date:</strong> {invoice.invoice_date ? dayjs(invoice.invoice_date).format('DD-MM-YYYY') : 'N/A'}
                    </div>
                    <div>
                      <strong>Due Date:</strong> {invoice.due_date ? dayjs(invoice.due_date).format('DD-MM-YYYY') : 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Body */}
            <div className="invoice-body">
              <div className="row mb-4">
                <div className="col-md-6">
                  <h6 className="fw-bold mb-3" style={{ color: themeColor }}>FROM:</h6>
                  <p className="mb-1"><strong>{invoice.business_name || 'N/A'}</strong></p>
                  {invoice.business_contact_name && <p className="mb-1">{invoice.business_contact_name}</p>}
                  {invoice.business_gstin && <p className="mb-1">GSTIN: {invoice.business_gstin}</p>}
                  {invoice.business_address_line1 && <p className="mb-1">{invoice.business_address_line1}</p>}
                  <p className="mb-1">
                    {invoice.business_city && `${invoice.business_city}, `}
                    {invoice.business_state && `${invoice.business_state} `}
                    {invoice.business_pincode && `- ${invoice.business_pincode}`}
                  </p>
                  {invoice.business_country && <p className="mb-0">{invoice.business_country}</p>}
                </div>
                <div className="col-md-6">
                  <h6 className="fw-bold mb-3" style={{ color: themeColor }}>BILL TO:</h6>
                  <p className="mb-1"><strong>{invoice.client_name || 'N/A'}</strong></p>
                  {invoice.client_gstin && <p className="mb-1">GSTIN: {invoice.client_gstin}</p>}
                  {invoice.client_address_line1 && <p className="mb-1">{invoice.client_address_line1}</p>}
                  <p className="mb-1">
                    {invoice.client_city && `${invoice.client_city}, `}
                    {invoice.client_state && `${invoice.client_state} `}
                    {invoice.client_pincode && `- ${invoice.client_pincode}`}
                  </p>
                  {invoice.client_country && <p className="mb-0">{invoice.client_country}</p>}
                </div>
              </div>

              {invoice.place_of_supply && (
                <div className="mb-4">
                  <strong>Place of Supply:</strong> {invoice.place_of_supply}
                </div>
              )}

              {/* Items Table */}
              <table className="invoice-table">
                <thead>
                  <tr>
                    <th>Description</th>
                    <th>HSN/SAC</th>
                    <th>Qty</th>
                    <th>Rate</th>
                    <th>SGST %</th>
                    <th>CGST %</th>
                    <th>Cess %</th>
                    <th>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {invoice.items && invoice.items.length > 0 ? (
                    invoice.items.map((item: any, index: number) => (
                      <tr key={index}>
                        <td>{item.description || 'N/A'}</td>
                        <td>{item.hsn_sac || 'N/A'}</td>
                        <td>{item.quantity || 0}</td>
                        <td>{formatCurrency(parseFloat(item.rate || 0))}</td>
                        <td>{item.sgst_percent || 0}%</td>
                        <td>{item.cgst_percent || 0}%</td>
                        <td>{item.cess_percent || 0}%</td>
                        <td>{formatCurrency(parseFloat(item.amount || 0))}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={8} className="text-center">No items</td>
                    </tr>
                  )}
                </tbody>
              </table>

              {/* Totals */}
              <div className="total-section">
                <div className="total-row">
                  <strong>Sub Total:</strong>
                  <span>{formatCurrency(parseFloat(invoice.sub_total || 0))}</span>
                </div>
                <div className="total-row">
                  <strong>Total SGST:</strong>
                  <span>{formatCurrency(parseFloat(invoice.total_sgst || 0))}</span>
                </div>
                <div className="total-row">
                  <strong>Total CGST:</strong>
                  <span>{formatCurrency(parseFloat(invoice.total_cgst || 0))}</span>
                </div>
                {parseFloat(invoice.total_cess || 0) > 0 && (
                  <div className="total-row" style={{ display: 'flex', visibility: 'visible' }}>
                    <strong>Total Cess:</strong>
                    <span>{formatCurrency(parseFloat(invoice.total_cess || 0))}</span>
                  </div>
                )}
                <div className="total-row final">
                  <strong>TOTAL:</strong>
                  <span>{formatCurrency(parseFloat(invoice.total_amount || 0))}</span>
                </div>
              </div>

              {/* Notes */}
              {invoice.notes && (
                <div className="mt-4">
                  <h6 className="fw-bold mb-2" style={{ color: '#fd7e14' }}>Notes:</h6>
                  <p className="mb-0">{invoice.notes}</p>
                </div>
              )}

              {/* Terms & Conditions */}
              {invoice.terms_and_conditions && (
                <div className="mt-4">
                  <h6 className="fw-bold mb-2" style={{ color: '#fd7e14' }}>Terms & Conditions:</h6>
                  <p className="mb-0">{invoice.terms_and_conditions}</p>
                </div>
              )}

              {/* Footer */}
              <div className="text-center mt-5 pt-4 border-top">
                <p className="text-muted mb-0" style={{ fontSize: '12px' }}>
                  Generated using <strong>NeexQ Technology</strong>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      <ToastContainer position="top-right" autoClose={3000} />
    </>
  );
};

export default InvoicePDFView;

