import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import CollapseHeader from "../../../core/common/collapse-header/collapse-header";
import { all_routes } from "../../router/all_routes";
import Table from "../../../core/common/dataTable/index";
import LeavePolicyModal from "./CreateModal";
import DeleteModal from "./deleteModal";
import { toast } from "react-toastify";

const getLeavePolicyKey = (policy: any) =>
  policy?.id ?? policy?.policy_id ?? policy?.policyId ?? null;

const LeavePolicies = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [policyIdToDelete, setPolicyIdToDelete] = useState<string | null>(null);
  const [editingPolicy, setEditingPolicy] = useState<any>(null);
  const [orgId, setOrgId] = useState<string | null>(null);

  // Get organization ID from session info
  const fetchOrgId = useCallback(async () => {
    try {
      const token = sessionStorage.getItem("access_token");
      const admin_id = sessionStorage.getItem("user_id");

      if (!admin_id) {
        toast.error("Admin ID not found. Please login again.");
        return;
      }

      // Try to get from sessionStorage first
      const storedOrgId = sessionStorage.getItem("organization_id");
      if (storedOrgId) {
        setOrgId(storedOrgId);
        return;
      }

      // Fetch from session info API
      const response = await axios.get(
        `http://127.0.0.1:8000/api/session-info/`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.data?.success && response.data?.data?.organization_id) {
        const org_id = response.data.data.organization_id;
        setOrgId(org_id);
        sessionStorage.setItem("organization_id", org_id);
      } else {
        toast.error("Unable to fetch organization information.");
      }
    } catch (error: any) {
      console.error("Error fetching org ID:", error);
      toast.error(error.response?.data?.message || "Failed to fetch organization information");
    }
  }, []);

  const fetchLeavePolicies = useCallback(async () => {
    if (!orgId) {
      return;
    }

    setLoading(true);
    try {
      const token = sessionStorage.getItem("access_token");

      const response = await axios.get(
        `http://127.0.0.1:8000/api/leave/leave-policies/${orgId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.data?.status === 200 && response.data?.data) {
        setData(response.data.data ?? []);
      } else {
        setData([]);
      }
    } catch (error: any) {
      console.error("Error fetching leave policies:", error);
      toast.error(error.response?.data?.message || "Failed to fetch leave policies");
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    fetchOrgId();
  }, [fetchOrgId]);

  useEffect(() => {
    if (orgId) {
      fetchLeavePolicies();
    }
  }, [orgId, fetchLeavePolicies]);

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
      sorter: (a: any, b: any) => (a.name ?? "").localeCompare(b.name ?? ""),
    },
    {
      title: "Scope",
      dataIndex: "scope",
      render: (scope: string) => {
        const scopeMap: { [key: string]: string } = {
          organization: "Organization Wide",
          department: "Department",
          designation: "Designation",
          employee: "Individual Employee",
        };
        return scopeMap[scope] || scope;
      },
      sorter: (a: any, b: any) => (a.scope ?? "").localeCompare(b.scope ?? ""),
    },
    {
      title: "Effective From",
      dataIndex: "effective_from",
      render: (date: string) => {
        if (!date) return "—";
        return new Date(date).toLocaleDateString("en-GB");
      },
      sorter: (a: any, b: any) => {
        const dateA = a.effective_from ? new Date(a.effective_from).getTime() : 0;
        const dateB = b.effective_from ? new Date(b.effective_from).getTime() : 0;
        return dateA - dateB;
      },
    },
    {
      title: "Effective To",
      dataIndex: "effective_to",
      render: (date: string) => {
        if (!date) return "—";
        return new Date(date).toLocaleDateString("en-GB");
      },
      sorter: (a: any, b: any) => {
        const dateA = a.effective_to ? new Date(a.effective_to).getTime() : 0;
        const dateB = b.effective_to ? new Date(b.effective_to).getTime() : 0;
        return dateA - dateB;
      },
    },
    {
      title: "Leave Allocations",
      dataIndex: "leave_allocations",
      render: (allocations: any) => {
        if (!allocations || typeof allocations !== "object") return "—";
        const entries = Object.entries(allocations).slice(0, 2);
        const display = entries.map(([key, val]) => `${key}: ${val}`).join(", ");
        const more = Object.keys(allocations).length > 2 ? "..." : "";
        return display ? `${display}${more}` : "—";
      },
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
      render: (_: any, policy: any) => (
        <div className="action-icon d-inline-flex">
          <Link
            to="#"
            className="me-2"
            onClick={(e) => {
              e.preventDefault();
              setEditingPolicy(policy);
            }}
            data-bs-toggle="modal"
            data-bs-target="#leavePolicyModal"
          >
            <i className="ti ti-pencil fs-5" />
          </Link>
          <Link
            to="#"
            onClick={(e) => {
              e.preventDefault();
              const id = getLeavePolicyKey(policy);
              setPolicyIdToDelete(id);
            }}
            data-bs-toggle="modal"
            data-bs-target="#deleteLeavePolicyModal"
          >
            <i className="ti ti-trash fs-5 text-danger" />
          </Link>
        </div>
      ),
    },
  ];

  const handlePolicyAdded = () => {
    fetchLeavePolicies();
    setEditingPolicy(null);
  };

  const handlePolicyUpdated = () => {
    fetchLeavePolicies();
    setEditingPolicy(null);
  };

  const handlePolicyDeleted = () => {
    fetchLeavePolicies();
    setPolicyIdToDelete(null);
  };

  const handleEditClose = () => {
    setEditingPolicy(null);
  };

  return (
    <>
      {/* Page Wrapper */}
      <div className="page-wrapper">
        <div className="content">
          {/* Breadcrumb */}
          <div className="d-md-flex d-block align-items-center justify-content-between page-breadcrumb mb-3">
            <div className="my-auto mb-2">
              <h2 className="mb-1">Leave Policies</h2>
              <nav>
                <ol className="breadcrumb mb-0">
                  <li className="breadcrumb-item">
                    <Link to={routes.adminDashboard}>
                      <i className="ti ti-smart-home" />
                    </Link>
                  </li>
                  <li className="breadcrumb-item">Settings</li>
                  <li className="breadcrumb-item active" aria-current="page">
                    Leave Policies
                  </li>
                </ol>
              </nav>
            </div>
            <div className="d-flex my-xl-auto right-content align-items-center flex-wrap ">
              <div className="mb-2">
                <Link
                  to="#"
                  data-bs-toggle="modal" data-inert={true}
                  data-bs-target="#leavePolicyModal"
                  className="btn btn-primary d-flex align-items-center"
                  onClick={() => setEditingPolicy(null)}
                >
                  <i className="ti ti-circle-plus me-2" />
                  Add Leave Policy
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
              <h5>Leave Policy List</h5>
            </div>
            <div className="card-body p-0">
              {loading ? (
                <p className="p-3">Loading leave policies...</p>
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

      {/* Leave Policy Create/Edit Modal */}
      <LeavePolicyModal
        orgId={orgId}
        onPolicyAdded={handlePolicyAdded}
        editingPolicy={editingPolicy}
        onPolicyUpdated={handlePolicyUpdated}
        onEditClose={handleEditClose}
      />

      {/* Delete Modal */}
      <DeleteModal
        orgId={orgId}
        policyId={policyIdToDelete}
        onPolicyDeleted={handlePolicyDeleted}
        onCancel={() => setPolicyIdToDelete(null)}
      />
    </>
  );
};

export default LeavePolicies;

