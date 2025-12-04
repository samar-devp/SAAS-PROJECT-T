import React, { useState, useEffect } from "react";
import axios from "axios";
import { BACKEND_PATH } from "../../../environment";
import { Table } from "antd";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import CollapseHeader from "../../../core/common/collapse-header/collapse-header";
import { Link } from "react-router-dom";
import { all_routes } from "../../router/all_routes";

interface Admin {
  id: string;
  admin_name: string;
  user_id?: string; // From new API structure
  email?: string; // From new API structure
  username?: string; // From new API structure
  phone_number?: string; // From new API structure
  status?: boolean; // From new API structure
  is_active?: boolean; // From new API structure
  user?: { // For backward compatibility with nested structure
    id: string;
    email: string;
    username: string;
    phone_number: string;
    is_active: boolean;
  };
  organization: string;
  created_at: string;
  updated_at?: string;
}

interface AdminListResponse {
  results: Admin[];
  count: number;
  next: string | null;
  previous: string | null;
  summary: {
    total: number;
    active: number;
    inactive: number;
  };
}

const OrganizationDashboard = () => {
  const routes = all_routes;
  const [admins, setAdmins] = useState<Admin[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAdmin, setSelectedAdmin] = useState<Admin | null>(null);
  const [showAdminDetails, setShowAdminDetails] = useState(false);
  const [selectedAdminForDashboard, setSelectedAdminForDashboard] = useState<Admin | null>(null);
  const [summary, setSummary] = useState({
    total: 0,
    active: 0,
    inactive: 0,
  });
  const [searchQuery, setSearchQuery] = useState("");
  const [showAddAdminModal, setShowAddAdminModal] = useState(false);
  const [isCreatingAdmin, setIsCreatingAdmin] = useState(false);
  const [updatingAdminId, setUpdatingAdminId] = useState<string | null>(null);
  const [showEditAdminModal, setShowEditAdminModal] = useState(false);
  const [isUpdatingAdmin, setIsUpdatingAdmin] = useState(false);
  const [editingAdmin, setEditingAdmin] = useState<Admin | null>(null);
  const [addAdminForm, setAddAdminForm] = useState({
    admin_name: "",
    email: "",
    username: "",
    password: "",
    phone_number: "",
  });
  const [editAdminForm, setEditAdminForm] = useState({
    admin_name: "",
    email: "",
    username: "",
    phone_number: "",
    is_active: true,
  });

  useEffect(() => {
    fetchAdmins();
    // Load selected admin from sessionStorage on mount
    const savedAdminId = sessionStorage.getItem("selected_admin_id");
    if (savedAdminId) {
      // Admin will be loaded after admins list is fetched
    }
  }, [searchQuery]);

  useEffect(() => {
    // When admins are loaded, check if we have a saved admin selection
    if (admins.length > 0 && !selectedAdminForDashboard) {
      const savedAdminId = sessionStorage.getItem("selected_admin_id");
      if (savedAdminId) {
        const admin = admins.find(a => (a.user?.id || a.user_id) === savedAdminId);
        if (admin) {
          setSelectedAdminForDashboard(admin);
          return;
        }
      }
      // Auto-select first admin if none selected
      setSelectedAdminForDashboard(admins[0]);
      const firstAdminUserId = admins[0].user?.id || admins[0].user_id;
      if (firstAdminUserId) {
        sessionStorage.setItem("selected_admin_id", firstAdminUserId);
      }
    }
  }, [admins, selectedAdminForDashboard]);

  const getAuthHeaders = () => {
    const token = sessionStorage.getItem("access_token");
    return {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    };
  };

  const fetchAdmins = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (searchQuery) {
        params.q = searchQuery;
      }
      const response = await axios.get<{ status: number; message: string; data: AdminListResponse }>(
        `${BACKEND_PATH}organization/admins`,
        {
          ...getAuthHeaders(),
          params,
        }
      );
      
      if (response.data.status === 200 && response.data.data) {
        // Handle paginated response structure
        const data = response.data.data;
        let adminsList: Admin[] = [];
        
        // Check if data is already an array
        if (Array.isArray(data)) {
          adminsList = data;
        } 
        // Check if data has results property (paginated response)
        else if (data && typeof data === 'object' && data.results && Array.isArray(data.results)) {
          // Map flat API response to nested structure for backward compatibility
          adminsList = data.results.map((admin: any) => ({
            ...admin,
            user: admin.user || {
              id: admin.user_id || admin.id,
              email: admin.email || '',
              username: admin.username || '',
              phone_number: admin.phone_number || '',
              is_active: admin.is_active ?? admin.status ?? true,
            },
            is_active: admin.is_active ?? admin.status ?? true,
            status: admin.status ?? admin.is_active ?? true,
          }));
        }
        // Fallback to empty array if structure is unexpected
        else {
          console.warn("Unexpected data structure:", data);
          adminsList = [];
        }
        
        // Show all admins (both active and inactive)
        setAdmins(adminsList);
        
        // Set summary if available
        if (data && typeof data === 'object' && data.summary) {
          setSummary(data.summary);
        }
      } else {
        setAdmins([]);
      }
    } catch (error: any) {
      console.error("Error fetching admins:", error);
      toast.error(error.response?.data?.message || "Failed to fetch admins");
      setAdmins([]); // Ensure admins is always an array even on error
    } finally {
      setLoading(false);
    }
  };

  const fetchAdminDetails = async (adminId: string) => {
    try {
      const response = await axios.get<{ status: number; message: string; data: Admin }>(
        `${BACKEND_PATH}admin/${adminId}`,
        getAuthHeaders()
      );
      
      if (response.data.status === 200 && response.data.data) {
        setSelectedAdmin(response.data.data);
        setShowAdminDetails(true);
      }
    } catch (error: any) {
      console.error("Error fetching admin details:", error);
      toast.error(error.response?.data?.message || "Failed to fetch admin details");
    }
  };

  const handleAdminClick = (admin: Admin) => {
    fetchAdminDetails(admin.id);
  };

  const handleAdminSelectionChange = (adminId: string) => {
    const admin = admins.find(a => a.id === adminId);
    if (admin) {
      setSelectedAdminForDashboard(admin);
      // Store admin's user ID (UID) in sessionStorage for API calls
      const userId = admin.user?.id || admin.user_id;
      if (userId) {
        sessionStorage.setItem("selected_admin_id", userId);
        toast.success(`Switched to admin: ${admin.admin_name}`);
      }
    }
  };

  const handleAddAdmin = async () => {
    // Validate form
    if (!addAdminForm.admin_name || !addAdminForm.email || !addAdminForm.username || !addAdminForm.password || !addAdminForm.phone_number) {
      toast.error("Please fill all required fields");
      return;
    }

    setIsCreatingAdmin(true);
    try {
      const token = sessionStorage.getItem("access_token");
      if (!token) {
        toast.error("Please login again");
        setIsCreatingAdmin(false);
        return;
      }

      const response = await axios.post(
        `${BACKEND_PATH}register/admin`,
        {
          admin_name: addAdminForm.admin_name,
          user: {
            email: addAdminForm.email,
            username: addAdminForm.username,
            password: addAdminForm.password,
            phone_number: addAdminForm.phone_number,
            role: "admin",
          },
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      toast.success("Admin created successfully");
      setShowAddAdminModal(false);
      setAddAdminForm({
        admin_name: "",
        email: "",
        username: "",
        password: "",
        phone_number: "",
      });
      fetchAdmins(); // Refresh admins list
    } catch (error: any) {
      console.error("Error creating admin:", error);
      
      // Helper function to extract all error messages from nested structure
      const extractErrorMessages = (errorObj: any, fieldMap: { [key: string]: string } = {}): string[] => {
        const messages: string[] = [];
        
        if (typeof errorObj === 'string') {
          messages.push(errorObj);
        } else if (Array.isArray(errorObj)) {
          errorObj.forEach((item: any) => {
            messages.push(...extractErrorMessages(item, fieldMap));
          });
        } else if (typeof errorObj === 'object' && errorObj !== null) {
          Object.entries(errorObj).forEach(([key, value]: [string, any]) => {
            // Map field names to user-friendly labels
            const fieldLabel = fieldMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
            
            if (Array.isArray(value)) {
              value.forEach((msg: any) => {
                if (typeof msg === 'string') {
                  // Clean up common error messages
                  let cleanMsg = msg;
                  if (msg.includes('already exists')) {
                    cleanMsg = msg.replace(/base user model with this /gi, '').replace(/^[a-z]/, (l: string) => l.toUpperCase());
                  }
                  messages.push(`${fieldLabel}: ${cleanMsg}`);
                } else {
                  messages.push(...extractErrorMessages(msg, fieldMap));
                }
              });
            } else if (typeof value === 'object' && value !== null) {
              // Handle nested objects (like user.email)
              messages.push(...extractErrorMessages(value, fieldMap));
            } else if (value) {
              messages.push(`${fieldLabel}: ${value}`);
            }
          });
        }
        
        return messages;
      };
      
      let errorMessages: string[] = [];
      
      if (error.response?.data) {
        const errorData = error.response.data;
        
        // Field name mapping for better readability
        const fieldMap: { [key: string]: string } = {
          'email': 'Email',
          'username': 'Username',
          'phone_number': 'Phone number',
          'admin_name': 'Admin name',
          'password': 'Password',
          'user': 'User'
        };
        
        // Check for errors object with nested structure
        if (errorData.errors) {
          const errorsObj = errorData.errors;
          // Handle nested user object specially
          if (errorsObj.user && typeof errorsObj.user === 'object') {
            // Extract user field errors directly
            Object.entries(errorsObj.user).forEach(([field, messages]: [string, any]) => {
              if (Array.isArray(messages)) {
                messages.forEach((msg: string) => {
                  const fieldLabel = fieldMap[field] || field.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase());
                  let cleanMsg = msg;
                  if (msg.includes('already exists')) {
                    cleanMsg = msg.replace(/base user model with this /gi, '').replace(/^[a-z]/, (l: string) => l.toUpperCase());
                  }
                  errorMessages.push(`${fieldLabel}: ${cleanMsg}`);
                });
              }
            });
          }
          
          // Handle other top-level errors (like admin_name)
          Object.entries(errorsObj).forEach(([key, value]: [string, any]) => {
            if (key !== 'user' && Array.isArray(value)) {
              const fieldLabel = fieldMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase());
              value.forEach((msg: string) => {
                errorMessages.push(`${fieldLabel}: ${msg}`);
              });
            }
          });
          
          // If no messages extracted yet, fall back to full extraction
          if (errorMessages.length === 0) {
            errorMessages = extractErrorMessages(errorData.errors, fieldMap);
          }
        }
        // Check for nested user errors
        else if (errorData.user) {
          errorMessages = extractErrorMessages(errorData.user, fieldMap);
        }
        // Check for message
        else if (errorData.message) {
          errorMessages = [errorData.message];
        }
        // Check for detail (DRF default)
        else if (errorData.detail) {
          errorMessages = [errorData.detail];
        }
        // Fallback to extracting all error data
        else {
          errorMessages = extractErrorMessages(errorData, fieldMap);
        }
      } else if (error.message) {
        errorMessages = [error.message];
      }
      
      // Format error messages
      let finalMessage = errorMessages.length > 0 
        ? errorMessages.join('. ')
        : "Failed to create admin. Please check the form and try again.";
      
      // Clean up redundant prefixes and improve formatting
      finalMessage = finalMessage
        .replace(/^User: /gi, '')
        .replace(/User\./gi, '')
        .replace(/\b([A-Z][a-z]+): \1:/gi, '$1:')  // Remove duplicate field names
        .trim();
      
      toast.error(finalMessage);
    } finally {
      setIsCreatingAdmin(false);
    }
  };

  const handleCloseAddAdminModal = () => {
    setShowAddAdminModal(false);
    setAddAdminForm({
      admin_name: "",
      email: "",
      username: "",
      password: "",
      phone_number: "",
    });
  };

  const handleEditAdmin = (admin: Admin) => {
    setEditingAdmin(admin);
    const currentStatus = admin.is_active !== undefined ? admin.is_active : 
                         (admin.status !== undefined ? admin.status : 
                          admin.user?.is_active !== undefined ? admin.user.is_active : true);
    setEditAdminForm({
      admin_name: admin.admin_name || "",
      email: admin.user?.email || "",
      username: admin.user?.username || "",
      phone_number: admin.user?.phone_number || "",
      is_active: currentStatus,
    });
    setShowEditAdminModal(true);
  };

  const handleCloseEditAdminModal = () => {
    setShowEditAdminModal(false);
    setEditingAdmin(null);
    setEditAdminForm({
      admin_name: "",
      email: "",
      username: "",
      phone_number: "",
      is_active: true,
    });
  };

  const handleUpdateAdmin = async () => {
    if (!editingAdmin) return;

    // Validate form
    if (!editAdminForm.admin_name || !editAdminForm.email || !editAdminForm.username || !editAdminForm.phone_number) {
      toast.error("Please fill all required fields");
      return;
    }

    setIsUpdatingAdmin(true);
    try {
      const token = sessionStorage.getItem("access_token");
      if (!token) {
        toast.error("Please login again");
        setIsUpdatingAdmin(false);
        return;
      }

      const response = await axios.put(
        `${BACKEND_PATH}organization/admins/${editingAdmin.id}`,
        {
          admin_name: editAdminForm.admin_name,
          is_active: editAdminForm.is_active,
          user: {
            email: editAdminForm.email,
            username: editAdminForm.username,
            phone_number: editAdminForm.phone_number,
          },
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.data?.status === 200) {
        toast.success("Admin updated successfully");
        setShowEditAdminModal(false);
        setEditingAdmin(null);
        fetchAdmins(); // Refresh admins list
      } else {
        toast.error(response.data?.message || "Failed to update admin");
      }
    } catch (error: any) {
      console.error("Error updating admin:", error);
      
      // Helper function to extract error messages
      const extractErrorMessages = (errorObj: any, fieldMap: { [key: string]: string } = {}): string[] => {
        const messages: string[] = [];
        
        if (typeof errorObj === 'string') {
          messages.push(errorObj);
        } else if (Array.isArray(errorObj)) {
          errorObj.forEach((item: any) => {
            messages.push(...extractErrorMessages(item, fieldMap));
          });
        } else if (typeof errorObj === 'object' && errorObj !== null) {
          Object.entries(errorObj).forEach(([key, value]: [string, any]) => {
            const fieldLabel = fieldMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase());
            
            if (Array.isArray(value)) {
              value.forEach((msg: any) => {
                if (typeof msg === 'string') {
                  let cleanMsg = msg;
                  if (msg.includes('already exists')) {
                    cleanMsg = msg.replace(/base user model with this /gi, '').replace(/^[a-z]/, (l: string) => l.toUpperCase());
                  }
                  messages.push(`${fieldLabel}: ${cleanMsg}`);
                } else {
                  messages.push(...extractErrorMessages(msg, fieldMap));
                }
              });
            } else if (typeof value === 'object' && value !== null) {
              messages.push(...extractErrorMessages(value, fieldMap));
            } else if (value) {
              messages.push(`${fieldLabel}: ${value}`);
            }
          });
        }
        
        return messages;
      };
      
      let errorMessages: string[] = [];
      
      if (error.response?.data) {
        const errorData = error.response.data;
        const fieldMap: { [key: string]: string } = {
          'email': 'Email',
          'username': 'Username',
          'phone_number': 'Phone number',
          'admin_name': 'Admin name',
        };
        
        if (errorData.errors) {
          const errorsObj = errorData.errors;
          if (errorsObj.user && typeof errorsObj.user === 'object') {
            Object.entries(errorsObj.user).forEach(([field, messages]: [string, any]) => {
              if (Array.isArray(messages)) {
                messages.forEach((msg: string) => {
                  const fieldLabel = fieldMap[field] || field.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase());
                  let cleanMsg = msg;
                  if (msg.includes('already exists')) {
                    cleanMsg = msg.replace(/base user model with this /gi, '').replace(/^[a-z]/, (l: string) => l.toUpperCase());
                  }
                  errorMessages.push(`${fieldLabel}: ${cleanMsg}`);
                });
              }
            });
          }
          
          Object.entries(errorsObj).forEach(([key, value]: [string, any]) => {
            if (key !== 'user' && Array.isArray(value)) {
              const fieldLabel = fieldMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase());
              value.forEach((msg: string) => {
                errorMessages.push(`${fieldLabel}: ${msg}`);
              });
            }
          });
          
          if (errorMessages.length === 0) {
            errorMessages = extractErrorMessages(errorData.errors, fieldMap);
          }
        } else if (errorData.message) {
          errorMessages = [errorData.message];
        } else if (errorData.detail) {
          errorMessages = [errorData.detail];
        }
      } else if (error.message) {
        errorMessages = [error.message];
      }
      
      let finalMessage = errorMessages.length > 0 
        ? errorMessages.join('. ')
        : "Failed to update admin. Please check the form and try again.";
      
      finalMessage = finalMessage
        .replace(/^User: /gi, '')
        .replace(/User\./gi, '')
        .replace(/\b([A-Z][a-z]+): \1:/gi, '$1:')
        .trim();
      
      toast.error(finalMessage);
    } finally {
      setIsUpdatingAdmin(false);
    }
  };

  const handleToggleAdminStatus = async (admin: Admin) => {
    const currentStatus = admin.is_active !== undefined ? admin.is_active : (admin.status !== undefined ? admin.status : admin.user?.is_active);
    const newStatus = !currentStatus;
    
    setUpdatingAdminId(admin.id);
    try {
      const token = sessionStorage.getItem("access_token");
      if (!token) {
        toast.error("Please login again");
        setUpdatingAdminId(null);
        return;
      }

      const response = await axios.put(
        `${BACKEND_PATH}admin/${admin.id}`,
        {
          is_active: newStatus,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.data?.status === 200) {
        toast.success(`Admin ${newStatus ? 'activated' : 'deactivated'} successfully`);
        fetchAdmins(); // Refresh admins list
      } else {
        toast.error(response.data?.message || "Failed to update admin status");
      }
    } catch (error: any) {
      console.error("Error updating admin status:", error);
      
      // Helper function to extract error messages
      const extractErrorMessage = (errorObj: any): string => {
        if (typeof errorObj === 'string') return errorObj;
        if (Array.isArray(errorObj)) {
          return errorObj.map(extractErrorMessage).join(', ');
        }
        if (typeof errorObj === 'object' && errorObj !== null) {
          return Object.entries(errorObj)
            .map(([key, value]: [string, any]) => {
              if (Array.isArray(value)) {
                return `${key}: ${value.map((v: any) => extractErrorMessage(v)).join(', ')}`;
              } else if (typeof value === 'object' && value !== null) {
                return `${key}: ${extractErrorMessage(value)}`;
              }
              return `${key}: ${value}`;
            })
            .join('; ');
        }
        return String(errorObj);
      };
      
      let errorMessage = "Failed to update admin status";
      
      if (error.response?.data) {
        const errorData = error.response.data;
        if (errorData.message) {
          errorMessage = errorData.message;
        } else if (errorData.errors) {
          errorMessage = extractErrorMessage(errorData.errors);
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else {
          errorMessage = extractErrorMessage(errorData);
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast.error(errorMessage);
    } finally {
      setUpdatingAdminId(null);
    }
  };

  const columns = [
    {
      title: "Admin Name",
      dataIndex: "admin_name",
      key: "admin_name",
      sorter: (a: Admin, b: Admin) => (a.admin_name || "").localeCompare(b.admin_name || ""),
      render: (text: string, record: Admin) => (
        <div className="d-flex align-items-center">
          <div className="avatar avatar-sm bg-primary rounded-circle me-2 d-flex align-items-center justify-content-center" style={{ width: '32px', height: '32px' }}>
            <span className="text-white fw-bold small">
              {text?.charAt(0)?.toUpperCase() || "A"}
            </span>
          </div>
          <Link
            to="#"
            onClick={(e) => {
              e.preventDefault();
              handleAdminClick(record);
            }}
            className="text-primary fw-semibold text-decoration-none"
          >
            {text}
          </Link>
        </div>
      ),
    },
    {
      title: "Email",
      dataIndex: ["user", "email"],
      key: "email",
      sorter: (a: Admin, b: Admin) => ((a.user?.email || "") > (b.user?.email || "") ? 1 : -1),
      render: (email: string) => (
        <span className="text-dark">
          <i className="ti ti-mail me-1 text-muted" />
          {email || "-"}
        </span>
      ),
    },
    {
      title: "Username",
      dataIndex: ["user", "username"],
      key: "username",
      sorter: (a: Admin, b: Admin) => ((a.user?.username || "") > (b.user?.username || "") ? 1 : -1),
      render: (username: string) => (
        <span className="text-dark">
          <i className="ti ti-user me-1 text-muted" />
          {username || "-"}
        </span>
      ),
    },
    {
      title: "Phone Number",
      dataIndex: ["user", "phone_number"],
      key: "phone_number",
      render: (phone: string) => (
        <span className="text-dark">
          <i className="ti ti-phone me-1 text-muted" />
          {phone || "-"}
        </span>
      ),
    },
    {
      title: "Status",
      dataIndex: "is_active",
      key: "status",
      render: (isActive: any, record: Admin) => {
        const currentStatus = record.is_active !== undefined ? record.is_active : (record.status !== undefined ? record.status : record.user?.is_active);
        const isUpdating = updatingAdminId === record.id;
        
        return (
          <div className="d-flex align-items-center gap-3">
            <span
              className={`badge ${
                currentStatus ? "badge-success" : "badge-danger"
              } d-inline-flex align-items-center badge-xs`}
            >
              <i className="ti ti-point-filled me-1" />
              {currentStatus ? "Active" : "Inactive"}
            </span>
            <label className="form-check form-switch form-switch-md mb-0">
              <input
                className={`form-check-input ${currentStatus ? 'status-active' : 'status-inactive'}`}
                type="checkbox"
                checked={currentStatus}
                onChange={() => handleToggleAdminStatus(record)}
                disabled={isUpdating}
                style={{ 
                  width: '48px',
                  height: '24px',
                  cursor: isUpdating ? 'not-allowed' : 'pointer'
                }}
              />
              {isUpdating && (
                <span className="spinner-border spinner-border-sm ms-2" style={{ width: '16px', height: '16px' }} />
              )}
            </label>
            <style>{`
              .form-check-input.status-active:checked {
                background-color: #28a745 !important;
                border-color: #28a745 !important;
              }
              .form-check-input.status-inactive:not(:checked) {
                background-color: #dc3545 !important;
                border-color: #dc3545 !important;
              }
              .form-check-input.status-active:checked:focus {
                box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25) !important;
              }
              .form-check-input.status-inactive:not(:checked):focus {
                box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25) !important;
              }
            `}</style>
          </div>
        );
      },
    },
    {
      title: "Created At",
      dataIndex: "created_at",
      key: "created_at",
      sorter: (a: Admin, b: Admin) => {
        const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
        const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
        return dateA - dateB;
      },
      render: (date: string) => {
        if (!date) return <span className="text-muted">-</span>;
        const d = new Date(date);
        return (
          <div>
            <div className="fw-medium">{d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}</div>
            <small className="text-muted">{d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}</small>
          </div>
        );
      },
    },
    {
      title: "Actions",
      key: "actions",
      render: (_: any, record: Admin) => (
        <div className="d-flex align-items-center gap-2">
          <button
            className="btn btn-sm btn-outline-primary d-flex align-items-center"
            onClick={() => handleEditAdmin(record)}
            title="Edit Admin"
          >
            <i className="ti ti-edit me-1" />
            Edit
          </button>
        </div>
      ),
    },
  ];

  return (
    <>
      <ToastContainer position="top-right" autoClose={3000} hideProgressBar={false} />
      
      {/* Page Wrapper */}
      <div className="page-wrapper">
        <div className="content">
          {/* Breadcrumb */}
          <div className="d-md-flex d-block align-items-center justify-content-between page-breadcrumb mb-4">
            <div className="my-auto mb-2">
              <h2 className="mb-2 fw-bold">
                <i className="ti ti-dashboard me-2 text-primary" />
                Organization Dashboard
              </h2>
              <nav aria-label="breadcrumb">
                <ol className="breadcrumb mb-0">
                  <li className="breadcrumb-item">
                    <Link to={routes.organizationDashboard} className="text-decoration-none">
                      <i className="ti ti-smart-home me-1" />
                      Home
                    </Link>
                  </li>
                  <li className="breadcrumb-item active" aria-current="page">
                    Admin Management
                  </li>
                </ol>
              </nav>
            </div>
            <div className="d-flex my-xl-auto right-content align-items-center flex-wrap gap-2">
              <button
                className="btn btn-primary d-flex align-items-center"
                onClick={() => setShowAddAdminModal(true)}
              >
                <i className="ti ti-circle-plus me-2" />
                Add Admin
              </button>
              <div className="head-icons">
                <CollapseHeader />
              </div>
            </div>
          </div>

          {/* Summary Cards */}
          <div className="row mb-4 g-3">
            <div className="col-lg-4 col-md-6">
              <div className="card flex-fill shadow-sm border-0 h-100">
                <div className="card-body">
                  <div className="d-flex align-items-center justify-content-between">
                    <div className="d-flex align-items-center">
                      <div className="avatar avatar-lg bg-primary bg-opacity-10 rounded-circle d-flex align-items-center justify-content-center me-3" style={{ width: '60px', height: '60px' }}>
                        <i className="ti ti-users fs-4 text-primary" />
                      </div>
                      <div>
                        <p className="fs-12 fw-medium mb-1 text-muted text-uppercase">Total Admins</p>
                        <h3 className="mb-0 fw-bold text-dark">{summary.total}</h3>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="col-lg-4 col-md-6">
              <div className="card flex-fill shadow-sm border-0 h-100">
                <div className="card-body">
                  <div className="d-flex align-items-center justify-content-between">
                    <div className="d-flex align-items-center">
                      <div className="avatar avatar-lg bg-success bg-opacity-10 rounded-circle d-flex align-items-center justify-content-center me-3" style={{ width: '60px', height: '60px' }}>
                        <i className="ti ti-check fs-4 text-success" />
                      </div>
                      <div>
                        <p className="fs-12 fw-medium mb-1 text-muted text-uppercase">Active Admins</p>
                        <h3 className="mb-0 fw-bold text-success">{summary.active}</h3>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="col-lg-4 col-md-6">
              <div className="card flex-fill shadow-sm border-0 h-100">
                <div className="card-body">
                  <div className="d-flex align-items-center justify-content-between">
                    <div className="d-flex align-items-center">
                      <div className="avatar avatar-lg bg-danger bg-opacity-10 rounded-circle d-flex align-items-center justify-content-center me-3" style={{ width: '60px', height: '60px' }}>
                        <i className="ti ti-x fs-4 text-danger" />
                      </div>
                      <div>
                        <p className="fs-12 fw-medium mb-1 text-muted text-uppercase">Inactive Admins</p>
                        <h3 className="mb-0 fw-bold text-danger">{summary.inactive}</h3>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Admins Table */}
          <div className="card shadow-sm">
            <div className="card-header bg-white border-bottom">
              <div className="d-flex align-items-center justify-content-between flex-wrap row-gap-3">
                <div>
                  <h5 className="mb-0 fw-semibold">
                    <i className="ti ti-users me-2 text-primary" />
                    Admins List
                  </h5>
                  <p className="text-muted mb-0 small mt-1">Manage and monitor all admins in your organization</p>
                </div>
                <div className="d-flex align-items-center gap-2 flex-wrap">
                  <div className="input-icon input-icon-start position-relative" style={{ minWidth: '250px' }}>
                    <span className="input-icon-addon">
                      <i className="ti ti-search" />
                    </span>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Search admins..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  <div className="d-flex align-items-center gap-2">
                    <span className="badge bg-primary-subtle text-primary px-3 py-2">
                      <i className="ti ti-users me-1" />
                      {summary.total} Total
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <div className="card-body p-0">
              <Table
                dataSource={Array.isArray(admins) ? admins : []}
                columns={columns}
                rowKey="id"
                loading={loading}
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showTotal: (total, range) =>
                    `${range[0]}-${range[1]} of ${total} admins`,
                  pageSizeOptions: ["10", "20", "50", "100"],
                }}
                className="custom-table"
                scroll={{ x: "max-content" }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Admin Details Modal */}
      {showAdminDetails && selectedAdmin && (
        <div
          className="modal fade show"
          id="admin_details_modal"
          tabIndex={-1}
          aria-labelledby="admin_details_modal_label"
          aria-modal="true"
          role="dialog"
          style={{ display: "block", paddingRight: "17px" }}
        >
          <div className="modal-dialog modal-lg modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title" id="admin_details_modal_label">
                  Admin Details
                </h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => {
                    setShowAdminDetails(false);
                    setSelectedAdmin(null);
                  }}
                  aria-label="Close"
                ></button>
              </div>
              <div className="modal-body">
                <div className="row">
                  <div className="col-md-6 mb-3">
                    <label className="form-label fw-medium">Admin Name</label>
                    <p className="mb-0">{selectedAdmin.admin_name}</p>
                  </div>
                  <div className="col-md-6 mb-3">
                    <label className="form-label fw-medium">Email</label>
                    <p className="mb-0">{selectedAdmin.user?.email || "-"}</p>
                  </div>
                  <div className="col-md-6 mb-3">
                    <label className="form-label fw-medium">Username</label>
                    <p className="mb-0">{selectedAdmin.user?.username || "-"}</p>
                  </div>
                  <div className="col-md-6 mb-3">
                    <label className="form-label fw-medium">Phone Number</label>
                    <p className="mb-0">{selectedAdmin.user?.phone_number || "-"}</p>
                  </div>
                  <div className="col-md-6 mb-3">
                    <label className="form-label fw-medium">User ID (UID)</label>
                    <p className="mb-0">
                      <code className="text-primary">{selectedAdmin.user?.id || "-"}</code>
                    </p>
                  </div>
                  <div className="col-md-6 mb-3">
                    <label className="form-label fw-medium">Status</label>
                    <div>
                      <span
                        className={`badge ${
                          selectedAdmin.user?.is_active
                            ? "badge-success"
                            : "badge-danger"
                        } d-inline-flex align-items-center badge-xs`}
                      >
                        <i className="ti ti-point-filled me-1" />
                        {selectedAdmin.user?.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                  </div>
                  <div className="col-md-6 mb-3">
                    <label className="form-label fw-medium">Created At</label>
                    <p className="mb-0">
                      {selectedAdmin.created_at
                        ? new Date(selectedAdmin.created_at).toLocaleString()
                        : "-"}
                    </p>
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowAdminDetails(false);
                    setSelectedAdmin(null);
                  }}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Backdrop */}
      {showAdminDetails && (
        <div
          className="modal-backdrop fade show"
          onClick={() => {
            setShowAdminDetails(false);
            setSelectedAdmin(null);
          }}
        ></div>
      )}

      {/* Edit Admin Modal */}
      {showEditAdminModal && editingAdmin && (
        <>
          <div
            className="modal fade show"
            id="edit_admin_modal"
            tabIndex={-1}
            aria-labelledby="edit_admin_modal_label"
            aria-modal="true"
            role="dialog"
            style={{ display: "block", paddingRight: "17px" }}
          >
            <div className="modal-dialog modal-lg modal-dialog-centered">
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title" id="edit_admin_modal_label">
                    Edit Admin
                  </h5>
                  <button
                    type="button"
                    className="btn-close"
                    onClick={handleCloseEditAdminModal}
                    aria-label="Close"
                  ></button>
                </div>
                <div className="modal-body">
                  <div className="row">
                    <div className="col-md-6 mb-3">
                      <label className="form-label fw-medium">
                        Admin Name <span className="text-danger">*</span>
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Enter admin name"
                        value={editAdminForm.admin_name}
                        onChange={(e) =>
                          setEditAdminForm({ ...editAdminForm, admin_name: e.target.value })
                        }
                      />
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label fw-medium">
                        Email <span className="text-danger">*</span>
                      </label>
                      <input
                        type="email"
                        className="form-control"
                        placeholder="Enter email"
                        value={editAdminForm.email}
                        onChange={(e) =>
                          setEditAdminForm({ ...editAdminForm, email: e.target.value })
                        }
                      />
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label fw-medium">
                        Username <span className="text-danger">*</span>
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Enter username"
                        value={editAdminForm.username}
                        onChange={(e) =>
                          setEditAdminForm({ ...editAdminForm, username: e.target.value })
                        }
                      />
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label fw-medium">
                        Phone Number <span className="text-danger">*</span>
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Enter phone number"
                        value={editAdminForm.phone_number}
                        onChange={(e) =>
                          setEditAdminForm({ ...editAdminForm, phone_number: e.target.value })
                        }
                      />
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label fw-medium">Status</label>
                      <div>
                        <label className="form-check form-switch">
                          <input
                            className="form-check-input"
                            type="checkbox"
                            checked={editAdminForm.is_active}
                            onChange={(e) =>
                              setEditAdminForm({ ...editAdminForm, is_active: e.target.checked })
                            }
                          />
                          <span className="form-check-label">
                            {editAdminForm.is_active ? "Active" : "Inactive"}
                          </span>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="modal-footer">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={handleCloseEditAdminModal}
                    disabled={isUpdatingAdmin}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleUpdateAdmin}
                    disabled={isUpdatingAdmin}
                  >
                    {isUpdatingAdmin ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" />
                        Updating...
                      </>
                    ) : (
                      <>
                        <i className="ti ti-check me-2" />
                        Update Admin
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div
            className="modal-backdrop fade show"
            onClick={handleCloseEditAdminModal}
          ></div>
        </>
      )}

      {/* Add Admin Modal */}
      {showAddAdminModal && (
        <>
          <div
            className="modal fade show"
            id="add_admin_modal"
            tabIndex={-1}
            aria-labelledby="add_admin_modal_label"
            aria-modal="true"
            role="dialog"
            style={{ display: "block", paddingRight: "17px" }}
          >
            <div className="modal-dialog modal-lg modal-dialog-centered">
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title" id="add_admin_modal_label">
                    Add New Admin
                  </h5>
                  <button
                    type="button"
                    className="btn-close"
                    onClick={handleCloseAddAdminModal}
                    aria-label="Close"
                  ></button>
                </div>
                <div className="modal-body">
                  <div className="row">
                    <div className="col-md-6 mb-3">
                      <label className="form-label fw-medium">
                        Admin Name <span className="text-danger">*</span>
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Enter admin name"
                        value={addAdminForm.admin_name}
                        onChange={(e) =>
                          setAddAdminForm({ ...addAdminForm, admin_name: e.target.value })
                        }
                      />
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label fw-medium">
                        Email <span className="text-danger">*</span>
                      </label>
                      <input
                        type="email"
                        className="form-control"
                        placeholder="Enter email"
                        value={addAdminForm.email}
                        onChange={(e) =>
                          setAddAdminForm({ ...addAdminForm, email: e.target.value })
                        }
                      />
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label fw-medium">
                        Username <span className="text-danger">*</span>
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Enter username"
                        value={addAdminForm.username}
                        onChange={(e) =>
                          setAddAdminForm({ ...addAdminForm, username: e.target.value })
                        }
                      />
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label fw-medium">
                        Phone Number <span className="text-danger">*</span>
                      </label>
                      <input
                        type="tel"
                        className="form-control"
                        placeholder="Enter phone number"
                        value={addAdminForm.phone_number}
                        onChange={(e) =>
                          setAddAdminForm({ ...addAdminForm, phone_number: e.target.value })
                        }
                      />
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label fw-medium">
                        Password <span className="text-danger">*</span>
                      </label>
                      <input
                        type="password"
                        className="form-control"
                        placeholder="Enter password"
                        value={addAdminForm.password}
                        onChange={(e) =>
                          setAddAdminForm({ ...addAdminForm, password: e.target.value })
                        }
                      />
                    </div>
                  </div>
                </div>
                <div className="modal-footer">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={handleCloseAddAdminModal}
                    disabled={isCreatingAdmin}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleAddAdmin}
                    disabled={isCreatingAdmin}
                  >
                    {isCreatingAdmin ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" />
                        Creating...
                      </>
                    ) : (
                      <>
                        <i className="ti ti-check me-2" />
                        Create Admin
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div
            className="modal-backdrop fade show"
            onClick={handleCloseAddAdminModal}
          ></div>
        </>
      )}
    </>
  );
};

export default OrganizationDashboard;

