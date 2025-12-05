import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { all_routes } from "../router/all_routes";
import ImageWithBasePath from "../../core/common/imageWithBasePath";
import Table from "../../core/common/dataTable/index";
import { DatePicker } from "antd";
import dayjs, { Dayjs } from "dayjs";
import axios from "axios";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { getAdminIdForApi } from "../../core/utils/apiHelpers";

const Invoices = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [fromDate, setFromDate] = useState<Dayjs | null>(dayjs());
  const [toDate, setToDate] = useState<Dayjs | null>(dayjs());
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  
  // Statistics
  const [stats, setStats] = useState({
    totalInvoice: 0,
    outstanding: 0,
    draft: 0,
    totalOverdue: 0,
    totalInvoiceChange: 0,
    outstandingChange: 0,
    draftChange: 0,
    totalOverdueChange: 0,
  });

  const getModalContainer = () => {
    const modalElement = document.getElementById("modal-datepicker");
    return modalElement ? modalElement : document.body;
  };

  const fetchInvoices = useCallback(async () => {
    setLoading(true);
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = getAdminIdForApi();

      if (!admin_id) {
        const role = sessionStorage.getItem("role");
        if (role === "organization") {
          toast.error("Please select an admin first from the dashboard.");
        } else {
          toast.error("Admin ID not found. Please login again.");
        }
        setLoading(false);
        return;
      }

      let url = `http://127.0.0.1:8000/api/invoices/${admin_id}`;
      const params = new URLSearchParams();
      
      if (statusFilter) {
        params.append("status", statusFilter);
      }
      if (searchQuery) {
        params.append("search", searchQuery);
      }
      // Add date filters
      if (fromDate) {
        params.append("from_date", fromDate.format("YYYY-MM-DD"));
      }
      if (toDate) {
        params.append("to_date", toDate.format("YYYY-MM-DD"));
      }
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await axios.get(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      let invoices = [];
      let allInvoices = []; // For stats calculation
      
      if (response.data && response.data.data) {
        if (response.data.data.results && Array.isArray(response.data.data.results)) {
          invoices = response.data.data.results;
        } else if (Array.isArray(response.data.data)) {
          invoices = response.data.data;
        }
      }

      // Fetch all invoices for stats (without pagination)
      const statsUrl = `http://127.0.0.1:8000/api/invoices/${admin_id}?page_size=10000`;
      const statsParams = new URLSearchParams();
      if (statusFilter) {
        statsParams.append("status", statusFilter);
      }
      if (fromDate) {
        statsParams.append("from_date", fromDate.format("YYYY-MM-DD"));
      }
      if (toDate) {
        statsParams.append("to_date", toDate.format("YYYY-MM-DD"));
      }
      
      const statsUrlWithParams = statsParams.toString() 
        ? `${statsUrl}&${statsParams.toString()}` 
        : statsUrl;
      
      try {
        const statsResponse = await axios.get(statsUrlWithParams, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        
        if (statsResponse.data && statsResponse.data.data) {
          if (statsResponse.data.data.results && Array.isArray(statsResponse.data.data.results)) {
            allInvoices = statsResponse.data.data.results;
          } else if (Array.isArray(statsResponse.data.data)) {
            allInvoices = statsResponse.data.data;
          }
        }
      } catch (statsError) {
        console.error("Error fetching stats:", statsError);
        // Use current page invoices for stats if stats fetch fails
        allInvoices = invoices;
      }

      // Transform data for table
      const transformedData = invoices.map((invoice: any) => ({
        id: invoice.id,
        invoice_number: invoice.invoice_number || `INV-${invoice.id}`,
        client_name: invoice.client_name || "N/A",
        invoice_date: invoice.invoice_date ? dayjs(invoice.invoice_date).format("DD-MM-YYYY") : "N/A",
        due_date: invoice.due_date ? dayjs(invoice.due_date).format("DD-MM-YYYY") : "N/A",
        total_amount: invoice.total_amount || 0,
        status: invoice.status || "draft",
        created_at: invoice.created_at ? dayjs(invoice.created_at).format("DD-MM-YYYY") : "N/A",
      }));

      setData(transformedData);

      // Calculate statistics from all invoices
      calculateStats(allInvoices);
    } catch (error: any) {
      console.error("Error fetching invoices:", error);
      toast.error(error.response?.data?.message || "Failed to fetch invoices");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, searchQuery, fromDate, toDate]);

  const calculateStats = (invoices: any[]) => {
    const totalInvoice = invoices.length;
    const totalAmount = invoices.reduce((sum, inv) => sum + parseFloat(inv.total_amount || 0), 0);
    const outstanding = invoices
      .filter((inv) => inv.status === "sent")
      .reduce((sum, inv) => sum + parseFloat(inv.total_amount || 0), 0);
    const draft = invoices
      .filter((inv) => inv.status === "draft")
      .reduce((sum, inv) => sum + parseFloat(inv.total_amount || 0), 0);
    const totalOverdue = invoices
      .filter((inv) => inv.status === "overdue")
      .reduce((sum, inv) => sum + parseFloat(inv.total_amount || 0), 0);

    setStats({
      totalInvoice: totalAmount,
      outstanding: outstanding,
      draft: draft,
      totalOverdue: totalOverdue,
      totalInvoiceChange: 32.40,
      outstandingChange: -4.40,
      draftChange: 12,
      totalOverdueChange: -15.40,
    });
  };

  useEffect(() => {
    fetchInvoices();
  }, [fetchInvoices]);

  const handleDelete = async (invoiceId: number) => {
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = getAdminIdForApi();

      if (!admin_id) {
        toast.error("Admin ID not found.");
        return;
      }

      await axios.delete(
        `http://127.0.0.1:8000/api/invoices/${admin_id}/${invoiceId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      toast.success("Invoice deleted successfully");
      fetchInvoices();
    } catch (error: any) {
      console.error("Error deleting invoice:", error);
      toast.error(error.response?.data?.message || "Failed to delete invoice");
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case "paid":
        return "badge-soft-success";
      case "sent":
        return "badge-soft-purple";
      case "draft":
        return "badge-soft-warning";
      case "overdue":
        return "badge-soft-danger";
      default:
        return "badge-soft-secondary";
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const columns = [
    {
      title: "Invoice",
      dataIndex: "invoice_number",
      render: (text: string, record: any) => (
        <Link
          to={`${all_routes.editInvoice.replace(":id", record.id)}`}
          className="tb-data"
        >
          {text}
        </Link>
      ),
    },
    {
      title: "Client Name",
      dataIndex: "client_name",
      render: (text: string, record: any) => (
        <div>
          <h6 className="fw-medium">{text}</h6>
        </div>
      ),
    },
    {
      title: "Invoice Date",
      dataIndex: "invoice_date",
    },
    {
      title: "Due Date",
      dataIndex: "due_date",
    },
    {
      title: "Total",
      dataIndex: "total_amount",
      render: (amount: number) => formatCurrency(amount),
    },
    {
      title: "Status",
      dataIndex: "status",
      render: (text: string) => (
        <span
          className={`badge ${getStatusBadgeClass(text)} d-inline-flex align-items-center`}
        >
          <i className="ti ti-point-filled me-1" />
          {text.charAt(0).toUpperCase() + text.slice(1)}
        </span>
      ),
    },
    {
      title: "",
      dataIndex: "action",
      render: (text: string, record: any) => (
        <div className="action-icon d-inline-flex">
          <Link
            to={all_routes.invoiceDetails.replace(":id", record.id.toString())}
            className="me-2 text-primary"
            title="View Invoice"
          >
            <i className="ti ti-eye" />
          </Link>
          <Link
            to={`${all_routes.editInvoice.replace(":id", record.id)}`}
            className="me-2"
            title="Edit"
          >
            <i className="ti ti-edit" />
          </Link>
          <Link
            to="#"
            className="text-danger"
            onClick={(e) => {
              e.preventDefault();
              if (window.confirm("Are you sure you want to delete this invoice?")) {
                handleDelete(record.id);
              }
            }}
            title="Delete"
          >
            <i className="ti ti-trash" />
          </Link>
        </div>
      ),
    },
  ];

  return (
    <>
      {/* Page Wrapper */}
      <div className="page-wrapper">
        <div className="content">
          {/* Breadcrumb */}
          <div className="d-md-flex d-block align-items-center justify-content-between page-breadcrumb mb-3">
            <div className="my-auto mb-2">
              <h2 className="mb-1">Invoices</h2>
              <nav>
                <ol className="breadcrumb mb-0">
                  <li className="breadcrumb-item">
                    <Link to={all_routes.adminDashboard}>
                      <i className="ti ti-smart-home" />
                    </Link>
                  </li>
                  <li className="breadcrumb-item">Billing</li>
                  <li className="breadcrumb-item active" aria-current="page">
                    Invoices
                  </li>
                </ol>
              </nav>
            </div>
            <div className="d-flex my-xl-auto right-content align-items-center flex-wrap">
              <div className="mb-2">
                <Link
                  to={all_routes.addInvoice}
                  className="btn btn-primary d-flex align-items-center"
                >
                  <i className="ti ti-circle-plus me-2" />
                  Add Invoice
                </Link>
              </div>
            </div>
          </div>
          {/* /Breadcrumb */}
          {/* Invoice Data */}
          <div className="row">
            <div className="col-xl-3 col-sm-6">
              <div className="card flex-fill">
                <div className="card-body">
                  <div className="d-flex align-items-center overflow-hidden mb-2">
                    <div>
                      <p className="fs-12 fw-normal mb-1 text-truncate">
                        Total Invoice
                      </p>
                      <h5>{formatCurrency(stats.totalInvoice)}</h5>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="col-xl-3 col-sm-6">
              <div className="card flex-fill">
                <div className="card-body">
                  <div className="d-flex align-items-center overflow-hidden mb-2">
                    <div>
                      <p className="fs-12 fw-normal mb-1 text-truncate">
                        Outstanding
                      </p>
                      <h5>{formatCurrency(stats.outstanding)}</h5>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="col-xl-3 col-sm-6">
              <div className="card flex-fill">
                <div className="card-body">
                  <div className="d-flex align-items-center overflow-hidden mb-2">
                    <div>
                      <p className="fs-12 fw-normal mb-1 text-truncate">
                        Draft
                      </p>
                      <h5>{formatCurrency(stats.draft)}</h5>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="col-xl-3 col-sm-6">
              <div className="card flex-fill">
                <div className="card-body">
                  <div className="d-flex align-items-center overflow-hidden mb-2">
                    <div>
                      <p className="fs-12 fw-normal mb-1 text-truncate">
                        Total Overdue
                      </p>
                      <h5>{formatCurrency(stats.totalOverdue)}</h5>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          {/* /Invoice Data */}
          {/* Invoice DataTable */}
          <div className="row">
            <div className="col-sm-12">
              <div className="card">
                <div className="card-header d-flex align-items-center justify-content-between flex-wrap row-gap-3">
                  <h5 className="d-flex align-items-center">
                    Invoices
                    <span className="badge badge-dark-transparent ms-2">
                      {data.length} Invoices
                    </span>
                  </h5>
                  <div className="d-flex align-items-center flex-wrap row-gap-3">
                    <div className="input-icon position-relative w-120 me-2">
                      <span className="input-icon-addon">
                        <i className="ti ti-calendar" />
                      </span>
                      <DatePicker
                        className="form-control datetimepicker"
                        value={fromDate}
                        onChange={(date) => setFromDate(date)}
                        format={{
                          format: "DD-MM-YYYY",
                          type: "mask",
                        }}
                        getPopupContainer={getModalContainer}
                        placeholder="From Date"
                      />
                    </div>
                    <div className="input-icon position-relative w-120 me-2">
                      <span className="input-icon-addon">
                        <i className="ti ti-calendar" />
                      </span>
                      <DatePicker
                        className="form-control datetimepicker"
                        value={toDate}
                        onChange={(date) => setToDate(date)}
                        format={{
                          format: "DD-MM-YYYY",
                          type: "mask",
                        }}
                        getPopupContainer={getModalContainer}
                        placeholder="To Date"
                      />
                    </div>
                    <div className="input-icon position-relative me-2">
                      <span className="input-icon-addon">
                        <i className="ti ti-search" />
                      </span>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Search invoices..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        style={{ width: "200px" }}
                      />
                    </div>
                    <div className="dropdown me-2">
                      <Link
                        to="#"
                        className="dropdown-toggle btn btn-white d-inline-flex align-items-center"
                        data-bs-toggle="dropdown"
                      >
                        {statusFilter || "Select Status"}
                      </Link>
                      <ul className="dropdown-menu dropdown-menu-end p-3">
                        <li>
                          <Link
                            to="#"
                            className="dropdown-item rounded-1"
                            onClick={(e) => {
                              e.preventDefault();
                              setStatusFilter("");
                            }}
                          >
                            All Status
                          </Link>
                        </li>
                        <li>
                          <Link
                            to="#"
                            className="dropdown-item rounded-1"
                            onClick={(e) => {
                              e.preventDefault();
                              setStatusFilter("paid");
                            }}
                          >
                            Paid
                          </Link>
                        </li>
                        <li>
                          <Link
                            to="#"
                            className="dropdown-item rounded-1"
                            onClick={(e) => {
                              e.preventDefault();
                              setStatusFilter("overdue");
                            }}
                          >
                            Overdue
                          </Link>
                        </li>
                        <li>
                          <Link
                            to="#"
                            className="dropdown-item rounded-1"
                            onClick={(e) => {
                              e.preventDefault();
                              setStatusFilter("sent");
                            }}
                          >
                            Sent
                          </Link>
                        </li>
                        <li>
                          <Link
                            to="#"
                            className="dropdown-item rounded-1"
                            onClick={(e) => {
                              e.preventDefault();
                              setStatusFilter("draft");
                            }}
                          >
                            Draft
                          </Link>
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
                <div className="card-body p-0">
                  {loading ? (
                    <div className="text-center p-4">
                      <div className="spinner-border" role="status">
                        <span className="visually-hidden">Loading...</span>
                      </div>
                    </div>
                  ) : (
                    <Table dataSource={data} columns={columns} Selection={true} />
                  )}
                </div>
              </div>
            </div>
          </div>
          {/* /Invoice DataTable */}
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
        {/* /Footer */}
        {/* /Page Wrapper */}
      </div>
      <ToastContainer position="top-right" autoClose={3000} />
    </>
  );
};

export default Invoices;
