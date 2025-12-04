/**
 * Modal Helper Utilities
 * 
 * This module provides utility functions to manage Bootstrap modals and their backdrops.
 * It helps prevent issues with stacked backdrops and improper modal state cleanup.
 */

/**
 * Removes all modal backdrops from the DOM
 * Safely checks if element still has a parent before removing
 */
export const removeAllBackdrops = (): void => {
  const backdrops = document.querySelectorAll('.modal-backdrop');
  backdrops.forEach(backdrop => {
    try {
      // Check if the element still has a parent node before removing
      if (backdrop && backdrop.parentNode) {
        backdrop.parentNode.removeChild(backdrop);
      }
    } catch (error) {
      // Silently catch any removal errors to prevent crashes
      console.debug('Backdrop already removed:', error);
    }
  });
};

/**
 * Removes all but the last backdrop (useful when opening a new modal)
 * Safely checks if element still has a parent before removing
 */
export const cleanupExcessBackdrops = (): void => {
  const backdrops = document.querySelectorAll('.modal-backdrop');
  // Keep only the last backdrop
  for (let i = 0; i < backdrops.length - 1; i++) {
    try {
      const backdrop = backdrops[i];
      // Check if the element still has a parent node before removing
      if (backdrop && backdrop.parentNode) {
        backdrop.parentNode.removeChild(backdrop);
      }
    } catch (error) {
      // Silently catch any removal errors to prevent crashes
      console.debug('Backdrop already removed:', error);
    }
  }
};

/**
 * Resets body styles that Bootstrap modals add
 */
export const resetBodyStyles = (): void => {
  document.body.classList.remove('modal-open');
  document.body.style.overflow = '';
  document.body.style.paddingRight = '';
  document.body.style.removeProperty('overflow');
  document.body.style.removeProperty('padding-right');
};

/**
 * Closes a specific modal by ID
 * @param modalId - The ID of the modal to close
 */
export const closeModal = (modalId: string): void => {
  const modal = document.getElementById(modalId);
  const $ = (window as any).jQuery || (window as any).$;
  
  if ($) {
    $(`#${modalId}`).modal('hide');
  } else if (modal) {
    modal.classList.remove('show');
    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');
    modal.removeAttribute('aria-modal');
  }
};

/**
 * Opens a specific modal by ID
 * @param modalId - The ID of the modal to open
 */
export const openModal = (modalId: string): void => {
  const modal = document.getElementById(modalId);
  const $ = (window as any).jQuery || (window as any).$;
  
  if ($) {
    try {
      $(`#${modalId}`).modal('show');
    } catch (error) {
      console.error('Error opening modal with jQuery:', error);
    }
  } else if (modal) {
    try {
      modal.classList.add('show');
      modal.style.display = 'block';
      modal.setAttribute('aria-hidden', 'false');
      modal.setAttribute('aria-modal', 'true');
      document.body.classList.add('modal-open');
      
      // Add single backdrop
      const backdrop = document.createElement('div');
      backdrop.className = 'modal-backdrop fade show';
      document.body.appendChild(backdrop);
    } catch (error) {
      console.error('Error opening modal manually:', error);
    }
  }
};

/**
 * Completely cleans up all modal states and backdrops
 */
export const cleanupAllModals = (): void => {
  // Close all modals
  const modals = document.querySelectorAll('.modal.show');
  modals.forEach(modal => {
    try {
      modal.classList.remove('show');
      (modal as HTMLElement).style.display = 'none';
      modal.setAttribute('aria-hidden', 'true');
      modal.removeAttribute('aria-modal');
    } catch (error) {
      console.debug('Error cleaning up modal:', error);
    }
  });
  
  // Remove all backdrops
  removeAllBackdrops();
  
  // Reset body
  resetBodyStyles();
};

/**
 * Switches from one modal to another with proper cleanup
 * @param fromModalId - ID of the modal to close
 * @param toModalId - ID of the modal to open
 * @param delay - Optional delay in ms before opening the new modal (default: 200)
 */
export const switchModal = (
  fromModalId: string,
  toModalId: string,
  delay: number = 200
): void => {
  // Close the source modal
  closeModal(fromModalId);
  
  // Wait for transition, then clean up and open new modal
  setTimeout(() => {
    // Remove all backdrops
    removeAllBackdrops();
    
    // Reset body
    resetBodyStyles();
    
    // Small delay to ensure clean state
    setTimeout(() => {
      // Double-check cleanup
      removeAllBackdrops();
      
      // Open new modal
      openModal(toModalId);
    }, 100);
  }, delay);
};

/**
 * Creates a backdrop cleanup interval (useful for component mounting)
 * @param intervalMs - How often to check for excess backdrops (default: 1000ms)
 * @returns Cleanup function to clear the interval
 */
export const createBackdropCleanupInterval = (
  intervalMs: number = 1000
): (() => void) => {
  const intervalId = setInterval(() => {
    const backdrops = document.querySelectorAll('.modal-backdrop');
    if (backdrops.length > 1) {
      // If more than one backdrop exists, remove all but the last one
      for (let i = 0; i < backdrops.length - 1; i++) {
        try {
          const backdrop = backdrops[i];
          // Check if the element still has a parent node before removing
          if (backdrop && backdrop.parentNode) {
            backdrop.parentNode.removeChild(backdrop);
          }
        } catch (error) {
          // Silently catch any removal errors
          console.debug('Backdrop already removed in interval:', error);
        }
      }
    }
  }, intervalMs);
  
  // Return cleanup function
  return () => clearInterval(intervalId);
};

