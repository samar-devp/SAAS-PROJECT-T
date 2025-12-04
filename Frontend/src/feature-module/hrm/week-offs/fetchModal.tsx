import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import CollapseHeader from "../../../core/common/collapse-header/collapse-header";
import { all_routes } from "../../router/all_routes";
import Table from "../../../core/common/dataTable/index";
import WeekOffModal from "./CreateModal";
import DeleteModal from "./deleteModal";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { getAdminIdForApi } from "../../../core/utils/apiHelpers";

const getWeekOffKey = (weekOff: any) =>
  weekOff?.id ?? weekOff?.week_off_id ?? weekOff?.weekOffId ?? null;

const normalizeWeekOffId = (value: any): number | null => {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const parsed = Number(value);
  return Number.isNaN(parsed) ? null : parsed;
};

const WeekOffs = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [weekOffIdToDelete, setWeekOffIdToDelete] = useState<number | null>(null);
  const [editingWeekOff, setEditingWeekOff] = useState<any>(null);

  const fetchWeekOffs = useCallback(async () => {
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
        `http://127.0.0.1:8000/api/week-off-policies/${admin_id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      // Backend response format: { status, message, data }
      const weekOffs = response.data.data || response.data;
      setData(Array.isArray(weekOffs) ? weekOffs : []);
    } catch (error: any) {
      console.error("Error fetching week offs:", error);
      toast.error(error.response?.data?.message || "Failed to fetch week offs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWeekOffs();
  }, [fetchWeekOffs]);

  const routes = all_routes;
  
  const columns = [
    {
      title: "Policy Name",
      dataIndex: "name",
      render: (text: string) => (
        <h6 className="fw-medium">
          <Link to="#">{text}</Link>
        </h6>
      ),
      sorter: (a: any, b: any) => (a.name || "").localeCompare(b.name || ""),
    },
    {
      title: "Week Days",
      dataIndex: "week_days",
      render: (days: string[]) => (
        <span>{Array.isArray(days) ? days.join(", ") : "-"}</span>
      ),
    },
    {
      title: "Description",
      dataIndex: "description",
      render: (text: string) => <span>{text || "-"}</span>,
      sorter: (a: any, b: any) =>
        (a.description || "").localeCompare(b.description || ""),
    },
    {
      title: "Status",
      dataIndex: "is_active",
      render: (isActive: boolean) => (
        <span
          className={`badge ${
            isActive ? "badge-soft-success" : "badge-soft-danger"
          }`}
        >
          {isActive ? "Active" : "Inactive"}
        </span>
      ),
      sorter: (a: any, b: any) => Number(a.is_active) - Number(b.is_active),
    },
    {
      title: "Action",
      dataIndex: "actions",
      render: (_: any, record: any) => {
        const weekOffId = normalizeWeekOffId(getWeekOffKey(record));
        return (
          <div className="action-icon d-inline-flex">
            <Link
              to="#"
              className="me-2"
              data-bs-toggle="modal"
              data-bs-target="#edit_week_off"
              onClick={(e) => {
                e.preventDefault();
                setEditingWeekOff(record);
              }}
            >
              <i className="ti ti-edit" />
            </Link>
            <Link
              to="#"
              data-bs-toggle="modal"
              data-bs-target="#delete_week_off_modal"
              onClick={(e) => {
                e.preventDefault();
                if (weekOffId !== null) {
                  setWeekOffIdToDelete(weekOffId);
                } else {
                  toast.error("Invalid week off ID");
                }
              }}
            >
              <i className="ti ti-trash" />
            </Link>
          </div>
        );
      },
    },
  ];

  return (
    <>
      <ToastContainer />
      {/* Page Wrapper */}
      <div className="page-wrapper">
        <div className="content">
          {/* Breadcrumb */}
          <div className="d-md-flex d-block align-items-center justify-content-between page-breadcrumb mb-3">
            <div className="my-auto mb-2">
              <h2 className="mb-1">Week Off Policies</h2>
            </div>
            <div className="d-flex my-xl-auto right-content align-items-center flex-wrap ">
              <div className="mb-2">
                <Link
                  to="#"
                  data-bs-toggle="modal" data-inert={true}
                  data-bs-target="#add_week_off"
                  className="btn btn-primary d-flex align-items-center"
                >
                  <i className="ti ti-circle-plus me-2" />
                  Add Week Off
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
              <h5>Week Off Policy List</h5>
            </div>
            <div className="card-body p-0">
              {loading ? (
                <p className="p-3">Loading week off policies...</p>
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

      <WeekOffModal
        onWeekOffAdded={fetchWeekOffs}
        editingWeekOff={editingWeekOff}
        onWeekOffUpdated={fetchWeekOffs}
        onEditClose={() => setEditingWeekOff(null)}
      />
      <DeleteModal
        itemId={weekOffIdToDelete}
        onConfirmDelete={() => {
          fetchWeekOffs();
          setWeekOffIdToDelete(null);
        }}
        onCancel={() => setWeekOffIdToDelete(null)}
      />
    </>
  );
};

export default WeekOffs;

