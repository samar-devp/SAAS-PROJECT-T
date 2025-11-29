// src/core/modals/DeleteModal.tsx
import React, { useState } from "react";
import axios from "axios";
import { toast } from "react-toastify";

interface DeleteModalProps {
  admin_id: string | null;
  leaveTypeId: number | null;
  onDeleted?: () => void;
}

const DeleteModal: React.FC<DeleteModalProps> = ({
  admin_id,
  leaveTypeId,
  onDeleted,
}) => {
  const [loading, setLoading] = useState(false);

  const handleDelete = async () => {
    if (leaveTypeId == null || !admin_id) {
      toast.error("Missing required identifiers");
      return;
    }
    
    setLoading(true);
    try {
      const token = sessionStorage.getItem("access_token");
      
      if (!token) {
        toast.error("Authentication token not found");
        setLoading(false);
        return;
      }

      await axios.delete(
        `http://127.0.0.1:8000/api/leave-types/${admin_id}/${leaveTypeId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      
      toast.success("Leave type deleted successfully");
      onDeleted?.();
      
      // Close modal
      const modalElement = document.getElementById("delete_modal");
      if (modalElement) {
        const modalInstance = (window as any).bootstrap?.Modal?.getInstance(modalElement);
        if (modalInstance) {
          modalInstance.hide();
        }
      }
    } catch (error: any) {
      console.error("Error deleting leave type:", error);
      toast.error(error.response?.data?.message || error.response?.data?.error || "Failed to delete leave type");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="modal fade"
      id="delete_modal"
      tabIndex={-1}
      aria-hidden="true"
    >
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content">
          <div className="modal-body text-center">
            <span className="avatar avatar-xl bg-transparent-danger text-danger mb-3">
              <i className="ti ti-trash-x fs-36" />
            </span>
            <h4 className="mb-1">Confirm Delete</h4>
            <p className="mb-3">
              Are you sure you want to delete this leave type? This action cannot be
              undone.
            </p>
            <div className="d-flex justify-content-center">
              <button
                type="button"
                className="btn btn-light me-3"
                data-bs-dismiss="modal"
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-danger"
                data-bs-dismiss="modal"
                onClick={handleDelete}
                disabled={leaveTypeId === null || !admin_id || loading}
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