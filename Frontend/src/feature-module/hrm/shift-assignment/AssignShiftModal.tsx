import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import { toast } from "react-toastify";
import { removeAllBackdrops, resetBodyStyles, cleanupExcessBackdrops } from "../../../core/utils/modalHelpers";

type AssignShiftModalProps = {
  employee?: any;
  onShiftAssigned?: (result: any) => void;
  onClose?: () => void;
};

type ShiftOption = {
  id: number;
  shift_name: string;
  start_time: string;
  end_time: string;
  break_duration_minutes: number;
  duration_minutes: number;
  is_night_shift: boolean;
};

const AssignShiftModal: React.FC<AssignShiftModalProps> = ({
  employee,
  onShiftAssigned,
  onClose,
}) => {
  const [shifts, setShifts] = useState<ShiftOption[]>([]);
  const [selectedShifts, setSelectedShifts] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingShifts, setLoadingShifts] = useState(true);
  const [assignedShifts, setAssignedShifts] = useState<ShiftOption[]>([]);
  
  // Store employee data locally to prevent issues if parent nullifies it
  const [currentEmployee, setCurrentEmployee] = useState<any>(null);
  const employeeRef = useRef<any>(null);

  // Tab state
  const [activeTab, setActiveTab] = useState<'assign' | 'summary'>('assign');
  const [loadingSummary, setLoadingSummary] = useState(false);

  // Sync employee prop to local state and ref
  useEffect(() => {
    if (employee) {
      console.log('Setting current employee:', employee);
      setCurrentEmployee(employee);
      employeeRef.current = employee;
    }
  }, [employee]);

  // Cleanup modal backdrops when modal opens/closes
  useEffect(() => {
    const modalElement = document.getElementById('assign_shift_modal');
    if (!modalElement) return;

    const handleModalShow = () => {
      // Clean up any stray backdrops before showing using utility function
      setTimeout(() => {
        cleanupExcessBackdrops();
      }, 50);
      
      // Fetch latest assigned shifts to pre-select them
      if (currentEmployee) {
        fetchAssignedShifts();
      }
    };

    const handleModalHide = () => {
      // Clean up when modal is hidden using utility functions
      setTimeout(() => {
        removeAllBackdrops();
        resetBodyStyles();
      }, 150);
    };

    // Add event listeners for Bootstrap modal events
    modalElement.addEventListener('shown.bs.modal', handleModalShow);
    modalElement.addEventListener('hidden.bs.modal', handleModalHide);

    return () => {
      modalElement.removeEventListener('shown.bs.modal', handleModalShow);
      modalElement.removeEventListener('hidden.bs.modal', handleModalHide);
    };
  }, []);

  // Fetch available shifts on mount
  useEffect(() => {
    fetchShifts();
  }, []);

  // Function to fetch shifts from API
  const fetchShifts = async () => {
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");

      if (!admin_id) {
        toast.error("Admin ID not found");
        return;
      }

      const response = await axios.get(
        `http://127.0.0.1:8000/api/service-shifts/${admin_id}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const shiftsData = response.data.data || response.data;
      setShifts(Array.isArray(shiftsData) ? shiftsData : []);
    } catch (error: any) {
      console.error("Error fetching shifts:", error);
      toast.error("Failed to fetch shifts");
      setShifts([]);
    } finally {
      setLoadingShifts(false);
    }
  };

  // Function to fetch assigned shifts from API
  const fetchAssignedShifts = async () => {
    // Use employeeRef for stable reference
    const emp = employeeRef.current || currentEmployee;
    
    console.log("🔄 fetchAssignedShifts - Employee check:", { 
      employeeRef: employeeRef.current, 
      currentEmployee,
      emp 
    });
    
    if (!emp) {
      console.warn("⚠️ No employee for fetchAssignedShifts, clearing list");
      setAssignedShifts([]);
      return;
    }

    // Set loading state based on active tab
    if (activeTab === 'summary') {
      setLoadingSummary(true);
    }

    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");
      const employeeUserId = emp.user?.id || emp.user_id || emp.id;

      if (!admin_id || !employeeUserId) return;

      console.log(`🔄 Fetching assigned shifts for ${emp.user_name || 'employee'}...`);
      
      const response = await axios.get(
        `http://127.0.0.1:8000/api/assign-shifts/${admin_id}/${employeeUserId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      console.log("📥 Raw Response:", response.data);
      
      const shiftsData = response.data.data?.assigned_shifts || [];
      console.log("📦 Extracted shiftsData:", shiftsData);
      
      setAssignedShifts(Array.isArray(shiftsData) ? shiftsData : []);
      
      // Pre-select already assigned shifts
      const assignedIds = shiftsData.map((shift: any) => shift.id);
      setSelectedShifts(assignedIds);
      
      console.log(`✅ Fetched ${shiftsData.length} assigned shift(s), pre-selected:`, assignedIds);
    } catch (error: any) {
      console.error("❌ ERROR fetching assigned shifts:", error);
      console.error("Error details:", error.response?.data);
      setAssignedShifts([]);
      setSelectedShifts([]);
    } finally {
      if (activeTab === 'summary') {
        setLoadingSummary(false);
      }
    }
  };

  // Fetch assigned shifts when employee changes
  useEffect(() => {
    if (currentEmployee) {
      fetchAssignedShifts(); // This will pre-select assigned shifts
    }
  }, [currentEmployee]);

  // Fetch data when tab changes (only for summary tab to refresh data)
  useEffect(() => {
    if (currentEmployee && activeTab === 'summary') {
      console.log(`📑 Tab switched to: ${activeTab}`);
      fetchAssignedShifts();
    }
  }, [activeTab]);

  const handleShiftToggle = (shiftId: number) => {
    if (selectedShifts.includes(shiftId)) {
      // Unselect: Remove from selected array
      const updatedShifts = selectedShifts.filter((id) => id !== shiftId);
      console.log(`❌ Deselected Shift ${shiftId}. Remaining selected:`, updatedShifts);
      setSelectedShifts(updatedShifts);
    } else {
      // Select: Add to selected array
      const updatedShifts = [...selectedShifts, shiftId];
      console.log(`✅ Selected Shift ${shiftId}. Now selected:`, updatedShifts);
      setSelectedShifts(updatedShifts);
    }
  };

  const isShiftAssigned = (shiftId: number) => {
    return assignedShifts.some((s) => s.id === shiftId);
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

    if (selectedShifts.length === 0) {
      toast.error("Please select at least one shift");
      return;
    }

    console.log("🔥 Assigning these shift IDs:", selectedShifts);
    
    setLoading(true);
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");

      if (!admin_id) {
        toast.error("Admin ID not found");
        setLoading(false);
        return;
      }

      const employeeUserId = emp.user?.id || emp.user_id || emp.id;
      
      console.log("Employee object:", emp);
      console.log("Extracted User ID:", employeeUserId);
      console.log("Admin ID:", admin_id);
      
      if (!employeeUserId) {
        toast.error("Employee ID not found in employee object");
        console.error("Employee structure:", JSON.stringify(emp));
        setLoading(false);
        return;
      }

      console.log("📤 Sending to backend:", { shift_ids: selectedShifts });

      const response = await axios.post(
        `http://127.0.0.1:8000/api/assign-shifts/${admin_id}/${employeeUserId}`,
        { shift_ids: selectedShifts },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      console.log("✅ Assignment response:", response.data);
      
      toast.success(response.data.message || "Shifts assigned successfully");
      
      // Refresh data (this will pre-select the newly assigned shifts)
      await fetchAssignedShifts();
      
      onShiftAssigned?.(response.data);
    } catch (error: any) {
      console.error("Error assigning shifts:", error);
      const errorMessage = error.response?.data?.message || "Failed to assign shifts";
      toast.error(errorMessage);
      setSelectedShifts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleUnassignAll = async () => {
    // Use employeeRef for stable reference
    const emp = employeeRef.current || employee || currentEmployee;
    
    if (!emp) {
      toast.error("No employee selected");
      return;
    }

    if (assignedShifts.length === 0) {
      toast.error("No shifts assigned to remove");
      return;
    }

    setLoading(true);
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");
      const employeeUserId = emp?.user?.id || emp?.user_id || emp?.id;

      if (!admin_id || !employeeUserId) {
        toast.error("Missing required information");
        setLoading(false);
        return;
      }

      const response = await axios.delete(
        `http://127.0.0.1:8000/api/assign-shifts/${admin_id}/${employeeUserId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      toast.success(response.data.message || "All shifts removed successfully");
      
      // Refresh data
      await fetchAssignedShifts();
      
      onShiftAssigned?.(response.data);
    } catch (error: any) {
      console.error("Error removing shifts:", error);
      const errorMessage = error.response?.data?.message || "Failed to remove shifts";
      toast.error(errorMessage, { autoClose: 6000 });
    } finally {
      setLoading(false);
    }
  };

  const handleUnassignSingle = async (shiftId: number, shiftName: string) => {
    // Use employeeRef to get stable employee reference
    const emp = employeeRef.current || employee || currentEmployee;
    
    console.log("🔍 handleUnassignSingle called with:", { 
      shiftId, 
      shiftName, 
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

    setLoading(true);
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");
      const employeeUserId = emp?.user?.id || emp?.user_id || emp?.id;

      if (!admin_id || !employeeUserId) {
        toast.error("Missing required information");
        setLoading(false);
        return;
      }

      const deleteUrl = `http://127.0.0.1:8000/api/assign-shifts/${admin_id}/${employeeUserId}/${shiftId}`;
      console.log(`🗑️ Removing shift ${shiftId} from employee ${employeeUserId}`);
      console.log(`📡 DELETE URL: ${deleteUrl}`);

      const response = await axios.delete(
        deleteUrl,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      
      console.log(`✅ DELETE Response:`, response.data);

      toast.success(response.data.message || `Shift '${shiftName}' removed successfully`);
      
      // Refresh data
      await fetchAssignedShifts();
      
      onShiftAssigned?.(response.data);
    } catch (error: any) {
      console.error("Error removing shift:", error);
      const errorMessage = error.response?.data?.message || "Failed to remove shift";
      toast.error(errorMessage, { autoClose: 6000 });
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setSelectedShifts([]);
    setActiveTab('assign');
    onClose?.();
  };

  const formatTime = (time: string) => {
    if (!time) return '-';
    // Convert 24h to 12h format
    const [hours, minutes] = time.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const hour12 = hour % 12 || 12;
    return `${hour12}:${minutes} ${ampm}`;
  };

  return (
    <div className="modal fade" id="assign_shift_modal">
      <div className="modal-dialog modal-dialog-centered modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h4 className="modal-title">
              Assign Shifts {currentEmployee ? `to ${currentEmployee.user_name || currentEmployee.user?.email || currentEmployee.email}` : ""}
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
                  className={`nav-link ${activeTab === 'assign' ? 'active' : ''}`}
                  onClick={() => setActiveTab('assign')}
                  type="button"
                  role="tab"
                >
                  <i className="ti ti-clock-plus me-2" />
                  Assign Shifts
                </button>
              </li>
              <li className="nav-item" role="presentation">
                <button
                  className={`nav-link ${activeTab === 'summary' ? 'active' : ''}`}
                  onClick={() => setActiveTab('summary')}
                  type="button"
                  role="tab"
                >
                  <i className="ti ti-report me-2" />
                  Shift Summary
                </button>
              </li>
            </ul>

            {/* Tab Content */}
            {activeTab === 'assign' ? (
              /* Assign Shifts Tab */
              <>
                {/* Shift Selection */}
                <div className="row">
                  <div className="col-12">
                    <h6 className="mb-3">Select Shifts</h6>
                    {loadingShifts ? (
                      <p>Loading shifts...</p>
                    ) : shifts.length === 0 ? (
                      <p className="text-muted">No shifts available. Please create shifts first.</p>
                    ) : (
                      <div className="table-responsive">
                        {assignedShifts.length > 0 && (
                          <div className="border-start border-secondary border-3 bg-light p-2 mb-3">
                            <small className="text-muted">
                              <i className="ti ti-info-circle me-2" />
                              <strong>{assignedShifts.length} shift(s)</strong> already assigned. 
                              Select new shifts or remove all to reassign.
                            </small>
                          </div>
                        )}
                        <table className="table table-bordered table-hover">
                          <thead className="table-light">
                            <tr>
                              <th style={{ width: "50px" }}>
                                <input
                                  type="checkbox"
                                  className="form-check-input"
                                  onChange={(e) => {
                                    console.log("Select All clicked:", e.target.checked);
                                    const unassignedShifts = shifts.filter(s => !isShiftAssigned(s.id));
                                    if (e.target.checked) {
                                      const unassignedIds = unassignedShifts.map((s) => s.id);
                                      const assignedIds = assignedShifts.map(s => s.id);
                                      const allIds = [...assignedIds, ...unassignedIds];
                                      console.log("Selecting all unassigned shifts:", unassignedIds);
                                      setSelectedShifts(allIds);
                                    } else {
                                      const assignedIds = assignedShifts.map(s => s.id);
                                      console.log("Deselecting all unassigned shifts, keeping assigned");
                                      setSelectedShifts(assignedIds);
                                    }
                                  }}
                                  checked={
                                    shifts.filter(s => !isShiftAssigned(s.id)).length > 0 &&
                                    shifts.filter(s => !isShiftAssigned(s.id)).every(s => selectedShifts.includes(s.id))
                                  }
                                />
                              </th>
                              <th>Shift Name</th>
                              <th>Timing</th>
                              <th>Duration</th>
                              <th>Type</th>
                              <th style={{ width: "100px" }}>Action</th>
                            </tr>
                          </thead>
                          <tbody>
                            {shifts.map((shift) => {
                              const isSelected = selectedShifts.includes(shift.id);
                              const alreadyAssigned = isShiftAssigned(shift.id);

                              return (
                                <tr key={shift.id} className={alreadyAssigned ? "table-secondary" : ""}>
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
                                        onChange={() => handleShiftToggle(shift.id)}
                                      />
                                    )}
                                  </td>
                                  <td>
                                    <strong>{shift.shift_name}</strong>
                                    {alreadyAssigned && (
                                      <>
                                        <br />
                                        <small className="text-muted">Currently Assigned</small>
                                      </>
                                    )}
                                  </td>
                                  <td>
                                    <i className="ti ti-clock me-1"></i>
                                    {formatTime(shift.start_time)} - {formatTime(shift.end_time)}
                                  </td>
                                  <td>
                                    <span className="badge bg-light text-dark border">
                                      {Math.floor(shift.duration_minutes / 60)}h {shift.duration_minutes % 60}m
                                    </span>
                                    {shift.break_duration_minutes > 0 && (
                                      <small className="d-block text-muted mt-1">
                                        Break: {shift.break_duration_minutes} min
                                      </small>
                                    )}
                                  </td>
                                  <td>
                                    {shift.is_night_shift ? (
                                      <span className="badge bg-dark">
                                        <i className="ti ti-moon me-1"></i>
                                        Night
                                      </span>
                                    ) : (
                                      <span className="badge bg-light text-dark border">
                                        <i className="ti ti-sun me-1"></i>
                                        Day
                                      </span>
                                    )}
                                  </td>
                                  <td>
                                    {alreadyAssigned ? (
                                      <button
                                        type="button"
                                        className="btn btn-sm btn-outline-danger"
                                        onClick={() => handleUnassignSingle(shift.id, shift.shift_name)}
                                        disabled={loading}
                                        title="Unassign this shift"
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
                  </div>
                </div>

                {/* Selected Summary */}
                {selectedShifts.length > 0 && (
                  <div className="border p-3 mt-3 rounded bg-light">
                    <small className="text-muted">
                      <strong>Selected {selectedShifts.length} shift(s):</strong>
                    </small>
                    <ul className="mb-0 mt-2 small">
                      {selectedShifts.map((shiftId) => {
                        const shift = shifts.find(s => s.id === shiftId);
                        return shift ? (
                          <li key={shiftId} className="text-muted">
                            {shift.shift_name} ({formatTime(shift.start_time)} - {formatTime(shift.end_time)})
                          </li>
                        ) : null;
                      })}
                    </ul>
                  </div>
                )}

                {/* Remove All Button */}
                {assignedShifts.length > 0 && (
                  <div className="alert alert-warning mt-3">
                    <div className="d-flex justify-content-between align-items-center">
                      <div>
                        <i className="ti ti-alert-circle me-2"></i>
                        <strong>{assignedShifts.length} shift(s)</strong> currently assigned
                      </div>
                      <button
                        type="button"
                        className="btn btn-sm btn-outline-danger"
                        onClick={handleUnassignAll}
                        disabled={loading}
                      >
                        <i className="ti ti-trash me-1"></i>
                        Remove All Shifts
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              /* Shift Summary Tab */
              <div className="shift-summary-content">
                {loadingSummary ? (
                  <div className="text-center py-4">
                    <div className="spinner-border text-primary" role="status">
                      <span className="visually-hidden">Loading...</span>
                    </div>
                    <p className="mt-2">Loading shift summary...</p>
                  </div>
                ) : assignedShifts.length === 0 ? (
                  <div className="text-center py-4">
                    <i className="ti ti-clock-off fs-1 text-muted" />
                    <p className="mt-2 text-muted">
                      No shifts assigned. Please assign shifts from the "Assign Shifts" tab.
                    </p>
                  </div>
                ) : (
                  <>
                    {/* Summary Card */}
                    <div className="row mb-4">
                      <div className="col-12">
                        <div className="card border shadow-sm">
                          <div className="card-body text-center">
                            <div className="mb-2">
                              <i className="ti ti-clock fs-1"></i>
                            </div>
                            <h3 className="mb-1">{assignedShifts.length}</h3>
                            <p className="text-muted mb-0">Total Assigned Shifts</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Detailed Table */}
                    <div className="table-responsive">
                      <table className="table table-bordered table-hover">
                        <thead className="table-light">
                          <tr>
                            <th>Shift Name</th>
                            <th>Timing</th>
                            <th>Duration</th>
                            <th style={{ width: "100px" }}>Action</th>
                            <th>Type</th>
                          </tr>
                        </thead>
                        <tbody>
                          {assignedShifts.map((shift: any) => (
                            <tr key={shift.id}>
                              <td>
                                <div className="d-flex align-items-center">
                                  <span className="avatar avatar-sm bg-light text-dark border me-2 d-flex align-items-center justify-content-center">
                                    <i className="ti ti-clock"></i>
                                  </span>
                                  <strong>{shift.shift_name}</strong>
                                </div>
                              </td>
                              <td>
                                <span className="badge bg-light text-dark border d-inline-flex align-items-center">
                                  <i className="ti ti-clock me-1"></i>
                                  {formatTime(shift.start_time)} - {formatTime(shift.end_time)}
                                </span>
                              </td>
                              <td>
                                <span className="badge bg-light text-dark border d-inline-flex align-items-center">
                                  <i className="ti ti-calendar-time me-1"></i>
                                  {Math.floor(shift.duration_minutes / 60)}h {shift.duration_minutes % 60}m
                                </span>
                                {shift.break_duration_minutes > 0 && (
                                  <small className="d-block text-muted mt-1">
                                    <i className="ti ti-coffee me-1"></i>
                                    Break: {shift.break_duration_minutes} min
                                  </small>
                                )}
                              </td>
                              <td>
                                <button
                                  type="button"
                                  className="btn btn-sm btn-outline-danger"
                                  onClick={() => handleUnassignSingle(shift.id, shift.shift_name)}
                                  disabled={loading}
                                  title="Remove this shift"
                                >
                                  <i className="ti ti-trash"></i>
                                </button>
                              </td>
                              <td>
                                {shift.is_night_shift ? (
                                  <span className="badge bg-light text-dark border d-inline-flex align-items-center">
                                    <i className="ti ti-moon me-1"></i>
                                    Night Shift
                                  </span>
                                ) : (
                                  <span className="badge bg-light text-dark border d-inline-flex align-items-center">
                                    <i className="ti ti-sun me-1"></i>
                                    Day Shift
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
          <div className="modal-footer border-top">
            <button
              type="button"
              className="btn btn-outline-secondary"
              data-bs-dismiss="modal"
              onClick={handleCancel}
            >
              <i className="ti ti-x me-2" />
              {activeTab === 'summary' ? 'Close' : 'Cancel'}
            </button>
            {activeTab === 'assign' && (
              <button
                type="button"
                className="btn btn-dark"
                onClick={handleAssign}
                disabled={
                  loading || 
                  selectedShifts.length === 0 || 
                  !currentEmployee
                }
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" />
                    Assigning...
                  </>
                ) : (
                  <>
                    <i className="ti ti-check me-2" />
                    Assign Shifts {selectedShifts.length > 0 && `(${selectedShifts.length})`}
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

export default AssignShiftModal;

