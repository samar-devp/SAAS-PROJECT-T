import React, { useState } from "react";
import axios from "axios";
import { toast } from "react-toastify";

interface DeleteModalProps {
  locationId: number | null;
  onLocationDeleted: () => void;
  onCancel: () => void;
}

const DeleteModal: React.FC<DeleteModalProps> = ({
  locationId,
  onLocationDeleted,
  onCancel,
}) => {
  const [loading, setLoading] = useState(false);

  const handleDelete = async () => {
    if (!locationId) {
      toast.error("Location ID not found");
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

      const response = await axios.delete(
        `http://127.0.0.1:8000/api/locations/${admin_id}/${locationId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      // Use backend message if available
      toast.success(response.data?.message || "Location deleted successfully!");
      onLocationDeleted();

      // Close modal
      const modalElement = document.getElementById("deleteLocationModal");
      if (modalElement) {
        const modal = (window as any).bootstrap?.Modal?.getInstance(modalElement);
        if (modal) {
          modal.hide();
        }
      }
    } catch (error: any) {
      console.error("Error deleting location:", error);
      
      // Show the full error message from backend
      const errorMessage = error.response?.data?.message || 
                          error.response?.data?.detail || 
                          "Failed to delete location";
      
      // Display backend message (already contains proper formatting and details)
      toast.error(errorMessage, {
        autoClose: 6000  // Give more time to read detailed message
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    onCancel();
  };

  return (
    <div
      className="modal fade"
      id="deleteLocationModal"
      tabIndex={-1}
      aria-labelledby="deleteLocationModalLabel"
      aria-hidden="true"
      data-bs-backdrop="static"
    >
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title" id="deleteLocationModalLabel">
              Delete Location
            </h5>
            <button
              type="button"
              className="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
              onClick={handleCancel}
            />
          </div>
          <div className="modal-body">
            <p>Are you sure you want to delete this location? This action cannot be undone.</p>
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
              type="button"
              className="btn btn-danger"
              onClick={handleDelete}
              disabled={loading || locationId === null}
            >
              {loading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" />
                  Deleting...
                </>
              ) : (
                <>
                  <i className="ti ti-trash me-1" />
                  Delete
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeleteModal;

