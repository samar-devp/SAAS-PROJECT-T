import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { all_routes } from "../../router/all_routes";
import { BACKEND_PATH } from "../../../environment";
import ImageWithBasePath from "../../../core/common/imageWithBasePath";

type PasswordField = "oldPassword" | "newPassword" | "confirmPassword";

const ChangePassword = () => {
  const routes = all_routes;
  const navigate = useNavigate();

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [passwordVisibility, setPasswordVisibility] = useState({
    oldPassword: false,
    newPassword: false,
    confirmPassword: false,
  });

  const togglePasswordVisibility = (field: PasswordField) => {
    setPasswordVisibility((prevState) => ({
      ...prevState,
      [field]: !prevState[field],
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    // Validation
    if (!oldPassword || !newPassword || !confirmPassword) {
      toast.error("Please fill all fields");
      setLoading(false);
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error("New password and confirm password do not match");
      setLoading(false);
      return;
    }

    if (newPassword.length < 6) {
      toast.error("New password must be at least 6 characters long");
      setLoading(false);
      return;
    }

    try {
      const token = sessionStorage.getItem("access_token");
      if (!token) {
        toast.error("Please login again");
        navigate(routes.login);
        return;
      }

      const response = await axios.post(
        `${BACKEND_PATH}change-password`,
        {
          old_password: oldPassword,
          new_password: newPassword,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.data.message) {
        toast.success(response.data.message || "Password changed successfully");
        // Clear form
        setOldPassword("");
        setNewPassword("");
        setConfirmPassword("");
        // Optionally redirect after 2 seconds
        setTimeout(() => {
          navigate(routes.adminDashboard);
        }, 2000);
      }
    } catch (error: any) {
      console.error("Error changing password:", error);
      toast.error(
        error.response?.data?.error ||
          error.response?.data?.message ||
          "Failed to change password"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="page-wrapper">
        <div className="content">
          <div className="row justify-content-center">
            <div className="col-md-6 col-lg-5">
              <div className="card">
                <div className="card-header">
                  <h4 className="card-title mb-0">Change Password</h4>
                </div>
                <div className="card-body">
                  <form onSubmit={handleSubmit}>
                    <div className="mb-3">
                      <label className="form-label">Old Password</label>
                      <div className="pass-group">
                        <input
                          type={
                            passwordVisibility.oldPassword ? "text" : "password"
                          }
                          className="pass-input form-control"
                          value={oldPassword}
                          onChange={(e) => setOldPassword(e.target.value)}
                          required
                        />
                        <span
                          className={`ti toggle-passwords ${
                            passwordVisibility.oldPassword
                              ? "ti-eye"
                              : "ti-eye-off"
                          }`}
                          onClick={() => togglePasswordVisibility("oldPassword")}
                        ></span>
                      </div>
                    </div>

                    <div className="mb-3">
                      <label className="form-label">New Password</label>
                      <div className="pass-group">
                        <input
                          type={
                            passwordVisibility.newPassword ? "text" : "password"
                          }
                          className="pass-input form-control"
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          required
                        />
                        <span
                          className={`ti toggle-passwords ${
                            passwordVisibility.newPassword
                              ? "ti-eye"
                              : "ti-eye-off"
                          }`}
                          onClick={() => togglePasswordVisibility("newPassword")}
                        ></span>
                      </div>
                    </div>

                    <div className="mb-3">
                      <label className="form-label">Confirm New Password</label>
                      <div className="pass-group">
                        <input
                          type={
                            passwordVisibility.confirmPassword
                              ? "text"
                              : "password"
                          }
                          className="pass-input form-control"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          required
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

                    <div className="d-flex gap-2">
                      <button
                        type="submit"
                        className="btn btn-primary"
                        disabled={loading}
                      >
                        {loading ? "Changing..." : "Change Password"}
                      </button>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={() => navigate(routes.adminDashboard)}
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <ToastContainer position="top-right" autoClose={3000} />
    </>
  );
};

export default ChangePassword;

