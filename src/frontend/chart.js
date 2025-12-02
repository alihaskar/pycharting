/**
 * Chart Manager Module
 * Manages uPlot chart initialization and rendering
 */

class ChartManager {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container not found: ${containerId}`);
        }
        
        this.chart = null;
        this.dataClient = new DataClient();
    }

    /**
     * Initialize and render chart with data
     * @param {Array} data - Chart data in uPlot format
     * @param {Object} metadata - Metadata about the chart data
     */
    renderChart(data, metadata) {
        // Define chart options
        const opts = {
            title: "Financial Chart",
            width: this.container.clientWidth,
            height: 400,
            series: [
                {},  // Timestamps
                { label: "Open", stroke: "blue" },
                { label: "High", stroke: "green" },
                { label: "Low", stroke: "red" },
                { label: "Close", stroke: "black", width: 2 },
                { label: "Volume", stroke: "gray" }
            ]
        };
        
        // Add indicator series if present
        if (metadata.indicators && metadata.indicators.length > 0) {
            const colors = ['orange', 'purple', 'brown', 'pink'];
            metadata.indicators.forEach((indicator, index) => {
                opts.series.push({
                    label: indicator,
                    stroke: colors[index % colors.length]
                });
            });
        }
        
        // Destroy existing chart if any
        if (this.chart) {
            this.chart.destroy();
        }
        
        // Create new chart
        this.chart = new uPlot(opts, data, this.container);
    }

    /**
     * Load and render chart from API
     * @param {string} filename - CSV filename to load
     * @param {Object} options - Optional parameters
     */
    async loadAndRender(filename, options = {}) {
        try {
            const response = await this.dataClient.fetchChartData(filename, options);
            this.renderChart(response.data, response.metadata);
        } catch (error) {
            console.error('Error loading chart:', error);
            this.container.innerHTML = `
                <div style="color: red; padding: 20px;">
                    <strong>Error loading chart:</strong>
                    <p>${error.message}</p>
                </div>
            `;
        }
    }

    /**
     * Destroy the chart instance
     */
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}

// Export for global use
window.ChartManager = ChartManager;

