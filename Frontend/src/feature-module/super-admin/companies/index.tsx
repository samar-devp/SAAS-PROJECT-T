import React, { useState, useEffect } from "react";
import axios from "axios";
import { Link, useLocation } from "react-router-dom";
import { all_routes } from "../../router/all_routes";
import PredefinedDateRanges from "../../../core/common/datePicker";
import { companies_details } from "../../../core/data/json/companiesdetails";
import ImageWithBasePath from "../../../core/common/imageWithBasePath";
// import Table from "../../../core/common/dataTable/index";
import { Table } from "antd";
import CommonSelect from "../../../core/common/commonSelect";
import { DatePicker } from "antd";
import ReactApexChart from "react-apexcharts";
import CollapseHeader from "../../../core/common/collapse-header/collapse-header";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { BACKEND_PATH } from "../../../environment";
import { getAdminIdForApi } from '../../../core/utils/apiHelpers';
import { removeAllBackdrops, resetBodyStyles, cleanupExcessBackdrops, createBackdropCleanupInterval } from "../../../core/utils/modalHelpers";
import AssignLeaveModal from "../../hrm/leave-assignment/AssignLeaveModal";
import LeaveApplicationsSidebar from "../../hrm/leave-applications/LeaveApplicationsSidebar";
import ApplyLeaveModal from "../../hrm/leave-applications/ApplyLeaveModal";
import AssignShiftModal from "../../hrm/shift-assignment/AssignShiftModal";
import AssignLocationModal from "../../hrm/location-assignment/AssignLocationModal";
import AssignWeekOffModal from "../../hrm/week-off-assignment/AssignWeekOffModal";

type PasswordField = "password" | "confirmPassword";
const Companies = () => {
  const location = useLocation();
  const [organizationName, setOrganizationName] = useState<string>("");
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [data, setData] = useState([]);
  const [deactivatedData, setDeactivatedData] = useState([]);
  const [activeTab, setActiveTab] = useState<'active' | 'deactivated'>(
    location.pathname === all_routes.deactivatedEmployees ? 'deactivated' : 'active'
  );
  const [loadingDeactivated, setLoadingDeactivated] = useState(false);
  const [selectedEmployees, setSelectedEmployees] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>("");
  type SummaryType = {
  total: number;
  active: number;
  inactive: number;
};

  const [summary, setSummary] = useState<SummaryType | null>(null);
  const [loading, setLoading] = useState(true);
  const [userRole, setUserRole] = useState<string | null>(null);

  // Employee registration form state
  const [employeeForm, setEmployeeForm] = useState({
    user_name: "",
    email: "",
    username: "",
    password: "",
    custom_employee_id: "",
    phone_number: "",
    date_of_birth: "",
    date_of_joining: "",
    gender: "",
    designation: "",
    job_title: "",
  });
  const [employeePasswordVisibility, setEmployeePasswordVisibility] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  // Bulk registration state
  const [showBulkUploadModal, setShowBulkUploadModal] = useState(false);
  const [bulkUploadFile, setBulkUploadFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string>("");
  
  // Employee edit modal state
  const [showEditEmployeeModal, setShowEditEmployeeModal] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<any>(null);
  const [isUpdatingEmployee, setIsUpdatingEmployee] = useState(false);
  const [editEmployeeForm, setEditEmployeeForm] = useState({
    user_name: "",
    email: "",
    username: "",
    phone_number: "",
    custom_employee_id: "",
    date_of_birth: "",
    date_of_joining: "",
    gender: "",
    designation: "",
    job_title: "",
    is_active: true,
  });

  // Leave assignment state
  const [selectedEmployeeForLeave, setSelectedEmployeeForLeave] = useState<any>(null);

  // Leave applications sidebar state
  const [isLeaveAppsSidebarOpen, setIsLeaveAppsSidebarOpen] = useState(false);
  const [selectedEmployeeForLeaveApps, setSelectedEmployeeForLeaveApps] = useState<any>(null);

  // Apply leave modal state
  const [selectedEmployeeForApplyLeave, setSelectedEmployeeForApplyLeave] = useState<any>(null);

  // Shift modal state
  const [selectedEmployeeForShift, setSelectedEmployeeForShift] = useState<any>(null);

  // Location modal state
  const [selectedEmployeeForLocation, setSelectedEmployeeForLocation] = useState<any>(null);

  // Week Off modal state
  const [selectedEmployeeForWeekOff, setSelectedEmployeeForWeekOff] = useState<any>(null);

  // Helper function to close any open modal
  const closeOpenModals = () => {
    const modals = ['assign_leave_modal', 'apply_leave_for_employee_modal', 'edit_employee_modal', 'bulk_upload_modal'];
    
    modals.forEach(modalId => {
      const modal = document.getElementById(modalId);
      if (modal && modal.classList.contains('show')) {
        modal.classList.remove('show');
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
        modal.removeAttribute('aria-modal');
      }
    });

    // Remove ALL backdrops using utility function
    removeAllBackdrops();

    // Reset body styles using utility function
    resetBodyStyles();
  };

  // Global cleanup function to ensure no stray backdrops remain
  useEffect(() => {
    // Use utility function to create cleanup interval
    const cleanup = createBackdropCleanupInterval(1000);
    
    return cleanup;
  }, []);

  useEffect(() => {
    // Get user role on mount
    const role = sessionStorage.getItem("role");
    setUserRole(role);
    
    const fetchCompanies = async () => {
      try {
        const token = sessionStorage.getItem("access_token");
        // Use utility function to get correct admin_id based on role
        // For organization: returns selected_admin_id (admin selected in dashboard)
        // For admin: returns user_id
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

        const response = await axios.get(
          `${BACKEND_PATH}staff-list/${admin_id}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        // ✅ Extract results array
        setData(response.data.results);
        setSummary(response.data.summary)
        console.log(response.data.results, "===============asasas", response.data.summary)
        setLoading(false);
      } catch (error) {
        console.error("Error fetching organizations:", error);
        setLoading(false);
      }
    };
    fetchCompanies();
  }, []);

  // Fetch deactivated employees
  const fetchDeactivatedEmployees = async (search: string = "") => {
    setLoadingDeactivated(true);
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
        setLoadingDeactivated(false);
        return;
      }

      let url = `${BACKEND_PATH}deactivate_list/${admin_id}`;
      if (search) {
        url += `?q=${encodeURIComponent(search)}`;
      }

      const response = await axios.get(
        url,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      let deactivatedEmployees = [];
      if (response.data && response.data.data) {
        if (response.data.data.results && Array.isArray(response.data.data.results)) {
          deactivatedEmployees = response.data.data.results;
        } else if (Array.isArray(response.data.data)) {
          deactivatedEmployees = response.data.data;
        }
      } else if (Array.isArray(response.data)) {
        deactivatedEmployees = response.data;
      }
      
      setDeactivatedData(deactivatedEmployees);
      setLoadingDeactivated(false);
    } catch (error: any) {
      console.error("Error fetching deactivated employees:", error);
      toast.error(error.response?.data?.message || "Failed to fetch deactivated employees");
      setLoadingDeactivated(false);
    }
  };

  // Set active tab based on route
  useEffect(() => {
    if (location.pathname === all_routes.deactivatedEmployees) {
      setActiveTab('deactivated');
    } else if (location.pathname === all_routes.adminDashboard || location.pathname === '/index') {
      setActiveTab('active');
    }
  }, [location.pathname]);

  // Fetch deactivated employees when tab changes
  useEffect(() => {
    if (activeTab === 'deactivated') {
      fetchDeactivatedEmployees(searchQuery);
    } else {
      // Clear search when switching to active tab
      setSearchQuery("");
    }
  }, [activeTab]);

  // Bulk activate/deactivate employees
  const handleBulkActivateDeactivate = async (action: 'activate' | 'deactivate') => {
    if (selectedEmployees.length === 0) {
      toast.error("Please select at least one employee");
      return;
    }

    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = getAdminIdForApi();
      
      if (!admin_id) {
        toast.error("Admin ID not found");
        return;
      }

      const response = await axios.put(
        `${BACKEND_PATH}deactivate_list_update/${admin_id}`,
        {
          employee_ids: selectedEmployees,
          action: action
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (response.data?.status === 200) {
        toast.success(`Successfully ${action === 'activate' ? 'activated' : 'deactivated'} ${selectedEmployees.length} employee(s)`);
        setSelectedEmployees([]);
        
        // Refresh data
        if (activeTab === 'active') {
          const fetchCompanies = async () => {
            try {
              const token = sessionStorage.getItem("access_token");
              const admin_id = getAdminIdForApi();
              if (!admin_id) return;

              const response = await axios.get(
                `${BACKEND_PATH}staff-list/${admin_id}`,
                {
                  headers: {
                    Authorization: `Bearer ${token}`,
                  },
                }
              );
              setData(response.data.results);
              setSummary(response.data.summary);
            } catch (error) {
              console.error("Error refreshing employee list:", error);
            }
          };
          fetchCompanies();
        } else {
          fetchDeactivatedEmployees(searchQuery);
        }
      } else {
        toast.error(response.data?.message || `Failed to ${action} employees`);
      }
    } catch (error: any) {
      console.error(`Error ${action}ing employees:`, error);
      toast.error(error.response?.data?.message || `Failed to ${action} employees`);
    }
  };

  // Helper function to get initials from name
  const getInitials = (name: string) => {
    if (!name) return "U";
    const parts = name.trim().split(" ");
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  // Helper function to get color based on name
  const getAvatarColor = (name: string) => {
    const colors = [
      "bg-primary",
      "bg-success",
      "bg-info",
      "bg-warning",
      "bg-danger",
      "bg-secondary",
    ];
    if (!name) return colors[0];
    const index = name.charCodeAt(0) % colors.length;
    return colors[index];
  };

  // Avatar component for employee
  const EmployeeAvatar = ({ record }: { record: any }) => {
    const [imageError, setImageError] = React.useState(false);
    const hasImage = record.profile_photo && !imageError;
    
    return (
      <Link to="#" className="avatar avatar-md border rounded-circle position-relative">
        {hasImage ? (
          <img
            src={record.profile_photo}
            className="img-fluid rounded-circle"
            alt={record.user_name || "User"}
            onError={() => setImageError(true)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        ) : (
          <span
            className={`avatar-initial rounded-circle ${getAvatarColor(
              record.user_name || ""
            )} d-flex align-items-center justify-content-center text-white fw-semibold`}
            style={{
              width: "100%",
              height: "100%",
              fontSize: "14px",
            }}
          >
            {getInitials(record.user_name || "User")}
          </span>
        )}
      </Link>
    );
  };

  const columns = [
    {
      title: "Employee Name",
      dataIndex: "user_name",
      render: (text: string, record: any) => (
        <div className="d-flex align-items-center file-name-icon">
          <EmployeeAvatar record={record} />
          <div className="ms-2">
            <h6 className="fw-medium mb-0">
              <Link to="#">{record.user_name}</Link>
            </h6>
          </div>
        </div>
      ),
      sorter: (a: any, b: any) => a.user_name.length - b.user_name.length,
    },
    {
      title: "Username",
      dataIndex: "user",
      render: (user: any) => user.username,
      sorter: (a: any, b: any) => a.user.username.length - b.user.username.length,
    },
    {
      title: "Email",
      dataIndex: "user",
      render: (user: any) => user.email,
      sorter: (a: any, b: any) => a.user.email.length - b.user.email.length,
    },
    {
      title: "Designation",
      dataIndex: "designation",
      sorter: (a: any, b: any) => a.designation.length - b.designation.length,
    },
    {
      title: "Created At",
      dataIndex: "created_at",
      render: (text: string) => new Date(text).toLocaleDateString(),
      sorter: (a: any, b: any) =>
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: "Leaves",
      key: "leaves",
      align: "center" as const,
      render: (_: any, record: any) => (
        <button
          className="btn btn-sm btn-outline-secondary"
          onClick={(e) => {
            e.preventDefault();
            console.log("Selected employee for leave:", record);
            
            // Clean up any stray backdrops before opening modal using utility function
            setTimeout(() => {
              cleanupExcessBackdrops();
            }, 100);
            
            setSelectedEmployeeForLeave(record);
          }}
          data-bs-toggle="modal"
          data-bs-target="#assign_leave_modal"
          title="Manage Leaves"
        >
          <i className="ti ti-calendar" />
        </button>
      ),
    },
    {
      title: "Shift",
      key: "shift",
      align: "center" as const,
      render: (_: any, record: any) => (
        <button
          className="btn btn-sm btn-outline-secondary"
          onClick={(e) => {
            e.preventDefault();
            console.log("Selected employee for shift:", record);
            
            // Clean up any stray backdrops before opening modal
            setTimeout(() => {
              cleanupExcessBackdrops();
            }, 100);
            
            setSelectedEmployeeForShift(record);
          }}
          data-bs-toggle="modal"
          data-bs-target="#assign_shift_modal"
          title="Assign Shift"
        >
          <i className="ti ti-clock" />
        </button>
      ),
    },
    {
      title: "Week Off",
      key: "weekoff",
      align: "center" as const,
      render: (_: any, record: any) => (
        <button
          className="btn btn-sm btn-outline-secondary"
          onClick={(e) => {
            e.preventDefault();
            console.log("Selected employee for week off:", record);
            
            // Clean up any stray backdrops before opening modal
            setTimeout(() => {
              cleanupExcessBackdrops();
            }, 100);
            
            setSelectedEmployeeForWeekOff(record);
          }}
          data-bs-toggle="modal"
          data-bs-target="#assign_week_off_modal"
          title="Assign Week Off"
        >
          <i className="ti ti-calendar-off" />
        </button>
      ),
    },
    {
      title: "Location",
      key: "location",
      align: "center" as const,
      render: (_: any, record: any) => (
        <button
          className="btn btn-sm btn-outline-secondary"
          onClick={(e) => {
            e.preventDefault();
            console.log("Selected employee for location:", record);
            
            // Clean up any stray backdrops before opening modal
            setTimeout(() => {
              cleanupExcessBackdrops();
            }, 100);
            
            setSelectedEmployeeForLocation(record);
          }}
          data-bs-toggle="modal"
          data-bs-target="#assign_location_modal"
          title="Assign Location"
        >
          <i className="ti ti-map-pin" />
        </button>
      ),
    },
    {
      title: "Edit",
      key: "edit",
      align: "center" as const,
      render: (_: any, record: any) => (
        <button
          className="btn btn-sm btn-outline-secondary"
          onClick={(e) => {
            e.preventDefault();
            closeOpenModals();
            handleEditEmployee(record);
          }}
          title="Edit Employee"
        >
          <i className="ti ti-edit me-1" />
          Edit
        </button>
      ),
    },
  ];
  const [passwordVisibility, setPasswordVisibility] = useState({
    password: false,
    confirmPassword: false,
  });

  const togglePasswordVisibility = (field: PasswordField) => {
    setPasswordVisibility((prevState) => ({
      ...prevState,
      [field]: !prevState[field],
    }));
  };

  const handleEditEmployee = (employee: any) => {
    setEditingEmployee(employee);
    setEditEmployeeForm({
      user_name: employee.user_name || "",
      email: employee.user?.email || "",
      username: employee.user?.username || "",
      phone_number: employee.user?.phone_number || "",
      custom_employee_id: employee.custom_employee_id || "",
      date_of_birth: employee.date_of_birth || "",
      date_of_joining: employee.date_of_joining || "",
      gender: employee.gender || "",
      designation: employee.designation || "",
      job_title: employee.job_title || "",
      is_active: employee.is_active !== undefined ? employee.is_active : (employee.user?.is_active !== undefined ? employee.user.is_active : true),
    });
    setShowEditEmployeeModal(true);
  };

  const handleCloseEditEmployeeModal = () => {
    setShowEditEmployeeModal(false);
    setEditingEmployee(null);
    setEditEmployeeForm({
      user_name: "",
      email: "",
      username: "",
      phone_number: "",
      custom_employee_id: "",
      date_of_birth: "",
      date_of_joining: "",
      gender: "",
      designation: "",
      job_title: "",
      is_active: true,
    });
  };

  const handleDownloadSampleCSV = async () => {
    try {
      const token = sessionStorage.getItem("access_token");
      if (!token) {
        toast.error("Please login again");
        return;
      }

      const response = await axios.get(
        `${BACKEND_PATH}bulk-register/download/employee-sample`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          responseType: 'blob', // Important for file download
        }
      );

      // Create a blob URL and trigger download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Get filename from response headers or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'employee_bulk_upload_template.csv';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success("Sample CSV downloaded successfully");
    } catch (error: any) {
      console.error("Error downloading sample CSV:", error);
      toast.error(error.response?.data?.message || "Failed to download sample CSV");
    }
  };

  const handleBulkUpload = async () => {
    if (!bulkUploadFile) {
      toast.error("Please select a file to upload");
      return;
    }

    const admin_id = getAdminIdForApi();
    if (!admin_id) {
      const role = sessionStorage.getItem("role");
      if (role === "organization") {
        toast.error("Please select an admin first from the dashboard.");
      } else {
        toast.error("Admin ID not found. Please login again.");
      }
      return;
    }

    setIsUploading(true);
    setUploadProgress("Preparing file for upload...");

    try {
      const token = sessionStorage.getItem("access_token");
      if (!token) {
        toast.error("Please login again");
        setIsUploading(false);
        return;
      }

      // Create FormData for file upload
      const formData = new FormData();
      formData.append('file', bulkUploadFile);

      setUploadProgress("Uploading file...");

      const response = await axios.post(
        `${BACKEND_PATH}bulk-register/employees/${admin_id}`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              );
              setUploadProgress(`Uploading... ${percentCompleted}%`);
            }
          },
        }
      );

      if (response.data?.status === 200) {
        const processed = response.data?.processed || 0;
        const errors = response.data?.errors || [];
        
        if (errors.length > 0) {
          toast.warning(
            `Successfully created ${processed} employees. ${errors.length} error(s) occurred. Check console for details.`
          );
          console.error("Bulk upload errors:", errors);
        } else {
          toast.success(`Successfully created ${processed} employees`);
        }
        
        // Close modal and refresh employee list
        setShowBulkUploadModal(false);
        setBulkUploadFile(null);
        setUploadProgress("");
        
        // Refresh employee list
        const fetchCompanies = async () => {
          try {
            const token = sessionStorage.getItem("access_token");
            const admin_id = getAdminIdForApi();
            if (!admin_id) return;

            const response = await axios.get(
              `${BACKEND_PATH}staff-list/${admin_id}`,
              {
                headers: {
                  Authorization: `Bearer ${token}`,
                },
              }
            );
            setData(response.data.results);
            setSummary(response.data.summary);
          } catch (error) {
            console.error("Error refreshing employee list:", error);
          }
        };
        fetchCompanies();
      } else {
        toast.error(response.data?.message || "Failed to upload file");
      }
    } catch (error: any) {
      console.error("Error uploading file:", error);
      let errorMessage = "Failed to upload file";
      
      if (error.response?.data) {
        if (error.response.data.errors && Array.isArray(error.response.data.errors)) {
          errorMessage = `Errors: ${error.response.data.errors.slice(0, 3).join(', ')}${error.response.data.errors.length > 3 ? '...' : ''}`;
        } else if (error.response.data.message) {
          errorMessage = error.response.data.message;
        } else if (error.response.data.error) {
          errorMessage = error.response.data.error;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast.error(errorMessage);
    } finally {
      setIsUploading(false);
      setUploadProgress("");
    }
  };

  const handleUpdateEmployee = async () => {
    if (!editingEmployee) return;

    // Validate required fields
    if (!editEmployeeForm.user_name || !editEmployeeForm.email || !editEmployeeForm.username || !editEmployeeForm.phone_number || !editEmployeeForm.custom_employee_id) {
      toast.error("Please fill all required fields");
      return;
    }

    setIsUpdatingEmployee(true);
    try {
      const token = sessionStorage.getItem("access_token");
      if (!token) {
        toast.error("Please login again");
        setIsUpdatingEmployee(false);
        return;
      }

      // Get admin_id and user_id
      // admin field can be UUID string or object with id, user field is always an object
      const admin_id = typeof editingEmployee.admin === 'string' 
        ? editingEmployee.admin 
        : (editingEmployee.admin?.id || editingEmployee.admin_id);
      const user_id = editingEmployee.user?.id || editingEmployee.user_id;

      if (!admin_id || !user_id) {
        toast.error("Admin ID or User ID not found. Please try refreshing the page.");
        setIsUpdatingEmployee(false);
        return;
      }

      // Use EmployeeProfileUpdateAPIView endpoint with admin_id and user_id
      const response = await axios.put(
        `${BACKEND_PATH}employee_profile_update/${admin_id}/${user_id}`,
        {
          user_name: editEmployeeForm.user_name,
          custom_employee_id: editEmployeeForm.custom_employee_id,
          date_of_birth: editEmployeeForm.date_of_birth || null,
          date_of_joining: editEmployeeForm.date_of_joining || null,
          gender: editEmployeeForm.gender || "",
          designation: editEmployeeForm.designation || "",
          job_title: editEmployeeForm.job_title || "",
          email: editEmployeeForm.email,
          phone_number: editEmployeeForm.phone_number,
          user: {
            is_active: editEmployeeForm.is_active,
          },
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.data?.status === 200 || response.status === 200) {
        toast.success(response.data?.message || "Employee updated successfully");
        setShowEditEmployeeModal(false);
        setEditingEmployee(null);
        // Refresh employee list
        window.location.reload();
      } else {
        toast.error(response.data?.message || "Failed to update employee");
      }
    } catch (error: any) {
      console.error("Error updating employee:", error);
      
      // Extract error messages
      let errorMessage = "Failed to update employee";
      
      if (error.response?.data) {
        const errorData = error.response.data;
        
        // Handle nested errors
        if (errorData.errors) {
          if (errorData.errors.user) {
            const userErrors = [];
            if (errorData.errors.user.email) userErrors.push(`Email: ${Array.isArray(errorData.errors.user.email) ? errorData.errors.user.email[0] : errorData.errors.user.email}`);
            if (errorData.errors.user.username) userErrors.push(`Username: ${Array.isArray(errorData.errors.user.username) ? errorData.errors.user.username[0] : errorData.errors.user.username}`);
            if (errorData.errors.user.phone_number) userErrors.push(`Phone: ${Array.isArray(errorData.errors.user.phone_number) ? errorData.errors.user.phone_number[0] : errorData.errors.user.phone_number}`);
            if (userErrors.length > 0) {
              errorMessage = userErrors.join(", ");
            }
          }
          
          if (!errorMessage || errorMessage === "Failed to update employee") {
            const fieldErrors = [];
            if (errorData.errors.custom_employee_id) fieldErrors.push(`Employee ID: ${Array.isArray(errorData.errors.custom_employee_id) ? errorData.errors.custom_employee_id[0] : errorData.errors.custom_employee_id}`);
            if (errorData.errors.user_name) fieldErrors.push(`Name: ${Array.isArray(errorData.errors.user_name) ? errorData.errors.user_name[0] : errorData.errors.user_name}`);
            if (fieldErrors.length > 0) {
              errorMessage = fieldErrors.join(", ");
            }
          }
        }
        
        if (!errorMessage || errorMessage === "Failed to update employee") {
          if (errorData.message) {
            errorMessage = errorData.message;
          } else if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast.error(errorMessage);
    } finally {
      setIsUpdatingEmployee(false);
    }
  };

  const planName = [
    { value: "Advanced", label: "Advanced" },
    { value: "Basic", label: "Basic" },
    { value: "Enterprise", label: "Enterprise" },
  ];
  const planType = [
    { value: "Monthly", label: "Monthly" },
    { value: "Yearly", label: "Yearly" },
  ];
  const currency = [
    { value: "USD", label: "USD" },
    { value: "Euro", label: "Euro" },
  ];
  const language = [
    { value: "English", label: "English" },
    { value: "Arabic", label: "Arabic" },
  ];
  const statusChoose = [
    { value: "Active", label: "Active" },
    { value: "Inactive", label: "Inactive" },
  ];

  const getModalContainer = () => {
    const modalElement = document.getElementById("modal-datepicker");
    return modalElement ? modalElement : document.body; // Fallback to document.body if modalElement is null
  };

  const [totalChart] = React.useState<any>({
    series: [
      {
        name: "Messages",
        data: [25, 66, 41, 12, 36, 9, 21],
      },
    ],
    fill: {
      type: "gradient",
      gradient: {
        opacityFrom: 0, // Start with 0 opacity (transparent)
        opacityTo: 0, // End with 0 opacity (transparent)
      },
    },
    chart: {
      foreColor: "#fff",
      type: "area",
      width: 50,
      toolbar: {
        show: !1,
      },
      zoom: {
        enabled: !1,
      },
      dropShadow: {
        enabled: 0,
        top: 3,
        left: 14,
        blur: 4,
        opacity: 0.12,
        color: "#fff",
      },
      sparkline: {
        enabled: !0,
      },
    },
    markers: {
      size: 0,
      colors: ["#F26522"],
      strokeColors: "#fff",
      strokeWidth: 2,
      hover: {
        size: 7,
      },
    },
    plotOptions: {
      bar: {
        horizontal: !1,
        columnWidth: "35%",
        endingShape: "rounded",
      },
    },
    dataLabels: {
      enabled: !1,
    },
    stroke: {
      show: !0,
      width: 2.5,
      curve: "smooth",
    },
    colors: ["#F26522"],
    xaxis: {
      categories: [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
      ],
    },
    tooltip: {
      theme: "dark",
      fixed: {
        enabled: !1,
      },
      x: {
        show: !1,
      },
      y: {
        title: {
          formatter: function (e: any) {
            return "";
          },
        },
      },
      marker: {
        show: !1,
      },
    },
  });
  const [activeChart] = React.useState<any>({
    series: [
      {
        name: "Active Company",
        data: [25, 40, 35, 20, 36, 9, 21],
      },
    ],
    fill: {
      type: "gradient",
      gradient: {
        opacityFrom: 0, // Start with 0 opacity (transparent)
        opacityTo: 0, // End with 0 opacity (transparent)
      },
    },
    chart: {
      foreColor: "#fff",
      type: "area",
      width: 50,
      toolbar: {
        show: !1,
      },
      zoom: {
        enabled: !1,
      },
      dropShadow: {
        enabled: 0,
        top: 3,
        left: 14,
        blur: 4,
        opacity: 0.12,
        color: "#fff",
      },
      sparkline: {
        enabled: !0,
      },
    },
    markers: {
      size: 0,
      colors: ["#F26522"],
      strokeColors: "#fff",
      strokeWidth: 2,
      hover: {
        size: 7,
      },
    },
    plotOptions: {
      bar: {
        horizontal: !1,
        columnWidth: "35%",
        endingShape: "rounded",
      },
    },
    dataLabels: {
      enabled: !1,
    },
    stroke: {
      show: !0,
      width: 2.5,
      curve: "smooth",
    },
    colors: ["#F26522"],
    xaxis: {
      categories: [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
      ],
    },
    tooltip: {
      theme: "dark",
      fixed: {
        enabled: !1,
      },
      x: {
        show: !1,
      },
      y: {
        title: {
          formatter: function (e: any) {
            return "";
          },
        },
      },
      marker: {
        show: !1,
      },
    },
  });
  const [inactiveChart] = React.useState<any>({
    series: [
      {
        name: "Inactive Company",
        data: [25, 10, 35, 5, 25, 28, 21],
      },
    ],
    fill: {
      type: "gradient",
      gradient: {
        opacityFrom: 0, // Start with 0 opacity (transparent)
        opacityTo: 0, // End with 0 opacity (transparent)
      },
    },
    chart: {
      foreColor: "#fff",
      type: "area",
      width: 50,
      toolbar: {
        show: !1,
      },
      zoom: {
        enabled: !1,
      },
      dropShadow: {
        enabled: 0,
        top: 3,
        left: 14,
        blur: 4,
        opacity: 0.12,
        color: "#fff",
      },
      sparkline: {
        enabled: !0,
      },
    },
    markers: {
      size: 0,
      colors: ["#F26522"],
      strokeColors: "#fff",
      strokeWidth: 2,
      hover: {
        size: 7,
      },
    },
    plotOptions: {
      bar: {
        horizontal: !1,
        columnWidth: "35%",
        endingShape: "rounded",
      },
    },
    dataLabels: {
      enabled: !1,
    },
    stroke: {
      show: !0,
      width: 2.5,
      curve: "smooth",
    },
    colors: ["#F26522"],
    xaxis: {
      categories: [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
      ],
    },
    tooltip: {
      theme: "dark",
      fixed: {
        enabled: !1,
      },
      x: {
        show: !1,
      },
      y: {
        title: {
          formatter: function (e: any) {
            return "";
          },
        },
      },
      marker: {
        show: !1,
      },
    },
  });
  const [locationChart] = React.useState<any>({
    series: [
      {
        name: "Inactive Company",
        data: [30, 40, 15, 23, 20, 23, 25],
      },
    ],
    fill: {
      type: "gradient",
      gradient: {
        opacityFrom: 0, // Start with 0 opacity (transparent)
        opacityTo: 0, // End with 0 opacity (transparent)
      },
    },
    chart: {
      foreColor: "#fff",
      type: "area",
      width: 50,
      toolbar: {
        show: !1,
      },
      zoom: {
        enabled: !1,
      },
      dropShadow: {
        enabled: 0,
        top: 3,
        left: 14,
        blur: 4,
        opacity: 0.12,
        color: "#fff",
      },
      sparkline: {
        enabled: !0,
      },
    },
    markers: {
      size: 0,
      colors: ["#F26522"],
      strokeColors: "#fff",
      strokeWidth: 2,
      hover: {
        size: 7,
      },
    },
    plotOptions: {
      bar: {
        horizontal: !1,
        columnWidth: "35%",
        endingShape: "rounded",
      },
    },
    dataLabels: {
      enabled: !1,
    },
    stroke: {
      show: !0,
      width: 2.5,
      curve: "smooth",
    },
    colors: ["#F26522"],
    xaxis: {
      categories: [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
      ],
    },
    tooltip: {
      theme: "dark",
      fixed: {
        enabled: !1,
      },
      x: {
        show: !1,
      },
      y: {
        title: {
          formatter: function (e: any) {
            return "";
          },
        },
      },
      marker: {
        show: !1,
      },
    },
  });

  return (
    <>
      {/* Page Wrapper */}
      <div className="page-wrapper">
        <div className="content">
          {/* Breadcrumb */}
          <div className="d-md-flex d-block align-items-center justify-content-between page-breadcrumb mb-3">
            <div className="my-auto mb-2">
              <h2 className="mb-1">Employees</h2>
            </div>
            <div className="d-flex my-xl-auto right-content align-items-center flex-wrap ">
              <div className="mb-2 d-flex gap-2">
                {/* Show Add Employee button only for admin role */}
                {userRole === "admin" && (
                  <Link
                    to="#"
                    data-bs-toggle="modal"
                    data-bs-target="#add_employee"
                    className="btn btn-primary d-flex align-items-center"
                  >
                    <i className="ti ti-circle-plus me-2" />
                    Add Employee
                  </Link>
                )}
                {/* Show Bulk Register button only for admin role */}
                {userRole === "admin" && (
                  <button
                    type="button"
                    onClick={() => setShowBulkUploadModal(true)}
                    className="btn btn-success d-flex align-items-center"
                  >
                    <i className="ti ti-upload me-2" />
                    Bulk Register
                  </button>
                )}
              </div>
              <div className="head-icons ms-2">
                <CollapseHeader />
              </div>
            </div>
          </div>
          {/* /Breadcrumb */}
          <div className="row">
            {/* Total Employees */}
            <div className="col-lg-3 col-md-6 d-flex">
              <div className="card flex-fill">
                <div className="card-body d-flex align-items-center justify-content-between">
                  <div className="d-flex align-items-center overflow-hidden">
                    <span className="avatar avatar-lg bg-primary flex-shrink-0">
                      <i className="ti ti-building fs-16" />
                    </span>
                    <div className="ms-2 overflow-hidden">
                      <p className="fs-12 fw-medium mb-1 text-truncate">
                        Total Employees
                      </p>
                      <h4>{summary?.total ?? 0}</h4>
                    </div>
                  </div>
                  <ReactApexChart
                    options={totalChart}
                    series={totalChart.series}
                    type="area"
                    width={50}
                  />
                </div>
              </div>
            </div>
            {/* /Total Employees */}
            {/* Total Employees */}
            <div className="col-lg-3 col-md-6 d-flex">
              <div className="card flex-fill">
                <div className="card-body d-flex align-items-center justify-content-between">
                  <div className="d-flex align-items-center overflow-hidden">
                    <span className="avatar avatar-lg bg-success flex-shrink-0">
                      <i className="ti ti-building fs-16" />
                    </span>
                    <div className="ms-2 overflow-hidden">
                      <p className="fs-12 fw-medium mb-1 text-truncate">
                        Active Employees
                      </p>
                      <h4>{summary?.active ?? 0}</h4>
                    </div>
                  </div>
                  <ReactApexChart
                    options={activeChart}
                    series={activeChart.series}
                    type="area"
                    width={50}
                  />
                </div>
              </div>
            </div>
            {/* /Total Employees */}
            {/* Inactive Employees */}
            <div className="col-lg-3 col-md-6 d-flex">
              <div className="card flex-fill">
                <div className="card-body d-flex align-items-center justify-content-between">
                  <div className="d-flex align-items-center overflow-hidden">
                    <span className="avatar avatar-lg bg-danger flex-shrink-0">
                      <i className="ti ti-building fs-16" />
                    </span>
                    <div className="ms-2 overflow-hidden">
                      <p className="fs-12 fw-medium mb-1 text-truncate">
                        Inactive Employees
                      </p>
                      <h4>{summary?.inactive ?? 0}</h4>
                    </div>
                  </div>
                  <ReactApexChart
                    options={inactiveChart}
                    series={inactiveChart.series}
                    type="area"
                    width={50}
                  />
                </div>
              </div>
            </div>
            {/* /Inactive Employees */}
          </div>
          <div className="card">
            <div className="card-header d-flex align-items-center justify-content-between flex-wrap row-gap-3">
              <h5>Employees List</h5>
              {activeTab === 'deactivated' && selectedEmployees.length > 0 && (
                <div className="d-flex gap-2">
                  <button
                    className="btn btn-sm btn-success"
                    onClick={() => handleBulkActivateDeactivate('activate')}
                  >
                    <i className="ti ti-check me-1" />
                    Activate Selected ({selectedEmployees.length})
                  </button>
                </div>
              )}
            </div>
            <div className="card-body p-0">
              {/* Tabs */}
              <ul className="nav nav-tabs border-bottom" role="tablist">
                <li className="nav-item" role="presentation">
                  <button
                    className={`nav-link ${activeTab === 'active' ? 'active' : ''}`}
                    onClick={() => setActiveTab('active')}
                    type="button"
                  >
                    Active Employees
                  </button>
                </li>
                <li className="nav-item" role="presentation">
                  <button
                    className={`nav-link ${activeTab === 'deactivated' ? 'active' : ''}`}
                    onClick={() => setActiveTab('deactivated')}
                    type="button"
                  >
                    Deactivated Employees
                  </button>
                </li>
              </ul>
              
              {/* Tab Content */}
              <div className="tab-content p-3">
                {activeTab === 'active' ? (
                  <Table
                    dataSource={data}
                    columns={columns}
                    loading={loading}
                    rowKey={(record: any) => record.user?.id || record.user_id || record.id}
                  />
                ) : (
                  <>
                    {/* Search Bar for Deactivated Employees */}
                    <div className="mb-3">
                      <div className="input-group">
                        <input
                          type="text"
                          className="form-control"
                          placeholder="Search by name, employee ID, or email..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                        />
                        <button
                          className="btn btn-outline-secondary"
                          type="button"
                          onClick={() => fetchDeactivatedEmployees(searchQuery)}
                        >
                          <i className="ti ti-search" />
                        </button>
                        {searchQuery && (
                          <button
                            className="btn btn-outline-secondary"
                            type="button"
                            onClick={() => {
                              setSearchQuery("");
                              fetchDeactivatedEmployees("");
                            }}
                          >
                            <i className="ti ti-x" />
                          </button>
                        )}
                      </div>
                    </div>
                    <Table
                      dataSource={deactivatedData}
                      columns={columns.map(col => {
                      if (col.key === 'edit') {
                        return {
                          ...col,
                          title: 'Actions',
                          render: (_: any, record: any) => (
                            <div className="d-flex gap-2">
                              <button
                                className="btn btn-sm btn-success"
                                onClick={async () => {
                                  try {
                                    const token = sessionStorage.getItem("access_token");
                                    const admin_id = getAdminIdForApi();
                                    if (!admin_id) return;

                                    await axios.put(
                                      `${BACKEND_PATH}deactivate_list_update/${admin_id}`,
                                      {
                                        employee_ids: [record.user?.id || record.user_id || record.id],
                                        action: 'activate'
                                      },
                                      {
                                        headers: {
                                          Authorization: `Bearer ${token}`,
                                          "Content-Type": "application/json",
                                        },
                                      }
                                    );
                                    toast.success("Employee activated successfully");
                                    fetchDeactivatedEmployees(searchQuery);
                                    
                                    // Refresh active employees list and summary
                                    const fetchCompanies = async () => {
                                      try {
                                        const token = sessionStorage.getItem("access_token");
                                        const admin_id = getAdminIdForApi();
                                        if (!admin_id) return;

                                        const response = await axios.get(
                                          `${BACKEND_PATH}staff-list/${admin_id}`,
                                          {
                                            headers: {
                                              Authorization: `Bearer ${token}`,
                                            },
                                          }
                                        );
                                        setData(response.data.results);
                                        setSummary(response.data.summary);
                                      } catch (error) {
                                        console.error("Error refreshing employee list:", error);
                                      }
                                    };
                                    fetchCompanies();
                                  } catch (error: any) {
                                    toast.error(error.response?.data?.message || "Failed to activate employee");
                                  }
                                }}
                              >
                                <i className="ti ti-check me-1" />
                                Activate
                              </button>
                            </div>
                          ),
                        };
                      }
                      return col;
                    })}
                    loading={loadingDeactivated}
                    rowKey={(record: any) => record.user?.id || record.user_id || record.id}
                    rowSelection={
                      userRole === "admin"
                        ? {
                            type: 'checkbox',
                            selectedRowKeys: selectedEmployees,
                            onChange: (selectedRowKeys: React.Key[]) => {
                              setSelectedEmployees(selectedRowKeys as string[]);
                            },
                            getCheckboxProps: (record: any) => ({
                              name: record.user?.id || record.user_id || record.id,
                            }),
                          }
                        : undefined
                    }
                  />
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
        <div className="footer d-sm-flex align-items-center justify-content-between border-top bg-white p-3">
          <p className="mb-0">2025 © NeexQ</p>
          <p>
            Designed &amp; Developed By{" "}
            <Link to="#" className="text-primary">
              NeexQ
            </Link>
          </p>
        </div>
      </div>
      {/* /Page Wrapper */}
      {/* Add Company */}
      <div className="modal fade" id="add_company">
        <div className="modal-dialog modal-dialog-centered modal-lg">
          <div className="modal-content">
            <div className="modal-header">
              <h4 className="modal-title">Add New Company</h4>
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
                    <div className="d-flex align-items-center flex-wrap row-gap-3 bg-light w-100 rounded p-3 mb-4">
                      <div className="d-flex align-items-center justify-content-center avatar avatar-xxl rounded-circle border border-dashed me-2 flex-shrink-0 text-dark frames">
                        <ImageWithBasePath
                          src="assets/img/profiles/avatar-30.jpg"
                          alt="img"
                          className="rounded-circle"
                        />
                      </div>
                      <div className="profile-upload">
                        <div className="mb-2">
                          <h6 className="mb-1">Upload Profile Image</h6>
                          <p className="fs-12">Image should be below 4 mb</p>
                        </div>
                        <div className="profile-uploader d-flex align-items-center">
                          <div className="drag-upload-btn btn btn-sm btn-primary me-2">
                            Upload
                            <input
                              type="file"
                              className="form-control image-sign"
                              multiple
                            />
                          </div>
                          <Link to="#" className="btn btn-light btn-sm">
                            Cancel
                          </Link>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">
                        Name <span className="text-danger"> *</span>
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        value={organizationName}
                        onChange={(e) => setOrganizationName(e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">Email Address</label>
                      <input
                        type="email"
                        className="form-control"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                      />
                    </div>
                  </div>
                  {/* <div className="col-md-12">
                    <div className="mb-3">
                      <label className="form-label">Account URL</label>
                      <input type="text" className="form-control" />
                    </div>
                  </div> */}
                  {/* <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">
                        Phone Number <span className="text-danger"> *</span>
                      </label>
                      <input type="text" className="form-control" />
                    </div>
                  </div> */}
                  {/* <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">Website</label>
                      <input type="text" className="form-control" />
                    </div>
                  </div> */}
                  <div className="col-md-6">
                    <div className="mb-3 ">
                      <label className="form-label">
                        Password <span className="text-danger"> *</span>
                      </label>
                      <div className="pass-group">
                        <input
                          type={
                            passwordVisibility.password ? "text" : "password"
                          }
                          className="pass-input form-control"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                        />
                        <span
                          className={`ti toggle-passwords ${
                            passwordVisibility.password
                              ? "ti-eye"
                              : "ti-eye-off"
                          }`}
                          onClick={() => togglePasswordVisibility("password")}
                        ></span>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3 ">
                      <label className="form-label">
                        Confirm Password <span className="text-danger"> *</span>
                      </label>
                      <div className="pass-group">
                        <input
                          type={
                            passwordVisibility.confirmPassword
                              ? "text"
                              : "password"
                          }
                          className="pass-input form-control"
                        />
                        <span
                          className={`ti toggle-passwords ${
                            passwordVisibility.confirmPassword
                              ? "ti-eye"
                              : "ti-eye-off"
                          }`}
                          onClick={() =>
                            togglePasswordVisibility("confirmPassword")
                          }
                        ></span>
                      </div>
                    </div>
                  </div>
                  {/* <div className="col-md-12">
                    <div className="mb-3">
                      <label className="form-label">Address</label>
                      <input type="text" className="form-control" />
                    </div>
                  </div> */}
                  {/* <div className="col-md-6">
                    <div className="mb-3 ">
                      <label className="form-label">
                        Plan Name <span className="text-danger"> *</span>
                      </label>
                      <CommonSelect
                        className="select"
                        options={planName}
                        defaultValue={planName[0]}
                      />
                    </div>
                  </div> */}
                  {/* <div className="col-md-6">
                    <div className="mb-3 ">
                      <label className="form-label">
                        Plan Type <span className="text-danger"> *</span>
                      </label>
                      <CommonSelect
                        className="select"
                        options={planType}
                        defaultValue={planType[0]}
                      />
                    </div>
                  </div> */}
                  {/* <div className="col-md-4">
                    <div className="mb-3 ">
                      <label className="form-label">
                        Currency <span className="text-danger"> *</span>
                      </label>
                      <CommonSelect
                        className="select"
                        options={currency}
                        defaultValue={currency[0]}
                      />
                    </div>
                  </div> */}
                  {/* <div className="col-md-4">
                    <div className="mb-3 ">
                      <label className="form-label">
                        Language <span className="text-danger"> *</span>
                      </label>
                      <CommonSelect
                        className="select"
                        options={language}
                        defaultValue={language[0]}
                      />
                    </div>
                  </div> */}
                  {/* <div className="col-md-4">
                    <div className="mb-3 ">
                      <label className="form-label">Status</label>
                      <CommonSelect
                        className="select"
                        options={statusChoose}
                        defaultValue={statusChoose[0]}
                      />
                    </div>
                  </div> */}
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
                >
                  Add Company
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
      {/* /Add Company */}
      {/* Edit Company */}
      <div className="modal fade" id="edit_company">
        <div className="modal-dialog modal-dialog-centered modal-lg">
          <div className="modal-content">
            <div className="modal-header">
              <h4 className="modal-title">Edit Company</h4>
              <button
                type="button"
                className="btn-close custom-btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
              >
                <i className="ti ti-x" />
              </button>
            </div>
            <form action="companies.html">
              <div className="modal-body pb-0">
                <div className="row">
                  <div className="col-md-12">
                    <div className="d-flex align-items-center flex-wrap row-gap-3 bg-light w-100 rounded p-3 mb-4">
                      <div className="d-flex align-items-center justify-content-center avatar avatar-xxl rounded-circle border border-dashed me-2 flex-shrink-0 text-dark frames">
                        <ImageWithBasePath
                          src="assets/img/profiles/avatar-30.jpg"
                          alt="img"
                          className="rounded-circle"
                        />
                      </div>
                      <div className="profile-upload">
                        <div className="mb-2">
                          <h6 className="mb-1">Upload Profile Image</h6>
                          <p className="fs-12">Image should be below 4 mb</p>
                        </div>
                        <div className="profile-uploader d-flex align-items-center">
                          <div className="drag-upload-btn btn btn-sm btn-primary me-2">
                            Upload
                            <input
                              type="file"
                              className="form-control image-sign"
                              multiple
                            />
                          </div>
                          <Link to="#" className="btn btn-light btn-sm">
                            Cancel
                          </Link>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">
                        Name <span className="text-danger"> *</span>
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        defaultValue="Stellar Dynamics"
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">Email Address</label>
                      <input
                        type="email"
                        className="form-control"
                        defaultValue="sophie@example.com"
                      />
                    </div>
                  </div>
                  <div className="col-md-12">
                    <div className="mb-3">
                      <label className="form-label">Account URL</label>
                      <input
                        type="text"
                        className="form-control"
                        defaultValue="sd.example.com"
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">
                        Phone Number <span className="text-danger"> *</span>
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        defaultValue="+1 895455450"
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">Website</label>
                      <input
                        type="text"
                        className="form-control"
                        defaultValue="Admin Website"
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3 ">
                      <label className="form-label">
                        Password <span className="text-danger"> *</span>
                      </label>
                      <div className="pass-group">
                        <input
                          type={
                            passwordVisibility.password ? "text" : "password"
                          }
                          className="pass-input form-control"
                        />
                        <span
                          className={`ti toggle-passwords ${
                            passwordVisibility.password
                              ? "ti-eye"
                              : "ti-eye-off"
                          }`}
                          onClick={() => togglePasswordVisibility("password")}
                        ></span>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3 ">
                      <label className="form-label">
                        Confirm Password <span className="text-danger"> *</span>
                      </label>
                      <div className="pass-group">
                        <input
                          type={
                            passwordVisibility.confirmPassword
                              ? "text"
                              : "password"
                          }
                          className="pass-input form-control"
                        />
                        <span
                          className={`ti toggle-passwords ${
                            passwordVisibility.confirmPassword
                              ? "ti-eye"
                              : "ti-eye-off"
                          }`}
                          onClick={() =>
                            togglePasswordVisibility("confirmPassword")
                          }
                        ></span>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-12">
                    <div className="mb-3">
                      <label className="form-label">Address</label>
                      <input type="text" className="form-control" />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3 ">
                      <label className="form-label">
                        Plan Name <span className="text-danger"> *</span>
                      </label>
                      <CommonSelect
                        className="select"
                        options={planName}
                        defaultValue={planName[1]}
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3 ">
                      <label className="form-label">
                        Plan Type <span className="text-danger"> *</span>
                      </label>
                      <CommonSelect
                        className="select"
                        options={planType}
                        defaultValue={planType[1]}
                      />
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="mb-3 ">
                      <label className="form-label">
                        Currency <span className="text-danger"> *</span>
                      </label>
                      <CommonSelect
                        className="select"
                        options={currency}
                        defaultValue={currency[1]}
                      />
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="mb-3 ">
                      <label className="form-label">
                        Language <span className="text-danger"> *</span>
                      </label>
                      <CommonSelect
                        className="select"
                        options={language}
                        defaultValue={language[1]}
                      />
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="mb-3 ">
                      <label className="form-label">Status</label>
                      <CommonSelect
                        className="select"
                        options={statusChoose}
                        defaultValue={statusChoose[1]}
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
                  data-bs-dismiss="modal"
                  className="btn btn-primary"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
      {/* /Edit Company */}
      {/* Upgrade Information */}
      <div className="modal fade" id="upgrade_info">
        <div className="modal-dialog modal-dialog-centered modal-lg">
          <div className="modal-content">
            <div className="modal-header">
              <h4 className="modal-title">Upgrade Package</h4>
              <button
                type="button"
                className="btn-close custom-btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
              >
                <i className="ti ti-x" />
              </button>
            </div>
            <div className="p-3 mb-1">
              <div className="rounded bg-light p-3">
                <h5 className="mb-3">Current Plan Details</h5>
                <div className="row align-items-center">
                  <div className="col-md-4">
                    <div className="mb-3">
                      <p className="fs-12 mb-0">Employee Name</p>
                      <p className="text-gray-9">BrightWave Innovations</p>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="mb-3">
                      <p className="fs-12 mb-0">Plan Name</p>
                      <p className="text-gray-9">Advanced</p>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="mb-3">
                      <p className="fs-12 mb-0">Plan Type</p>
                      <p className="text-gray-9">Monthly</p>
                    </div>
                  </div>
                </div>
                <div className="row align-items-center">
                  <div className="col-md-4">
                    <div className="mb-3">
                      <p className="fs-12 mb-0">Price</p>
                      <p className="text-gray-9">200</p>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="mb-3">
                      <p className="fs-12 mb-0">Register Date</p>
                      <p className="text-gray-9">12 Sep 2024</p>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="mb-3">
                      <p className="fs-12 mb-0">Expiring On</p>
                      <p className="text-gray-9">11 Oct 2024</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <form action="companies.html">
              <div className="modal-body pb-0">
                <h5 className="mb-4">Change Plan</h5>
                <div className="row">
                  <div className="col-md-6">
                    <div className="mb-3 ">
                      <label className="form-label">
                        Plan Name <span className="text-danger">*</span>
                      </label>
                      <CommonSelect
                        className="select"
                        options={planName}
                        defaultValue={planName[0]}
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3 ">
                      <label className="form-label">
                        Plan Type <span className="text-danger">*</span>
                      </label>
                      <CommonSelect
                        className="select"
                        options={planType}
                        defaultValue={planType[0]}
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">
                        Ammount<span className="text-danger">*</span>
                      </label>
                      <input type="text" className="form-control" />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">
                        Payment Date <span className="text-danger">*</span>
                      </label>
                      <div className="input-icon-end position-relative">
                        <DatePicker
                          className="form-control datetimepicker"
                          format={{
                            format: "DD-MM-YYYY",
                            type: "mask",
                          }}
                          getPopupContainer={getModalContainer}
                          placeholder="DD-MM-YYYY"
                        />
                        <span className="input-icon-addon">
                          <i className="ti ti-calendar text-gray-7" />
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">
                        Next Payment Date <span className="text-danger">*</span>
                      </label>
                      <div className="input-icon-end position-relative">
                        <DatePicker
                          className="form-control datetimepicker"
                          format={{
                            format: "DD-MM-YYYY",
                            type: "mask",
                          }}
                          getPopupContainer={getModalContainer}
                          placeholder="DD-MM-YYYY"
                        />
                        <span className="input-icon-addon">
                          <i className="ti ti-calendar text-gray-7" />
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">
                        Expiring On <span className="text-danger">*</span>
                      </label>
                      <div className="input-icon-end position-relative">
                        <DatePicker
                          className="form-control datetimepicker"
                          format={{
                            format: "DD-MM-YYYY",
                            type: "mask",
                          }}
                          getPopupContainer={getModalContainer}
                          placeholder="DD-MM-YYYY"
                        />
                        <span className="input-icon-addon">
                          <i className="ti ti-calendar text-gray-7" />
                        </span>
                      </div>
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
                  data-bs-dismiss="modal"
                  className="btn btn-primary"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
      {/* /Upgrade Information */}
      {/* Company Detail */}
      <div className="modal fade" id="company_detail">
        <div className="modal-dialog modal-dialog-centered modal-lg">
          <div className="modal-content">
            <div className="modal-header">
              <h4 className="modal-title">Company Detail</h4>
              <button
                type="button"
                className="btn-close custom-btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
              >
                <i className="ti ti-x" />
              </button>
            </div>
            <div className="moday-body">
              <div className="p-3">
                <div className="d-flex justify-content-between align-items-center rounded bg-light p-3">
                  <div className="file-name-icon d-flex align-items-center">
                    <Link
                      to="#"
                      className="avatar avatar-md border rounded-circle flex-shrink-0 me-2"
                    >
                      <ImageWithBasePath
                        src="assets/img/company/company-01.svg"
                        className="img-fluid"
                        alt="img"
                      />
                    </Link>
                    <div>
                      <p className="text-gray-9 fw-medium mb-0">
                        BrightWave Innovations
                      </p>
                      <p>michael@example.com</p>
                    </div>
                  </div>
                  <span className="badge badge-success">
                    <i className="ti ti-point-filled" />
                    Active
                  </span>
                </div>
              </div>
              <div className="p-3">
                <p className="text-gray-9 fw-medium">Basic Info</p>
                <div className="pb-1 border-bottom mb-4">
                  <div className="row align-items-center">
                    <div className="col-md-4">
                      <div className="mb-3">
                        <p className="fs-12 mb-0">Account URL</p>
                        <p className="text-gray-9">bwi.example.com</p>
                      </div>
                    </div>
                    <div className="col-md-4">
                      <div className="mb-3">
                        <p className="fs-12 mb-0">Phone Number</p>
                        <p className="text-gray-9">(163) 2459 315</p>
                      </div>
                    </div>
                    <div className="col-md-4">
                      <div className="mb-3">
                        <p className="fs-12 mb-0">Website</p>
                        <p className="text-gray-9">www.exmple.com</p>
                      </div>
                    </div>
                  </div>
                  <div className="row align-items-center">
                    <div className="col-md-4">
                      <div className="mb-3">
                        <p className="fs-12 mb-0">Currency</p>
                        <p className="text-gray-9">
                          United Stated Dollar (USD)
                        </p>
                      </div>
                    </div>
                    <div className="col-md-4">
                      <div className="mb-3">
                        <p className="fs-12 mb-0">Language</p>
                        <p className="text-gray-9">English</p>
                      </div>
                    </div>
                    <div className="col-md-4">
                      <div className="mb-3">
                        <p className="fs-12 mb-0">Addresss</p>
                        <p className="text-gray-9">
                          3705 Lynn Avenue, Phelps, WI 54554
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                <p className="text-gray-9 fw-medium">Plan Details</p>
                <div>
                  <div className="row align-items-center">
                    <div className="col-md-4">
                      <div className="mb-3">
                        <p className="fs-12 mb-0">Plan Name</p>
                        <p className="text-gray-9">Advanced</p>
                      </div>
                    </div>
                    <div className="col-md-4">
                      <div className="mb-3">
                        <p className="fs-12 mb-0">Plan Type</p>
                        <p className="text-gray-9">Monthly</p>
                      </div>
                    </div>
                    <div className="col-md-4">
                      <div className="mb-3">
                        <p className="fs-12 mb-0">Price</p>
                        <p className="text-gray-9">$200</p>
                      </div>
                    </div>
                  </div>
                  <div className="row align-items-center">
                    <div className="col-md-4">
                      <div className="mb-3">
                        <p className="fs-12 mb-0">Register Date</p>
                        <p className="text-gray-9">12 Sep 2024</p>
                      </div>
                    </div>
                    <div className="col-md-4">
                      <div className="mb-3">
                        <p className="fs-12 mb-0">Expiring On</p>
                        <p className="text-gray-9">11 Oct 2024</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* /Company Detail */}

      {/* Add Employee Modal */}
      <div className="modal fade" id="add_employee">
        <div className="modal-dialog modal-dialog-centered modal-lg">
          <div className="modal-content">
            <div className="modal-header">
              <h4 className="modal-title">Add New Employee</h4>
              <button
                type="button"
                className="btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
              ></button>
            </div>
            <div className="modal-body">
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  setSubmitting(true);
                  try {
                    const token = sessionStorage.getItem("access_token");
                    if (!token) {
                      toast.error("Please login again");
                      setSubmitting(false);
                      return;
                    }

                    // Validate required fields
                    if (!employeeForm.user_name.trim()) {
                      toast.error("Employee Name is required");
                      setSubmitting(false);
                      return;
                    }
                    if (!employeeForm.custom_employee_id.trim()) {
                      toast.error("Employee ID is required");
                      setSubmitting(false);
                      return;
                    }
                    if (!employeeForm.email.trim()) {
                      toast.error("Email is required");
                      setSubmitting(false);
                      return;
                    }
                    if (!employeeForm.username.trim()) {
                      toast.error("Username is required");
                      setSubmitting(false);
                      return;
                    }
                    if (!employeeForm.password.trim()) {
                      toast.error("Password is required");
                      setSubmitting(false);
                      return;
                    }
                    if (!employeeForm.phone_number.trim()) {
                      toast.error("Phone Number is required");
                      setSubmitting(false);
                      return;
                    }
                    if (!employeeForm.date_of_joining.trim()) {
                      toast.error("Date of Joining is required");
                      setSubmitting(false);
                      return;
                    }
                    if (!employeeForm.gender.trim()) {
                      toast.error("Gender is required");
                      setSubmitting(false);
                      return;
                    }

                    // Get role from sessionStorage
                    const role = sessionStorage.getItem("role");
                    
                    // Build payload
                    const payload: any = {
                      user: {
                        email: employeeForm.email,
                        username: employeeForm.username,
                        password: employeeForm.password,
                        phone_number: employeeForm.phone_number,
                      },
                      user_name: employeeForm.user_name,
                      custom_employee_id: employeeForm.custom_employee_id,
                      phone_number: employeeForm.phone_number,
                      date_of_birth: employeeForm.date_of_birth || null,
                      date_of_joining: employeeForm.date_of_joining,
                      gender: employeeForm.gender,
                      designation: employeeForm.designation || "",
                      job_title: employeeForm.job_title || "",
                    };

                    // If role is organization, add admin_id to payload
                    if (role === "organization") {
                      const admin_id = getAdminIdForApi();
                      if (!admin_id) {
                        toast.error("Please select an admin first from the dashboard.");
                        setSubmitting(false);
                        return;
                      }
                      payload.admin_id = admin_id;
                    }

                    const response = await axios.post(
                      `${BACKEND_PATH}register/user`,
                      payload,
                      {
                        headers: {
                          Authorization: `Bearer ${token}`,
                        },
                      }
                    );

                    toast.success("Employee registered successfully!");
                    // Reset form
                    setEmployeeForm({
                      user_name: "",
                      email: "",
                      username: "",
                      password: "",
                      custom_employee_id: "",
                      phone_number: "",
                      date_of_birth: "",
                      date_of_joining: "",
                      gender: "",
                      designation: "",
                      job_title: "",
                    });
                    // Close modal
                    const modal = document.getElementById("add_employee");
                    if (modal) {
                      const bsModal = (window as any).bootstrap?.Modal?.getInstance(modal);
                      if (bsModal) {
                        bsModal.hide();
                      }
                    }
                    // Refresh employee list
                    window.location.reload();
                  } catch (error: any) {
                    console.error("Error registering employee:", error);
                    console.error("Error response:", error.response?.data);
                    
                    let errorMessage = "Failed to register employee";
                    
                    if (error.response?.data) {
                      const errorData = error.response.data;
                      
                      // Handle DRF validation errors
                      if (errorData.user) {
                        // Nested user errors (email, username, phone_number, etc.)
                        const userErrors = [];
                        if (errorData.user.email) userErrors.push(`Email: ${Array.isArray(errorData.user.email) ? errorData.user.email[0] : errorData.user.email}`);
                        if (errorData.user.username) userErrors.push(`Username: ${Array.isArray(errorData.user.username) ? errorData.user.username[0] : errorData.user.username}`);
                        if (errorData.user.phone_number) userErrors.push(`Phone Number: ${Array.isArray(errorData.user.phone_number) ? errorData.user.phone_number[0] : errorData.user.phone_number}`);
                        if (errorData.user.password) userErrors.push(`Password: ${Array.isArray(errorData.user.password) ? errorData.user.password[0] : errorData.user.password}`);
                        if (userErrors.length > 0) {
                          errorMessage = userErrors.join(", ");
                        }
                      }
                      
                      // Handle top-level field errors (including admin_id)
                      if (!errorMessage || errorMessage === "Failed to register employee") {
                        const fieldErrors = [];
                        if (errorData.custom_employee_id) fieldErrors.push(`Employee ID: ${Array.isArray(errorData.custom_employee_id) ? errorData.custom_employee_id[0] : errorData.custom_employee_id}`);
                        if (errorData.user_name) fieldErrors.push(`Name: ${Array.isArray(errorData.user_name) ? errorData.user_name[0] : errorData.user_name}`);
                        if (errorData.admin_id) fieldErrors.push(`Admin ID: ${Array.isArray(errorData.admin_id) ? errorData.admin_id[0] : errorData.admin_id}`);
                        if (errorData.admin) fieldErrors.push(`Admin: ${Array.isArray(errorData.admin) ? errorData.admin[0] : errorData.admin}`);
                        if (errorData.non_field_errors) fieldErrors.push(Array.isArray(errorData.non_field_errors) ? errorData.non_field_errors[0] : errorData.non_field_errors);
                        if (fieldErrors.length > 0) {
                          errorMessage = fieldErrors.join(", ");
                        }
                      }
                      
                      // Handle general error messages
                      if (!errorMessage || errorMessage === "Failed to register employee") {
                        if (errorData.detail) {
                          errorMessage = errorData.detail;
                        } else if (errorData.message) {
                          errorMessage = errorData.message;
                        } else if (errorData.error) {
                          errorMessage = errorData.error;
                        } else if (typeof errorData === 'string') {
                          errorMessage = errorData;
                        } else if (Array.isArray(errorData)) {
                          errorMessage = errorData.join(", ");
                        }
                      }
                    } else if (error.message) {
                      errorMessage = error.message;
                    }
                    
                    toast.error(errorMessage);
                  } finally {
                    setSubmitting(false);
                  }
                }}
              >
                <div className="row">
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">
                        Employee Name <span className="text-danger">*</span>
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        value={employeeForm.user_name}
                        onChange={(e) =>
                          setEmployeeForm({ ...employeeForm, user_name: e.target.value })
                        }
                        required
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">
                        Employee ID <span className="text-danger">*</span>
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        value={employeeForm.custom_employee_id}
                        onChange={(e) =>
                          setEmployeeForm({ ...employeeForm, custom_employee_id: e.target.value })
                        }
                        required
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">
                        Email <span className="text-danger">*</span>
                      </label>
                      <input
                        type="email"
                        className="form-control"
                        value={employeeForm.email}
                        onChange={(e) =>
                          setEmployeeForm({ ...employeeForm, email: e.target.value })
                        }
                        required
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">
                        Username <span className="text-danger">*</span>
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        value={employeeForm.username}
                        onChange={(e) =>
                          setEmployeeForm({ ...employeeForm, username: e.target.value })
                        }
                        required
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">
                        Password <span className="text-danger">*</span>
                      </label>
                      <div className="pass-group">
                        <input
                          type={employeePasswordVisibility ? "text" : "password"}
                          className="pass-input form-control"
                          value={employeeForm.password}
                          onChange={(e) =>
                            setEmployeeForm({ ...employeeForm, password: e.target.value })
                          }
                          required
                        />
                        <span
                          className={`ti toggle-passwords ${
                            employeePasswordVisibility ? "ti-eye" : "ti-eye-off"
                          }`}
                          onClick={() => setEmployeePasswordVisibility(!employeePasswordVisibility)}
                        ></span>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">
                        Phone Number <span className="text-danger">*</span>
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        value={employeeForm.phone_number}
                        onChange={(e) =>
                          setEmployeeForm({ ...employeeForm, phone_number: e.target.value })
                        }
                        required
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">Date of Birth</label>
                      <input
                        type="date"
                        className="form-control"
                        value={employeeForm.date_of_birth}
                        onChange={(e) =>
                          setEmployeeForm({ ...employeeForm, date_of_birth: e.target.value })
                        }
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">
                        Date of Joining <span className="text-danger">*</span>
                      </label>
                      <input
                        type="date"
                        className="form-control"
                        value={employeeForm.date_of_joining}
                        onChange={(e) =>
                          setEmployeeForm({ ...employeeForm, date_of_joining: e.target.value })
                        }
                        required
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">
                        Gender <span className="text-danger">*</span>
                      </label>
                      <select
                        className="form-select"
                        value={employeeForm.gender}
                        onChange={(e) =>
                          setEmployeeForm({ ...employeeForm, gender: e.target.value })
                        }
                        required
                      >
                        <option value="">Select Gender</option>
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">Designation</label>
                      <input
                        type="text"
                        className="form-control"
                        value={employeeForm.designation}
                        onChange={(e) =>
                          setEmployeeForm({ ...employeeForm, designation: e.target.value })
                        }
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">Job Title</label>
                      <input
                        type="text"
                        className="form-control"
                        value={employeeForm.job_title}
                        onChange={(e) =>
                          setEmployeeForm({ ...employeeForm, job_title: e.target.value })
                        }
                      />
                    </div>
                  </div>
                </div>
                <div className="modal-footer">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    data-bs-dismiss="modal"
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={submitting}>
                    {submitting ? "Registering..." : "Register Employee"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
      {/* /Add Employee Modal */}

      {/* Bulk Register Employees Modal */}
      {showBulkUploadModal && (
        <>
          <div
            className="modal fade show"
            id="bulk_upload_modal"
            style={{ display: 'block', paddingRight: '17px' }}
            tabIndex={-1}
            aria-modal="true"
            role="dialog"
          >
            <div className="modal-dialog modal-dialog-centered modal-lg">
              <div className="modal-content">
                <div className="modal-header">
                  <h4 className="modal-title">Bulk Register Employees</h4>
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => {
                      setShowBulkUploadModal(false);
                      setBulkUploadFile(null);
                      setUploadProgress("");
                    }}
                    aria-label="Close"
                  ></button>
                </div>
                <div className="modal-body">
                  <div className="mb-4">
                    <div className="d-flex justify-content-between align-items-center mb-3">
                      <h5 className="mb-0">Upload CSV/Excel File</h5>
                      <button
                        type="button"
                        onClick={handleDownloadSampleCSV}
                        className="btn btn-outline-primary btn-sm d-flex align-items-center"
                      >
                        <i className="ti ti-download me-2" />
                        Download Sample CSV
                      </button>
                    </div>
                    <p className="text-muted mb-3">
                      Upload a CSV or Excel file with employee details. Maximum file size: 10MB
                    </p>
                    <div className="mb-3">
                      <label className="form-label">Select File (CSV or Excel)</label>
                      <input
                        type="file"
                        className="form-control"
                        accept=".csv,.xlsx,.xls"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) {
                            // Validate file size (10MB)
                            if (file.size > 10 * 1024 * 1024) {
                              toast.error("File size exceeds 10MB limit");
                              return;
                            }
                            // Validate file type
                            const fileExtension = file.name.split('.').pop()?.toLowerCase();
                            if (!['csv', 'xlsx', 'xls'].includes(fileExtension || '')) {
                              toast.error("Please upload a CSV or Excel file");
                              return;
                            }
                            setBulkUploadFile(file);
                          }
                        }}
                      />
                      {bulkUploadFile && (
                        <div className="mt-2">
                          <span className="badge bg-success">
                            <i className="ti ti-file me-1" />
                            {bulkUploadFile.name} ({(bulkUploadFile.size / 1024).toFixed(2)} KB)
                          </span>
                        </div>
                      )}
                    </div>
                    {uploadProgress && (
                      <div className="alert alert-info">
                        <i className="ti ti-info-circle me-2" />
                        {uploadProgress}
                      </div>
                    )}
                    <div className="alert alert-warning">
                      <i className="ti ti-alert-triangle me-2" />
                      <strong>Important:</strong> Make sure your file matches the sample format. 
                      Required fields: email, user_name, custom_employee_id
                    </div>
                  </div>
                </div>
                <div className="modal-footer">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => {
                      setShowBulkUploadModal(false);
                      setBulkUploadFile(null);
                      setUploadProgress("");
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleBulkUpload}
                    disabled={!bulkUploadFile || isUploading}
                  >
                    {isUploading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        Uploading...
                      </>
                    ) : (
                      <>
                        <i className="ti ti-upload me-2" />
                        Upload & Register
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div className="modal-backdrop fade show"></div>
        </>
      )}
      {/* /Bulk Register Employees Modal */}

      {/* Edit Employee Modal */}
      {showEditEmployeeModal && editingEmployee && (
        <>
          <div
            className="modal fade show"
            id="edit_employee_modal"
            tabIndex={-1}
            aria-labelledby="edit_employee_modal_label"
            aria-modal="true"
            role="dialog"
            style={{ display: "block", paddingRight: "17px" }}
          >
            <div className="modal-dialog modal-lg modal-dialog-centered">
              <div className="modal-content">
                <div className="modal-header">
                  <h4 className="modal-title" id="edit_employee_modal_label">
                    Edit Employee
                  </h4>
                  <button
                    type="button"
                    className="btn-close"
                    onClick={handleCloseEditEmployeeModal}
                    aria-label="Close"
                  ></button>
                </div>
                <div className="modal-body">
                  <form onSubmit={(e) => { e.preventDefault(); handleUpdateEmployee(); }}>
                    <div className="row">
                      <div className="col-md-6">
                        <div className="mb-3">
                          <label className="form-label">
                            Employee Name <span className="text-danger">*</span>
                          </label>
                          <input
                            type="text"
                            className="form-control"
                            value={editEmployeeForm.user_name}
                            onChange={(e) =>
                              setEditEmployeeForm({ ...editEmployeeForm, user_name: e.target.value })
                            }
                            required
                          />
                        </div>
                      </div>
                      <div className="col-md-6">
                        <div className="mb-3">
                          <label className="form-label">
                            Employee ID <span className="text-danger">*</span>
                          </label>
                          <input
                            type="text"
                            className="form-control"
                            value={editEmployeeForm.custom_employee_id}
                            onChange={(e) =>
                              setEditEmployeeForm({ ...editEmployeeForm, custom_employee_id: e.target.value })
                            }
                            required
                          />
                        </div>
                      </div>
                      <div className="col-md-6">
                        <div className="mb-3">
                          <label className="form-label">
                            Email <span className="text-danger">*</span>
                          </label>
                          <input
                            type="email"
                            className="form-control"
                            value={editEmployeeForm.email}
                            onChange={(e) =>
                              setEditEmployeeForm({ ...editEmployeeForm, email: e.target.value })
                            }
                            required
                          />
                        </div>
                      </div>
                      <div className="col-md-6">
                        <div className="mb-3">
                          <label className="form-label">
                            Username <span className="text-danger">*</span>
                          </label>
                          <input
                            type="text"
                            className="form-control"
                            value={editEmployeeForm.username}
                            onChange={(e) =>
                              setEditEmployeeForm({ ...editEmployeeForm, username: e.target.value })
                            }
                            required
                          />
                        </div>
                      </div>
                      <div className="col-md-6">
                        <div className="mb-3">
                          <label className="form-label">
                            Phone Number <span className="text-danger">*</span>
                          </label>
                          <input
                            type="text"
                            className="form-control"
                            value={editEmployeeForm.phone_number}
                            onChange={(e) =>
                              setEditEmployeeForm({ ...editEmployeeForm, phone_number: e.target.value })
                            }
                            required
                          />
                        </div>
                      </div>
                      <div className="col-md-6">
                        <div className="mb-3">
                          <label className="form-label">Date of Birth</label>
                          <input
                            type="date"
                            className="form-control"
                            value={editEmployeeForm.date_of_birth}
                            onChange={(e) =>
                              setEditEmployeeForm({ ...editEmployeeForm, date_of_birth: e.target.value })
                            }
                          />
                        </div>
                      </div>
                      <div className="col-md-6">
                        <div className="mb-3">
                          <label className="form-label">Date of Joining</label>
                          <input
                            type="date"
                            className="form-control"
                            value={editEmployeeForm.date_of_joining}
                            onChange={(e) =>
                              setEditEmployeeForm({ ...editEmployeeForm, date_of_joining: e.target.value })
                            }
                          />
                        </div>
                      </div>
                      <div className="col-md-6">
                        <div className="mb-3">
                          <label className="form-label">Gender</label>
                          <select
                            className="form-control"
                            value={editEmployeeForm.gender}
                            onChange={(e) =>
                              setEditEmployeeForm({ ...editEmployeeForm, gender: e.target.value })
                            }
                          >
                            <option value="">Select Gender</option>
                            <option value="Male">Male</option>
                            <option value="Female">Female</option>
                            <option value="Other">Other</option>
                          </select>
                        </div>
                      </div>
                      <div className="col-md-6">
                        <div className="mb-3">
                          <label className="form-label">Designation</label>
                          <input
                            type="text"
                            className="form-control"
                            value={editEmployeeForm.designation}
                            onChange={(e) =>
                              setEditEmployeeForm({ ...editEmployeeForm, designation: e.target.value })
                            }
                          />
                        </div>
                      </div>
                      <div className="col-md-6">
                        <div className="mb-3">
                          <label className="form-label">Job Title</label>
                          <input
                            type="text"
                            className="form-control"
                            value={editEmployeeForm.job_title}
                            onChange={(e) =>
                              setEditEmployeeForm({ ...editEmployeeForm, job_title: e.target.value })
                            }
                          />
                        </div>
                      </div>
                      <div className="col-md-6">
                        <div className="mb-3">
                          <label className="form-label">Status</label>
                          <div>
                            <label className="form-check form-switch">
                              <input
                                className="form-check-input"
                                type="checkbox"
                                checked={editEmployeeForm.is_active}
                                onChange={(e) =>
                                  setEditEmployeeForm({ ...editEmployeeForm, is_active: e.target.checked })
                                }
                              />
                              <span className="form-check-label">
                                {editEmployeeForm.is_active ? "Active" : "Inactive"}
                              </span>
                            </label>
                          </div>
                        </div>
                      </div>
                    </div>
                  </form>
                </div>
                <div className="modal-footer">
                  <button
                    type="button"
                    className="btn btn-light me-2"
                    onClick={handleCloseEditEmployeeModal}
                    disabled={isUpdatingEmployee}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleUpdateEmployee}
                    disabled={isUpdatingEmployee}
                  >
                    {isUpdatingEmployee ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" />
                        Updating...
                      </>
                    ) : (
                      <>
                        <i className="ti ti-check me-2" />
                        Update Employee
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div
            className="modal-backdrop fade show"
            onClick={handleCloseEditEmployeeModal}
          ></div>
        </>
      )}
      {/* /Edit Employee Modal */}

      {/* Assign Leave Modal */}
      <AssignLeaveModal
        employee={selectedEmployeeForLeave}
        onLeaveAssigned={(result) => {
          toast.success("Leaves assigned successfully!");
          setSelectedEmployeeForLeave(null);
          // Optionally refresh employee data here if needed
        }}
        onClose={() => setSelectedEmployeeForLeave(null)}
        onOpenLeaveApplications={() => {
          // Open leave applications sidebar for the same employee
          setSelectedEmployeeForLeaveApps(selectedEmployeeForLeave);
          setIsLeaveAppsSidebarOpen(true);
        }}
        onOpenApplyLeave={() => {
          // Set employee for apply leave modal
          setSelectedEmployeeForApplyLeave(selectedEmployeeForLeave);
        }}
      />
      {/* /Assign Leave Modal */}

      {/* Apply Leave Modal */}
      <ApplyLeaveModal
        employee={selectedEmployeeForApplyLeave}
        onLeaveApplied={() => {
          toast.success("Leave applied successfully!");
          setSelectedEmployeeForApplyLeave(null);
          // Optionally refresh employee data here if needed
        }}
      />
      {/* /Apply Leave Modal */}

      {/* Assign Shift Modal */}
      <AssignShiftModal
        employee={selectedEmployeeForShift}
        onShiftAssigned={(result) => {
          toast.success("Shifts assigned successfully!");
          setSelectedEmployeeForShift(null);
          // Optionally refresh employee data here if needed
        }}
        onClose={() => setSelectedEmployeeForShift(null)}
      />
      {/* /Assign Shift Modal */}

      {/* Assign Location Modal */}
      <AssignLocationModal
        employee={selectedEmployeeForLocation}
        onLocationAssigned={(result) => {
          toast.success("Locations assigned successfully!");
          setSelectedEmployeeForLocation(null);
          // Optionally refresh employee data here if needed
        }}
        onClose={() => setSelectedEmployeeForLocation(null)}
      />
      {/* /Assign Location Modal */}

      {/* Assign Week Off Modal */}
      <AssignWeekOffModal
        employee={selectedEmployeeForWeekOff}
        onWeekOffAssigned={(result) => {
          toast.success("Week offs assigned successfully!");
          setSelectedEmployeeForWeekOff(null);
          // Optionally refresh employee data here if needed
        }}
        onClose={() => setSelectedEmployeeForWeekOff(null)}
      />
      {/* /Assign Week Off Modal */}

      {/* Leave Applications Sidebar */}
      <LeaveApplicationsSidebar
        isOpen={isLeaveAppsSidebarOpen}
        onClose={() => {
          setIsLeaveAppsSidebarOpen(false);
          setSelectedEmployeeForLeaveApps(null);
        }}
        employeeId={selectedEmployeeForLeaveApps?.user?.id || selectedEmployeeForLeaveApps?.user_id}
        employeeName={selectedEmployeeForLeaveApps?.user_name}
      />
      {/* /Leave Applications Sidebar */}

      <ToastContainer position="top-right" autoClose={3000} />
    </>
  );
};

export default Companies;
