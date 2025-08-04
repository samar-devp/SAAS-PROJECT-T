import { BACKEND_PATH } from "../../../environment";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import axios from "axios";
import React, { useEffect, useState } from "react";
import ImageWithBasePath from "../../../core/common/imageWithBasePath";
import { Link, useNavigate } from "react-router-dom";
import { all_routes } from "../../router/all_routes";
type PasswordField = "password";

const Login = () => {
  const routes = all_routes;
  const navigation = useNavigate();

  const navigationPath = () => {
    navigation(routes.adminDashboard);
  };
  // Email, password, error aur password visibility ke state
  const [username, setUsername] = useState(""); // Email input ka value
  const [password, setPassword] = useState(""); // Password input ka value
  const [error, setError] = useState<string | null>(null); // Error message agar login fail ho
  const [passwordVisibility, setPasswordVisibility] = useState({
    password: false, // Initially password hidden hoga
  });

  const togglePasswordVisibility = (field: PasswordField) => {
    setPasswordVisibility((prevState) => ({
      ...prevState,
      [field]: !prevState[field],
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    console.log("________________API CALLED");
    e.preventDefault();
    setError(null);
    try {
      const response = await axios.post(`${BACKEND_PATH}login`, {
        username,
        password,
      });
      const { access, refresh } = response.data;
      // ✅ Destructure response
      const { access_token, refresh_token, user_id, role } = response.data;

      // ✅ Store tokens and user data
      localStorage.setItem("access_token", access_token);
      localStorage.setItem("refresh_token", refresh_token);
      localStorage.setItem("user_id", user_id);
      localStorage.setItem("role", role);

      // Navigate to admin dashboard

      if (role !== "admin") {
        toast.error("Login failed");
      } else {
        navigation(routes.adminDashboard);
      }
    } catch (err: any) {
      console.log("_____________error");
      toast.error(err.response?.data?.error || "Login failed");
    }
  };

  return (
    <div className="container-fuild">
      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
      />
      <div className="w-100 overflow-hidden position-relative flex-wrap d-block vh-100">
        <div className="row">
          <div className="col-lg-5">
            <div className="login-background position-relative d-lg-flex align-items-center justify-content-center d-none flex-wrap vh-100">
              <div className="bg-overlay-img">
                <ImageWithBasePath
                  src="assets/img/bg/bg-01.png"
                  className="bg-1"
                  alt="Img"
                />
                <ImageWithBasePath
                  src="assets/img/bg/bg-02.png"
                  className="bg-2"
                  alt="Img"
                />
                <ImageWithBasePath
                  src="assets/img/bg/bg-03.png"
                  className="bg-3"
                  alt="Img"
                />
              </div>
              <div className="authentication-card w-100">
                <div className="authen-overlay-item border w-100">
                  <h1 className="text-white display-1">
                    Empowering people <br /> through seamless HR <br />{" "}
                    management.
                  </h1>
                  <div className="my-4 mx-auto authen-overlay-img">
                    <ImageWithBasePath
                      src="assets/img/bg/authentication-bg-01.png"
                      alt="Img"
                    />
                  </div>
                  <div>
                    <p className="text-white fs-20 fw-semibold text-center">
                      Efficiently manage your workforce, streamline <br />{" "}
                      operations effortlessly.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="col-lg-7 col-md-12 col-sm-12">
            <div className="row justify-content-center align-items-center vh-100 overflow-auto flex-wrap">
              <div className="col-md-7 mx-auto vh-100">
                <form className="vh-100">
                  <div className="vh-100 d-flex flex-column justify-content-between p-4 pb-0">
                    <div className=" mx-auto mb-5 text-center">
                      <ImageWithBasePath
                        src="assets/img/logo.svg"
                        className="img-fluid"
                        alt="Logo"
                      />
                    </div>
                    <div className="">
                      <div className="text-center mb-3">
                        <h2 className="mb-2">Sign In</h2>
                        <p className="mb-0">
                          Please enter your details to sign in
                        </p>
                      </div>
                      <div className="mb-3">
                        <label className="form-label">Username</label>
                        <div className="input-group">
                          <input
                            type="text"
                            defaultValue=""
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="form-control border-end-0"
                          />
                          <span className="input-group-text border-start-0">
                            <i className="ti ti-mail" />
                          </span>
                        </div>
                      </div>
                      <div className="mb-3">
                        <label className="form-label">Password</label>
                        <div className="pass-group">
                          <input
                            type={
                              passwordVisibility.password ? "text" : "password"
                            }
                            className="pass-input form-control"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
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
                      <div className="mb-3">
                        <button
                          type="submit"
                          className="btn btn-primary w-100"
                          onClick={handleSubmit}
                        >
                          Sign In
                        </button>
                      </div>
                    </div>
                    <div className="mt-5 pb-4 text-center">
                      <p className="mb-0 text-gray-9">
                        Copyright © 2025 - NextPiQ
                      </p>
                    </div>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
