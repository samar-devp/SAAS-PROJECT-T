import CommonSelect from "../common/commonSelect";
import { DatePicker } from "antd";
import React, { useState } from "react";
import axios from "axios";

const HolidaysModal = () => {
  const [date, setDate] = useState<string>("");

  const [formData, setFormData] = useState({
    title: "",
    date: "",
    description: "",
    status: "Active",
  });

  const status = [
    { value: "Active", label: "Active" },
    { value: "Inactive", label: "Inactive" },
  ];

  const getModalContainer = () => {
    const modalElement = document.getElementById("modal-datepicker");
    return modalElement ? modalElement : document.body;
  };

  // handle change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // API call
  const handleSubmit = async () => {
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");
      console.log(admin_id, "+++++++++++++++Admin ID")
      const payload = {
        name: formData.title,
        holiday_date: formData.date,
        description: formData.description,
        is_active: formData.status === "Active",
        admin: admin_id, 
      };

      const response = await axios.post(
        `http://127.0.0.1:8000/api/holidays/${admin_id}`,
        payload,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      console.log("Holiday added:", response.data);
      alert("Holiday added successfully!");
    } catch (error) {
      console.error("Error adding holiday:", error);
      alert("Failed to add holiday");
    }
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
                      <label className="form-label">name</label>
                      <input
                          type="text"
                          className="form-control"
                          name="title"
                          value={formData.title}
                          onChange={handleChange}
                        />
                    </div>
                  </div>
                  <div className="col-md-12">
                    <div className="mb-3">
                      <label className="form-label">Date</label>
                      <div className="input-icon-end position-relative">
                        <DatePicker
                          format="YYYY-MM-DD"
                          onChange={(_, dateString) =>
                            setFormData((prev) => ({
                              ...prev,
                              date: dateString as string, // ✅ direct formData me set
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
                      <label className="form-label">Status</label>
                      <CommonSelect
                        className="select"
                        options={status}
                        defaultValue={status[0]}
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
      onClick={handleSubmit}
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
                      <label className="form-label">Title</label>
                      <input
                        type="text"
                        className="form-control"
                        defaultValue="New Year"
                      />
                    </div>
                  </div>
                  <div className="col-md-12">
                    <div className="mb-3">
                      <label className="form-label">Date</label>
                      <div>
                        <DatePicker
                            format="YYYY-MM-DD"
                            onChange={(_, dateString) => setDate(dateString as string)} // ✅ cast to string
                            placeholder="YYYY-MM-DD"
                          />

                          <p>Selected Date: {date}</p>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-12">
                    <div className="mb-3">
                      <label className="form-label">Description</label>
                      <textarea
                        className="form-control"
                        rows={3}
                        defaultValue={"First day of the new year"}
                      />
                    </div>
                  </div>
                  <div className="col-md-12">
                    <div className="mb-3">
                      <label className="form-label">Status</label>
                      <CommonSelect
                        className="select"
                        options={status}
                        defaultValue={status[1]}
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
                  data-bs-dismiss="modal"
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
