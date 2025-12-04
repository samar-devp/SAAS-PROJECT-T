import React, { useState, useEffect, useMemo } from "react";
import axios from "axios";
import { toast } from "react-toastify";
import { getAdminIdForApi } from "../../../core/utils/apiHelpers";

interface WeekOffModalProps {
  onWeekOffAdded: () => void;
  editingWeekOff: any;
  onWeekOffUpdated: () => void;
  onEditClose: () => void;
}

type WeekOffFormState = {
  name: string;
  week_off_type: string;
  week_days: string[];
  description: string;
  status: "Active" | "Inactive";
};

const initialFormState: WeekOffFormState = {
  name: "",
  week_off_type: "Fixed",
  week_days: ["Sunday"],
  description: "",
  status: "Active",
};

const WEEKDAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

const WeekOffModal: React.FC<WeekOffModalProps> = ({
  onWeekOffAdded,
  editingWeekOff,
  onWeekOffUpdated,
  onEditClose,
}) => {
  const [addFormData, setAddFormData] = useState<WeekOffFormState>(initialFormState);
  const [editFormData, setEditFormData] = useState<WeekOffFormState>(initialFormState);

  const statusOptions = useMemo(
    () => [
      { value: "Active" as const, label: "Active" },
      { value: "Inactive" as const, label: "Inactive" },
    ],
    []
  );

  useEffect(() => {
    if (editingWeekOff) {
      setEditFormData({
        name: editingWeekOff.name ?? "",
        week_off_type: editingWeekOff.week_off_type ?? "Fixed",
        week_days: Array.isArray(editingWeekOff.week_days) ? editingWeekOff.week_days : ["Sunday"],
        description: editingWeekOff.description ?? "",
        status: editingWeekOff.is_active ? "Active" : "Inactive",
      });
    } else {
      setEditFormData(initialFormState);
    }
  }, [editingWeekOff]);

  const handleAddInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setAddFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleEditInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setEditFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleWeekDayToggle = (day: string, isEdit: boolean) => {
    const setter = isEdit ? setEditFormData : setAddFormData;
    const formData = isEdit ? editFormData : addFormData;

    setter((prev) => {
      const currentDays = prev.week_days;
      if (currentDays.includes(day)) {
        return { ...prev, week_days: currentDays.filter((d) => d !== day) };
      } else {
        return { ...prev, week_days: [...currentDays, day] };
      }
    });
  };

  const buildPayload = (form: WeekOffFormState) => ({
    name: form.name,
    week_off_type: form.week_off_type,
    week_days: form.week_days,
    description: form.description,
    is_active: form.status === "Active",
  });

  const resetAddForm = () => setAddFormData(initialFormState);

  const handleCreate = async () => {
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = getAdminIdForApi();

      if (!admin_id) {
        toast.error("Admin ID not found");
        return;
      }

      if (!addFormData.name.trim()) {
        toast.error("Policy name is required");
        return;
      }

      if (addFormData.week_days.length === 0) {
        toast.error("Please select at least one week day");
        return;
      }

      const payload = buildPayload(addFormData);

      const response = await axios.post(
        `http://127.0.0.1:8000/api/week-off-policies/${admin_id}`,
        payload,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const policyName = response.data.data?.name || "Week Off Policy";
      toast.success(`✅ Week off policy '${policyName}' created successfully`);
      
      resetAddForm();
      onWeekOffAdded();
    } catch (error: any) {
      console.error("Error creating week off policy:", error);
      const errorMessage =
        error.response?.data?.message || "Failed to create week off policy";
      toast.error(`❌ ${errorMessage}`);
    }
  };

  const handleUpdate = async () => {
    if (!editingWeekOff) return;

    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = getAdminIdForApi();

      if (!admin_id) {
        toast.error("Admin ID not found");
        return;
      }

      if (!editFormData.name.trim()) {
        toast.error("Policy name is required");
        return;
      }

      if (editFormData.week_days.length === 0) {
        toast.error("Please select at least one week day");
        return;
      }

      const payload = buildPayload(editFormData);

      const response = await axios.put(
        `http://127.0.0.1:8000/api/week-off-policies/${admin_id}/${editingWeekOff.id}`,
        payload,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const policyName = response.data.data?.name || editFormData.name;
      toast.success(`✅ Week off policy '${policyName}' updated successfully`);
      
      onWeekOffUpdated();
      onEditClose();
    } catch (error: any) {
      console.error("Error updating week off policy:", error);
      const errorMessage =
        error.response?.data?.message || "Failed to update week off policy";
      toast.error(`❌ ${errorMessage}`);
    }
  };

  const handleEditCancel = () => {
    onEditClose();
  };

  const renderWeekOffFields = (
    formData: WeekOffFormState,
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => void,
    isEdit: boolean
  ) => (
    <div>
      <div className="row">
        <div className="col-md-12">
          <div className="mb-3">
            <label className="form-label">Policy Name <span className="text-danger">*</span></label>
            <input
              type="text"
              className="form-control"
              name="name"
              value={formData.name}
              onChange={onChange}
              placeholder="e.g., Weekend Policy"
            />
          </div>
        </div>
      </div>

      <div className="row">
        <div className="col-12">
          <div className="mb-3">
            <label className="form-label">Week Days <span className="text-danger">*</span></label>
            <div className="d-flex flex-wrap gap-2">
              {WEEKDAYS.map((day) => (
                <div key={day} className="form-check">
                  <input
                    type="checkbox"
                    className="form-check-input"
                    id={`${isEdit ? 'edit' : 'add'}_${day}`}
                    checked={formData.week_days.includes(day)}
                    onChange={() => handleWeekDayToggle(day, isEdit)}
                  />
                  <label
                    className="form-check-label"
                    htmlFor={`${isEdit ? 'edit' : 'add'}_${day}`}
                  >
                    {day}
                  </label>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="row">
        <div className="col-md-12">
          <div className="mb-3">
            <label className="form-label">Description</label>
            <textarea
              className="form-control"
              name="description"
              rows={3}
              value={formData.description}
              onChange={onChange}
              placeholder="Enter policy description..."
            />
          </div>
        </div>
      </div>

      <div className="row">
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
    </div>
  );

  return (
    <>
      {/* Add Week Off Modal */}
      <div className="modal fade" id="add_week_off">
        <div className="modal-dialog modal-dialog-centered modal-md">
          <div className="modal-content">
            <div className="modal-header">
              <h4 className="modal-title">Add Week Off Policy</h4>
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
                {renderWeekOffFields(addFormData, handleAddInputChange, false)}
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
                  Add Week Off
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Edit Week Off Modal */}
      <div className="modal fade" id="edit_week_off">
        <div className="modal-dialog modal-dialog-centered modal-md">
          <div className="modal-content">
            <div className="modal-header">
              <h4 className="modal-title">Edit Week Off Policy</h4>
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
                {renderWeekOffFields(editFormData, handleEditInputChange, true)}
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

export default WeekOffModal;

