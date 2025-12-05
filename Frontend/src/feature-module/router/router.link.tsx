import { Navigate, Route } from "react-router";
import { all_routes } from "./all_routes";

import Register from "../auth/register/register";
import Login from "../auth/login/login";
import ChangePassword from "../auth/change-password";
// import Holidays from "../super-admin/hrm/holidays";
import AdminDashboard from "../adminDashboard";
import AttendanceAdmin from "../hrm/attendance/fetchModal";
// import Companies from "../super-admin/companies";
import Holidays from "../hrm/holidays/fetchModal";
import Companies from "../super-admin/companies";
import SystemOwnerOrganizations from "../super-admin/organizations";
import OrganizationDashboard from "../organization/dashboard";
import UnderConstruction from "../pages/underConstruction";
import ServiceShifts from "../hrm/shifts/fetchModal";
import LeaveTypes from "../hrm/leave/fetchModal";
import LeavePolicies from "../hrm/leave-policies/fetchModal";
import Locations from "../hrm/locations/fetchModal";
import WeekOffs from "../hrm/week-offs/fetchModal";
import EmployeeLeaves from "../hrm/leave-applications/EmployeeLeaves";
import Visits from "../crm/visit/fetchModal";
import VisitMap from "../crm/visit/VisitMap";
import Contacts from "../crm/contact/index";
import Invoices from "../invoice/index";
import AddInvoice from "../invoice/add-invoice";
import InvoicePDFView from "../invoice/invoice-pdf-view";

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
    path: routes.employeeLeaves,
    element: <EmployeeLeaves />,
  },
  {
    path: routes.workLocations,
    element: <Locations />,
  },
  {
    path: routes.weekOffs,
    element: <WeekOffs />,
  },
  {
  path: routes.attendanceadmin,
  element: <AttendanceAdmin />,
},
  {
    path: routes.securitysettings,
    element: <ChangePassword />,
  },
  {
    path: routes.organizationDashboard,
    element: <OrganizationDashboard />,
  },
  {
    path: routes.visit,
    element: <Visits />,
  },
  {
    path: routes.visitMap,
    element: <VisitMap />,
  },
  {
    path: routes.contactGrid,
    element: <Contacts />,
  },
  {
    path: routes.contactList,
    element: <Contacts />,
  },
  {
    path: routes.deactivatedEmployees,
    element: <Companies />,
  },
  {
    path: routes.invoices,
    element: <Invoices />,
  },
  {
    path: routes.addInvoice,
    element: <AddInvoice />,
  },
  {
    path: routes.editInvoice,
    element: <AddInvoice />,
  },
  {
    path: routes.invoiceDetails,
    element: <InvoicePDFView />,
  },
];
