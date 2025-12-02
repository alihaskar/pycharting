/**
 * MultiChartManager - Manages multiple synchronized uPlot charts
 * 
 * Coordinates main OHLC chart with overlay indicators and subplot charts
 * for indicators that require separate Y-axes. Provides cursor and zoom
 * synchronization across all charts.
 */

import { DraggableDivider } from './divider.js';

/**
 * Draw candlestick paths for uPlot OHLC rendering
 * @param {Object} u - uPlot instance
 * @param {number} seriesIdx - Series index
 * @param {number} idx0 - Start index
 * @param {number} idx1 - End index
 * @returns {Object} SVG path object with stroke and fill paths
 */
function candlestickPaths(u, seriesIdx, idx0, idx1) {
    const data = u.data;
    const timestamps = data[0];
    const opens = data[1];
    const highs = data[2];
    const lows = data[3];
    const closes = data[4];
    
    let pathUp = '';
    let pathDown = '';
    
    const candleWidth = Math.max(2, (u.bbox.width / (idx1 - idx0)) * 0.6);
    
    for (let i = idx0; i <= idx1; i++) {
        if (opens[i] == null || closes[i] == null) continue;
        
        const x = Math.round(u.valToPos(timestamps[i], 'x', true));
        const open = u.valToPos(opens[i], 'price', true);
        const high = u.valToPos(highs[i], 'price', true);
        const low = u.valToPos(lows[i], 'price', true);
        const close = u.valToPos(closes[i], 'price', true);
        
        const isUp = closes[i] >= opens[i];
        const halfWidth = candleWidth / 2;
        
        // Draw wick (high-low line)
        const wick = `M ${x} ${high} L ${x} ${low}`;
        
        // Draw body (open-close rectangle)
        const bodyTop = Math.min(open, close);
        const bodyBottom = Math.max(open, close);
        const bodyHeight = Math.abs(bodyBottom - bodyTop);
        
        const body = bodyHeight > 0
            ? `M ${x - halfWidth} ${bodyTop} L ${x + halfWidth} ${bodyTop} L ${x + halfWidth} ${bodyBottom} L ${x - halfWidth} ${bodyBottom} Z`
            : `M ${x - halfWidth} ${bodyTop} L ${x + halfWidth} ${bodyTop}`;
        
        if (isUp) {
            pathUp += wick + ' ' + body + ' ';
        } else {
            pathDown += wick + ' ' + body + ' ';
        }
    }
    
    return {
        stroke: new Path2D(pathDown),
        fill: new Path2D(pathUp)
    };
}

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
        this.chartData = null; // Stores data loaded via loadAndRender
        
        // Task 6.1: Dynamic container management
        this.subplotContainers = [];
        this.mainChartWrapper = null;
        this.subplotsWrapper = null;
        this.dividers = [];
        
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
     * Setup draggable dividers between charts
     * 
     * Task 26.1: Divider implementation
     */
    setupDividers() {
        console.log('Setting up dividers...');
        
        // Clear existing dividers
        this.dividers.forEach(d => d.destroy());
        this.dividers = [];
        
        const subplotCount = this.subplots.length;
        if (subplotCount === 0) {
            return;
        }
        
        // 1. Divider between Main Chart and First Subplot
        const mainContainer = document.getElementById('main-chart-container');
        const firstSubplotContainer = document.getElementById('subplot-0-container');
        
        if (mainContainer && firstSubplotContainer) {
            this.createDivider(mainContainer, firstSubplotContainer, this.mainChart, this.subplots[0]);
        }
        
        // 2. Dividers between Subplots
        for (let i = 0; i < subplotCount - 1; i++) {
            const topContainer = document.getElementById(`subplot-${i}-container`);
            const bottomContainer = document.getElementById(`subplot-${i+1}-container`);
            
            if (topContainer && bottomContainer) {
                this.createDivider(topContainer, bottomContainer, this.subplots[i], this.subplots[i+1]);
            }
        }
        
        console.log(`Created ${this.dividers.length} dividers`);
    }

    /**
     * Create a single divider between two chart containers
     * 
     * @param {HTMLElement} topContainer
     * @param {HTMLElement} bottomContainer
     * @param {Object} topChart - uPlot instance
     * @param {Object} bottomChart - uPlot instance
     */
    createDivider(topContainer, bottomContainer, topChart, bottomChart) {
        // Create a temporary container for the divider to prevent it from auto-appending
        const tempContainer = document.createElement('div');
        
        const divider = new DraggableDivider(tempContainer, {
            topElement: topContainer,
            bottomElement: bottomContainer,
            minSize: 100, // Minimum height for any chart
            onDrag: () => {
                // Resize uPlot instances to match new container dimensions
                if (topChart && topContainer) {
                    topChart.setSize({
                        width: topContainer.clientWidth,
                        height: topContainer.clientHeight
                    });
                }
                
                if (bottomChart && bottomContainer) {
                    bottomChart.setSize({
                        width: bottomContainer.clientWidth,
                        height: bottomContainer.clientHeight
                    });
                }
            }
        });
        
        // Remove from temp container and insert in correct position
        divider.element.remove();
        
        // Insert divider in DOM between the two containers
        if (bottomContainer && bottomContainer.parentNode) {
            bottomContainer.parentNode.insertBefore(divider.element, bottomContainer);
        }
        
        this.dividers.push(divider);
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
        this.setupDividers();
        this.setupSynchronization();
    }
    
    // =========================================================================
    // Task 6.1: Dynamic Container Creation for N Subplots
    // =========================================================================
    
    /**
     * Get the count of subplots from config
     * @returns {number} Number of subplots configured
     */
    getSubplotCount() {
        return this.config.subplots ? this.config.subplots.length : 0;
    }
    
    /**
     * Create N subplot containers based on indicator count
     * 
     * @param {number} count - Number of subplot containers to create
     */
    createSubplotContainers(count) {
        // Clear existing containers first
        this.clearSubplotContainers();
        
        // Create N new containers
        for (let i = 0; i < count; i++) {
            const container = document.createElement('div');
            container.id = `subplot-container-${i}`;
            container.style.position = 'relative';
            container.style.minHeight = '100px';
            
            // Add class for styling
            if (container.classList) {
                container.classList.add('subplot-container');
            }
            
            // Add dataset for indicator mapping
            container._dataset = container._dataset || {};
            if (this.config.subplots && this.config.subplots[i]) {
                container._dataset.indicator = this.config.subplots[i].name;
                container._dataset.index = i;
            }
            
            this.subplotContainers.push(container);
        }
        
        console.log(`Created ${count} subplot containers`);
    }
    
    /**
     * Clear all existing subplot containers
     */
    clearSubplotContainers() {
        // Remove from DOM
        this.subplotContainers.forEach(container => {
            if (container.parentElement) {
                container.parentElement.removeChild(container);
            }
        });
        
        // Clear array
        this.subplotContainers = [];
    }
    
    /**
     * Create the container hierarchy with main chart and subplots wrappers
     */
    createContainerHierarchy() {
        // Clear existing content
        this.container.innerHTML = '';
        
        // Create main chart wrapper
        this.mainChartWrapper = document.createElement('div');
        this.mainChartWrapper.id = 'main-chart-wrapper';
        this.mainChartWrapper.style.position = 'relative';
        this.container.appendChild(this.mainChartWrapper);
        
        // Create subplots wrapper
        this.subplotsWrapper = document.createElement('div');
        this.subplotsWrapper.id = 'subplots-wrapper';
        this.subplotsWrapper.style.position = 'relative';
        this.container.appendChild(this.subplotsWrapper);
        
        console.log('Container hierarchy created');
    }
    
    // =========================================================================
    // Task 6.2: CSS Grid/Flexbox Layout Algorithm
    // =========================================================================
    
    /**
     * Apply CSS Grid layout to container
     */
    applyGridLayout() {
        this.container.style.display = 'grid';
        
        // Calculate grid rows based on subplots
        const subplotCount = this.getSubplotCount();
        const mainHeight = subplotCount > 0 ? '60%' : '100%';
        
        if (subplotCount > 0) {
            const subplotHeight = `${40 / subplotCount}%`;
            const rows = [mainHeight, ...Array(subplotCount).fill(subplotHeight)];
            this.container.style.gridTemplateRows = rows.join(' ');
        } else {
            this.container.style.gridTemplateRows = mainHeight;
        }
        
        this.container.style.gridTemplateColumns = '1fr';
        this.container.style.gap = `${this.config.layout?.spacing || 4}px`;
        
        console.log('Grid layout applied');
    }
    
    /**
     * Apply CSS Flexbox layout to container
     */
    applyFlexLayout() {
        this.container.style.display = 'flex';
        this.container.style.flexDirection = 'column';
        this.container.style.gap = `${this.config.layout?.spacing || 4}px`;
        
        console.log('Flex layout applied');
    }
    
    /**
     * Get layout configuration
     * @returns {Object} Layout config with mode and settings
     */
    getLayoutConfig() {
        return {
            mode: this.config.layout?.mode || 'flex',
            spacing: this.config.layout?.spacing || 4,
            minSubplotHeight: this.config.layout?.minSubplotHeight || 100
        };
    }
    
    /**
     * Calculate responsive breakpoints based on container width
     * @returns {Object} Breakpoint configuration
     */
    calculateResponsiveBreakpoints() {
        const width = this.container.offsetWidth || 800;
        
        if (width < 480) {
            return { size: 'xs', columns: 1, minHeight: 80 };
        } else if (width < 768) {
            return { size: 'sm', columns: 1, minHeight: 100 };
        } else if (width < 1024) {
            return { size: 'md', columns: 1, minHeight: 120 };
        } else {
            return { size: 'lg', columns: 1, minHeight: 150 };
        }
    }
    
    /**
     * Apply layout based on configuration
     */
    applyLayout() {
        const layoutConfig = this.getLayoutConfig();
        
        if (layoutConfig.mode === 'grid') {
            this.applyGridLayout();
        } else {
            this.applyFlexLayout();
        }
    }
    
    // =========================================================================
    // Task 6.3: Height Calculation and Virtualization
    // =========================================================================
    
    /**
     * Calculate individual subplot heights
     * 
     * For <=10 subplots: Equal distribution
     * For >10 subplots: Minimum height with scrolling
     * 
     * @returns {number[]} Array of heights in pixels
     */
    calculateSubplotHeights() {
        const count = this.getSubplotCount();
        if (count === 0) return [];
        
        const containerHeight = this.container.offsetHeight || 600;
        const mainChartHeight = containerHeight * 0.6;
        const availableHeight = containerHeight - mainChartHeight;
        const minHeight = this.config.layout?.minSubplotHeight || 100;
        
        if (count <= 10) {
            // Equal distribution
            const heightPerSubplot = Math.max(minHeight, availableHeight / count);
            return Array(count).fill(heightPerSubplot);
        } else {
            // Fixed minimum height with scrolling
            return Array(count).fill(minHeight);
        }
    }
    
    /**
     * Check if scrolling should be enabled for subplots
     * @returns {boolean} True if scrolling needed
     */
    shouldEnableScrolling() {
        const count = this.getSubplotCount();
        if (count <= 10) return false;
        
        const containerHeight = this.container.offsetHeight || 600;
        const mainChartHeight = containerHeight * 0.6;
        const availableHeight = containerHeight - mainChartHeight;
        const minHeight = this.config.layout?.minSubplotHeight || 100;
        
        return count * minHeight > availableHeight;
    }
    
    /**
     * Get indices of visible subplots based on scroll position
     * 
     * @param {number} scrollTop - Current scroll position
     * @returns {number[]} Array of visible subplot indices
     */
    getVisibleSubplots(scrollTop = 0) {
        const count = this.getSubplotCount();
        if (count === 0) return [];
        
        const heights = this.calculateSubplotHeights();
        const viewportHeight = (this.container.offsetHeight || 600) * 0.4;
        const bufferZone = 50; // Extra pixels for smooth scrolling
        
        const visibleStart = scrollTop - bufferZone;
        const visibleEnd = scrollTop + viewportHeight + bufferZone;
        
        const visible = [];
        let currentTop = 0;
        
        for (let i = 0; i < count; i++) {
            const height = heights[i];
            const subplotBottom = currentTop + height;
            
            // Check if subplot is in visible range
            if (subplotBottom >= visibleStart && currentTop <= visibleEnd) {
                visible.push(i);
            }
            
            currentTop = subplotBottom;
        }
        
        return visible;
    }
    
    /**
     * Apply virtualization to render only visible subplots
     */
    applyVirtualization() {
        if (!this.shouldEnableScrolling()) {
            console.log('Virtualization not needed');
            return;
        }
        
        // Enable scrolling on subplot container
        if (this.subplotsWrapper) {
            this.subplotsWrapper.style.overflowY = 'auto';
            this.subplotsWrapper.style.maxHeight = `${(this.container.offsetHeight || 600) * 0.4}px`;
        }
        
        console.log('Virtualization applied');
    }
    
    /**
     * Get total height needed for all subplots
     * @returns {number} Total height in pixels
     */
    getTotalSubplotAreaHeight() {
        const heights = this.calculateSubplotHeights();
        return heights.reduce((sum, h) => sum + h, 0);
    }
    
    // =========================================================================
    // Task 6.4: Enhanced uPlot Synchronization for N Subplots
    // =========================================================================
    
    /**
     * Register a chart for cursor/zoom synchronization
     * @param {Object} chart - uPlot chart instance
     */
    registerChartForSync(chart) {
        if (!chart) return;
        
        if (!this.syncedCharts.includes(chart)) {
            this.syncedCharts.push(chart);
            console.log(`Chart registered for sync, total: ${this.syncedCharts.length}`);
        }
    }
    
    /**
     * Unregister a chart from synchronization
     * @param {Object} chart - uPlot chart instance to remove
     */
    unregisterChartFromSync(chart) {
        const index = this.syncedCharts.indexOf(chart);
        if (index > -1) {
            this.syncedCharts.splice(index, 1);
            console.log(`Chart unregistered from sync, remaining: ${this.syncedCharts.length}`);
        }
    }
    
    /**
     * Broadcast cursor position to all synchronized charts
     * @param {Object} position - Cursor position { left, top }
     * @param {Object} sourceChart - Chart that triggered the event
     */
    broadcastCursorPosition(position, sourceChart) {
        if (this._syncInProgress) return;
        
        this._syncInProgress = true;
        
        this.syncedCharts.forEach(chart => {
            if (chart !== sourceChart && chart.setCursor) {
                chart.setCursor(position);
            }
        });
        
        // Reset sync lock after brief delay
        setTimeout(() => {
            this._syncInProgress = false;
        }, 10);
    }
    
    /**
     * Broadcast zoom range to all synchronized charts
     * @param {Object} range - Zoom range { min, max }
     * @param {Object} sourceChart - Chart that triggered the event
     */
    broadcastZoomRange(range, sourceChart) {
        if (this._syncInProgress) return;
        
        this._syncInProgress = true;
        
        this.syncedCharts.forEach(chart => {
            if (chart !== sourceChart && chart.setScale) {
                chart.setScale('x', range);
            }
        });
        
        setTimeout(() => {
            this._syncInProgress = false;
        }, 10);
    }
    
    /**
     * Get synchronization status
     * @returns {Object} Sync status info
     */
    getSyncStatus() {
        return {
            chartCount: this.syncedCharts.length,
            cursorSyncEnabled: this.config.sync?.cursor !== false,
            zoomSyncEnabled: this.config.sync?.zoom !== false,
            syncInProgress: this._syncInProgress || false
        };
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
        
        // Task 21.2 & 21.3: Create main chart container with proper ID and styling
        const mainContainer = document.createElement('div');
        mainContainer.id = 'main-chart-container';
        
        // Use fixed height for scrollable layout
        const subplotCount = this.config.subplots?.length || 0;
        if (subplotCount > 0) {
            mainContainer.style.height = '500px'; // Fixed height for main chart
        } else {
            mainContainer.style.height = '600px'; // Larger when no subplots
        }
        
        mainContainer.style.position = 'relative'; // For responsive behavior
        this.container.appendChild(mainContainer);
        
        // Task 21.2 & 21.3: Create subplot containers with unique IDs
        this.config.subplots.forEach((subplot, index) => {
            const subplotContainer = document.createElement('div');
            subplotContainer.id = `subplot-${index}-container`;
            
            // Use fixed height for scrollable layout
            subplotContainer.style.height = '200px'; // Fixed height for each subplot
            subplotContainer.style.position = 'relative'; // For responsive behavior
            
            this.container.appendChild(subplotContainer);
        });
        
        console.log(`Created ${1 + this.config.subplots.length} chart containers`);
    }
    
    /**
     * Fetch chart data from API or data source
     * 
     * Task 22.3: Data fetching and formatting
     * @returns {Promise<Array>} uPlot-compatible data array
     */
    async fetchChartData() {
        // Return real data if loaded via loadAndRender
        if (this.chartData && Array.isArray(this.chartData)) {
            console.log('Using loaded chart data, points:', this.chartData[0]?.length || 0);
            return this.chartData;
        }
        
        console.warn('No chart data loaded, using mock data');
        // Fallback to mock data for testing
        const mockData = [
            // Timestamps
            [1609459200000, 1609545600000, 1609632000000],
            // Open
            [100, 102, 101],
            // High
            [105, 108, 106],
            // Low
            [98, 100, 99],
            // Close
            [103, 101, 104],
            // Overlay 1 (if configured)
            [101, 102, 103],
            // Overlay 2 (if configured)
            [102, 103, 104]
        ];
        
        return mockData;
    }
    
    /**
     * Get candlestick fill color based on price movement
     * 
     * Task 22.5: Color management for candlesticks
     * @param {Object} u - uPlot instance
     * @param {number} seriesIdx - Series index
     * @param {Array} ohlcData - [timestamp, open, high, low, close]
     * @returns {string} Color string
     */
    getCandlestickFill(u, seriesIdx, ohlcData) {
        if (!ohlcData || ohlcData.length < 5) {
            return '#888888';
        }
        
        const [, open, , , close] = ohlcData;
        
        // Bullish (close > open) = green
        // Bearish (close <= open) = red
        return close > open ? '#26a69a' : '#ef5350';
    }
    
    /**
     * Get indicator color from palette
     * 
     * Task 22.5: Color management for overlays
     * @param {string} indicatorName - Name of the indicator
     * @returns {string} Color string
     */
    getIndicatorColor(indicatorName) {
        // Color palette for indicators
        const colors = [
            '#2196F3', // Blue
            '#FF9800', // Orange
            '#4CAF50', // Green
            '#9C27B0', // Purple
            '#F44336', // Red
            '#00BCD4', // Cyan
            '#FFEB3B', // Yellow
            '#795548'  // Brown
        ];
        
        // Use hash of indicator name to get consistent color
        let hash = 0;
        for (let i = 0; i < indicatorName.length; i++) {
            hash = ((hash << 5) - hash) + indicatorName.charCodeAt(i);
            hash = hash & hash; // Convert to 32bit integer
        }
        
        return colors[Math.abs(hash) % colors.length];
    }
    
    /**
     * Create series configuration for uPlot
     * 
     * Task 22.1 & 22.2: Candlestick and overlay series config
     * @param {Array<string>} overlays - List of overlay indicator names
     * @returns {Array} Series configuration array
     */
    createSeriesConfig(overlays = []) {
        const series = [
            // X-axis (time)
            { label: 'Time' },
            
            // OHLC Candlesticks (Task 22.1)
            {
                label: 'OHLC',
                paths: candlestickPaths,
                points: { show: false },
                stroke: "#ef5350",  // Red for bearish candles  
                fill: "#26a69a",    // Green for bullish candles
                width: 1.5,
                scale: 'price'
            }
        ];
        
        // Add overlay series (Task 22.2)
        overlays.forEach(overlayName => {
            series.push({
                label: overlayName,
                stroke: this.getIndicatorColor(overlayName),
                width: 2,
                scale: 'price' // Share price axis
            });
        });
        
        return series;
    }
    
    /**
     * Create axes configuration with shared scaling
     * 
     * Task 22.4: Y-axis scaling coordination
     * @returns {Array} Axes configuration
     */
    createAxesConfig() {
        return [
            // X-axis (time)
            {
                scale: 'x',
                space: 50,
                incrs: [
                    60,           // 1 minute
                    3600,         // 1 hour
                    86400,        // 1 day
                    604800,       // 1 week
                    2592000,      // ~1 month
                ]
            },
            // Y-axis (price) - shared by OHLC and overlays (Task 22.4)
            {
                scale: 'price',
                space: 50,
                side: 1, // Right side
            }
        ];
    }
    
    /**
     * Create the main OHLC chart with overlays
     * 
     * Task 22: Complete main chart implementation
     * @returns {Promise<void>}
     */
    async createMainChart() {
        console.log('Creating main chart with overlays...');
        
        // Get overlays from config
        const overlays = this.config.overlays || [];
        
        // Fetch data (Task 22.3)
        const data = await this.fetchChartData();
        
        // Create series configuration (Task 22.1 & 22.2)
        const series = this.createSeriesConfig(overlays);
        
        // Create axes configuration (Task 22.4)
        const axes = this.createAxesConfig();
        
        // Get main chart container
        const mainContainer = document.getElementById('main-chart-container');
        if (!mainContainer) {
            console.error('Main chart container not found');
            return;
        }
        
        // Configuration for uPlot
        const opts = {
            width: mainContainer.clientWidth || 800,
            height: parseInt(this.config.mainChart.height) || 400,
            series: series,
            axes: axes,
            scales: {
                x: { time: true },
                price: { auto: true } // Auto-scale based on data
            },
            cursor: {
                drag: {
                    x: false,  // Disable select-box zoom
                    y: false
                }
            },
            hooks: {
                ready: [
                    (u) => {
                        // Add mouse wheel zoom
                        u.over.addEventListener('wheel', (e) => {
                            e.preventDefault();
                            const { left } = u.cursor;
                            const xVal = u.posToVal(left, 'x');
                            const xScale = u.scales.x;
                            const min = xScale.min;
                            const max = xScale.max;
                            const range = max - min;
                            
                            const zoomFactor = e.deltaY < 0 ? 0.9 : 1.1;
                            const newRange = range * zoomFactor;
                            const leftRatio = (xVal - min) / range;
                            
                            u.setScale('x', {
                                min: xVal - newRange * leftRatio,
                                max: xVal + newRange * (1 - leftRatio)
                            });
                        });
                        
                        // Add drag-to-pan functionality
                        let isDragging = false;
                        let startX = 0;
                        let startScale = { min: 0, max: 0 };
                        
                        u.over.addEventListener('mousedown', (e) => {
                            isDragging = true;
                            startX = e.clientX;
                            const xScale = u.scales.x;
                            startScale = { min: xScale.min, max: xScale.max };
                            u.over.style.cursor = 'grabbing';
                        });
                        
                        u.over.addEventListener('mousemove', (e) => {
                            if (!isDragging) return;
                            
                            const dx = e.clientX - startX;
                            const range = startScale.max - startScale.min;
                            const pxToVal = range / u.bbox.width;
                            const shift = -dx * pxToVal;
                            
                            u.setScale('x', {
                                min: startScale.min + shift,
                                max: startScale.max + shift
                            });
                        });
                        
                        u.over.addEventListener('mouseup', () => {
                            isDragging = false;
                            u.over.style.cursor = 'grab';
                        });
                        
                        u.over.addEventListener('mouseleave', () => {
                            isDragging = false;
                            u.over.style.cursor = 'grab';
                        });
                        
                        u.over.style.cursor = 'grab';
                    }
                ],
                setCursor: [
                    (u) => {
                        // Display OHLC values on hover
                        const idx = u.cursor.idx;
                        if (idx === null) return;
                        
                        const timestamp = data[0][idx];
                        const open = data[1][idx];
                        const high = data[2][idx];
                        const low = data[3][idx];
                        const close = data[4][idx];
                        
                        // Create or update OHLC display element
                        let ohlcDisplay = document.getElementById('ohlc-display');
                        if (!ohlcDisplay) {
                            ohlcDisplay = document.createElement('div');
                            ohlcDisplay.id = 'ohlc-display';
                            ohlcDisplay.style.position = 'absolute';
                            ohlcDisplay.style.top = '10px';
                            ohlcDisplay.style.left = '10px';
                            ohlcDisplay.style.background = 'rgba(0,0,0,0.75)';
                            ohlcDisplay.style.color = 'white';
                            ohlcDisplay.style.padding = '8px 12px';
                            ohlcDisplay.style.borderRadius = '4px';
                            ohlcDisplay.style.fontSize = '12px';
                            ohlcDisplay.style.fontFamily = 'monospace';
                            ohlcDisplay.style.pointerEvents = 'none';
                            ohlcDisplay.style.zIndex = '1000';
                            mainContainer.appendChild(ohlcDisplay);
                        }
                        
                        const date = new Date(timestamp).toLocaleString();
                        const color = close >= open ? '#26a69a' : '#ef5350';
                        
                        ohlcDisplay.innerHTML = `
                            <div style="font-weight: bold; margin-bottom: 4px;">${date}</div>
                            <div>O: <span style="color: ${color}">${open?.toFixed(2)}</span></div>
                            <div>H: <span style="color: ${color}">${high?.toFixed(2)}</span></div>
                            <div>L: <span style="color: ${color}">${low?.toFixed(2)}</span></div>
                            <div>C: <span style="color: ${color}">${close?.toFixed(2)}</span></div>
                        `;
                    }
                ]
            }
        };
        
        // Create the actual uPlot chart instance
        this.mainChart = new uPlot(opts, data, mainContainer);
        
        console.log(`Main chart created with ${overlays.length} overlays`);
    }
    
    /**
     * Extract data for a specific subplot indicator
     * 
     * Task 23.4: Data extraction for subplot indicators
     * @param {Array} fullData - Complete dataset from fetchChartData
     * @param {string} indicatorName - Name of indicator to extract
     * @param {number} dataIndex - Index in data array where indicator data is located
     * @returns {Array} [timestamps, indicatorData]
     */
    extractSubplotData(fullData, indicatorName, dataIndex) {
        if (!fullData || fullData.length < 2) {
            return [[], []];
        }
        
        // Return timestamps and specific indicator data
        return [
            fullData[0], // timestamps
            fullData[dataIndex] || [] // indicator data at specified index
        ];
    }
    
    /**
     * Detect chart type based on indicator name
     * 
     * Task 23.5: Chart type detection
     * @param {string} indicatorName - Name of the indicator
     * @returns {string} Chart type: 'line', 'area', or 'histogram'
     */
    detectChartType(indicatorName) {
        const lower = indicatorName.toLowerCase();
        
        // Histogram indicators
        if (lower.includes('volume') || lower.includes('vol')) {
            return 'histogram';
        }
        
        // Area chart indicators (e.g., Bollinger Bands)
        if (lower.includes('bb') || lower.includes('band')) {
            return 'area';
        }
        
        // Default to line chart
        return 'line';
    }
    
    /**
     * Create series configuration for subplot
     * 
     * Task 23.1 & 23.5: Subplot series with chart type handling
     * @param {string} indicatorName - Name of the indicator
     * @param {string} chartType - Type of chart (line/area/histogram)
     * @returns {Array} Series configuration
     */
    createSubplotSeriesConfig(indicatorName, chartType = 'line') {
        const series = [
            // X-axis (time)
            { label: 'Time' },
            
            // Indicator series
            {
                label: indicatorName,
                stroke: this.getIndicatorColor(indicatorName),
                width: 2,
                scale: `${indicatorName}_scale`
            }
        ];
        
        // Apply chart type specific configuration
        if (chartType === 'histogram') {
            series[1].paths = 'bars';
            series[1].width = 1;
        } else if (chartType === 'area') {
            series[1].fill = this.getIndicatorColor(indicatorName) + '33'; // Add transparency
        }
        
        return series;
    }
    
    /**
     * Create axes configuration for subplot
     * 
     * Task 23.2: Independent y-axis configuration
     * @param {string} indicatorName - Name of the indicator
     * @returns {Array} Axes configuration
     */
    createSubplotAxesConfig(indicatorName) {
        return [
            // X-axis (shared/synchronized - Task 23.3)
            {
                scale: 'x',
                show: false // Hide x-axis labels on subplots (main chart shows them)
            },
            // Y-axis (independent per subplot - Task 23.2)
            {
                scale: `${indicatorName}_scale`,
                side: 1, // Right side
                space: 40
            }
        ];
    }
    
    /**
     * Create scale configuration for subplot
     * 
     * Task 23.6: Scale management per subplot
     * @param {string} indicatorName - Name of the indicator
     * @returns {Object} Scale configuration
     */
    createScaleConfig(indicatorName) {
        return {
            auto: true, // Auto-scale based on data
            range: (u, min, max) => {
                // Add 5% padding to top and bottom
                const padding = (max - min) * 0.05;
                return [min - padding, max + padding];
            }
        };
    }
    
    /**
     * Get subplot height from configuration
     * 
     * @returns {number} Height in pixels
     */
    getSubplotHeight() {
        const subplotCount = this.config.subplots.length;
        if (subplotCount === 0) return 0;
        
        // Default subplot height or from config
        return this.config.subplots[0].height || 150;
    }
    
    /**
     * Create subplot charts
     * 
     * Task 23: Complete subplot implementation
     * @returns {Promise<void>}
     */
    async createSubplots() {
        console.log('Creating subplots...');
        
        if (!this.config.subplots || this.config.subplots.length === 0) {
            console.log('No subplots configured');
            return;
        }
        
        // Fetch data
        const fullData = await this.fetchChartData();
        
        // Create each subplot (Task 23.1)
        this.config.subplots.forEach((subplot, index) => {
            const indicatorName = subplot.name || `subplot_${index}`;
            const chartType = subplot.type || this.detectChartType(indicatorName);
            
            // Extract data for this subplot (Task 23.4)
            const subplotData = this.extractSubplotData(
                fullData, 
                indicatorName, 
                index + 5 // Skip timestamps + OHLC data (indices 0-4)
            );
            
            // Create series configuration (Task 23.1 & 23.5)
            const series = this.createSubplotSeriesConfig(indicatorName, chartType);
            
            // Create axes configuration (Task 23.2 & 23.3)
            const axes = this.createSubplotAxesConfig(indicatorName);
            
            // Create scale configuration (Task 23.6)
            const scales = {
                x: { time: true }, // Shared time scale (Task 23.3)
                [`${indicatorName}_scale`]: this.createScaleConfig(indicatorName)
            };
            
            // Get subplot container
            const subplotContainer = document.getElementById(`subplot-${index}-container`);
            if (!subplotContainer) {
                console.warn(`Subplot container ${index} not found`);
                return;
            }
            
            // Configuration for uPlot
            const opts = {
                width: subplotContainer.clientWidth || 800,
                height: this.getSubplotHeight(),
                series: series,
                axes: axes,
                scales: scales
            };
            
            // Create the actual uPlot chart instance
            const chart = new uPlot(opts, subplotData, subplotContainer);
            this.subplots.push(chart);
            
            console.log(`Created subplot ${index}: ${indicatorName} (${chartType})`);
        });
        
        console.log(`Total subplots created: ${this.subplots.length}`);
    }
    
    /**
     * Throttle function calls for performance optimization
     * 
     * Task 24.4: Performance optimization
     * @param {Function} func - Function to throttle
     * @param {number} delay - Delay in milliseconds
     * @returns {Function} Throttled function
     */
    throttle(func, delay) {
        let lastCall = 0;
        return function(...args) {
            const now = Date.now();
            if (now - lastCall >= delay) {
                lastCall = now;
                return func.apply(this, args);
            }
        };
    }
    
    /**
     * Propagate cursor position to all charts
     * 
     * Task 24.3: Event propagation logic
     * @param {Object} sourceChart - Chart that triggered the cursor update
     * @param {Object} position - Cursor position {left, top}
     */
    propagateCursorPosition(sourceChart, position) {
        if (!this.config.sync.cursor) {
            return;
        }
        
        // Update all charts except the source
        this.syncedCharts.forEach(chart => {
            if (chart !== sourceChart && chart.setCursor) {
                try {
                    // Update cursor position (false = don't trigger event)
                    chart.setCursor(position, false);
                } catch (e) {
                    console.warn('Failed to update cursor on chart:', e);
                }
            }
        });
    }
    
    /**
     * Setup cursor event handlers for all charts
     * 
     * Task 24.2: Cursor event handling
     */
    setupCursorHandlers() {
        // Create throttled cursor update function (Task 24.4)
        const throttledUpdate = this.throttle(
            (sourceChart, position) => {
                this.propagateCursorPosition(sourceChart, position);
            },
            16 // ~60fps
        );
        
        // Setup cursor handlers for each chart
        this.syncedCharts.forEach(chart => {
            if (!chart || !chart.over) {
                return;
            }
            
            // Listen to cursor move events
            const handleMouseMove = (e) => {
                if (!e || !chart.over) return;
                
                // Calculate cursor position relative to chart
                const rect = chart.over.getBoundingClientRect?.() || { left: 0, top: 0 };
                const position = {
                    left: e.clientX - rect.left,
                    top: e.clientY - rect.top
                };
                
                // Propagate to other charts (throttled)
                throttledUpdate(chart, position);
            };
            
            // Bind event listener
            if (chart.over.addEventListener) {
                chart.over.addEventListener('mousemove', handleMouseMove);
            }
        });
    }
    
    /**
     * Setup synchronization between charts
     * 
     * Task 24: Complete cursor synchronization implementation
     */
    setupSynchronization() {
        console.log('Setting up cursor and zoom synchronization...');
        
        if (!this.config.sync.cursor && !this.config.sync.zoom) {
            console.log('Synchronization disabled in config');
            return;
        }
        
        // Task 24.1: Collect all chart instances
        this.syncedCharts = [];
        
        if (this.mainChart) {
            this.syncedCharts.push(this.mainChart);
        }
        
        if (this.subplots && this.subplots.length > 0) {
            this.syncedCharts.push(...this.subplots);
        }
        
        console.log(`Collected ${this.syncedCharts.length} charts for synchronization`);
        
        if (this.syncedCharts.length === 0) {
            console.warn('No charts available for synchronization');
            return;
        }
        
        // Task 24.1: Create sync group (simplified for testing)
        this.syncGroup = {
            id: 'charts',
            charts: this.syncedCharts,
            cursor: this.config.sync.cursor,
            zoom: this.config.sync.zoom
        };
        
        // Task 24.2 & 24.3: Setup cursor event handlers with propagation
        if (this.config.sync.cursor) {
            this.setupCursorHandlers();
            console.log('Cursor synchronization enabled');
        }
        
        // Task 25: Zoom and pan synchronization
        if (this.config.sync.zoom) {
            this.setupZoomPanSync();
            console.log('Zoom synchronization enabled');
        }
        
        console.log('Synchronization setup complete');
    }
    
    // === Zoom and Pan Synchronization (Task 25) ===
    
    /**
     * Check if an axis should be synchronized
     * 
     * Task 25.3: Y-axis independence preservation
     * @param {string} axisKey - Axis key (e.g., 'x', 'y', 'price')
     * @returns {boolean} True if axis should be synced
     */
    shouldSyncAxis(axisKey) {
        // Only sync x-axis (time)
        return axisKey === 'x';
    }
    
    /**
     * Propagate zoom/pan scale to all charts
     * 
     * Task 25.2: X-axis synchronization logic
     * Task 25.4: Infinite loop prevention
     * @param {Object} sourceChart - Chart that triggered the scale change
     * @param {string} axisKey - Axis that changed
     * @param {Object} scaleRange - New scale range {min, max}
     */
    propagateZoomScale(sourceChart, axisKey, scaleRange) {
        if (!this.config.sync.zoom) {
            return;
        }
        
        // Task 25.3: Only sync x-axis
        if (!this.shouldSyncAxis(axisKey)) {
            return;
        }
        
        // Task 25.4: Prevent infinite loops
        if (this._syncInProgress) {
            return;
        }
        
        this._syncInProgress = true;
        
        try {
            // Task 25.2: Propagate to other charts
            this.syncedCharts.forEach(chart => {
                if (chart !== sourceChart && chart.setScale) {
                    try {
                        chart.setScale(axisKey, scaleRange);
                    } catch (e) {
                        console.warn('Failed to sync scale on chart:', e);
                    }
                }
            });
        } finally {
            // Reset flag after propagation
            this._syncInProgress = false;
        }
    }
    
    /**
     * Register scale event hooks on charts
     * 
     * Task 25.1: Scale event hook infrastructure
     */
    registerScaleHooks() {
        this.syncedCharts.forEach(chart => {
            if (!chart || !chart.hooks) {
                return;
            }
            
            // Create hooks array if it doesn't exist
            if (!chart.hooks.setScale) {
                chart.hooks = chart.hooks || {};
                chart.hooks.setScale = [];
            }
            
            // Add scale change hook
            const scaleHook = (u, scaleKey) => {
                // Get the scale that changed
                const scale = u.scales?.[scaleKey];
                if (!scale) return;
                
                // Propagate to other charts
                this.propagateZoomScale(chart, scaleKey, {
                    min: scale.min,
                    max: scale.max
                });
            };
            
            chart.hooks.setScale.push(scaleHook);
        });
    }
    
    /**
     * Setup zoom and pan synchronization
     * 
     * Task 25: Complete zoom/pan sync implementation
     * Task 25.5: Gesture handling
     */
    setupZoomPanSync() {
        console.log('Setting up zoom/pan synchronization...');
        
        // Initialize sync flag (Task 25.4)
        this._syncInProgress = false;
        
        // Task 25.1: Register scale event hooks
        this.registerScaleHooks();
        
        console.log('Zoom/pan synchronization configured');
        
        // Task 25.5: Gesture handling would be handled by uPlot's built-in
        // mouse wheel and drag handlers, which trigger the setScale hooks
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
    
    /**
     * Load data and render charts (compatibility method for app.js)
     * 
     * @param {string} filename - CSV filename to load
     * @param {Object} options - Loading options
     * @returns {Promise<void>}
     */
    async loadAndRender(filename, options = {}) {
        try {
            // Show loading state
            this.container.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #999;">Loading chart data...</div>';
            
            // Build API URL
            const params = new URLSearchParams({ filename });
            
            // Extract overlays and subplots from options or config
            let overlays = [];
            let subplots = [];
            
            // Priority 1: Use overlays/subplots from options if provided
            if (options.overlays && Array.isArray(options.overlays)) {
                overlays = options.overlays;
            } else if (this.config.overlays && Array.isArray(this.config.overlays)) {
                // Priority 2: Use from config (set during initialization from URL)
                overlays = this.config.overlays;
            }
            
            if (options.subplots && Array.isArray(options.subplots)) {
                subplots = options.subplots;
            } else if (this.config.subplots && Array.isArray(this.config.subplots)) {
                // Priority 2: Use from config (set during initialization from URL)
                subplots = this.config.subplots;
            }
            
            // Helper function to convert UI format (RSI:14) to CSV format (rsi_14)
            const convertIndicatorName = (uiName) => {
                // RSI:14 -> rsi_14, SMA:20 -> sma_20, EMA:12 -> ema_12
                return uiName.toLowerCase().replace(':', '_');
            };
            
            // Priority 3: Convert from indicators array (UI format)
            if (overlays.length === 0 && subplots.length === 0 && options.indicators && Array.isArray(options.indicators)) {
                // Classify based on common patterns
                // SMA/EMA are overlays, RSI/MACD are subplots
                options.indicators.forEach(ind => {
                    const csvName = convertIndicatorName(ind);
                    const indLower = ind.toLowerCase();
                    
                    if (indLower.startsWith('sma') || indLower.startsWith('ema') || indLower.startsWith('bb_')) {
                        overlays.push(csvName);
                    } else if (indLower.startsWith('rsi') || indLower.startsWith('macd') || indLower.startsWith('stoch')) {
                        subplots.push(csvName);
                    }
                });
                console.log('Converted indicators:', { 
                    from: options.indicators, 
                    overlays, 
                    subplots 
                });
            }
            
            console.log('Using indicators:', { overlays, subplots });
            
            if (overlays.length > 0) {
                params.append('overlays', overlays.join(','));
            }
            if (subplots.length > 0) {
                params.append('subplots', subplots.join(','));
            }
            
            // Fetch data
            const apiUrl = `${this.config.apiBaseUrl || 'http://127.0.0.1:8000'}/chart-data?${params}`;
            console.log('Fetching from:', apiUrl);
            const response = await fetch(apiUrl);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('API Error:', response.status, errorText);
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('API Response:', result);
            console.log('API returned overlays:', result.metadata?.overlays);
            console.log('API returned subplots:', result.metadata?.subplots);
            
            // Keep the requested overlays/subplots (don't overwrite with API response)
            // The API response confirms what's available, but we already requested them
            // this.config.overlays = result.metadata?.overlays || [];
            // this.config.subplots = result.metadata?.subplots || [];
            
            // Store data
            this.chartData = result.data;
            
            // Store all available indicators from metadata
            this.availableOverlays = result.metadata?.overlays || [];
            this.availableSubplots = result.metadata?.subplots || [];
            
            // Track which indicators are currently visible
            this.visibleOverlays = new Set(this.config.overlays);
            this.visibleSubplots = new Set(this.config.subplots);
            
            // Initialize charts with the new data
            await this.initialize();
            
            console.log('Charts loaded successfully');
        } catch (error) {
            console.error('Failed to load chart:', error);
            this.container.innerHTML = `<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #e74c3c;">
                <p style="font-size: 1.2rem; margin-bottom: 0.5rem;">Failed to load chart</p>
                <p style="font-size: 0.9rem; color: #999;">${error.message}</p>
            </div>`;
            throw error;
        }
    }
    
    /**
     * Toggle an overlay indicator on/off
     * @param {string} indicator - Indicator name (e.g., 'sma_20')
     */
    toggleOverlay(indicator) {
        if (this.visibleOverlays.has(indicator)) {
            this.visibleOverlays.delete(indicator);
        } else {
            this.visibleOverlays.add(indicator);
        }
        
        // Update config
        this.config.overlays = Array.from(this.visibleOverlays);
        
        // Re-render the main chart
        this.initialize();
    }
    
    /**
     * Toggle a subplot indicator on/off
     * @param {string} indicator - Indicator name (e.g., 'rsi_14')
     */
    toggleSubplot(indicator) {
        if (this.visibleSubplots.has(indicator)) {
            this.visibleSubplots.delete(indicator);
        } else {
            this.visibleSubplots.add(indicator);
        }
        
        // Update config
        this.config.subplots = Array.from(this.visibleSubplots);
        
        // Re-render all charts
        this.initialize();
    }
    
    /**
     * Get all available indicators
     * @returns {Object} Object with overlays and subplots arrays
     */
    getAvailableIndicators() {
        return {
            overlays: this.availableOverlays || [],
            subplots: this.availableSubplots || []
        };
    }
    
    /**
     * Get currently visible indicators
     * @returns {Object} Object with visible overlays and subplots arrays
     */
    getVisibleIndicators() {
        return {
            overlays: Array.from(this.visibleOverlays || []),
            subplots: Array.from(this.visibleSubplots || [])
        };
    }
}

