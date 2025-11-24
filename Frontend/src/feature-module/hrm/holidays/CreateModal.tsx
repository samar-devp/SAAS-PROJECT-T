import dayjs from "dayjs";
import CommonSelect, { Option } from "../../../core/common/commonSelect";
import { DatePicker } from "antd";
import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";

type HolidaysModalProps = {
  onHolidayAdded?: (newHoliday: any) => void;
  editingHoliday?: any;
  onHolidayUpdated?: (updatedHoliday: any) => void;
  onEditClose?: () => void;
};

const initialFormState = {
  title: "",
  date: "",
  description: "",
  status: "Active",
};

const HolidaysModal: React.FC<HolidaysModalProps> = ({
  onHolidayAdded,
  editingHoliday,
  onHolidayUpdated,
  onEditClose,
}) => {
  const [addFormData, setAddFormData] = useState(initialFormState);
  const [editFormData, setEditFormData] = useState(initialFormState);

  const statusOptions: Option[] = useMemo(
    () => [
      { value: "Active", label: "Active" },
      { value: "Inactive", label: "Inactive" },
    ],
    []
  );

  const getStatusOption = (value: string) =>
    statusOptions.find((option) => option.value === value) ?? statusOptions[0];

  useEffect(() => {
    if (editingHoliday) {
      setEditFormData({
        title: editingHoliday.name ?? "",
        date: editingHoliday.holiday_date ?? "",
        description: editingHoliday.description ?? "",
        status: editingHoliday.is_active ? "Active" : "Inactive",
      });
    } else {
      setEditFormData(initialFormState);
    }
  }, [editingHoliday, statusOptions]);

  const handleAddInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setAddFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleEditInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setEditFormData((prev) => ({ ...prev, [name]: value }));
  };

  const resetAddForm = () => setAddFormData(initialFormState);

  const handleCreate = async () => {
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");
      const payload = {
        name: addFormData.title,
        holiday_date: addFormData.date,
        description: addFormData.description,
        admin: admin_id,
      };

      const response = await axios.post(
        `http://127.0.0.1:8000/api/holidays/${admin_id}`,
        payload,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const createdHoliday = response.data;
      onHolidayAdded?.(createdHoliday);
      resetAddForm();
    } catch (error) {
      console.error("Error adding holiday:", error);
    }
  };

  const getEditingHolidayId = () =>
    editingHoliday?.id ?? editingHoliday?.holiday_id ?? editingHoliday?.holidayId ?? null;

  const handleUpdate = async () => {
    const holidayId = getEditingHolidayId();
    const admin_id = sessionStorage.getItem("user_id");

    if (!holidayId || !admin_id) {
      console.warn("Missing identifiers for update");
      return;
    }

    try {
      const token = sessionStorage.getItem("access_token");
      const payload = {
        name: editFormData.title,
        holiday_date: editFormData.date,
        description: editFormData.description,
        admin: admin_id,
      };

      const response = await axios.put(
        `http://127.0.0.1:8000/api/holidays/${admin_id}/${holidayId}`,
        payload,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      onHolidayUpdated?.(response.data);
      onEditClose?.();
    } catch (error) {
      console.error("Error updating holiday:", error);
    }
  };

  const handleEditCancel = () => {
    onEditClose?.();
    setEditFormData(initialFormState);
  };
  return (
    <>
      {/* Add Holiday Modal */}
      <div className="modal fade" id="add_holiday">
        <div className="modal-dialog modal-dialog-centered modal-md">
          <div className="modal-content">
            <div className="modal-header">
              <h4 className="modal-title">Add Holiday</h4>
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
                <div className="row">
                  <div className="col-md-12">
                    <div className="mb-3">
                      <label className="form-label">Name</label>
                      <input
                          type="text"
                          className="form-control"
                          name="title"
                          value={addFormData.title}
                          onChange={handleAddInputChange}
                        />
                    </div>
                  </div>
                  <div className="col-md-12">
                    <div className="mb-3">
                      <label className="form-label">Date</label>
                      <div className="input-icon-end position-relative">
                        <DatePicker
                          format="YYYY-MM-DD"
                          value={addFormData.date ? dayjs(addFormData.date) : null}
                          onChange={(_, dateString) =>
                            setAddFormData((prev) => ({
                              ...prev,
                              date: (dateString as string) || "",
                            }))
                          }
                          placeholder="YYYY-MM-DD"
                        />
                        <span className="input-icon-addon">
                          <i className="ti ti-calendar text-gray-7" />
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-12">
                    <div className="mb-3">
                      <label className="form-label">Description</label>
                      <textarea
                        className="form-control"
                        rows={3}
                        name="description"
                        value={addFormData.description}
                        onChange={handleAddInputChange}
                      />
                    </div>
                  </div>
                </div>
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
      Add Holiday
    </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Edit Holiday Modal */}
      <div className="modal fade" id="edit_holiday">
        <div className="modal-dialog modal-dialog-centered modal-md">
          <div className="modal-content">
            <div className="modal-header">
              <h4 className="modal-title">Edit Holiday</h4>
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
                <div className="row">
                  <div className="col-md-12">
                    <div className="mb-3">
                      <label className="form-label">Name</label>
                      <input
                        type="text"
                        className="form-control"
                        name="title"
                        value={editFormData.title}
                        onChange={handleEditInputChange}
                      />
                    </div>
                  </div>
                  <div className="col-md-12">
                    <div className="mb-3">
                      <label className="form-label">Date</label>
                      <div>
                        <DatePicker
                          format="YYYY-MM-DD"
                          value={editFormData.date ? dayjs(editFormData.date) : null}
                          onChange={(_, dateString) =>
                            setEditFormData((prev) => ({
                              ...prev,
                              date: (dateString as string) || "",
                            }))
                          }
                          placeholder="YYYY-MM-DD"
                        />
                      </div>
                    </div>
                  </div>
                  <div className="col-md-12">
                    <div className="mb-3">
                      <label className="form-label">Description</label>
                      <textarea
                        className="form-control"
                        rows={3}
                        name="description"
                        value={editFormData.description}
                        onChange={handleEditInputChange}
                      />
                    </div>
                  </div>
                </div>
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

export default HolidaysModal;
