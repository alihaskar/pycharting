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
        
        // Create and setup divider element
        this.element = this.createDividerElement();
        this.container.appendChild(this.element);
        
        // Bind event handlers
        this.boundHandleMouseDown = this.handleMouseDown.bind(this);
        this.boundHandleMouseMove = this.handleMouseMove.bind(this);
        this.boundHandleMouseUp = this.handleMouseUp.bind(this);
        this.boundHandleTouchStart = this.handleTouchStart.bind(this);
        this.boundHandleTouchMove = this.handleTouchMove.bind(this);
        this.boundHandleTouchEnd = this.handleTouchEnd.bind(this);
        
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
     * Setup all event listeners
     * @private
     */
    setupEventListeners() {
        // Mouse events
        this.element.addEventListener('mousedown', this.boundHandleMouseDown);
        
        // Touch events
        this.element.addEventListener('touchstart', this.boundHandleTouchStart, { passive: false });
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
     * Cleanup and remove the divider
     */
    destroy() {
        // Remove event listeners
        this.element.removeEventListener('mousedown', this.boundHandleMouseDown);
        this.element.removeEventListener('touchstart', this.boundHandleTouchStart);
        
        // Remove document-level listeners if dragging
        if (this.isDragging) {
            document.removeEventListener('mousemove', this.boundHandleMouseMove);
            document.removeEventListener('mouseup', this.boundHandleMouseUp);
            document.removeEventListener('touchmove', this.boundHandleTouchMove);
            document.removeEventListener('touchend', this.boundHandleTouchEnd);
        }
        
        // Remove element from DOM
        if (this.element && this.element.parentElement) {
            this.element.parentElement.removeChild(this.element);
        }
        
        // Clear references
        this.element = null;
        this.container = null;
        this.options = null;
    }
}

