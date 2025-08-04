// import React, { useState } from "react";
// import axios from "axios";
// import dayjs from "dayjs"; // date picker value handle
// // import React from "react";
// import CommonSelect from "../common/commonSelect";
// import { DatePicker } from "antd";

// const HolidaysModal = () => {

//    const [title, setTitle] = useState("");
//    const [holidayDate, setHolidayDate] = useState<string>("");

//   const handleAddHoliday = async () => {
//     if (!title || !holidayDate) {
//       alert("Please fill all fields");
//       return;
//     }

//     try {
//       const response = await axios.post(
//         "http://localhost:8000/api/holidays/42d896b2-a4b2-422d-8ba2-c221bf928799",
//         {
//           name: title,
//           holiday_date: holidayDate,
//         }
//       );
//       console.log("Holiday added:", response.data);
//       // reset input fields
//       setTitle("");
//       setHolidayDate("");
//     } catch (error) {
//       console.error("Error adding holiday:", error);
//     }
//   };

//   const status = [

//     { value: "Select", label: "Select" },
//     { value: "Active", label: "Active" },
//     { value: "Inactive", label: "Inactive" },
//   ];
//   const getModalContainer = () => {
//     const modalElement = document.getElementById("modal-datepicker");
//     return modalElement ? modalElement : document.body; // Fallback to document.body if modalElement is null
//   };
//   return (
//     <>
//       {/* Add Plan */}
//       <div className="modal fade" id="add_holiday">
//         <div className="modal-dialog modal-dialog-centered modal-md">
//           <div className="modal-content">
//             <div className="modal-header">
//               <h4 className="modal-title">Add Holiday</h4>
//               <button
//                 type="button"
//                 className="btn-close custom-btn-close"
//                 data-bs-dismiss="modal"
//                 aria-label="Close"
//               >
//                 <i className="ti ti-x" />
//               </button>
//             </div>
//             <form>
//               <div className="modal-body pb-0">
//                 <div className="row">
//                   <div className="col-md-12">
//                     <div className="mb-3">
//                       <label className="form-label">Title</label>
//                       <input
//                         type="text"
//                         className="form-control"
//                         value={title}
//                         onChange={(e) => setTitle(e.target.value)}
//                       />
//                     </div>
//                   </div>
//                   <div className="col-md-12">
//                     <div className="mb-3">
//                       <label className="form-label">Date</label>
//                       <div className="input-icon-end position-relative">
//                         <DatePicker
//                           className="form-control datetimepicker"
//                           format="YYYY-MM-DD" // ✅
//                           getPopupContainer={getModalContainer}
//                           placeholder="YYYY-MM-DD"
//                           value={
//                             holidayDate
//                               ? dayjs(holidayDate, "YYYY-MM-DD")
//                               : null
//                           } // ✅ state
//                           onChange={(date, dateString) => {
//                             if (typeof dateString === "string") {
//                               setHolidayDate(dateString);
//                             } else {
//                               setHolidayDate(""); // or handle array case if needed
//                             }
//                           }} // ✅
//                         />
//                         <span className="input-icon-addon">
//                           <i className="ti ti-calendar text-gray-7" />
//                         </span>
//                       </div>
//                     </div>
//                   </div>
//                   {/* <div className="col-md-12">
//                     <div className="mb-3">
//                       <label className="form-label">Description</label>
//                       <textarea
//                         className="form-control"
//                         rows={3}
//                         defaultValue={""}
//                       />
//                     </div>
//                   </div>
//                   <div className="col-md-12">
//                     <div className="mb-3">
//                       <label className="form-label">Status</label>
//                       <CommonSelect
//                         className="select"
//                         options={status}
//                         defaultValue={status[0]}
//                       />
//                     </div> */}
//                   {/* </div> */}
//                 </div>
//               </div>
//               <div className="modal-footer">
//                 <button
//                   type="button"
//                   className="btn btn-light me-2"
//                   data-bs-dismiss="modal"
//                 >
//                   Cancel
//                 </button>
//                 <button
//                   type="button"
//                   data-bs-dismiss="modal"
//                   className="btn btn-primary"
//                   onClick={handleAddHoliday}
//                 >
//                   Add Holiday
//                 </button>
//               </div>
//             </form>
//           </div>
//         </div>
//       </div>
//       {/* /Add Plan */}
//       {/* Edit Plan */}
//       <div className="modal fade" id="edit_holiday">
//         <div className="modal-dialog modal-dialog-centered modal-md">
//           <div className="modal-content">
//             <div className="modal-header">
//               <h4 className="modal-title">Edit Holiday</h4>
//               <button
//                 type="button"
//                 className="btn-close custom-btn-close"
//                 data-bs-dismiss="modal"
//                 aria-label="Close"
//               >
//                 <i className="ti ti-x" />
//               </button>
//             </div>
//             <form>
//               <div className="modal-body pb-0">
//                 <div className="row">
//                   <div className="col-md-12">
//                     <div className="mb-3">
//                       <label className="form-label">Title</label>
//                       <input
//                         type="text"
//                         className="form-control"
//                         defaultValue="New Year"
//                       />
//                     </div>
//                   </div>
//                   <div className="col-md-12">
//                     <div className="mb-3">
//                       <label className="form-label">Date</label>
//                       <div className="input-icon-end position-relative">
//                         <DatePicker
//                           className="form-control datetimepicker"
//                           format={{
//                             format: "DD-MM-YYYY",
//                             type: "mask",
//                           }}
//                           getPopupContainer={getModalContainer}
//                           placeholder="DD-MM-YYYY"
//                         />
//                         <span className="input-icon-addon">
//                           <i className="ti ti-calendar text-gray-7" />
//                         </span>
//                       </div>
//                     </div>
//                   </div>
//                   {/* <div className="col-md-12">
//                     <div className="mb-3">
//                       <label className="form-label">Description</label>
//                       <textarea
//                         className="form-control"
//                         rows={3}
//                         defaultValue={"First day of the new year"}
//                       />
//                     </div>
//                   </div> */}
//                   {/* <div className="col-md-12">
//                     <div className="mb-3">
//                       <label className="form-label">Status</label>
//                       <CommonSelect
//                         className="select"
//                         options={status}
//                         defaultValue={status[1]}
//                       />
//                     </div>
//                   </div> */}
//                 </div>
//               </div>
//               <div className="modal-footer">
//                 <button
//                   type="button"
//                   className="btn btn-light me-2"
//                   data-bs-dismiss="modal"
//                 >
//                   Cancel
//                 </button>
//                 <button
//                   type="button"
//                   data-bs-dismiss="modal"
//                   className="btn btn-primary"
//                 >
//                   Save Changes
//                 </button>
//               </div>
//             </form>
//           </div>
//         </div>
//       </div>
//       {/* /Edit Plan */}
//     </>
//   );
// };

// export default HolidaysModal;

import React, { useState, useEffect } from "react";
import axios from "axios";
import dayjs from "dayjs";
import { DatePicker } from "antd";

interface Holiday {
  id: number;
  name: string;
  holiday_date: string;
}

const HolidaysModal: React.FC<{ selectedHoliday: Holiday | null }> = ({
  selectedHoliday,
}) => {
  // Add fields
  const [title, setTitle] = useState("");
  const [holidayDate, setHolidayDate] = useState<string>("");

  // Edit fields
  const [editTitle, setEditTitle] = useState("");
  const [editHolidayDate, setEditHolidayDate] = useState<string>("");
  const admin_id = localStorage.getItem("user_id"); // ⬅️ Get token

  // POST (Add)
  const handleAddHoliday = async () => {
    if (!title || !holidayDate) {
      alert("Please fill all fields");
      return;
    }
    try {
      const response = await axios.post(
        `http://localhost:8000/api/holidays/${admin_id}`,
        { name: title, holiday_date: holidayDate }
      );
      console.log("✅ Holiday added:", response.data);
      setTitle("");
      setHolidayDate("");
    } catch (error) {
      console.error("❌ Error adding holiday:", error);
    }
  };

  // PUT (Edit)
  const handleEditHoliday = async () => {
    if (!selectedHoliday) {
      alert("No holiday selected");
      return;
    }
    if (!editTitle || !editHolidayDate) {
      alert("Please fill all fields");
      return;
    }
    try {
      const response = await axios.put(
        `http://localhost:8000/api/holidays/42d896b2-a4b2-422d-8ba2-c221bf928799/${selectedHoliday.id}`,
        { name: editTitle, holiday_date: editHolidayDate }
      );
      console.log("✅ Holiday updated:", response.data);
      setEditTitle("");
      setEditHolidayDate("");
    } catch (error) {
      console.error("❌ Error updating holiday:", error);
    }
  };

  // Sync edit fields with selectedHoliday
  useEffect(() => {
    if (selectedHoliday) {
      setEditTitle(selectedHoliday.name);
      setEditHolidayDate(selectedHoliday.holiday_date);
    } else {
      setEditTitle("");
      setEditHolidayDate("");
    }
  }, [selectedHoliday]);

  const getModalContainer = () => {
    const modalElement = document.getElementById("modal-datepicker");
    return modalElement ? modalElement : document.body;
  };

  return (
    <>
      {/* Add Holiday Modal */}
      <div className="modal fade" id="add_holiday">
        <div className="modal-dialog modal-dialog-centered modal-md">
          <div className="modal-content">
            <div className="modal-header">
              <h4 className="modal-title">Add Holiday</h4>
              <button
                type="button"
                className="btn-close custom-btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
              >
                <i className="ti ti-x" />
              </button>
            </div>
            <form>
              <div className="modal-body pb-0">
                <div className="mb-3">
                  <label className="form-label">Title</label>
                  <input
                    type="text"
                    className="form-control"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Date</label>
                  <DatePicker
                    className="form-control datetimepicker"
                    format="YYYY-MM-DD"
                    getPopupContainer={getModalContainer}
                    placeholder="YYYY-MM-DD"
                    value={
                      holidayDate ? dayjs(holidayDate, "YYYY-MM-DD") : null
                    }
                    onChange={(date, dateString) => {
                      if (typeof dateString === "string") {
                        setHolidayDate(dateString);
                      } else {
                        setHolidayDate("");
                      }
                    }}
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-light me-2"
                  data-bs-dismiss="modal"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  data-bs-dismiss="modal"
                  onClick={handleAddHoliday}
                >
                  Add Holiday
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Edit Holiday Modal */}
      <div className="modal fade" id="edit_holiday">
        <div className="modal-dialog modal-dialog-centered modal-md">
          <div className="modal-content">
            <div className="modal-header">
              <h4 className="modal-title">Edit Holiday</h4>
              <button
                type="button"
                className="btn-close custom-btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
              >
                <i className="ti ti-x" />
              </button>
            </div>
            <form>
              <div className="modal-body pb-0">
                <div className="mb-3">
                  <label className="form-label">Title</label>
                  <input
                    type="text"
                    className="form-control"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Date</label>
                  <DatePicker
                    className="form-control datetimepicker"
                    format="YYYY-MM-DD"
                    getPopupContainer={getModalContainer}
                    placeholder="YYYY-MM-DD"
                    value={
                      editHolidayDate
                        ? dayjs(editHolidayDate, "YYYY-MM-DD")
                        : null
                    }
                    onChange={(date, dateString) => {
                      if (typeof dateString === "string") {
                        setEditHolidayDate(dateString);
                      } else {
                        setEditHolidayDate("");
                      }
                    }}
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-light me-2"
                  data-bs-dismiss="modal"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  data-bs-dismiss="modal"
                  onClick={handleEditHoliday}
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
};

export default HolidaysModal;
