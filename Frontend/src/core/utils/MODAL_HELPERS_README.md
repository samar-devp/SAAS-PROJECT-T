# Modal Helpers - Usage Guide

## Problem Solved
This utility module solves the common issue of **stacked modal backdrops** and **clicking not working** after closing nested modals in Bootstrap applications.

## Root Cause
When multiple modals are opened and closed in sequence:
1. Bootstrap creates a `.modal-backdrop` element for each modal
2. Sometimes these backdrops don't get cleaned up properly
3. Multiple backdrops stack on top of each other
4. The lingering backdrops block all clicks on the page
5. React and Bootstrap can sometimes try to remove the same DOM element, causing errors

## Solution
This module provides safe, defensive utility functions that:
- Check if elements exist before manipulating them
- Verify parent-child relationships before removal
- Use try-catch blocks to prevent crashes
- Provide consistent modal state management

## Functions

### `removeAllBackdrops()`
Safely removes all modal backdrops from the DOM.
```typescript
import { removeAllBackdrops } from 'core/utils/modalHelpers';

// Remove all backdrops
removeAllBackdrops();
```

### `cleanupExcessBackdrops()`
Removes all but the last backdrop (useful when opening a new modal).
```typescript
import { cleanupExcessBackdrops } from 'core/utils/modalHelpers';

// Keep only the last backdrop
cleanupExcessBackdrops();
```

### `resetBodyStyles()`
Resets body styles that Bootstrap modals add.
```typescript
import { resetBodyStyles } from 'core/utils/modalHelpers';

// Clean up body styles
resetBodyStyles();
```

### `closeModal(modalId)`
Closes a specific modal by ID.
```typescript
import { closeModal } from 'core/utils/modalHelpers';

closeModal('myModalId');
```

### `openModal(modalId)`
Opens a specific modal by ID.
```typescript
import { openModal } from 'core/utils/modalHelpers';

openModal('myModalId');
```

### `switchModal(fromModalId, toModalId, delay?)`
Switches from one modal to another with proper cleanup.
```typescript
import { switchModal } from 'core/utils/modalHelpers';

// Switch modals with 200ms delay (default)
switchModal('modal1', 'modal2');

// Custom delay
switchModal('modal1', 'modal2', 300);
```

### `cleanupAllModals()`
Completely cleans up all modal states and backdrops.
```typescript
import { cleanupAllModals } from 'core/utils/modalHelpers';

// Nuclear option - close everything
cleanupAllModals();
```

### `createBackdropCleanupInterval(intervalMs?)`
Creates a periodic cleanup interval (useful for component mounting).
```typescript
import { createBackdropCleanupInterval } from 'core/utils/modalHelpers';

useEffect(() => {
  // Automatically cleanup excess backdrops every second
  const cleanup = createBackdropCleanupInterval(1000);
  
  return cleanup; // Cleanup on unmount
}, []);
```

## Best Practices

### 1. Always use utility functions instead of direct DOM manipulation
❌ Bad:
```typescript
const backdrops = document.querySelectorAll('.modal-backdrop');
backdrops.forEach(b => b.remove()); // Can throw errors!
```

✅ Good:
```typescript
import { removeAllBackdrops } from 'core/utils/modalHelpers';
removeAllBackdrops(); // Safe, won't crash
```

### 2. Add cleanup intervals in parent components
```typescript
useEffect(() => {
  const cleanup = createBackdropCleanupInterval(1000);
  return cleanup;
}, []);
```

### 3. Clean up on modal hide events
```typescript
useEffect(() => {
  const modalElement = document.getElementById('myModal');
  if (!modalElement) return;

  const handleModalHide = () => {
    setTimeout(() => {
      removeAllBackdrops();
      resetBodyStyles();
    }, 150);
  };

  modalElement.addEventListener('hidden.bs.modal', handleModalHide);
  return () => modalElement.removeEventListener('hidden.bs.modal', handleModalHide);
}, []);
```

### 4. Clean up before opening new modals
```typescript
onClick={() => {
  removeAllBackdrops();
  closeModal('oldModal');
  resetBodyStyles();
  
  setTimeout(() => {
    openModal('newModal');
  }, 200);
}}
```

## Components Using This
- `ApplyLeaveModal.tsx` - Leave application modal
- `AssignLeaveModal.tsx` - Leave assignment modal
- `companies/index.tsx` - Parent component with cleanup interval

## Troubleshooting

### Issue: "Node to be removed is not a child" error
**Solution**: Already handled! The utility functions check for parent-child relationships before removal.

### Issue: Multiple backdrops visible
**Solution**: Use `cleanupExcessBackdrops()` or ensure cleanup interval is running.

### Issue: Page not clickable after closing modal
**Solution**: Call `removeAllBackdrops()` and `resetBodyStyles()` when closing modals.

### Issue: Modals not opening properly
**Solution**: Always clean up before opening:
```typescript
removeAllBackdrops();
resetBodyStyles();
setTimeout(() => openModal('myModal'), 200);
```

## Technical Details

### Why the delays (setTimeout)?
Bootstrap modal transitions take time. We wait for:
- Modal hide animation to complete (~150ms)
- DOM to update before manipulating it
- Smooth user experience

### Why parentNode.removeChild instead of remove()?
- More defensive - can check if parentNode exists first
- Catches edge cases where element is already detached
- Better error handling

### Why try-catch blocks?
- Prevents app crashes from DOM manipulation errors
- Handles race conditions between React and Bootstrap
- Provides debugging information via console.debug

