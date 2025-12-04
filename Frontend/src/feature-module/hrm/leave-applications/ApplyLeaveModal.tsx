import React, { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "react-toastify";
import { removeAllBackdrops, resetBodyStyles, openModal, closeModal } from "../../../core/utils/modalHelpers";

const BACKEND_PATH = "http://127.0.0.1:8000";

type ApplyLeaveModalProps = {
  employee?: any;
  onLeaveApplied?: () => void;
};

type LeaveType = {
  id: number;
  name: string;
  code: string;
  default_count: number;
  is_paid: boolean;
};

type LeaveBalance = {
  id: number;
  leave_type: number;
  leave_type_name: string;
  assigned: number;
  used: number;
  balance: number;
};

const ApplyLeaveModal: React.FC<ApplyLeaveModalProps> = ({ employee, onLeaveApplied }) => {
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [leaveBalances, setLeaveBalances] = useState<LeaveBalance[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingLeaveTypes, setLoadingLeaveTypes] = useState(true);

  const [selectedLeaveType, setSelectedLeaveType] = useState<string>("");
  const [fromDate, setFromDate] = useState<string>("");
  const [toDate, setToDate] = useState<string>("");
  const [reason, setReason] = useState<string>("");
  const [totalDays, setTotalDays] = useState<number>(0);

  // Fetch leave types on mount
  useEffect(() => {
    fetchLeaveTypes();
  }, []);

  // Fetch leave balances when employee changes
  useEffect(() => {
    if (employee) {
      fetchLeaveBalances();
    } else {
      setLeaveBalances([]);
      resetForm();
    }
  }, [employee]);

  // Calculate total days when dates change
  useEffect(() => {
    if (fromDate && toDate) {
      const from = new Date(fromDate);
      const to = new Date(toDate);
      const diffTime = to.getTime() - from.getTime();
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
      setTotalDays(diffDays > 0 ? diffDays : 0);
    } else {
      setTotalDays(0);
    }
  }, [fromDate, toDate]);

  // Listen for modal close events (escape, backdrop click, etc.)
  useEffect(() => {
    const modalElement = document.getElementById('apply_leave_for_employee_modal');
    if (!modalElement) return;

    const handleModalHide = () => {
      // Clean up when modal is hidden by any means
      setTimeout(() => {
        // Use utility function to remove all backdrops
        removeAllBackdrops();
        
        // Clean up this modal completely
        const applyModal = document.getElementById('apply_leave_for_employee_modal');
        if (applyModal) {
          applyModal.classList.remove('show');
          applyModal.style.display = 'none';
          applyModal.setAttribute('aria-hidden', 'true');
          applyModal.removeAttribute('aria-modal');
        }
        
        // Use utility function to reset body styles
        resetBodyStyles();
        
        // Reopen Assign modal with proper cleanup
        openModal('assign_leave_modal');
      }, 150);
    };

    // Add event listener for Bootstrap modal hide event
    modalElement.addEventListener('hidden.bs.modal', handleModalHide);

    return () => {
      modalElement.removeEventListener('hidden.bs.modal', handleModalHide);
    };
  }, []);

  const fetchLeaveTypes = async () => {
    try {
      const token = sessionStorage.getItem("access_token");
      const adminId = sessionStorage.getItem("user_id");

      const response = await axios.get(
        `${BACKEND_PATH}/api/leave-types/${adminId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const types = response.data.data || response.data;
      setLeaveTypes(Array.isArray(types) ? types : []);
    } catch (error) {
      console.error("Error fetching leave types:", error);
      toast.error("Failed to fetch leave types");
    } finally {
      setLoadingLeaveTypes(false);
    }
  };

  const fetchLeaveBalances = async () => {
    if (!employee) return;

    try {
      const token = sessionStorage.getItem("access_token");
      const adminId = sessionStorage.getItem("user_id");
      const currentYear = new Date().getFullYear();
      const employeeUserId = employee.user?.id || employee.user_id || employee.id;

      const response = await axios.get(
        `${BACKEND_PATH}/api/leave-balances/${adminId}/${employeeUserId}?year=${currentYear}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const balances = response.data.data || response.data;
      setLeaveBalances(Array.isArray(balances) ? balances : []);
    } catch (error) {
      console.error("Error fetching leave balances:", error);
      setLeaveBalances([]);
    }
  };

  const getAvailableBalance = (leaveTypeId: number) => {
    const balance = leaveBalances.find(b => b.leave_type === leaveTypeId);
    return balance?.balance || 0;
  };

  const resetForm = () => {
    setSelectedLeaveType("");
    setFromDate("");
    setToDate("");
    setReason("");
    setTotalDays(0);
  };

  const cleanupAndReopenAssignModal = () => {
    // Close Apply Leave modal using utility function
    closeModal('apply_leave_for_employee_modal');
    
    setTimeout(() => {
      // Remove all backdrops
      removeAllBackdrops();
      
      // Clean Apply Leave modal completely
      const applyModal = document.getElementById('apply_leave_for_employee_modal');
      if (applyModal) {
        applyModal.classList.remove('show');
        applyModal.style.display = 'none';
        applyModal.setAttribute('aria-hidden', 'true');
        applyModal.removeAttribute('aria-modal');
      }
      
      // Reset body styles
      resetBodyStyles();
      
      // Small delay before reopening assign modal
      setTimeout(() => {
        // Double-check cleanup
        removeAllBackdrops();
        
        // Reopen Assign Leave modal using utility function
        openModal('assign_leave_modal');
      }, 100);
    }, 150);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!employee) {
      toast.error("No employee selected");
      return;
    }

    if (!selectedLeaveType || !fromDate || !toDate || !reason) {
      toast.error("Please fill all required fields");
      return;
    }

    if (totalDays <= 0) {
      toast.error("Invalid date range. End date must be after start date");
      return;
    }

    // Check if employee has sufficient balance
    const availableBalance = getAvailableBalance(parseInt(selectedLeaveType));
    if (availableBalance < totalDays) {
      toast.error(`Insufficient balance. Available: ${availableBalance} days, Required: ${totalDays} days`);
      return;
    }

    setLoading(true);
    try {
      const token = sessionStorage.getItem("access_token");
      const adminId = sessionStorage.getItem("user_id");
      const employeeUserId = employee.user?.id || employee.user_id || employee.id;

      const response = await axios.post(
        `${BACKEND_PATH}/api/leave-applications/${adminId}/${employeeUserId}`,
        {
          leave_type: parseInt(selectedLeaveType),
          from_date: fromDate,
          to_date: toDate,
          reason: reason,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      toast.success(response.data.message || "Leave applied successfully");
      
      // Reset form
      resetForm();
      
      // Clean up and reopen assign modal
      cleanupAndReopenAssignModal();
      
      // Callback to refresh parent
      onLeaveApplied?.();
    } catch (error: any) {
      console.error("Error applying leave:", error);
      const errorMessage = error.response?.data?.message || "Failed to apply leave";
      toast.error(errorMessage, { autoClose: 6000 });
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    resetForm();
    cleanupAndReopenAssignModal();
  };

  const selectedLeaveTypeData = leaveTypes.find(lt => lt.id === parseInt(selectedLeaveType));
  const availableBalance = selectedLeaveType ? getAvailableBalance(parseInt(selectedLeaveType)) : 0;

  if (!employee) return null;

  return (
    <div className="modal fade" id="apply_leave_for_employee_modal">
      <div className="modal-dialog modal-dialog-centered modal-md">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              Apply Leave for {employee.user_name || employee.user?.email || employee.email}
            </h5>
            <button
              type="button"
              className="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
              onClick={handleCancel}
            />
          </div>
          <form onSubmit={handleSubmit}>
            <div className="modal-body">
              {/* Leave Type Selection */}
              <div className="mb-3">
                <label className="form-label">
                  Leave Type <span className="text-danger">*</span>
                </label>
                <select
                  className="form-select"
                  value={selectedLeaveType}
                  onChange={(e) => setSelectedLeaveType(e.target.value)}
                  disabled={loadingLeaveTypes}
                  required
                >
                  <option value="">Choose Leave Type...</option>
                  {leaveTypes.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.name} ({type.code}) - {type.is_paid ? "Paid" : "Unpaid"}
                    </option>
                  ))}
                </select>
                {selectedLeaveType && (
                  <small className="text-muted d-block mt-1">
                    Available Balance: <strong>{availableBalance} days</strong>
                    {selectedLeaveTypeData && ` (Max: ${selectedLeaveTypeData.default_count} days)`}
                  </small>
                )}
              </div>

              {/* Date Range */}
              <div className="row">
                <div className="col-md-6">
                  <div className="mb-3">
                    <label className="form-label">
                      From Date <span className="text-danger">*</span>
                    </label>
                    <input
                      type="date"
                      className="form-control"
                      value={fromDate}
                      onChange={(e) => setFromDate(e.target.value)}
                      min={new Date().toISOString().split('T')[0]}
                      required
                    />
                  </div>
                </div>
                <div className="col-md-6">
                  <div className="mb-3">
                    <label className="form-label">
                      To Date <span className="text-danger">*</span>
                    </label>
                    <input
                      type="date"
                      className="form-control"
                      value={toDate}
                      onChange={(e) => setToDate(e.target.value)}
                      min={fromDate || new Date().toISOString().split('T')[0]}
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Total Days Display */}
              {totalDays > 0 && (
                <div className="alert alert-info mb-3">
                  <i className="ti ti-calendar me-2" />
                  <strong>Total Days: {totalDays}</strong>
                  {availableBalance > 0 && (
                    <span className="ms-3">
                      (Remaining after: {availableBalance - totalDays} days)
                    </span>
                  )}
                </div>
              )}

              {/* Reason */}
              <div className="mb-3">
                <label className="form-label">
                  Reason <span className="text-danger">*</span>
                </label>
                <textarea
                  className="form-control"
                  rows={3}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Enter reason for leave..."
                  required
                />
              </div>

              {/* Validation Messages */}
              {totalDays > availableBalance && availableBalance >= 0 && selectedLeaveType && (
                <div className="alert alert-danger">
                  <i className="ti ti-alert-circle me-2" />
                  Insufficient balance! Required: {totalDays} days, Available: {availableBalance} days
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-secondary"
                data-bs-dismiss="modal"
                onClick={handleCancel}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={
                  loading ||
                  !selectedLeaveType ||
                  !fromDate ||
                  !toDate ||
                  !reason ||
                  totalDays <= 0 ||
                  totalDays > availableBalance
                }
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" />
                    Applying...
                  </>
                ) : (
                  <>
                    <i className="ti ti-check me-2" />
                    Apply Leave
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ApplyLeaveModal;

