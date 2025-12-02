/**
 * Main Application Module - Task 26: MultiChartManager Integration
 * Integrates all components and handles user interactions
 */

class ChartApplication {
    constructor() {
        // Initialize components
        this.chartManager = null;
        this.activeIndicators = [];
        this.currentFilename = null;
        this.currentTimeframe = null;
        
        // Task 26.3: Parse URL parameters for overlays and subplots
        this.urlParams = this.parseURLParameters();
        
        // Get DOM elements
        this.fileInput = document.getElementById('file-select');
        this.timeframeSelect = document.getElementById('timeframe-select');
        this.indicatorSelect = document.getElementById('indicator-select');
        this.loadBtn = document.getElementById('load-btn');
        this.activeIndicatorsContainer = document.getElementById('active-indicators');
        
        // Initialize chart manager
        this.initializeChart();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Load state from localStorage or URL params
        this.loadState();
    }

    /**
     * Parse URL parameters
     * Task 26.3: URL parameter parsing functionality
     * @returns {Object} Parsed parameters {overlays, subplots, filename}
     */
    parseURLParameters() {
        const urlParams = new URLSearchParams(window.location.search);
        
        // Parse overlays (comma-separated)
        const overlaysParam = urlParams.get('overlays');
        const overlays = overlaysParam ? overlaysParam.split(',').filter(o => o.trim()) : [];
        
        // Parse subplots (comma-separated)
        const subplotsParam = urlParams.get('subplots');
        const subplots = subplotsParam ? subplotsParam.split(',').filter(s => s.trim()) : [];
        
        // Parse filename if provided
        const filename = urlParams.get('filename') || null;
        
        console.log('Parsed URL params:', { overlays, subplots, filename });
        
        return { overlays, subplots, filename };
    }

    /**
     * Initialize chart manager
     * Task 26.4: MultiChartManager integration
     */
    initializeChart() {
        try {
            // Task 26.4: Use MultiChartManager instead of ChartManager
            const container = document.getElementById('chart-container');
            
            // Configure multi-chart with overlays and subplots from URL
            const config = {
                overlays: this.urlParams.overlays,
                subplots: this.urlParams.subplots,
                mainChart: {
                    height: 400
                },
                sync: {
                    cursor: true,
                    zoom: true
                }
            };
            
            // Create MultiChartManager instance
            this.chartManager = new MultiChartManager(container, config);
            console.log('MultiChartManager initialized successfully');
            
            // If filename is in URL, auto-load
            if (this.urlParams.filename) {
                this.fileInput.value = this.urlParams.filename;
                this.currentFilename = this.urlParams.filename;
                // Auto-load after a short delay to allow UI to settle
                setTimeout(() => this.loadChart(), 100);
            }
        } catch (error) {
            console.error('Failed to initialize chart:', error);
            this.showError('Failed to initialize chart: ' + error.message);
        }
    }

    /**
     * Setup event listeners for UI controls
     */
    setupEventListeners() {
        // Load button
        this.loadBtn.addEventListener('click', () => {
            this.loadChart();
        });
        
        // Indicator selection
        this.indicatorSelect.addEventListener('change', (e) => {
            if (e.target.value) {
                this.addIndicator(e.target.value);
                e.target.value = ''; // Reset selection
            }
        });
        
        // Timeframe selection
        this.timeframeSelect.addEventListener('change', () => {
            if (this.currentFilename) {
                this.loadChart();
            }
        });
        
        // Enter key on file input
        this.fileInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.loadChart();
            }
        });
        
        // Window resize
        window.addEventListener('resize', () => {
            if (this.chartManager && this.chartManager.chart) {
                this.chartManager.resize();
            }
        });
    }

    /**
     * Add indicator to active list
     * @param {string} indicator - Indicator string (e.g., "RSI:14")
     */
    addIndicator(indicator) {
        if (!this.activeIndicators.includes(indicator)) {
            this.activeIndicators.push(indicator);
            this.updateIndicatorDisplay();
            this.saveState();
            
            // Reload chart if data is loaded
            if (this.currentFilename) {
                this.loadChart();
            }
        }
    }

    /**
     * Remove indicator from active list
     * @param {string} indicator - Indicator to remove
     */
    removeIndicator(indicator) {
        const index = this.activeIndicators.indexOf(indicator);
        if (index > -1) {
            this.activeIndicators.splice(index, 1);
            this.updateIndicatorDisplay();
            this.saveState();
            
            // Reload chart if data is loaded
            if (this.currentFilename) {
                this.loadChart();
            }
        }
    }

    /**
     * Update indicator display (badges)
     */
    updateIndicatorDisplay() {
        this.activeIndicatorsContainer.innerHTML = '';
        
        if (this.activeIndicators.length === 0) {
            this.activeIndicatorsContainer.innerHTML = '<span style="opacity: 0.7; font-size: 0.75rem;">No indicators</span>';
            return;
        }
        
        this.activeIndicators.forEach(indicator => {
            const badge = document.createElement('div');
            badge.className = 'indicator-badge';
            badge.innerHTML = `
                <span>${indicator}</span>
                <button onclick="app.removeIndicator('${indicator}')">&times;</button>
            `;
            this.activeIndicatorsContainer.appendChild(badge);
        });
    }

    /**
     * Load and render chart
     */
    async loadChart() {
        const filename = this.fileInput.value.trim();
        
        if (!filename) {
            this.showError('Please enter a CSV filename');
            return;
        }
        
        this.currentFilename = filename;
        this.currentTimeframe = this.timeframeSelect.value;
        
        // Build options
        const options = {
            indicators: this.activeIndicators
        };
        
        if (this.currentTimeframe) {
            options.timeframe = this.currentTimeframe;
        }
        
        // Save state
        this.saveState();
        
        // Load chart with debouncing
        try {
            await this.chartManager.loadAndRender(filename, options);
            console.log('Chart loaded successfully');
        } catch (error) {
            console.error('Error loading chart:', error);
            this.showError('Failed to load chart: ' + error.message);
        }
    }

    /**
     * Show error message
     * @param {string} message - Error message
     */
    showError(message) {
        alert(message);
    }

    /**
     * Save application state to localStorage
     */
    saveState() {
        const state = {
            filename: this.currentFilename,
            timeframe: this.currentTimeframe,
            indicators: this.activeIndicators
        };
        
        try {
            localStorage.setItem('chartAppState', JSON.stringify(state));
        } catch (error) {
            console.warn('Failed to save state:', error);
        }
    }

    /**
     * Load application state from localStorage
     */
    loadState() {
        try {
            const saved = localStorage.getItem('chartAppState');
            if (saved) {
                const state = JSON.parse(saved);
                
                if (state.filename) {
                    this.fileInput.value = state.filename;
                    this.currentFilename = state.filename;
                }
                
                if (state.timeframe) {
                    this.timeframeSelect.value = state.timeframe;
                    this.currentTimeframe = state.timeframe;
                }
                
                if (state.indicators && Array.isArray(state.indicators)) {
                    this.activeIndicators = state.indicators;
                    this.updateIndicatorDisplay();
                }
            }
        } catch (error) {
            console.warn('Failed to load state:', error);
        }
    }

    /**
     * Clear all state and reset
     */
    clearState() {
        this.activeIndicators = [];
        this.currentFilename = null;
        this.currentTimeframe = null;
        this.fileInput.value = '';
        this.timeframeSelect.value = '';
        this.updateIndicatorDisplay();
        
        try {
            localStorage.removeItem('chartAppState');
        } catch (error) {
            console.warn('Failed to clear state:', error);
        }
        
        if (this.chartManager) {
            this.chartManager.destroy();
        }
    }

    /**
     * Get current application state
     * @returns {Object} Current state
     */
    getState() {
        return {
            filename: this.currentFilename,
            timeframe: this.currentTimeframe,
            indicators: [...this.activeIndicators],
            hasChart: this.chartManager && this.chartManager.chart !== null
        };
    }
}

// Initialize application when DOM is ready
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new ChartApplication();
    console.log('Chart application initialized');
    
    // Expose globally for debugging
    window.app = app;
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChartApplication;
}

