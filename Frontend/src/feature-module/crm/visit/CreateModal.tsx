import React, { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "react-toastify";
import { getAdminIdForApi } from "../../../core/utils/apiHelpers";

interface VisitModalProps {
  onVisitAdded: () => void;
  editingVisit: any;
  onVisitUpdated: () => void;
  onEditClose: () => void;
}

interface VisitFormState {
  title: string;
  description: string;
  schedule_date: string;
  schedule_time: string;
  client_name: string;
  location_name: string;
  address: string;
  city: string;
  state: string;
  pincode: string;
  country: string;
  contact_person: string;
  contact_phone: string;
  contact_email: string;
  assigned_employee: string;
}

const VisitModal: React.FC<VisitModalProps> = ({
  onVisitAdded,
  editingVisit,
  onVisitUpdated,
  onEditClose,
}) => {
  const initialFormState: VisitFormState = {
    title: "",
    description: "",
    schedule_date: "",
    schedule_time: "",
    client_name: "",
    location_name: "",
    address: "",
    city: "",
    state: "",
    pincode: "",
    country: "India",
    contact_person: "",
    contact_phone: "",
    contact_email: "",
    assigned_employee: "",
  };

  const [formData, setFormData] = useState<VisitFormState>(initialFormState);
  const [loading, setLoading] = useState(false);
  const [employees, setEmployees] = useState<any[]>([]);
  const [loadingEmployees, setLoadingEmployees] = useState(false);

  useEffect(() => {
    fetchEmployees();
  }, []);

  useEffect(() => {
    if (editingVisit) {
      setFormData({
        title: editingVisit.title || "",
        description: editingVisit.description || "",
        schedule_date: editingVisit.schedule_date || "",
        schedule_time: editingVisit.schedule_time || "",
        client_name: editingVisit.client_name || "",
        location_name: editingVisit.location_name || "",
        address: editingVisit.address || "",
        city: editingVisit.city || "",
        state: editingVisit.state || "",
        pincode: editingVisit.pincode || "",
        country: editingVisit.country || "India",
        contact_person: editingVisit.contact_person || "",
        contact_phone: editingVisit.contact_phone || "",
        contact_email: editingVisit.contact_email || "",
        assigned_employee: editingVisit.assigned_employee || "",
      });
    } else {
      setFormData(initialFormState);
    }
  }, [editingVisit]);

  const fetchEmployees = async () => {
    setLoadingEmployees(true);
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = getAdminIdForApi();

      if (!admin_id) {
        setLoadingEmployees(false);
        return;
      }

      const response = await axios.get(
        `http://127.0.0.1:8000/api/staff-list/${admin_id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      let employeesData = [];
      if (response.data && response.data.results && Array.isArray(response.data.results)) {
        employeesData = response.data.results;
      } else if (response.data && response.data.data) {
        if (Array.isArray(response.data.data)) {
          employeesData = response.data.data;
        } else if (response.data.data.results && Array.isArray(response.data.data.results)) {
          employeesData = response.data.data.results;
        }
      } else if (Array.isArray(response.data)) {
        employeesData = response.data;
      }
      setEmployees(employeesData);
    } catch (error: any) {
      console.error("Error fetching employees:", error);
    } finally {
      setLoadingEmployees(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title.trim()) {
      toast.error("Please enter visit title");
      return;
    }

    if (!formData.schedule_date) {
      toast.error("Please select schedule date");
      return;
    }

    if (!formData.address.trim()) {
      toast.error("Please enter address");
      return;
    }

    if (!formData.assigned_employee) {
      toast.error("Please select assigned employee");
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

      const payload: any = {
        title: formData.title.trim(),
        description: formData.description.trim(),
        schedule_date: formData.schedule_date,
        schedule_time: formData.schedule_time || null,
        client_name: formData.client_name.trim() || null,
        location_name: formData.location_name.trim() || null,
        address: formData.address.trim(),
        city: formData.city.trim() || null,
        state: formData.state.trim() || null,
        pincode: formData.pincode.trim() || null,
        country: formData.country.trim() || "India",
        contact_person: formData.contact_person.trim() || null,
        contact_phone: formData.contact_phone.trim() || null,
        contact_email: formData.contact_email.trim() || null,
        assigned_employee: formData.assigned_employee,
      };

      let response;

      if (editingVisit) {
        // Update existing visit
        const user_id = editingVisit.assigned_employee || formData.assigned_employee;
        response = await axios.put(
          `http://127.0.0.1:8000/api/visit/visit-detail-update-delete/${admin_id}/${user_id}/${editingVisit.id}`,
          payload,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        toast.success(response.data.message || "Visit updated successfully!");
        onVisitUpdated();
      } else {
        // Create new visit
        response = await axios.post(
          `http://127.0.0.1:8000/api/visit/visit-list-create/${admin_id}`,
          payload,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        toast.success(response.data.message || "Visit created successfully!");
        onVisitAdded();
      }

      // Reset form
      setFormData(initialFormState);
      
      // Close modal
      const modalElement = document.getElementById("visitModal");
      if (modalElement) {
        const modal = (window as any).bootstrap?.Modal?.getInstance(modalElement);
        if (modal) {
          modal.hide();
        }
      }
    } catch (error: any) {
      console.error("Error saving visit:", error);
      toast.error(
        error.response?.data?.message || 
        error.response?.data?.data || 
        `Failed to ${editingVisit ? "update" : "create"} visit`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setFormData(initialFormState);
    onEditClose();
  };

  return (
    <div
      className="modal fade"
      id="visitModal"
      tabIndex={-1}
      aria-labelledby="visitModalLabel"
      aria-hidden="true"
      data-bs-backdrop="static"
    >
      <div className="modal-dialog modal-lg modal-dialog-centered">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title" id="visitModalLabel">
              {editingVisit ? "Edit Visit" : "Add Visit"}
            </h5>
            <button
              type="button"
              className="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
              onClick={handleCancel}
            ></button>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="modal-body">
              <div className="row">
                <div className="col-md-12 mb-3">
                  <label className="form-label">Title <span className="text-danger">*</span></label>
                  <input
                    type="text"
                    className="form-control"
                    name="title"
                    value={formData.title}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="col-md-12 mb-3">
                  <label className="form-label">Description</label>
                  <textarea
                    className="form-control"
                    name="description"
                    value={formData.description}
                    onChange={handleInputChange}
                    rows={3}
                  />
                </div>
                <div className="col-md-6 mb-3">
                  <label className="form-label">Schedule Date <span className="text-danger">*</span></label>
                  <input
                    type="date"
                    className="form-control"
                    name="schedule_date"
                    value={formData.schedule_date}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="col-md-6 mb-3">
                  <label className="form-label">Schedule Time</label>
                  <input
                    type="time"
                    className="form-control"
                    name="schedule_time"
                    value={formData.schedule_time}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="col-md-6 mb-3">
                  <label className="form-label">Assigned Employee <span className="text-danger">*</span></label>
                  <select
                    className="form-select"
                    name="assigned_employee"
                    value={formData.assigned_employee}
                    onChange={handleInputChange}
                    required
                    disabled={loadingEmployees}
                  >
                    <option value="">Select Employee</option>
                    {employees.map((emp) => (
                      <option key={emp.user?.id || emp.id} value={emp.user?.id || emp.id}>
                        {emp.user_name || emp.user?.email || "Unknown"}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-md-6 mb-3">
                  <label className="form-label">Client Name</label>
                  <input
                    type="text"
                    className="form-control"
                    name="client_name"
                    value={formData.client_name}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="col-md-6 mb-3">
                  <label className="form-label">Location Name</label>
                  <input
                    type="text"
                    className="form-control"
                    name="location_name"
                    value={formData.location_name}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="col-md-12 mb-3">
                  <label className="form-label">Address <span className="text-danger">*</span></label>
                  <textarea
                    className="form-control"
                    name="address"
                    value={formData.address}
                    onChange={handleInputChange}
                    rows={2}
                    required
                  />
                </div>
                <div className="col-md-4 mb-3">
                  <label className="form-label">City</label>
                  <input
                    type="text"
                    className="form-control"
                    name="city"
                    value={formData.city}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="col-md-4 mb-3">
                  <label className="form-label">State</label>
                  <input
                    type="text"
                    className="form-control"
                    name="state"
                    value={formData.state}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="col-md-4 mb-3">
                  <label className="form-label">Pincode</label>
                  <input
                    type="text"
                    className="form-control"
                    name="pincode"
                    value={formData.pincode}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="col-md-6 mb-3">
                  <label className="form-label">Country</label>
                  <input
                    type="text"
                    className="form-control"
                    name="country"
                    value={formData.country}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="col-md-6 mb-3">
                  <label className="form-label">Contact Person</label>
                  <input
                    type="text"
                    className="form-control"
                    name="contact_person"
                    value={formData.contact_person}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="col-md-6 mb-3">
                  <label className="form-label">Contact Phone</label>
                  <input
                    type="text"
                    className="form-control"
                    name="contact_phone"
                    value={formData.contact_phone}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="col-md-6 mb-3">
                  <label className="form-label">Contact Email</label>
                  <input
                    type="email"
                    className="form-control"
                    name="contact_email"
                    value={formData.contact_email}
                    onChange={handleInputChange}
                  />
                </div>
              </div>
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
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? "Saving..." : editingVisit ? "Update" : "Create"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default VisitModal;

