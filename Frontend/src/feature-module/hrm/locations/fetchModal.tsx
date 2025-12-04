import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import CollapseHeader from "../../../core/common/collapse-header/collapse-header";
import { all_routes } from "../../router/all_routes";
import Table from "../../../core/common/dataTable/index";
import LocationModal from "./CreateModal";
import DeleteModal from "./deleteModal";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { getAdminIdForApi } from "../../../core/utils/apiHelpers";

const getLocationKey = (location: any) =>
  location?.id ?? location?.location_id ?? location?.locationId ?? null;

const normalizeLocationId = (value: any): number | null => {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const parsed = Number(value);
  return Number.isNaN(parsed) ? null : parsed;
};

const Locations = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [locationIdToDelete, setLocationIdToDelete] = useState<number | null>(null);
  const [editingLocation, setEditingLocation] = useState<any>(null);

  const fetchLocations = useCallback(async () => {
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
        `http://127.0.0.1:8000/api/locations/${admin_id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      // Backend response format: { status, message, data }
      const locations = response.data.data || response.data;
      setData(Array.isArray(locations) ? locations : []);
    } catch (error: any) {
      console.error("Error fetching locations:", error);
      toast.error(error.response?.data?.message || "Failed to fetch locations");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLocations();
  }, [fetchLocations]);

  const routes = all_routes;
  
  const columns = [
    {
      title: "Location Name",
      dataIndex: "name",
      render: (text: string) => (
        <h6 className="fw-medium">
          <Link to="#">{text}</Link>
        </h6>
      ),
      sorter: (a: any, b: any) => (a.name ?? "").localeCompare(b.name ?? ""),
    },
    {
      title: "Address",
      dataIndex: "address",
      render: (text: string) => (
        <span className="text-truncate d-inline-block" style={{ maxWidth: "300px" }}>
          {text ?? "—"}
        </span>
      ),
    },
    {
      title: "Latitude",
      dataIndex: "latitude",
      render: (value: number | null) => (value ? parseFloat(value.toString()).toFixed(6) : "—"),
      sorter: (a: any, b: any) => 
        Number(a.latitude ?? 0) - Number(b.latitude ?? 0),
    },
    {
      title: "Longitude",
      dataIndex: "longitude",
      render: (value: number | null) => (value ? parseFloat(value.toString()).toFixed(6) : "—"),
      sorter: (a: any, b: any) => 
        Number(a.longitude ?? 0) - Number(b.longitude ?? 0),
    },
    {
      title: "Radius (m)",
      dataIndex: "radius",
      render: (value: number | null) => (value ?? "—"),
      sorter: (a: any, b: any) => Number(a.radius ?? 0) - Number(b.radius ?? 0),
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
      render: (_: any, location: any) => (
        <div className="action-icon d-inline-flex">
          <Link
            to="#"
            className="me-2"
            data-bs-toggle="modal"
            data-bs-target="#locationModal"
            onClick={() => setEditingLocation(location)}
          >
            <i className="ti ti-edit" />
          </Link>
          <Link
            to="#"
            data-bs-toggle="modal"
            data-bs-target="#deleteLocationModal"
            onClick={() => setLocationIdToDelete(normalizeLocationId(getLocationKey(location)))}
          >
            <i className="ti ti-trash" />
          </Link>
        </div>
      ),
    },
  ];

  const handleLocationAdded = () => {
    fetchLocations();
    setEditingLocation(null);
  };

  const handleLocationUpdated = () => {
    fetchLocations();
    setEditingLocation(null);
  };

  const handleLocationDeleted = () => {
    fetchLocations();
    setLocationIdToDelete(null);
  };

  const handleEditClose = () => {
    setEditingLocation(null);
  };

  return (
    <>
      {/* Page Wrapper */}
      <div className="page-wrapper">
        <div className="content">
          {/* Breadcrumb */}
          <div className="d-md-flex d-block align-items-center justify-content-between page-breadcrumb mb-3">
            <div className="my-auto mb-2">
              <h2 className="mb-1">Work Locations</h2>
            </div>
            <div className="d-flex my-xl-auto right-content align-items-center flex-wrap ">
              <div className="mb-2">
                <Link
                  to="#"
                  data-bs-toggle="modal" data-inert={true}
                  data-bs-target="#locationModal"
                  className="btn btn-primary d-flex align-items-center"
                  onClick={() => setEditingLocation(null)}
                >
                  <i className="ti ti-circle-plus me-2" />
                  Add Location
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
              <h5>Location List</h5>
            </div>
            <div className="card-body p-0">
              {loading ? (
                <p className="p-3">Loading locations...</p>
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

      {/* Location Create/Edit Modal */}
      <LocationModal
        onLocationAdded={handleLocationAdded}
        editingLocation={editingLocation}
        onLocationUpdated={handleLocationUpdated}
        onEditClose={handleEditClose}
      />

      {/* Delete Modal */}
      <DeleteModal
        locationId={locationIdToDelete}
        onLocationDeleted={handleLocationDeleted}
        onCancel={() => setLocationIdToDelete(null)}
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

export default Locations;

