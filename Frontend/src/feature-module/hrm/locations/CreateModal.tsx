import React, { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "react-toastify";

interface LocationModalProps {
  onLocationAdded: () => void;
  editingLocation: any;
  onLocationUpdated: () => void;
  onEditClose: () => void;
}

interface LocationFormState {
  name: string;
  address: string;
  latitude: string;
  longitude: string;
  radius: string;
}

const LocationModal: React.FC<LocationModalProps> = ({
  onLocationAdded,
  editingLocation,
  onLocationUpdated,
  onEditClose,
}) => {
  const initialFormState: LocationFormState = {
    name: "",
    address: "",
    latitude: "",
    longitude: "",
    radius: "100",
  };

  const [formData, setFormData] = useState<LocationFormState>(initialFormState);
  const [loading, setLoading] = useState(false);
  const [geocoding, setGeocoding] = useState(false);

  useEffect(() => {
    if (editingLocation) {
      setFormData({
        name: editingLocation.name || "",
        address: editingLocation.address || "",
        latitude: editingLocation.latitude?.toString() || "",
        longitude: editingLocation.longitude?.toString() || "",
        radius: editingLocation.radius?.toString() || "100",
      });
    } else {
      setFormData(initialFormState);
    }
  }, [editingLocation]);

  // Geocode address to get latitude and longitude
  const geocodeAddress = async (address: string) => {
    if (!address || address.trim() === "") {
      return;
    }

    setGeocoding(true);
    try {
      // Using OpenStreetMap Nominatim API (free, no API key needed)
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`,
        {
          headers: {
            "User-Agent": "LocationManagement/1.0", // Required by Nominatim
          },
        }
      );

      const data = await response.json();

      if (data && data.length > 0) {
        const result = data[0];
        setFormData((prev) => ({
          ...prev,
          latitude: parseFloat(result.lat).toFixed(6),
          longitude: parseFloat(result.lon).toFixed(6),
        }));
        toast.success("Location coordinates found!");
      } else {
        toast.warning("Could not find coordinates for this address. Please enter manually.");
      }
    } catch (error) {
      console.error("Geocoding error:", error);
      toast.error("Failed to geocode address. Please enter coordinates manually.");
    } finally {
      setGeocoding(false);
    }
  };

  // Get current location from browser
  const getCurrentLocation = () => {
    if (!navigator.geolocation) {
      toast.error("Geolocation is not supported by your browser.");
      return;
    }

    setGeocoding(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setFormData((prev) => ({
          ...prev,
          latitude: position.coords.latitude.toFixed(6),
          longitude: position.coords.longitude.toFixed(6),
        }));
        toast.success("Current location captured!");
        setGeocoding(false);
      },
      (error) => {
        console.error("Geolocation error:", error);
        toast.error("Failed to get current location. Please enter manually.");
        setGeocoding(false);
      }
    );
  };

  // Reverse geocode to get address from coordinates
  const reverseGeocode = async (lat: string, lon: string) => {
    if (!lat || !lon) {
      return;
    }

    setGeocoding(true);
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`,
        {
          headers: {
            "User-Agent": "LocationManagement/1.0",
          },
        }
      );

      const data = await response.json();

      if (data && data.display_name) {
        setFormData((prev) => ({
          ...prev,
          address: data.display_name,
        }));
        toast.success("Address found from coordinates!");
      }
    } catch (error) {
      console.error("Reverse geocoding error:", error);
    } finally {
      setGeocoding(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleAddressBlur = () => {
    // Auto-geocode when user leaves address field
    if (formData.address && formData.address.trim() !== "" && !formData.latitude) {
      geocodeAddress(formData.address);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      toast.error("Please enter location name");
      return;
    }

    if (!formData.address.trim()) {
      toast.error("Please enter address");
      return;
    }

    if (!formData.latitude || !formData.longitude) {
      toast.error("Please enter latitude and longitude or use geocoding");
      return;
    }

    const latitude = parseFloat(formData.latitude);
    const longitude = parseFloat(formData.longitude);

    if (isNaN(latitude) || isNaN(longitude)) {
      toast.error("Please enter valid latitude and longitude");
      return;
    }

    if (latitude < -90 || latitude > 90) {
      toast.error("Latitude must be between -90 and 90");
      return;
    }

    if (longitude < -180 || longitude > 180) {
      toast.error("Longitude must be between -180 and 180");
      return;
    }

    const radius = parseInt(formData.radius) || 100;
    if (radius < 0) {
      toast.error("Radius must be a positive number");
      return;
    }

    setLoading(true);

    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");

      if (!admin_id) {
        toast.error("Admin ID not found. Please login again.");
        return;
      }

      const payload = {
        name: formData.name.trim(),
        address: formData.address.trim(),
        latitude: latitude,
        longitude: longitude,
        radius: radius,
        is_active: true,
      };

      let response;

      if (editingLocation) {
        // Update existing location
        response = await axios.put(
          `http://127.0.0.1:8000/api/locations/${admin_id}/${editingLocation.id}`,
          payload,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        toast.success("Location updated successfully!");
        onLocationUpdated();
      } else {
        // Create new location
        response = await axios.post(
          `http://127.0.0.1:8000/api/locations/${admin_id}`,
          payload,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        toast.success("Location added successfully!");
        onLocationAdded();
      }

      // Reset form
      setFormData(initialFormState);
      
      // Close modal
      const modalElement = document.getElementById("locationModal");
      if (modalElement) {
        const modal = (window as any).bootstrap?.Modal?.getInstance(modalElement);
        if (modal) {
          modal.hide();
        }
      }
    } catch (error: any) {
      console.error("Error saving location:", error);
      toast.error(
        error.response?.data?.message || 
        error.response?.data?.detail || 
        `Failed to ${editingLocation ? "update" : "add"} location`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setFormData(initialFormState);
    onEditClose();
  };

  const getModalContainer = () => document.getElementById("locationModal") || document.body;

  return (
    <div
      className="modal fade"
      id="locationModal"
      tabIndex={-1}
      aria-labelledby="locationModalLabel"
      aria-hidden="true"
      data-bs-backdrop="static"
    >
      <div className="modal-dialog modal-lg modal-dialog-centered">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title" id="locationModalLabel">
              {editingLocation ? "Edit Location" : "Add New Location"}
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
              <div className="row">
                <div className="col-md-12">
                  <div className="mb-3">
                    <label className="form-label">
                      Location Name <span className="text-danger">*</span>
                    </label>
                    <input
                      type="text"
                      className="form-control"
                      name="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      placeholder="e.g. Main Office, Branch Office"
                      required
                    />
                  </div>
                </div>

                <div className="col-md-12">
                  <div className="mb-3">
                    <label className="form-label">
                      Address <span className="text-danger">*</span>
                    </label>
                    <div className="input-group">
                      <textarea
                        className="form-control"
                        name="address"
                        value={formData.address}
                        onChange={handleInputChange}
                        onBlur={handleAddressBlur}
                        placeholder="Enter full address"
                        rows={3}
                        required
                      />
                      <button
                        type="button"
                        className="btn btn-outline-primary"
                        onClick={() => geocodeAddress(formData.address)}
                        disabled={geocoding || !formData.address.trim()}
                        title="Get coordinates from address"
                      >
                        {geocoding ? (
                          <span className="spinner-border spinner-border-sm" />
                        ) : (
                          <i className="ti ti-map-search" />
                        )}
                      </button>
                    </div>
                    <small className="text-muted">
                      Enter address and click the search icon to auto-fill coordinates
                    </small>
                  </div>
                </div>

                <div className="col-md-6">
                  <div className="mb-3">
                    <label className="form-label">
                      Latitude <span className="text-danger">*</span>
                    </label>
                    <input
                      type="number"
                      step="any"
                      className="form-control"
                      name="latitude"
                      value={formData.latitude}
                      onChange={handleInputChange}
                      placeholder="e.g. 28.6139"
                      min="-90"
                      max="90"
                      required
                    />
                  </div>
                </div>

                <div className="col-md-6">
                  <div className="mb-3">
                    <label className="form-label">
                      Longitude <span className="text-danger">*</span>
                    </label>
                    <input
                      type="number"
                      step="any"
                      className="form-control"
                      name="longitude"
                      value={formData.longitude}
                      onChange={handleInputChange}
                      placeholder="e.g. 77.2090"
                      min="-180"
                      max="180"
                      required
                    />
                  </div>
                </div>

                <div className="col-md-12">
                  <div className="mb-3">
                    <button
                      type="button"
                      className="btn btn-outline-info btn-sm"
                      onClick={getCurrentLocation}
                      disabled={geocoding}
                    >
                      <i className="ti ti-current-location me-1" />
                      {geocoding ? "Getting location..." : "Use Current Location"}
                    </button>
                    <button
                      type="button"
                      className="btn btn-outline-secondary btn-sm ms-2"
                      onClick={() => {
                        if (formData.latitude && formData.longitude) {
                          reverseGeocode(formData.latitude, formData.longitude);
                        } else {
                          toast.warning("Please enter latitude and longitude first");
                        }
                      }}
                      disabled={geocoding || !formData.latitude || !formData.longitude}
                    >
                      <i className="ti ti-arrow-back me-1" />
                      Get Address from Coordinates
                    </button>
                  </div>
                </div>

                <div className="col-md-12">
                  <div className="mb-3">
                    <label className="form-label">
                      Radius (meters) <span className="text-danger">*</span>
                    </label>
                    <input
                      type="number"
                      className="form-control"
                      name="radius"
                      value={formData.radius}
                      onChange={handleInputChange}
                      placeholder="100"
                      min="1"
                      required
                    />
                    <small className="text-muted">
                      Geofencing radius in meters for location tracking
                    </small>
                  </div>
                </div>

                {formData.latitude && formData.longitude && (
                  <div className="col-md-12">
                    <div className="mb-3">
                      <label className="form-label">Location Preview</label>
                      <div
                        style={{
                          height: "300px",
                          width: "100%",
                          border: "1px solid #ddd",
                          borderRadius: "4px",
                          overflow: "hidden",
                        }}
                      >
                        <iframe
                          width="100%"
                          height="100%"
                          frameBorder="0"
                          scrolling="no"
                          src={`https://www.openstreetmap.org/export/embed.html?bbox=${
                            parseFloat(formData.longitude) - 0.01
                          },${parseFloat(formData.latitude) - 0.01},${
                            parseFloat(formData.longitude) + 0.01
                          },${parseFloat(formData.latitude) + 0.01}&layer=mapnik&marker=${
                            formData.latitude
                          },${formData.longitude}`}
                        />
                      </div>
                      <small className="text-muted">
                        <a
                          href={`https://www.openstreetmap.org/?mlat=${formData.latitude}&mlon=${formData.longitude}&zoom=15`}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          View larger map
                        </a>
                      </small>
                    </div>
                  </div>
                )}
              </div>
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
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" />
                    {editingLocation ? "Updating..." : "Adding..."}
                  </>
                ) : (
                  <>
                    <i className="ti ti-check me-1" />
                    {editingLocation ? "Update Location" : "Add Location"}
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

export default LocationModal;

