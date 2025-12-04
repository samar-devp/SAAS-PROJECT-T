import React, { useState } from "react";
import axios from "axios";
import { toast } from "react-toastify";
import { getAdminIdForApi } from "../../../core/utils/apiHelpers";

interface DeleteModalProps {
  itemId: number | null;
  onConfirmDelete: () => void;
  onCancel: () => void;
}

const DeleteModal: React.FC<DeleteModalProps> = ({
  itemId,
  onConfirmDelete,
  onCancel,
}) => {
  const [loading, setLoading] = useState(false);

  const handleDelete = async () => {
    if (!itemId) {
      toast.error("Week Off ID not found");
      return;
    }

    setLoading(true);

    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = getAdminIdForApi();

      if (!admin_id) {
        toast.error("Admin ID not found. Please login again.");
        setLoading(false);
        return;
      }

      const response = await axios.delete(
        `http://127.0.0.1:8000/api/week-off-policies/${admin_id}/${itemId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      // Use backend message if available
      toast.success(response.data?.message || "Week off policy deleted successfully!");
      onConfirmDelete();

      // Close modal
      const modalElement = document.getElementById("delete_week_off_modal");
      if (modalElement) {
        const modal = (window as any).bootstrap?.Modal?.getInstance(modalElement);
        if (modal) {
          modal.hide();
        }
      }
    } catch (error: any) {
      console.error("Error deleting week off policy:", error);
      
      // Show the full error message from backend
      const errorMessage = error.response?.data?.message || 
                          error.response?.data?.detail || 
                          "Failed to delete week off policy";
      
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
      id="delete_week_off_modal"
      tabIndex={-1}
      aria-labelledby="deleteWeekOffModalLabel"
      aria-hidden="true"
      data-bs-backdrop="static"
    >
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content">
          <div className="modal-body text-center">
            <span className="avatar avatar-xl bg-transparent-danger text-danger mb-3">
              <i className="ti ti-trash-x fs-36" />
            </span>
            <h4 className="mb-1">Confirm Delete</h4>
            <p className="mb-3">
              Are you sure you want to delete this week off policy? This action cannot be undone.
            </p>
            <div className="d-flex justify-content-center">
              <button
                type="button"
                className="btn btn-light me-3"
                data-bs-dismiss="modal"
                onClick={handleCancel}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-danger"
                onClick={handleDelete}
                disabled={loading || itemId === null}
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" />
                    Deleting...
                  </>
                ) : (
                  "Yes, Delete"
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeleteModal;

