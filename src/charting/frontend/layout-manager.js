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
    
    /**
     * Save layout state to localStorage
     * 
     * Serializes the current layout state and stores it in localStorage
     * for persistence across page reloads.
     * 
     * @returns {boolean} True if save was successful
     * 
     * @example
     * manager.saveLayout();
     */
    saveLayout() {
        // Check if localStorage is available
        if (typeof localStorage === 'undefined') {
            console.warn('LayoutManager: localStorage not available');
            return false;
        }
        
        try {
            // Serialize layout state
            const stateToSave = {
                mainHeight: this.layoutState.mainHeight,
                subplotHeights: this.layoutState.subplotHeights,
                containerHeight: this.layoutState.containerHeight,
                timestamp: Date.now()
            };
            
            const serialized = JSON.stringify(stateToSave);
            
            // Save to localStorage
            localStorage.setItem(this.config.storageKey, serialized);
            
            console.log('LayoutManager: layout saved to localStorage');
            return true;
        } catch (error) {
            console.error('LayoutManager: failed to save layout', error);
            return false;
        }
    }
    
    /**
     * Load layout state from localStorage
     * 
     * Retrieves and deserializes saved layout state from localStorage.
     * Returns null if no saved state exists or if data is corrupted.
     * 
     * @returns {Object|null} Loaded layout state or null
     * 
     * @example
     * const savedLayout = manager.loadLayout();
     * if (savedLayout) {
     *     // Apply saved layout
     * }
     */
    loadLayout() {
        // Check if localStorage is available
        if (typeof localStorage === 'undefined') {
            console.warn('LayoutManager: localStorage not available');
            return null;
        }
        
        try {
            // Retrieve from localStorage
            const serialized = localStorage.getItem(this.config.storageKey);
            
            if (!serialized) {
                console.log('LayoutManager: no saved layout found');
                return null;
            }
            
            // Deserialize
            const loaded = JSON.parse(serialized);
            
            // Validate structure
            if (!this._isValidLayoutState(loaded)) {
                console.warn('LayoutManager: invalid saved layout structure, ignoring');
                return null;
            }
            
            console.log('LayoutManager: layout loaded from localStorage');
            return loaded;
        } catch (error) {
            console.error('LayoutManager: failed to load layout', error);
            return null;
        }
    }
    
    /**
     * Validate loaded layout state structure
     * 
     * @private
     * @param {Object} state - Layout state to validate
     * @returns {boolean} True if valid
     */
    _isValidLayoutState(state) {
        if (!state || typeof state !== 'object') {
            return false;
        }
        
        // Check for required fields
        if (typeof state.mainHeight !== 'number') {
            return false;
        }
        
        // mainHeight should be between 0 and 1
        if (state.mainHeight < 0 || state.mainHeight > 1) {
            return false;
        }
        
        return true;
    }
    
    /**
     * Initialize draggable dividers
     * 
     * Creates DraggableDivider instances for panel boundaries.
     * Divider instances are stored and managed by the LayoutManager.
     * 
     * @param {Array} config - Array of divider configurations
     * @returns {void}
     * 
     * @example
     * manager.initializeDividers([
     *     { id: 'main', type: 'main-subplot', topElement: mainPanel, bottomElement: subplotPanel }
     * ]);
     */
    initializeDividers(config) {
        if (!Array.isArray(config)) {
            console.warn('LayoutManager: initializeDividers requires array config');
            return;
        }
        
        // Clear existing dividers
        this.dividers.forEach(divider => {
            if (divider && typeof divider.destroy === 'function') {
                divider.destroy();
            }
        });
        this.dividers = [];
        
        // Create new dividers (placeholder - actual DraggableDivider integration in future)
        config.forEach(dividerConfig => {
            const divider = {
                id: dividerConfig.id,
                type: dividerConfig.type,
                config: dividerConfig,
                destroy: () => {}  // Mock destroy for now
            };
            this.dividers.push(divider);
        });
        
        console.log(`LayoutManager: initialized ${this.dividers.length} dividers`);
    }
    
    /**
     * Handle divider drag events
     * 
     * Called when a divider is dragged. Updates layout state and
     * optionally saves to localStorage.
     * 
     * @param {Object} event - Drag event data
     * @param {string} event.dividerId - ID of dragged divider
     * @param {number} event.deltaY - Vertical movement in pixels
     * @returns {void}
     * 
     * @example
     * manager.onDividerDrag({ dividerId: 'main', deltaY: 50 });
     */
    onDividerDrag(event) {
        if (!event || typeof event !== 'object') {
            return;
        }
        
        const { dividerId, deltaY } = event;
        
        console.log(`LayoutManager: divider '${dividerId}' dragged by ${deltaY}px`);
        
        // Update layout state based on drag
        // (Actual implementation would calculate new heights based on deltaY)
        // For now, just mark that state should be updated
        this.layoutState.lastDragEvent = {
            dividerId,
            deltaY,
            timestamp: Date.now()
        };
        
        // Auto-save if enabled
        if (this.config.autoSave) {
            this.saveLayout();
        }
    }
    
    /**
     * Get panel configuration
     * 
     * Returns the current panel configuration including heights
     * and layout information.
     * 
     * @returns {Array} Array of panel configurations
     * 
     * @example
     * const panels = manager.getPanelConfig();
     */
    getPanelConfig() {
        return [...this.panels];
    }
    
    /**
     * Set panel configuration
     * 
     * Updates the panel configuration with new layout information.
     * 
     * @param {Array} config - Array of panel configurations
     * @returns {void}
     * 
     * @example
     * manager.setPanelConfig([
     *     { id: 'main', height: 0.6 },
     *     { id: 'subplot1', height: 0.4 }
     * ]);
     */
    setPanelConfig(config) {
        if (!Array.isArray(config)) {
            console.warn('LayoutManager: setPanelConfig requires array');
            return;
        }
        
        this.panels = [...config];
        
        console.log(`LayoutManager: panel config updated, ${this.panels.length} panels`);
    }
}

