import React from "react";
import {  Route, Routes } from "react-router";
import { authRoutes, publicRoutes } from "./router.link";
import Feature from "../feature";
import AuthFeature from "../authFeature";
import SystemOwnerOrganizations from "../super-admin/organizations";
import { all_routes } from "./all_routes";

const ALLRoutes: React.FC = () => {
  return (
    <>
      <Routes>
        {/* System Owner Organizations Page - No Sidebar */}
        <Route 
          path={all_routes.systemOwnerOrganizations} 
          element={<SystemOwnerOrganizations />} 
        />
        
        <Route element={<Feature />}>
          {publicRoutes.map((route, idx) => (
            <Route path={route.path} element={route.element} key={idx} />
          ))}
        </Route>

        <Route element={<AuthFeature />}>
          {authRoutes.map((route, idx) => (
            <Route path={route.path} element={route.element} key={idx} />
          ))}
        </Route>
      </Routes>
    </>
  );
};

export default ALLRoutes;
