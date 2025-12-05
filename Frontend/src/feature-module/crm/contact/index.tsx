import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import CollapseHeader from "../../../core/common/collapse-header/collapse-header";
import { all_routes } from "../../router/all_routes";
import Table from "../../../core/common/dataTable/index";
import ContactModal from "./ContactModal";
import DeleteModal from "./DeleteModal";
import ContactDetailModal from "./ContactDetailModal";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { getAdminIdForApi } from "../../../core/utils/apiHelpers";

const getContactKey = (contact: any) => contact?.id ?? null;

const normalizeContactId = (value: any): string | null => {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  return String(value);
};

const Contacts = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [contactIdToDelete, setContactIdToDelete] = useState<string | null>(null);
  const [editingContact, setEditingContact] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [sourceTypeFilter, setSourceTypeFilter] = useState<string>("");
  const [companyFilter, setCompanyFilter] = useState<string>("");
  const [stateFilter, setStateFilter] = useState<string>("");
  const [cityFilter, setCityFilter] = useState<string>("");
  const [fromDate, setFromDate] = useState<string>("");
  const [toDate, setToDate] = useState<string>("");
  const [stats, setStats] = useState<any>(null);

  // Set default dates to current date on mount
  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    setFromDate(today);
    setToDate(today);
  }, []);

  const fetchContacts = useCallback(async () => {
    setLoading(true);
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = getAdminIdForApi();

      if (!admin_id) {
        const role = sessionStorage.getItem("role");
        if (role === "organization") {
          toast.error("Please select an admin first from the dashboard.");
        } else {
          toast.error("Admin ID not found. Please login again.");
        }
        setLoading(false);
        return;
      }

      const role = sessionStorage.getItem("role");
      const user_id = sessionStorage.getItem("user_id");
      
      // Admin sees all contacts, User sees only their own
      let url = `http://127.0.0.1:8000/api/contact/contact-list-create/${admin_id}`;
      if (role === "user" && user_id) {
        url = `http://127.0.0.1:8000/api/contact/contact-list-create-by-user/${admin_id}/${user_id}`;
      }
      
      const params = new URLSearchParams();
      if (searchQuery) params.append("search", searchQuery);
      if (sourceTypeFilter) params.append("source_type", sourceTypeFilter);
      if (companyFilter) params.append("company", companyFilter);
      if (stateFilter) params.append("state", stateFilter);
      if (cityFilter) params.append("city", cityFilter);
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await axios.get(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      let contacts = [];
      if (response.data && response.data.data) {
        if (response.data.data.results && Array.isArray(response.data.data.results)) {
          contacts = response.data.data.results;
        } else if (Array.isArray(response.data.data)) {
          contacts = response.data.data;
        }
      } else if (Array.isArray(response.data)) {
        contacts = response.data;
      }
      setData(contacts);
    } catch (error: any) {
      console.error("Error fetching contacts:", error);
      toast.error(error.response?.data?.message || "Failed to fetch contacts");
    } finally {
      setLoading(false);
    }
  }, [searchQuery, sourceTypeFilter, companyFilter, stateFilter, cityFilter, fromDate, toDate]);

  const fetchStats = useCallback(async () => {
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = getAdminIdForApi();
      
      if (!admin_id) {
        return;
      }

      const role = sessionStorage.getItem("role");
      const user_id = sessionStorage.getItem("user_id");
      
      // Admin sees all stats, User sees only their own
      let url = `http://127.0.0.1:8000/api/contact/contact-stats/${admin_id}`;
      if (role === "user" && user_id) {
        url = `http://127.0.0.1:8000/api/contact/contact-stats-by-user/${admin_id}/${user_id}`;
      }

      const response = await axios.get(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.data && response.data.data) {
        setStats(response.data.data);
      }
    } catch (error: any) {
      console.error("Error fetching stats:", error);
    }
  }, []);

  useEffect(() => {
    fetchContacts();
    fetchStats();
  }, [fetchContacts, fetchStats]);

  const routes = all_routes;

  const handleContactAdded = () => {
    fetchContacts();
    fetchStats();
  };

  const handleContactUpdated = () => {
    fetchContacts();
    fetchStats();
  };

  const handleDelete = async () => {
    if (!contactIdToDelete) return;

    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = getAdminIdForApi();
      const role = sessionStorage.getItem("role");
      const user_id = sessionStorage.getItem("user_id");

      if (!admin_id) {
        toast.error("Admin ID not found");
        return;
      }

      // For delete, we need both adminId and userId in URL
      // If user role, use user_id, otherwise use empty string or find from contact
      const deleteUserId = role === "user" && user_id ? user_id : "";

      await axios.delete(
        `http://127.0.0.1:8000/api/contact/contact-detail-update-delete/${admin_id}/${deleteUserId}/${contactIdToDelete}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      toast.success("Contact deleted successfully");
      fetchContacts();
      fetchStats();
      setContactIdToDelete(null);
      
      // Close modal
      const modalElement = document.getElementById("deleteContactModal");
      if (modalElement) {
        const modal = (window as any).bootstrap?.Modal?.getInstance(modalElement);
        if (modal) {
          modal.hide();
        }
      }
    } catch (error: any) {
      console.error("Error deleting contact:", error);
      toast.error(error.response?.data?.message || "Failed to delete contact");
    }
  };

  const columns = [
    {
      title: "Name",
      dataIndex: "full_name",
      render: (text: string, record: any) => (
        <h6 className="fw-medium">
          <Link to="#" data-bs-toggle="modal" data-bs-target="#contactDetailModal" onClick={() => setEditingContact(record)}>
            {text || "—"}
          </Link>
        </h6>
      ),
      sorter: (a: any, b: any) => (a.full_name ?? "").localeCompare(b.full_name ?? ""),
    },
    {
      title: "Company",
      dataIndex: "company_name",
      render: (text: string) => <span>{text || "—"}</span>,
      sorter: (a: any, b: any) => (a.company_name ?? "").localeCompare(b.company_name ?? ""),
    },
    {
      title: "Job Title",
      dataIndex: "job_title",
      render: (text: string) => <span>{text || "—"}</span>,
    },
    {
      title: "Email",
      dataIndex: "email_address",
      render: (text: string) => (
        text ? (
          <a href={`mailto:${text}`} className="text-primary">
            {text}
          </a>
        ) : (
          <span>—</span>
        )
      ),
    },
    {
      title: "Mobile",
      dataIndex: "mobile_number",
      render: (text: string) => (
        text ? (
          <a href={`tel:${text}`} className="text-primary">
            {text}
          </a>
        ) : (
          <span>—</span>
        )
      ),
    },
    {
      title: "Location",
      dataIndex: "city",
      render: (_: any, record: any) => (
        <span>
          {[record.city, record.state].filter(Boolean).join(", ") || "—"}
        </span>
      ),
    },
    {
      title: "Source",
      dataIndex: "source_type",
      render: (source: string) => {
        const sourceColors: any = {
          scanned: "badge-success",
          manual: "badge-info",
        };
        const sourceLabels: any = {
          scanned: "Scanned",
          manual: "Manual",
        };
        return (
          <span className={`badge d-inline-flex align-items-center badge-sm ${sourceColors[source] || "badge-secondary"}`}>
            <i className="ti ti-point-filled me-1" />
            {sourceLabels[source] || source}
          </span>
        );
      },
    },
    {
      title: "Created",
      dataIndex: "created_at",
      render: (date: string) => {
        if (!date) return "—";
        return new Date(date).toLocaleDateString();
      },
      sorter: (a: any, b: any) => 
        new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime(),
    },
    {
      title: "Actions",
      dataIndex: "actions",
      render: (_: any, contact: any) => (
        <div className="action-icon d-inline-flex">
          <Link
            to="#"
            className="me-2"
            data-bs-toggle="modal"
            data-bs-target="#contactModal"
            onClick={() => setEditingContact(contact)}
          >
            <i className="ti ti-edit" />
          </Link>
          <Link
            to="#"
            data-bs-toggle="modal"
            data-bs-target="#deleteContactModal"
            onClick={() => setContactIdToDelete(normalizeContactId(getContactKey(contact)))}
          >
            <i className="ti ti-trash" />
          </Link>
        </div>
      ),
    },
  ];

  return (
    <div className="page-wrapper">
      <div className="content">
        <CollapseHeader />
        
        {/* Statistics Cards */}
        {stats && (
          <div className="row mb-4">
            <div className="col-md-3">
              <div className="card">
                <div className="card-body">
                  <h6 className="text-muted mb-2">Total Contacts</h6>
                  <h3 className="mb-0">{stats.total_contacts || 0}</h3>
                </div>
              </div>
            </div>
            <div className="col-md-3">
              <div className="card">
                <div className="card-body">
                  <h6 className="text-muted mb-2">Scanned</h6>
                  <h3 className="mb-0 text-success">{stats.scanned_contacts || 0}</h3>
                </div>
              </div>
            </div>
            <div className="col-md-3">
              <div className="card">
                <div className="card-body">
                  <h6 className="text-muted mb-2">Manual</h6>
                  <h3 className="mb-0 text-info">{stats.manual_contacts || 0}</h3>
                </div>
              </div>
            </div>
            <div className="col-md-3">
              <div className="card">
                <div className="card-body">
                  <h6 className="text-muted mb-2">Companies</h6>
                  <h3 className="mb-0">{stats.unique_companies || 0}</h3>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="card">
          <div className="card-body">
            <div className="row g-3">
              <div className="col-md-3">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Search contacts..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div className="col-md-2">
                <select
                  className="form-select"
                  value={sourceTypeFilter}
                  onChange={(e) => setSourceTypeFilter(e.target.value)}
                >
                  <option value="">All Sources</option>
                  <option value="scanned">Scanned</option>
                  <option value="manual">Manual</option>
                </select>
              </div>
              <div className="col-md-2">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Company"
                  value={companyFilter}
                  onChange={(e) => setCompanyFilter(e.target.value)}
                />
              </div>
              <div className="col-md-2">
                <input
                  type="text"
                  className="form-control"
                  placeholder="State"
                  value={stateFilter}
                  onChange={(e) => setStateFilter(e.target.value)}
                />
              </div>
              <div className="col-md-2">
                <input
                  type="text"
                  className="form-control"
                  placeholder="City"
                  value={cityFilter}
                  onChange={(e) => setCityFilter(e.target.value)}
                />
              </div>
              <div className="col-md-2">
                <input
                  type="date"
                  className="form-control"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                  placeholder="From Date"
                />
              </div>
              <div className="col-md-2">
                <input
                  type="date"
                  className="form-control"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                  placeholder="To Date"
                />
              </div>
              <div className="col-md-1">
                <button
                  className="btn btn-primary w-100"
                  data-bs-toggle="modal"
                  data-bs-target="#contactModal"
                  onClick={() => setEditingContact(null)}
                >
                  <i className="ti ti-plus me-1" />
                  Add
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Contacts Table */}
        <div className="card">
          <div className="card-body">
            {loading ? (
              <div className="text-center p-4">
                <div className="spinner-border" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
              </div>
            ) : (
              <Table
                columns={columns}
                dataSource={data}
                Selection={true}
              />
            )}
          </div>
        </div>

        {/* Modals */}
        {getAdminIdForApi() && (
          <ContactModal
            onContactAdded={handleContactAdded}
            editingContact={editingContact}
            onContactUpdated={handleContactUpdated}
            onEditClose={() => setEditingContact(null)}
            adminId={getAdminIdForApi() || ""}
            userId={sessionStorage.getItem("user_id") || ""}
          />
        )}

        <DeleteModal
          contactId={contactIdToDelete}
          onDelete={handleDelete}
          onClose={() => setContactIdToDelete(null)}
        />

        <ContactDetailModal
          contact={editingContact}
          onClose={() => setEditingContact(null)}
        />

        <ToastContainer />
      </div>
    </div>
  );
};

export default Contacts;

