import React, { useEffect, useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import CollapseHeader from "../../../core/common/collapse-header/collapse-header";
import { all_routes } from "../../router/all_routes";
import HolidaysModal from "../../../core/modals/holidaysModal";
import DeleteModal from "../../../core/modals/deleteModal"; // ✅ import delete modal

const Holidays = () => {
  const routes = all_routes;

  interface Holiday {
    id: number;
    name: string;
    holiday_date: string;
    description: string | null;
    is_optional: boolean;
  }

  const [holidayData, setHolidayData] = useState<Holiday[]>([]);
  const [selectedHoliday, setSelectedHoliday] = useState<Holiday | null>(null);
  const [deleteHolidayId, setDeleteHolidayId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const admin_id = localStorage.getItem("user_id"); // ⬅️ Get token
  console.log(admin_id, "________________________admin_id");

  // ✅ Fetch holidays
  const getHolidays = async () => {
    try {
      const response = await axios.get(
        `http://localhost:8000/api/holidays/${admin_id}`
      );
      setHolidayData(response.data);
    } catch (error) {
      console.error("❌ Error fetching holidays:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getHolidays();
  }, []);

  // ✅ Callback after delete
  const handleDeleteSuccess = () => {
    getHolidays();
    setDeleteHolidayId(null);
  };

  return (
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
          <div className="d-flex my-xl-auto right-content align-items-center flex-wrap">
            <div className="mb-2">
              <Link
                to="#"
                data-bs-toggle="modal"
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

        {/* Holiday List Card */}
        <div className="card">
          <div className="card-header d-flex align-items-center justify-content-between flex-wrap row-gap-3">
            <h5>Holidays List</h5>
          </div>
          <div className="card-body p-3">
            {loading ? (
              <p>Loading holidays…</p>
            ) : holidayData.length === 0 ? (
              <p>No holidays found.</p>
            ) : (
              <div className="table-responsive">
                <table className="table table-striped table-bordered">
                  <thead className="table-light">
                    <tr>
                      <th>Title</th>
                      <th>Date</th>
                      <th>Description</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {holidayData.map((holiday) => (
                      <tr key={holiday.id}>
                        <td>
                          <h6 className="fw-medium mb-0">{holiday.name}</h6>
                        </td>
                        <td>{holiday.holiday_date}</td>
                        <td>{holiday.description ?? "-"}</td>
                        <td>
                          <span
                            className={`badge ${
                              holiday.is_optional
                                ? "badge-success"
                                : "badge-danger"
                            }`}
                          >
                            {holiday.is_optional ? "Optional" : "Mandatory"}
                          </span>
                        </td>
                        <td>
                          <div className="action-icon d-inline-flex">
                            {/* Edit Button */}
                            <Link
                              to="#"
                              className="me-2"
                              data-bs-toggle="modal"
                              data-bs-target="#edit_holiday"
                              onClick={() => setSelectedHoliday(holiday)}
                            >
                              <i className="ti ti-edit" />
                            </Link>
                            {/* Delete Button */}
                            <Link
                              to="#"
                              data-bs-toggle="modal"
                              data-bs-target="#delete_modal"
                              onClick={() => setDeleteHolidayId(holiday.id)}
                            >
                              <i className="ti ti-trash" />
                            </Link>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="footer d-sm-flex align-items-center justify-content-between border-top bg-white p-3">
        <p className="mb-0">2014 - 2025 © SmartHR.</p>
        <p>
          Designed &amp; Developed By{" "}
          <Link to="#" className="text-primary">
            Dreams
          </Link>
        </p>
      </div>

      {/* Modals */}
      {/* ✅ DeleteModal हमेशा render करो */}
      <DeleteModal
        admin_id={admin_id}
        holidayId={deleteHolidayId}
        onDeleted={handleDeleteSuccess}
      />
    </div>
  );
};

export default Holidays;

// import React, { useEffect, useState } from "react";
// import axios from "axios";
// import { Link } from "react-router-dom";
// import CollapseHeader from "../../../core/common/collapse-header/collapse-header";
// import { all_routes } from "../../router/all_routes";
// import HolidaysModal from "../../../core/modals/holidaysModal";

// const Holidays = () => {
//   const routes = all_routes;

//   interface Holiday {
//     id: number;
//     name: string;
//     holiday_date: string;
//     description: string | null;
//     is_optional: boolean;
//   }

//   const [holidayData, setHolidayData] = useState<Holiday[]>([]);
//   const [selectedHoliday, setSelectedHoliday] = useState<Holiday | null>(null);
//   const [loading, setLoading] = useState(true);

//   const getHolidays = async () => {
//     try {
//       const response = await axios.get(
//         "http://localhost:8000/api/holidays/42d896b2-a4b2-422d-8ba2-c221bf928799"
//       );
//       console.log("✅ API response:", response.data);
//       setHolidayData(response.data);
//     } catch (error) {
//       console.error("❌ Error fetching holidays:", error);
//     } finally {
//       setLoading(false);
//     }
//   };

//   useEffect(() => {
//     getHolidays();
//   }, []);

//   return (
//     <div className="page-wrapper">
//       <div className="content">
//         {/* Breadcrumb */}
//         <div className="d-md-flex d-block align-items-center justify-content-between page-breadcrumb mb-3">
//           <div className="my-auto mb-2">
//             <h2 className="mb-1">Holidays</h2>
//             <nav>
//               <ol className="breadcrumb mb-0">
//                 <li className="breadcrumb-item">
//                   <Link to={routes.adminDashboard}>
//                     <i className="ti ti-smart-home" />
//                   </Link>
//                 </li>
//                 <li className="breadcrumb-item">Employee</li>
//                 <li className="breadcrumb-item active" aria-current="page">
//                   Holidays
//                 </li>
//               </ol>
//             </nav>
//           </div>
//           <div className="d-flex my-xl-auto right-content align-items-center flex-wrap">
//             <div className="mb-2">
//               <Link
//                 to="#"
//                 data-bs-toggle="modal"
//                 data-bs-target="#add_holiday"
//                 className="btn btn-primary d-flex align-items-center"
//               >
//                 <i className="ti ti-circle-plus me-2" />
//                 Add Holiday
//               </Link>
//             </div>
//             <div className="head-icons ms-2">
//               <CollapseHeader />
//             </div>
//           </div>
//         </div>

//         {/* Card to display holidays */}
//         <div className="card">
//           <div className="card-header d-flex align-items-center justify-content-between flex-wrap row-gap-3">
//             <h5>Holidays List</h5>
//           </div>
//           <div className="card-body p-3">
//             {loading ? (
//               <p>Loading holidays…</p>
//             ) : holidayData.length === 0 ? (
//               <p>No holidays found.</p>
//             ) : (
//               <div className="table-responsive">
//                 <table className="table table-striped table-bordered">
//                   <thead className="table-light">
//                     <tr>
//                       <th>Title</th>
//                       <th>Date</th>
//                       <th>Description</th>
//                       <th>Status</th>
//                       <th>Actions</th>
//                     </tr>
//                   </thead>
//                   <tbody>
//                     {holidayData.map((holiday) => (
//                       <tr key={holiday.id}>
//                         <td>
//                           <h6 className="fw-medium mb-0">{holiday.name}</h6>
//                         </td>
//                         <td>{holiday.holiday_date}</td>
//                         <td>{holiday.description ?? "-"}</td>
//                         <td>
//                           <span
//                             className={`badge ${
//                               holiday.is_optional
//                                 ? "badge-success"
//                                 : "badge-danger"
//                             }`}
//                           >
//                             {holiday.is_optional ? "Optional" : "Mandatory"}
//                           </span>
//                         </td>
//                         <td>
//                           <div className="action-icon d-inline-flex">
//                             <Link
//                               to="#"
//                               className="me-2"
//                               data-bs-toggle="modal"
//                               data-bs-target="#edit_holiday"
//                               onClick={() => setSelectedHoliday(holiday)}
//                             >
//                               <i className="ti ti-edit" />
//                             </Link>
//                             <Link
//                               to="#"
//                               data-bs-toggle="modal"
//                               data-bs-target="#delete_modal"
//                             >
//                               <i className="ti ti-trash" />
//                             </Link>
//                           </div>
//                         </td>
//                       </tr>
//                     ))}
//                   </tbody>
//                 </table>
//               </div>
//             )}
//           </div>
//         </div>
//       </div>

//       <div className="footer d-sm-flex align-items-center justify-content-between border-top bg-white p-3">
//         <p className="mb-0">2014 - 2025 © SmartHR.</p>
//         <p>
//           Designed &amp; Developed By{" "}
//           <Link to="#" className="text-primary">
//             Dreams
//           </Link>
//         </p>
//       </div>

//       <HolidaysModal selectedHoliday={selectedHoliday} />
//     </div>
//   );
// };

// export default Holidays;
