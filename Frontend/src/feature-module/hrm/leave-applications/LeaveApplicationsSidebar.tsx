import React, { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import { toast } from "react-toastify";
import { BACKEND_PATH } from "../../../environment";
import { resetBodyStyles } from "../../../core/utils/modalHelpers";

type LeaveApplicationsSidebarProps = {
  isOpen: boolean;
  onClose: () => void;
  employeeId?: string;
  employeeName?: string;
};

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

type ApiResponse = {
  status: number;
  message: string;
  count: number;
  year: number;
  date_range: {
    start_date: string;
    end_date: string;
  };
  data: LeaveApplication[];
};

const LeaveApplicationsSidebar: React.FC<LeaveApplicationsSidebarProps> = ({
  isOpen,
  onClose,
  employeeId,
  employeeName,
}) => {
  const currentYear = new Date().getFullYear();
  const [selectedYear, setSelectedYear] = useState<number>(currentYear);
  const [leaveApplications, setLeaveApplications] = useState<LeaveApplication[]>([]);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState<{ start_date: string; end_date: string } | null>(null);
  const [processingLeaveId, setProcessingLeaveId] = useState<number | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const backdropRef = useRef<HTMLDivElement | null>(null);

  // Year options: Only 2025 and 2026
  const yearOptions = [2025, 2026];

  // Handle backdrop and body classes manually
  const handleClose = useCallback(() => {
    onClose();
  }, [onClose]);

  useEffect(() => {
    if (isOpen) {
      // Create backdrop manually outside React
      const backdrop = document.createElement('div');
      backdrop.className = 'modal-backdrop show';
      backdrop.style.zIndex = '1040';
      backdrop.onclick = handleClose;
      document.body.appendChild(backdrop);
      backdropRef.current = backdrop;
      document.body.classList.add('modal-open');
    }

    return () => {
      // Cleanup
      if (backdropRef.current) {
        try {
          if (document.body.contains(backdropRef.current)) {
            document.body.removeChild(backdropRef.current);
          }
        } catch (error) {
          console.debug('Backdrop already removed:', error);
        }
        backdropRef.current = null;
      }
      resetBodyStyles();
    };
  }, [isOpen, handleClose]);

  // Fetch leave applications when sidebar opens or year changes
  useEffect(() => {
    if (isOpen && employeeId) {
      fetchLeaveApplications();
    }
  }, [isOpen, employeeId, selectedYear]);

  const fetchLeaveApplications = async () => {
    setLoading(true);
    try {
      const token = sessionStorage.getItem("access_token");
      const adminId = sessionStorage.getItem("user_id");

      if (!adminId || !employeeId) {
        toast.error("Missing required information");
        return;
      }

      const response = await axios.get<ApiResponse>(
        `${BACKEND_PATH}leave-applications/${adminId}/${employeeId}?year=${selectedYear}`,
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

  const handleApproveReject = async (leaveId: number, action: "approved" | "rejected") => {
    setProcessingLeaveId(leaveId);
    try {
      const token = sessionStorage.getItem("access_token");
      const adminId = sessionStorage.getItem("user_id");

      if (!adminId || !employeeId) {
        toast.error("Missing required information");
        return;
      }

      const response = await axios.put(
        `${BACKEND_PATH}leave-applications/${adminId}/${employeeId}/${leaveId}`,
        {
          status: action,
          reviewed_at: new Date().toISOString(),
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      toast.success(response.data.message || `Leave ${action} successfully`);
      
      // Refresh the list
      fetchLeaveApplications();
    } catch (error: any) {
      console.error(`Error ${action} leave:`, error);
      const errorMessage = error.response?.data?.message || `Failed to ${action} leave`;
      toast.error(errorMessage);
    } finally {
      setProcessingLeaveId(null);
    }
  };

  const handleCancelLeave = async (leaveId: number) => {
    if (!window.confirm("Are you sure you want to cancel this leave application?")) {
      return;
    }

    setProcessingLeaveId(leaveId);
    try {
      const token = sessionStorage.getItem("access_token");
      const adminId = sessionStorage.getItem("user_id");

      if (!adminId || !employeeId) {
        toast.error("Missing required information");
        return;
      }

      const response = await axios.delete(
        `${BACKEND_PATH}leave-applications/${adminId}/${employeeId}/${leaveId}`,
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

  if (!isOpen) return null;

  return (
    <>
      {/* Sidebar */}
      <div
        className="offcanvas offcanvas-end show"
        style={{
          visibility: "visible",
          width: "600px",
          zIndex: 1050,
        }}
      >
        <div className="offcanvas-header border-bottom">
          <h5 className="offcanvas-title">
            Leave Applications
            {employeeName && (
              <>
                <br />
                <small className="text-muted">{employeeName}</small>
              </>
            )}
          </h5>
          <button
            type="button"
            className="btn-close"
            onClick={handleClose}
          />
        </div>

        <div className="offcanvas-body">
          {/* Year Selector */}
          <div className="mb-3">
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
                Date Range: {new Date(dateRange.start_date).toLocaleDateString()} to{" "}
                {new Date(dateRange.end_date).toLocaleDateString()}
              </small>
            )}
          </div>

          {/* Status Filter */}
          <div className="mb-3">
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

          {/* Loading State */}
          {loading && (
            <div className="text-center py-4">
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <p className="mt-2">Loading leave applications...</p>
            </div>
          )}

          {/* Empty State */}
          {!loading && filteredApplications.length === 0 && (
            <div className="text-center py-4">
              <i className="ti ti-clipboard-off fs-1 text-muted" />
              <p className="mt-2 text-muted">
                No leave applications found for {selectedYear}
              </p>
            </div>
          )}

          {/* Leave Applications List */}
          {!loading && filteredApplications.length > 0 && (
            <div className="leave-applications-list">
              <p className="mb-3">
                <strong>{filteredApplications.length}</strong> application(s) found
              </p>
              {filteredApplications.map((leave) => (
                <div key={leave.id} className="card mb-3">
                  <div className="card-body">
                    <div className="d-flex justify-content-between align-items-start mb-2">
                      <div>
                        <h6 className="mb-1">
                          {leave.leave_type_name} ({leave.leave_type_code})
                        </h6>
                        <small className="text-muted">
                          Applied on: {new Date(leave.applied_at).toLocaleDateString()}
                        </small>
                      </div>
                      <span className={`badge ${getStatusBadgeClass(leave.status)}`}>
                        {leave.status.toUpperCase()}
                      </span>
                    </div>

                    <div className="mb-2">
                      <div className="d-flex align-items-center mb-1">
                        <i className="ti ti-calendar me-2 text-primary" />
                        <strong>Duration:</strong>
                      </div>
                      <p className="mb-0 ms-4">
                        {new Date(leave.from_date).toLocaleDateString()} to{" "}
                        {new Date(leave.to_date).toLocaleDateString()}
                        <span className="badge badge-info ms-2">
                          {leave.total_days} day(s)
                        </span>
                      </p>
                    </div>

                    <div className="mb-2">
                      <div className="d-flex align-items-center mb-1">
                        <i className="ti ti-file-text me-2 text-primary" />
                        <strong>Reason:</strong>
                      </div>
                      <p className="mb-0 ms-4">{leave.reason}</p>
                    </div>

                    {leave.reviewed_at && (
                      <div className="mb-2">
                        <small className="text-muted">
                          Reviewed on: {new Date(leave.reviewed_at).toLocaleDateString()}
                          {leave.reviewed_by_email && ` by ${leave.reviewed_by_email}`}
                        </small>
                      </div>
                    )}

                    {leave.comments && (
                      <div className="mb-2">
                        <div className="d-flex align-items-center mb-1">
                          <i className="ti ti-message me-2 text-primary" />
                          <strong>Comments:</strong>
                        </div>
                        <p className="mb-0 ms-4 text-muted">{leave.comments}</p>
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="mt-3 d-flex gap-2">
                      {leave.status === "pending" && (
                        <>
                          <button
                            className="btn btn-sm btn-success"
                            onClick={() => handleApproveReject(leave.id, "approved")}
                            disabled={processingLeaveId === leave.id}
                          >
                            {processingLeaveId === leave.id ? (
                              <>
                                <span className="spinner-border spinner-border-sm me-1" />
                                Approving...
                              </>
                            ) : (
                              <>
                                <i className="ti ti-check me-1" />
                                Approve
                              </>
                            )}
                          </button>
                          <button
                            className="btn btn-sm btn-danger"
                            onClick={() => handleApproveReject(leave.id, "rejected")}
                            disabled={processingLeaveId === leave.id}
                          >
                            {processingLeaveId === leave.id ? (
                              <>
                                <span className="spinner-border spinner-border-sm me-1" />
                                Rejecting...
                              </>
                            ) : (
                              <>
                                <i className="ti ti-x me-1" />
                                Reject
                              </>
                            )}
                          </button>
                          <button
                            className="btn btn-sm btn-secondary"
                            onClick={() => handleCancelLeave(leave.id)}
                            disabled={processingLeaveId === leave.id}
                          >
                            {processingLeaveId === leave.id ? (
                              <>
                                <span className="spinner-border spinner-border-sm me-1" />
                                Cancelling...
                              </>
                            ) : (
                              <>
                                <i className="ti ti-ban me-1" />
                                Cancel
                              </>
                            )}
                          </button>
                        </>
                      )}
                      {leave.status !== "pending" && (
                        <span className="text-muted small">
                          No actions available for {leave.status} leaves
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default LeaveApplicationsSidebar;

