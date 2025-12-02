/**
 * DraggableDivider Component
 * 
 * Provides a draggable horizontal divider for resizing chart panels.
 * Supports both mouse and touch interactions for cross-device compatibility.
 * 
 * @example
 * const container = document.getElementById('chart-container');
 * const divider = new DraggableDivider(container, {
 *     minSize: 100,
 *     onDrag: (deltaY) => {
 *         // Handle resize logic
 *     }
 * });
 */

export class DraggableDivider {
    /**
     * Create a draggable divider
     * 
     * @param {HTMLElement} container - Parent container element
     * @param {Object} options - Configuration options
     * @param {number} options.minSize - Minimum size for resizable panels (default: 50)
     * @param {Function} options.onDrag - Callback fired during drag with deltaY
     * @param {Function} options.onDragStart - Callback fired when drag starts
     * @param {Function} options.onDragEnd - Callback fired when drag ends
     */
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            minSize: 50,
            onDrag: null,
            onDragStart: null,
            onDragEnd: null,
            ...options
        };
        
        // Drag state
        this.isDragging = false;
        this.startY = 0;
        this.currentY = 0;
        
        // Keyboard step size
        this.keyboardStep = options.keyboardStep || 10;
        this.keyboardStepLarge = options.keyboardStepLarge || 50;
        
        // Create and setup divider element
        this.element = this.createDividerElement();
        this.container.appendChild(this.element);
        
        // Create ARIA live region if needed
        if (options.announceChanges) {
            this.liveRegion = this.createLiveRegion();
        }
        
        // Bind event handlers
        this.boundHandleMouseDown = this.handleMouseDown.bind(this);
        this.boundHandleMouseMove = this.handleMouseMove.bind(this);
        this.boundHandleMouseUp = this.handleMouseUp.bind(this);
        this.boundHandleTouchStart = this.handleTouchStart.bind(this);
        this.boundHandleTouchMove = this.handleTouchMove.bind(this);
        this.boundHandleTouchEnd = this.handleTouchEnd.bind(this);
        this.boundHandleKeyDown = this.handleKeyDown.bind(this);
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    /**
     * Create the divider DOM element
     * @private
     */
    createDividerElement() {
        const divider = document.createElement('div');
        divider.classList.add('chart-divider');
        
        // Set individual style properties (better for testing and debugging)
        divider.style.height = '3px';
        divider.style.background = '#ccc';
        divider.style.cursor = 'ns-resize';
        divider.style.position = 'relative';
        divider.style.zIndex = '10';
        divider.style.userSelect = 'none';
        divider.style.webkitUserSelect = 'none';
        divider.style.mozUserSelect = 'none';
        divider.style.msUserSelect = 'none';
        
        // GPU acceleration hint
        divider.style.willChange = 'transform';
        
        // Accessibility attributes
        divider.setAttribute('role', 'separator');
        divider.setAttribute('aria-label', 'Resizable chart divider');
        divider.setAttribute('aria-orientation', 'horizontal');
        divider.setAttribute('tabindex', '0');
        
        // Add aria-live if announcements are enabled
        if (this.options.announceChanges) {
            divider.setAttribute('aria-live', 'polite');
        }
        
        // Add hover effect
        divider.addEventListener('mouseenter', () => {
            divider.style.background = '#999';
        });
        divider.addEventListener('mouseleave', () => {
            if (!this.isDragging) {
                divider.style.background = '#ccc';
            }
        });
        
        return divider;
    }
    
    /**
     * Create ARIA live region for announcements
     * @private
     */
    createLiveRegion() {
        const liveRegion = document.createElement('div');
        liveRegion.setAttribute('role', 'status');
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.style.position = 'absolute';
        liveRegion.style.left = '-10000px';
        liveRegion.style.width = '1px';
        liveRegion.style.height = '1px';
        liveRegion.style.overflow = 'hidden';
        
        this.container.appendChild(liveRegion);
        return liveRegion;
    }
    
    /**
     * Setup all event listeners
     * @private
     */
    setupEventListeners() {
        // Mouse events
        this.element.addEventListener('mousedown', this.boundHandleMouseDown);
        
        // Touch events
        this.element.addEventListener('touchstart', this.boundHandleTouchStart, { passive: false });
        
        // Keyboard events for accessibility
        this.element.addEventListener('keydown', this.boundHandleKeyDown);
    }
    
    /**
     * Handle mouse down event
     * @param {MouseEvent} event
     */
    handleMouseDown(event) {
        event.preventDefault();
        
        this.isDragging = true;
        this.startY = event.clientY;
        this.currentY = event.clientY;
        
        // Change divider appearance
        this.element.style.background = '#666';
        
        // Add document-level listeners for move and up
        document.addEventListener('mousemove', this.boundHandleMouseMove);
        document.addEventListener('mouseup', this.boundHandleMouseUp);
        
        // Fire onDragStart callback
        if (this.options.onDragStart) {
            this.options.onDragStart();
        }
    }
    
    /**
     * Handle mouse move event
     * @param {MouseEvent} event
     */
    handleMouseMove(event) {
        if (!this.isDragging) return;
        
        event.preventDefault();
        
        const newY = event.clientY;
        const deltaY = newY - this.currentY;
        this.currentY = newY;
        
        // Resize panels if elements are provided
        if (this.options.topElement && this.options.bottomElement) {
            this.resizePanels(deltaY);
        }
        
        // Fire onDrag callback with delta
        if (this.options.onDrag) {
            this.options.onDrag(deltaY);
        }
    }
    
    /**
     * Handle mouse up event
     */
    handleMouseUp() {
        if (!this.isDragging) return;
        
        this.isDragging = false;
        
        // Reset divider appearance
        this.element.style.background = '#ccc';
        
        // Remove document-level listeners
        document.removeEventListener('mousemove', this.boundHandleMouseMove);
        document.removeEventListener('mouseup', this.boundHandleMouseUp);
        
        // Fire onDragEnd callback
        if (this.options.onDragEnd) {
            this.options.onDragEnd();
        }
    }
    
    /**
     * Handle touch start event
     * @param {TouchEvent} event
     */
    handleTouchStart(event) {
        event.preventDefault();
        
        if (event.touches.length === 0) return;
        
        this.isDragging = true;
        this.startY = event.touches[0].clientY;
        this.currentY = event.touches[0].clientY;
        
        // Change divider appearance
        this.element.style.background = '#666';
        
        // Add document-level listeners for move and end
        document.addEventListener('touchmove', this.boundHandleTouchMove, { passive: false });
        document.addEventListener('touchend', this.boundHandleTouchEnd);
        
        // Fire onDragStart callback
        if (this.options.onDragStart) {
            this.options.onDragStart();
        }
    }
    
    /**
     * Handle touch move event
     * @param {TouchEvent} event
     */
    handleTouchMove(event) {
        if (!this.isDragging) return;
        if (event.touches.length === 0) return;
        
        event.preventDefault();
        
        const newY = event.touches[0].clientY;
        const deltaY = newY - this.currentY;
        this.currentY = newY;
        
        // Resize panels if elements are provided
        if (this.options.topElement && this.options.bottomElement) {
            this.resizePanels(deltaY);
        }
        
        // Fire onDrag callback with delta
        if (this.options.onDrag) {
            this.options.onDrag(deltaY);
        }
    }
    
    /**
     * Handle touch end event
     */
    handleTouchEnd() {
        if (!this.isDragging) return;
        
        this.isDragging = false;
        
        // Reset divider appearance
        this.element.style.background = '#ccc';
        
        // Remove document-level listeners
        document.removeEventListener('touchmove', this.boundHandleTouchMove);
        document.removeEventListener('touchend', this.boundHandleTouchEnd);
        
        // Fire onDragEnd callback
        if (this.options.onDragEnd) {
            this.options.onDragEnd();
        }
    }
    
    /**
     * Extract Y coordinate from mouse or touch event
     * @param {MouseEvent|TouchEvent} event
     * @returns {number} Y coordinate
     */
    getEventY(event) {
        if (event.touches && event.touches.length > 0) {
            return event.touches[0].clientY;
        }
        return event.clientY || 0;
    }
    
    /**
     * Constrain a size value within min/max bounds
     * @param {number} size - The size to constrain
     * @param {number} min - Minimum allowed size
     * @param {number} max - Maximum allowed size (optional)
     * @returns {number} Constrained size
     */
    constrainSize(size, min, max = Infinity) {
        if (size < min) return min;
        if (size > max) return max;
        return size;
    }
    
    /**
     * Resize adjacent panels based on drag delta
     * @param {number} deltaY - The vertical distance moved
     */
    resizePanels(deltaY) {
        const topElement = this.options.topElement;
        const bottomElement = this.options.bottomElement;
        
        if (!topElement || !bottomElement) {
            return; // No panels to resize
        }
        
        // Get current heights
        const topHeight = parseInt(topElement.style.height) || topElement.offsetHeight || 0;
        const bottomHeight = parseInt(bottomElement.style.height) || bottomElement.offsetHeight || 0;
        
        // Calculate new heights
        let newTopHeight = topHeight + deltaY;
        let newBottomHeight = bottomHeight - deltaY;
        
        // Apply constraints
        const minSize = this.options.minSize || 50;
        const maxSize = this.options.maxSize || Infinity;
        
        // Constrain top panel
        newTopHeight = this.constrainSize(newTopHeight, minSize, maxSize);
        
        // Constrain bottom panel
        newBottomHeight = this.constrainSize(newBottomHeight, minSize, maxSize);
        
        // Verify the resize is valid (both panels are within bounds)
        const totalHeight = topHeight + bottomHeight;
        const newTotalHeight = newTopHeight + newBottomHeight;
        
        // Adjust if the total changed (due to constraints)
        if (Math.abs(newTotalHeight - totalHeight) > 1) {
            // Recalculate to maintain total height
            if (newTopHeight < minSize) {
                newTopHeight = minSize;
                newBottomHeight = totalHeight - minSize;
            } else if (newBottomHeight < minSize) {
                newBottomHeight = minSize;
                newTopHeight = totalHeight - minSize;
            }
        }
        
        // Apply new heights
        topElement.style.height = `${newTopHeight}px`;
        bottomElement.style.height = `${newBottomHeight}px`;
    }
    
    /**
     * Handle keyboard navigation
     * @param {KeyboardEvent} event
     */
    handleKeyDown(event) {
        // Only handle arrow keys
        if (event.key !== 'ArrowUp' && event.key !== 'ArrowDown') {
            return;
        }
        
        event.preventDefault();
        
        // Determine step size (larger with shift key)
        const step = event.shiftKey ? this.keyboardStepLarge : this.keyboardStep;
        
        // Calculate delta based on arrow key
        const deltaY = event.key === 'ArrowDown' ? step : -step;
        
        // Resize panels if elements are provided
        if (this.options.topElement && this.options.bottomElement) {
            this.resizePanels(deltaY);
        }
        
        // Fire onDrag callback
        if (this.options.onDrag) {
            this.options.onDrag(deltaY);
        }
        
        // Announce change to screen readers
        if (this.liveRegion) {
            this.announceResize(deltaY);
        }
    }
    
    /**
     * Announce resize to screen readers
     * @private
     * @param {number} deltaY - The resize delta
     */
    announceResize(deltaY) {
        if (!this.liveRegion) return;
        
        const direction = deltaY > 0 ? 'increased' : 'decreased';
        const amount = Math.abs(deltaY);
        
        this.liveRegion.textContent = `Panel size ${direction} by ${amount} pixels`;
        
        // Clear announcement after a delay
        setTimeout(() => {
            if (this.liveRegion) {
                this.liveRegion.textContent = '';
            }
        }, 1000);
    }
    
    /**
     * Cleanup and remove the divider
     */
    destroy() {
        // Remove event listeners
        this.element.removeEventListener('mousedown', this.boundHandleMouseDown);
        this.element.removeEventListener('touchstart', this.boundHandleTouchStart);
        this.element.removeEventListener('keydown', this.boundHandleKeyDown);
        
        // Remove document-level listeners if dragging
        if (this.isDragging) {
            document.removeEventListener('mousemove', this.boundHandleMouseMove);
            document.removeEventListener('mouseup', this.boundHandleMouseUp);
            document.removeEventListener('touchmove', this.boundHandleTouchMove);
            document.removeEventListener('touchend', this.boundHandleTouchEnd);
        }
        
        // Remove live region if it exists
        if (this.liveRegion && this.liveRegion.parentElement) {
            this.liveRegion.parentElement.removeChild(this.liveRegion);
        }
        
        // Remove element from DOM
        if (this.element && this.element.parentElement) {
            this.element.parentElement.removeChild(this.element);
        }
        
        // Clear references
        this.element = null;
        this.container = null;
        this.liveRegion = null;
        this.options = null;
    }
}

