import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import CollapseHeader from "../../../core/common/collapse-header/collapse-header";
import { all_routes } from "../../router/all_routes";
import Table from "../../../core/common/dataTable/index";
import VisitModal from "./CreateModal";
import DeleteModal from "./deleteModal";
import CheckInOutModal from "./CheckInOutModal";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { getAdminIdForApi } from "../../../core/utils/apiHelpers";

const getVisitKey = (visit: any) => visit?.id ?? null;

const normalizeVisitId = (value: any): string | null => {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  return String(value);
};

const Visits = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [visitIdToDelete, setVisitIdToDelete] = useState<string | null>(null);
  const [editingVisit, setEditingVisit] = useState<any>(null);
  const [checkInOutVisit, setCheckInOutVisit] = useState<any>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [selectedUserId, setSelectedUserId] = useState<string>("");
  const [fromDate, setFromDate] = useState<string>("");
  const [toDate, setToDate] = useState<string>("");

  // Set default dates to current date on mount
  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    setFromDate(today);
    setToDate(today);
  }, []);

  const fetchVisits = useCallback(async () => {
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

      let url = `http://127.0.0.1:8000/api/visit/visit-list-create/${admin_id}`;
      if (selectedUserId) {
        url = `http://127.0.0.1:8000/api/visit/visit-list-create-by-user/${admin_id}/${selectedUserId}`;
      }
      
      const params = new URLSearchParams();
      if (statusFilter) {
        params.append('status', statusFilter);
      }
      if (fromDate) {
        params.append('date_from', fromDate);
      }
      if (toDate) {
        params.append('date_to', toDate);
      }
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await axios.get(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      // Backend response format: { status, message, data: { results: [...] } }
      let visits = [];
      if (response.data && response.data.data) {
        if (response.data.data.results && Array.isArray(response.data.data.results)) {
          visits = response.data.data.results;
        } else if (Array.isArray(response.data.data)) {
          visits = response.data.data;
        }
      } else if (Array.isArray(response.data)) {
        visits = response.data;
      }
      setData(visits);
    } catch (error: any) {
      console.error("Error fetching visits:", error);
      toast.error(error.response?.data?.message || "Failed to fetch visits");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, selectedUserId, fromDate, toDate]);

  useEffect(() => {
    fetchVisits();
  }, [fetchVisits]);

  const routes = all_routes;
  
  const columns = [
    {
      title: "Title",
      dataIndex: "title",
      render: (text: string) => (
        <h6 className="fw-medium">
          <Link to="#">{text}</Link>
        </h6>
      ),
      sorter: (a: any, b: any) => (a.title ?? "").localeCompare(b.title ?? ""),
    },
    {
      title: "Employee",
      dataIndex: "assigned_employee_name",
      render: (text: string) => <span>{text ?? "—"}</span>,
    },
    {
      title: "Client/Location",
      dataIndex: "client_name",
      render: (_: any, record: any) => (
        <span>{record.client_name || record.location_name || "—"}</span>
      ),
    },
    {
      title: "Schedule Date",
      dataIndex: "schedule_date",
      render: (date: string) => {
        if (!date) return "—";
        return new Date(date).toLocaleDateString();
      },
      sorter: (a: any, b: any) => 
        new Date(a.schedule_date || 0).getTime() - new Date(b.schedule_date || 0).getTime(),
    },
    {
      title: "Status",
      dataIndex: "status",
      render: (status: string) => {
        const statusColors: any = {
          pending: "badge-warning",
          in_progress: "badge-info",
          completed: "badge-success",
          cancelled: "badge-danger",
        };
        const statusLabels: any = {
          pending: "Pending",
          in_progress: "In Progress",
          completed: "Completed",
          cancelled: "Cancelled",
        };
        return (
          <span className={`badge d-inline-flex align-items-center badge-sm ${statusColors[status] || "badge-secondary"}`}>
            <i className="ti ti-point-filled me-1" />
            {statusLabels[status] || status}
          </span>
        );
      },
      sorter: (a: any, b: any) => (a.status ?? "").localeCompare(b.status ?? ""),
    },
    {
      title: "Check-in",
      dataIndex: "check_in_timestamp",
      render: (timestamp: string) => {
        if (!timestamp) return <span className="text-muted">—</span>;
        return new Date(timestamp).toLocaleString();
      },
    },
    {
      title: "Check-out",
      dataIndex: "check_out_timestamp",
      render: (timestamp: string) => {
        if (!timestamp) return <span className="text-muted">—</span>;
        return new Date(timestamp).toLocaleString();
      },
    },
    {
      title: "Actions",
      dataIndex: "actions",
      render: (_: any, visit: any) => (
        <div className="action-icon d-inline-flex">
          <Link
            to="#"
            className="me-2"
            data-bs-toggle="modal"
            data-bs-target="#visitModal"
            onClick={() => setEditingVisit(visit)}
          >
            <i className="ti ti-edit" />
          </Link>
          <Link
            to="#"
            data-bs-toggle="modal"
            data-bs-target="#deleteVisitModal"
            onClick={() => setVisitIdToDelete(normalizeVisitId(getVisitKey(visit)))}
          >
            <i className="ti ti-trash" />
          </Link>
        </div>
      ),
    },
  ];

  const handleVisitAdded = () => {
    fetchVisits();
    setEditingVisit(null);
  };

  const handleVisitUpdated = () => {
    fetchVisits();
    setEditingVisit(null);
  };

  const handleVisitDeleted = () => {
    fetchVisits();
    setVisitIdToDelete(null);
  };

  const handleCheckInOut = () => {
    fetchVisits();
    setCheckInOutVisit(null);
  };

  const handleEditClose = () => {
    setEditingVisit(null);
  };

  return (
    <>
      {/* Page Wrapper */}
      <div className="page-wrapper">
        <div className="content">
          {/* Breadcrumb */}
          <div className="d-md-flex d-block align-items-center justify-content-between page-breadcrumb mb-3">
            <div className="my-auto mb-2">
              <h2 className="mb-1">Visits</h2>
            </div>
            <div className="d-flex my-xl-auto right-content align-items-center flex-wrap ">
              <div className="mb-2">
                <Link
                  to="#"
                  data-bs-toggle="modal" data-inert={true}
                  data-bs-target="#visitModal"
                  className="btn btn-primary d-flex align-items-center"
                  onClick={() => setEditingVisit(null)}
                >
                  <i className="ti ti-circle-plus me-2" />
                  Add Visit
                </Link>
              </div>
              <div className="head-icons ms-2">
                <CollapseHeader />
              </div>
            </div>
          </div>
          {/* /Breadcrumb */}
          <div className="card">
            <div className="card-header d-flex align-items-center justify-content-between flex-wrap row-gap-3">
              <h5>Visit List</h5>
              <div className="d-flex gap-2 flex-wrap">
                <select
                  className="form-select form-select-sm"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  style={{ width: "150px" }}
                >
                  <option value="">All Status</option>
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
                <input
                  type="date"
                  className="form-control form-control-sm"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                  placeholder="From Date"
                  style={{ width: "150px" }}
                />
                <input
                  type="date"
                  className="form-control form-control-sm"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                  placeholder="To Date"
                  style={{ width: "150px" }}
                />
              </div>
            </div>
            <div className="card-body p-0">
              {loading ? (
                <p className="p-3">Loading visits...</p>
              ) : (
                <Table dataSource={data} columns={columns} Selection={true} />
              )}
            </div>
          </div>
        </div>
        <div className="footer d-sm-flex align-items-center justify-content-between border-top bg-white p-3">
          <p className="mb-0">2025 © NeexQ</p>
          <p>
            Designed &amp; Developed By{" "}
            <Link to="#" className="text-primary">
              NeexQ
            </Link>
          </p>
        </div>
      </div>
      {/* /Page Wrapper */}

      {/* Visit Create/Edit Modal */}
      <VisitModal
        onVisitAdded={handleVisitAdded}
        editingVisit={editingVisit}
        onVisitUpdated={handleVisitUpdated}
        onEditClose={handleEditClose}
      />

      {/* Check-in/Check-out Modal */}
      <CheckInOutModal
        visit={checkInOutVisit}
        onCheckInOut={handleCheckInOut}
        onClose={() => setCheckInOutVisit(null)}
      />

      {/* Delete Modal */}
      <DeleteModal
        visitId={visitIdToDelete}
        onVisitDeleted={handleVisitDeleted}
        onCancel={() => setVisitIdToDelete(null)}
      />
      
      {/* Toast Container */}
      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
      />
    </>
  );
};

export default Visits;

