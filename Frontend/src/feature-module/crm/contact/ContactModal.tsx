import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { toast } from "react-toastify";

interface ContactModalProps {
  onContactAdded: () => void;
  editingContact: any;
  onContactUpdated: () => void;
  onEditClose: () => void;
  adminId: string;
  userId: string;
}

interface ContactFormState {
  full_name: string;
  company_name: string;
  job_title: string;
  department: string;
  mobile_number: string;
  alternate_phone: string;
  office_landline: string;
  fax_number: string;
  email_address: string;
  alternate_email: string;
  full_address: string;
  state: string;
  city: string;
  country: string;
  pincode: string;
  whatsapp_number: string;
  additional_notes: string;
  business_card_image: File | null;
  source_type: "scanned" | "manual";
}

const ContactModal: React.FC<ContactModalProps> = ({
  onContactAdded,
  editingContact,
  onContactUpdated,
  onEditClose,
  adminId,
  userId,
}) => {
  const initialFormState: ContactFormState = {
    full_name: "",
    company_name: "",
    job_title: "",
    department: "",
    mobile_number: "",
    alternate_phone: "",
    office_landline: "",
    fax_number: "",
    email_address: "",
    alternate_email: "",
    full_address: "",
    state: "",
    city: "",
    country: "",
    pincode: "",
    whatsapp_number: "",
    additional_notes: "",
    business_card_image: null,
    source_type: "manual",
  };

  const [formData, setFormData] = useState<ContactFormState>(initialFormState);
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [mode, setMode] = useState<"manual" | "scan">("manual");
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editingContact) {
      setFormData({
        full_name: editingContact.full_name || "",
        company_name: editingContact.company_name || "",
        job_title: editingContact.job_title || "",
        department: editingContact.department || "",
        mobile_number: editingContact.mobile_number || "",
        alternate_phone: editingContact.alternate_phone || "",
        office_landline: editingContact.office_landline || "",
        fax_number: editingContact.fax_number || "",
        email_address: editingContact.email_address || "",
        alternate_email: editingContact.alternate_email || "",
        full_address: editingContact.full_address || "",
        state: editingContact.state || "",
        city: editingContact.city || "",
        country: editingContact.country || "",
        pincode: editingContact.pincode || "",
        whatsapp_number: editingContact.whatsapp_number || "",
        additional_notes: editingContact.additional_notes || "",
        business_card_image: null,
        source_type: editingContact.source_type || "manual",
      });
      if (editingContact.business_card_image_url) {
        setImagePreview(editingContact.business_card_image_url);
      }
      setMode("manual");
    } else {
      setFormData(initialFormState);
      setImagePreview(null);
      setMode("manual");
    }
  }, [editingContact]);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith("image/")) {
        toast.error("Please select an image file");
        return;
      }
      setFormData((prev) => ({ ...prev, business_card_image: file }));
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleExtractFromImage = async () => {
    if (!formData.business_card_image) {
      toast.error("Please upload a business card image first");
      return;
    }

    if (!adminId) {
      toast.error("Admin ID not found");
      return;
    }

    setExtracting(true);
    try {
      const token = sessionStorage.getItem("access_token");
      const formDataToSend = new FormData();
      formDataToSend.append("business_card_image", formData.business_card_image);

      const role = sessionStorage.getItem("role");
      let url = `http://127.0.0.1:8000/api/contact/contact-extract/${adminId}`;
      if (role === "user" && userId) {
        url = `http://127.0.0.1:8000/api/contact/contact-extract-by-user/${adminId}/${userId}`;
      }

      const response = await axios.post(
        url,
        formDataToSend,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "multipart/form-data",
          },
        }
      );

      if (response.data && response.data.data) {
        const extractedData = response.data.data;
        setFormData((prev) => ({
          ...prev,
          ...extractedData,
          source_type: "scanned",
        }));
        toast.success("Contact information extracted successfully! Please review and edit as needed.");
        setMode("manual"); // Switch to manual mode for editing
      }
    } catch (error: any) {
      console.error("Error extracting contact info:", error);
      toast.error(
        error.response?.data?.message ||
          "Failed to extract contact information. You can still enter details manually."
      );
    } finally {
      setExtracting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const role = sessionStorage.getItem("role");
    if (!adminId) {
      toast.error("Admin ID not found");
      setLoading(false);
      return;
    }

    // If user role, userId is required
    if (role === "user" && !userId) {
      toast.error("User ID not found");
      setLoading(false);
      return;
    }

    try {
      const token = sessionStorage.getItem("access_token");
      const formDataToSend = new FormData();

      // Append all form fields
      Object.keys(formData).forEach((key) => {
        const value = formData[key as keyof ContactFormState];
        if (key === "business_card_image") {
          if (value) {
            formDataToSend.append(key, value as File);
          }
        } else if (value !== null && value !== "") {
          formDataToSend.append(key, String(value));
        }
      });

      let response;

      if (editingContact) {
        // Update existing contact
        // For update, we need both adminId and userId in URL
        const updateUserId = userId || editingContact.assigned_user_id || "";
        response = await axios.put(
          `http://127.0.0.1:8000/api/contact/contact-detail-update-delete/${adminId}/${updateUserId}/${editingContact.id}`,
          formDataToSend,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "multipart/form-data",
            },
          }
        );
        toast.success(response.data.message || "Contact updated successfully!");
        onContactUpdated();
      } else {
        // Create new contact
        // Admin creates without user_id in URL, User creates with both admin_id and user_id
        let url = `http://127.0.0.1:8000/api/contact/contact-list-create/${adminId}`;
        if (role === "user" && userId) {
          url = `http://127.0.0.1:8000/api/contact/contact-list-create-by-user/${adminId}/${userId}`;
        }
        
        response = await axios.post(
          url,
          formDataToSend,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "multipart/form-data",
            },
          }
        );
        toast.success(response.data.message || "Contact created successfully!");
        onContactAdded();
      }

      // Reset form
      setFormData(initialFormState);
      setImagePreview(null);
      setMode("manual");

      // Close modal
      const modalElement = document.getElementById("contactModal");
      if (modalElement) {
        const modal = (window as any).bootstrap?.Modal?.getInstance(modalElement);
        if (modal) {
          modal.hide();
        }
      }
    } catch (error: any) {
      console.error("Error saving contact:", error);
      toast.error(
        error.response?.data?.message ||
          error.response?.data?.data ||
          `Failed to ${editingContact ? "update" : "create"} contact`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setFormData(initialFormState);
    setImagePreview(null);
    setMode("manual");
    onEditClose();
  };

  return (
    <div
      className="modal fade"
      id="contactModal"
      tabIndex={-1}
      aria-labelledby="contactModalLabel"
      aria-hidden="true"
    >
      <div className="modal-dialog modal-xl">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title" id="contactModalLabel">
              {editingContact ? "Edit Contact" : "Add New Contact"}
            </h5>
            <button
              type="button"
              className="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
              onClick={handleCancel}
            />
          </div>
          <form onSubmit={handleSubmit}>
            <div className="modal-body">
              {/* Mode Selection */}
              {!editingContact && (
                <div className="row mb-3">
                  <div className="col-12">
                    <div className="btn-group w-100" role="group">
                      <button
                        type="button"
                        className={`btn ${mode === "scan" ? "btn-primary" : "btn-outline-primary"}`}
                        onClick={() => setMode("scan")}
                      >
                        <i className="ti ti-scan me-1" />
                        Scan Business Card
                      </button>
                      <button
                        type="button"
                        className={`btn ${mode === "manual" ? "btn-primary" : "btn-outline-primary"}`}
                        onClick={() => setMode("manual")}
                      >
                        <i className="ti ti-edit me-1" />
                        Manual Entry
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Scan Mode */}
              {mode === "scan" && !editingContact && (
                <div className="row mb-4">
                  <div className="col-12">
                    <div className="card border-primary">
                      <div className="card-body">
                        <h6 className="card-title mb-3">
                          <i className="ti ti-scan me-2" />
                          Upload Business Card
                        </h6>
                        <div className="mb-3">
                          <input
                            ref={fileInputRef}
                            type="file"
                            className="form-control"
                            accept="image/*"
                            onChange={handleImageChange}
                          />
                          <small className="text-muted">
                            Supported formats: JPG, PNG, GIF. Maximum size: 10MB
                          </small>
                        </div>
                        {imagePreview && (
                          <div className="mb-3">
                            <img
                              src={imagePreview}
                              alt="Business card preview"
                              className="img-thumbnail"
                              style={{ maxHeight: "200px" }}
                            />
                          </div>
                        )}
                        <button
                          type="button"
                          className="btn btn-primary"
                          onClick={handleExtractFromImage}
                          disabled={!formData.business_card_image || extracting}
                        >
                          {extracting ? (
                            <>
                              <span className="spinner-border spinner-border-sm me-2" />
                              Extracting...
                            </>
                          ) : (
                            <>
                              <i className="ti ti-scan me-1" />
                              Extract Contact Information
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Manual Entry Form */}
              <div className="row">
                <div className="col-md-6">
                  <h6 className="mb-3">Basic Information</h6>
                  <div className="mb-3">
                    <label className="form-label">Full Name *</label>
                    <input
                      type="text"
                      className="form-control"
                      name="full_name"
                      value={formData.full_name}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Company Name</label>
                    <input
                      type="text"
                      className="form-control"
                      name="company_name"
                      value={formData.company_name}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Job Title</label>
                    <input
                      type="text"
                      className="form-control"
                      name="job_title"
                      value={formData.job_title}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Department</label>
                    <input
                      type="text"
                      className="form-control"
                      name="department"
                      value={formData.department}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>

                <div className="col-md-6">
                  <h6 className="mb-3">Contact Information</h6>
                  <div className="mb-3">
                    <label className="form-label">Mobile Number</label>
                    <input
                      type="tel"
                      className="form-control"
                      name="mobile_number"
                      value={formData.mobile_number}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Alternate Phone</label>
                    <input
                      type="tel"
                      className="form-control"
                      name="alternate_phone"
                      value={formData.alternate_phone}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Office Landline</label>
                    <input
                      type="tel"
                      className="form-control"
                      name="office_landline"
                      value={formData.office_landline}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Fax Number</label>
                    <input
                      type="tel"
                      className="form-control"
                      name="fax_number"
                      value={formData.fax_number}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>
              </div>

              <div className="row">
                <div className="col-md-6">
                  <h6 className="mb-3">Email Information</h6>
                  <div className="mb-3">
                    <label className="form-label">Email Address</label>
                    <input
                      type="email"
                      className="form-control"
                      name="email_address"
                      value={formData.email_address}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Alternate Email</label>
                    <input
                      type="email"
                      className="form-control"
                      name="alternate_email"
                      value={formData.alternate_email}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>

                <div className="col-md-6">
                  <h6 className="mb-3">Address Information</h6>
                  <div className="mb-3">
                    <label className="form-label">Full Address</label>
                    <textarea
                      className="form-control"
                      name="full_address"
                      rows={3}
                      value={formData.full_address}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="row">
                    <div className="col-md-6 mb-3">
                      <label className="form-label">City</label>
                      <input
                        type="text"
                        className="form-control"
                        name="city"
                        value={formData.city}
                        onChange={handleInputChange}
                      />
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label">State</label>
                      <input
                        type="text"
                        className="form-control"
                        name="state"
                        value={formData.state}
                        onChange={handleInputChange}
                      />
                    </div>
                  </div>
                  <div className="row">
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
                      <label className="form-label">Pincode</label>
                      <input
                        type="text"
                        className="form-control"
                        name="pincode"
                        value={formData.pincode}
                        onChange={handleInputChange}
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="row">
                <div className="col-md-6">
                  <h6 className="mb-3">Social Links</h6>
                  <div className="mb-3">
                    <label className="form-label">WhatsApp Number</label>
                    <input
                      type="tel"
                      className="form-control"
                      name="whatsapp_number"
                      value={formData.whatsapp_number}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>

                <div className="col-md-6">
                  <h6 className="mb-3">Additional Information</h6>
                  <div className="mb-3">
                    <label className="form-label">Additional Notes</label>
                    <textarea
                      className="form-control"
                      name="additional_notes"
                      rows={5}
                      value={formData.additional_notes}
                      onChange={handleInputChange}
                    />
                  </div>
                  {mode === "manual" && !editingContact && (
                    <div className="mb-3">
                      <label className="form-label">Business Card Image (Optional)</label>
                      <input
                        type="file"
                        className="form-control"
                        accept="image/*"
                        onChange={handleImageChange}
                      />
                      {imagePreview && (
                        <img
                          src={imagePreview}
                          alt="Preview"
                          className="img-thumbnail mt-2"
                          style={{ maxHeight: "150px" }}
                        />
                      )}
                    </div>
                  )}
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
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" />
                    Saving...
                  </>
                ) : (
                  <>
                    <i className="ti ti-check me-1" />
                    {editingContact ? "Update" : "Save"} Contact
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ContactModal;

