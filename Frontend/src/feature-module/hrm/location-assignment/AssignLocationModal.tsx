import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import { toast } from "react-toastify";
import { removeAllBackdrops, resetBodyStyles, cleanupExcessBackdrops } from "../../../core/utils/modalHelpers";

type AssignLocationModalProps = {
  employee?: any;
  onLocationAssigned?: (result: any) => void;
  onClose?: () => void;
};

type LocationOption = {
  id: number;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  radius: number;
};

const AssignLocationModal: React.FC<AssignLocationModalProps> = ({
  employee,
  onLocationAssigned,
  onClose,
}) => {
  const [locations, setLocations] = useState<LocationOption[]>([]);
  const [selectedLocations, setSelectedLocations] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingLocations, setLoadingLocations] = useState(true);
  const [assignedLocations, setAssignedLocations] = useState<LocationOption[]>([]);
  
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
    const modalElement = document.getElementById('assign_location_modal');
    if (!modalElement) return;

    const handleModalShow = () => {
      // Clean up any stray backdrops before showing using utility function
      setTimeout(() => {
        cleanupExcessBackdrops();
      }, 50);
      
      // Fetch latest assigned locations to pre-select them
      if (currentEmployee) {
        fetchAssignedLocations();
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

  // Fetch available locations on mount
  useEffect(() => {
    fetchLocations();
  }, []);

  // Function to fetch locations from API
  const fetchLocations = async () => {
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");

      if (!admin_id) {
        toast.error("Admin ID not found");
        return;
      }

      const response = await axios.get(
        `http://127.0.0.1:8000/api/locations/${admin_id}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const locationsData = response.data.data || response.data;
      setLocations(Array.isArray(locationsData) ? locationsData : []);
    } catch (error: any) {
      console.error("Error fetching locations:", error);
      toast.error("Failed to fetch locations");
      setLocations([]);
    } finally {
      setLoadingLocations(false);
    }
  };

  // Function to fetch assigned locations from API
  const fetchAssignedLocations = async () => {
    // Use employeeRef for stable reference
    const emp = employeeRef.current || currentEmployee;
    
    console.log("🔄 fetchAssignedLocations - Employee check:", { 
      employeeRef: employeeRef.current, 
      currentEmployee,
      emp 
    });
    
    if (!emp) {
      console.warn("⚠️ No employee for fetchAssignedLocations, clearing list");
      setAssignedLocations([]);
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

      console.log(`🔄 Fetching assigned locations for ${emp.user_name || 'employee'}...`);
      
      const response = await axios.get(
        `http://127.0.0.1:8000/api/assign-locations/${admin_id}/${employeeUserId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      console.log("📥 Raw Response:", response.data);
      
      const locationsData = response.data.data?.assigned_locations || [];
      console.log("📦 Extracted locationsData:", locationsData);
      
      setAssignedLocations(Array.isArray(locationsData) ? locationsData : []);
      
      // Pre-select already assigned locations
      const assignedIds = locationsData.map((location: any) => location.id);
      setSelectedLocations(assignedIds);
      
      console.log(`✅ Fetched ${locationsData.length} assigned location(s), pre-selected:`, assignedIds);
    } catch (error: any) {
      console.error("❌ ERROR fetching assigned locations:", error);
      console.error("Error details:", error.response?.data);
      setAssignedLocations([]);
      setSelectedLocations([]);
    } finally {
      if (activeTab === 'summary') {
        setLoadingSummary(false);
      }
    }
  };

  // Fetch assigned locations when employee changes
  useEffect(() => {
    if (currentEmployee) {
      fetchAssignedLocations(); // This will pre-select assigned locations
    }
  }, [currentEmployee]);

  // Fetch data when tab changes (only for summary tab to refresh data)
  useEffect(() => {
    if (currentEmployee && activeTab === 'summary') {
      console.log(`📑 Tab switched to: ${activeTab}`);
      fetchAssignedLocations();
    }
  }, [activeTab]);

  const handleLocationToggle = (locationId: number) => {
    if (selectedLocations.includes(locationId)) {
      // Unselect: Remove from selected array
      const updatedLocations = selectedLocations.filter((id) => id !== locationId);
      console.log(`❌ Deselected Location ${locationId}. Remaining selected:`, updatedLocations);
      setSelectedLocations(updatedLocations);
    } else {
      // Select: Add to selected array
      const updatedLocations = [...selectedLocations, locationId];
      console.log(`✅ Selected Location ${locationId}. Now selected:`, updatedLocations);
      setSelectedLocations(updatedLocations);
    }
  };

  const isLocationAssigned = (locationId: number) => {
    return assignedLocations.some((l) => l.id === locationId);
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

    if (selectedLocations.length === 0) {
      toast.error("Please select at least one location");
      return;
    }

    console.log("🔥 Assigning these location IDs:", selectedLocations);
    
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

      console.log("📤 Sending to backend:", { location_ids: selectedLocations });

      const response = await axios.post(
        `http://127.0.0.1:8000/api/assign-locations/${admin_id}/${employeeUserId}`,
        { location_ids: selectedLocations },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      console.log("✅ Assignment response:", response.data);
      
      toast.success(response.data.message || "Locations assigned successfully");
      
      // Refresh data (this will pre-select the newly assigned locations)
      await fetchAssignedLocations();
      
      onLocationAssigned?.(response.data);
    } catch (error: any) {
      console.error("Error assigning locations:", error);
      const errorMessage = error.response?.data?.message || "Failed to assign locations";
      toast.error(errorMessage);
      setSelectedLocations([]);
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

    if (assignedLocations.length === 0) {
      toast.error("No locations assigned to remove");
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
        `http://127.0.0.1:8000/api/assign-locations/${admin_id}/${employeeUserId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      toast.success(response.data.message || "All locations removed successfully");
      
      // Refresh data
      await fetchAssignedLocations();
      
      onLocationAssigned?.(response.data);
    } catch (error: any) {
      console.error("Error removing locations:", error);
      const errorMessage = error.response?.data?.message || "Failed to remove locations";
      toast.error(errorMessage, { autoClose: 6000 });
    } finally {
      setLoading(false);
    }
  };

  const handleUnassignSingle = async (locationId: number, locationName: string) => {
    // Use employeeRef to get stable employee reference
    const emp = employeeRef.current || employee || currentEmployee;
    
    console.log("🔍 handleUnassignSingle called with:", { 
      locationId, 
      locationName, 
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

      const deleteUrl = `http://127.0.0.1:8000/api/assign-locations/${admin_id}/${employeeUserId}/${locationId}`;
      console.log(`🗑️ Removing location ${locationId} from employee ${employeeUserId}`);
      console.log(`📡 DELETE URL: ${deleteUrl}`);

      const response = await axios.delete(
        deleteUrl,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      
      console.log(`✅ DELETE Response:`, response.data);

      toast.success(response.data.message || `Location '${locationName}' removed successfully`);
      
      // Refresh data
      await fetchAssignedLocations();
      
      onLocationAssigned?.(response.data);
    } catch (error: any) {
      console.error("Error removing location:", error);
      const errorMessage = error.response?.data?.message || "Failed to remove location";
      toast.error(errorMessage, { autoClose: 6000 });
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setSelectedLocations([]);
    setActiveTab('assign');
    onClose?.();
  };

  // Helper function to safely format coordinates
  const formatCoordinate = (value: any, decimals: number = 6): string => {
    if (value === null || value === undefined) return '-';
    const num = typeof value === 'number' ? value : parseFloat(value);
    return isNaN(num) ? '-' : num.toFixed(decimals);
  };

  return (
    <div className="modal fade" id="assign_location_modal">
      <div className="modal-dialog modal-dialog-centered modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h4 className="modal-title">
              Assign Locations {currentEmployee ? `to ${currentEmployee.user_name || currentEmployee.user?.email || currentEmployee.email}` : ""}
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
                  <i className="ti ti-map-pin-plus me-2" />
                  Assign Locations
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
                  Location Summary
                </button>
              </li>
            </ul>

            {/* Tab Content */}
            {activeTab === 'assign' ? (
              /* Assign Locations Tab */
              <>
                {/* Location Selection */}
                <div className="row">
                  <div className="col-12">
                    <h6 className="mb-3">Select Locations</h6>
                    {loadingLocations ? (
                      <p>Loading locations...</p>
                    ) : locations.length === 0 ? (
                      <p className="text-muted">No locations available. Please create locations first.</p>
                    ) : (
                      <div className="table-responsive">
                        {assignedLocations.length > 0 && (
                          <div className="border-start border-secondary border-3 bg-light p-2 mb-3">
                            <small className="text-muted">
                              <i className="ti ti-info-circle me-2" />
                              <strong>{assignedLocations.length} location(s)</strong> already assigned. 
                              Select new locations or remove all to reassign.
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
                                    const unassignedLocations = locations.filter(l => !isLocationAssigned(l.id));
                                    if (e.target.checked) {
                                      const unassignedIds = unassignedLocations.map((l) => l.id);
                                      const assignedIds = assignedLocations.map(l => l.id);
                                      const allIds = [...assignedIds, ...unassignedIds];
                                      console.log("Selecting all unassigned locations:", unassignedIds);
                                      setSelectedLocations(allIds);
                                    } else {
                                      const assignedIds = assignedLocations.map(l => l.id);
                                      console.log("Deselecting all unassigned locations, keeping assigned");
                                      setSelectedLocations(assignedIds);
                                    }
                                  }}
                                  checked={
                                    locations.filter(l => !isLocationAssigned(l.id)).length > 0 &&
                                    locations.filter(l => !isLocationAssigned(l.id)).every(l => selectedLocations.includes(l.id))
                                  }
                                />
                              </th>
                              <th>Location Name</th>
                              <th>Address</th>
                              <th>Coordinates</th>
                              <th>Radius</th>
                              <th style={{ width: "100px" }}>Action</th>
                            </tr>
                          </thead>
                          <tbody>
                            {locations.map((location) => {
                              const isSelected = selectedLocations.includes(location.id);
                              const alreadyAssigned = isLocationAssigned(location.id);

                              return (
                                <tr key={location.id} className={alreadyAssigned ? "table-secondary" : ""}>
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
                                        onChange={() => handleLocationToggle(location.id)}
                                      />
                                    )}
                                  </td>
                                  <td>
                                    <strong>{location.name}</strong>
                                    {alreadyAssigned && (
                                      <>
                                        <br />
                                        <small className="text-muted">Currently Assigned</small>
                                      </>
                                    )}
                                  </td>
                                  <td>
                                    <small className="text-muted">
                                      <i className="ti ti-map-pin me-1"></i>
                                      {location.address}
                                    </small>
                                  </td>
                                  <td>
                                    <small className="text-muted">
                                      {formatCoordinate(location.latitude)}, {formatCoordinate(location.longitude)}
                                    </small>
                                  </td>
                                  <td>
                                    <span className="badge bg-light text-dark border">
                                      {location.radius}m
                                    </span>
                                  </td>
                                  <td>
                                    {alreadyAssigned ? (
                                      <button
                                        type="button"
                                        className="btn btn-sm btn-outline-danger"
                                        onClick={() => handleUnassignSingle(location.id, location.name)}
                                        disabled={loading}
                                        title="Unassign this location"
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
                {selectedLocations.length > 0 && (
                  <div className="border p-3 mt-3 rounded bg-light">
                    <small className="text-muted">
                      <strong>Selected {selectedLocations.length} location(s):</strong>
                    </small>
                    <ul className="mb-0 mt-2 small">
                      {selectedLocations.map((locationId) => {
                        const location = locations.find(l => l.id === locationId);
                        return location ? (
                          <li key={locationId} className="text-muted">
                            {location.name} - {location.address}
                          </li>
                        ) : null;
                      })}
                    </ul>
                  </div>
                )}

                {/* Remove All Button */}
                {assignedLocations.length > 0 && (
                  <div className="alert alert-warning mt-3">
                    <div className="d-flex justify-content-between align-items-center">
                      <div>
                        <i className="ti ti-alert-circle me-2"></i>
                        <strong>{assignedLocations.length} location(s)</strong> currently assigned
                      </div>
                      <button
                        type="button"
                        className="btn btn-sm btn-outline-danger"
                        onClick={handleUnassignAll}
                        disabled={loading}
                      >
                        <i className="ti ti-trash me-1"></i>
                        Remove All Locations
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              /* Location Summary Tab */
              <div className="location-summary-content">
                {loadingSummary ? (
                  <div className="text-center py-4">
                    <div className="spinner-border text-primary" role="status">
                      <span className="visually-hidden">Loading...</span>
                    </div>
                    <p className="mt-2">Loading location summary...</p>
                  </div>
                ) : assignedLocations.length === 0 ? (
                  <div className="text-center py-4">
                    <i className="ti ti-map-pin-off fs-1 text-muted" />
                    <p className="mt-2 text-muted">
                      No locations assigned. Please assign locations from the "Assign Locations" tab.
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
                              <i className="ti ti-map-pin fs-1"></i>
                            </div>
                            <h3 className="mb-1">{assignedLocations.length}</h3>
                            <p className="text-muted mb-0">Total Assigned Locations</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Detailed Table */}
                    <div className="table-responsive">
                      <table className="table table-bordered table-hover">
                        <thead className="table-light">
                          <tr>
                            <th>Location Name</th>
                            <th>Address</th>
                            <th>Coordinates</th>
                            <th>Radius</th>
                            <th style={{ width: "100px" }}>Action</th>
                          </tr>
                        </thead>
                        <tbody>
                          {assignedLocations.map((location: any) => (
                            <tr key={location.id}>
                              <td>
                                <div className="d-flex align-items-center">
                                  <span className="avatar avatar-sm bg-light text-dark border me-2 d-flex align-items-center justify-content-center">
                                    <i className="ti ti-map-pin"></i>
                                  </span>
                                  <strong>{location.name}</strong>
                                </div>
                              </td>
                              <td>
                                <span className="badge bg-light text-dark border d-inline-flex align-items-center">
                                  <i className="ti ti-map-pin me-1"></i>
                                  {location.address}
                                </span>
                              </td>
                              <td>
                                <small className="text-muted">
                                  Lat: {formatCoordinate(location.latitude)}<br />
                                  Lng: {formatCoordinate(location.longitude)}
                                </small>
                              </td>
                              <td className="text-center">
                                <span className="badge bg-light text-dark border d-inline-flex align-items-center">
                                  <i className="ti ti-circle-dotted me-1"></i>
                                  {location.radius}m radius
                                </span>
                              </td>
                              <td>
                                <button
                                  type="button"
                                  className="btn btn-sm btn-outline-danger"
                                  onClick={() => handleUnassignSingle(location.id, location.name)}
                                  disabled={loading}
                                  title="Remove this location"
                                >
                                  <i className="ti ti-trash"></i>
                                </button>
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
                  selectedLocations.length === 0 || 
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
                    Assign Locations {selectedLocations.length > 0 && `(${selectedLocations.length})`}
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

export default AssignLocationModal;

