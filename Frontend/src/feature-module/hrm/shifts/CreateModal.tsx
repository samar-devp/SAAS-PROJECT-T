import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";

type ServiceShiftModalProps = {
  onShiftAdded?: (newShift: any) => void;
  editingShift?: any;
  onShiftUpdated?: (updatedShift: any) => void;
  onEditClose?: () => void;
};

type ShiftFormState = {
  shift_name: string;
  start_time: string;
  end_time: string;
  break_duration_minutes: string;
  status: "Active" | "Inactive";
};

const initialFormState: ShiftFormState = {
  shift_name: "",
  start_time: "",
  end_time: "",
  break_duration_minutes: "",
  status: "Active",
};

const ServiceShiftModal: React.FC<ServiceShiftModalProps> = ({
  onShiftAdded,
  editingShift,
  onShiftUpdated,
  onEditClose,
}) => {
  const [addFormData, setAddFormData] = useState<ShiftFormState>(initialFormState);
  const [editFormData, setEditFormData] = useState<ShiftFormState>(initialFormState);

  const statusOptions = useMemo(
    () => [
      { value: "Active" as const, label: "Active" },
      { value: "Inactive" as const, label: "Inactive" },
    ],
    []
  );

  useEffect(() => {
    if (editingShift) {
      setEditFormData({
        shift_name: editingShift.shift_name ?? "",
        start_time: editingShift.start_time ?? "",
        end_time: editingShift.end_time ?? "",
        break_duration_minutes:
          editingShift.break_duration_minutes?.toString() ?? "",
        status: editingShift.is_active ? "Active" : "Inactive",
      });
    } else {
      setEditFormData(initialFormState);
    }
  }, [editingShift]);

  const handleAddInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setAddFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleEditInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setEditFormData((prev) => ({ ...prev, [name]: value }));
  };

  const buildPayload = (form: ShiftFormState) => ({
    shift_name: form.shift_name,
    start_time: form.start_time,
    end_time: form.end_time,
    break_duration_minutes:
      form.break_duration_minutes !== ""
        ? Number(form.break_duration_minutes)
        : null,
    is_active: form.status === "Active",
  });

  const resetAddForm = () => setAddFormData(initialFormState);

  const handleCreate = async () => {
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");
      if (!admin_id) {
        console.warn("Admin id missing");
        return;
      }

      const response = await axios.post(
        `http://127.0.0.1:8000/api/service-shifts/${admin_id}`,
        buildPayload(addFormData),
        token
          ? {
              headers: { Authorization: `Bearer ${token}` },
            }
          : undefined
      );

      onShiftAdded?.(response.data);
      resetAddForm();
    } catch (error) {
      console.error("Error adding service shift:", error);
    }
  };

  const getEditingShiftId = () =>
    editingShift?.id ?? editingShift?.shift_id ?? editingShift?.shiftId ?? null;

  const handleUpdate = async () => {
    const shiftId = getEditingShiftId();
    const admin_id = sessionStorage.getItem("user_id");

    if (!shiftId || !admin_id) {
      console.warn("Missing identifiers for update");
      return;
    }

    try {
      const token = sessionStorage.getItem("access_token");

      const response = await axios.put(
        `http://127.0.0.1:8000/api/service-shifts/${admin_id}/${shiftId}`,
        buildPayload(editFormData),
        token
          ? {
              headers: { Authorization: `Bearer ${token}` },
            }
          : undefined
      );

      onShiftUpdated?.(response.data);
      onEditClose?.();
    } catch (error) {
      console.error("Error updating service shift:", error);
    }
  };

  const handleEditCancel = () => {
    onEditClose?.();
    setEditFormData(initialFormState);
  };

  const renderShiftFields = (
    formData: ShiftFormState,
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void
  ) => (
    <div className="row">
      <div className="col-md-12">
        <div className="mb-3">
          <label className="form-label">Shift Name</label>
          <input
            type="text"
            className="form-control"
            name="shift_name"
            value={formData.shift_name}
            onChange={onChange}
            placeholder="e.g. Default Shift"
          />
        </div>
      </div>
      <div className="col-md-6">
        <div className="mb-3">
          <label className="form-label">Start Time</label>
          <input
            type="time"
            className="form-control"
            name="start_time"
            value={formData.start_time}
            onChange={onChange}
          />
        </div>
      </div>
      <div className="col-md-6">
        <div className="mb-3">
          <label className="form-label">End Time</label>
          <input
            type="time"
            className="form-control"
            name="end_time"
            value={formData.end_time}
            onChange={onChange}
          />
        </div>
      </div>
      <div className="col-md-6">
        <div className="mb-3">
          <label className="form-label">Break Duration (minutes)</label>
          <input
            type="number"
            min="0"
            className="form-control"
            name="break_duration_minutes"
            value={formData.break_duration_minutes}
            onChange={onChange}
            placeholder="Optional"
          />
        </div>
      </div>
      <div className="col-md-6">
        <div className="mb-3">
          <label className="form-label">Status</label>
          <select
            className="form-select"
            name="status"
            value={formData.status}
            onChange={onChange}
          >
            {statusOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Add Shift Modal */}
      <div className="modal fade" id="add_shift">
        <div className="modal-dialog modal-dialog-centered modal-md">
          <div className="modal-content">
            <div className="modal-header">
              <h4 className="modal-title">Add Shift</h4>
              <button
                type="button"
                className="btn-close custom-btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
              >
                <i className="ti ti-x" />
              </button>
            </div>
            <form>
              <div className="modal-body pb-0">
                {renderShiftFields(addFormData, handleAddInputChange)}
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-light me-2"
                  data-bs-dismiss="modal"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleCreate}
                  data-bs-dismiss="modal"
                >
                  Add Shift
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Edit Shift Modal */}
      <div className="modal fade" id="edit_shift">
        <div className="modal-dialog modal-dialog-centered modal-md">
          <div className="modal-content">
            <div className="modal-header">
              <h4 className="modal-title">Edit Shift</h4>
              <button
                type="button"
                className="btn-close custom-btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
              >
                <i className="ti ti-x" />
              </button>
            </div>
            <form>
              <div className="modal-body pb-0">
                {renderShiftFields(editFormData, handleEditInputChange)}
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-light me-2"
                  data-bs-dismiss="modal"
                  onClick={handleEditCancel}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  data-bs-dismiss="modal"
                  onClick={handleUpdate}
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
};

export default ServiceShiftModal;
