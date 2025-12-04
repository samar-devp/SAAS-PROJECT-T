import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { toast } from "react-toastify";
import { ToastContainer } from "react-toastify";
import CollapseHeader from "../../../core/common/collapse-header/collapse-header";
import { all_routes } from "../../router/all_routes";
import Table from "../../../core/common/dataTable/index";
import LeaveTypeModal from "./CreateModal";
import DeleteModal from "./deleteModal";
import { getAdminIdForApi } from "../../../core/utils/apiHelpers";

const getLeaveTypeKey = (leaveType: any) =>
  leaveType?.id ?? leaveType?.leave_type_id ?? leaveType?.leaveTypeId ?? null;

const normalizeLeaveTypeId = (value: any): number | null => {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const parsed = Number(value);
  return Number.isNaN(parsed) ? null : parsed;
};

const LeaveTypes = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [leaveTypeIdToDelete, setLeaveTypeIdToDelete] = useState<number | null>(null);
  const [editingLeaveType, setEditingLeaveType] = useState<any>(null);

  const fetchLeaveTypes = useCallback(async () => {
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
        `http://127.0.0.1:8000/api/leave-types/${admin_id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      // Backend response format: { status, message, data }
      const leaveTypes = response.data.data || response.data;
      setData(Array.isArray(leaveTypes) ? leaveTypes : []);
    } catch (error: any) {
      console.error("Error fetching leave types:", error);
      toast.error(error.response?.data?.message || "Failed to fetch leave types");
      setData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLeaveTypes();
  }, [fetchLeaveTypes]);
  const routes = all_routes;
  const columns = [
    {
      title: "Leave Type Name",
      dataIndex: "name",
      render: (text: string) => (
        <h6 className="fw-medium">
          <Link to="#">{text}</Link>
        </h6>
      ),
      sorter: (a: any, b: any) => (a.name ?? "").localeCompare(b.name ?? ""),
    },
    {
      title: "Code",
      dataIndex: "code",
      sorter: (a: any, b: any) => (a.code ?? "").localeCompare(b.code ?? ""),
    },
    {
      title: "Default Count",
      dataIndex: "default_count",
      render: (value: number | null) => (value ?? 0),
      sorter: (a: any, b: any) =>
        Number(a.default_count ?? 0) - Number(b.default_count ?? 0),
    },
    {
      title: "Paid Leave",
      dataIndex: "is_paid",
      render: (value: boolean) => (value ? "Yes" : "No"),
      sorter: (a: any, b: any) => Number(a.is_paid) - Number(b.is_paid),
    },
    {
      title: "Description",
      dataIndex: "description",
      render: (text: string) => (text ? (text.length > 50 ? `${text.substring(0, 50)}...` : text) : "—"),
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
      render: (_: any, leaveType: any) => (
        <div className="action-icon d-inline-flex">
          <Link
            to="#"
            className="me-2"
            data-bs-toggle="modal"
            data-bs-target="#edit_leave_type"
            onClick={() => setEditingLeaveType(leaveType)}
          >
            <i className="ti ti-edit" />
          </Link>
          <Link
            to="#"
            data-bs-toggle="modal"
            data-bs-target="#delete_modal"
            onClick={() => setLeaveTypeIdToDelete(normalizeLeaveTypeId(getLeaveTypeKey(leaveType)))}
          >
            <i className="ti ti-trash text-danger" />
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
              <h2 className="mb-1">Leave Types</h2>
            </div>
            <div className="d-flex my-xl-auto right-content align-items-center flex-wrap ">
              <div className="mb-2">
                <Link
                  to="#"
                  data-bs-toggle="modal" data-inert={true}
                  data-bs-target="#add_leave_type"
                  className="btn btn-primary d-flex align-items-center"
                >
                  <i className="ti ti-circle-plus me-2" />
                  Add Leave Type
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
              <h5>Leave Type List</h5>
            </div>
            <div className="card-body p-0">
              {loading ? (
                <p className="p-3">Loading leave types...</p>
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

      <LeaveTypeModal
        onLeaveTypeAdded={(newLeaveType) => {
          setData((prev) => [newLeaveType, ...prev]);
          fetchLeaveTypes();
        }}
        editingLeaveType={editingLeaveType}
        onEditClose={() => setEditingLeaveType(null)}
        onLeaveTypeUpdated={(updatedLeaveType) => {
          const updatedId = normalizeLeaveTypeId(getLeaveTypeKey(updatedLeaveType));
          if (updatedId === null) {
            fetchLeaveTypes();
            return;
          }
          setData((prev) =>
            prev.map((leaveType) =>
              normalizeLeaveTypeId(getLeaveTypeKey(leaveType)) === updatedId ? updatedLeaveType : leaveType
            )
          );
          fetchLeaveTypes();
        }}
      />
      <DeleteModal
        admin_id={typeof window !== "undefined" ? sessionStorage.getItem("user_id") : null}
        leaveTypeId={leaveTypeIdToDelete}
        onDeleted={() => {
          if (leaveTypeIdToDelete !== null) {
            setData((prev) =>
              prev.filter(
                (leaveType) => normalizeLeaveTypeId(getLeaveTypeKey(leaveType)) !== leaveTypeIdToDelete
              )
            );
          }
          setLeaveTypeIdToDelete(null);
          fetchLeaveTypes();
        }}
      />
      <ToastContainer position="top-right" autoClose={3000} />
    </>
  );
};

export default LeaveTypes;
