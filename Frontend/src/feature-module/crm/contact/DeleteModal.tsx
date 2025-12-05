import React from "react";

interface DeleteModalProps {
  contactId: string | null;
  onDelete: () => void;
  onClose: () => void;
}

const DeleteModal: React.FC<DeleteModalProps> = ({ contactId, onDelete, onClose }) => {
  if (!contactId) return null;

  return (
    <div
      className="modal fade"
      id="deleteContactModal"
      tabIndex={-1}
      aria-labelledby="deleteContactModalLabel"
      aria-hidden="true"
    >
      <div className="modal-dialog">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title" id="deleteContactModalLabel">
              Delete Contact
            </h5>
            <button
              type="button"
              className="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
              onClick={onClose}
            />
          </div>
          <div className="modal-body">
            <p>Are you sure you want to delete this contact? This action cannot be undone.</p>
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
            <button
              type="button"
              className="btn btn-danger"
              onClick={onDelete}
            >
              <i className="ti ti-trash me-1" />
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeleteModal;

