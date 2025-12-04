/**
 * API Helper Utilities
 * Functions to help with API calls, authentication, and session management
 */

/**
 * Get the admin ID to use for API calls
 * For organization role: returns selected_admin_id from sessionStorage
 * For admin role: returns user_id from sessionStorage
 * @returns {string | null} Admin ID or null if not found
 */
export const getAdminIdForApi = (): string | null => {
  const role = sessionStorage.getItem("role");
  const user_id = sessionStorage.getItem("user_id");
  
  // If organization role, use selected_admin_id
  if (role === "organization") {
    const selectedAdminId = sessionStorage.getItem("selected_admin_id");
    if (selectedAdminId) {
      return selectedAdminId;
    }
    // If no admin selected yet, return null (should not happen after first selection)
    return null;
  }
  
  // For admin role or others, use user_id
  return user_id;
};

/**
 * Get authentication headers for API calls
 * @returns {object} Headers object with Authorization token
 */
export const getAuthHeaders = () => {
  const token = sessionStorage.getItem("access_token");
  return {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  };
};

/**
 * Check if organization has selected an admin
 * @returns {boolean} True if admin is selected, false otherwise
 */
export const hasSelectedAdmin = (): boolean => {
  const role = sessionStorage.getItem("role");
  if (role === "organization") {
    const selectedAdminId = sessionStorage.getItem("selected_admin_id");
    return selectedAdminId !== null && selectedAdminId !== "";
  }
  return true; // For admin role, they are always "selected"
};

