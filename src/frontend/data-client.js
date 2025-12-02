/**
 * Data Client Module
 * Handles communication with the FastAPI backend
 */

class DataClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    /**
     * Fetch chart data from the API
     * @param {string} filename - CSV filename to load
     * @param {Object} options - Optional parameters (indicators, timeframe, etc.)
     * @returns {Promise<Object>} Chart data in uPlot format
     */
    async fetchChartData(filename, options = {}) {
        const params = new URLSearchParams({ filename });
        
        // Add optional parameters
        if (options.indicators) {
            options.indicators.forEach(indicator => {
                params.append('indicators', indicator);
            });
        }
        
        if (options.timeframe) {
            params.append('timeframe', options.timeframe);
        }
        
        if (options.start_date) {
            params.append('start_date', options.start_date);
        }
        
        if (options.end_date) {
            params.append('end_date', options.end_date);
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/chart-data?${params}`);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to fetch chart data');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error fetching chart data:', error);
            throw error;
        }
    }
}

// Export for use in other modules
window.DataClient = DataClient;

