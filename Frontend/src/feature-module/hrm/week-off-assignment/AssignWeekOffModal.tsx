import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { toast } from "react-toastify";
import {
  removeAllBackdrops,
  resetBodyStyles,
  cleanupExcessBackdrops,
} from "../../../core/utils/modalHelpers";

type AssignWeekOffModalProps = {
  employee?: any;
  onWeekOffAssigned?: (result: any) => void;
  onClose?: () => void;
};

type WeekOffOption = {
  id: number;
  name: string;
  week_off_type: string;
  week_days: string[];
  description?: string;
  is_active: boolean;
};

const AssignWeekOffModal: React.FC<AssignWeekOffModalProps> = ({
  employee,
  onWeekOffAssigned,
  onClose,
}) => {
  const [weekOffs, setWeekOffs] = useState<WeekOffOption[]>([]);
  const [selectedWeekOffs, setSelectedWeekOffs] = useState<number[]>([]);
  const [assignedWeekOffs, setAssignedWeekOffs] = useState<WeekOffOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingWeekOffs, setLoadingWeekOffs] = useState(true);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [activeTab, setActiveTab] = useState<"assign" | "summary">("assign");
  const [currentEmployee, setCurrentEmployee] = useState<any>(null);
  const employeeRef = useRef<any>(null);

  useEffect(() => {
    setCurrentEmployee(employee);
    if (employee) {
      employeeRef.current = employee;
      console.log("📝 Employee stored in ref:", employee);
    }
  }, [employee]);

  // Modal event listeners
  useEffect(() => {
    const modalElement = document.getElementById("assign_week_off_modal");
    if (!modalElement) return;

    const handleModalShow = () => {
      setTimeout(() => {
        cleanupExcessBackdrops();
      }, 50);
      
      if (currentEmployee) {
        fetchAssignedWeekOffs();
      }
    };

    const handleModalHide = () => {
      setTimeout(() => {
        removeAllBackdrops();
        resetBodyStyles();
      }, 150);
    };

    modalElement.addEventListener("shown.bs.modal", handleModalShow);
    modalElement.addEventListener("hidden.bs.modal", handleModalHide);

    return () => {
      modalElement.removeEventListener("shown.bs.modal", handleModalShow);
      modalElement.removeEventListener("hidden.bs.modal", handleModalHide);
    };
  }, []);

  useEffect(() => {
    fetchWeekOffs();
  }, []);

  const fetchWeekOffs = async () => {
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");

      if (!admin_id) {
        toast.error("Admin ID not found");
        return;
      }

      const response = await axios.get(
        `http://127.0.0.1:8000/api/week-off-policies/${admin_id}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const weekOffsData = response.data.data || response.data;
      setWeekOffs(Array.isArray(weekOffsData) ? weekOffsData : []);
    } catch (error: any) {
      console.error("Error fetching week offs:", error);
      toast.error("Failed to fetch week offs");
      setWeekOffs([]);
    } finally {
      setLoadingWeekOffs(false);
    }
  };

  const fetchAssignedWeekOffs = async () => {
    // Use employeeRef for stable reference
    const emp = employeeRef.current || currentEmployee;
    
    console.log("🔄 fetchAssignedWeekOffs - Employee check:", { 
      employeeRef: employeeRef.current, 
      currentEmployee,
      emp 
    });
    
    if (!emp) {
      console.warn("⚠️ No employee for fetchAssignedWeekOffs, clearing list");
      setAssignedWeekOffs([]);
      return;
    }

    if (activeTab === "summary") {
      setLoadingSummary(true);
    }

    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");
      const employeeUserId =
        emp.user?.id ||
        emp.user_id ||
        emp.id;

      if (!admin_id || !employeeUserId) return;

      console.log(
        `🔄 Fetching assigned week offs for ${
          emp.user_name || "employee"
        }...`
      );

      const response = await axios.get(
        `http://127.0.0.1:8000/api/assign-week-offs/${admin_id}/${employeeUserId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      console.log("📥 Raw Response:", response.data);
      
      const weekOffsData = response.data.data?.assigned_week_offs || [];
      console.log("📦 Extracted weekOffsData:", weekOffsData);
      
      setAssignedWeekOffs(Array.isArray(weekOffsData) ? weekOffsData : []);

      const assignedIds = weekOffsData.map((weekOff: any) => weekOff.id);
      setSelectedWeekOffs(assignedIds);

      console.log(
        `✅ Fetched ${weekOffsData.length} assigned week off(s), pre-selected:`,
        assignedIds
      );
    } catch (error: any) {
      console.error("❌ ERROR fetching assigned week offs:", error);
      console.error("Error details:", error.response?.data);
      setAssignedWeekOffs([]);
      setSelectedWeekOffs([]);
    } finally {
      if (activeTab === "summary") {
        setLoadingSummary(false);
      }
    }
  };

  useEffect(() => {
    if (currentEmployee) {
      fetchAssignedWeekOffs();
    }
  }, [currentEmployee]);

  // Fetch data when tab changes (only for summary tab to refresh data)
  useEffect(() => {
    if (currentEmployee && activeTab === 'summary') {
      console.log(`📑 Tab switched to: ${activeTab}`);
      fetchAssignedWeekOffs();
    }
  }, [activeTab]);

  const handleWeekOffToggle = (weekOffId: number) => {
    if (selectedWeekOffs.includes(weekOffId)) {
      const updatedWeekOffs = selectedWeekOffs.filter((id) => id !== weekOffId);
      console.log(
        `❌ Deselected Week Off ${weekOffId}. Remaining selected:`,
        updatedWeekOffs
      );
      setSelectedWeekOffs(updatedWeekOffs);
    } else {
      const updatedWeekOffs = [...selectedWeekOffs, weekOffId];
      console.log(
        `✅ Selected Week Off ${weekOffId}. Now selected:`,
        updatedWeekOffs
      );
      setSelectedWeekOffs(updatedWeekOffs);
    }
  };

  const isWeekOffAssigned = (weekOffId: number) => {
    return assignedWeekOffs.some((w) => w.id === weekOffId);
  };

  const handleAssign = async () => {
    // Use employeeRef for stable reference
    const emp = employeeRef.current || employee || currentEmployee;
    
    console.log("🔍 handleAssign - Employee check:", { 
      employeeRef: employeeRef.current, 
      employeeProp: employee,
      currentEmployee,
      emp 
    });
    
    if (!emp) {
      console.error("❌ No employee found for assign");
      toast.error("No employee selected");
      return;
    }

    if (selectedWeekOffs.length === 0) {
      toast.error("Please select at least one week off policy");
      return;
    }

    console.log("🔥 Assigning these week off IDs:", selectedWeekOffs);

    setLoading(true);
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");

      if (!admin_id) {
        toast.error("Admin ID not found");
        setLoading(false);
        return;
      }

      const employeeUserId =
        emp.user?.id ||
        emp.user_id ||
        emp.id;

      console.log("Employee object:", emp);
      console.log("Extracted User ID:", employeeUserId);
      console.log("Admin ID:", admin_id);
      
      if (!employeeUserId) {
        toast.error("Employee ID not found in employee object");
        console.error("Employee structure:", JSON.stringify(emp));
        setLoading(false);
        return;
      }

      console.log("📤 Sending to backend:", { week_off_ids: selectedWeekOffs });

      const response = await axios.post(
        `http://127.0.0.1:8000/api/assign-week-offs/${admin_id}/${employeeUserId}`,
        { week_off_ids: selectedWeekOffs },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      console.log("✅ Assignment response:", response.data);

      toast.success(
        response.data.message || "Week offs assigned successfully"
      );

      await fetchAssignedWeekOffs();

      onWeekOffAssigned?.(response.data);
    } catch (error: any) {
      console.error("Error assigning week offs:", error);
      const errorMessage =
        error.response?.data?.message || "Failed to assign week offs";
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAll = () => {
    console.log("Select All clicked. Current selected:", selectedWeekOffs.length, "Total:", weekOffs.length);
    const unassignedWeekOffs = weekOffs.filter(w => !isWeekOffAssigned(w.id));
    const allUnassignedSelected = unassignedWeekOffs.every(w => selectedWeekOffs.includes(w.id));
    
    if (allUnassignedSelected && unassignedWeekOffs.length > 0) {
      const assignedIds = assignedWeekOffs.map(w => w.id);
      console.log("Deselecting all unassigned week offs, keeping assigned");
      setSelectedWeekOffs(assignedIds);
    } else {
      const unassignedIds = unassignedWeekOffs.map((w) => w.id);
      const assignedIds = assignedWeekOffs.map(w => w.id);
      const allIds = [...assignedIds, ...unassignedIds];
      console.log("Selecting all unassigned week offs:", unassignedIds);
      setSelectedWeekOffs(allIds);
    }
  };

  const handleUnassignSingle = async (weekOffId: number, weekOffName: string) => {
    // Use employeeRef to get stable employee reference
    const emp = employeeRef.current || employee || currentEmployee;
    
    console.log("🔍 handleUnassignSingle called with:", { 
      weekOffId, 
      weekOffName, 
      emp,
      employeeRef: employeeRef.current,
      employeeProp: employee,
      currentEmployee 
    });
    
    if (!emp) {
      console.error("❌ No employee found:", { 
        employeeRef: employeeRef.current, 
        employee, 
        currentEmployee 
      });
      toast.error("No employee selected");
      return;
    }

    console.log("✅ Employee exists:", emp);
    setLoading(true);
    
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");
      const employeeUserId = emp?.user?.id || emp?.user_id || emp?.id;

      console.log("📋 IDs:", { admin_id, employeeUserId, weekOffId });

      if (!admin_id || !employeeUserId) {
        console.error("❌ Missing IDs:", { admin_id, employeeUserId });
        toast.error("Missing required information");
        setLoading(false);
        return;
      }

      const deleteUrl = `http://127.0.0.1:8000/api/assign-week-offs/${admin_id}/${employeeUserId}/${weekOffId}`;
      console.log(`🗑️ Removing week off ${weekOffId} from employee ${employeeUserId}`);
      console.log(`📡 DELETE URL: ${deleteUrl}`);

      const response = await axios.delete(
        deleteUrl,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      
      console.log(`✅ DELETE Response:`, response.data);

      toast.success(response.data.message || `Week off '${weekOffName}' removed successfully`);
      
      console.log("🔄 Refreshing assigned week offs after delete...");
      // Refresh data
      await fetchAssignedWeekOffs();
      console.log("✅ Refresh complete");
      
      onWeekOffAssigned?.(response.data);
    } catch (error: any) {
      console.error("Error removing week off:", error);
      const errorMessage = error.response?.data?.message || "Failed to remove week off";
      toast.error(errorMessage, { autoClose: 6000 });
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setSelectedWeekOffs([]);
    setActiveTab("assign");
    onClose?.();
  };

  return (
    <div className="modal fade" id="assign_week_off_modal">
      <div className="modal-dialog modal-dialog-centered modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h4 className="modal-title">
              Assign Week Offs{" "}
              {currentEmployee
                ? `to ${
                    currentEmployee.user_name ||
                    currentEmployee.user?.email ||
                    currentEmployee.email
                  }`
                : ""}
            </h4>
            <button
              type="button"
              className="btn-close custom-btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            >
              <i className="ti ti-x" />
            </button>
          </div>
          <div className="modal-body">
            {/* Tabs */}
            <ul className="nav nav-tabs mb-3" role="tablist">
              <li className="nav-item" role="presentation">
                <button
                  className={`nav-link ${
                    activeTab === "assign" ? "active" : ""
                  }`}
                  onClick={() => setActiveTab("assign")}
                  type="button"
                  role="tab"
                >
                  <i className="ti ti-calendar-plus me-2" />
                  Assign Week Offs
                </button>
              </li>
              <li className="nav-item" role="presentation">
                <button
                  className={`nav-link ${
                    activeTab === "summary" ? "active" : ""
                  }`}
                  onClick={() => setActiveTab("summary")}
                  type="button"
                  role="tab"
                >
                  <i className="ti ti-report me-2" />
                  Week Off Summary
                </button>
              </li>
            </ul>

            {/* Tab Content */}
            {activeTab === "assign" ? (
              <>
                {loadingWeekOffs ? (
                  <div className="text-center py-4">
                    <div className="spinner-border" role="status">
                      <span className="visually-hidden">Loading...</span>
                    </div>
                  </div>
                ) : weekOffs.length === 0 ? (
                  <div className="alert alert-info">
                    No week off policies available. Please create some first.
                  </div>
                ) : (
                  <div className="table-responsive">
                    <table className="table table-hover">
                      <thead>
                        <tr>
                          <th style={{ width: "50px" }}>
                            <input
                              type="checkbox"
                              className="form-check-input"
                              checked={
                                weekOffs.filter(w => !isWeekOffAssigned(w.id)).length > 0 &&
                                weekOffs.filter(w => !isWeekOffAssigned(w.id)).every(w => selectedWeekOffs.includes(w.id))
                              }
                              onChange={handleSelectAll}
                            />
                          </th>
                          <th>Policy Name</th>
                          <th>Week Days</th>
                          <th>Description</th>
                          <th style={{ width: "100px" }}>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {weekOffs.map((weekOff) => {
                          const isSelected = selectedWeekOffs.includes(
                            weekOff.id
                          );
                          const alreadyAssigned = isWeekOffAssigned(weekOff.id);

                          return (
                            <tr key={weekOff.id} className={alreadyAssigned ? "table-secondary" : ""}>
                              <td>
                                {alreadyAssigned ? (
                                  <span 
                                    className="badge bg-secondary d-flex align-items-center justify-content-center" 
                                    style={{ width: '24px', height: '24px' }}
                                    title="Already Assigned"
                                  >
                                    <i className="ti ti-check" />
                                  </span>
                                ) : (
                                  <input
                                    type="checkbox"
                                    className="form-check-input"
                                    checked={isSelected}
                                    onChange={() => handleWeekOffToggle(weekOff.id)}
                                  />
                                )}
                              </td>
                              <td>
                                <strong>{weekOff.name}</strong>
                                {alreadyAssigned && (
                                  <>
                                    <br />
                                    <small className="text-muted">Currently Assigned</small>
                                  </>
                                )}
                              </td>
                              <td>
                                {Array.isArray(weekOff.week_days)
                                  ? weekOff.week_days.join(", ")
                                  : "-"}
                              </td>
                              <td>{weekOff.description || "-"}</td>
                              <td>
                                {alreadyAssigned ? (
                                  <button
                                    type="button"
                                    className="btn btn-sm btn-outline-danger"
                                    onClick={() => handleUnassignSingle(weekOff.id, weekOff.name)}
                                    disabled={loading}
                                    title="Unassign this week off policy"
                                  >
                                    <i className="ti ti-trash me-1"></i>
                                    Unassign
                                  </button>
                                ) : (
                                  <span className="text-muted">-</span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            ) : (
              <>
                {loadingSummary ? (
                  <div className="text-center py-4">
                    <div className="spinner-border" role="status">
                      <span className="visually-hidden">Loading...</span>
                    </div>
                  </div>
                ) : assignedWeekOffs.length === 0 ? (
                  <div className="alert alert-info">
                    No week off policies assigned to this employee yet.
                  </div>
                ) : (
                  <div className="table-responsive">
                    <table className="table table-hover">
                      <thead>
                        <tr>
                          <th>Policy Name</th>
                          <th>Week Days</th>
                          <th>Description</th>
                          <th style={{ width: "100px" }}>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {assignedWeekOffs.map((weekOff) => (
                          <tr key={weekOff.id}>
                            <td>
                              <strong>{weekOff.name}</strong>
                            </td>
                            <td>
                              {Array.isArray(weekOff.week_days)
                                ? weekOff.week_days.join(", ")
                                : "-"}
                            </td>
                            <td>{weekOff.description || "-"}</td>
                            <td>
                              <button
                                type="button"
                                className="btn btn-sm btn-outline-danger"
                                onClick={() => handleUnassignSingle(weekOff.id, weekOff.name)}
                                disabled={loading}
                                title="Remove this week off policy"
                              >
                                <i className="ti ti-trash"></i>
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </div>
          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-light me-2"
              data-bs-dismiss="modal"
              onClick={handleCancel}
            >
              Close
            </button>
            {activeTab === "assign" && (
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleAssign}
                disabled={loading || selectedWeekOffs.length === 0}
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" />
                    Assigning...
                  </>
                ) : (
                  <>
                    <i className="ti ti-check me-2" />
                    Assign Week Offs
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssignWeekOffModal;

