import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { all_routes } from '../../router/all_routes';
import ImageWithBasePath from '../../../core/common/imageWithBasePath';
import CommonSelect from '../../../core/common/commonSelect';
import { DatePicker, TimePicker, Table as AntTable } from 'antd';
import type { Dayjs } from 'dayjs';
import CollapseHeader from '../../../core/common/collapse-header/collapse-header';
import dayjs from "dayjs";
import axios from "axios";
import { img_path } from '../../../environment';
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { getAdminIdForApi } from '../../../core/utils/apiHelpers';

const AttendanceAdmin = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(dayjs());
  const [statusFilter, setStatusFilter] = useState("");
  const [editingAttendance, setEditingAttendance] = useState<any>(null);
  const [editingEntry, setEditingEntry] = useState<any>(null);
  const [editEntryModalVisible, setEditEntryModalVisible] = useState(false);
  const [editEntryForm, setEditEntryForm] = useState<{
    check_in_time: Dayjs | null;
    check_out_time: Dayjs | null;
  }>({
    check_in_time: null,
    check_out_time: null,
  });
  const [summary, setSummary] = useState({
    present: 0,
    late_login: 0,
    absent: 0,
  });

  const fetchAttendanceData = useCallback(async () => {
    setLoading(true);
    try {
      // Use utility function to get correct admin_id based on role
      // For organization: returns selected_admin_id (admin selected in dashboard)
      // For admin: returns user_id
      const admin_id = getAdminIdForApi();
      
      if (!admin_id) {
        const role = sessionStorage.getItem("role");
        console.error("Admin ID not found in session storage.");
        if (role === "organization") {
          toast.error("Please select an admin first from the dashboard.");
        } else {
          toast.error("Admin ID not found. Please login again.");
        }
        setLoading(false);
        return;
      }

      const dateParam = selectedDate.format("YYYY-MM-DD");
      let url = `http://127.0.0.1:8000/api/employee-attendance/${admin_id}?date=${dateParam}`;
      if (statusFilter) {
        url += `&status=${statusFilter.toLowerCase()}`;
      } 
      const token = sessionStorage.getItem("access_token");
      const response = await axios.get(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const jsonData = response.data;



      if (jsonData && jsonData.data && jsonData.data.length > 0) {
        console.log(jsonData.data);
        const mappedData = jsonData.data.map((item: any) => ({
          Employee: item.employee_name,
          Role: 'Employee',
          Image: item.employee_image || 'avatar-02.jpg',
          Status: item.attendance_status.charAt(0).toUpperCase() + item.attendance_status.slice(1),
          CheckIn: item.check_in ? new Date(item.check_in).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }) : '-',
          CheckOut: item.check_out ? new Date(item.check_out).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }) : '-',
          Break: item.break_duration,
          Late: item.late_minutes_display,
          ProductionHours: item.production_hours,
          ShiftName: item.shift_name,
          employee_id: item.employee_id,
          user_id: item.user_id,  // Add user_id UUID for edit API
          multiple_entries: item.multiple_entries || [],
        }));
        setData(mappedData);
    } else {
        // Clear data if empty
        setData([]);
      }

      if (jsonData && jsonData.summary) {
        setSummary(jsonData.summary);
      }
    } catch (error) {
      console.error("Error fetching attendance data:", error);
    } finally {
      setLoading(false);
    }
  }, [selectedDate, statusFilter]);

  useEffect(() => {
    fetchAttendanceData();
  }, [fetchAttendanceData, selectedDate, statusFilter]);

  // Helper function to get user initials
  const getUserInitials = (name: string) => {
    if (!name) return 'U';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  // Helper function to get avatar color based on name
  const getAvatarColor = (name: string) => {
    const colors = [
      'bg-primary',
      'bg-success',
      'bg-info',
      'bg-warning',
      'bg-danger',
      'bg-secondary',
    ];
    if (!name) return colors[0];
    const index = name.charCodeAt(0) % colors.length;
    return colors[index];
  };

  // Component for user avatar with fallback
  const UserAvatar = ({ image, name }: { image: string; name: string }) => {
    const [imageError, setImageError] = useState(false);
    const hasValidImage = image && image.trim() !== '' && image !== 'avatar-02.jpg' && !imageError;
    const initials = getUserInitials(name);
    const avatarColor = getAvatarColor(name);

    return (
      <Link to="#" className="avatar avatar-md border avatar-rounded" style={{ position: 'relative', overflow: 'hidden' }}>
        {hasValidImage ? (
          <img
            src={`${img_path}assets/img/users/${image}`}
            className="img-fluid"
            alt={name}
            onError={() => setImageError(true)}
            style={{ display: imageError ? 'none' : 'block', width: '100%', height: '100%', objectFit: 'cover' }}
          />
        ) : null}
        <span 
          className={`${avatarColor} text-fixed-white d-flex align-items-center justify-content-center`} 
          style={{ 
            position: hasValidImage && !imageError ? 'absolute' : 'relative',
            top: 0,
            left: 0,
            width: '100%', 
            height: '100%', 
            fontSize: '0.8rem', 
            fontWeight: '600',
            borderRadius: '50%',
            display: hasValidImage && !imageError ? 'none' : 'flex'
          }}
        >
          {initials}
        </span>
      </Link>
    );
  };

  const columns = [
    {
      title: "Employee",
      dataIndex: "Employee",
      render: (text: String, record: any) => (
        <div className="d-flex align-items-center file-name-icon">
          <UserAvatar image={record.Image} name={record.Employee} />
          <div className="ms-2">
            <h6 className="fw-medium">
              <Link to="#">{record.Employee}</Link>
            </h6>
            <span className="fs-12 fw-normal ">{record.Role}</span>
          </div>
        </div>
      ),
      sorter: (a: any, b: any) => a.Employee.length - b.Employee.length,
    },
    {
      title: "Status",
      dataIndex: "Status",
      render: (text: String, record: any) => (
        <span className={`badge ${text === 'Present' ? 'badge-success-transparent' : 'badge-danger-transparent'} d-inline-flex align-items-center`}>
          <i className="ti ti-point-filled me-1" />
          {record.Status}
        </span>

      ),
      sorter: (a: any, b: any) => a.Status.length - b.Status.length,
    },
    {
      title: "Check In",
      dataIndex: "CheckIn",
      sorter: (a: any, b: any) => a.CheckIn.length - b.CheckIn.length,
    },
    {
      title: "Check Out",
      dataIndex: "CheckOut",
      sorter: (a: any, b: any) => a.CheckOut.length - b.CheckOut.length,
    },
    {
      title: "Break",
      dataIndex: "Break",
      sorter: (a: any, b: any) => a.Break.length - b.Break.length,
    },
    {
      title: "Late",
      dataIndex: "Late",
      sorter: (a: any, b: any) => a.Late.length - b.Late.length,
    },
    {
      title: "Production Hours",
      dataIndex: "ProductionHours",
      render: (text: String, record: any) => (
        <span className={`badge d-inline-flex align-items-center badge-sm ${record.ProductionHours < '8.00'
          ? 'badge-danger'
          : record.ProductionHours >= '8.00' && record.ProductionHours <= '9.00'
            ? 'badge-success'
            : 'badge-info'
          }`}
        >
          <i className="ti ti-clock-hour-11 me-1"></i>{record.ProductionHours}
        </span>
      ),
      sorter: (a: any, b: any) => a.ProductionHours.length - b.ProductionHours.length,
    },
    {
      title: "Assign Shift",
      dataIndex: "ShiftName",
      render: (text: string, record: any) => (
        <span>{record.ShiftName || '-'}</span>
      ),
      sorter: (a: any, b: any) => {
        const aShift = a.ShiftName || '';
        const bShift = b.ShiftName || '';
        return aShift.length - bShift.length;
      },
    },
  ]
  const statusChoose = [
    { value: "Select", label: "Select" },
    { value: "Present", label: "Present" },
    { value: "Absent", label: "Absent" },
  ];

  const getModalContainer = () => {
    const modalElement = document.getElementById('modal-datepicker');
    return modalElement ? modalElement : document.body; // Fallback to document.body if modalElement is null
  };
  const getModalContainer2 = () => {
    const modalElement = document.getElementById('modal_datepicker');
    return modalElement ? modalElement : document.body; // Fallback to document.body if modalElement is null
  };

  const handleEditEntry = (entry: any, userId: string) => {
    setEditingEntry({ ...entry, user_id: userId });
    setEditEntryForm({
      check_in_time: entry.check_in_time ? dayjs(entry.check_in_time) : null,
      check_out_time: entry.check_out_time ? dayjs(entry.check_out_time) : null,
    });
    setEditEntryModalVisible(true);
  };

  const handleExportExcel = async () => {
    try {
      const admin_id = getAdminIdForApi();
      if (!admin_id) {
        toast.error("Admin ID not found. Please select an admin first.");
        return;
      }

      const dateParam = selectedDate.format("YYYY-MM-DD");
      const token = sessionStorage.getItem("access_token");
      
      const url = `http://127.0.0.1:8000/api/employee-attendance/${admin_id}?date=${dateParam}&export=true`;
      
      const response = await axios.get(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        responseType: 'blob', // Important for file download
      });

      // Create a blob from the response
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });

      // Create a temporary URL and trigger download
      const url_blob = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url_blob;
      link.setAttribute('download', `attendance_${dateParam}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url_blob);

      toast.success("Excel report downloaded successfully!");
    } catch (error: any) {
      console.error("Error exporting attendance:", error);
      const errorMessage = error.response?.data?.message || "Failed to export attendance. Please try again.";
      toast.error(errorMessage);
    }
  };

  const handleSaveEntry = async () => {
    if (!editingEntry) return;

    // Validation: Check if check_out_time is before check_in_time
    if (editEntryForm.check_in_time && editEntryForm.check_out_time) {
      if (editEntryForm.check_out_time.isBefore(editEntryForm.check_in_time)) {
        toast.error("Check out time cannot be before check in time!");
        return;
      }
    }

    try {
      const token = sessionStorage.getItem("access_token");
      const payload: any = {};
      
      if (editEntryForm.check_in_time) {
        payload.check_in_time = editEntryForm.check_in_time.format("YYYY-MM-DD HH:mm:ss");
      }
      if (editEntryForm.check_out_time) {
        payload.check_out_time = editEntryForm.check_out_time.format("YYYY-MM-DD HH:mm:ss");
      }

      const response = await axios.put(
        `http://127.0.0.1:8000/api/edit-attendance/${editingEntry.user_id}/${editingEntry.id}`,
        payload,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.data.status === 200) {
        toast.success("Attendance entry updated successfully!");
        setEditEntryModalVisible(false);
        setEditingEntry(null);
        setEditEntryForm({ check_in_time: null, check_out_time: null });
        // Refresh the data
        fetchAttendanceData();
      }
    } catch (error: any) {
      console.error("Error updating attendance entry:", error);
      const errorMessage = error.response?.data?.message || "Failed to update attendance entry. Please try again.";
      toast.error(errorMessage);
    }
  };

  const expandedRowRender = (record: any) => {
    const entryColumns = [
      { 
        title: 'Check In Time', 
        dataIndex: 'check_in_time', 
        key: 'check_in_time', 
        render: (text:string) => text ? new Date(text).toLocaleString() : '-' 
      },
      { 
        title: 'Check Out Time', 
        dataIndex: 'check_out_time', 
        key: 'check_out_time', 
        render: (text:string) => text ? new Date(text).toLocaleString() : '-' 
      },
      { 
        title: 'Working Minutes', 
        dataIndex: 'total_working_minutes', 
        key: 'total_working_minutes',
        render: (text: number) => text ? `${text} min` : '-'
      },
      { 
        title: 'Remarks', 
        dataIndex: 'remarks', 
        key: 'remarks', 
        render: (text:string) => text || '-' 
      },
      {
        title: 'Action',
        key: 'action',
        render: (_: any, entry: any) => (
          <button
            className="btn btn-sm btn-primary"
            onClick={() => handleEditEntry(entry, record.user_id)}
          >
            <i className="ti ti-edit me-1" />
            Edit
          </button>
        ),
      },
    ];

    if (!record.multiple_entries || record.multiple_entries.length === 0) {
      return <p style={{ padding: '16px' }}>No individual entries found for this employee on this day.</p>;
    }

    return (
      <AntTable
        columns={entryColumns}
        dataSource={record.multiple_entries}
        pagination={false}
        rowKey="id"
      />
    );
  };

  return (
    <>
      {/* Page Wrapper */}
      <div className="page-wrapper">
        <div className="content">
          {/* Breadcrumb */}
          <div className="d-md-flex d-block align-items-center justify-content-between page-breadcrumb mb-3">
            <div className="my-auto mb-2">
              <h2 className="mb-1">Attendance Admin</h2>
            </div>
            <div className="d-flex my-xl-auto right-content align-items-center flex-wrap ">
              <div className="mb-2">
                <button
                  type="button"
                  onClick={handleExportExcel}
                  className="btn btn-success d-flex align-items-center me-2"
                >
                  <i className="ti ti-file-type-xls me-2" />
                  Download Report
                </button>
              </div>
              <div className="ms-2 head-icons">
                <CollapseHeader />
              </div>
            </div>
          </div>
          {/* /Breadcrumb */}
          <div className="card border-0">
            <div className="card-body">
              <div className="row align-items-center mb-4">
                <div className="col-md-5">
                  <div className="mb-3 mb-md-0">
                    <h4 className="mb-1">Attendance Details</h4>
                  </div>
                </div>
                <div className="col-md-7">
                  <div className="d-flex align-items-center justify-content-md-end">
                    <h6>Total Employees {data.length}</h6>
                    <div className="avatar-list-stacked avatar-group-sm ms-4">
                      <span className="avatar avatar-rounded">
                        <ImageWithBasePath
                          className="border border-white"
                          src="assets/img/profiles/avatar-02.jpg"
                          alt="img"
                        />
                      </span>
                      <span className="avatar avatar-rounded">
                        <ImageWithBasePath
                          className="border border-white"
                          src="assets/img/profiles/avatar-03.jpg"
                          alt="img"
                        />
                      </span>
                      <span className="avatar avatar-rounded">
                        <ImageWithBasePath
                          className="border border-white"
                          src="assets/img/profiles/avatar-05.jpg"
                          alt="img"
                        />
                      </span>
                      <span className="avatar avatar-rounded">
                        <ImageWithBasePath
                          className="border border-white"
                          src="assets/img/profiles/avatar-06.jpg"
                          alt="img"
                        />
                      </span>
                      <span className="avatar avatar-rounded">
                        <ImageWithBasePath
                          className="border border-white"
                          src="assets/img/profiles/avatar-07.jpg"
                          alt="img"
                        />
                      </span>
                      <Link
                        className="avatar bg-primary avatar-rounded text-fixed-white fs-12"
                        to="#"
                      >
                        +1
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
              <div className="border rounded">
                <div className="row gx-0">
                  <div className="col-md col-sm-4 border-end">
                    <div className="p-3">
                      <span className="fw-medium mb-1 d-block">Present</span>
                      <div className="d-flex align-items-center justify-content-between">
                        <h5>{summary.present}</h5>
                      </div>
                    </div>
                  </div>
                  <div className="col-md col-sm-4 border-end">
                    <div className="p-3">
                      <span className="fw-medium mb-1 d-block">Late Login</span>
                      <div className="d-flex align-items-center justify-content-between">
                        <h5>{summary.late_login}</h5>
                      </div>
                    </div>
                  </div>
                  <div className="col-md col-sm-4">
                    <div className="p-3">
                      <span className="fw-medium mb-1 d-block">Absent</span>
                      <div className="d-flex align-items-center justify-content-between">
                        <h5>{summary.absent}</h5>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="card-header d-flex align-items-center justify-content-between flex-wrap row-gap-3">
              <h5>Employee Attendance</h5>
              <div className="d-flex my-xl-auto right-content align-items-center flex-wrap row-gap-3">
                <div className="me-3">
                  <div className="input-icon-end position-relative">
                  <DatePicker
                      value={selectedDate}
                      onChange={(date) => setSelectedDate(date || dayjs())}
                      format="YYYY-MM-DD"
                      className="form-control"
                      placeholder="Select Date"
                    />
                    <span className="input-icon-addon">
                      <i className="ti ti-calendar" />
                    </span>
                  </div>
                </div>
                <div className="dropdown me-3">
                <Link
                    to="#"
                    className="btn btn-white dropdown-toggle"
                    data-bs-toggle="dropdown"
                    aria-expanded="false"
                  >
                    {statusFilter || "Select Status"}
                  </Link>
                  <ul className="dropdown-menu dropdown-menu-end">
                    <li><Link className="dropdown-item" to="#" onClick={() => setStatusFilter("Present")}>Present</Link></li>
                    <li><Link className="dropdown-item" to="#" onClick={() => setStatusFilter("Absent")}>Absent</Link></li>
                    <li><Link className="dropdown-item" to="#" onClick={() => setStatusFilter("Late")}>Late</Link></li>
                    <li><hr className="dropdown-divider" /></li>
                    <li><Link className="dropdown-item" to="#" onClick={() => setStatusFilter("")}>Show All</Link></li>
                  </ul>
                </div>
              </div>
            </div>
            <div className="card-body p-0">
              {loading ? (
                <p className="p-3">Loading attendance...</p>
              ) : (
                <AntTable 
                  dataSource={data} 
                  columns={columns} 
                  expandable={{ expandedRowRender }}
                  rowKey={(record, index) => `${record.Employee}-${index}`}
                />
              )}
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
      {/* Edit Attendance */}
      <div className="modal fade" id="edit_attendance">
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content">
            <div className="modal-header">
              <h4 className="modal-title">Edit Attendance</h4>
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
                      <label className="form-label">Date</label>
                      <div className="input-icon input-icon-new position-relative w-100 me-2">
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
                          <i className="ti ti-calendar" />
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">Check In</label>
                      <div className="input-icon input-icon-new position-relative w-100">
                        <TimePicker getPopupContainer={getModalContainer2} use12Hours placeholder="Choose" format="h:mm A" className="form-control timepicker" />
                        <span className="input-icon-addon">
                          <i className="ti ti-clock-hour-3" />
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">Check Out</label>
                      <div className="input-icon input-icon-new position-relative w-100">
                        <TimePicker getPopupContainer={getModalContainer2} use12Hours placeholder="Choose" format="h:mm A" className="form-control timepicker" />
                        <span className="input-icon-addon">
                          <i className="ti ti-clock-hour-3" />
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">Break</label>
                      <input
                        type="text"
                        className="form-control"
                        defaultValue="30 Min	"
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">Late</label>
                      <input
                        type="text"
                        className="form-control"
                        defaultValue="32 Min"
                      />
                    </div>
                  </div>
                  <div className="col-md-12">
                    <div className="mb-3">
                      <label className="form-label">Production Hours</label>
                      <div className="input-icon input-icon-new position-relative w-100">
                        <TimePicker getPopupContainer={getModalContainer2} use12Hours placeholder="Choose" format="h:mm A" className="form-control timepicker" />
                        <span className="input-icon-addon">
                          <i className="ti ti-clock-hour-3" />
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-12">
                    <div className="mb-3 ">
                      <label className="form-label">Status</label>
                      <CommonSelect
                        className='select'
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
                <button type="button" data-bs-dismiss="modal" className="btn btn-primary">
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
      {/* /Edit Attendance */}
      {/* Attendance Report */}
      <div className="modal fade" id="attendance_report">
        <div className="modal-dialog modal-dialog-centered modal-lg">
          <div className="modal-content">
            <div className="modal-header">
              <h4 className="modal-title">Attendance</h4>
              <button
                type="button"
                className="btn-close custom-btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
              >
                <i className="ti ti-x" />
              </button>
            </div>
            <div className="modal-body">
              <div className="card shadow-none bg-transparent-light">
                <div className="card-body pb-1">
                  <div className="row align-items-center">
                    <div className="col-lg-4">
                      <div className="d-flex align-items-center mb-3">
                        <span className="avatar avatar-sm avatar-rounded bg-primary text-fixed-white flex-shrink-0 me-2 d-flex align-items-center justify-content-center">
                          <i className="ti ti-user fs-16"></i>
                        </span>
                        <div>
                          <h6 className="fw-medium">Anthony Lewis</h6>
                          <span>UI/UX Team</span>
                        </div>
                      </div>
                    </div>
                    <div className="col-lg-8">
                      <div className="row">
                        <div className="col-sm-3">
                          <div className="mb-3 text-sm-end">
                            <span>Date</span>
                            <p className="text-gray-9 fw-medium">15 Apr 2025</p>
                          </div>
                        </div>
                        <div className="col-sm-3">
                          <div className="mb-3 text-sm-end">
                            <span>Punch in at</span>
                            <p className="text-gray-9 fw-medium">09:00 AM</p>
                          </div>
                        </div>
                        <div className="col-sm-3">
                          <div className="mb-3 text-sm-end">
                            <span>Punch out at</span>
                            <p className="text-gray-9 fw-medium">06:45 PM</p>
                          </div>
                        </div>
                        <div className="col-sm-3">
                          <div className="mb-3 text-sm-end">
                            <span>Status</span>
                            <p className="text-gray-9 fw-medium">Present</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="card shadow-none border mb-0">
                <div className="card-body">
                  <div className="row">
                    <div className="col-xl-3">
                      <div className="mb-4">
                        <p className="d-flex align-items-center mb-1">
                          <i className="ti ti-point-filled text-dark-transparent me-1" />
                          Total Working hours
                        </p>
                        <h3>12h 36m</h3>
                      </div>
                    </div>
                    <div className="col-xl-3">
                      <div className="mb-4">
                        <p className="d-flex align-items-center mb-1">
                          <i className="ti ti-point-filled text-success me-1" />
                          Productive Hours
                        </p>
                        <h3>08h 36m</h3>
                      </div>
                    </div>
                    <div className="col-xl-3">
                      <div className="mb-4">
                        <p className="d-flex align-items-center mb-1">
                          <i className="ti ti-point-filled text-warning me-1" />
                          Break hours
                        </p>
                        <h3>22m 15s</h3>
                      </div>
                    </div>
                    <div className="col-xl-3">
                      <div className="mb-4">
                        <p className="d-flex align-items-center mb-1">
                          <i className="ti ti-point-filled text-info me-1" />
                          Overtime
                        </p>
                        <h3>02h 15m</h3>
                      </div>
                    </div>
                  </div>
                  <div className="row">
                    <div className="col-md-8 mx-auto">
                      <div
                        className="progress bg-transparent-dark mb-3"
                        style={{ height: 24 }}
                      >
                        <div
                          className="progress-bar bg-success rounded me-2"
                          role="progressbar"
                          style={{ width: "18%" }}
                        />
                        <div
                          className="progress-bar bg-warning rounded me-2"
                          role="progressbar"
                          style={{ width: "5%" }}
                        />
                        <div
                          className="progress-bar bg-success rounded me-2"
                          role="progressbar"
                          style={{ width: "28%" }}
                        />
                        <div
                          className="progress-bar bg-warning rounded me-2"
                          role="progressbar"
                          style={{ width: "17%" }}
                        />
                        <div
                          className="progress-bar bg-success rounded me-2"
                          role="progressbar"
                          style={{ width: "22%" }}
                        />
                        <div
                          className="progress-bar bg-warning rounded me-2"
                          role="progressbar"
                          style={{ width: "5%" }}
                        />
                        <div
                          className="progress-bar bg-info rounded me-2"
                          role="progressbar"
                          style={{ width: "3%" }}
                        />
                        <div
                          className="progress-bar bg-info rounded"
                          role="progressbar"
                          style={{ width: "2%" }}
                        />
                      </div>
                    </div>
                    <div className="co-md-12">
                      <div className="d-flex align-items-center justify-content-between">
                        <span className="fs-10">06:00</span>
                        <span className="fs-10">07:00</span>
                        <span className="fs-10">08:00</span>
                        <span className="fs-10">09:00</span>
                        <span className="fs-10">10:00</span>
                        <span className="fs-10">11:00</span>
                        <span className="fs-10">12:00</span>
                        <span className="fs-10">01:00</span>
                        <span className="fs-10">02:00</span>
                        <span className="fs-10">03:00</span>
                        <span className="fs-10">04:00</span>
                        <span className="fs-10">05:00</span>
                        <span className="fs-10">06:00</span>
                        <span className="fs-10">07:00</span>
                        <span className="fs-10">08:00</span>
                        <span className="fs-10">09:00</span>
                        <span className="fs-10">10:00</span>
                        <span className="fs-10">11:00</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* /Attendance Report */}
      {/* Edit Entry Modal */}
      <div className={`modal fade ${editEntryModalVisible ? 'show' : ''}`} id="edit_entry_modal" style={{ display: editEntryModalVisible ? 'block' : 'none' }}>
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content">
            <div className="modal-header">
              <div className="d-flex align-items-center">
                <span className="avatar avatar-sm avatar-rounded bg-primary text-fixed-white me-2 d-flex align-items-center justify-content-center">
                  <i className="ti ti-user fs-16"></i>
                </span>
                <h4 className="modal-title mb-0">Edit Entry</h4>
              </div>
              <button
                type="button"
                className="btn-close custom-btn-close"
                onClick={() => {
                  setEditEntryModalVisible(false);
                  setEditingEntry(null);
                  setEditEntryForm({ check_in_time: null, check_out_time: null });
                }}
                aria-label="Close"
              >
                <i className="ti ti-x" />
              </button>
            </div>
            <div className="modal-body pb-0">
              <div className="row">
                <div className="col-md-6">
                  <div className="mb-3">
                    <label className="form-label">Check In Time</label>
                    <div className="input-icon input-icon-new position-relative w-100">
                      <DatePicker
                        showTime={{ format: 'HH:mm:ss' }}
                        value={editEntryForm.check_in_time}
                        onChange={(date) => setEditEntryForm({ ...editEntryForm, check_in_time: date })}
                        format="YYYY-MM-DD HH:mm:ss"
                        className="form-control"
                        placeholder="Select Check In Time"
                        getPopupContainer={getModalContainer2}
                        style={{ width: '100%' }}
                      />
                      <span className="input-icon-addon">
                        <i className="ti ti-calendar" />
                      </span>
                    </div>
                  </div>
                </div>
                <div className="col-md-6">
                  <div className="mb-3">
                    <label className="form-label">Check Out Time</label>
                    <div className="input-icon input-icon-new position-relative w-100">
                      <DatePicker
                        showTime={{ format: 'HH:mm:ss' }}
                        value={editEntryForm.check_out_time}
                        onChange={(date) => setEditEntryForm({ ...editEntryForm, check_out_time: date })}
                        format="YYYY-MM-DD HH:mm:ss"
                        className="form-control"
                        placeholder="Select Check Out Time"
                        getPopupContainer={getModalContainer2}
                        style={{ width: '100%' }}
                      />
                      <span className="input-icon-addon">
                        <i className="ti ti-calendar" />
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
                onClick={() => {
                  setEditEntryModalVisible(false);
                  setEditingEntry(null);
                  setEditEntryForm({ check_in_time: null, check_out_time: null });
                }}
              >
                Cancel
              </button>
              <button 
                type="button" 
                className="btn btn-primary"
                onClick={handleSaveEntry}
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      </div>
      {editEntryModalVisible && <div className="modal-backdrop fade show" onClick={() => {
        setEditEntryModalVisible(false);
        setEditingEntry(null);
        setEditEntryForm({ check_in_time: null, check_out_time: null });
      }}></div>}
      {/* /Edit Entry Modal */}
      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
      />
    </>




  )
}

export default AttendanceAdmin
