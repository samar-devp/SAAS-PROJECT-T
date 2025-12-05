import React, { useState, useEffect } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { all_routes } from '../router/all_routes'
import ImageWithBasePath from '../../core/common/imageWithBasePath';
import CommonSelect from '../../core/common/commonSelect';
import { DatePicker } from 'antd';
import dayjs, { Dayjs } from 'dayjs';
import axios from 'axios';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { getAdminIdForApi } from '../../core/utils/apiHelpers';

interface InvoiceItem {
    id: string;
    description: string;
    hsn: string;
    qty: number;
    rate: number;
    sgstPercent: number;
    cgstPercent: number;
    cessPercent: number;
    amount: number;
}

const AddInvoice = () => {
    const navigate = useNavigate();
    const { id } = useParams();
    const [loading, setLoading] = useState(false);
    const [selectedTheme, setSelectedTheme] = useState('red');
    
    // Form state
    const [invoiceDate, setInvoiceDate] = useState<Dayjs | null>(dayjs());
    const [dueDate, setDueDate] = useState<Dayjs | null>(dayjs().add(30, 'day'));
    const [invoiceNumber, setInvoiceNumber] = useState('');
    
    // Business Details
    const [businessName, setBusinessName] = useState('');
    const [businessContactName, setBusinessContactName] = useState('');
    const [businessGstin, setBusinessGstin] = useState('');
    const [businessAddressLine1, setBusinessAddressLine1] = useState('');
    const [businessCity, setBusinessCity] = useState('');
    const [businessState, setBusinessState] = useState('Select State');
    const [businessCountry, setBusinessCountry] = useState('India');
    const [businessPincode, setBusinessPincode] = useState('');
    const [businessLogo, setBusinessLogo] = useState<File | null>(null);
    const [businessLogoPreview, setBusinessLogoPreview] = useState<string>('');
    
    // Client Details
    const [clientName, setClientName] = useState('');
    const [clientGstin, setClientGstin] = useState('');
    const [clientAddressLine1, setClientAddressLine1] = useState('');
    const [clientCity, setClientCity] = useState('');
    const [clientState, setClientState] = useState('Select State');
    const [clientCountry, setClientCountry] = useState('India');
    const [clientPincode, setClientPincode] = useState('');
    
    // Place of Supply
    const [placeOfSupply, setPlaceOfSupply] = useState('Select State');
    
    // Notes & Terms
    const [notes, setNotes] = useState('');
    const [termsAndConditions, setTermsAndConditions] = useState('');
    
    const [invoiceItems, setInvoiceItems] = useState<InvoiceItem[]>([
        {
            id: Date.now().toString(),
            description: '',
            hsn: '',
            qty: 1,
            rate: 0,
            sgstPercent: 0,
            cgstPercent: 0,
            cessPercent: 0,
            amount: 0
        }
    ]);

    const themes = [
        { color: '#dc3545', name: 'red' },
        { color: '#fd7e14', name: 'orange' },
        { color: '#0d6efd', name: 'blue' },
        { color: '#198754', name: 'green' },
        { color: '#6f42c1', name: 'purple' },
        { color: '#d63384', name: 'pink' },
        { color: '#20c997', name: 'teal' },
        { color: '#ffc107', name: 'yellow' },
        { color: '#17a2b8', name: 'cyan' },
        { color: '#6c757d', name: 'gray' },
        { color: '#e83e8c', name: 'hotpink' },
        { color: '#6610f2', name: 'indigo' },
        { color: '#28a745', name: 'success' },
        { color: '#ff6b6b', name: 'coral' },
        { color: '#4ecdc4', name: 'turquoise' },
        { color: '#45b7d1', name: 'skyblue' },
        { color: '#f9ca24', name: 'gold' },
        { color: '#6c5ce7', name: 'lavender' },
        { color: '#a29bfe', name: 'lightpurple' },
        { color: '#fd79a8', name: 'rose' },
        { color: '#00b894', name: 'mint' },
        { color: '#00cec9', name: 'aqua' },
        { color: '#e17055', name: 'peach' },
        { color: '#0984e3', name: 'ocean' },
        { color: '#2d3436', name: 'charcoal' },
        { color: '#636e72', name: 'slate' },
        { color: '#b2bec3', name: 'silver' },
        { color: '#dfe6e9', name: 'lightgray' }
    ];

    const getModalContainer = () => {
        const modalElement = document.getElementById('modal-datepicker');
        return modalElement ? modalElement : document.body;
    };

    const calculateItemAmount = (item: InvoiceItem) => {
        const baseAmount = item.qty * item.rate;
        const sgstAmount = (baseAmount * item.sgstPercent) / 100;
        const cgstAmount = (baseAmount * item.cgstPercent) / 100;
        const cessAmount = (baseAmount * item.cessPercent) / 100;
        return baseAmount + sgstAmount + cgstAmount + cessAmount;
    };

    const calculateTotals = () => {
        const subTotal = invoiceItems.reduce((sum, item) => sum + (item.qty * item.rate), 0);
        const totalSGST = invoiceItems.reduce((sum, item) => sum + ((item.qty * item.rate * item.sgstPercent) / 100), 0);
        const totalCGST = invoiceItems.reduce((sum, item) => sum + ((item.qty * item.rate * item.cgstPercent) / 100), 0);
        const totalCess = invoiceItems.reduce((sum, item) => sum + ((item.qty * item.rate * item.cessPercent) / 100), 0);
        const total = subTotal + totalSGST + totalCGST + totalCess;
        return { subTotal, totalSGST, totalCGST, totalCess, total };
    };

    const totals = calculateTotals();

    const addNewItem = () => {
        const newItem: InvoiceItem = {
            id: Date.now().toString(),
            description: '',
            hsn: '',
            qty: 1,
            rate: 0,
            sgstPercent: 0,
            cgstPercent: 0,
            cessPercent: 0,
            amount: 0
        };
        setInvoiceItems([...invoiceItems, newItem]);
    };

    const removeItem = (id: string) => {
        setInvoiceItems(invoiceItems.filter(item => item.id !== id));
    };

    const updateItem = (id: string, field: keyof InvoiceItem, value: any) => {
        setInvoiceItems(invoiceItems.map(item => {
            if (item.id === id) {
                const updated = { ...item, [field]: value };
                updated.amount = calculateItemAmount(updated);
                return updated;
            }
            return item;
        }));
    };

    // Fetch invoice if editing
    useEffect(() => {
        if (id) {
            fetchInvoice(id);
        }
    }, [id]);

    const fetchInvoice = async (invoiceId: string) => {
        try {
            setLoading(true);
            const token = sessionStorage.getItem("access_token");
            const admin_id = getAdminIdForApi();
            
            if (!admin_id) {
                toast.error("Admin ID not found. Please login again.");
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
                const invoice = response.data.data;
                
                // Debug: Log invoice data
                console.log("Fetched invoice:", invoice);
                console.log("Invoice items:", invoice.items);
                console.log("Items type:", typeof invoice.items);
                console.log("Items is array:", Array.isArray(invoice.items));
                
                // Set form fields
                setInvoiceDate(invoice.invoice_date ? dayjs(invoice.invoice_date) : dayjs());
                setDueDate(invoice.due_date ? dayjs(invoice.due_date) : dayjs().add(30, 'day'));
                setInvoiceNumber(invoice.invoice_number || '');
                setSelectedTheme(invoice.theme_color || 'red');
                
                setBusinessName(invoice.business_name || '');
                setBusinessContactName(invoice.business_contact_name || '');
                setBusinessGstin(invoice.business_gstin || '');
                setBusinessAddressLine1(invoice.business_address_line1 || '');
                setBusinessCity(invoice.business_city || '');
                setBusinessState(invoice.business_state && invoice.business_state.trim() !== '' ? invoice.business_state : 'Select State');
                setBusinessCountry(invoice.business_country || 'India');
                setBusinessPincode(invoice.business_pincode || '');
                if (invoice.business_logo || invoice.business_logo_url) {
                    const logoUrl = invoice.business_logo_url || invoice.business_logo;
                    setBusinessLogoPreview(logoUrl.startsWith('http') ? logoUrl : `http://127.0.0.1:8000${logoUrl}`);
                }
                
                setClientName(invoice.client_name || '');
                setClientGstin(invoice.client_gstin || '');
                setClientAddressLine1(invoice.client_address_line1 || '');
                setClientCity(invoice.client_city || '');
                setClientState(invoice.client_state && invoice.client_state.trim() !== '' ? invoice.client_state : 'Select State');
                setClientCountry(invoice.client_country || 'India');
                setClientPincode(invoice.client_pincode || '');
                
                setPlaceOfSupply(invoice.place_of_supply && invoice.place_of_supply.trim() !== '' ? invoice.place_of_supply : 'Select State');
                setNotes(invoice.notes || '');
                setTermsAndConditions(invoice.terms_and_conditions || '');
                
                // Set items - handle both array and other formats
                let itemsToProcess = [];
                if (invoice.items) {
                    if (Array.isArray(invoice.items)) {
                        itemsToProcess = invoice.items;
                    } else if (typeof invoice.items === 'string') {
                        // If items is a JSON string, parse it
                        try {
                            itemsToProcess = JSON.parse(invoice.items);
                        } catch (e) {
                            console.error("Error parsing items JSON string:", e);
                            itemsToProcess = [];
                        }
                    }
                }
                
                console.log("Items to process:", itemsToProcess);
                
                if (itemsToProcess && itemsToProcess.length > 0) {
                    const mappedItems = itemsToProcess.map((item: any) => {
                        // Parse percentages - handle Decimal, string, and number formats
                        const parsePercent = (value: any): number => {
                            if (value === null || value === undefined || value === '') return 0;
                            if (typeof value === 'number') return value;
                            if (typeof value === 'string') {
                                const parsed = parseFloat(value);
                                return isNaN(parsed) ? 0 : parsed;
                            }
                            // Handle Decimal type from Django
                            if (value && typeof value === 'object' && 'toString' in value) {
                                return parseFloat(value.toString());
                            }
                            return 0;
                        };
                        
                        const sgst = parsePercent(item.sgst_percent);
                        const cgst = parsePercent(item.cgst_percent);
                        const cess = parsePercent(item.cess_percent);
                        
                        const qty = parseFloat(String(item.quantity || item.qty || 1));
                        const rate = parseFloat(String(item.rate || 0));
                        
                        // Recalculate amount based on loaded values
                        const baseAmount = qty * rate;
                        const sgstAmount = (baseAmount * sgst) / 100;
                        const cgstAmount = (baseAmount * cgst) / 100;
                        const cessAmount = (baseAmount * cess) / 100;
                        const calculatedAmount = baseAmount + sgstAmount + cgstAmount + cessAmount;
                        
                        const mappedItem = {
                            id: item.id?.toString() || Date.now().toString(),
                            description: item.description || '',
                            hsn: item.hsn_sac || item.hsn || '',
                            qty: qty,
                            rate: rate,
                            sgstPercent: sgst,
                            cgstPercent: cgst,
                            cessPercent: cess,
                            amount: calculatedAmount || parseFloat(String(item.amount || 0))
                        };
                        return mappedItem;
                    });
                    setInvoiceItems(mappedItems);
                } else {
                    // If no items, reset to empty array
                    setInvoiceItems([]);
                }
            }
        } catch (error: any) {
            console.error("Error fetching invoice:", error);
            toast.error(error.response?.data?.message || "Failed to fetch invoice");
        } finally {
            setLoading(false);
        }
    };

    const handleSaveInvoice = async (status: 'draft' | 'sent' = 'draft') => {
        try {
            // Validation
            if (!businessName || !clientName) {
                toast.error("Please fill in business name and client name");
                return;
            }
            
            if (invoiceItems.length === 0 || invoiceItems.some(item => !item.description)) {
                toast.error("Please add at least one item with description");
                return;
            }

            if (!invoiceDate || !dueDate) {
                toast.error("Please select invoice date and due date");
                return;
            }

            setLoading(true);
            const token = sessionStorage.getItem("access_token");
            const admin_id = getAdminIdForApi();
            
            if (!admin_id) {
                toast.error("Admin ID not found. Please login again.");
                setLoading(false);
                return;
            }

            const totals = calculateTotals();
            
            // Prepare items array
            const itemsArray = invoiceItems.map(item => ({
                description: item.description || '',
                hsn_sac: item.hsn || '',
                quantity: item.qty || 0,
                rate: item.rate || 0,
                sgst_percent: item.sgstPercent || 0,
                cgst_percent: item.cgstPercent || 0,
                cess_percent: item.cessPercent || 0,
                amount: item.amount || 0
            }));

            // Create FormData for file upload
            const formData = new FormData();
            
            // Append all fields to FormData
            formData.append('invoice_date', invoiceDate.format('YYYY-MM-DD'));
            formData.append('due_date', dueDate.format('YYYY-MM-DD'));
            formData.append('status', status);
            formData.append('theme_color', selectedTheme);
            formData.append('business_name', businessName);
            formData.append('business_contact_name', businessContactName || '');
            formData.append('business_gstin', businessGstin || '');
            formData.append('business_address_line1', businessAddressLine1 || '');
            formData.append('business_city', businessCity || '');
            formData.append('business_state', businessState === 'Select State' ? '' : businessState);
            formData.append('business_country', businessCountry);
            formData.append('business_pincode', businessPincode || '');
            formData.append('client_name', clientName);
            formData.append('client_gstin', clientGstin || '');
            formData.append('client_address_line1', clientAddressLine1 || '');
            formData.append('client_city', clientCity || '');
            formData.append('client_state', clientState === 'Select State' ? '' : clientState);
            formData.append('client_country', clientCountry);
            formData.append('client_pincode', clientPincode || '');
            formData.append('place_of_supply', placeOfSupply === 'Select State' ? '' : placeOfSupply);
            formData.append('sub_total', totals.subTotal.toString());
            formData.append('total_sgst', totals.totalSGST.toString());
            formData.append('total_cgst', totals.totalCGST.toString());
            formData.append('total_cess', (totals.totalCess || 0).toString());
            formData.append('total_amount', totals.total.toString());
            formData.append('notes', notes || '');
            formData.append('terms_and_conditions', termsAndConditions || '');
            
            // Append items as JSON string
            formData.append('items', JSON.stringify(itemsArray));

            // Append logo file if selected
            if (businessLogo) {
                formData.append('business_logo', businessLogo);
            }

            let response;
            if (id) {
                // Update existing invoice
                response = await axios.put(
                    `http://127.0.0.1:8000/api/invoices/${admin_id}/${id}`,
                    formData,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                            'Content-Type': 'multipart/form-data',
                        },
                    }
                );
                toast.success(response.data.message || "Invoice updated successfully");
            } else {
                // Create new invoice
                response = await axios.post(
                    `http://127.0.0.1:8000/api/invoices/${admin_id}`,
                    formData,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                            'Content-Type': 'multipart/form-data',
                        },
                    }
                );
                toast.success(response.data.message || "Invoice created successfully");
            }

            // Navigate to invoice list after successful save
            setTimeout(() => {
                navigate(all_routes.invoices);
            }, 1500);
        } catch (error: any) {
            console.error("Error saving invoice:", error);
            toast.error(error.response?.data?.message || "Failed to save invoice");
        } finally {
            setLoading(false);
        }
    };

    const stateOptions = [
        { value: "Select State", label: "Select State" },
        { value: "Andhra Pradesh", label: "Andhra Pradesh" },
        { value: "Arunachal Pradesh", label: "Arunachal Pradesh" },
        { value: "Assam", label: "Assam" },
        { value: "Bihar", label: "Bihar" },
        { value: "Chhattisgarh", label: "Chhattisgarh" },
        { value: "Goa", label: "Goa" },
        { value: "Gujarat", label: "Gujarat" },
        { value: "Haryana", label: "Haryana" },
        { value: "Himachal Pradesh", label: "Himachal Pradesh" },
        { value: "Jharkhand", label: "Jharkhand" },
        { value: "Karnataka", label: "Karnataka" },
        { value: "Kerala", label: "Kerala" },
        { value: "Madhya Pradesh", label: "Madhya Pradesh" },
        { value: "Maharashtra", label: "Maharashtra" },
        { value: "Manipur", label: "Manipur" },
        { value: "Meghalaya", label: "Meghalaya" },
        { value: "Mizoram", label: "Mizoram" },
        { value: "Nagaland", label: "Nagaland" },
        { value: "Odisha", label: "Odisha" },
        { value: "Punjab", label: "Punjab" },
        { value: "Rajasthan", label: "Rajasthan" },
        { value: "Sikkim", label: "Sikkim" },
        { value: "Tamil Nadu", label: "Tamil Nadu" },
        { value: "Telangana", label: "Telangana" },
        { value: "Tripura", label: "Tripura" },
        { value: "Uttar Pradesh", label: "Uttar Pradesh" },
        { value: "Uttarakhand", label: "Uttarakhand" },
        { value: "West Bengal", label: "West Bengal" },
        { value: "Andaman and Nicobar Islands", label: "Andaman and Nicobar Islands" },
        { value: "Chandigarh", label: "Chandigarh" },
        { value: "Dadra and Nagar Haveli and Daman and Diu", label: "Dadra and Nagar Haveli and Daman and Diu" },
        { value: "Delhi", label: "Delhi" },
        { value: "Jammu and Kashmir", label: "Jammu and Kashmir" },
        { value: "Ladakh", label: "Ladakh" },
        { value: "Lakshadweep", label: "Lakshadweep" },
        { value: "Puducherry", label: "Puducherry" }
    ];

    return (
        <>
            <style>{`
                .invoice-theme-selector {
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }
                .theme-selector-label {
                    font-weight: 600;
                    color: #495057;
                    font-size: 14px;
                    margin-bottom: 4px;
                }
                .theme-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(36px, 1fr));
                    gap: 10px;
                    max-width: 500px;
                    padding: 12px;
                    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                    border-radius: 10px;
                    border: 1px solid #e9ecef;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                }
                .theme-circle {
                    width: 36px;
                    height: 36px;
                    border-radius: 50%;
                    cursor: pointer;
                    border: 3px solid transparent;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    position: relative;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                }
                .theme-circle::before {
                    content: '';
                    position: absolute;
                    inset: -2px;
                    border-radius: 50%;
                    padding: 2px;
                    background: linear-gradient(45deg, transparent, rgba(255,255,255,0.3), transparent);
                    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
                    -webkit-mask-composite: xor;
                    mask-composite: exclude;
                    opacity: 0;
                    transition: opacity 0.3s;
                }
                .theme-circle:hover {
                    transform: scale(1.2) translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                }
                .theme-circle:hover::before {
                    opacity: 1;
                }
                .theme-circle.active {
                    border-color: #212529;
                    transform: scale(1.3);
                    box-shadow: 0 0 0 4px rgba(0,0,0,0.1), 0 6px 16px rgba(0,0,0,0.2), 0 0 0 8px rgba(0,0,0,0.05);
                    z-index: 10;
                }
                .theme-circle.active::after {
                    content: '✓';
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.4);
                    animation: checkmark 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                }
                @keyframes checkmark {
                    0% {
                        transform: translate(-50%, -50%) scale(0);
                        opacity: 0;
                    }
                    50% {
                        transform: translate(-50%, -50%) scale(1.2);
                    }
                    100% {
                        transform: translate(-50%, -50%) scale(1);
                        opacity: 1;
                    }
                }
                .tax-invoice-header {
                    background: linear-gradient(135deg, ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'} 0%, ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'}dd 100%);
                    color: white;
                    padding: 35px;
                    border-radius: 12px 12px 0 0;
                    box-shadow: 0 6px 24px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.08);
                    position: relative;
                    overflow: hidden;
                }
                .tax-invoice-header::before {
                    content: '';
                    position: absolute;
                    top: -50%;
                    right: -50%;
                    width: 200%;
                    height: 200%;
                    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                    animation: shimmer 3s infinite;
                }
                @keyframes shimmer {
                    0%, 100% {
                        transform: rotate(0deg);
                    }
                    50% {
                        transform: rotate(180deg);
                    }
                }
                .tax-invoice-title {
                    font-size: 42px;
                    font-weight: 900;
                    margin: 0;
                    text-align: right;
                    letter-spacing: 2px;
                    text-shadow: 0 3px 6px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2);
                    position: relative;
                    z-index: 1;
                    background: linear-gradient(135deg, rgba(255,255,255,1) 0%, rgba(255,255,255,0.9) 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }
                .invoice-form-container {
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1), 0 4px 16px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.04);
                    overflow: hidden;
                    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                    border: 1px solid rgba(0,0,0,0.05);
                    position: relative;
                    max-width: 1200px;
                    margin: 0 auto;
                }
                .invoice-form-container::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 4px;
                    background: linear-gradient(90deg, ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'}, ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'}dd);
                    opacity: 0;
                    transition: opacity 0.3s;
                }
                .invoice-form-container:hover {
                    box-shadow: 0 12px 48px rgba(0,0,0,0.15), 0 6px 24px rgba(0,0,0,0.1), 0 4px 12px rgba(0,0,0,0.08);
                    transform: translateY(-2px);
                }
                .invoice-form-container:hover::before {
                    opacity: 1;
                }
                .invoice-section-label {
                    font-weight: 700;
                    color: ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'};
                    margin-bottom: 14px;
                    font-size: 14px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                .logo-upload-box {
                    width: 130px;
                    height: 130px;
                    border: 2px dashed #ddd;
                    border-radius: 10px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                    position: relative;
                    overflow: hidden;
                }
                .logo-upload-box::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: -100%;
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
                    transition: left 0.5s;
                }
                .logo-upload-box:hover::before {
                    left: 100%;
                }
                .logo-upload-box:hover {
                    border-color: ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'};
                    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                }
                .items-table {
                    width: 100%;
                    border-collapse: separate;
                    border-spacing: 0;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.04);
                    background: white;
                }
                .items-table thead {
                    background: linear-gradient(135deg, ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'} 0%, ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'}dd 100%);
                    color: white;
                    position: relative;
                }
                .items-table thead::after {
                    content: '';
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    height: 2px;
                    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
                }
                .items-table thead th {
                    padding: 16px 12px;
                    text-align: left;
                    font-weight: 700;
                    font-size: 13px;
                    border: none;
                    white-space: nowrap;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    position: relative;
                }
                .items-table thead th:not(:last-child)::after {
                    content: '';
                    position: absolute;
                    right: 0;
                    top: 20%;
                    height: 60%;
                    width: 1px;
                    background: rgba(255,255,255,0.2);
                }
                .items-table thead th:first-child {
                    border-radius: 8px 0 0 0;
                }
                .items-table thead th:last-child {
                    border-radius: 0 8px 0 0;
                }
                .items-table tbody tr {
                    transition: all 0.2s ease;
                    animation: slideIn 0.3s ease-out;
                }
                .items-table tbody tr:hover {
                    background-color: #f8f9fa;
                    transform: scale(1.001);
                }
                @keyframes slideIn {
                    from {
                        opacity: 0;
                        transform: translateX(-10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }
                .items-table tbody td {
                    padding: 12px 10px;
                    border: 1px solid #e9ecef;
                    border-top: none;
                    background: white;
                }
                .items-table tbody tr:first-child td {
                    border-top: 1px solid #e9ecef;
                }
                .items-table tbody input {
                    border: none;
                    width: 100%;
                    padding: 6px 8px;
                    font-size: 13px;
                    background: transparent;
                    transition: all 0.2s;
                }
                .items-table tbody input:focus {
                    outline: 2px solid ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'};
                    outline-offset: -2px;
                    background: #fff;
                    border-radius: 4px;
                }
                .total-section {
                    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                    padding: 24px;
                    border-radius: 12px;
                    border: 2px solid #e9ecef;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.08), inset 0 1px 0 rgba(255,255,255,0.8);
                    position: relative;
                    overflow: hidden;
                }
                .total-section::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 3px;
                    background: linear-gradient(90deg, ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'}, ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'}dd);
                }
                .total-button {
                    background: linear-gradient(135deg, ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'} 0%, ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'}dd 100%);
                    color: white;
                    border: none;
                    padding: 20px 32px;
                    border-radius: 12px;
                    font-size: 22px;
                    font-weight: 800;
                    width: 100%;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    cursor: pointer;
                    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.2), 0 2px 8px rgba(0,0,0,0.1);
                    letter-spacing: 1px;
                    position: relative;
                    overflow: hidden;
                }
                .total-button::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: -100%;
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                    transition: left 0.5s;
                }
                .total-button:hover::before {
                    left: 100%;
                }
                .total-button:hover {
                    transform: translateY(-4px) scale(1.02);
                    box-shadow: 0 8px 28px rgba(0,0,0,0.3), 0 4px 12px rgba(0,0,0,0.15);
                }
                .total-button:active {
                    transform: translateY(-2px) scale(1.01);
                }
                .add-line-item-btn {
                    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                    border: 2px solid #dee2e6;
                    padding: 12px 20px;
                    border-radius: 8px;
                    color: #495057;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 14px;
                }
                .add-line-item-btn:hover {
                    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                    border-color: ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'};
                    color: ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'};
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                }
                .notes-heading, .terms-heading {
                    font-weight: 800;
                    color: #fd7e14;
                    margin-bottom: 14px;
                    font-size: 18px;
                    letter-spacing: 0.5px;
                    text-transform: uppercase;
                    position: relative;
                    padding-left: 12px;
                }
                .notes-heading::before, .terms-heading::before {
                    content: '';
                    position: absolute;
                    left: 0;
                    top: 50%;
                    transform: translateY(-50%);
                    width: 4px;
                    height: 20px;
                    background: linear-gradient(135deg, #fd7e14, #ff9500);
                    border-radius: 2px;
                }
                .notes-textarea, .terms-textarea {
                    border: 2px solid #dee2e6;
                    border-radius: 10px;
                    padding: 14px;
                    font-size: 14px;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    resize: vertical;
                    font-family: inherit;
                    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                    min-height: 100px;
                }
                .notes-textarea:focus, .terms-textarea:focus {
                    border-color: ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'};
                    outline: none;
                    box-shadow: 0 0 0 4px ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'}20, 0 4px 12px rgba(0,0,0,0.1);
                    background: #ffffff;
                    transform: translateY(-1px);
                }
                .footer-text {
                    color: #6c757d;
                    font-size: 13px;
                    font-style: italic;
                }
                .footer-link {
                    color: #0d6efd;
                    text-decoration: none;
                    font-weight: 600;
                    transition: all 0.2s;
                }
                .footer-link:hover {
                    color: #0a58ca;
                    text-decoration: underline;
                }
                .form-control-sm {
                    transition: all 0.2s ease;
                }
                .form-control-sm:focus {
                    border-color: ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'};
                    box-shadow: 0 0 0 3px ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'}20, 0 2px 8px rgba(0,0,0,0.1);
                    transform: translateY(-1px);
                }
                .invoice-section-card {
                    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                    border-radius: 12px;
                    padding: 20px;
                    border: 1px solid #e9ecef;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
                    transition: all 0.3s ease;
                    margin-bottom: 20px;
                }
                .invoice-section-card:hover {
                    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
                    transform: translateY(-2px);
                }
                .step-indicator {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 24px;
                    padding: 16px;
                    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                    border-radius: 12px;
                    border: 1px solid #e9ecef;
                }
                .step-item {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 8px 16px;
                    border-radius: 8px;
                    background: white;
                    border: 2px solid #dee2e6;
                    font-weight: 600;
                    font-size: 14px;
                    color: #6c757d;
                    transition: all 0.3s;
                }
                .step-item.active {
                    background: linear-gradient(135deg, ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'}, ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'}dd);
                    color: white;
                    border-color: ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'};
                    box-shadow: 0 4px 12px ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'}40;
                }
                .step-connector {
                    width: 40px;
                    height: 2px;
                    background: #dee2e6;
                    border-radius: 2px;
                }
                @keyframes fadeIn {
                    from {
                        opacity: 0;
                        transform: translateY(10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                .invoice-form-container {
                    animation: fadeIn 0.5s ease-out;
                }
                .date-picker-white {
                    background: rgba(255,255,255,0.15) !important;
                    border: 1px solid rgba(255,255,255,0.3) !important;
                    color: white !important;
                    backdrop-filter: blur(10px);
                }
                .date-picker-white::placeholder {
                    color: rgba(255,255,255,0.7) !important;
                }
                .date-picker-white:focus {
                    background: rgba(255,255,255,0.25) !important;
                    border-color: rgba(255,255,255,0.5) !important;
                    box-shadow: 0 0 0 3px rgba(255,255,255,0.2) !important;
                }
                .date-picker-white input {
                    color: white !important;
                }
                .form-control-sm {
                    border-radius: 6px;
                }
                .form-control-sm:focus {
                    transform: translateY(-1px);
                }
                .btn-primary {
                    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15), 0 2px 6px rgba(0,0,0,0.1);
                    font-weight: 600;
                    letter-spacing: 0.3px;
                    position: relative;
                    overflow: hidden;
                }
                .btn-primary::before {
                    content: '';
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    width: 0;
                    height: 0;
                    border-radius: 50%;
                    background: rgba(255,255,255,0.3);
                    transform: translate(-50%, -50%);
                    transition: width 0.6s, height 0.6s;
                }
                .btn-primary:hover::before {
                    width: 300px;
                    height: 300px;
                }
                .btn-primary:hover {
                    transform: translateY(-3px) scale(1.02);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.2), 0 4px 12px rgba(0,0,0,0.15);
                }
                .btn-primary:active {
                    transform: translateY(-1px) scale(1.01);
                }
                .btn-outline-primary, .btn-outline-secondary {
                    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                    font-weight: 600;
                    letter-spacing: 0.3px;
                    border-width: 2px;
                }
                .btn-outline-primary:hover {
                    transform: translateY(-3px) scale(1.02);
                    box-shadow: 0 6px 20px rgba(13, 110, 253, 0.25), 0 4px 12px rgba(13, 110, 253, 0.15);
                    border-width: 2px;
                }
                .btn-outline-secondary:hover {
                    transform: translateY(-3px) scale(1.02);
                    box-shadow: 0 6px 20px rgba(108, 117, 125, 0.25), 0 4px 12px rgba(108, 117, 125, 0.15);
                    border-width: 2px;
                }
                .btn-outline-primary:active, .btn-outline-secondary:active {
                    transform: translateY(-1px) scale(1.01);
                }
                @keyframes pulse {
                    0%, 100% {
                        opacity: 1;
                    }
                    50% {
                        opacity: 0.7;
                    }
                }
                .invoice-section-label {
                    animation: fadeIn 0.5s ease-out;
                }
                .card {
                    border: none;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.04);
                    border-radius: 12px;
                    transition: all 0.3s ease;
                }
                .card:hover {
                    box-shadow: 0 8px 24px rgba(0,0,0,0.12), 0 4px 12px rgba(0,0,0,0.06);
                    transform: translateY(-2px);
                }
                .btn-link.text-danger {
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    border-radius: 6px;
                    padding: 4px 8px;
                }
                .btn-link.text-danger:hover {
                    background: rgba(220, 53, 69, 0.1);
                    transform: scale(1.1);
                    box-shadow: 0 2px 8px rgba(220, 53, 69, 0.2);
                }
                .btn-link.text-danger:active {
                    transform: scale(0.95);
                }
                .breadcrumb {
                    background: transparent;
                    padding: 0;
                }
                .breadcrumb-item a {
                    transition: all 0.2s;
                    color: #6c757d;
                }
                .breadcrumb-item a:hover {
                    color: ${themes.find(t => t.name === selectedTheme)?.color || '#dc3545'};
                    transform: translateX(2px);
                }
            `}</style>

            <div className="page-wrapper">
                <div className="content">
                    {/* Breadcrumb */}
                    <div className="d-md-flex d-block align-items-center justify-content-between page-breadcrumb mb-3">
                        <div className="my-auto mb-2">
                            <h2 className="mb-1">Create Tax Invoice</h2>
                            <nav>
                                <ol className="breadcrumb mb-0">
                                    <li className="breadcrumb-item">
                                        <Link to={all_routes.adminDashboard}>
                                            <i className="ti ti-smart-home" />
                                        </Link>
                                    </li>
                                    <li className="breadcrumb-item">
                                        <Link to={all_routes.invoices}>Invoices</Link>
                                    </li>
                                    <li className="breadcrumb-item active" aria-current="page">
                                        Create Invoice
                                    </li>
                                </ol>
                            </nav>
                        </div>
                    </div>

                    <div className="row justify-content-center">
                        <div className="col-xl-10 col-lg-11 col-md-12">
                            <div className="invoice-form-container">
                                {/* Header with Theme Selector and Save Button */}
                                <div className="d-flex justify-content-between align-items-center p-3 border-bottom bg-white">
                                    <div className="invoice-theme-selector">
                                        <div className="theme-selector-label">Choose Theme Color:</div>
                                        <div className="theme-grid">
                                            {themes.map((theme) => (
                                                <div
                                                    key={theme.name}
                                                    className={`theme-circle ${selectedTheme === theme.name ? 'active' : ''}`}
                                                    style={{ backgroundColor: theme.color }}
                                                    onClick={() => setSelectedTheme(theme.name)}
                                                    title={theme.name.charAt(0).toUpperCase() + theme.name.slice(1)}
                                                />
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                {/* Tax Invoice Title Section */}
                                <div className="tax-invoice-header">
                                    <div className="row align-items-center">
                                        <div className="col-md-6">
                                            <div className="d-flex align-items-center gap-3">
                                                <div className="logo-upload-box position-relative">
                                                    <input
                                                        type="file"
                                                        accept="image/*"
                                                        className="position-absolute w-100 h-100 opacity-0"
                                                        style={{ cursor: 'pointer', zIndex: 10 }}
                                                        onChange={(e) => {
                                                            const file = e.target.files?.[0];
                                                            if (file) {
                                                                setBusinessLogo(file);
                                                                const reader = new FileReader();
                                                                reader.onloadend = () => {
                                                                    setBusinessLogoPreview(reader.result as string);
                                                                };
                                                                reader.readAsDataURL(file);
                                                            }
                                                        }}
                                                    />
                                                    {businessLogoPreview ? (
                                                        <img 
                                                            src={businessLogoPreview} 
                                                            alt="Logo" 
                                                            style={{ 
                                                                width: '100%', 
                                                                height: '100%', 
                                                                objectFit: 'contain',
                                                                borderRadius: '8px'
                                                            }} 
                                                        />
                                                    ) : (
                                                        <>
                                                            <i className="ti ti-cloud-upload fs-24 mb-2" style={{ color: '#999' }} />
                                                            <span className="fs-12 text-muted">Click to Upload Logo</span>
                                                        </>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="col-md-6">
                                            <h1 className="tax-invoice-title">TAX INVOICE</h1>
                                            <div className="row mt-3">
                                                <div className="col-md-4 mb-2">
                                                    <label className="text-white-50 fs-12 mb-1 d-block">Invoice #</label>
                                                    <input 
                                                        type="text" 
                                                        className="form-control form-control-sm" 
                                                        value={invoiceNumber}
                                                        readOnly
                                                        style={{ background: 'rgba(255,255,255,0.2)', border: '1px solid rgba(255,255,255,0.3)', color: 'white' }}
                                                        placeholder="Auto-generated"
                                                    />
                                                </div>
                                                <div className="col-md-4 mb-2">
                                                    <label className="text-white-50 fs-12 mb-1 d-block fw-medium">Date</label>
                                                    <div className="position-relative">
                                                        <DatePicker
                                                            className="form-control form-control-sm date-picker-white"
                                                            value={invoiceDate}
                                                            onChange={(date) => setInvoiceDate(date)}
                                                            format={{
                                                                format: "DD-MM-YYYY",
                                                                type: "mask",
                                                            }}
                                                            getPopupContainer={getModalContainer}
                                                            placeholder="dd-mm-yyyy"
                                                        />
                                                        <i className="ti ti-calendar position-absolute" style={{ right: '10px', top: '50%', transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.8)', pointerEvents: 'none' }} />
                                                    </div>
                                                </div>
                                                <div className="col-md-4 mb-2">
                                                    <label className="text-white-50 fs-12 mb-1 d-block fw-medium">Due Date</label>
                                                    <div className="position-relative">
                                                        <DatePicker
                                                            className="form-control form-control-sm date-picker-white"
                                                            value={dueDate}
                                                            onChange={(date) => setDueDate(date)}
                                                            format={{
                                                                format: "DD-MM-YYYY",
                                                                type: "mask",
                                                            }}
                                                            getPopupContainer={getModalContainer}
                                                            placeholder="dd-mm-yyyy"
                                                        />
                                                        <i className="ti ti-calendar position-absolute" style={{ right: '10px', top: '50%', transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.8)', pointerEvents: 'none' }} />
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Main Content */}
                                <div className="p-4">
                                    <div className="row">
                                        {/* Left Column - Company & Bill To */}
                                        <div className="col-md-6">
                                            {/* Company Details */}
                                            <div className="mb-4">
                                                <div className="invoice-section-label">Your Company Details</div>
                                                <div className="row g-2">
                                                    <div className="col-12">
                                                        <input 
                                                            type="text" 
                                                            className="form-control form-control-sm" 
                                                            placeholder="Your Company Name" 
                                                            value={businessName}
                                                            onChange={(e) => setBusinessName(e.target.value)}
                                                        />
                                                    </div>
                                                    <div className="col-12">
                                                        <input 
                                                            type="text" 
                                                            className="form-control form-control-sm" 
                                                            placeholder="Your Name" 
                                                            value={businessContactName}
                                                            onChange={(e) => setBusinessContactName(e.target.value)}
                                                        />
                                                    </div>
                                                    <div className="col-12">
                                                        <input 
                                                            type="text" 
                                                            className="form-control form-control-sm" 
                                                            placeholder="GSTIN" 
                                                            value={businessGstin}
                                                            onChange={(e) => setBusinessGstin(e.target.value)}
                                                        />
                                                    </div>
                                                    <div className="col-12">
                                                        <input 
                                                            type="text" 
                                                            className="form-control form-control-sm" 
                                                            placeholder="Address Line 1" 
                                                            value={businessAddressLine1}
                                                            onChange={(e) => setBusinessAddressLine1(e.target.value)}
                                                        />
                                                    </div>
                                                    <div className="col-12">
                                                        <input 
                                                            type="text" 
                                                            className="form-control form-control-sm" 
                                                            placeholder="City" 
                                                            value={businessCity}
                                                            onChange={(e) => setBusinessCity(e.target.value)}
                                                        />
                                                    </div>
                                                    <div className="col-md-6">
                                                        <CommonSelect
                                                            key={`business-state-${businessState}`}
                                                            className='select'
                                                            options={stateOptions}
                                                            defaultValue={stateOptions.find(opt => opt.value === businessState) || stateOptions[0]}
                                                            onChange={(option: any) => setBusinessState(option?.value || 'Select State')}
                                                        />
                                                    </div>
                                                    <div className="col-md-6">
                                                        <CommonSelect
                                                            key={`business-country-${businessCountry}`}
                                                            className='select'
                                                            options={[{ value: "India", label: "India" }]}
                                                            defaultValue={{ value: businessCountry, label: businessCountry }}
                                                            onChange={(option: any) => setBusinessCountry(option?.value || 'India')}
                                                        />
                                                    </div>
                                                    <div className="col-12">
                                                        <input 
                                                            type="text" 
                                                            className="form-control form-control-sm" 
                                                            placeholder="Pincode" 
                                                            value={businessPincode}
                                                            onChange={(e) => setBusinessPincode(e.target.value)}
                                                        />
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Bill To Section */}
                                            <div>
                                                <div className="invoice-section-label">BILL TO:</div>
                                                <div className="row g-2">
                                                    <div className="col-12">
                                                        <input 
                                                            type="text" 
                                                            className="form-control form-control-sm" 
                                                            placeholder="Customer Name" 
                                                            value={clientName}
                                                            onChange={(e) => setClientName(e.target.value)}
                                                        />
                                                    </div>
                                                    <div className="col-12">
                                                        <input 
                                                            type="text" 
                                                            className="form-control form-control-sm" 
                                                            placeholder="Customer GSTIN" 
                                                            value={clientGstin}
                                                            onChange={(e) => setClientGstin(e.target.value)}
                                                        />
                                                    </div>
                                                    <div className="col-12">
                                                        <input 
                                                            type="text" 
                                                            className="form-control form-control-sm" 
                                                            placeholder="Address Line 1" 
                                                            value={clientAddressLine1}
                                                            onChange={(e) => setClientAddressLine1(e.target.value)}
                                                        />
                                                    </div>
                                                    <div className="col-12">
                                                        <input 
                                                            type="text" 
                                                            className="form-control form-control-sm" 
                                                            placeholder="City" 
                                                            value={clientCity}
                                                            onChange={(e) => setClientCity(e.target.value)}
                                                        />
                                                    </div>
                                                    <div className="col-md-6">
                                                        <CommonSelect
                                                            key={`client-state-${clientState}`}
                                                            className='select'
                                                            options={stateOptions}
                                                            defaultValue={stateOptions.find(opt => opt.value === clientState) || stateOptions[0]}
                                                            onChange={(option: any) => setClientState(option?.value || 'Select State')}
                                                        />
                                                    </div>
                                                    <div className="col-md-6">
                                                        <CommonSelect
                                                            key={`client-country-${clientCountry}`}
                                                            className='select'
                                                            options={[{ value: "India", label: "India" }]}
                                                            defaultValue={{ value: clientCountry, label: clientCountry }}
                                                            onChange={(option: any) => setClientCountry(option?.value || 'India')}
                                                        />
                                                    </div>
                                                    <div className="col-12">
                                                        <input 
                                                            type="text" 
                                                            className="form-control form-control-sm" 
                                                            placeholder="Pincode" 
                                                            value={clientPincode}
                                                            onChange={(e) => setClientPincode(e.target.value)}
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Right Column - Place of Supply */}
                                        <div className="col-md-6">
                                            <div className="mb-4">
                                                <div className="invoice-section-label">PLACE OF SUPPLY:</div>
                                                <CommonSelect
                                                    key={`place-of-supply-${placeOfSupply}`}
                                                    className='select'
                                                    options={stateOptions}
                                                    defaultValue={stateOptions.find(opt => opt.value === placeOfSupply) || stateOptions[0]}
                                                    onChange={(option: any) => setPlaceOfSupply(option?.value || 'Select State')}
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    {/* Items Table */}
                                    <div className="mt-4">
                                        <table className="items-table">
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
                                                    <th style={{ width: '50px' }}></th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {invoiceItems.map((item) => (
                                                    <tr key={item.id}>
                                                        <td>
                                                            <input
                                                                type="text"
                                                                value={item.description}
                                                                onChange={(e) => updateItem(item.id, 'description', e.target.value)}
                                                                placeholder="Item description"
                                                            />
                                                        </td>
                                                        <td>
                                                            <input
                                                                type="text"
                                                                value={item.hsn}
                                                                onChange={(e) => updateItem(item.id, 'hsn', e.target.value)}
                                                                placeholder="HSN"
                                                            />
                                                        </td>
                                                        <td>
                                                            <input
                                                                type="number"
                                                                value={item.qty}
                                                                onChange={(e) => updateItem(item.id, 'qty', parseFloat(e.target.value) || 0)}
                                                                placeholder="1"
                                                            />
                                                        </td>
                                                        <td>
                                                            <input
                                                                type="number"
                                                                value={item.rate}
                                                                onChange={(e) => updateItem(item.id, 'rate', parseFloat(e.target.value) || 0)}
                                                                placeholder="120"
                                                            />
                                                        </td>
                                                        <td>
                                                            <div>
                                                                <input
                                                                    type="number"
                                                                    value={item.sgstPercent !== undefined && item.sgstPercent !== null ? item.sgstPercent : ''}
                                                                    onChange={(e) => updateItem(item.id, 'sgstPercent', parseFloat(e.target.value) || 0)}
                                                                    placeholder="9"
                                                                    style={{ width: '50px', marginBottom: '4px' }}
                                                                />
                                                                <div className="fs-12 text-muted">₹{((item.qty * item.rate * item.sgstPercent) / 100).toFixed(2)}</div>
                                                            </div>
                                                        </td>
                                                        <td>
                                                            <div>
                                                                <input
                                                                    type="number"
                                                                    value={item.cgstPercent !== undefined && item.cgstPercent !== null ? item.cgstPercent : ''}
                                                                    onChange={(e) => updateItem(item.id, 'cgstPercent', parseFloat(e.target.value) || 0)}
                                                                    placeholder="9"
                                                                    style={{ width: '50px', marginBottom: '4px' }}
                                                                />
                                                                <div className="fs-12 text-muted">₹{((item.qty * item.rate * item.cgstPercent) / 100).toFixed(2)}</div>
                                                            </div>
                                                        </td>
                                                        <td>
                                                            <div>
                                                                <input
                                                                    type="number"
                                                                    value={item.cessPercent !== undefined && item.cessPercent !== null ? item.cessPercent : ''}
                                                                    onChange={(e) => updateItem(item.id, 'cessPercent', parseFloat(e.target.value) || 0)}
                                                                    placeholder="0"
                                                                    style={{ width: '50px', marginBottom: '4px' }}
                                                                />
                                                                <div className="fs-12 text-muted">₹{((item.qty * item.rate * item.cessPercent) / 100).toFixed(2)}</div>
                                                            </div>
                                                        </td>
                                                        <td>
                                                            <div className="fw-medium">₹{item.amount.toFixed(2)}</div>
                                                        </td>
                                                        <td className="text-center">
                                                            {invoiceItems.length > 1 && (
                                                                <button
                                                                    className="btn btn-sm btn-link text-danger p-0"
                                                                    onClick={() => removeItem(item.id)}
                                                                    title="Remove item"
                                                                >
                                                                    <i className="ti ti-trash fs-16" />
                                                                </button>
                                                            )}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                        <button className="add-line-item-btn mt-3" onClick={addNewItem}>
                                            <i className="ti ti-plus" />
                                            Add Line Item
                                        </button>
                                    </div>

                                    {/* Summary Section */}
                                    <div className="row mt-4">
                                        <div className="col-md-6"></div>
                                        <div className="col-md-6">
                                            <div className="total-section">
                                                <div className="d-flex justify-content-between mb-2">
                                                    <span className="fw-medium">Sub Total:</span>
                                                    <span className="fw-medium">₹{totals.subTotal.toFixed(2)}</span>
                                                </div>
                                                <div className="d-flex justify-content-between mb-2">
                                                    <span className="fw-medium">Total SGST:</span>
                                                    <span className="fw-medium">₹{totals.totalSGST.toFixed(2)}</span>
                                                </div>
                                                <div className="d-flex justify-content-between mb-2">
                                                    <span className="fw-medium">Total CGST:</span>
                                                    <span className="fw-medium">₹{totals.totalCGST.toFixed(2)}</span>
                                                </div>
                                                {(totals.totalCess || 0) > 0 && (
                                                    <div className="d-flex justify-content-between mb-2">
                                                        <span className="fw-medium">Total Cess:</span>
                                                        <span className="fw-medium">₹{(totals.totalCess || 0).toFixed(2)}</span>
                                                    </div>
                                                )}
                                                <button className="total-button">
                                                    <span>TOTAL:</span>
                                                    <span>₹{totals.total.toFixed(2)}</span>
                                                </button>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Notes Section */}
                                    <div className="mt-4">
                                        <h6 className="notes-heading">Notes:</h6>
                                        <textarea
                                            className="form-control notes-textarea"
                                            rows={4}
                                            placeholder="Add any additional notes here..."
                                            value={notes}
                                            onChange={(e) => setNotes(e.target.value)}
                                        />
                                    </div>

                                    {/* Terms & Conditions Section */}
                                    <div className="mt-4">
                                        <h6 className="terms-heading">Terms & Conditions:</h6>
                                        <textarea
                                            className="form-control terms-textarea"
                                            rows={4}
                                            placeholder="Payment terms and conditions..."
                                            value={termsAndConditions}
                                            onChange={(e) => setTermsAndConditions(e.target.value)}
                                        />
                                    </div>

                                    {/* Footer Text */}
                                    <div className="text-center mt-4 mb-3">
                                        <p className="footer-text mb-0">
                                            Generated using <Link to="#" className="footer-link">NeexQ Technology</Link>.
                                        </p>
                                    </div>

                                    {/* Action Buttons */}
                                    <div className="d-flex justify-content-between align-items-center mt-4 pt-3 border-top">
                                        <Link to={all_routes.invoices} className="btn btn-outline-secondary">
                                            <i className="ti ti-arrow-left me-2" />
                                            Back to List
                                        </Link>
                                        <div className="d-flex gap-2">
                                            <button 
                                                className="btn btn-primary"
                                                onClick={() => handleSaveInvoice('draft')}
                                                disabled={loading}
                                            >
                                                <i className="ti ti-device-floppy me-2" />
                                                {loading ? 'Saving...' : 'Save'}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                {/* Footer */}
                <div className="footer d-sm-flex align-items-center justify-content-between bg-white border-top p-3">
                    <p className="mb-0">2025 © NeexQ Technology.</p>
                    <p>
                        Designed &amp; Developed By{" "}
                        <Link to="#" className="text-primary">
                            Dreams
                        </Link>
                    </p>
                </div>
            </div>
            <ToastContainer position="top-right" autoClose={3000} />
        </>
    )
}

export default AddInvoice
