/**
 * Chart Manager Module
 * Manages uPlot chart initialization and rendering with OHLC support
 */

/**
 * Chart State Manager
 * Tracks chart configuration and state
 */
class ChartState {
    constructor() {
        this.config = {};
        this.zoomLevel = 1;
        this.panPosition = 0;
        this.visibleRange = null;
        this.indicators = [];
    }

    update(key, value) {
        this.config[key] = value;
    }

    get(key) {
        return this.config[key];
    }

    reset() {
        this.config = {};
        this.zoomLevel = 1;
        this.panPosition = 0;
        this.visibleRange = null;
    }
}

class ChartManager {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container not found: ${containerId}`);
        }
        
        this.chart = null;
        this.dataClient = new DataClient();
        this.state = new ChartState();
        this.currentData = null;
        this.currentMetadata = null;
    }

    /**
     * Create uPlot options with multi-axis support
     * @param {Object} metadata - Chart metadata
     * @returns {Object} uPlot options
     */
    createChartOptions(metadata) {
        const opts = {
            title: "Financial Chart",
            width: this.container.clientWidth,
            height: 400,
            cursor: {
                drag: {
                    x: true,
                    y: false
                }
            },
            scales: {
                x: {
                    time: true
                },
                y: {
                    auto: true
                }
            },
            axes: [
                {
                    // X-axis (time)
                    space: 80,
                    incrs: [
                        // minute divisors (# of secs)
                        1,
                        5,
                        10,
                        15,
                        30,
                        // hour divisors
                        60,
                        60 * 5,
                        60 * 15,
                        60 * 30,
                        // day divisors
                        3600,
                    ]
                },
                {
                    // Y-axis (price)
                    scale: 'y',
                    label: 'Price',
                    labelGap: 5,
                    size: 60,
                    grid: {
                        show: true,
                        stroke: '#eee',
                        width: 1
                    }
                }
            ],
            series: [
                {},  // Timestamps
                { label: "Open", stroke: "blue", scale: 'y' },
                { label: "High", stroke: "green", scale: 'y' },
                { label: "Low", stroke: "red", scale: 'y' },
                { label: "Close", stroke: "black", width: 2, scale: 'y' },
                { label: "Volume", stroke: "gray", scale: 'y' }
            ],
            plugins: []
        };
        
        // Add indicator series with appropriate axes
        if (metadata && metadata.indicators && metadata.indicators.length > 0) {
            const colors = ['orange', 'purple', 'brown', 'pink', 'cyan'];
            metadata.indicators.forEach((indicator, index) => {
                // Determine if indicator needs its own axis (oscillators like RSI)
                const needsOwnAxis = indicator.toUpperCase().includes('RSI');
                
                if (needsOwnAxis) {
                    // Create new scale and axis for oscillator
                    const scaleKey = `ind${index}`;
                    opts.scales[scaleKey] = { auto: true };
                    opts.axes.push({
                        scale: scaleKey,
                        label: indicator,
                        side: 3, // Right side
                        size: 50,
                        grid: { show: false }
                    });
                    
                    opts.series.push({
                        label: indicator,
                        stroke: colors[index % colors.length],
                        scale: scaleKey,
                        width: 2
                    });
                } else {
                    // Overlay on price axis (moving averages)
                    opts.series.push({
                        label: indicator,
                        stroke: colors[index % colors.length],
                        scale: 'y',
                        width: 2
                    });
                }
            });
        }
        
        return opts;
    }

    /**
     * Initialize and render chart with data
     * @param {Array} data - Chart data in uPlot format
     * @param {Object} metadata - Metadata about the chart data
     */
    renderChart(data, metadata) {
        // Store current data and metadata
        this.currentData = data;
        this.currentMetadata = metadata;
        
        // Create chart options
        const opts = this.createChartOptions(metadata);
        
        // Destroy existing chart if any
        if (this.chart) {
            this.chart.destroy();
        }
        
        // Create new chart
        this.chart = new uPlot(opts, data, this.container);
        
        // Update state
        this.state.indicators = metadata.indicators || [];
    }

    /**
     * Update chart data without full re-initialization
     * @param {Array} newData - New chart data
     */
    setData(newData) {
        if (this.chart && newData) {
            this.currentData = newData;
            this.chart.setData(newData);
        }
    }

    /**
     * Update chart with new data efficiently
     * @param {Array} newData - New data to append or replace
     * @param {boolean} append - Whether to append or replace
     */
    updateData(newData, append = false) {
        if (!this.chart) {
            return;
        }

        if (append && this.currentData) {
            // Append new data points
            const mergedData = this.currentData.map((series, i) => {
                return [...series, ...newData[i]];
            });
            this.setData(mergedData);
        } else {
            // Replace all data
            this.setData(newData);
        }
    }

    /**
     * Load and render chart from API
     * @param {string} filename - CSV filename to load
     * @param {Object} options - Optional parameters
     */
    async loadAndRender(filename, options = {}) {
        try {
            // Show loading state
            this.showLoading();
            
            const response = await this.dataClient.fetchChartData(filename, options);
            this.renderChart(response.data, response.metadata);
        } catch (error) {
            console.error('Error loading chart:', error);
            this.showError(error.message);
        }
    }

    /**
     * Load and render chart with debouncing (for zoom/pan operations)
     * @param {string} filename - CSV filename to load
     * @param {Object} options - Optional parameters
     * @param {number} delay - Debounce delay in milliseconds
     */
    async loadAndRenderDebounced(filename, options = {}, delay = 300) {
        try {
            this.showLoading();
            
            const response = await this.dataClient.fetchChartDataDebounced(
                filename, 
                options, 
                delay
            );
            this.renderChart(response.data, response.metadata);
        } catch (error) {
            if (error.name !== 'NetworkError' || !error.message.includes('cancelled')) {
                console.error('Error loading chart:', error);
                this.showError(error.message);
            }
        }
    }

    /**
     * Show loading indicator
     */
    showLoading() {
        if (!this.chart) {
            this.container.innerHTML = `
                <div style="padding: 20px; text-align: center;">
                    <p>Loading chart data...</p>
                </div>
            `;
        }
    }

    /**
     * Show error message
     * @param {string} message - Error message to display
     */
    showError(message) {
        this.container.innerHTML = `
            <div style="color: red; padding: 20px;">
                <strong>Error loading chart:</strong>
                <p>${message}</p>
            </div>
        `;
    }

    /**
     * Get current zoom level
     * @returns {number} Current zoom level
     */
    getZoom() {
        return this.state.zoomLevel;
    }

    /**
     * Set zoom level
     * @param {number} level - Zoom level
     */
    setZoom(level) {
        this.state.zoomLevel = level;
        // Zoom implementation would interact with uPlot's scale methods
    }

    /**
     * Get visible time range
     * @returns {Object|null} Visible range {min, max}
     */
    getVisibleRange() {
        if (this.chart) {
            const scales = this.chart.scales;
            return {
                min: scales.x.min,
                max: scales.x.max
            };
        }
        return null;
    }

    /**
     * Get chart state
     * @returns {Object} Current chart state
     */
    getState() {
        return {
            zoomLevel: this.state.zoomLevel,
            panPosition: this.state.panPosition,
            visibleRange: this.getVisibleRange(),
            indicators: this.state.indicators,
            hasData: this.currentData !== null
        };
    }

    /**
     * Reset chart state
     */
    resetState() {
        this.state.reset();
    }

    /**
     * Destroy the chart instance and cleanup
     */
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        this.currentData = null;
        this.currentMetadata = null;
        this.resetState();
    }

    /**
     * Resize chart to fit container
     */
    resize() {
        if (this.chart && this.container) {
            const width = this.container.clientWidth;
            const height = this.container.clientHeight || 400;
            this.chart.setSize({ width, height });
        }
    }
}

// Export for global use
window.ChartManager = ChartManager;
window.ChartState = ChartState;
