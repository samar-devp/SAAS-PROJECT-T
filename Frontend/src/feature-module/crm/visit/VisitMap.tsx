import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import CollapseHeader from "../../../core/common/collapse-header/collapse-header";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { getAdminIdForApi } from "../../../core/utils/apiHelpers";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

interface VisitMapData {
  id: string;
  title: string;
  assigned_employee_name: string;
  schedule_date: string;
  address: string;
  scheduled_lat?: number;
  scheduled_lng?: number;
  check_in_latitude?: number;
  check_in_longitude?: number;
  check_out_latitude?: number;
  check_out_longitude?: number;
  status: string;
  check_in_timestamp?: string;
  check_out_timestamp?: string;
}

const VisitMap = () => {
  const [visits, setVisits] = useState<VisitMapData[]>([]);
  const [loading, setLoading] = useState(true);
  const [dateFrom, setDateFrom] = useState<Date | null>(new Date());
  const [dateTo, setDateTo] = useState<Date | null>(new Date());
  const [selectedUserId, setSelectedUserId] = useState<string>("");
  const [employees, setEmployees] = useState<any[]>([]);
  const [selectedVisit, setSelectedVisit] = useState<VisitMapData | null>(null);

  // Calculate distance between two coordinates (Haversine formula)
  const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
    const R = 6371; // Radius of the Earth in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c; // Distance in km
  };

  // Geocode address to get coordinates
  const geocodeAddress = async (address: string): Promise<{ lat: number; lng: number } | null> => {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`,
        {
          headers: {
            "User-Agent": "VisitManagement/1.0",
          },
        }
      );
      const data = await response.json();
      if (data && data.length > 0) {
        return {
          lat: parseFloat(data[0].lat),
          lng: parseFloat(data[0].lon),
        };
      }
    } catch (error) {
      console.error("Geocoding error:", error);
    }
    return null;
  };

  const fetchEmployees = async () => {
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = getAdminIdForApi();

      if (!admin_id) return;

      const response = await axios.get(
        `http://127.0.0.1:8000/api/staff-list/${admin_id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      let employeesData = [];
      if (response.data && response.data.results && Array.isArray(response.data.results)) {
        employeesData = response.data.results;
      } else if (response.data && response.data.data) {
        if (Array.isArray(response.data.data)) {
          employeesData = response.data.data;
        } else if (response.data.data.results && Array.isArray(response.data.data.results)) {
          employeesData = response.data.data.results;
        }
      } else if (Array.isArray(response.data)) {
        employeesData = response.data;
      }
      setEmployees(employeesData);
    } catch (error: any) {
      console.error("Error fetching employees:", error);
    }
  };

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

      const params: any = {};
      if (dateFrom) {
        params.date_from = dateFrom.toISOString().split("T")[0];
      }
      if (dateTo) {
        params.date_to = dateTo.toISOString().split("T")[0];
      }

      const queryString = new URLSearchParams(params).toString();
      if (queryString) {
        url += `?${queryString}`;
      }

      const response = await axios.get(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      let visitsData = [];
      if (response.data && response.data.data) {
        if (response.data.data.results && Array.isArray(response.data.data.results)) {
          visitsData = response.data.data.results;
        } else if (Array.isArray(response.data.data)) {
          visitsData = response.data.data;
        }
      } else if (Array.isArray(response.data)) {
        visitsData = response.data;
      }

      // Filter visits: Only show visits that have check-in location (check_in_latitude and check_in_longitude)
      const visitsWithCheckIn = visitsData.filter((visit: any) => {
        return visit.check_in_latitude && visit.check_in_longitude;
      });

      // Geocode addresses for visits that don't have scheduled coordinates
      const visitsWithCoords = await Promise.all(
        visitsWithCheckIn.map(async (visit: any) => {
          let scheduledLat = visit.scheduled_lat;
          let scheduledLng = visit.scheduled_lng;

          // If no scheduled coordinates, geocode the address
          if (!scheduledLat || !scheduledLng) {
            if (visit.address) {
              const coords = await geocodeAddress(visit.address);
              if (coords) {
                scheduledLat = coords.lat;
                scheduledLng = coords.lng;
              }
            }
          }

          // Convert DecimalField values to numbers
          const checkInLat = visit.check_in_latitude ? parseFloat(visit.check_in_latitude) : null;
          const checkInLng = visit.check_in_longitude ? parseFloat(visit.check_in_longitude) : null;
          const checkOutLat = visit.check_out_latitude ? parseFloat(visit.check_out_latitude) : null;
          const checkOutLng = visit.check_out_longitude ? parseFloat(visit.check_out_longitude) : null;

          return {
            ...visit,
            scheduled_lat: scheduledLat,
            scheduled_lng: scheduledLng,
            check_in_latitude: checkInLat,
            check_in_longitude: checkInLng,
            check_out_latitude: checkOutLat,
            check_out_longitude: checkOutLng,
          };
        })
      );

      setVisits(visitsWithCoords);
      if (visitsWithCoords.length > 0 && !selectedVisit) {
        setSelectedVisit(visitsWithCoords[0]);
      }
    } catch (error: any) {
      console.error("Error fetching visits:", error);
      toast.error(error.response?.data?.message || "Failed to fetch visits");
    } finally {
      setLoading(false);
    }
  }, [dateFrom, dateTo, selectedUserId, selectedVisit]);

  useEffect(() => {
    fetchEmployees();
  }, []);

  useEffect(() => {
    fetchVisits();
  }, [fetchVisits]);

  // Generate OpenStreetMap URL with markers
  const getMapUrl = (visit: VisitMapData | null): string => {
    if (!visit) {
      return "https://www.openstreetmap.org/export/embed.html?bbox=68.0,6.0,97.0,37.0&layer=mapnik";
    }

    // Only show check-out if it exists, otherwise show check-in if it exists
    let lat: number | null = null;
    let lng: number | null = null;
    
    if (visit.check_out_latitude && visit.check_out_longitude) {
      // Show check-out location if available
      lat = visit.check_out_latitude;
      lng = visit.check_out_longitude;
    } else if (visit.check_in_latitude && visit.check_in_longitude) {
      // Show check-in location if check-out is not available
      lat = visit.check_in_latitude;
      lng = visit.check_in_longitude;
    }

    if (!lat || !lng) {
      return "https://www.openstreetmap.org/export/embed.html?bbox=68.0,6.0,97.0,37.0&layer=mapnik";
    }

    // Add padding around the marker
    const padding = 0.01;
    const bbox = `${lng - padding},${lat - padding},${lng + padding},${lat + padding}`;
    
    // Build URL with marker
    const url = `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat},${lng}`;
    
    return url;
  };

  return (
    <>
      <div className="page-wrapper">
        <div className="content">
          {/* Breadcrumb */}
          <div className="d-md-flex d-block align-items-center justify-content-between page-breadcrumb mb-3">
            <div className="my-auto mb-2">
              <h2 className="mb-1">Visit Map</h2>
            </div>
            <div className="d-flex my-xl-auto right-content align-items-center flex-wrap">
              <div className="head-icons ms-2">
                <CollapseHeader />
              </div>
            </div>
          </div>

          {/* Filters */}
          <div className="card mb-3">
            <div className="card-body">
              <div className="row g-3">
                <div className="col-md-3">
                  <label className="form-label">Date From</label>
                  <DatePicker
                    selected={dateFrom}
                    onChange={(date: Date | null) => setDateFrom(date)}
                    dateFormat="yyyy-MM-dd"
                    className="form-control"
                    placeholderText="Select start date"
                  />
                </div>
                <div className="col-md-3">
                  <label className="form-label">Date To</label>
                  <DatePicker
                    selected={dateTo}
                    onChange={(date: Date | null) => setDateTo(date)}
                    dateFormat="yyyy-MM-dd"
                    className="form-control"
                    placeholderText="Select end date"
                    minDate={dateFrom || undefined}
                  />
                </div>
                <div className="col-md-3">
                  <label className="form-label">Employee</label>
                  <select
                    className="form-select"
                    value={selectedUserId}
                    onChange={(e) => setSelectedUserId(e.target.value)}
                  >
                    <option value="">All Employees</option>
                    {employees.map((emp) => (
                      <option key={emp.user?.id || emp.id} value={emp.user?.id || emp.id}>
                        {emp.user_name || emp.user?.email || "Unknown"}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-md-3 d-flex align-items-end">
                  <button
                    className="btn btn-primary w-100"
                    onClick={() => fetchVisits()}
                    disabled={loading}
                  >
                    {loading ? "Loading..." : "Apply Filters"}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="row">
            {/* Visit List */}
            <div className="col-md-4">
              <div className="card">
                <div className="card-header">
                  <h5>Visits with Check-in</h5>
                  <p className="text-muted mb-0">
                    <small><i className="ti ti-info-circle me-1" /> Only visits with check-in locations are shown</small>
                  </p>
                </div>
                <div className="card-body p-0">
                  {loading ? (
                    <div className="p-3 text-center">
                      <p>Loading visits...</p>
                    </div>
                  ) : visits.length === 0 ? (
                    <div className="p-3 text-center">
                      <p className="text-muted">No visits with check-in locations found</p>
                    </div>
                  ) : (
                    <div className="list-group list-group-flush">
                      {visits.map((visit) => (
                        <div
                          key={visit.id}
                          className={`list-group-item list-group-item-action cursor-pointer ${
                            selectedVisit?.id === visit.id ? "active" : ""
                          }`}
                          onClick={() => setSelectedVisit(visit)}
                          style={{ cursor: "pointer" }}
                        >
                          <div className="d-flex w-100 justify-content-between">
                            <h6 className="mb-1">{visit.title}</h6>
                            <small>{new Date(visit.schedule_date).toLocaleDateString()}</small>
                          </div>
                          <p className="mb-1">
                            <small className="text-muted">Employee: {visit.assigned_employee_name}</small>
                          </p>
                          {visit.check_in_latitude && visit.check_in_longitude && (
                            <p className="mb-0">
                              <small>
                                <i className="ti ti-map-pin me-1" />
                                Check-in: {visit.check_in_latitude.toFixed(4)}, {visit.check_in_longitude.toFixed(4)}
                              </small>
                            </p>
                          )}
                          {visit.check_out_latitude && visit.check_out_longitude && (
                            <p className="mb-0">
                              <small>
                                <i className="ti ti-map-pin me-1" />
                                Check-out: {visit.check_out_latitude.toFixed(4)}, {visit.check_out_longitude.toFixed(4)}
                              </small>
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Map */}
            <div className="col-md-8">
              <div className="card">
                <div className="card-header">
                  <h5>Location Map</h5>
                </div>
                <div className="card-body p-0">
                  {loading ? (
                    <div className="p-5 text-center">
                      <p>Loading map...</p>
                    </div>
                  ) : !selectedVisit ? (
                    <div className="p-5 text-center">
                      <p className="text-muted">Select a visit to view on map</p>
                    </div>
                  ) : (
                    <div style={{ height: "600px", width: "100%", position: "relative" }}>
                      <iframe
                        width="100%"
                        height="100%"
                        frameBorder="0"
                        scrolling="no"
                        marginHeight={0}
                        marginWidth={0}
                        src={getMapUrl(selectedVisit)}
                        style={{ border: "none" }}
                      />
                      <div className="p-3 bg-white border-top">
                        <div className="row">
                          <div className="col-md-6">
                            <h6>{selectedVisit.title}</h6>
                            <p className="mb-1">
                              <strong>Employee:</strong> {selectedVisit.assigned_employee_name}
                            </p>
                            <p className="mb-1">
                              <strong>Date:</strong> {new Date(selectedVisit.schedule_date).toLocaleDateString()}
                            </p>
                            <p className="mb-1">
                              <strong>Address:</strong> {selectedVisit.address}
                            </p>
                          </div>
                          <div className="col-md-6">
                            {selectedVisit.check_in_latitude && selectedVisit.check_in_longitude && (
                              <p className="mb-1">
                                <strong>Check-in:</strong> {new Date(selectedVisit.check_in_timestamp || "").toLocaleString()}
                                <br />
                                <small>Lat: {selectedVisit.check_in_latitude.toFixed(6)}, Lng: {selectedVisit.check_in_longitude.toFixed(6)}</small>
                              </p>
                            )}
                            {selectedVisit.check_out_latitude && selectedVisit.check_out_longitude && (
                              <p className="mb-1">
                                <strong>Check-out:</strong> {new Date(selectedVisit.check_out_timestamp || "").toLocaleString()}
                                <br />
                                <small>Lat: {selectedVisit.check_out_latitude.toFixed(6)}, Lng: {selectedVisit.check_out_longitude.toFixed(6)}</small>
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="mt-2">
                          <a
                            href={`https://www.openstreetmap.org/?mlat=${selectedVisit.check_out_latitude || selectedVisit.check_in_latitude || 0}&mlon=${selectedVisit.check_out_longitude || selectedVisit.check_in_longitude || 0}&zoom=15`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-sm btn-outline-primary"
                          >
                            <i className="ti ti-external-link me-1" />
                            Open in OpenStreetMap
                          </a>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
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

export default VisitMap;
