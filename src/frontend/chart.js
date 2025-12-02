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
        
        // Bind the candlestick paths function
        this.ohlcPaths = this.candlestickPaths.bind(this);
    }

    /**
     * Draw candlestick paths for uPlot
     * @param {Object} u - uPlot instance
     * @param {number} seriesIdx - Series index
     * @param {number} idx0 - Start index
     * @param {number} idx1 - End index
     * @returns {Object} SVG path object
     */
    candlestickPaths(u, seriesIdx, idx0, idx1) {
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
            const open = u.valToPos(opens[i], 'y', true);
            const high = u.valToPos(highs[i], 'y', true);
            const low = u.valToPos(lows[i], 'y', true);
            const close = u.valToPos(closes[i], 'y', true);
            
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
     * Create uPlot options with multi-axis support
     * @param {Object} metadata - Chart metadata
     * @returns {Object} uPlot options
     */
    createChartOptions(metadata) {
        const opts = {
            title: "",  // No title, we have it in header
            width: this.container.clientWidth,
            height: this.container.clientHeight || window.innerHeight - 150,
            cursor: {
                drag: {
                    x: false,  // Disable default drag selection
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
            hooks: {
                ready: [
                    u => {
                        let isDragging = false;
                        let dragStartX = null;
                        let dragStartMin = null;
                        let dragStartMax = null;
                        
                        // Mouse down - start drag
                        u.over.addEventListener('mousedown', e => {
                            isDragging = true;
                            dragStartX = e.clientX;
                            const xScale = u.scales.x;
                            dragStartMin = xScale.min;
                            dragStartMax = xScale.max;
                            u.over.style.cursor = 'grabbing';
                        });
                        
                        // Mouse move - pan chart
                        u.over.addEventListener('mousemove', e => {
                            if (!isDragging) return;
                            
                            const deltaX = e.clientX - dragStartX;
                            const { width } = u.over.getBoundingClientRect();
                            const xRange = dragStartMax - dragStartMin;
                            const xDelta = -(deltaX / width) * xRange;
                            
                            u.setScale('x', {
                                min: dragStartMin + xDelta,
                                max: dragStartMax + xDelta
                            });
                        });
                        
                        // Mouse up - end drag
                        const endDrag = () => {
                            if (isDragging) {
                                isDragging = false;
                                dragStartX = null;
                                dragStartMin = null;
                                dragStartMax = null;
                                u.over.style.cursor = 'grab';
                            }
                        };
                        
                        u.over.addEventListener('mouseup', endDrag);
                        u.over.addEventListener('mouseleave', endDrag);
                        
                        // Set initial cursor
                        u.over.style.cursor = 'grab';
                        
                        // Add mouse wheel zoom after chart is ready
                        u.over.addEventListener('wheel', e => {
                            e.preventDefault();
                            
                            const { left, width } = u.over.getBoundingClientRect();
                            const xPos = e.clientX - left;
                            const xPct = xPos / width;
                            
                            const xScale = u.scales.x;
                            const xMin = xScale.min;
                            const xMax = xScale.max;
                            const xRange = xMax - xMin;
                            
                            // Zoom factor: scroll up = zoom in, scroll down = zoom out
                            const factor = e.deltaY < 0 ? 0.9 : 1.1;
                            
                            const newRange = xRange * factor;
                            const newMin = xMin - (newRange - xRange) * xPct;
                            const newMax = xMax + (newRange - xRange) * (1 - xPct);
                            
                            u.setScale('x', { min: newMin, max: newMax });
                        });
                        
                        // Add double-click to reset zoom
                        u.over.addEventListener('dblclick', () => {
                            u.setScale('x', { min: null, max: null });
                        });
                    }
                ],
                setCursor: [
                    (u) => {
                        // Update OHLC display on cursor move
                        const idx = u.cursor.idx;
                        
                        if (idx === null || idx === undefined) {
                            this.ohlcDisplay.style.display = 'none';
                            return;
                        }
                        
                        this.ohlcDisplay.style.display = 'block';
                        
                        // Extract OHLC values (series indices: 0=time, 1=open, 2=high, 3=low, 4=close)
                        const timestamp = u.data[0][idx];
                        const open = u.data[1][idx];
                        const high = u.data[2][idx];
                        const low = u.data[3][idx];
                        const close = u.data[4][idx];
                        const volume = u.data[5] ? u.data[5][idx] : null;
                        
                        // Format date
                        const date = new Date(timestamp * 1000);
                        const dateStr = date.toLocaleString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                        });
                        
                        // Determine if bullish or bearish
                        const isUp = close >= open;
                        const color = isUp ? '#4caf50' : '#f44336';
                        
                        // Build display HTML
                        let html = `<div style="color: #666; margin-bottom: 4px;">${dateStr}</div>`;
                        html += `<div><span style="color: #666;">O</span> <span style="font-weight: bold;">${open?.toFixed(2) || '-'}</span></div>`;
                        html += `<div><span style="color: #666;">H</span> <span style="font-weight: bold;">${high?.toFixed(2) || '-'}</span></div>`;
                        html += `<div><span style="color: #666;">L</span> <span style="font-weight: bold;">${low?.toFixed(2) || '-'}</span></div>`;
                        html += `<div><span style="color: #666;">C</span> <span style="font-weight: bold; color: ${color};">${close?.toFixed(2) || '-'}</span></div>`;
                        
                        if (volume !== null && volume !== undefined) {
                            html += `<div style="margin-top: 4px;"><span style="color: #666;">Vol</span> <span style="font-weight: bold;">${volume?.toLocaleString() || '-'}</span></div>`;
                        }
                        
                        this.ohlcDisplay.innerHTML = html;
                    }
                ]
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
                {},  // Timestamps (series[0])
                // OHLC candlestick - series[1] reads data[1-4] for O,H,L,C
                {
                    label: "OHLC",
                    scale: 'y',
                    paths: this.ohlcPaths,
                    points: { show: false },
                    stroke: "#ef5350",  // Red for bearish candles
                    fill: "#26a69a",    // Green for bullish candles
                    width: 1.5
                },
                // These are placeholders for H, L, C in data array
                // They won't be rendered separately since OHLC handles all 4
                { show: false }, // High (data[2])
                { show: false }, // Low (data[3])
                { show: false }, // Close (data[4])
                // Volume
                { show: false }  // Volume (data[5]) - hidden for now
            ],
            plugins: []
        };
        
        // Add indicator series with appropriate axes
        if (metadata && metadata.indicators && metadata.indicators.length > 0) {
            const colors = ['#ff6b35', '#7b2cbf', '#06ffa5', '#ffd60a', '#00b4d8'];
            metadata.indicators.forEach((indicator, index) => {
                // Determine if indicator needs its own axis (oscillators like RSI)
                const needsOwnAxis = indicator.toUpperCase().includes('RSI');
                
                if (needsOwnAxis) {
                    // Create new scale and axis for oscillator
                    const scaleKey = `ind${index}`;
                    opts.scales[scaleKey] = { 
                        auto: true,
                        range: [0, 100]  // RSI is 0-100
                    };
                    opts.axes.push({
                        scale: scaleKey,
                        label: indicator,
                        side: 1, // Right side
                        size: 50,
                        grid: { show: false }
                    });
                    
                    opts.series.push({
                        label: indicator,
                        stroke: colors[index % colors.length],
                        scale: scaleKey,
                        width: 2,
                        points: { show: false }
                    });
                } else {
                    // Overlay on price axis (moving averages)
                    opts.series.push({
                        label: indicator,
                        stroke: colors[index % colors.length],
                        scale: 'y',
                        width: 2,
                        points: { show: false },
                        dash: [5, 5]  // Dashed line for overlays
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
        
        // Destroy existing chart if any
        if (this.chart) {
            this.chart.destroy();
        }
        
        // Clear any loading/error messages
        this.container.innerHTML = '';
        
        // Create OHLC value display BEFORE creating chart options
        this.ohlcDisplay = document.createElement('div');
        this.ohlcDisplay.style.cssText = `
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(255, 255, 255, 0.95);
            padding: 8px 12px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
            line-height: 1.5;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            pointer-events: none;
            z-index: 10;
            display: none;
        `;
        this.container.style.position = 'relative';
        this.container.appendChild(this.ohlcDisplay);
        
        // Create chart options (now ohlcDisplay exists)
        const opts = this.createChartOptions(metadata);
        
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
        // Destroy existing chart first
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        
        this.container.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #999;">
                <p>Loading chart data...</p>
            </div>
        `;
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
