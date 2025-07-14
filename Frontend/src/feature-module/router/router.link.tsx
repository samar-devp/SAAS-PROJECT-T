import { Navigate, Route } from "react-router";
import { all_routes } from "./all_routes";

import Register from "../auth/register/register";
import Login from "../auth/login/login";
import AdminDashboard from "../adminDashboard";
import Companies from "../super-admin/companies";
const routes = all_routes;

export const authRoutes = [
 {
    path: routes.register,
    element: <Register />,
    route: Route,
  },
  {
    path: routes.login,
    element: <Login />,
    route: Route,
  },
]

export const publicRoutes = [
    {
    path: routes.superAdminCompanies,
    element: <Companies />,
    route: Route,
  },
    {
    path: routes.adminDashboard,
    element: <Companies />,
    route: Route,
  },
  {
    path: "/",
    name: "Root",
    element: <Navigate to="/index" />,
    route: Route,
  },
]