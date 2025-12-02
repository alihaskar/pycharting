/**
 * LayoutManager - Manages multiple draggable dividers and layout state
 * 
 * Coordinates multiple DraggableDivider instances to create a flexible,
 * resizable layout for chart panels. Handles layout calculations, state
 * persistence, and responsive behavior.
 * 
 * @module layout-manager
 */

/**
 * Default configuration for LayoutManager
 */
const DEFAULT_CONFIG = {
    minMainHeight: 0.2,      // Minimum 20% for main chart
    maxMainHeight: 0.8,      // Maximum 80% for main chart
    minSubplotHeight: 100,   // Minimum 100px per subplot
    debounceDelay: 150,      // 150ms debounce for resize events
    storageKey: 'chart-layout-state',  // localStorage key
    autoSave: true           // Automatically save layout changes
};

/**
 * LayoutManager class for managing chart panel layout
 * 
 * @class
 */
export class LayoutManager {
    /**
     * Create a LayoutManager instance
     * 
     * @param {HTMLElement} container - The container element for the layout
     * @param {Object} options - Configuration options
     * @param {number} options.minMainHeight - Minimum height ratio for main chart (0-1)
     * @param {number} options.maxMainHeight - Maximum height ratio for main chart (0-1)
     * @param {number} options.minSubplotHeight - Minimum height in pixels for subplots
     * @param {number} options.debounceDelay - Debounce delay for resize events in ms
     * @param {string} options.storageKey - localStorage key for state persistence
     * @param {boolean} options.autoSave - Enable automatic layout saving
     * 
     * @throws {Error} If container is not provided or invalid
     * 
     * @example
     * const container = document.getElementById('chart-container');
     * const manager = new LayoutManager(container, {
     *     minMainHeight: 0.3,
     *     maxMainHeight: 0.7
     * });
     * manager.initialize();
     */
    constructor(container, options = {}) {
        // Validate container
        if (!container) {
            throw new Error('LayoutManager: container element is required');
        }
        
        // Check if container is valid (HTMLElement in browser or mock in Node.js)
        const isHTMLElement = typeof HTMLElement !== 'undefined' && container instanceof HTMLElement;
        const isMockElement = this._isMockElement(container);
        
        if (!isHTMLElement && !isMockElement) {
            throw new Error('LayoutManager: container must be an HTMLElement');
        }
        
        // Store container reference
        this.container = container;
        
        // Merge configuration with defaults
        this.config = {
            ...DEFAULT_CONFIG,
            ...options
        };
        
        // Initialize state
        this.dividers = [];
        this.panels = [];
        this.layoutState = {
            initialized: false,
            mainHeight: null,
            subplotHeights: [],
            containerHeight: null
        };
        
        // ResizeObserver and debounce state
        this.resizeObserver = null;
        this.debounceTimer = null;
        this.isDestroyed = false;
    }
    
    /**
     * Check if object is a mock element (for testing)
     * @private
     */
    _isMockElement(obj) {
        return obj && typeof obj === 'object' && 'tagName' in obj;
    }
    
    /**
     * Initialize the layout manager
     * 
     * Sets up the initial layout, creates dividers, and starts
     * monitoring for container size changes.
     * 
     * @returns {LayoutManager} Returns this for method chaining
     * 
     * @example
     * manager.initialize();
     */
    initialize() {
        if (this.layoutState.initialized) {
            console.warn('LayoutManager: already initialized');
            return this;
        }
        
        // Mark as initialized
        this.layoutState.initialized = true;
        this.isDestroyed = false;
        
        // Setup resize observer
        this.setupResizeObserver();
        
        console.log('LayoutManager: initialized');
        
        return this;
    }
    
    /**
     * Setup ResizeObserver to monitor container size changes
     * 
     * Creates a ResizeObserver that watches the container element
     * and triggers debounced layout recalculations on resize.
     * 
     * @private
     * @returns {void}
     * 
     * @example
     * this.setupResizeObserver();
     */
    setupResizeObserver() {
        // Check if ResizeObserver is available
        if (typeof ResizeObserver === 'undefined') {
            console.warn('LayoutManager: ResizeObserver not available');
            return;
        }
        
        // Create debounced resize handler
        const debouncedResize = (entries) => {
            // Clear existing timer
            if (this.debounceTimer) {
                clearTimeout(this.debounceTimer);
            }
            
            // Set new timer
            this.debounceTimer = setTimeout(() => {
                this.handleResize(entries);
                this.debounceTimer = null;
            }, this.config.debounceDelay);
        };
        
        // Create ResizeObserver
        this.resizeObserver = new ResizeObserver(debouncedResize);
        
        // Observe container
        this.resizeObserver.observe(this.container);
        
        console.log('LayoutManager: ResizeObserver setup complete');
    }
    
    /**
     * Handle container resize events
     * 
     * Called after debounce delay when container size changes.
     * Recalculates layout and updates panel dimensions.
     * 
     * @private
     * @param {ResizeObserverEntry[]} entries - ResizeObserver entries
     * @returns {void}
     * 
     * @example
     * this.handleResize(entries);
     */
    handleResize(entries) {
        if (this.isDestroyed || !this.layoutState.initialized) {
            return;
        }
        
        // Get new container dimensions
        const entry = entries?.[0];
        if (!entry) {
            return;
        }
        
        const newHeight = entry.contentRect?.height || entry.target?.offsetHeight || 0;
        
        // Update layout state
        this.layoutState.containerHeight = newHeight;
        
        console.log('LayoutManager: container resized to', newHeight);
        
        // TODO: Recalculate layout (will be implemented in next subtask)
    }
    
    /**
     * Destroy the layout manager and clean up resources
     * 
     * Removes all dividers, stops monitoring, clears state,
     * and removes event listeners.
     * 
     * @example
     * manager.destroy();
     */
    destroy() {
        if (this.isDestroyed) {
            return;
        }
        
        // Clear dividers
        this.dividers.forEach(divider => {
            if (divider && typeof divider.destroy === 'function') {
                divider.destroy();
            }
        });
        this.dividers = [];
        
        // Clear panels
        this.panels = [];
        
        // Stop resize observer
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
            this.resizeObserver = null;
        }
        
        // Clear debounce timer
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
            this.debounceTimer = null;
        }
        
        // Reset state
        this.layoutState = {
            initialized: false,
            mainHeight: null,
            subplotHeights: [],
            containerHeight: null
        };
        
        this.isDestroyed = true;
        
        console.log('LayoutManager: destroyed');
    }
    
    /**
     * Get the current configuration
     * 
     * @returns {Object} Current configuration object
     * 
     * @example
     * const config = manager.getConfiguration();
     * console.log(config.minMainHeight);
     */
    getConfiguration() {
        return { ...this.config };
    }
    
    /**
     * Set configuration options
     * 
     * Updates configuration by merging with existing config.
     * Does not remove existing properties.
     * 
     * @param {Object} newConfig - New configuration options to merge
     * @returns {LayoutManager} Returns this for method chaining
     * 
     * @example
     * manager.setConfiguration({ minMainHeight: 0.25 });
     */
    setConfiguration(newConfig) {
        if (!newConfig || typeof newConfig !== 'object') {
            console.warn('LayoutManager: invalid configuration provided');
            return this;
        }
        
        // Merge new config with existing
        this.config = {
            ...this.config,
            ...newConfig
        };
        
        console.log('LayoutManager: configuration updated', this.config);
        
        return this;
    }
    
    /**
     * Get the current layout state
     * 
     * @returns {Object} Current layout state
     * 
     * @example
     * const state = manager.getState();
     * console.log(state.mainHeight);
     */
    getState() {
        return { ...this.layoutState };
    }
    
    /**
     * Check if the layout manager is initialized
     * 
     * @returns {boolean} True if initialized
     * 
     * @example
     * if (manager.isInitialized()) {
     *     // Do something
     * }
     */
    isInitialized() {
        return this.layoutState.initialized && !this.isDestroyed;
    }
    
    /**
     * Calculate panel heights with constraints
     * 
     * Applies min/max constraints and converts between percentages
     * and pixel values. Ensures layout is valid and feasible.
     * 
     * @param {Object} layout - Layout configuration
     * @param {number} layout.mainHeight - Main chart height as ratio (0-1)
     * @param {number} layout.subplotCount - Number of subplot panels
     * @returns {Object} Calculated layout with pixel values
     * 
     * @example
     * const result = manager.calculateHeights({
     *     mainHeight: 0.6,
     *     subplotCount: 2
     * });
     * // Returns: { mainHeight: 0.6, mainHeightPx: 600, subplotHeights: [200, 200], ... }
     */
    calculateHeights(layout) {
        const containerHeight = this.container.offsetHeight || this.layoutState.containerHeight || 600;
        const subplotCount = layout.subplotCount || 0;
        
        // Start with requested main height
        let mainHeight = layout.mainHeight || 0.6;
        
        // Enforce min/max constraints for main height
        mainHeight = Math.max(mainHeight, this.config.minMainHeight);
        mainHeight = Math.min(mainHeight, this.config.maxMainHeight);
        
        // Calculate remaining space for subplots
        let subplotSpace = 1.0 - mainHeight;
        let subplotSpacePx = containerHeight * subplotSpace;
        
        // Check if subplots meet minimum height requirement
        if (subplotCount > 0) {
            const minTotalSubplotPx = subplotCount * this.config.minSubplotHeight;
            
            if (subplotSpacePx < minTotalSubplotPx) {
                // Adjust main height to accommodate subplot minimum
                subplotSpacePx = minTotalSubplotPx;
                subplotSpace = subplotSpacePx / containerHeight;
                mainHeight = 1.0 - subplotSpace;
                
                // Ensure main height still meets minimum
                if (mainHeight < this.config.minMainHeight) {
                    mainHeight = this.config.minMainHeight;
                    subplotSpace = 1.0 - mainHeight;
                    subplotSpacePx = containerHeight * subplotSpace;
                }
            }
        }
        
        // Calculate individual subplot heights (evenly distributed)
        const subplotHeights = [];
        if (subplotCount > 0) {
            const heightPerSubplot = subplotSpacePx / subplotCount;
            for (let i = 0; i < subplotCount; i++) {
                subplotHeights.push(heightPerSubplot);
            }
        }
        
        // Convert to pixels
        const mainHeightPx = containerHeight * mainHeight;
        
        return {
            mainHeight,
            mainHeightPx,
            subplotSpace,
            subplotSpacePx,
            subplotHeights,
            containerHeight,
            valid: this.validateConstraints({
                mainHeight,
                subplotCount,
                containerHeight
            })
        };
    }
    
    /**
     * Validate layout constraints
     * 
     * Checks if the requested layout configuration is feasible
     * given the current constraints and container size.
     * 
     * @param {Object} layout - Layout to validate
     * @param {number} layout.mainHeight - Main chart height ratio
     * @param {number} layout.subplotCount - Number of subplots
     * @param {number} [layout.containerHeight] - Container height in pixels
     * @returns {boolean} True if layout is valid
     * 
     * @example
     * const valid = manager.validateConstraints({
     *     mainHeight: 0.6,
     *     subplotCount: 2
     * });
     */
    validateConstraints(layout) {
        const containerHeight = layout.containerHeight || this.container.offsetHeight || this.layoutState.containerHeight || 600;
        const mainHeight = layout.mainHeight || 0.6;
        const subplotCount = layout.subplotCount || 0;
        
        // Check main height constraints
        if (mainHeight < this.config.minMainHeight) {
            return false;
        }
        if (mainHeight > this.config.maxMainHeight) {
            return false;
        }
        
        // Check subplot minimum height
        if (subplotCount > 0) {
            const subplotSpacePx = containerHeight * (1.0 - mainHeight);
            const heightPerSubplot = subplotSpacePx / subplotCount;
            
            if (heightPerSubplot < this.config.minSubplotHeight) {
                // Check if it's even possible to fit all subplots
                const minRequiredSpace = subplotCount * this.config.minSubplotHeight;
                const maxAvailableSpace = containerHeight * (1.0 - this.config.minMainHeight);
                
                if (minRequiredSpace > maxAvailableSpace) {
                    return false;  // Impossible configuration
                }
            }
        }
        
        return true;
    }
}

