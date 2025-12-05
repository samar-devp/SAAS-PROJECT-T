import React, { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "react-toastify";
import { getAdminIdForApi } from "../../../core/utils/apiHelpers";

interface CheckInOutModalProps {
  visit: any;
  onCheckInOut: () => void;
  onClose: () => void;
}

const CheckInOutModal: React.FC<CheckInOutModalProps> = ({
  visit,
  onCheckInOut,
  onClose,
}) => {
  const [loading, setLoading] = useState(false);
  const [latitude, setLatitude] = useState<string>("");
  const [longitude, setLongitude] = useState<string>("");
  const [note, setNote] = useState<string>("");
  const [gettingLocation, setGettingLocation] = useState(false);

  useEffect(() => {
    if (visit) {
      getCurrentLocation();
    }
  }, [visit]);

  const getCurrentLocation = () => {
    if (!navigator.geolocation) {
      toast.error("Geolocation is not supported by your browser.");
      return;
    }

    setGettingLocation(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLatitude(position.coords.latitude.toFixed(6));
        setLongitude(position.coords.longitude.toFixed(6));
        setGettingLocation(false);
        toast.success("Location captured!");
      },
      (error) => {
        console.error("Geolocation error:", error);
        toast.error("Failed to get current location. Please enter manually.");
        setGettingLocation(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!latitude || !longitude) {
      toast.error("Please provide GPS coordinates");
      return;
    }

    const lat = parseFloat(latitude);
    const lon = parseFloat(longitude);

    if (isNaN(lat) || isNaN(lon)) {
      toast.error("Please enter valid GPS coordinates");
      return;
    }

    if (lat < -90 || lat > 90) {
      toast.error("Latitude must be between -90 and 90");
      return;
    }

    if (lon < -180 || lon > 180) {
      toast.error("Longitude must be between -180 and 180");
      return;
    }

    setLoading(true);

    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = getAdminIdForApi();

      if (!admin_id || !visit) {
        toast.error("Missing required information");
        setLoading(false);
        return;
      }

      const user_id = visit.assigned_employee || visit.assigned_employee_id;
      const visit_id = visit.id;
      const isCheckIn = visit.status === "pending";
      const endpoint = isCheckIn ? "check-in" : "check-out";

      const payload = {
        latitude: lat,
        longitude: lon,
        note: note.trim() || null,
      };

      const response = await axios.post(
        `http://127.0.0.1:8000/api/visit/visit-${endpoint}/${admin_id}/${user_id}/${visit_id}`,
        payload,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      toast.success(response.data.message || `${isCheckIn ? "Check-in" : "Check-out"} successful!`);
      onCheckInOut();

      // Close modal
      const modalElement = document.getElementById("checkInOutModal");
      if (modalElement) {
        const modal = (window as any).bootstrap?.Modal?.getInstance(modalElement);
        if (modal) {
          modal.hide();
        }
      }
    } catch (error: any) {
      console.error(`Error during ${visit.status === "pending" ? "check-in" : "check-out"}:`, error);
      toast.error(
        error.response?.data?.message || 
        `Failed to ${visit.status === "pending" ? "check-in" : "check-out"}`
      );
    } finally {
      setLoading(false);
    }
  };

  if (!visit) return null;

  const isCheckIn = visit.status === "pending";

  return (
    <div
      className="modal fade"
      id="checkInOutModal"
      tabIndex={-1}
      aria-labelledby="checkInOutModalLabel"
      aria-hidden="true"
      data-bs-backdrop="static"
    >
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title" id="checkInOutModalLabel">
              {isCheckIn ? "Check In" : "Check Out"}
            </h5>
            <button
              type="button"
              className="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
              onClick={onClose}
            ></button>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="modal-body">
              <div className="mb-3">
                <label className="form-label">
                  Visit: <strong>{visit.title}</strong>
                </label>
              </div>
              <div className="mb-3">
                <label className="form-label">
                  GPS Coordinates <span className="text-danger">*</span>
                </label>
                <div className="row">
                  <div className="col-md-6 mb-2">
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Latitude"
                      value={latitude}
                      onChange={(e) => setLatitude(e.target.value)}
                      required
                    />
                  </div>
                  <div className="col-md-6 mb-2">
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Longitude"
                      value={longitude}
                      onChange={(e) => setLongitude(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <button
                  type="button"
                  className="btn btn-sm btn-outline-primary mt-2"
                  onClick={getCurrentLocation}
                  disabled={gettingLocation}
                >
                  {gettingLocation ? "Getting Location..." : "Get Current Location"}
                </button>
              </div>
              <div className="mb-3">
                <label className="form-label">Note (Optional)</label>
                <textarea
                  className="form-control"
                  rows={3}
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Add any notes about this visit..."
                />
              </div>
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-secondary"
                data-bs-dismiss="modal"
                onClick={onClose}
              >
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={loading || gettingLocation}>
                {loading ? "Processing..." : isCheckIn ? "Check In" : "Check Out"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CheckInOutModal;

