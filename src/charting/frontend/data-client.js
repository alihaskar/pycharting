/**
 * Data Client Module
 * Handles communication with the FastAPI backend
 */

/**
 * Custom error classes for better error handling
 */
class APIError extends Error {
    constructor(message, status) {
        super(message);
        this.name = 'APIError';
        this.status = status;
    }
}

class NetworkError extends Error {
    constructor(message) {
        super(message);
        this.name = 'NetworkError';
    }
}

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ValidationError';
    }
}

/**
 * Loading state manager for tracking request states
 */
class LoadingStateManager {
    constructor() {
        this.states = new Map();
        this.listeners = [];
    }

    setState(key, state) {
        this.states.set(key, {
            status: state,
            timestamp: Date.now()
        });
        this.notify(key, state);
    }

    getState(key) {
        return this.states.get(key)?.status || 'idle';
    }

    isLoading(key) {
        return this.getState(key) === 'loading';
    }

    addListener(callback) {
        this.listeners.push(callback);
    }

    notify(key, state) {
        this.listeners.forEach(callback => callback(key, state));
    }
}

class DataClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.pendingRequests = new Map();
        this.debounceTimers = new Map();
        this.loadingState = new LoadingStateManager();
    }

    /**
     * Debounce a function call
     * @param {string} key - Unique key for the debounce timer
     * @param {Function} fn - Function to debounce
     * @param {number} delay - Delay in milliseconds
     */
    debounce(key, fn, delay = 300) {
        // Clear existing timer
        if (this.debounceTimers.has(key)) {
            clearTimeout(this.debounceTimers.get(key));
        }
        
        // Set new timer
        return new Promise((resolve, reject) => {
            const timer = setTimeout(async () => {
                this.debounceTimers.delete(key);
                try {
                    const result = await fn();
                    resolve(result);
                } catch (error) {
                    reject(error);
                }
            }, delay);
            
            this.debounceTimers.set(key, timer);
        });
    }

    /**
     * Cancel a pending request
     * @param {string} key - Request key to cancel
     */
    cancelRequest(key) {
        // Cancel debounce timer
        if (this.debounceTimers.has(key)) {
            clearTimeout(this.debounceTimers.get(key));
            this.debounceTimers.delete(key);
        }
        
        // Abort fetch request
        if (this.pendingRequests.has(key)) {
            this.pendingRequests.get(key).abort();
            this.pendingRequests.delete(key);
        }
        
        // Update loading state
        this.loadingState.setState(key, 'cancelled');
    }

    /**
     * Fetch chart data from the API
     * @param {string} filename - CSV filename to load
     * @param {Object} options - Optional parameters (indicators, timeframe, etc.)
     * @returns {Promise<Object>} Chart data in uPlot format
     */
    async fetchChartData(filename, options = {}) {
        // Validate required parameter
        if (!filename || typeof filename !== 'string') {
            throw new ValidationError('Filename is required and must be a string');
        }
        
        const requestKey = `chart-${filename}-${JSON.stringify(options)}`;
        
        // Set loading state
        this.loadingState.setState(requestKey, 'loading');
        
        // Build query parameters
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
            // Create abort controller for request cancellation
            const controller = new AbortController();
            this.pendingRequests.set(requestKey, controller);
            
            const response = await fetch(`${this.baseUrl}/chart-data?${params}`, {
                signal: controller.signal
            });
            
            // Clean up pending request
            this.pendingRequests.delete(requestKey);
            
            if (!response.ok) {
                const error = await response.json();
                throw new APIError(error.detail || 'Failed to fetch chart data', response.status);
            }
            
            const data = await response.json();
            
            // Update loading state to success
            this.loadingState.setState(requestKey, 'success');
            
            return data;
        } catch (error) {
            // Clean up
            this.pendingRequests.delete(requestKey);
            
            // Update loading state to error
            this.loadingState.setState(requestKey, 'error');
            
            // Handle different error types
            if (error.name === 'AbortError') {
                console.log('Request cancelled:', requestKey);
                throw new NetworkError('Request was cancelled');
            } else if (error instanceof APIError) {
                console.error('API error:', error.message);
                throw error;
            } else {
                console.error('Network error fetching chart data:', error);
                throw new NetworkError(error.message || 'Network request failed');
            }
        }
    }

    /**
     * Fetch chart data with debouncing
     * @param {string} filename - CSV filename to load
     * @param {Object} options - Optional parameters
     * @param {number} delay - Debounce delay in milliseconds
     * @returns {Promise<Object>} Chart data in uPlot format
     */
    async fetchChartDataDebounced(filename, options = {}, delay = 300) {
        const requestKey = `chart-${filename}`;
        return this.debounce(requestKey, () => this.fetchChartData(filename, options), delay);
    }
}

// Export for use in other modules
window.DataClient = DataClient;
window.APIError = APIError;
window.NetworkError = NetworkError;
window.ValidationError = ValidationError;
window.LoadingStateManager = LoadingStateManager;

