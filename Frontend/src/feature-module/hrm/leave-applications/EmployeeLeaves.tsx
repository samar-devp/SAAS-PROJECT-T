import React, { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "react-toastify";
import { Table } from "antd";

const BACKEND_PATH = "http://127.0.0.1:8000";

type LeaveApplication = {
  id: number;
  user: string;
  user_name: string;
  user_email: string;
  leave_type: number;
  leave_type_name: string;
  leave_type_code: string;
  from_date: string;
  to_date: string;
  total_days: number;
  reason: string;
  status: "pending" | "approved" | "rejected" | "cancelled";
  applied_at: string;
  reviewed_at?: string;
  reviewed_by_email?: string;
  comments?: string;
};

const EmployeeLeaves: React.FC = () => {
  const currentYear = new Date().getFullYear();
  const [selectedYear, setSelectedYear] = useState<number>(currentYear);
  const [leaveApplications, setLeaveApplications] = useState<LeaveApplication[]>([]);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState<{ start_date: string; end_date: string } | null>(null);
  const [processingLeaveId, setProcessingLeaveId] = useState<number | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>("all");

  // Year options: Only 2025 and 2026
  const yearOptions = [2025, 2026];

  // Fetch leave applications on mount and when year changes
  useEffect(() => {
    fetchLeaveApplications();
  }, [selectedYear]);

  const fetchLeaveApplications = async () => {
    setLoading(true);
    try {
      const token = sessionStorage.getItem("access_token");
      const adminId = sessionStorage.getItem("user_id");

      if (!adminId) {
        toast.error("Admin ID not found");
        return;
      }

      const response = await axios.get(
        `${BACKEND_PATH}/api/leave-applications/${adminId}?year=${selectedYear}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      setLeaveApplications(response.data.data || []);
      setDateRange(response.data.date_range);
    } catch (error: any) {
      console.error("Error fetching leave applications:", error);
      const errorMessage = error.response?.data?.message || "Failed to fetch leave applications";
      toast.error(errorMessage);
      setLeaveApplications([]);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveReject = async (leaveId: number, newStatus: "approved" | "rejected", employeeId: string) => {
    setProcessingLeaveId(leaveId);
    try {
      const token = sessionStorage.getItem("access_token");
      const adminId = sessionStorage.getItem("user_id");

      if (!adminId) {
        toast.error("Admin ID not found");
        return;
      }

      const response = await axios.put(
        `${BACKEND_PATH}/api/leave-applications/${adminId}/${employeeId}/${leaveId}`,
        {
          status: newStatus,
          reviewed_at: new Date().toISOString(),
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      toast.success(response.data.message || `Leave ${newStatus} successfully`);
      
      // Refresh the list
      fetchLeaveApplications();
    } catch (error: any) {
      console.error(`Error ${newStatus} leave:`, error);
      const errorMessage = error.response?.data?.message || `Failed to ${newStatus} leave`;
      toast.error(errorMessage);
    } finally {
      setProcessingLeaveId(null);
    }
  };

  const handleCancelLeave = async (leaveId: number, employeeId: string) => {
    if (!window.confirm("Are you sure you want to cancel this leave application?")) {
      return;
    }

    setProcessingLeaveId(leaveId);
    try {
      const token = sessionStorage.getItem("access_token");
      const adminId = sessionStorage.getItem("user_id");

      if (!adminId) {
        toast.error("Admin ID not found");
        return;
      }

      const response = await axios.delete(
        `${BACKEND_PATH}/api/leave-applications/${adminId}/${employeeId}/${leaveId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      toast.success(response.data.message || "Leave cancelled successfully");
      
      // Refresh the list
      fetchLeaveApplications();
    } catch (error: any) {
      console.error("Error cancelling leave:", error);
      const errorMessage = error.response?.data?.message || "Failed to cancel leave";
      toast.error(errorMessage, { autoClose: 6000 });
    } finally {
      setProcessingLeaveId(null);
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case "pending":
        return "badge-warning";
      case "approved":
        return "badge-success";
      case "rejected":
        return "badge-danger";
      case "cancelled":
        return "badge-secondary";
      default:
        return "badge-info";
    }
  };

  const filteredApplications = selectedStatus === "all" 
    ? leaveApplications 
    : leaveApplications.filter(app => app.status === selectedStatus);

  const columns = [
    {
      title: "Employee",
      dataIndex: "user_name",
      key: "user_name",
      render: (text: string, record: LeaveApplication) => (
        <div>
          <strong>{text}</strong>
          <br />
          <small className="text-muted">{record.user_email}</small>
        </div>
      ),
      sorter: (a: LeaveApplication, b: LeaveApplication) => a.user_name.localeCompare(b.user_name),
    },
    {
      title: "Leave Type",
      dataIndex: "leave_type_name",
      key: "leave_type_name",
      render: (text: string, record: LeaveApplication) => (
        <div>
          {text}
          <br />
          <small className="text-muted">({record.leave_type_code})</small>
        </div>
      ),
    },
    {
      title: "Duration",
      key: "duration",
      render: (_: any, record: LeaveApplication) => (
        <div>
          <div>{new Date(record.from_date).toLocaleDateString()} to {new Date(record.to_date).toLocaleDateString()}</div>
          <span className="badge badge-info badge-sm">{record.total_days} day(s)</span>
        </div>
      ),
    },
    {
      title: "Reason",
      dataIndex: "reason",
      key: "reason",
      render: (text: string) => (
        <div style={{ maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis" }}>
          {text}
        </div>
      ),
    },
    {
      title: "Applied On",
      dataIndex: "applied_at",
      key: "applied_at",
      render: (text: string) => new Date(text).toLocaleDateString(),
      sorter: (a: LeaveApplication, b: LeaveApplication) => 
        new Date(a.applied_at).getTime() - new Date(b.applied_at).getTime(),
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      render: (status: string) => (
        <span className={`badge ${getStatusBadgeClass(status)}`}>
          {status.toUpperCase()}
        </span>
      ),
      filters: [
        { text: 'Pending', value: 'pending' },
        { text: 'Approved', value: 'approved' },
        { text: 'Rejected', value: 'rejected' },
        { text: 'Cancelled', value: 'cancelled' },
      ],
      onFilter: (value: any, record: LeaveApplication) => record.status === value,
    },
    {
      title: "Actions",
      key: "actions",
      align: "center" as const,
      render: (_: any, record: LeaveApplication) => (
        <div className="d-flex gap-1 justify-content-center">
          {record.status === "pending" && (
            <>
              <button
                className="btn btn-sm btn-success"
                onClick={() => handleApproveReject(record.id, "approved", record.user)}
                disabled={processingLeaveId === record.id}
                title="Approve"
              >
                {processingLeaveId === record.id ? (
                  <span className="spinner-border spinner-border-sm" />
                ) : (
                  <i className="ti ti-check" />
                )}
              </button>
              <button
                className="btn btn-sm btn-danger"
                onClick={() => handleApproveReject(record.id, "rejected", record.user)}
                disabled={processingLeaveId === record.id}
                title="Reject"
              >
                {processingLeaveId === record.id ? (
                  <span className="spinner-border spinner-border-sm" />
                ) : (
                  <i className="ti ti-x" />
                )}
              </button>
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => handleCancelLeave(record.id, record.user)}
                disabled={processingLeaveId === record.id}
                title="Cancel"
              >
                {processingLeaveId === record.id ? (
                  <span className="spinner-border spinner-border-sm" />
                ) : (
                  <i className="ti ti-ban" />
                )}
              </button>
            </>
          )}
          {record.status !== "pending" && (
            <span className="text-muted small">No actions</span>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="page-wrapper">
      <div className="content">
        {/* Page Header */}
        <div className="d-md-flex d-block align-items-center justify-content-between mb-3">
          <div className="my-auto mb-2">
            <h3 className="page-title mb-1">Employee Leaves</h3>
            <nav>
              <ol className="breadcrumb mb-0">
                <li className="breadcrumb-item">
                  <a href="index">Dashboard</a>
                </li>
                <li className="breadcrumb-item">Employees</li>
                <li className="breadcrumb-item active" aria-current="page">
                  Employee Leaves
                </li>
              </ol>
            </nav>
          </div>
        </div>

        {/* Filters */}
        <div className="card mb-3">
          <div className="card-body">
            <div className="row align-items-center">
              <div className="col-md-4">
                <div className="mb-3 mb-md-0">
                  <label className="form-label">Select Year</label>
                  <select
                    className="form-select"
                    value={selectedYear}
                    onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                  >
                    {yearOptions.map((year) => (
                      <option key={year} value={year}>
                        {year}
                      </option>
                    ))}
                  </select>
                  {dateRange && (
                    <small className="text-muted d-block mt-1">
                      Range: {new Date(dateRange.start_date).toLocaleDateString()} to{" "}
                      {new Date(dateRange.end_date).toLocaleDateString()}
                    </small>
                  )}
                </div>
              </div>
              <div className="col-md-4">
                <div className="mb-3 mb-md-0">
                  <label className="form-label">Filter by Status</label>
                  <select
                    className="form-select"
                    value={selectedStatus}
                    onChange={(e) => setSelectedStatus(e.target.value)}
                  >
                    <option value="all">All Status</option>
                    <option value="pending">Pending</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
              </div>
              <div className="col-md-4">
                <div className="mb-3 mb-md-0">
                  <label className="form-label">Total Applications</label>
                  <div className="h5 mb-0">{filteredApplications.length}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Leave Applications Table */}
        <div className="card">
          <div className="card-body">
            <Table
              columns={columns}
              dataSource={filteredApplications}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} applications`,
              }}
              scroll={{ x: "max-content" }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmployeeLeaves;

