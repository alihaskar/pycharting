/**
 * PyCharting - Multi-Chart Synchronization
 * 
 * Handles synchronized cursor and zoom/pan across multiple chart instances.
 */

class ChartSync {
    /**
     * Create a ChartSync instance for managing multiple synchronized charts.
     * @param {Object} options - Configuration options
     */
    constructor(options = {}) {
        this.charts = [];
        this.syncCursor = options.syncCursor !== false;
        this.syncZoom = options.syncZoom !== false;
        this.syncPan = options.syncPan !== false;
        
        // Track which chart is being interacted with
        this.activeChart = null;
        this.isSyncing = false;
    }
    
    /**
     * Add a chart to the synchronization group
     * @param {PyChart|uPlot} chart - Chart instance to synchronize
     * @param {Object} options - Chart-specific options
     */
    addChart(chart, options = {}) {
        const chartConfig = {
            chart: chart.chart || chart, // Handle both PyChart and raw uPlot
            pyChart: chart.chart ? chart : null, // Store PyChart if available
            id: options.id || `chart_${this.charts.length}`,
            syncCursor: options.syncCursor !== false && this.syncCursor,
            syncZoom: options.syncZoom !== false && this.syncZoom,
            syncPan: options.syncPan !== false && this.syncPan,
        };
        
        this.charts.push(chartConfig);
        this._setupChartHooks(chartConfig);
        
        return chartConfig.id;
    }
    
    /**
     * Remove a chart from synchronization
     * @param {String} chartId - ID of chart to remove
     */
    removeChart(chartId) {
        const index = this.charts.findIndex(c => c.id === chartId);
        if (index !== -1) {
            this.charts.splice(index, 1);
        }
    }
    
    /**
     * Setup synchronization hooks for a chart
     * @param {Object} chartConfig - Chart configuration object
     * @private
     */
    _setupChartHooks(chartConfig) {
        const uplot = chartConfig.chart;
        
        if (!uplot) return;
        
        // Cursor synchronization
        if (chartConfig.syncCursor) {
            uplot.hooks.setCursor = uplot.hooks.setCursor || [];
            uplot.hooks.setCursor.push((u) => {
                if (!this.isSyncing && this.activeChart !== chartConfig) {
                    this.activeChart = chartConfig;
                    this._syncCursor(chartConfig);
                }
            });
        }
        
        // Zoom/Pan synchronization
        if (chartConfig.syncZoom || chartConfig.syncPan) {
            uplot.hooks.setScale = uplot.hooks.setScale || [];
            uplot.hooks.setScale.push((u, key) => {
                if (key === 'x' && !this.isSyncing) {
                    this.activeChart = chartConfig;
                    this._syncScale(chartConfig);
                }
            });
        }
    }
    
    /**
     * Synchronize cursor position across all charts
     * @param {Object} sourceChart - Chart that triggered the cursor update
     * @private
     */
    _syncCursor(sourceChart) {
        if (!sourceChart.syncCursor) return;
        
        const sourcePlot = sourceChart.chart;
        const cursor = sourcePlot.cursor;
        
        if (!cursor || cursor.left == null) return;
        
        this.isSyncing = true;
        
        try {
            this.charts.forEach(targetConfig => {
                if (targetConfig.id === sourceChart.id || !targetConfig.syncCursor) {
                    return;
                }
                
                const targetPlot = targetConfig.chart;
                
                // Get the value from source chart's x-axis
                const sourceValue = sourcePlot.posToVal(cursor.left, 'x');
                
                // Convert to position in target chart
                const targetLeft = targetPlot.valToPos(sourceValue, 'x');
                
                // Set cursor on target chart
                if (targetLeft != null && !isNaN(targetLeft)) {
                    targetPlot.setCursor({
                        left: targetLeft,
                        top: cursor.top
                    });
                }
            });
        } finally {
            this.isSyncing = false;
        }
    }
    
    /**
     * Synchronize zoom/pan across all charts
     * @param {Object} sourceChart - Chart that triggered the scale update
     * @private
     */
    _syncScale(sourceChart) {
        const sourcePlot = sourceChart.chart;
        const sourceScale = sourcePlot.scales.x;
        
        if (!sourceScale) return;
        
        this.isSyncing = true;
        
        try {
            this.charts.forEach(targetConfig => {
                if (targetConfig.id === sourceChart.id) {
                    return;
                }
                
                const targetPlot = targetConfig.chart;
                const shouldSync = (
                    (sourceChart.syncZoom && targetConfig.syncZoom) ||
                    (sourceChart.syncPan && targetConfig.syncPan)
                );
                
                if (!shouldSync) return;
                
                // Apply the same scale range to target chart
                targetPlot.setScale('x', {
                    min: sourceScale.min,
                    max: sourceScale.max
                });
            });
        } finally {
            this.isSyncing = false;
        }
    }
    
    /**
     * Get all synchronized chart instances
     * @returns {Array} Array of chart configurations
     */
    getCharts() {
        return this.charts;
    }
    
    /**
     * Clear all charts from synchronization
     */
    clearCharts() {
        this.charts = [];
        this.activeChart = null;
    }
    
    /**
     * Enable/disable cursor synchronization
     * @param {Boolean} enabled - Whether to enable cursor sync
     */
    setCursorSync(enabled) {
        this.syncCursor = enabled;
        this.charts.forEach(c => c.syncCursor = enabled);
    }
    
    /**
     * Enable/disable zoom synchronization
     * @param {Boolean} enabled - Whether to enable zoom sync
     */
    setZoomSync(enabled) {
        this.syncZoom = enabled;
        this.charts.forEach(c => c.syncZoom = enabled);
    }
    
    /**
     * Enable/disable pan synchronization
     * @param {Boolean} enabled - Whether to enable pan sync
     */
    setPanSync(enabled) {
        this.syncPan = enabled;
        this.charts.forEach(c => c.syncPan = enabled);
    }
}

/**
 * Multi-Chart Manager for creating subplot layouts
 */
class MultiChartManager {
    /**
     * Create a MultiChartManager instance
     * @param {HTMLElement} container - Container element for charts
     * @param {Object} options - Configuration options
     */
    constructor(container, options = {}) {
        this.container = container;
        this.chartSync = new ChartSync(options);
        this.mainChart = null;
        this.subCharts = [];
        
        // Layout configuration
        this.mainHeight = options.mainHeight || 400;
        this.subHeight = options.subHeight || 150;
        this.gap = options.gap || 10;
        
        this._setupContainer();
    }
    
    /**
     * Setup container styling
     * @private
     */
    _setupContainer() {
        this.container.style.display = 'flex';
        this.container.style.flexDirection = 'column';
        this.container.style.gap = `${this.gap}px`;
    }
    
    /**
     * Create the main chart
     * @param {Object} config - Chart configuration
     * @returns {PyChart} Main chart instance
     */
    createMainChart(config = {}) {
        const chartDiv = document.createElement('div');
        chartDiv.style.height = `${this.mainHeight}px`;
        this.container.appendChild(chartDiv);
        
        this.mainChart = new PyChart(chartDiv, {
            ...config,
            height: this.mainHeight,
            title: config.title || 'OHLC Chart'
        });
        
        this.chartSync.addChart(this.mainChart, { id: 'main' });
        
        return this.mainChart;
    }
    
    /**
     * Add a subplot
     * @param {Object} config - Subplot configuration
     * @returns {PyChart} Subplot instance
     */
    addSubplot(config = {}) {
        const chartDiv = document.createElement('div');
        chartDiv.style.height = `${this.subHeight}px`;
        this.container.appendChild(chartDiv);
        
        const subChart = new PyChart(chartDiv, {
            ...config,
            height: this.subHeight,
            title: config.title || `Subplot ${this.subCharts.length + 1}`
        });
        
        const id = `subplot_${this.subCharts.length}`;
        this.chartSync.addChart(subChart, { id });
        this.subCharts.push({ id, chart: subChart });
        
        return subChart;
    }
    
    /**
     * Load data into all charts
     * @param {Object} data - Data object with main and subplot data
     */
    loadData(data) {
        // Load main chart data
        if (this.mainChart && data.main) {
            this.mainChart.setData(data.main);
        }
        
        // Load subplot data
        if (data.subplots && Array.isArray(data.subplots)) {
            data.subplots.forEach((subData, index) => {
                if (this.subCharts[index]) {
                    this.subCharts[index].chart.setData(subData);
                }
            });
        }
    }
    
    /**
     * Get the chart sync instance
     * @returns {ChartSync} Chart sync instance
     */
    getSync() {
        return this.chartSync;
    }
    
    /**
     * Remove a subplot
     * @param {Number} index - Index of subplot to remove
     */
    removeSubplot(index) {
        if (index >= 0 && index < this.subCharts.length) {
            const subplot = this.subCharts[index];
            this.chartSync.removeChart(subplot.id);
            subplot.chart.destroy();
            this.subCharts.splice(index, 1);
        }
    }
    
    /**
     * Clear all charts
     */
    clear() {
        if (this.mainChart) {
            this.mainChart.destroy();
            this.mainChart = null;
        }
        
        this.subCharts.forEach(subplot => {
            subplot.chart.destroy();
        });
        
        this.subCharts = [];
        this.chartSync.clearCharts();
        this.container.innerHTML = '';
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ChartSync, MultiChartManager };
} else {
    window.ChartSync = ChartSync;
    window.MultiChartManager = MultiChartManager;
}
