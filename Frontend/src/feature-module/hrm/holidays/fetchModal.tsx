import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import CollapseHeader from "../../../core/common/collapse-header/collapse-header";
import { all_routes } from "../../router/all_routes";
import Table from "../../../core/common/dataTable/index";
import HolidaysModal from "./CreateModal";
import DeleteModal from "./deleteModal";

const getHolidayKey = (holiday: any) =>
  holiday?.id ?? holiday?.holiday_id ?? holiday?.holidayId ?? null;

const normalizeHolidayId = (value: any): number | null => {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const parsed = Number(value);
  return Number.isNaN(parsed) ? null : parsed;
};

const Holidays = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [holidayIdToDelete, setHolidayIdToDelete] = useState<number | null>(null);
  const [editingHoliday, setEditingHoliday] = useState<any>(null);

  const fetchHolidays = useCallback(async () => {
    setLoading(true);
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");

      const response = await axios.get(
        `http://127.0.0.1:8000/api/holidays/${admin_id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setData(response.data);
    } catch (error) {
      console.error("Error fetching holidays:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHolidays();
  }, [fetchHolidays]);
  const routes = all_routes;
  // const data = data;
  const columns = [
  {
    title: "Name",
    dataIndex: "name",
    render: (text: string) => (
      <h6 className="fw-medium">
        <Link to="#">{text}</Link>
      </h6>
    ),
    sorter: (a: any, b: any) => a.name.localeCompare(b.name),
  },
  {
    title: "Date",
    dataIndex: "holiday_date",
    sorter: (a: any, b: any) =>
      new Date(a.holiday_date).getTime() - new Date(b.holiday_date).getTime(),
  },
  {
    title: "Day",
    dataIndex: "day",
    render: (text: string | null) => text ?? "—",
    sorter: (a: any, b: any) => (a.day ?? "").localeCompare(b.day ?? ""),
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
  render: (_: any, holiday: any) => (
    <div className="action-icon d-inline-flex">
      <Link
        to="#"
        className="me-2"
        data-bs-toggle="modal"
        data-bs-target="#edit_holiday"
        onClick={() => setEditingHoliday(holiday)}
      >
        <i className="ti ti-edit" />
      </Link>
      <Link
        to="#"
        data-bs-toggle="modal"
        data-bs-target="#delete_modal"
        onClick={() => setHolidayIdToDelete(normalizeHolidayId(getHolidayKey(holiday)))}
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
              <h2 className="mb-1">Holidays</h2>
              <nav>
                <ol className="breadcrumb mb-0">
                  <li className="breadcrumb-item">
                    <Link to={routes.adminDashboard}>
                      <i className="ti ti-smart-home" />
                    </Link>
                  </li>
                  <li className="breadcrumb-item">Employee</li>
                  <li className="breadcrumb-item active" aria-current="page">
                    Holidays
                  </li>
                </ol>
              </nav>
            </div>
            <div className="d-flex my-xl-auto right-content align-items-center flex-wrap ">
              <div className="mb-2">
                <Link
                  to="#"
                  data-bs-toggle="modal" data-inert={true}
                  data-bs-target="#add_holiday"
                  className="btn btn-primary d-flex align-items-center"
                >
                  <i className="ti ti-circle-plus me-2" />
                  Add Holiday
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
              <h5>Holidays List</h5>
            </div>
            <div className="card-body p-0">
            {loading ? (
              <p className="p-3">Loading holidays...</p>
            ) : (
              <Table dataSource={data} columns={columns} Selection={true} />
            )}
          </div>
          </div>
        </div>
        <div className="footer d-sm-flex align-items-center justify-content-between border-top bg-white p-3">
          <p className="mb-0">2014 - 2025 © SmartHR.</p>
          <p>
            Designed &amp; Developed By{" "}
            <Link to="#" className="text-primary">
              Dreams
            </Link>
          </p>
        </div>
      </div>
      {/* /Page Wrapper */}

      <HolidaysModal
        onHolidayAdded={(newHoliday) => {
          setData((prev) => [newHoliday, ...prev]);
          fetchHolidays();
        }}
        editingHoliday={editingHoliday}
        onEditClose={() => setEditingHoliday(null)}
        onHolidayUpdated={(updatedHoliday) => {
          const updatedId = normalizeHolidayId(getHolidayKey(updatedHoliday));
          if (updatedId === null) {
            fetchHolidays();
            return;
          }
          setData((prev) =>
            prev.map((holiday) =>
              normalizeHolidayId(getHolidayKey(holiday)) === updatedId ? updatedHoliday : holiday
            )
          );
          fetchHolidays();
        }}
      />
      <DeleteModal
        admin_id={typeof window !== "undefined" ? sessionStorage.getItem("user_id") : null}
        holidayId={holidayIdToDelete}
        onDeleted={() => {
          if (holidayIdToDelete !== null) {
            setData((prev) =>
              prev.filter(
                (holiday) =>
                  normalizeHolidayId(getHolidayKey(holiday)) !== holidayIdToDelete
              )
            );
          }
          setHolidayIdToDelete(null);
          fetchHolidays();
        }}
      />
    </>
  );
};

export default Holidays;
