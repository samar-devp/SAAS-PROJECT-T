import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import CollapseHeader from "../../../core/common/collapse-header/collapse-header";
import { all_routes } from "../../router/all_routes";
import Table from "../../../core/common/dataTable/index";
import ServiceShiftModal from "./CreateModal";
import DeleteModal from "./deleteModal";
import { getAdminIdForApi } from "../../../core/utils/apiHelpers";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const getShiftKey = (shift: any) =>
  shift?.id ?? shift?.shift_id ?? shift?.shiftId ?? null;

const normalizeShiftId = (value: any): number | null => {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const parsed = Number(value);
  return Number.isNaN(parsed) ? null : parsed;
};

const ServiceShifts = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [shiftIdToDelete, setShiftIdToDelete] = useState<number | null>(null);
  const [editingShift, setEditingShift] = useState<any>(null);

  const fetchServiceShift = useCallback(async () => {
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

      const response = await axios.get(
        `http://127.0.0.1:8000/api/service-shifts/${admin_id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      // Backend response format: { status, message, data }
      const shifts = response.data.data || response.data;
      setData(Array.isArray(shifts) ? shifts : []);
    } catch (error) {
      console.error("Error fetching service shifts:", error);
      toast.error("Failed to fetch service shifts");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchServiceShift();
  }, [fetchServiceShift]);
  const routes = all_routes;
  const columns = [
    {
      title: "Shift Name",
      dataIndex: "shift_name",
      render: (text: string) => (
        <h6 className="fw-medium">
          <Link to="#">{text}</Link>
        </h6>
      ),
      sorter: (a: any, b: any) => (a.shift_name ?? "").localeCompare(b.shift_name ?? ""),
    },
    {
      title: "Start Time",
      dataIndex: "start_time",
      sorter: (a: any, b: any) => (a.start_time ?? "").localeCompare(b.start_time ?? ""),
    },
    {
      title: "End Time",
      dataIndex: "end_time",
      sorter: (a: any, b: any) => (a.end_time ?? "").localeCompare(b.end_time ?? ""),
    },
    {
      title: "Break (min)",
      dataIndex: "break_duration_minutes",
      render: (value: number | null) => (value ?? "—"),
      sorter: (a: any, b: any) =>
        Number(a.break_duration_minutes ?? 0) - Number(b.break_duration_minutes ?? 0),
    },
    {
      title: "Duration (min)",
      dataIndex: "duration_minutes",
      sorter: (a: any, b: any) =>
        Number(a.duration_minutes ?? 0) - Number(b.duration_minutes ?? 0),
    },
    {
      title: "Night Shift",
      dataIndex: "is_night_shift",
      render: (value: boolean) => (value ? "Yes" : "No"),
      sorter: (a: any, b: any) => Number(a.is_night_shift) - Number(b.is_night_shift),
    },
    {
      title: "Status",
      dataIndex: "is_active",
      render: (active: boolean) => (
        <span
          className={`badge d-inline-flex align-items-center badge-sm ${
            active ? "badge-success" : "badge-danger"
          }`}
        >
          <i className="ti ti-point-filled me-1" />
          {active ? "Active" : "Inactive"}
        </span>
      ),
      sorter: (a: any, b: any) => Number(a.is_active) - Number(b.is_active),
    },
    {
      title: "Actions",
      dataIndex: "actions",
      render: (_: any, shift: any) => (
        <div className="action-icon d-inline-flex">
          <Link
            to="#"
            className="me-2"
            data-bs-toggle="modal"
            data-bs-target="#edit_shift"
            onClick={() => setEditingShift(shift)}
          >
            <i className="ti ti-edit" />
          </Link>
          <Link
            to="#"
            data-bs-toggle="modal"
            data-bs-target="#delete_modal"
            onClick={() => setShiftIdToDelete(normalizeShiftId(getShiftKey(shift)))}
          >
            <i className="ti ti-trash" />
          </Link>
        </div>
      ),
    },
  ];
  return (
    <>
      {/* Page Wrapper */}
      <div className="page-wrapper">
        <div className="content">
          {/* Breadcrumb */}
          <div className="d-md-flex d-block align-items-center justify-content-between page-breadcrumb mb-3">
            <div className="my-auto mb-2">
              <h2 className="mb-1">Service Shifts</h2>
            </div>
            <div className="d-flex my-xl-auto right-content align-items-center flex-wrap ">
              <div className="mb-2">
                <Link
                  to="#"
                  data-bs-toggle="modal" data-inert={true}
                  data-bs-target="#add_shift"
                  className="btn btn-primary d-flex align-items-center"
                >
                  <i className="ti ti-circle-plus me-2" />
                  Add Shift
                </Link>
              </div>
              <div className="head-icons ms-2">
                <CollapseHeader />
              </div>
            </div>
          </div>
          {/* /Breadcrumb */}
          <div className="card">
            <div className="card-header d-flex align-items-center justify-content-between flex-wrap row-gap-3">
              <h5>Service Shift List</h5>
            </div>
            <div className="card-body p-0">
              {loading ? (
                <p className="p-3">Loading service shifts...</p>
              ) : (
                <Table dataSource={data} columns={columns} Selection={true} />
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

      <ServiceShiftModal
        onShiftAdded={(newShift) => {
          setData((prev) => [newShift, ...prev]);
          fetchServiceShift();
        }}
        editingShift={editingShift}
        onEditClose={() => setEditingShift(null)}
        onShiftUpdated={(updatedShift) => {
          const updatedId = normalizeShiftId(getShiftKey(updatedShift));
          if (updatedId === null) {
            fetchServiceShift();
            return;
          }
          setData((prev) =>
            prev.map((shift) =>
              normalizeShiftId(getShiftKey(shift)) === updatedId ? updatedShift : shift
            )
          );
          fetchServiceShift();
        }}
      />
      <DeleteModal
        admin_id={typeof window !== "undefined" ? sessionStorage.getItem("user_id") : null}
        shiftId={shiftIdToDelete}
        onDeleted={() => {
          if (shiftIdToDelete !== null) {
            setData((prev) =>
              prev.filter(
                (shift) => normalizeShiftId(getShiftKey(shift)) !== shiftIdToDelete
              )
            );
          }
          setShiftIdToDelete(null);
          fetchServiceShift();
        }}
      />
      
      {/* Toast Container */}
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
  );
};

export default ServiceShifts;
