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
        const prevHadTimestamps = this.timestamps != null;
        const nowHasTimestamps = timestamps != null;
        
        this.data = data;
        this.timestamps = timestamps;
        
        // Debug: Check what we received
        if (timestamps && timestamps.length > 0) {
            console.log('Chart received timestamps. First:', timestamps[0], 'Type:', typeof timestamps[0]);
            console.log('Chart received X-indices. First:', data[0][0]);
        } else {
            console.log('Chart received NO timestamps');
        }
        
        // Rebuild chart if:
        // 1. Series count changed (e.g., overlays added)
        // 2. Timestamp presence changed (affects axis formatting)
        const needsRebuild = !this.chart || 
                             prevLen !== data.length || 
                             prevHadTimestamps !== nowHasTimestamps;
        
        if (this.chart && !needsRebuild) {
            // Fast path: just update data
            this.chart.setData(data);
            return;
        }
        
        // Rebuild chart
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
        if (!this.timestamps) {
            console.log('formatDate: No timestamps array');
            return index;
        }
        
        if (this.data && this.data[0] && this.data[0].length > 0) {
            const startIndex = this.data[0][0];
            const dataIndex = Math.round(index - startIndex);
            
            if (dataIndex >= 0 && dataIndex < this.timestamps.length) {
                const val = this.timestamps[dataIndex];
                
                console.log(`formatDate: index=${index}, dataIndex=${dataIndex}, val=${val}, type=${typeof val}`);
                
                // Heuristic: Only format as date if value looks like a timestamp (milliseconds)
                if (typeof val === 'number' && val > 315360000000) {
                    const date = new Date(val);
                    return date.toLocaleString(undefined, {
                        month: 'numeric', day: 'numeric', 
                        hour: '2-digit', minute: '2-digit'
                    });
                }
                console.log('Value too small for timestamp:', val);
                return val;
            }
            console.log('dataIndex out of range:', dataIndex, 'timestamps.length:', this.timestamps.length);
        }
        return index;
    }
    
    /**
     * Create uPlot configuration
     * @param {Array} data - Chart data
     */
    createConfig(data) {
        const self = this;
        // Check if Open series exists and contains any non-null values
        const openSeries = data[1];
        const hasOHLC = openSeries && Array.isArray(openSeries) && openSeries.some(v => v != null);
        
        // Build series configuration
        const series = [
            {
                label: 'Time',
                value: (u, v) => self.formatDate(v)
            },
            {
                label: 'Open',
                show: false,
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
                stroke: hasOHLC ? 'transparent' : '#2196F3',
                width: hasOHLC ? 0 : 2,
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
                    values: (u, vals) => vals.map(v => {
                        const idx = Math.round(v);
                        return self.formatDate(idx);
                    }),
                },
                {
                    stroke: '#888',
                    grid: { stroke: '#eee', width: 1 },
                    values: (u, vals) => vals.map(v => v.toFixed(2)),
                }
            ],
            plugins: hasOHLC ? [this.candlestickPlugin()] : [],
            cursor: {
                drag: { x: false, y: false },
                sync: { key: 'pycharting' }
            }
        };
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
