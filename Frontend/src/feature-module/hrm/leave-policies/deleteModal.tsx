import React, { useState } from "react";
import axios from "axios";
import { toast } from "react-toastify";

interface DeleteModalProps {
  orgId: string | null;
  policyId: string | null;
  onPolicyDeleted: () => void;
  onCancel: () => void;
}

const DeleteModal: React.FC<DeleteModalProps> = ({
  orgId,
  policyId,
  onPolicyDeleted,
  onCancel,
}) => {
  const [loading, setLoading] = useState(false);

  const handleDelete = async () => {
    if (!policyId) {
      toast.error("Policy ID not found");
      return;
    }

    if (!orgId) {
      toast.error("Organization ID not found");
      return;
    }

    setLoading(true);

    try {
      const token = sessionStorage.getItem("access_token");

      // Soft delete by setting is_active to false
      await axios.put(
        `http://127.0.0.1:8000/api/leave/leave-policies/${orgId}/${policyId}`,
        { is_active: false },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      toast.success("Leave policy deleted successfully!");
      onPolicyDeleted();

      // Close modal
      const modalElement = document.getElementById("deleteLeavePolicyModal");
      if (modalElement) {
        const modal = (window as any).bootstrap?.Modal?.getInstance(modalElement);
        if (modal) {
          modal.hide();
        }
      }
    } catch (error: any) {
      console.error("Error deleting leave policy:", error);
      toast.error(
        error.response?.data?.message ||
          error.response?.data?.detail ||
          "Failed to delete leave policy"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    onCancel();
  };

  if (policyId === null) {
    return null;
  }

  return (
    <div
      className="modal fade"
      id="deleteLeavePolicyModal"
      tabIndex={-1}
      aria-labelledby="deleteLeavePolicyModalLabel"
      aria-hidden="true"
      data-bs-backdrop="static"
    >
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title" id="deleteLeavePolicyModalLabel">
              Delete Leave Policy
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
            <p>
              Are you sure you want to delete this leave policy? This action cannot be undone.
            </p>
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
              disabled={loading}
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

