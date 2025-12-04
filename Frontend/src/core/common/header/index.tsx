import React, { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import {
  setDataLayout,
} from "../../data/redux/themeSettingSlice";
import ImageWithBasePath from "../imageWithBasePath";
import {
  setMobileSidebar,
  toggleMiniSidebar,
} from "../../data/redux/sidebarSlice";
import { all_routes } from "../../../feature-module/router/all_routes";
import { HorizontalSidebarData } from '../../data/json/horizontalSidebar'
import axios from "axios";
import { BACKEND_PATH } from "../../../environment";
import { toast } from "react-toastify";

interface Admin {
  id: string;
  admin_name: string;
  user_id?: string; // From new API structure
  email?: string; // From new API structure
  username?: string; // From new API structure
  phone_number?: string; // From new API structure
  status?: boolean; // From new API structure
  is_active?: boolean; // From new API structure
  user?: { // For backward compatibility with nested structure
    id: string;
    email: string;
    username: string;
    phone_number: string;
    is_active: boolean;
  };
  organization: string;
  created_at: string;
  updated_at?: string;
}

interface AdminListResponse {
  results: Admin[];
  count: number;
  next: string | null;
  previous: string | null;
  summary: {
    total: number;
    active: number;
    inactive: number;
  };
}

const Header = () => {
  const routes = all_routes;
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const dataLayout = useSelector((state: any) => state.themeSetting.dataLayout);
  const Location = useLocation();
  
  // Admin selector state for organization role
  const [admins, setAdmins] = useState<Admin[]>([]);
  const [selectedAdmin, setSelectedAdmin] = useState<Admin | null>(null);
  const [loadingAdmins, setLoadingAdmins] = useState(false);
  const role = sessionStorage.getItem("role");

  const handleLogout = () => {
    // Clear all session storage
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("refresh_token");
    sessionStorage.removeItem("user_id");
    sessionStorage.removeItem("role");
    sessionStorage.removeItem("organization_id");
    sessionStorage.removeItem("selected_admin_id");
    // Navigate to login
    navigate(routes.login);
  };

  // Fetch admins for organization role
  const fetchAdmins = async () => {
    if (role !== "organization") return;
    
    try {
      setLoadingAdmins(true);
      const token = sessionStorage.getItem("access_token");
      const response = await axios.get<{ status: number; message: string; data: AdminListResponse }>(
        `${BACKEND_PATH}organization/admins`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      
      if (response.data.status === 200 && response.data.data) {
        const data = response.data.data;
        let adminsList: Admin[] = [];
        
        if (Array.isArray(data)) {
          adminsList = data;
        } else if (data && typeof data === 'object' && data.results && Array.isArray(data.results)) {
          // Map flat API response to nested structure for backward compatibility
          adminsList = data.results.map((admin: any) => ({
            ...admin,
            user: admin.user || {
              id: admin.user_id || admin.id,
              email: admin.email || '',
              username: admin.username || '',
              phone_number: admin.phone_number || '',
              is_active: admin.is_active ?? admin.status ?? true,
            },
            is_active: admin.is_active ?? admin.status ?? true,
            status: admin.status ?? admin.is_active ?? true,
          }));
        } else {
          adminsList = [];
        }
        
        // Show all admins (both active and inactive)
        setAdmins(adminsList);
        
        // Check if there's a previously selected admin in sessionStorage
        const selectedAdminId = sessionStorage.getItem("selected_admin_id");
        if (selectedAdminId && adminsList.length > 0) {
          const foundAdmin = adminsList.find(a => (a.user?.id || a.user_id) === selectedAdminId);
          if (foundAdmin) {
            setSelectedAdmin(foundAdmin);
          } else if (adminsList.length > 0) {
            // Auto-select first admin if previously selected admin not found
            const firstAdmin = adminsList[0];
            setSelectedAdmin(firstAdmin);
            const firstAdminUserId = firstAdmin.user?.id || firstAdmin.user_id;
            if (firstAdminUserId) {
              sessionStorage.setItem("selected_admin_id", firstAdminUserId);
            }
          }
        } else if (adminsList.length > 0) {
          // Auto-select first admin if no previous selection
          const firstAdmin = adminsList[0];
          setSelectedAdmin(firstAdmin);
          const firstAdminUserId = firstAdmin.user?.id || firstAdmin.user_id;
          if (firstAdminUserId) {
            sessionStorage.setItem("selected_admin_id", firstAdminUserId);
          }
        }
      }
    } catch (error: any) {
      console.error("Error fetching admins:", error);
      // Don't show toast error in header to avoid disruption
    } finally {
      setLoadingAdmins(false);
    }
  };

  // Fetch admins on mount if organization role
  useEffect(() => {
    if (role === "organization") {
      fetchAdmins();
    }
  }, [role]);

  // Handle admin selection change
  const handleAdminSelectionChange = (adminId: string) => {
    const admin = admins.find(a => a.id === adminId);
    if (admin) {
      setSelectedAdmin(admin);
      const userId = admin.user?.id || admin.user_id;
      if (userId) {
        sessionStorage.setItem("selected_admin_id", userId);
        toast.success(`Switched to admin: ${admin.admin_name}`);
        // Refresh page after a brief delay to reload data with new admin
        setTimeout(() => {
          window.location.reload();
        }, 500);
      }
    }
  };

  // Add custom styles for profile dropdown and page background
  React.useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      .profile-dropdown .dropdown-item:hover {
        background-color: #f8f9fa !important;
        transform: translateX(4px);
      }
      .profile-dropdown .dropdown-item.text-danger:hover {
        background-color: #fee !important;
      }
      /* Page background color - light gray instead of pure white */
      body, .page-wrapper, .content {
        background-color:rgb(255, 255, 255) !important;
      }
      .page-wrapper .content {
        background-color:rgb(236, 236, 236) !important;
      }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(style);
    };
  }, []);

  const [subOpen, setSubopen] = useState<any>("");
  const [subsidebar, setSubsidebar] = useState("");

  const toggleSidebar = (title: any) => {
	localStorage.setItem("menuOpened", title);
	if (title === subOpen) {
	  setSubopen("");
	} else {
	  setSubopen(title);
	}
  };

  const toggleSubsidebar = (subitem: any) => {
	if (subitem === subsidebar) {
	  setSubsidebar("");
	} else {
	  setSubsidebar(subitem);
	}
  };
  const mobileSidebar = useSelector(
    (state: any) => state.sidebarSlice.mobileSidebar
  );

  const toggleMobileSidebar = () => {
    dispatch(setMobileSidebar(!mobileSidebar));
  };


  const handleToggleMiniSidebar = () => {
    if (dataLayout === "mini_layout") {
      dispatch(setDataLayout("default_layout"));
      localStorage.setItem("dataLayout", "default_layout");
    } else {
      dispatch(toggleMiniSidebar());
    }
  };




  const [isFullscreen, setIsFullscreen] = useState(false);
  const toggleFullscreen = () => {
    if (!isFullscreen) {
      if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen().catch((err) => {
        });
        setIsFullscreen(true);
      }
    } else {
      if (document.exitFullscreen) {
        if (document.fullscreenElement) {
          document.exitFullscreen().catch((err) => {
          });
        }
        setIsFullscreen(false);
      }
    }
  };

  return (
    <>
      {/* Header */}
      <div className="header">
			<div className="main-header">

				<div className="header-left">
					<Link to={routes.adminDashboard} className="logo">
						<ImageWithBasePath src="assets/img/logo/logo4.png" alt="Logo"   className="login-logo"/>
					</Link>
					<Link to={routes.adminDashboard} className="dark-logo">
						<ImageWithBasePath src="assets/img/logo/logo4.png" alt="Logo"/>
					</Link>
				</div>

				<Link id="mobile_btn" onClick={toggleMobileSidebar} className="mobile_btn" to="#sidebar">
					<span className="bar-icon">
						<span></span>
						<span></span>
						<span></span>
					</span>
				</Link>

				<div className="header-user">
					<div className="nav user-menu nav-list">

						<div className="me-auto d-flex align-items-center" id="header-search">
							<div className="dropdown crm-dropdown">
								<div className="dropdown-menu dropdown-lg dropdown-menu-start">
									<div className="card mb-0 border-0 shadow-none">
										<div className="card-header">
											<h4>CRM</h4>
										</div>
										<div className="card-body pb-1">		
											<div className="row">
												<div className="col-sm-6">							
													<Link to={routes.contactList} className="d-flex align-items-center justify-content-between p-2 crm-link mb-3">
														<span className="d-flex align-items-center me-3">
															<i className="ti ti-user-shield text-default me-2"></i>Contacts
														</span>
														<i className="ti ti-arrow-right"></i>
													</Link>							
													<Link to={routes.dealsGrid} className="d-flex align-items-center justify-content-between p-2 crm-link mb-3">
														<span className="d-flex align-items-center me-3">
															<i className="ti ti-heart-handshake text-default me-2"></i>Deals
														</span>
														<i className="ti ti-arrow-right"></i>
													</Link>								
													<Link to={routes.pipeline} className="d-flex align-items-center justify-content-between p-2 crm-link mb-3">
														<span className="d-flex align-items-center me-3">
															<i className="ti ti-timeline-event-text text-default me-2"></i>Pipeline
														</span>
														<i className="ti ti-arrow-right"></i>
													</Link>		
												</div>
												<div className="col-sm-6">							
													<Link to={routes.companiesGrid} className="d-flex align-items-center justify-content-between p-2 crm-link mb-3">
														<span className="d-flex align-items-center me-3">
															<i className="ti ti-building text-default me-2"></i>Companies
														</span>
														<i className="ti ti-arrow-right"></i>
													</Link>								
													<Link to={routes.leadsGrid} className="d-flex align-items-center justify-content-between p-2 crm-link mb-3">
														<span className="d-flex align-items-center me-3">
															<i className="ti ti-user-check text-default me-2"></i>Leads
														</span>
														<i className="ti ti-arrow-right"></i>
													</Link>								
													<Link to={routes.activity} className="d-flex align-items-center justify-content-between p-2 crm-link mb-3">
														<span className="d-flex align-items-center me-3">
															<i className="ti ti-activity text-default me-2"></i>Activities
														</span>
														<i className="ti ti-arrow-right"></i>
													</Link>		
												</div>
											</div>		
										</div>
									</div>
								</div>
							</div>
						</div>

						<div className="sidebar sidebar-horizontal" id="horizontal-single">
							<div className="sidebar-menu">
								<div className="main-menu">
									<ul className="nav-menu">
										<li className="menu-title">
											<span>Main</span>
										</li>
										{HorizontalSidebarData?.map((mainMenu, index) => (
											<React.Fragment key={`main-${index}`}>
												{mainMenu?.menu?.map((data, i) => (
												<li className="submenu" key={`menu-${i}`}>
													<Link to="#" className={`
														${
															data?.subMenus
																?.map((link: any) => link?.route)
																.includes(Location.pathname) 
																? "active"
																: ""
															} ${subOpen === data.menuValue ? "subdrop" : ""}`} onClick={() => toggleSidebar(data.menuValue)}>
													<i className={`ti ti-${data.icon}`}></i>
													<span>{data.menuValue}</span>
													<span className="menu-arrow"></span>
													</Link>

													{/* First-level Submenus */}
													<ul style={{ display: subOpen === data.menuValue ? "block" : "none" }}>
													{data?.subMenus?.map((subMenu:any, j) => (
														<li
														key={`submenu-${j}`}
														className={subMenu?.customSubmenuTwo ? "submenu" : ""}
														>
														<Link to={subMenu?.route || "#"} className={`${
															subMenu?.subMenusTwo
																?.map((link: any) => link?.route)
																.includes(Location.pathname) || subMenu?.route === Location.pathname
																? "active"
																: ""
															} ${subsidebar === subMenu.menuValue ? "subdrop" : ""}`} onClick={() => toggleSubsidebar(subMenu.menuValue)}>
															<span>{subMenu?.menuValue}</span>
															{subMenu?.customSubmenuTwo && <span className="menu-arrow"></span>}
														</Link>

														{/* Check if `customSubmenuTwo` exists */}
														{subMenu?.customSubmenuTwo && subMenu?.subMenusTwo && (
															<ul style={{ display: subsidebar === subMenu.menuValue ? "block" : "none" }}>
															{subMenu.subMenusTwo.map((subMenuTwo:any, k:number) => (
																<li key={`submenu-two-${k}`}>
																<Link className={subMenuTwo.route === Location.pathname?'active':''} to={subMenuTwo.route}>{subMenuTwo.menuValue}</Link>
																</li>
															))}
															</ul>
														)}
														</li>
													))}
													</ul>
												</li>
												))}
											</React.Fragment>
											))}
									</ul>
								</div>
							</div>
						</div>

					<div className="d-flex align-items-center gap-3">
						{/* Admin Selector for Organization Role */}
						{role === "organization" && (
							<div className="dropdown">
								<button
									className="btn btn-light dropdown-toggle d-flex align-items-center"
									type="button"
									id="adminSelectorDropdown"
									data-bs-toggle="dropdown"
									aria-expanded="false"
									disabled={loadingAdmins || admins.length === 0}
									style={{
										minWidth: '200px',
										justifyContent: 'space-between',
										borderRadius: '8px',
										fontSize: '14px'
									}}
								>
									<span className="d-flex align-items-center">
										<i className="ti ti-user-shield me-2"></i>
										{loadingAdmins ? (
											<span>Loading...</span>
										) : selectedAdmin ? (
											<span>{selectedAdmin.admin_name}</span>
										) : (
											<span>Select Admin</span>
										)}
									</span>
								</button>
								<ul
									className="dropdown-menu dropdown-menu-end"
									aria-labelledby="adminSelectorDropdown"
									style={{ minWidth: '250px', maxHeight: '400px', overflowY: 'auto' }}
								>
									<li>
										<h6 className="dropdown-header">Select Admin</h6>
									</li>
									{admins.length === 0 ? (
										<li>
											<span className="dropdown-item-text text-muted">No admins available</span>
										</li>
									) : (
										admins.map((admin) => (
											<li key={admin.id}>
												<button
													className={`dropdown-item d-flex align-items-center ${
														selectedAdmin?.id === admin.id ? 'active' : ''
													}`}
													onClick={() => handleAdminSelectionChange(admin.id)}
													style={{ cursor: 'pointer' }}
												>
													<i className="ti ti-check me-2" style={{ 
														visibility: selectedAdmin?.id === admin.id ? 'visible' : 'hidden' 
													}}></i>
													<div className="flex-grow-1">
														<div className="fw-medium">{admin.admin_name}</div>
														<small className="text-muted">
															{admin.user?.email || admin.user?.username || ''}
														</small>
													</div>
												</button>
											</li>
										))
									)}
									{admins.length > 0 && (
										<>
											<li><hr className="dropdown-divider" /></li>
											<li>
												<Link
													className="dropdown-item d-flex align-items-center"
													to={routes.organizationDashboard}
												>
													<i className="ti ti-dashboard me-2"></i>
													<span>Go to Dashboard</span>
												</Link>
											</li>
										</>
									)}
								</ul>
							</div>
						)}
						
						<div className="dropdown profile-dropdown">
							<Link to="#" className="dropdown-toggle d-flex align-items-center" data-bs-toggle="dropdown">
								<span className="avatar avatar-md online">
									<ImageWithBasePath src="assets/img/profiles/avatar-12.jpg" alt="Img" className="img-fluid rounded-circle"/>
								</span>
							</Link>
								<div className="dropdown-menu dropdown-menu-end shadow-lg border-0 p-0" style={{ minWidth: '200px', borderRadius: '8px' }}>
									<div className="card mb-0 border-0">
										<div className="card-body p-3">
											<Link className="dropdown-item d-flex align-items-center px-3 py-2 rounded mb-2" to={routes.securitysettings} style={{ transition: 'all 0.3s ease' }}>
												<i className="ti ti-lock me-3" style={{ fontSize: '20px' }}></i>
												<span className="fw-medium">Change Password</span>
											</Link>
										</div>
										<div className="card-footer border-top p-3 pt-2">
											<Link 
												className="dropdown-item d-flex align-items-center px-3 py-2 rounded text-danger" 
												to="#" 
												onClick={(e) => {
													e.preventDefault();
													handleLogout();
												}}
												style={{ transition: 'all 0.3s ease', cursor: 'pointer' }}
											>
												<i className="ti ti-logout me-3" style={{ fontSize: '20px' }}></i>
												<span className="fw-medium">Logout</span>
											</Link>
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>

				<div className="dropdown mobile-user-menu">
					<Link to="#" className="nav-link dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">
						<i className="fa fa-ellipsis-v"></i>
					</Link>
					<div className="dropdown-menu dropdown-menu-end">
						<Link className="dropdown-item" to={routes.securitysettings}>Change Password</Link>
						<Link 
							className="dropdown-item" 
							to="#" 
							onClick={(e) => {
								e.preventDefault();
								handleLogout();
							}}
						>
							Logout
						</Link>
					</div>
				</div>

			</div>

		</div>
      {/* /Header */}
    </>
  );
};

export default Header;
