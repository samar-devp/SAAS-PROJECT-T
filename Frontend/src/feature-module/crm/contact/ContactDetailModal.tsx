import React from "react";

interface ContactDetailModalProps {
  contact: any;
  onClose: () => void;
}

const ContactDetailModal: React.FC<ContactDetailModalProps> = ({ contact, onClose }) => {
  if (!contact) return null;

  return (
    <div
      className="modal fade"
      id="contactDetailModal"
      tabIndex={-1}
      aria-labelledby="contactDetailModalLabel"
      aria-hidden="true"
    >
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title" id="contactDetailModalLabel">
              Contact Details
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
            <div className="row">
              <div className="col-md-6">
                <h6 className="mb-3">Basic Information</h6>
                <table className="table table-borderless">
                  <tbody>
                    <tr>
                      <td className="fw-medium" style={{ width: "40%" }}>Full Name:</td>
                      <td>{contact.full_name || "—"}</td>
                    </tr>
                    <tr>
                      <td className="fw-medium">Company:</td>
                      <td>{contact.company_name || "—"}</td>
                    </tr>
                    <tr>
                      <td className="fw-medium">Job Title:</td>
                      <td>{contact.job_title || "—"}</td>
                    </tr>
                    <tr>
                      <td className="fw-medium">Department:</td>
                      <td>{contact.department || "—"}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div className="col-md-6">
                <h6 className="mb-3">Contact Information</h6>
                <table className="table table-borderless">
                  <tbody>
                    <tr>
                      <td className="fw-medium" style={{ width: "40%" }}>Mobile:</td>
                      <td>
                        {contact.mobile_number ? (
                          <a href={`tel:${contact.mobile_number}`}>{contact.mobile_number}</a>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                    <tr>
                      <td className="fw-medium">Alternate Phone:</td>
                      <td>
                        {contact.alternate_phone ? (
                          <a href={`tel:${contact.alternate_phone}`}>{contact.alternate_phone}</a>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                    <tr>
                      <td className="fw-medium">Office Landline:</td>
                      <td>
                        {contact.office_landline ? (
                          <a href={`tel:${contact.office_landline}`}>{contact.office_landline}</a>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                    <tr>
                      <td className="fw-medium">Fax:</td>
                      <td>{contact.fax_number || "—"}</td>
                    </tr>
                    <tr>
                      <td className="fw-medium">Email:</td>
                      <td>
                        {contact.email_address ? (
                          <a href={`mailto:${contact.email_address}`}>{contact.email_address}</a>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                    <tr>
                      <td className="fw-medium">Alternate Email:</td>
                      <td>
                        {contact.alternate_email ? (
                          <a href={`mailto:${contact.alternate_email}`}>{contact.alternate_email}</a>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div className="row mt-3">
              <div className="col-md-6">
                <h6 className="mb-3">Address Information</h6>
                <table className="table table-borderless">
                  <tbody>
                    <tr>
                      <td className="fw-medium" style={{ width: "40%" }}>Address:</td>
                      <td>{contact.full_address || "—"}</td>
                    </tr>
                    <tr>
                      <td className="fw-medium">City:</td>
                      <td>{contact.city || "—"}</td>
                    </tr>
                    <tr>
                      <td className="fw-medium">State:</td>
                      <td>{contact.state || "—"}</td>
                    </tr>
                    <tr>
                      <td className="fw-medium">Country:</td>
                      <td>{contact.country || "—"}</td>
                    </tr>
                    <tr>
                      <td className="fw-medium">Pincode:</td>
                      <td>{contact.pincode || "—"}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div className="col-md-6">
                <h6 className="mb-3">Social Links</h6>
                <table className="table table-borderless">
                  <tbody>
                    <tr>
                      <td className="fw-medium">WhatsApp:</td>
                      <td>
                        {contact.whatsapp_number ? (
                          <a href={`https://wa.me/${contact.whatsapp_number.replace(/\D/g, '')}`} target="_blank" rel="noopener noreferrer">
                            {contact.whatsapp_number}
                          </a>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {contact.additional_notes && (
              <div className="row mt-3">
                <div className="col-12">
                  <h6 className="mb-3">Additional Notes</h6>
                  <p className="text-muted">{contact.additional_notes}</p>
                </div>
              </div>
            )}

            {contact.business_card_image_url && (
              <div className="row mt-3">
                <div className="col-12">
                  <h6 className="mb-3">Business Card</h6>
                  <img
                    src={contact.business_card_image_url}
                    alt="Business card"
                    className="img-thumbnail"
                    style={{ maxHeight: "300px" }}
                  />
                </div>
              </div>
            )}

            <div className="row mt-3">
              <div className="col-12">
                <small className="text-muted">
                  Created: {contact.created_at ? new Date(contact.created_at).toLocaleString() : "—"} | 
                  Source: <span className={`badge ${contact.source_type === 'scanned' ? 'badge-success' : 'badge-info'}`}>
                    {contact.source_type === 'scanned' ? 'Scanned' : 'Manual'}
                  </span>
                </small>
              </div>
            </div>
          </div>
          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              data-bs-dismiss="modal"
              onClick={onClose}
            >
              Close
            </button>
            <button
              type="button"
              className="btn btn-primary"
              data-bs-dismiss="modal"
              data-bs-toggle="modal"
              data-bs-target="#contactModal"
              onClick={() => {
                onClose();
                // The parent component should handle setting editingContact
              }}
            >
              <i className="ti ti-edit me-1" />
              Edit
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContactDetailModal;

