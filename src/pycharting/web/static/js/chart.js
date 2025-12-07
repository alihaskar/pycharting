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
        this.measurementButtonElement = null;
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
            return index;
        }
        
        if (this.data && this.data[0] && this.data[0].length > 0) {
            const startIndex = this.data[0][0];
            const dataIndex = Math.round(index - startIndex);
            
            if (dataIndex >= 0 && dataIndex < this.timestamps.length) {
                const val = this.timestamps[dataIndex];
                
                // Heuristic: Only format as date if value looks like a timestamp (milliseconds)
                // Threshold: Year 1980 (~3.15e11 ms)
                if (typeof val === 'number' && val > 315360000000) {
                    const date = new Date(val);
                    return date.toLocaleString(undefined, {
                        month: 'numeric', day: 'numeric', 
                        hour: '2-digit', minute: '2-digit'
                    });
                }
                return val;
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
     * Also sets up measurement tool (activated with Shift key).
     * @private
     */
    _setupInteractions() {
        const u = this.chart;
        if (!u) return;
        
        const over = u.over;
        if (!over) return;
        
        // Setup measurement tool (Shift key)
        this._setupMeasurementTool();
        
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
        // Skip panning when Shift is pressed (for measurement tool)
        let dragging = false;
        let dragStartX = 0;
        let dragMin = 0;
        let dragMax = 0;
        
        over.addEventListener('mousedown', (e) => {
            if (e.button !== 0) return;
            // Skip panning if Shift is held OR measurement tool is enabled
            if (e.shiftKey || this.measurementState.enabled) return;
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
            
            // Resize measurement overlay to match plotting area
            if (this.measurementOverlay && this.chart.bbox) {
                const bbox = this.chart.bbox;
                
                this.measurementOverlay.style.left = bbox.left + 'px';
                this.measurementOverlay.style.top = bbox.top + 'px';
                this.measurementOverlay.width = bbox.width;
                this.measurementOverlay.height = bbox.height;
                this.measurementOverlay.style.width = bbox.width + 'px';
                this.measurementOverlay.style.height = bbox.height + 'px';
                
                // Redraw measurement if one exists
                if (this.measurementState && this.measurementState.startValX !== null && this._drawMeasurement) {
                    this._drawMeasurement();
                }
            }
        }
    }
    
    /**
     * Setup measurement tool (activated with Shift key or button)
     * @private
     */
    _setupMeasurementTool() {
        const u = this.chart;
        const over = u.over;
        if (!over) {
            console.warn('Cannot setup measurement tool: no overlay element');
            return;
        }
        
        console.log('Setting up measurement tool...');
        
        // State for measurement - stored in DATA coordinates for persistence
        this.measurementState = {
            measuring: false,
            startValX: null,  // Data value (x-axis)
            startValY: null,  // Data value (y-axis)
            endValX: null,
            endValY: null,
            enabled: false    // Button toggle state
        };
        let shiftPressed = false;
        
        // Overlay canvas for drawing measurement line
        const overlay = document.createElement('canvas');
        overlay.style.position = 'absolute';
        overlay.style.pointerEvents = 'none';
        overlay.style.zIndex = '10';
        over.parentElement.appendChild(overlay);
        
        const overlayCtx = overlay.getContext('2d');
        
        // Resize overlay to match chart plotting area exactly
        const resizeOverlay = () => {
            // Position overlay to match the plotting area (account for axes margins)
            overlay.style.left = u.bbox.left + 'px';
            overlay.style.top = u.bbox.top + 'px';
            
            // Size to match plotting area only
            overlay.width = u.bbox.width;
            overlay.height = u.bbox.height;
            overlay.style.width = u.bbox.width + 'px';
            overlay.style.height = u.bbox.height + 'px';
        };
        resizeOverlay();
        
        // Helper to format time delta
        const formatTimeDelta = (ms) => {
            const seconds = Math.abs(ms / 1000);
            const minutes = Math.floor(seconds / 60);
            const hours = Math.floor(minutes / 60);
            const days = Math.floor(hours / 24);
            
            if (days > 0) return `${days}d ${hours % 24}h`;
            if (hours > 0) return `${hours}h ${minutes % 60}m`;
            if (minutes > 0) return `${minutes}m ${Math.floor(seconds % 60)}s`;
            return `${seconds.toFixed(1)}s`;
        };
        
        // Helper to draw line directly from coordinates (bypass data conversion)
        this._drawMeasurementLine = (startX, startY, endX, endY) => {
            overlayCtx.clearRect(0, 0, overlay.width, overlay.height);
            
            // Draw line
            overlayCtx.strokeStyle = '#2196F3';
            overlayCtx.lineWidth = 2;
            overlayCtx.setLineDash([5, 5]);
            overlayCtx.beginPath();
            overlayCtx.moveTo(startX, startY);
            overlayCtx.lineTo(endX, endY);
            overlayCtx.stroke();
            overlayCtx.setLineDash([]);
            
            // Draw circles
            overlayCtx.fillStyle = '#2196F3';
            overlayCtx.beginPath();
            overlayCtx.arc(startX, startY, 5, 0, Math.PI * 2);
            overlayCtx.fill();
            overlayCtx.beginPath();
            overlayCtx.arc(endX, endY, 5, 0, Math.PI * 2);
            overlayCtx.fill();
            
            // We can still show the box using data values (which we have)
            // But line position is visual only
        };
        
        // Draw measurement - uses DATA coordinates for persistence through zoom/pan
        const drawMeasurement = () => {
            overlayCtx.clearRect(0, 0, overlay.width, overlay.height);
            
            const ms = this.measurementState;
            // Draw if we have valid start/end points (even if measuring is complete)
            if (ms.startValX === null || ms.endValX === null) {
                return;
            }
            
            let startX, startY, endX, endY;
            
            // Use stored visual coords if available (prevents drift on release)
            if (ms.visualStartX != null && ms.visualEndX != null) {
                startX = ms.visualStartX;
                startY = ms.visualStartY;
                endX = ms.visualEndX;
                endY = ms.visualEndY;
            } else {
                // Recalculate from data (for zoom/pan)
                // Convert data coordinates to pixel coordinates relative to PLOTTING AREA (bbox)
                startX = u.valToPos(ms.startValX, 'x', false);
                startY = u.valToPos(ms.startValY, 'y', false);
                endX = u.valToPos(ms.endValX, 'x', false);
                endY = u.valToPos(ms.endValY, 'y', false);
            }
            
            // Draw line
            overlayCtx.strokeStyle = '#2196F3';
            overlayCtx.lineWidth = 2;
            overlayCtx.setLineDash([5, 5]);
            overlayCtx.beginPath();
            overlayCtx.moveTo(startX, startY);
            overlayCtx.lineTo(endX, endY);
            overlayCtx.stroke();
            overlayCtx.setLineDash([]);
            
            // Draw circles at endpoints
            overlayCtx.fillStyle = '#2196F3';
            overlayCtx.beginPath();
            overlayCtx.arc(startX, startY, 5, 0, Math.PI * 2);
            overlayCtx.fill();
            overlayCtx.beginPath();
            overlayCtx.arc(endX, endY, 5, 0, Math.PI * 2);
            overlayCtx.fill();
            
            // Calculate deltas
            const deltaVal = ms.endValY - ms.startValY;
            const deltaPercent = ((deltaVal / ms.startValY) * 100).toFixed(2);
            
            // Calculate time delta
            let timeDeltaStr = '';
            if (this.timestamps) {
                const startIdx = Math.round(ms.startValX);
                const endIdx = Math.round(ms.endValX);
                const startDataIdx = Math.max(0, Math.min(this.timestamps.length - 1, startIdx - (this.chart.data[0][0] || 0)));
                const endDataIdx = Math.max(0, Math.min(this.timestamps.length - 1, endIdx - (this.chart.data[0][0] || 0)));
                
                if (this.timestamps[startDataIdx] && this.timestamps[endDataIdx]) {
                    const timeDelta = this.timestamps[endDataIdx] - this.timestamps[startDataIdx];
                    timeDeltaStr = formatTimeDelta(timeDelta);
                } else {
                    timeDeltaStr = `${Math.abs(endIdx - startIdx).toFixed(0)} bars`;
                }
            } else {
                timeDeltaStr = `${Math.abs(ms.endValX - ms.startValX).toFixed(0)} bars`;
            }
            
            // Draw measurement box
            const boxX = (startX + endX) / 2;
            const boxY = (startY + endY) / 2 - 40;
            
            const lines = [
                `Δ Price: ${deltaVal >= 0 ? '+' : ''}${deltaVal.toFixed(2)}`,
                `Δ %: ${deltaPercent >= 0 ? '+' : ''}${deltaPercent}%`,
                `Δ Time: ${timeDeltaStr}`
            ];
            
            // Measure text width for box sizing
            overlayCtx.font = '12px monospace';
            const maxWidth = Math.max(...lines.map(l => overlayCtx.measureText(l).width));
            const boxWidth = maxWidth + 20;
            const boxHeight = 60;
            
            // Draw box background
            overlayCtx.fillStyle = 'rgba(33, 33, 33, 0.9)';
            overlayCtx.fillRect(boxX - boxWidth / 2, boxY, boxWidth, boxHeight);
            
            // Draw box border
            overlayCtx.strokeStyle = '#2196F3';
            overlayCtx.lineWidth = 1;
            overlayCtx.strokeRect(boxX - boxWidth / 2, boxY, boxWidth, boxHeight);
            
            // Draw text
            overlayCtx.fillStyle = deltaVal >= 0 ? '#26a69a' : '#ef5350';
            overlayCtx.textAlign = 'center';
            lines.forEach((line, i) => {
                overlayCtx.fillText(line, boxX, boxY + 18 + i * 16);
            });
        };
        
        // Track Shift key
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Shift') {
                shiftPressed = true;
                this.measurementState.enabled = true;
                over.style.cursor = 'crosshair';
                console.log('Measurement tool activated (Shift pressed)');
            }
        });
        
        window.addEventListener('keyup', (e) => {
            if (e.key === 'Shift') {
                shiftPressed = false;
                // Don't disable if button is active
                if (!this.measurementButtonActive) {
                    this.measurementState.enabled = false;
                    over.style.cursor = 'default';
                }
                console.log('Measurement tool deactivated (Shift released)');
            }
        });
        
        const getPlotCoords = (event) => {
            const rect = overlay.getBoundingClientRect();
            const rawX = event.clientX - rect.left;
            const rawY = event.clientY - rect.top;
            const clamp = (value, limit) => Math.max(0, Math.min(limit, value));
            return {
                x: clamp(rawX, overlay.width),
                y: clamp(rawY, overlay.height),
            };
        };

        // Click to start/end measurement (when enabled via Shift or button)
        over.addEventListener('mousedown', (e) => {
            const ms = this.measurementState;
            if (!ms.enabled && !shiftPressed) return;
            
            e.preventDefault();
            e.stopPropagation();
            
            const { x: plotX, y: plotY } = getPlotCoords(e);
            
            if (!ms.measuring) {
                // Start new measurement
                ms.startValX = u.posToVal(plotX, 'x');
                ms.startValY = u.posToVal(plotY, 'y');
                ms.endValX = ms.startValX;
                ms.endValY = ms.startValY;
                ms.measuring = true;
                
                // Store visual start point
                ms.visualStartX = plotX;
                ms.visualStartY = plotY;
                ms.visualEndX = plotX;
                ms.visualEndY = plotY;
                
                this._drawMeasurementLine(plotX, plotY, plotX, plotY);
                console.log('Measurement started');
            } else {
                ms.measuring = false;
                drawMeasurement(); 
                console.log('Measurement ended');
                this._autoDeactivateMeasurementButton();
            }
        }, true);  // Use capture phase to get event first
        
        // Mouse move to update measurement line
        over.addEventListener('mousemove', (e) => {
            const ms = this.measurementState;
            if (!ms.measuring) return;
            
            const { x: plotX, y: plotY } = getPlotCoords(e);
            
            // Update end point in DATA coordinates
            ms.endValX = u.posToVal(plotX, 'x');
            ms.endValY = u.posToVal(plotY, 'y');
            
            // Store visual end point
            ms.visualEndX = plotX;
            ms.visualEndY = plotY;
            
            // Draw using visual coords to prevent jitter/drift
            // Use stored visual start to ensure anchor doesn't move
            this._drawMeasurementLine(ms.visualStartX, ms.visualStartY, plotX, plotY);
        });
        
        // Hook into uPlot to redraw measurement on scale changes (zoom/pan)
        u.hooks.setScale = u.hooks.setScale || [];
        u.hooks.setScale.push(() => {
            // Clear visual coords to force recalculation from data on zoom
            if (this.measurementState) {
                this.measurementState.visualStartX = null;
                this.measurementState.visualStartY = null;
                this.measurementState.visualEndX = null;
                this.measurementState.visualEndY = null;
            }
            // Redraw measurement after scale changes
            drawMeasurement();
        });
        
        // Store references for cleanup and external access
        this.measurementOverlay = overlay;
        this.measurementButtonActive = false;
        this._drawMeasurement = drawMeasurement; // Store for resize/external calls
        console.log('Measurement tool ready (Hold Shift + Click to measure)');
    }
    
    /**
     * Enable measurement tool via button click
     */
    enableMeasurementTool() {
        this.measurementButtonActive = true;
        this.measurementState.enabled = true;
        if (this.chart && this.chart.over) {
            this.chart.over.style.cursor = 'crosshair';
        }
        this._updateMeasurementButtonElement();
        console.log('Measurement tool enabled via button');
    }
    
    /**
     * Disable measurement tool via button click
     */
    disableMeasurementTool() {
        this.measurementButtonActive = false;
        this.measurementState.enabled = false;
        
        // Clear all measurement state
        this.measurementState.measuring = false;
        this.measurementState.startValX = null;
        this.measurementState.startValY = null;
        this.measurementState.endValX = null;
        this.measurementState.endValY = null;
        
        // Clear the overlay canvas
        if (this.measurementOverlay) {
            const ctx = this.measurementOverlay.getContext('2d');
            ctx.clearRect(0, 0, this.measurementOverlay.width, this.measurementOverlay.height);
        }
        
        if (this.chart && this.chart.over) {
            this.chart.over.style.cursor = 'default';
        }
        this._updateMeasurementButtonElement();
        console.log('Measurement tool disabled via button');
    }
    
    /**
     * Check if measurement tool is enabled
     */
    get measurementEnabled() {
        return this.measurementButtonActive;
    }

    /**
     * Register DOM button for measurement so we can keep classes in sync.
     * Clears previous registration if passed null.
     */
    registerMeasurementButton(button) {
        this.measurementButtonElement = button;
        this._updateMeasurementButtonElement();
    }

    _updateMeasurementButtonElement() {
        if (!this.measurementButtonElement) return;
        if (this.measurementButtonActive) {
            this.measurementButtonElement.classList.add('active');
        } else {
            this.measurementButtonElement.classList.remove('active');
        }
    }

    _autoDeactivateMeasurementButton() {
        if (!this.measurementButtonActive) return;

        this.measurementButtonActive = false;
        if (this.measurementState) {
            this.measurementState.enabled = false;
        }
        if (this.chart && this.chart.over) {
            this.chart.over.style.cursor = 'default';
        }
        this._updateMeasurementButtonElement();
    }
    
    /**
     * Destroy the chart and clean up resources
     */
    destroy() {
        if (this.measurementOverlay) {
            this.measurementOverlay.remove();
            this.measurementOverlay = null;
        }
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
