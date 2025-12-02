/**
 * MultiChartManager - Manages multiple synchronized uPlot charts
 * 
 * Coordinates main OHLC chart with overlay indicators and subplot charts
 * for indicators that require separate Y-axes. Provides cursor and zoom
 * synchronization across all charts.
 */

/**
 * Default configuration for MultiChartManager
 */
const DEFAULT_CONFIG = {
    mainChart: {
        height: 400,
        width: null, // Auto-fit container
    },
    subplots: [],
    sync: {
        cursor: true,
        zoom: true,
        crosshair: true,
    },
    layout: {
        spacing: 10, // Pixels between charts
    }
};

/**
 * MultiChartManager Class
 * 
 * Manages multiple chart instances with synchronization
 */
export class MultiChartManager {
    /**
     * Create a new MultiChartManager
     * 
     * @param {HTMLElement} container - DOM element to render charts in
     * @param {Object} config - Configuration object
     * @throws {Error} If container is null or config is invalid
     */
    constructor(container, config) {
        // Validate inputs
        if (!container || !(container instanceof HTMLElement)) {
            throw new Error('Container must be a valid HTMLElement');
        }
        
        if (config === null || config === undefined || typeof config !== 'object') {
            throw new Error('Config must be a valid object');
        }
        
        // Store core properties
        this.container = container;
        this.config = this.mergeConfig(config);
        
        // Initialize chart tracking
        this.mainChart = null;
        this.subplots = [];
        this.syncedCharts = [];
        
        console.log('MultiChartManager initialized');
    }
    
    /**
     * Merge user config with defaults
     * 
     * @param {Object} userConfig - User-provided configuration
     * @returns {Object} Merged configuration
     */
    mergeConfig(userConfig) {
        return {
            mainChart: {
                ...DEFAULT_CONFIG.mainChart,
                ...(userConfig.mainChart || {})
            },
            subplots: userConfig.subplots || DEFAULT_CONFIG.subplots,
            sync: {
                ...DEFAULT_CONFIG.sync,
                ...(userConfig.sync || {})
            },
            layout: {
                ...DEFAULT_CONFIG.layout,
                ...(userConfig.layout || {})
            }
        };
    }
    
    /**
     * Initialize the multi-chart system
     * 
     * Creates containers and sets up all charts
     */
    async initialize() {
        this.createContainers();
        await this.createMainChart();
        await this.createSubplots();
        this.setupSynchronization();
    }
    
    /**
     * Calculate heights for main chart and subplots
     * 
     * Task 21.1: Dynamic height allocation based on subplot count
     * - Main chart: 60% when subplots exist, 100% otherwise
     * - Subplots: Split remaining 40% equally
     * 
     * @returns {Object} Heights object with main and subplot percentages
     */
    calculateHeights() {
        const subplotCount = this.config.subplots.length;
        
        if (subplotCount === 0) {
            return {
                main: '100%',
                subplot: '0%'
            };
        }
        
        const mainHeight = '60%';
        const subplotHeight = `${40 / subplotCount}%`;
        
        return {
            main: mainHeight,
            subplot: subplotHeight
        };
    }
    
    /**
     * Create container elements for charts
     * 
     * Task 21: Creates main chart container and subplot containers with
     * proper height calculations, IDs, and responsive styling
     */
    createContainers() {
        // Clear existing content
        this.container.innerHTML = '';
        
        // Calculate dynamic heights
        const heights = this.calculateHeights();
        
        // Task 21.2 & 21.3: Create main chart container with proper ID and styling
        const mainContainer = document.createElement('div');
        mainContainer.id = 'main-chart-container';
        mainContainer.style.height = heights.main;
        mainContainer.style.marginBottom = `${this.config.layout.spacing}px`;
        mainContainer.style.position = 'relative'; // For responsive behavior
        this.container.appendChild(mainContainer);
        
        // Task 21.2 & 21.3: Create subplot containers with unique IDs
        this.config.subplots.forEach((subplot, index) => {
            const subplotContainer = document.createElement('div');
            subplotContainer.id = `subplot-${index}-container`;
            subplotContainer.style.height = heights.subplot;
            subplotContainer.style.marginBottom = `${this.config.layout.spacing}px`;
            subplotContainer.style.position = 'relative'; // For responsive behavior
            this.container.appendChild(subplotContainer);
        });
        
        console.log(`Created ${1 + this.config.subplots.length} chart containers`);
    }
    
    /**
     * Create the main OHLC chart
     * 
     * @returns {Promise<void>}
     */
    async createMainChart() {
        // Stub implementation - will be filled in later tasks
        console.log('Creating main chart...');
    }
    
    /**
     * Create subplot charts
     * 
     * @returns {Promise<void>}
     */
    async createSubplots() {
        // Stub implementation - will be filled in later tasks
        console.log('Creating subplots...');
    }
    
    /**
     * Setup synchronization between charts
     * 
     * Implements cursor and zoom sync
     */
    setupSynchronization() {
        // Stub implementation - will be filled in later tasks
        console.log('Setting up synchronization...');
    }
    
    // === Chart Instance Management (Task 20.2) ===
    
    /**
     * Add a chart instance to the manager
     * 
     * @param {Object} chart - Chart instance with id and type
     */
    addChart(chart) {
        if (!chart || !chart.id) {
            throw new Error('Chart must have an id property');
        }
        
        this.syncedCharts.push(chart);
        
        // Track in appropriate collection
        if (chart.type === 'main') {
            this.mainChart = chart;
        } else if (chart.type === 'subplot') {
            this.subplots.push(chart);
        }
    }
    
    /**
     * Remove a chart instance from the manager
     * 
     * @param {string} chartId - ID of chart to remove
     */
    removeChart(chartId) {
        // Remove from syncedCharts
        this.syncedCharts = this.syncedCharts.filter(c => c.id !== chartId);
        
        // Remove from mainChart
        if (this.mainChart && this.mainChart.id === chartId) {
            this.mainChart = null;
        }
        
        // Remove from subplots
        this.subplots = this.subplots.filter(c => c.id !== chartId);
    }
    
    /**
     * Get a chart instance by ID
     * 
     * @param {string} chartId - ID of chart to retrieve
     * @returns {Object|null} Chart instance or null if not found
     */
    getChart(chartId) {
        return this.syncedCharts.find(c => c.id === chartId) || null;
    }
    
    /**
     * Clear all chart instances
     */
    clearCharts() {
        this.syncedCharts = [];
        this.mainChart = null;
        this.subplots = [];
    }
    
    // === Configuration Handling (Task 20.3) ===
    
    /**
     * Validate configuration object
     * 
     * @returns {boolean} True if configuration is valid
     */
    validateConfig() {
        // Basic validation
        if (!this.config || typeof this.config !== 'object') {
            return false;
        }
        
        // Validate mainChart config
        if (this.config.mainChart && typeof this.config.mainChart !== 'object') {
            return false;
        }
        
        // Validate subplots array
        if (this.config.subplots && !Array.isArray(this.config.subplots)) {
            return false;
        }
        
        return true;
    }
    
    /**
     * Get configuration for a specific chart
     * 
     * @param {string} chartId - ID of chart or 'mainChart'
     * @returns {Object|null} Chart configuration or null
     */
    getChartConfig(chartId) {
        if (chartId === 'mainChart') {
            return this.config.mainChart || null;
        }
        
        // Look for subplot config
        const subplotIndex = parseInt(chartId.replace('subplot-', ''));
        if (!isNaN(subplotIndex) && this.config.subplots[subplotIndex]) {
            return this.config.subplots[subplotIndex];
        }
        
        return null;
    }
    
    // === Public Interface Methods (Task 20.4) ===
    
    /**
     * Update chart data
     * 
     * @param {string} chartId - ID of chart to update
     * @param {Array} data - New chart data
     */
    updateChart(chartId, data) {
        const chart = this.getChart(chartId);
        if (!chart) {
            console.warn(`Chart ${chartId} not found`);
            return;
        }
        
        // Stub - will be implemented in later tasks
        console.log(`Updating chart ${chartId} with data`);
    }
    
    /**
     * Destroy a chart instance
     * 
     * @param {string} chartId - ID of chart to destroy
     */
    destroyChart(chartId) {
        const chart = this.getChart(chartId);
        if (chart && chart.destroy) {
            chart.destroy();
        }
        
        this.removeChart(chartId);
    }
    
    /**
     * Synchronize cursor position across charts
     * 
     * @param {Object} cursorData - Cursor position data
     */
    syncCursor(cursorData) {
        if (!this.config.sync.cursor) {
            return;
        }
        
        // Stub - will be implemented in later tasks
        console.log('Syncing cursor...', cursorData);
    }
    
    /**
     * Synchronize zoom level across charts
     * 
     * @param {Object} zoomData - Zoom range data
     */
    syncZoom(zoomData) {
        if (!this.config.sync.zoom) {
            return;
        }
        
        // Stub - will be implemented in later tasks
        console.log('Syncing zoom...', zoomData);
    }
}

