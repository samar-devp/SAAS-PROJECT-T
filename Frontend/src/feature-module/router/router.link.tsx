import { Navigate, Route } from "react-router";
import { all_routes } from "./all_routes";

import Register from "../auth/register/register";
import Login from "../auth/login/login";
// import Holidays from "../super-admin/hrm/holidays";
import AdminDashboard from "../adminDashboard";
import AttendanceAdmin from "../hrm/attendance/fetchModal";
// import Companies from "../super-admin/companies";
import Holidays from "../hrm/holidays/fetchModal";
import Companies from "../super-admin/companies";
import UnderConstruction from "../pages/underConstruction";
import ServiceShifts from "../hrm/shifts/fetchModal";
import LeaveTypes from "../hrm/leave/fetchModal";
import LeavePolicies from "../hrm/leave-policies/fetchModal";
import Locations from "../hrm/locations/fetchModal";

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
];

export const publicRoutes = [
   {
    path: routes.adminDashboard,
    element: <Companies />,
    route: Route,
  },

      {
    path: routes.adminDashboard,
    element: <Holidays />,
    route: Route,
  },
  {
    path: "/",
    name: "Root",
    element: <Navigate to="/index" />,
    route: Route,
  },
  {
    path: routes.holidays,
    element: <Holidays />,
    route: Route,
  },
  {
    path: routes.underConstruction,
    element: <UnderConstruction />,
  },
  {
    path: routes.serviceShifts,
    element: <ServiceShifts />,
  },
  {
    path: routes.leaveTypes,
    element: <LeaveTypes />,
  },
  {
    path: routes.leavePolicies,
    element: <LeavePolicies />,
  },
  {
    path: routes.workLocations,
    element: <Locations />,
  },
  {
  path: routes.attendanceadmin,
  element: <AttendanceAdmin />,
},
];
