/**
 * PyCharting - Viewport Management for Dynamic Data Loading
 * 
 * Handles efficient data loading based on user zoom/pan interactions.
 */

class ViewportManager {
    /**
     * Create a new ViewportManager instance.
     * @param {PyChart} chart - PyChart instance to manage
     * @param {Object} options - Configuration options
     */
    constructor(chart, options = {}) {
        this.chart = chart;
        this.sessionId = options.sessionId || 'default';
        this.apiBaseUrl = options.apiBaseUrl || '/api';
        
        // Buffer configuration (as percentage of viewport)
        this.bufferMargin = options.bufferMargin || 0.5; // 50% buffer on each side
        
        // Debounce configuration
        this.debounceDelay = options.debounceDelay || 300; // ms
        this.debounceTimer = null;
        
        // Cache management
        this.dataCache = {
            startIndex: null,
            endIndex: null,
            data: null
        };
        
        // Loading state
        this.isLoading = false;
        this.loadingCallbacks = options.onLoading || [];

        // Optional callbacks to update any external subplot charts
        this.subplotCallbacks = options.onSubplotsUpdate || [];
        
        // Total data length (from server)
        this.totalLength = null;
        
        // Track the uPlot instance we've attached listeners to
        this.lastAttachedChart = null;
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    /**
     * Set up uPlot event listeners for zoom and pan
     */
    setupEventListeners() {
        if (!this.chart.chart) {
            // Chart not yet initialized, will be setup after first data load
            return;
        }
        
        // Avoid duplicate listeners on the same chart instance
        if (this.chart.chart === this.lastAttachedChart) {
            return;
        }
        
        const uplot = this.chart.chart;
        this.lastAttachedChart = uplot;
        
        // Listen for scale changes (zoom/pan)
        uplot.hooks.setScale = uplot.hooks.setScale || [];
        uplot.hooks.setScale.push((u, key) => {
            if (key === 'x') {
                // Debounce the viewport update
                this.debouncedViewportUpdate();

                // Keep any registered subplot charts in sync on the X axis
                if (window.viewportSubplotCharts && u.scales && u.scales.x) {
                    const { min, max } = u.scales.x;
                    Object.values(window.viewportSubplotCharts).forEach((subplot) => {
                        try {
                            subplot.setScale('x', { min, max });
                        } catch (e) {
                            // Ignore sync errors per subplot
                        }
                    });
                }
            }
        });
    }
    
    /**
     * Debounced viewport update
     */
    debouncedViewportUpdate() {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.updateViewport();
        }, this.debounceDelay);
    }
    
    /**
     * Calculate visible index range from current viewport
     * @returns {Object} {startIndex, endIndex} with buffer margins
     */
    calculateVisibleRange() {
        const uplot = this.chart.chart;
        if (!uplot) {
            return null;
        }
        
        const scale = uplot.scales.x || {};
        const data = uplot.data && uplot.data[0] ? uplot.data[0] : null;
        
        if (!data || data.length === 0) {
            return null;
        }
        
        // Current viewport in "index space" (we use plain indices on the x-axis)
        const currentMin = scale.min != null ? scale.min : data[0];
        const currentMax = scale.max != null ? scale.max : data[data.length - 1];
        
        const total = this.totalLength != null ? this.totalLength : data.length;
        
        // Visible absolute indices (clamped to total length)
        let visibleStart = Math.max(0, Math.floor(currentMin));
        let visibleEnd = Math.min(total - 1, Math.ceil(currentMax));
        
        if (visibleEnd < visibleStart) {
            [visibleStart, visibleEnd] = [visibleEnd, visibleStart];
        }
        
        // For now, request exactly the visible range (no automatic over-buffering)
        // to avoid runaway prefetching when the chart first initializes.
        const startIndex = visibleStart;
        const endIndex = visibleEnd + 1; // +1 for exclusive end
        
        return {
            startIndex,
            endIndex,
            visibleStart,
            visibleEnd
        };
    }
    
    /**
     * Check if data needs to be fetched
     * @param {Object} range - Visible range with buffers
     * @returns {Boolean} True if fetch is needed
     */
    needsFetch(range) {
        if (!range || this.isLoading) {
            return false;
        }
        
        // No cached data
        if (this.dataCache.data === null) {
            return true;
        }
        
        // Check if visible range is outside cached range
        const { startIndex, endIndex } = range;
        const { startIndex: cacheStart, endIndex: cacheEnd } = this.dataCache;
        
        // Need fetch if requested range extends beyond cache
        return startIndex < cacheStart || endIndex > cacheEnd;
    }
    
    /**
     * Fetch data from API
     * @param {Number} startIndex - Start index
     * @param {Number} endIndex - End index
     * @returns {Promise<Object>} API response data
     */
    async fetchData(startIndex, endIndex) {
        const url = `${this.apiBaseUrl}/data?` + 
                    `start_index=${startIndex}&` +
                    `end_index=${endIndex}&` +
                    `session_id=${this.sessionId}`;
        
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching data:', error);
            throw error;
        }
    }
    
    /**
     * Update viewport and fetch data if needed
     */
    async updateViewport() {
        const range = this.calculateVisibleRange();
        
        if (!range || !this.needsFetch(range)) {
            return;
        }
        
        // Set loading state
        this.isLoading = true;
        this.notifyLoading(true);
        
        try {
            // Fetch data with buffer
            const data = await this.fetchData(range.startIndex, range.endIndex);
            
            // Update cache
            this.dataCache = {
                startIndex: range.startIndex,
                endIndex: range.endIndex,
                data: data
            };
            
            // Store total length
            if (data.total_length) {
                this.totalLength = data.total_length;
            }
            
            // Update chart data
            this.updateChartData(data);
            
        } catch (error) {
            console.error('Viewport update failed:', error);
            this.notifyError(error);
        } finally {
            this.isLoading = false;
            this.notifyLoading(false);
        }
    }
    
    /**
     * Update chart with new data
     * @param {Object} data - Data from API
     */
    updateChartData(data) {
        // Generate array of integer indices for X-axis
        const startIndex = data.start_index || 0;
        const xIndices = data.index.map((_, i) => startIndex + i);
        const len = xIndices.length;
        
        // Helper to ensure data array exists
        const ensureArray = (arr) => arr || Array(len).fill(null);

        // Keep timestamps for labeling
        const timestamps = data.index;

        // Convert data format to uPlot format
        // Use xIndices for the first array (X-axis)
        // Ensure all series are arrays, even if null in API response
        const chartData = [
            xIndices,
            ensureArray(data.open),
            ensureArray(data.high),
            ensureArray(data.low),
            ensureArray(data.close)
        ];
        
        // Add overlays if present
        if (data.overlays) {
            Object.values(data.overlays).forEach(overlay => {
                chartData.push(overlay);
            });
        }
        
        // Update chart with indices as X, and pass timestamps for formatting
        this.chart.setData(chartData, timestamps);
        
        // Ensure listeners are set up (needed if chart was just created/recreated)
        this.setupEventListeners();

        // Notify any subplot handlers with full data payload
        // We need to pass the xIndices here too if subplots use uPlot
        data.xIndices = xIndices;
        
        this.subplotCallbacks.forEach((cb) => {
            if (typeof cb === 'function') {
                cb(data, this);
            }
        });
    }
    
    /**
     * Initialize session with data
     * @param {String} sessionId - Optional session ID
     * @returns {Promise<Object>} Initialization response
     */
    async initializeSession(sessionId = null) {
        if (sessionId) {
            this.sessionId = sessionId;
        }
        
        try {
            const response = await fetch(
                `${this.apiBaseUrl}/data/init?session_id=${this.sessionId}`,
                { method: 'POST' }
            );
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            this.totalLength = result.data_points;
            
            // Load initial data
            await this.loadInitialData();
            
            return result;
        } catch (error) {
            console.error('Session initialization failed:', error);
            throw error;
        }
    }
    
    /**
     * Load initial data view
     * @param {Number} points - Number of initial points to load
     */
    async loadInitialData(points = 1000) {
        // By default, load the *last* `points` data items so users see the
        // most recent data first. We'll backfill older data on pan/zoom.
        const total = this.totalLength || points;
        const endIndex = total;
        const startIndex = Math.max(0, total - points);
        
        try {
            const data = await this.fetchData(startIndex, endIndex);
            
            this.dataCache = {
                startIndex,
                endIndex: endIndex,
                data: data
            };
            
            // Store total length from response if available
            if (data.total_length) {
                this.totalLength = data.total_length;
            }
            
            this.updateChartData(data);
        } catch (error) {
            console.error('Initial data load failed:', error);
            throw error;
        }
    }
    
    /**
     * Notify loading state change
     * @param {Boolean} loading - Loading state
     */
    notifyLoading(loading) {
        this.loadingCallbacks.forEach(callback => {
            if (typeof callback === 'function') {
                callback(loading);
            }
        });
    }
    
    /**
     * Notify error
     * @param {Error} error - Error object
     */
    notifyError(error) {
        console.error('ViewportManager error:', error);
    }
    
    /**
     * Get current cache info
     * @returns {Object} Cache information
     */
    getCacheInfo() {
        return {
            startIndex: this.dataCache.startIndex,
            endIndex: this.dataCache.endIndex,
            cached: this.dataCache.data !== null,
            totalLength: this.totalLength
        };
    }
    
    /**
     * Clear cache
     */
    clearCache() {
        this.dataCache = {
            startIndex: null,
            endIndex: null,
            data: null
        };
    }
    
    /**
     * Destroy viewport manager
     */
    destroy() {
        clearTimeout(this.debounceTimer);
        this.clearCache();
    }
}

// Export for use in modules or global scope
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ViewportManager;
} else {
    window.ViewportManager = ViewportManager;
}
