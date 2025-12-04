import React, { useEffect, useState } from "react";
import axios from "axios";
import { toast } from "react-toastify";
import { removeAllBackdrops, resetBodyStyles, cleanupExcessBackdrops, closeModal, openModal } from "../../../core/utils/modalHelpers";

type AssignLeaveModalProps = {
  employee?: any;
  onLeaveAssigned?: (result: any) => void;
  onClose?: () => void;
  onOpenLeaveApplications?: () => void;
  onOpenApplyLeave?: () => void;
};

type LeaveTypeOption = {
  id: number;
  name: string;
  code: string;
  default_count: number;
  is_paid: boolean;
};

type LeaveAssignment = {
  leave_type: number;
  assigned?: number;
  use_default: boolean;
};

const AssignLeaveModal: React.FC<AssignLeaveModalProps> = ({
  employee,
  onLeaveAssigned,
  onClose,
  onOpenLeaveApplications,
  onOpenApplyLeave,
}) => {
  const [leaveTypes, setLeaveTypes] = useState<LeaveTypeOption[]>([]);
  const [selectedLeaves, setSelectedLeaves] = useState<LeaveAssignment[]>([]);
  const year = new Date().getFullYear(); // Always use current year
  const [loading, setLoading] = useState(false);
  const [loadingLeaveTypes, setLoadingLeaveTypes] = useState(true);
  const [existingBalances, setExistingBalances] = useState<any[]>([]);
  const [editingBalance, setEditingBalance] = useState<{[key: number]: boolean}>({});
  const [editValues, setEditValues] = useState<{[key: number]: number}>({});
  const [loadingItems, setLoadingItems] = useState<{[key: number]: boolean}>({});
  
  // Store employee data locally to prevent issues if parent nullifies it
  const [currentEmployee, setCurrentEmployee] = useState<any>(null);
  
  // Tab state
  const [activeTab, setActiveTab] = useState<'assign' | 'summary'>('assign');
  const [leaveSummary, setLeaveSummary] = useState<any[]>([]);
  const [loadingSummary, setLoadingSummary] = useState(false);

  // Sync employee prop to local state
  useEffect(() => {
    if (employee) {
      console.log('Setting current employee:', employee);
      setCurrentEmployee(employee);
    }
  }, [employee]);

  // Cleanup modal backdrops when modal opens/closes
  useEffect(() => {
    const modalElement = document.getElementById('assign_leave_modal');
    if (!modalElement) return;

    const handleModalShow = () => {
      // Clean up any stray backdrops before showing using utility function
      setTimeout(() => {
        cleanupExcessBackdrops();
      }, 50);
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

  // Fetch available leave types
  useEffect(() => {
    const fetchLeaveTypes = async () => {
      try {
        const token = sessionStorage.getItem("access_token");
        const admin_id = sessionStorage.getItem("user_id");

        if (!admin_id) {
          toast.error("Admin ID not found");
          return;
        }

        const response = await axios.get(
          `http://127.0.0.1:8000/api/leave-types/${admin_id}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        const types = response.data.data || response.data;
        setLeaveTypes(Array.isArray(types) ? types : []);
      } catch (error: any) {
        console.error("Error fetching leave types:", error);
        toast.error("Failed to fetch leave types");
        setLeaveTypes([]);
      } finally {
        setLoadingLeaveTypes(false);
      }
    };

    fetchLeaveTypes();
  }, []);

  // Function to fetch leave balances from API
  const fetchExistingBalances = async () => {
    if (!currentEmployee) {
      setExistingBalances([]);
      setLeaveSummary([]);
      return;
    }

    // Set loading state based on active tab
    if (activeTab === 'summary') {
      setLoadingSummary(true);
    }

    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");
      const employeeUserId = currentEmployee.user?.id || currentEmployee.user_id || currentEmployee.id;

      if (!admin_id || !employeeUserId) return;

      console.log(`🔄 Fetching leave balances for ${currentEmployee.user_name || 'employee'}...`);
      
      const response = await axios.get(
        `http://127.0.0.1:8000/api/leave-balances/${admin_id}/${employeeUserId}?year=${year}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const balances = response.data.data || response.data;
      setExistingBalances(Array.isArray(balances) ? balances : []);
      setLeaveSummary(Array.isArray(balances) ? balances : []);
      
      console.log(`✅ Fetched ${balances.length} leave balance(s)`);
    } catch (error: any) {
      console.error("Error fetching existing balances:", error);
      setExistingBalances([]);
      setLeaveSummary([]);
    } finally {
      if (activeTab === 'summary') {
        setLoadingSummary(false);
      }
    }
  };

  // Fetch existing balances when employee changes
  useEffect(() => {
    if (currentEmployee) {
      setSelectedLeaves([]);
      fetchExistingBalances();
    }
  }, [currentEmployee]); // year is always current year (constant)

  // Fetch data when tab changes (only for summary tab to refresh data)
  useEffect(() => {
    if (currentEmployee && activeTab === 'summary') {
      console.log(`📑 Tab switched to: ${activeTab}`);
      fetchExistingBalances();
    }
  }, [activeTab]); // Fetch fresh data when tab changes

  const handleLeaveTypeToggle = (leaveTypeId: number) => {
    console.log(`🔄 Toggle leave type ${leaveTypeId}`);
    
    // Prevent toggling if leave is already assigned
    if (isLeaveTypeAlreadyAssigned(leaveTypeId)) {
      console.log(`⚠️ Leave type ${leaveTypeId} is already assigned, cannot toggle`);
      toast.info("This leave type is already assigned. Use 'Unassign' button to remove it.");
      return;
    }
    
    const exists = selectedLeaves.find((l) => l.leave_type === leaveTypeId);

    if (exists) {
      // Remove if already selected
      console.log(`❌ Deselecting leave type ${leaveTypeId}`);
      setSelectedLeaves(selectedLeaves.filter((l) => l.leave_type !== leaveTypeId));
    } else {
      // Add with use_default true
      console.log(`✅ Selecting leave type ${leaveTypeId}`);
      setSelectedLeaves([
        ...selectedLeaves,
        {
          leave_type: leaveTypeId,
          use_default: true,
        },
      ]);
    }
  };

  const handleAssignedChange = (leaveTypeId: number, value: string) => {
    const leaveType = leaveTypes.find((lt) => lt.id === leaveTypeId);
    const maxAllowed = leaveType?.default_count || 0;
    
    // Validate against default_count
    if (value && parseFloat(value) > maxAllowed) {
      toast.warning(`Cannot assign more than ${maxAllowed} days for ${leaveType?.name}`);
      return;
    }
    
    setSelectedLeaves(
      selectedLeaves.map((leave) =>
        leave.leave_type === leaveTypeId
          ? {
              ...leave,
              assigned: value ? parseFloat(value) : undefined,
              use_default: !value,
            }
          : leave
      )
    );
  };

  const getLeaveTypeName = (id: number) => {
    const type = leaveTypes.find((lt) => lt.id === id);
    return type ? `${type.name} (${type.code})` : "";
  };

  const getDefaultCount = (id: number) => {
    const type = leaveTypes.find((lt) => lt.id === id);
    return type?.default_count || 0;
  };

  const isLeaveTypeAlreadyAssigned = (leaveTypeId: number) => {
    return existingBalances.some(
      (b) => (b.leave_type === leaveTypeId || b.leave_type_id === leaveTypeId)
    );
  };

  const getExistingBalance = (leaveTypeId: number) => {
    return existingBalances.find(
      (b) => (b.leave_type === leaveTypeId || b.leave_type_id === leaveTypeId)
    );
  };

  const handleAssign = async () => {
    if (!currentEmployee) {
      toast.error("No employee selected");
      return;
    }

    if (selectedLeaves.length === 0) {
      toast.error("Please select at least one leave type");
      return;
    }

    setLoading(true);
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");

      if (!admin_id) {
        toast.error("Admin ID not found");
        setLoading(false);
        return;
      }

      // Prepare payload based on single or bulk
      const payload: any = {
        year: year,
      };

      if (selectedLeaves.length === 1) {
        // Single format
        const leave = selectedLeaves[0];
        payload.leave_type = leave.leave_type;
        if (!leave.use_default && leave.assigned !== undefined) {
          payload.assigned = leave.assigned;
        }
      } else {
        // Bulk format
        payload.leaves = selectedLeaves.map((leave) => {
          const item: any = { leave_type: leave.leave_type };
          if (!leave.use_default && leave.assigned !== undefined) {
            item.assigned = leave.assigned;
          }
          return item;
        });
      }

      // Get the correct user ID from employee object
      // Staff list returns: currentEmployee.user.id
      const employeeUserId = currentEmployee.user?.id || currentEmployee.user_id || currentEmployee.id;
      
      console.log("Employee object:", currentEmployee);
      console.log("Extracted User ID:", employeeUserId);
      console.log("Admin ID:", admin_id);
      
      if (!employeeUserId) {
        toast.error("Employee ID not found in employee object");
        console.error("Employee structure:", JSON.stringify(currentEmployee));
        setLoading(false);
        return;
      }

      const response = await axios.post(
        `http://127.0.0.1:8000/api/assign-leaves/${admin_id}/${employeeUserId}`,
        payload,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      console.log("Assignment response:", response.data);
      
      // Check if there are any errors in the response
      const responseData = response.data.data;
      const hasErrors = responseData?.errors && responseData.errors.length > 0;
      const hasCreated = responseData?.created && responseData.created.length > 0;
      
      if (hasErrors && !hasCreated) {
        // All failed - show detailed errors
        responseData.errors.forEach((err: any) => {
          if (err.error) {
            toast.error(err.error);
          }
        });
      } else if (hasErrors && hasCreated) {
        // Partial success - show both
        toast.success(response.data.message || "Leaves assigned successfully");
        responseData.errors.forEach((err: any) => {
          if (err.error) {
            toast.warning(err.error);
          }
        });
      } else {
        // Full success
        toast.success(response.data.message || "Leaves assigned successfully");
      }
      
      // Refresh data using the common function
      await fetchExistingBalances();
      
      onLeaveAssigned?.(response.data);
      
      // Reset selected leaves after assignment
      setSelectedLeaves([]);
      
      // Don't close modal - let user see assigned leaves and edit if needed
    } catch (error: any) {
      console.error("Error assigning leaves:", error);
      
      // Extract detailed errors from response
      const errorData = error.response?.data?.data;
      if (errorData?.errors && errorData.errors.length > 0) {
        // Show each specific error
        errorData.errors.forEach((err: any) => {
          if (err.error) {
            toast.error(err.error);
          }
        });
      } else {
        // Generic error
        toast.error(error.response?.data?.message || "Failed to assign leaves");
      }
      
      // Don't close modal on error - let user try again or manually close
      setSelectedLeaves([]);
    } finally {
      setLoading(false);
    }
  };

  const handleEditClick = (leaveTypeId: number, currentAssigned: number) => {
    console.log('Edit clicked for leave type:', leaveTypeId, 'Current loading states:', loadingItems);
    setEditingBalance(prev => ({ ...prev, [leaveTypeId]: true }));
    setEditValues(prev => ({ ...prev, [leaveTypeId]: currentAssigned }));
  };

  const handleEditCancel = (leaveTypeId: number) => {
    setEditingBalance(prev => {
      const newState = { ...prev };
      delete newState[leaveTypeId];
      return newState;
    });
    setEditValues(prev => {
      const newState = { ...prev };
      delete newState[leaveTypeId];
      return newState;
    });
  };

  const handleEditSave = async (leaveTypeId: number) => {
    console.log('Save clicked for leave type:', leaveTypeId, 'Current loading states:', loadingItems);
    const existingBalance = getExistingBalance(leaveTypeId);
    if (!existingBalance) {
      console.log('No existing balance found for leave type:', leaveTypeId);
      return;
    }

    const newValue = editValues[leaveTypeId];
    console.log('New value:', newValue, 'Existing assigned:', existingBalance.assigned);
    if (newValue === undefined || newValue === existingBalance.assigned) {
      console.log('No change in value, canceling edit');
      handleEditCancel(leaveTypeId);
      return;
    }

    // Validation: Cannot be less than used
    if (newValue < existingBalance.used) {
      toast.error(`Cannot assign ${newValue} days. Employee has already used ${existingBalance.used} days`);
      return;
    }

    // Validation: Cannot exceed default_count
    const leaveType = leaveTypes.find(lt => lt.id === leaveTypeId);
    if (leaveType && newValue > leaveType.default_count) {
      toast.error(`Cannot assign ${newValue} days. Maximum allowed is ${leaveType.default_count} days`);
      return;
    }

    console.log('Starting API call to save leave. Setting loading state...');
    setLoadingItems(prev => ({ ...prev, [leaveTypeId]: true }));
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");
      const employeeUserId = currentEmployee?.user?.id || currentEmployee?.user_id || currentEmployee?.id;

      if (!admin_id || !employeeUserId) {
        toast.error("Missing required information");
        console.log('Missing info - admin_id:', admin_id, 'employeeUserId:', employeeUserId, 'currentEmployee:', currentEmployee);
        setLoadingItems(prev => ({ ...prev, [leaveTypeId]: false }));
        return;
      }

      const response = await axios.put(
        `http://127.0.0.1:8000/api/leave-balances/${admin_id}/${employeeUserId}/${existingBalance.id}`,
        { assigned: newValue },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      toast.success(response.data.message || "Leave balance updated successfully");
      console.log('API call successful, refreshing balances...');
      
      // Refresh data using the common function
      await fetchExistingBalances();
      console.log('Balances refreshed');
      
      // Clear edit state
      handleEditCancel(leaveTypeId);
      console.log('Edit state cleared for leave type:', leaveTypeId);
      
      // Call callback if provided
      onLeaveAssigned?.(response.data);
    } catch (error: any) {
      console.error("Error updating leave balance:", error);
      const errorMessage = error.response?.data?.message || "Failed to update leave balance";
      toast.error(errorMessage, { autoClose: 6000 });
    } finally {
      console.log('Finally block: Clearing loading state for leave type:', leaveTypeId);
      setLoadingItems(prev => {
        const newState = { ...prev, [leaveTypeId]: false };
        console.log('New loading states after clear:', newState);
        return newState;
      });
    }
  };

  const handleUnassign = async (leaveTypeId: number) => {
    const existingBalance = getExistingBalance(leaveTypeId);
    if (!existingBalance) return;

    // Check if used is 0
    if (existingBalance.used > 0) {
      toast.error(`Cannot unassign ${existingBalance.leave_type_name}. Employee has already used ${existingBalance.used} days`);
      return;
    }

    setLoadingItems(prev => ({ ...prev, [leaveTypeId]: true }));
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");
      const employeeUserId = currentEmployee?.user?.id || currentEmployee?.user_id || currentEmployee?.id;

      if (!admin_id || !employeeUserId) {
        toast.error("Missing required information");
        setLoadingItems(prev => ({ ...prev, [leaveTypeId]: false }));
        return;
      }

      const response = await axios.delete(
        `http://127.0.0.1:8000/api/leave-balances/${admin_id}/${employeeUserId}/${existingBalance.id}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      toast.success(response.data.message || "Leave unassigned successfully");
      
      // Refresh data using the common function
      await fetchExistingBalances();
      
      // Call callback if provided
      onLeaveAssigned?.(response.data);
    } catch (error: any) {
      console.error("Error unassigning leave balance:", error);
      const errorMessage = error.response?.data?.message || "Failed to unassign leave balance";
      toast.error(errorMessage, { autoClose: 6000 });
    } finally {
      setLoadingItems(prev => ({ ...prev, [leaveTypeId]: false }));
    }
  };

  const handleCancel = () => {
    setSelectedLeaves([]);
    setEditingBalance({});
    setEditValues({});
    setLoadingItems({});
    onClose?.();
  };

  return (
    <div className="modal fade" id="assign_leave_modal">
      <div className="modal-dialog modal-dialog-centered modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h4 className="modal-title">
              Assign Leaves {currentEmployee ? `to ${currentEmployee.user_name || currentEmployee.user?.email || currentEmployee.email}` : ""}
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
            {/* Action Buttons */}
            {currentEmployee && (
              <div className="d-flex gap-2 mb-3">
                {onOpenLeaveApplications && (
                  <button
                    type="button"
                    className="btn btn-outline-secondary flex-fill"
                    onClick={(e) => {
                      e.preventDefault();
                      onOpenLeaveApplications();
                    }}
                  >
                    <i className="ti ti-list me-2" />
                    View Applications
                  </button>
                )}
                {onOpenApplyLeave && (
                  <button
                    type="button"
                    className="btn btn-outline-secondary flex-fill"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        // Step 1: Clean all backdrops using utility function
                        removeAllBackdrops();
                        
                        // Step 2: Close Assign Leave modal using utility function
                        closeModal('assign_leave_modal');
                        
                        // Step 3: Reset body state using utility function
                        resetBodyStyles();
                        
                        // Step 4: Set employee and open Apply Leave modal
                        onOpenApplyLeave();
                        
                        setTimeout(() => {
                          // Ensure clean state before opening new modal
                          removeAllBackdrops();
                          
                          // Open Apply Leave modal using utility function
                          openModal('apply_leave_for_employee_modal');
                        }, 200);
                      }}
                    >
                    <i className="ti ti-calendar-plus me-2" />
                    Apply Leave
                  </button>
                )}
              </div>
            )}
            
            {/* Tabs */}
            <ul className="nav nav-tabs mb-3" role="tablist">
              <li className="nav-item" role="presentation">
                <button
                  className={`nav-link ${activeTab === 'assign' ? 'active' : ''}`}
                  onClick={() => setActiveTab('assign')}
                  type="button"
                  role="tab"
                >
                  <i className="ti ti-user-plus me-2" />
                  Assign Leaves
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
                  Leave Summary
                </button>
              </li>
            </ul>
            
            {/* Current Year Display */}
            <div className="border-start border-primary border-3 bg-light p-2 mb-3">
              <small className="text-muted">
                <i className="ti ti-calendar me-2" />
                {activeTab === 'assign' ? 'Assigning' : 'Showing'} leaves for year: <strong>{year}</strong>
              </small>
            </div>

            {/* Tab Content */}
            {activeTab === 'assign' ? (
              /* Assign Leaves Tab */
              <>
            {/* Leave Types Selection */}
            <div className="row">
              <div className="col-12">
                <h6 className="mb-3">Select Leave Types</h6>
                {loadingLeaveTypes ? (
                  <p>Loading leave types...</p>
                ) : leaveTypes.length === 0 ? (
                  <p className="text-muted">No leave types available. Please create leave types first.</p>
                ) : (
                  <div className="table-responsive">
                    {existingBalances.length > 0 && (
                      <div className="border-start border-secondary border-3 bg-light p-2 mb-3">
                        <small className="text-muted">
                          <i className="ti ti-info-circle me-2" />
                          <strong>{existingBalances.length} leave type(s)</strong> already assigned for {year}. 
                          {existingBalances.length === leaveTypes.length ? (
                            <span> All leave types assigned. Edit or unassign below.</span>
                          ) : (
                            <span> Edit existing or select new types below.</span>
                          )}
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
                                if (e.target.checked) {
                                  // Select only unassigned leave types
                                  const unassignedLeaveTypes = leaveTypes.filter(
                                    (lt) => !isLeaveTypeAlreadyAssigned(lt.id)
                                  );
                                  setSelectedLeaves(
                                    unassignedLeaveTypes.map((lt) => ({
                                      leave_type: lt.id,
                                      use_default: true,
                                    }))
                                  );
                                } else {
                                  setSelectedLeaves([]);
                                }
                              }}
                              checked={
                                selectedLeaves.length > 0 &&
                                selectedLeaves.length === leaveTypes.filter(lt => !isLeaveTypeAlreadyAssigned(lt.id)).length &&
                                leaveTypes.filter(lt => !isLeaveTypeAlreadyAssigned(lt.id)).length > 0
                              }
                            />
                          </th>
                          <th>Leave Type</th>
                          <th>Default / Max Count</th>
                          <th>Assigned Count (Editable)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {leaveTypes.map((leaveType) => {
                          const isSelected = selectedLeaves.some(
                            (l) => l.leave_type === leaveType.id
                          );
                          const selectedLeave = selectedLeaves.find(
                            (l) => l.leave_type === leaveType.id
                          );
                          const alreadyAssigned = isLeaveTypeAlreadyAssigned(leaveType.id);

                          return (
                            <tr key={leaveType.id} className={alreadyAssigned ? "table-secondary" : ""}>
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
                                    onChange={() => handleLeaveTypeToggle(leaveType.id)}
                                  />
                                )}
                              </td>
                              <td>
                                <strong>{leaveType.name}</strong>
                                <br />
                                <small className="text-muted">
                                  ({leaveType.code})
                                  {leaveType.is_paid && <> • Paid</>}
                                  {alreadyAssigned && <> • Assigned</>}
                                </small>
                              </td>
                              <td>
                                <span className="badge bg-light text-dark border">{leaveType.default_count}</span>
                                {alreadyAssigned && (
                                  <>
                                    <br />
                                    <small className="text-muted">
                                      Current: {getExistingBalance(leaveType.id)?.assigned || 0} assigned, 
                                      {" "}{getExistingBalance(leaveType.id)?.used || 0} used,
                                      {" "}{getExistingBalance(leaveType.id)?.balance || 0} left
                                    </small>
                                  </>
                                )}
                              </td>
                              <td>
                                {alreadyAssigned ? (
                                  editingBalance[leaveType.id] ? (
                                    <div className="d-flex align-items-center gap-2">
                                      <input
                                        type="number"
                                        className="form-control form-control-sm"
                                        value={editValues[leaveType.id] !== undefined ? editValues[leaveType.id] : (getExistingBalance(leaveType.id)?.assigned || 0)}
                                        onChange={(e) => {
                                          const value = parseFloat(e.target.value);
                                          if (!isNaN(value)) {
                                            setEditValues(prev => ({ ...prev, [leaveType.id]: value }));
                                          }
                                        }}
                                        min={getExistingBalance(leaveType.id)?.used || 0}
                                        max={leaveType.default_count}
                                        step={0.5}
                                        disabled={loadingItems[leaveType.id] || false}
                                        style={{ maxWidth: "100px" }}
                                      />
                                      <button
                                        type="button"
                                        className="btn btn-sm btn-outline-secondary"
                                        onClick={(e) => {
                                          e.preventDefault();
                                          e.stopPropagation();
                                          handleEditSave(leaveType.id);
                                        }}
                                        disabled={loadingItems[leaveType.id] || false}
                                        title="Save changes"
                                      >
                                        {loadingItems[leaveType.id] ? (
                                          <span className="spinner-border spinner-border-sm" />
                                        ) : (
                                          <i className="ti ti-check" />
                                        )}
                                      </button>
                                      <button
                                        type="button"
                                        className="btn btn-sm btn-outline-secondary"
                                        onClick={(e) => {
                                          e.preventDefault();
                                          e.stopPropagation();
                                          handleEditCancel(leaveType.id);
                                        }}
                                        disabled={loadingItems[leaveType.id] || false}
                                        title="Cancel"
                                      >
                                        <i className="ti ti-x" />
                                      </button>
                                    </div>
                                  ) : (
                                    <div className="d-flex align-items-center gap-2">
                                      <span className="badge bg-light text-dark border">
                                        {getExistingBalance(leaveType.id)?.assigned || 0} days
                                      </span>
                                      <button
                                        type="button"
                                        className="btn btn-sm btn-outline-secondary"
                                        onClick={(e) => {
                                          e.preventDefault();
                                          e.stopPropagation();
                                          handleEditClick(leaveType.id, getExistingBalance(leaveType.id)?.assigned || 0);
                                        }}
                                        disabled={loadingItems[leaveType.id] || false}
                                        title="Edit assigned count"
                                      >
                                        <i className="ti ti-pencil" />
                                      </button>
                                      <button
                                        type="button"
                                        className="btn btn-sm btn-outline-secondary"
                                        onClick={(e) => {
                                          e.preventDefault();
                                          e.stopPropagation();
                                          handleUnassign(leaveType.id);
                                        }}
                                        disabled={(loadingItems[leaveType.id] || false) || Number(getExistingBalance(leaveType.id)?.used || 0) > 0}
                                        title={
                                          Number(getExistingBalance(leaveType.id)?.used || 0) > 0
                                            ? `Cannot unassign - employee has used ${getExistingBalance(leaveType.id)?.used} days`
                                            : "Click to unassign this leave type"
                                        }
                                      >
                                        {loadingItems[leaveType.id] ? (
                                          <span className="spinner-border spinner-border-sm" />
                                        ) : (
                                          <i className="ti ti-trash" />
                                        )}
                                      </button>
                                    </div>
                                  )
                                ) : (
                                  <input
                                    type="number"
                                    className="form-control form-control-sm"
                                    placeholder={`Max: ${leaveType.default_count}`}
                                    disabled={!isSelected}
                                    value={selectedLeave?.assigned || ""}
                                    onChange={(e) =>
                                      handleAssignedChange(leaveType.id, e.target.value)
                                    }
                                    min={0}
                                    max={leaveType.default_count}
                                    step={0.5}
                                    title={`Maximum allowed: ${leaveType.default_count} days`}
                                  />
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
                {leaveTypes.length > 0 && (
                  <div className="bg-light p-2 mt-2 mb-0 rounded">
                    <small className="text-muted">
                      <strong>Note:</strong> Leave empty to use default count. Edit assigned leaves by clicking the edit icon. Cannot assign less than used days.
                    </small>
                  </div>
                )}
              </div>
            </div>

            {/* Selected Summary */}
            {selectedLeaves.length > 0 && (
              <div className="border p-3 mt-3 rounded bg-light">
                <small className="text-muted">
                  <strong>Selected {selectedLeaves.length} leave type(s):</strong>
                </small>
                <ul className="mb-0 mt-2 small">
                  {selectedLeaves.map((leave) => (
                    <li key={leave.leave_type} className="text-muted">
                      {getLeaveTypeName(leave.leave_type)}:{" "}
                      {leave.use_default ? (
                        <span className="text-dark">
                          {getDefaultCount(leave.leave_type)} days (default)
                        </span>
                      ) : (
                        <span className="text-dark">
                          {leave.assigned} days
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            </>
            ) : (
              /* Leave Summary Tab */
              <div className="leave-summary-content">
                {loadingSummary ? (
                  <div className="text-center py-4">
                    <div className="spinner-border text-primary" role="status">
                      <span className="visually-hidden">Loading...</span>
                    </div>
                    <p className="mt-2">Loading leave summary...</p>
                  </div>
                ) : leaveSummary.length === 0 ? (
                  <div className="text-center py-4">
                    <i className="ti ti-clipboard-off fs-1 text-muted" />
                    <p className="mt-2 text-muted">
                      No leaves assigned for {year}. Please assign leaves first from the "Assign Leaves" tab.
                    </p>
                  </div>
                ) : (
                  <>
                    {/* Summary Cards */}
                    <div className="row mb-4">
                      <div className="col-md-4">
                        <div className="card border shadow-sm">
                          <div className="card-body text-center">
                            <div className="mb-2">
                              <i className="ti ti-calendar-check fs-1"></i>
                            </div>
                            <h3 className="mb-1">
                              {leaveSummary.reduce((sum: number, leave: any) => sum + parseFloat(leave.assigned || 0), 0).toFixed(1)}
                            </h3>
                            <p className="text-muted mb-0">Total Assigned Days</p>
                          </div>
                        </div>
                      </div>
                      <div className="col-md-4">
                        <div className="card border shadow-sm">
                          <div className="card-body text-center">
                            <div className="mb-2">
                              <i className="ti ti-calendar-minus fs-1"></i>
                            </div>
                            <h3 className="mb-1">
                              {leaveSummary.reduce((sum: number, leave: any) => sum + parseFloat(leave.used || 0), 0).toFixed(1)}
                            </h3>
                            <p className="text-muted mb-0">Total Used Days</p>
                          </div>
                        </div>
                      </div>
                      <div className="col-md-4">
                        <div className="card border shadow-sm">
                          <div className="card-body text-center">
                            <div className="mb-2">
                              <i className="ti ti-calendar-stats fs-1"></i>
                            </div>
                            <h3 className="mb-1">
                              {leaveSummary.reduce((sum: number, leave: any) => sum + parseFloat(leave.balance || 0), 0).toFixed(1)}
                            </h3>
                            <p className="text-muted mb-0">Total Balance Days</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Detailed Table */}
                    <div className="table-responsive">
                      <table className="table table-bordered table-hover">
                        <thead className="table-light">
                          <tr>
                            <th>Leave Type</th>
                            <th className="text-center">Assigned</th>
                            <th className="text-center">Used</th>
                            <th className="text-center">Balance</th>
                            <th className="text-center">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {leaveSummary.map((leave: any) => (
                            <tr key={leave.id}>
                              <td>
                                <div className="d-flex align-items-center">
                                  <span className="avatar avatar-sm bg-light text-dark border me-2 d-flex align-items-center justify-content-center">
                                    <i className="ti ti-calendar"></i>
                                  </span>
                                  <div>
                                    <strong className="d-block">{leave.leave_type_name}</strong>
                                    <small className="text-muted">({leave.leave_type_code})</small>
                                  </div>
                                </div>
                              </td>
                              <td className="text-center">
                                <span className="badge bg-light text-dark border d-inline-flex align-items-center">
                                  <i className="ti ti-point-filled me-1"></i>
                                  {leave.assigned} days
                                </span>
                              </td>
                              <td className="text-center">
                                <span className="badge bg-light text-dark border d-inline-flex align-items-center">
                                  <i className="ti ti-point-filled me-1"></i>
                                  {leave.used} days
                                </span>
                              </td>
                              <td className="text-center">
                                <span className="badge bg-light text-dark border d-inline-flex align-items-center">
                                  <i className="ti ti-point-filled me-1"></i>
                                  {leave.balance} days
                                </span>
                              </td>
                              <td className="text-center">
                                {leave.balance > 5 ? (
                                  <span className="badge bg-light text-dark border d-inline-flex align-items-center">
                                    <i className="ti ti-circle-check me-1"></i>
                                    Available
                                  </span>
                                ) : leave.balance > 0 ? (
                                  <span className="badge bg-light text-dark border d-inline-flex align-items-center">
                                    <i className="ti ti-alert-triangle me-1"></i>
                                    Low
                                  </span>
                                ) : (
                                  <span className="badge bg-light text-dark border d-inline-flex align-items-center">
                                    <i className="ti ti-x me-1"></i>
                                    Exhausted
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
                  selectedLeaves.length === 0 || 
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
                    Assign Leaves {selectedLeaves.length > 0 && `(${selectedLeaves.length})`}
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

export default AssignLeaveModal;

