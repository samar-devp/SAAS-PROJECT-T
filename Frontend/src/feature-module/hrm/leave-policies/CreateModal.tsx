import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { toast } from "react-toastify";
import dayjs, { Dayjs } from "dayjs";
import { getAdminIdForApi } from "../../../core/utils/apiHelpers";

type LeavePolicyModalProps = {
  adminId: string | null;
  onPolicyAdded?: (newPolicy: any) => void;
  editingPolicy?: any;
  onPolicyUpdated?: (updatedPolicy: any) => void;
  onEditClose?: () => void;
};

type LeaveAllocation = {
  leaveType: string;
  days: string;
};

type LeavePolicyFormState = {
  name: string;
  description: string;
  scope: "organization" | "department" | "designation" | "employee";
  scope_value: string;
  effective_from: string;
  effective_to: string;
  is_active: boolean;
  probation_period_days: string;
  max_leaves_per_month: string;
  weekend_count_in_leave: boolean;
  holiday_count_in_leave: boolean;
  leave_allocations: LeaveAllocation[];
};

const initialFormState: LeavePolicyFormState = {
  name: "",
  description: "",
  scope: "organization",
  scope_value: "",
  effective_from: dayjs().format("YYYY-MM-DD"),
  effective_to: "",
  is_active: true,
  probation_period_days: "90",
  max_leaves_per_month: "",
  weekend_count_in_leave: false,
  holiday_count_in_leave: false,
  leave_allocations: [],
};

const LeavePolicyModal: React.FC<LeavePolicyModalProps> = ({
  adminId,
  onPolicyAdded,
  editingPolicy,
  onPolicyUpdated,
  onEditClose,
}) => {
  const [formData, setFormData] = useState<LeavePolicyFormState>(initialFormState);
  const [loading, setLoading] = useState(false);
  const [leaveTypes, setLeaveTypes] = useState<any[]>([]);

  // Fetch leave types for allocation dropdown
  const fetchLeaveTypes = useCallback(async () => {
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = adminId || getAdminIdForApi();

      if (!admin_id) return;

      const response = await axios.get(
        `http://127.0.0.1:8000/api/leave/leave-types/${admin_id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (Array.isArray(response.data)) {
        setLeaveTypes(response.data);
      }
    } catch (error) {
      console.error("Error fetching leave types:", error);
    }
  }, []);

  useEffect(() => {
    fetchLeaveTypes();
  }, [fetchLeaveTypes]);

  useEffect(() => {
    if (editingPolicy) {
      // Parse leave_allocations from JSON object to array
      let allocations: LeaveAllocation[] = [];
      if (editingPolicy.leave_allocations && typeof editingPolicy.leave_allocations === "object") {
        allocations = Object.entries(editingPolicy.leave_allocations).map(([key, value]) => ({
          leaveType: key,
          days: String(value),
        }));
      }

      setFormData({
        name: editingPolicy.name ?? "",
        description: editingPolicy.description ?? "",
        scope: editingPolicy.scope ?? "organization",
        scope_value: editingPolicy.scope_value ?? "",
        effective_from: editingPolicy.effective_from
          ? dayjs(editingPolicy.effective_from).format("YYYY-MM-DD")
          : dayjs().format("YYYY-MM-DD"),
        effective_to: editingPolicy.effective_to
          ? dayjs(editingPolicy.effective_to).format("YYYY-MM-DD")
          : "",
        is_active: editingPolicy.is_active ?? true,
        probation_period_days: String(editingPolicy.probation_period_days ?? 90),
        max_leaves_per_month: editingPolicy.max_leaves_per_month
          ? String(editingPolicy.max_leaves_per_month)
          : "",
        weekend_count_in_leave: editingPolicy.weekend_count_in_leave ?? false,
        holiday_count_in_leave: editingPolicy.holiday_count_in_leave ?? false,
        leave_allocations: allocations,
      });
    } else {
      setFormData(initialFormState);
    }
  }, [editingPolicy]);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    if (type === "checkbox") {
      setFormData((prev) => ({ ...prev, [name]: checked }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }
  };

  const handleAllocationChange = (index: number, field: "leaveType" | "days", value: string) => {
    setFormData((prev) => {
      const newAllocations = [...prev.leave_allocations];
      newAllocations[index] = { ...newAllocations[index], [field]: value };
      return { ...prev, leave_allocations: newAllocations };
    });
  };

  const addAllocation = () => {
    setFormData((prev) => ({
      ...prev,
      leave_allocations: [...prev.leave_allocations, { leaveType: "", days: "" }],
    }));
  };

  const removeAllocation = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      leave_allocations: prev.leave_allocations.filter((_, i) => i !== index),
    }));
  };

  const buildPayload = () => {
    // Convert leave_allocations array to JSON object
    const allocationsObj: { [key: string]: number } = {};
    formData.leave_allocations.forEach((alloc) => {
      if (alloc.leaveType && alloc.days) {
        allocationsObj[alloc.leaveType] = Number(alloc.days);
      }
    });

    const payload: any = {
      name: formData.name,
      description: formData.description,
      scope: formData.scope,
      effective_from: formData.effective_from,
      is_active: formData.is_active,
      probation_period_days: Number(formData.probation_period_days),
      weekend_count_in_leave: formData.weekend_count_in_leave,
      holiday_count_in_leave: formData.holiday_count_in_leave,
      leave_allocations: allocationsObj,
    };

    if (formData.scope_value) {
      payload.scope_value = formData.scope_value;
    }

    if (formData.effective_to) {
      payload.effective_to = formData.effective_to;
    }

    if (formData.max_leaves_per_month) {
      payload.max_leaves_per_month = Number(formData.max_leaves_per_month);
    }

    return payload;
  };

  const handleSubmit = async () => {
    const currentAdminId = adminId || getAdminIdForApi();
    if (!currentAdminId) {
      const role = sessionStorage.getItem("role");
      if (role === "organization") {
        toast.error("Please select an admin first from the dashboard.");
      } else {
        toast.error("Admin ID not found. Please login again.");
      }
      return;
    }

    if (!formData.name.trim()) {
      toast.error("Policy name is required");
      return;
    }

    if (!formData.effective_from) {
      toast.error("Effective from date is required");
      return;
    }

    if (formData.effective_to && formData.effective_to < formData.effective_from) {
      toast.error("Effective to date must be after effective from date");
      return;
    }

    if ((formData.scope === "department" || formData.scope === "designation" || formData.scope === "employee") && !formData.scope_value.trim()) {
      toast.error("Scope value is required for this scope type");
      return;
    }

    setLoading(true);
    try {
      const token = sessionStorage.getItem("access_token");
      const payload = buildPayload();

      if (editingPolicy) {
        // Update
        const policyId = editingPolicy.id;
        const response = await axios.put(
          `http://127.0.0.1:8000/api/leave/leave-policies/${currentAdminId}/${policyId}`,
          payload,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (response.data?.status === 200) {
          toast.success("Leave policy updated successfully");
          if (onPolicyUpdated) {
            onPolicyUpdated(response.data.data);
          }
          // Close modal
          const modalElement = document.getElementById("leavePolicyModal");
          if (modalElement) {
            const modalInstance = (window as any).bootstrap?.Modal?.getInstance(modalElement);
            if (modalInstance) {
              modalInstance.hide();
            }
          }
        } else {
          toast.error(response.data?.message || "Failed to update leave policy");
        }
      } else {
        // Create
        const response = await axios.post(
          `http://127.0.0.1:8000/api/leave/leave-policies/${currentAdminId}`,
          payload,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (response.data?.status === 201 || response.data?.status === 200) {
          toast.success("Leave policy created successfully");
          if (onPolicyAdded) {
            onPolicyAdded(response.data.data);
          }
          // Reset form
          setFormData(initialFormState);
          // Close modal
          const modalElement = document.getElementById("leavePolicyModal");
          if (modalElement) {
            const modalInstance = (window as any).bootstrap?.Modal?.getInstance(modalElement);
            if (modalInstance) {
              modalInstance.hide();
            }
          }
        } else {
          toast.error(response.data?.message || "Failed to create leave policy");
        }
      }
    } catch (error: any) {
      console.error("Error saving leave policy:", error);
      toast.error(error.response?.data?.message || error.response?.data?.errors || "Failed to save leave policy");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="modal fade"
      id="leavePolicyModal"
      tabIndex={-1}
      aria-labelledby="leavePolicyModalLabel"
      aria-hidden="true"
    >
      <div className="modal-dialog modal-lg modal-dialog-centered">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title" id="leavePolicyModalLabel">
              {editingPolicy ? "Edit Leave Policy" : "Add Leave Policy"}
            </h5>
            <button
              type="button"
              className="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
              onClick={() => {
                if (onEditClose) onEditClose();
                setFormData(initialFormState);
              }}
            />
          </div>
          <div className="modal-body">
            <div className="row">
              <div className="col-md-12 mb-3">
                <label className="form-label">
                  Policy Name <span className="text-danger">*</span>
                </label>
                <input
                  type="text"
                  className="form-control"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="Enter policy name"
                />
              </div>

              <div className="col-md-12 mb-3">
                <label className="form-label">Description</label>
                <textarea
                  className="form-control"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  rows={3}
                  placeholder="Enter policy description"
                />
              </div>

              <div className="col-md-6 mb-3">
                <label className="form-label">
                  Scope <span className="text-danger">*</span>
                </label>
                <select
                  className="form-select"
                  name="scope"
                  value={formData.scope}
                  onChange={handleInputChange}
                >
                  <option value="organization">Organization Wide</option>
                  <option value="department">Department</option>
                  <option value="designation">Designation</option>
                  <option value="employee">Individual Employee</option>
                </select>
              </div>

              {(formData.scope === "department" ||
                formData.scope === "designation" ||
                formData.scope === "employee") && (
                <div className="col-md-6 mb-3">
                  <label className="form-label">
                    Scope Value <span className="text-danger">*</span>
                  </label>
                  <input
                    type="text"
                    className="form-control"
                    name="scope_value"
                    value={formData.scope_value}
                    onChange={handleInputChange}
                    placeholder={
                      formData.scope === "department"
                        ? "Enter department ID"
                        : formData.scope === "designation"
                        ? "Enter designation ID"
                        : "Enter employee ID"
                    }
                  />
                </div>
              )}

              <div className="col-md-6 mb-3">
                <label className="form-label">
                  Effective From <span className="text-danger">*</span>
                </label>
                <input
                  type="date"
                  className="form-control"
                  name="effective_from"
                  value={formData.effective_from}
                  onChange={handleInputChange}
                />
              </div>

              <div className="col-md-6 mb-3">
                <label className="form-label">Effective To</label>
                <input
                  type="date"
                  className="form-control"
                  name="effective_to"
                  value={formData.effective_to}
                  onChange={handleInputChange}
                  min={formData.effective_from}
                />
              </div>

              <div className="col-md-6 mb-3">
                <label className="form-label">Probation Period (Days)</label>
                <input
                  type="number"
                  className="form-control"
                  name="probation_period_days"
                  value={formData.probation_period_days}
                  onChange={handleInputChange}
                  min="0"
                />
              </div>

              <div className="col-md-6 mb-3">
                <label className="form-label">Max Leaves Per Month</label>
                <input
                  type="number"
                  className="form-control"
                  name="max_leaves_per_month"
                  value={formData.max_leaves_per_month}
                  onChange={handleInputChange}
                  min="0"
                  step="0.5"
                />
              </div>

              <div className="col-md-6 mb-3">
                <div className="form-check">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    name="weekend_count_in_leave"
                    checked={formData.weekend_count_in_leave}
                    onChange={handleInputChange}
                  />
                  <label className="form-check-label">Weekend Count in Leave</label>
                </div>
              </div>

              <div className="col-md-6 mb-3">
                <div className="form-check">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    name="holiday_count_in_leave"
                    checked={formData.holiday_count_in_leave}
                    onChange={handleInputChange}
                  />
                  <label className="form-check-label">Holiday Count in Leave</label>
                </div>
              </div>

              <div className="col-md-12 mb-3">
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <label className="form-label mb-0">Leave Allocations</label>
                  <button
                    type="button"
                    className="btn btn-sm btn-primary"
                    onClick={addAllocation}
                  >
                    <i className="ti ti-plus me-1" />
                    Add Allocation
                  </button>
                </div>
                {formData.leave_allocations.length === 0 ? (
                  <p className="text-muted small">No leave allocations added</p>
                ) : (
                  <div className="table-responsive">
                    <table className="table table-bordered">
                      <thead>
                        <tr>
                          <th>Leave Type</th>
                          <th>Days</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {formData.leave_allocations.map((alloc, index) => (
                          <tr key={index}>
                            <td>
                              <select
                                className="form-select form-select-sm"
                                value={alloc.leaveType}
                                onChange={(e) =>
                                  handleAllocationChange(index, "leaveType", e.target.value)
                                }
                              >
                                <option value="">Select Leave Type</option>
                                {leaveTypes.map((lt) => (
                                  <option key={lt.id} value={lt.code || lt.name}>
                                    {lt.name} ({lt.code})
                                  </option>
                                ))}
                              </select>
                            </td>
                            <td>
                              <input
                                type="number"
                                className="form-control form-control-sm"
                                value={alloc.days}
                                onChange={(e) =>
                                  handleAllocationChange(index, "days", e.target.value)
                                }
                                min="0"
                                step="0.5"
                                placeholder="Days"
                              />
                            </td>
                            <td>
                              <button
                                type="button"
                                className="btn btn-sm btn-danger"
                                onClick={() => removeAllocation(index)}
                              >
                                <i className="ti ti-trash" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              <div className="col-md-12 mb-3">
                <div className="form-check">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    name="is_active"
                    checked={formData.is_active}
                    onChange={handleInputChange}
                  />
                  <label className="form-check-label">Active</label>
                </div>
              </div>
            </div>
          </div>
          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              data-bs-dismiss="modal"
              onClick={() => {
                if (onEditClose) onEditClose();
                setFormData(initialFormState);
              }}
            >
              Cancel
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? (
                <>
                  <span
                    className="spinner-border spinner-border-sm me-2"
                    role="status"
                    aria-hidden="true"
                  />
                  {editingPolicy ? "Updating..." : "Creating..."}
                </>
              ) : (
                <>{editingPolicy ? "Update" : "Create"}</>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeavePolicyModal;

