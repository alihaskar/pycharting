/**
 * PyCharting - uPlot-based OHLC Chart Rendering
 * 
 * High-performance candlestick chart with overlays using uPlot.
 */

class PyChart {
    /**
     * Create a new PyChart instance.
     * @param {HTMLElement} container - Container element for the chart
     * @param {Object} options - Chart configuration options
     */
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            width: options.width || container.clientWidth,
            height: options.height || 400,
            title: options.title || 'OHLC Chart',
            ...options
        };
        
        this.chart = null;
        this.data = null;
    }
    
    /**
     * Custom uPlot plugin for candlestick rendering
     */
    candlestickPlugin() {
        const self = this;
        
        return {
            hooks: {
                draw: [
                    (u) => {
                        const ctx = u.ctx;
                        const [iMin, iMax] = u.series[0].idxs;
                        
                        // Get data indices
                        const timeIdx = 0;
                        const openIdx = 1;
                        const highIdx = 2;
                        const lowIdx = 3;
                        const closeIdx = 4;
                        
                        // Get pixel positions
                        const xPos = (i) => Math.round(u.valToPos(u.data[timeIdx][i], 'x', true));
                        const yPos = (val) => Math.round(u.valToPos(val, 'y', true));
                        
                        // Calculate candle width
                        const numCandles = iMax - iMin;
                        const availableWidth = u.bbox.width;
                        const candleWidth = Math.max(1, Math.floor((availableWidth / numCandles) * 0.7));
                        
                        // Draw candlesticks
                        for (let i = iMin; i <= iMax; i++) {
                            const open = u.data[openIdx][i];
                            const high = u.data[highIdx][i];
                            const low = u.data[lowIdx][i];
                            const close = u.data[closeIdx][i];
                            
                            if (open == null || high == null || low == null || close == null) {
                                continue;
                            }
                            
                            const x = xPos(i);
                            const yOpen = yPos(open);
                            const yHigh = yPos(high);
                            const yLow = yPos(low);
                            const yClose = yPos(close);
                            
                            // Determine color (green for up, red for down)
                            const isUp = close >= open;
                            ctx.fillStyle = isUp ? '#26a69a' : '#ef5350';
                            ctx.strokeStyle = isUp ? '#26a69a' : '#ef5350';
                            
                            // Draw high-low line (wick)
                            ctx.beginPath();
                            ctx.moveTo(x, yHigh);
                            ctx.lineTo(x, yLow);
                            ctx.lineWidth = 1;
                            ctx.stroke();
                            
                            // Draw open-close body
                            const bodyHeight = Math.abs(yClose - yOpen);
                            const bodyY = Math.min(yOpen, yClose);
                            
                            if (bodyHeight > 0) {
                                ctx.fillRect(
                                    x - candleWidth / 2,
                                    bodyY,
                                    candleWidth,
                                    bodyHeight
                                );
                            } else {
                                // Doji - draw horizontal line
                                ctx.beginPath();
                                ctx.moveTo(x - candleWidth / 2, yOpen);
                                ctx.lineTo(x + candleWidth / 2, yOpen);
                                ctx.lineWidth = 1;
                                ctx.stroke();
                            }
                        }
                    }
                ]
            }
        };
    }
    
    /**
     * Set chart data and render
     * @param {Array} data - Chart data [xValues, open, high, low, close, ...overlays]
     * @param {Array} timestamps - Optional array of timestamps corresponding to xValues
     */
    setData(data, timestamps = null) {
        const prevLen = this.data ? this.data.length : null;
        this.data = data;
        this.timestamps = timestamps;
        
        // If the number of series hasn't changed, we can just update data
        if (this.chart && prevLen === data.length) {
            this.chart.setData(data);
            return;
        }
        
        // If the series count changed (e.g. overlays added), rebuild the chart
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        
        const config = this.createConfig(data);
        this.chart = new uPlot(config, data, this.container);
        this._setupInteractions();
    }

    /**
     * Helper to format x-axis values (indices) to dates
     */
    formatDate(index) {
        if (!this.timestamps) return index;
        
        // Find the timestamp for this index
        // Since we don't store the full map, we assume data[0] contains indices
        // and this.timestamps aligns with data[0]
        if (this.data && this.data[0]) {
            const dataIndex = this.data[0].indexOf(index);
            if (dataIndex !== -1 && this.timestamps[dataIndex]) {
                const date = new Date(this.timestamps[dataIndex]);
                return date.toLocaleString();
            }
        }
        return index;
    }
    
    /**
     * Create uPlot configuration
     * @param {Array} data - Chart data
     */
    createConfig(data) {
        const self = this;
        // Always use numeric indices for X-axis to support ViewportManager slicing
        const isTimestamp = false; 
        
        // Build series configuration
        const series = [
            {
                label: 'Time',
                // Format value using timestamp map if available
                value: (u, v) => self.formatDate(v)
            },
            {
                label: 'Open',
                show: false, // Hide from legend, shown in candlestick
            },
            {
                label: 'High',
                show: false,
            },
            {
                label: 'Low',
                show: false,
            },
            {
                label: 'Close',
                stroke: 'transparent',
                fill: 'transparent',
            }
        ];
        
        // Add overlay series (starting from index 5)
        if (data.length > 5) {
            for (let i = 5; i < data.length; i++) {
                const colors = ['#2196F3', '#FF9800', '#9C27B0', '#4CAF50'];
                series.push({
                    label: `Overlay ${i - 4}`,
                    stroke: colors[(i - 5) % colors.length],
                    width: 2,
                });
            }
        }
        
        return {
            ...this.options,
            series,
            scales: {
                x: {
                    time: false,
                },
                y: {
                    auto: true,
                }
            },
            axes: [
                {
                    stroke: '#888',
                    grid: { stroke: '#eee', width: 1 },
                    // Format ticks using timestamp map
                    values: (u, vals) => vals.map(v => {
                        if (self.timestamps && self.data && self.data[0]) {
                            // Binary search or approximate lookup would be faster for large datasets
                            // but for the viewport chunk (1-2k points), direct lookup is okay
                            // Actually, uPlot ticks `vals` might not exactly match data indices
                            // So we find the closest index
                            const idx = Math.round(v);
                            return self.formatDate(idx);
                        }
                        return v.toFixed(0);
                    }),
                },
                {
                    stroke: '#888',
                    grid: { stroke: '#eee', width: 1 },
                    values: (u, vals) => vals.map(v => v.toFixed(2)),
                }
            ],
            plugins: [
                this.candlestickPlugin()
            ],
            cursor: {
                drag: { x: false, y: false },
                sync: { key: 'pycharting' }
            }
        };
    }
    
    /**
     * Set chart data and render
     * @param {Array} data - Chart data [timestamps, open, high, low, close, ...overlays]
     */
    setData(data) {
        const prevLen = this.data ? this.data.length : null;
        this.data = data;
        
        // If the number of series hasn't changed, we can just update data
        if (this.chart && prevLen === data.length) {
            this.chart.setData(data);
            return;
        }
        
        // If the series count changed (e.g. overlays added), rebuild the chart
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        
        const config = this.createConfig(data);
        this.chart = new uPlot(config, data, this.container);
        this._setupInteractions();
    }
    
    /**
     * Attach basic mouse wheel zoom and drag-to-pan interactions.
     * uPlot doesn't ship these by default; we implement minimal X-only behavior.
     * @private
     */
    _setupInteractions() {
        const u = this.chart;
        if (!u) return;
        
        const over = u.over;
        if (!over) return;
        
        // --- Wheel zoom (horizontal) ---
        const zoomFactor = 0.25;
        over.addEventListener('wheel', (e) => {
            e.preventDefault();
            
            const rect = over.getBoundingClientRect();
            const x = e.clientX - rect.left;
            
            const xVal = u.posToVal(x, 'x');
            const scale = u.scales.x;
            const min = scale.min;
            const max = scale.max;
            
            if (min == null || max == null) return;
            
            const range = max - min;
            const factor = e.deltaY < 0 ? (1 - zoomFactor) : (1 + zoomFactor);
            
            const newMin = xVal - (xVal - min) * factor;
            const newMax = xVal + (max - xVal) * factor;
            
            u.setScale('x', { min: newMin, max: newMax });
        }, { passive: false });
        
        // --- Drag pan (left mouse button) ---
        let dragging = false;
        let dragStartX = 0;
        let dragMin = 0;
        let dragMax = 0;
        
        over.addEventListener('mousedown', (e) => {
            if (e.button !== 0) return;
            dragging = true;
            dragStartX = e.clientX;
            const scale = u.scales.x;
            dragMin = scale.min;
            dragMax = scale.max;
        });
        
        window.addEventListener('mousemove', (e) => {
            if (!dragging) return;
            const dx = e.clientX - dragStartX;
            const pxPerUnit = u.bbox.width / (dragMax - dragMin);
            const shift = -dx / pxPerUnit;
            
            u.setScale('x', {
                min: dragMin + shift,
                max: dragMax + shift,
            });
        });
        
        const endDrag = () => {
            dragging = false;
        };
        
        window.addEventListener('mouseup', endDrag);
        window.addEventListener('mouseleave', endDrag);
    }
    
    /**
     * Update chart size
     * @param {number} width - New width
     * @param {number} height - New height
     */
    setSize(width, height) {
        if (this.chart) {
            this.chart.setSize({ width, height });
        }
    }
    
    /**
     * Destroy the chart and clean up resources
     */
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}

// Export for use in modules or global scope
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PyChart;
} else {
    window.PyChart = PyChart;
}
