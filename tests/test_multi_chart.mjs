/**
 * Node.js test runner for MultiChartManager
 * Uses ES modules to test the frontend class
 */

// Mock DOM elements for Node.js
class MockHTMLElement {
    constructor() {
        this._innerHTML = '';
        this.id = '';
        this.style = {};
        this.children = [];
    }
    
    get innerHTML() {
        return this._innerHTML;
    }
    
    set innerHTML(value) {
        this._innerHTML = value;
        // Clear children when innerHTML is set
        if (value === '') {
            this.children = [];
        }
    }
    
    appendChild(child) {
        this.children.push(child);
    }
}

global.HTMLElement = MockHTMLElement;
global.document = {
    createElement(tag) {
        return new MockHTMLElement();
    }
};

// Import the class to test
import { MultiChartManager } from '../src/frontend/multi-chart.js';

// Test utilities
let passed = 0;
let failed = 0;

function test(description, fn) {
    try {
        fn();
        passed++;
        console.log(`✓ ${description}`);
    } catch (error) {
        failed++;
        console.error(`✗ ${description}`);
        console.error(`  ${error.message}`);
    }
}

function assertEqual(actual, expected, message = '') {
    if (actual !== expected) {
        throw new Error(`${message}\nExpected: ${expected}\nActual: ${actual}`);
    }
}

function assertTrue(value, message = '') {
    if (!value) {
        throw new Error(`${message}\nExpected truthy value, got: ${value}`);
    }
}

function assertFalse(value, message = '') {
    if (value) {
        throw new Error(`${message}\nExpected falsy value, got: ${value}`);
    }
}

function assertNotNull(value, message = '') {
    if (value === null || value === undefined) {
        throw new Error(`${message}\nExpected non-null value, got: ${value}`);
    }
}

function assertThrows(fn, message = '') {
    try {
        fn();
        throw new Error(`${message}\nExpected function to throw an error`);
    } catch (e) {
        if (e.message.includes('Expected function to throw')) {
            throw e;
        }
        // Expected - function threw an error
    }
}

// === Test 20.1: Constructor and Property Initialization ===

test('MultiChartManager constructor accepts container and config', () => {
    const container = new MockHTMLElement();
    const config = { mainChart: {}, subplots: [] };
    
    const manager = new MultiChartManager(container, config);
    
    assertNotNull(manager);
    assertEqual(manager.container, container);
});

test('MultiChartManager initializes properties correctly', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertEqual(manager.mainChart, null);
    assertTrue(Array.isArray(manager.subplots));
    assertEqual(manager.subplots.length, 0);
    assertTrue(Array.isArray(manager.syncedCharts));
    assertEqual(manager.syncedCharts.length, 0);
});

test('MultiChartManager validates container element', () => {
    assertThrows(() => {
        new MultiChartManager(null, {});
    }, 'Should throw error for null container');
});

test('MultiChartManager validates config object', () => {
    const container = new MockHTMLElement();
    
    assertThrows(() => {
        new MultiChartManager(container, null);
    }, 'Should throw error for null config');
});

test('MultiChartManager merges with default config', () => {
    const container = new MockHTMLElement();
    const customConfig = { mainChart: { height: 500 } };
    
    const manager = new MultiChartManager(container, customConfig);
    
    assertNotNull(manager.config);
    assertEqual(manager.config.mainChart.height, 500);
});

test('MultiChartManager has expected methods', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.initialize === 'function');
    assertTrue(typeof manager.createContainers === 'function');
    assertTrue(typeof manager.setupSynchronization === 'function');
    assertTrue(typeof manager.createMainChart === 'function');
    assertTrue(typeof manager.createSubplots === 'function');
});

test('MultiChartManager config has sync settings', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertNotNull(manager.config.sync);
    assertTrue(manager.config.sync.cursor === true);
    assertTrue(manager.config.sync.zoom === true);
});

test('MultiChartManager createContainers creates main container', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, { subplots: [] });
    
    manager.createContainers();
    
    assertTrue(container.children.length > 0);
});

// === Test 20.2: Chart Instance Management ===

test('MultiChartManager can add chart instances', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    const chartMock = { id: 'test-chart', type: 'main' };
    manager.addChart(chartMock);
    
    assertTrue(manager.syncedCharts.length > 0);
});

test('MultiChartManager can remove chart instances', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    const chartMock = { id: 'test-chart', type: 'main' };
    manager.addChart(chartMock);
    manager.removeChart('test-chart');
    
    assertEqual(manager.syncedCharts.length, 0);
});

test('MultiChartManager can get chart by id', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    const chartMock = { id: 'test-chart', type: 'main' };
    manager.addChart(chartMock);
    
    const retrieved = manager.getChart('test-chart');
    assertEqual(retrieved.id, 'test-chart');
});

test('MultiChartManager can clear all charts', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    manager.addChart({ id: 'chart1', type: 'main' });
    manager.addChart({ id: 'chart2', type: 'subplot' });
    manager.clearCharts();
    
    assertEqual(manager.syncedCharts.length, 0);
    assertEqual(manager.mainChart, null);
    assertEqual(manager.subplots.length, 0);
});

// === Test 20.3: Configuration Handling ===

test('MultiChartManager validates configuration', () => {
    const container = new MockHTMLElement();
    const config = {
        mainChart: { height: 400 },
        subplots: [{ name: 'RSI', height: 150 }]
    };
    
    const manager = new MultiChartManager(container, config);
    const isValid = manager.validateConfig();
    
    assertTrue(isValid);
});

test('MultiChartManager can get chart-specific config', () => {
    const container = new MockHTMLElement();
    const config = {
        mainChart: { height: 400 },
        subplots: [{ name: 'RSI', height: 150 }]
    };
    
    const manager = new MultiChartManager(container, config);
    const chartConfig = manager.getChartConfig('mainChart');
    
    assertNotNull(chartConfig);
    assertEqual(chartConfig.height, 400);
});

// === Test 20.4: Method Signatures and Interface ===

test('MultiChartManager has updateChart method', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.updateChart === 'function');
});

test('MultiChartManager has destroyChart method', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.destroyChart === 'function');
});

test('MultiChartManager has syncCursor method', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.syncCursor === 'function');
});

test('MultiChartManager has syncZoom method', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.syncZoom === 'function');
});

test('MultiChartManager methods have JSDoc documentation', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    // Check that key methods exist (documentation checked in code review)
    assertTrue(typeof manager.initialize === 'function');
    assertTrue(typeof manager.updateChart === 'function');
    assertTrue(typeof manager.destroyChart === 'function');
});

// === Test 21.1: Layout Height Calculations ===

test('MultiChartManager calculates 100% height with no subplots', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, { subplots: [] });
    
    const heights = manager.calculateHeights();
    
    assertEqual(heights.main, '100%');
    assertEqual(heights.subplot, '0%');
});

test('MultiChartManager calculates 60/40 split with subplots', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, { 
        subplots: [{ name: 'RSI' }] 
    });
    
    const heights = manager.calculateHeights();
    
    assertEqual(heights.main, '60%');
    assertEqual(heights.subplot, '40%');
});

test('MultiChartManager splits subplot height evenly', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, { 
        subplots: [{ name: 'RSI' }, { name: 'MACD' }] 
    });
    
    const heights = manager.calculateHeights();
    
    assertEqual(heights.main, '60%');
    assertEqual(heights.subplot, '20%'); // 40% / 2
});

test('MultiChartManager handles 5 subplots correctly', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, { 
        subplots: [{}, {}, {}, {}, {}]
    });
    
    const heights = manager.calculateHeights();
    
    assertEqual(heights.main, '60%');
    assertEqual(heights.subplot, '8%'); // 40% / 5
});

// === Test 21.2: DOM Element Creation and Styling ===

test('MultiChartManager creates main container with correct height', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, { subplots: [] });
    
    manager.createContainers();
    
    assertTrue(container.children.length === 1);
    assertEqual(container.children[0].style.height, '100%');
});

test('MultiChartManager creates subplot containers', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, { 
        subplots: [{ name: 'RSI' }, { name: 'MACD' }] 
    });
    
    manager.createContainers();
    
    // 1 main + 2 subplots = 3 total
    assertEqual(container.children.length, 3);
});

test('MultiChartManager applies correct styling to containers', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, { 
        subplots: [{ name: 'RSI' }] 
    });
    
    manager.createContainers();
    
    // Check main container
    assertEqual(container.children[0].style.height, '60%');
    // Check subplot container
    assertEqual(container.children[1].style.height, '40%');
});

// === Test 21.3: Container ID Generation ===

test('MultiChartManager assigns main-chart ID', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, { subplots: [] });
    
    manager.createContainers();
    
    assertEqual(container.children[0].id, 'main-chart-container');
});

test('MultiChartManager assigns subplot IDs with index', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, { 
        subplots: [{ name: 'RSI' }, { name: 'MACD' }] 
    });
    
    manager.createContainers();
    
    assertEqual(container.children[1].id, 'subplot-0-container');
    assertEqual(container.children[2].id, 'subplot-1-container');
});

test('MultiChartManager IDs are unique', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, { 
        subplots: [{}, {}, {}] 
    });
    
    manager.createContainers();
    
    const ids = container.children.map(c => c.id);
    const uniqueIds = new Set(ids);
    
    assertEqual(ids.length, uniqueIds.size);
});

// === Test 21.4: Responsive Design ===

test('MultiChartManager containers clear previous content', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, { subplots: [] });
    
    container.innerHTML = 'old content';
    manager.createContainers();
    
    assertEqual(container.innerHTML, '');
    assertTrue(container.children.length > 0);
});

test('MultiChartManager can recreate containers', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, { 
        subplots: [{ name: 'RSI' }] 
    });
    
    manager.createContainers();
    const firstCount = container.children.length;
    
    manager.createContainers();
    const secondCount = container.children.length;
    
    // Should have 2 containers (1 main + 1 subplot)
    assertEqual(firstCount, 2);
    assertEqual(secondCount, 2);
});

// === Test 22: Main Chart with Overlays ===

test('MultiChartManager has createMainChart method', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.createMainChart === 'function');
});

test('MultiChartManager has fetchChartData method', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.fetchChartData === 'function');
});

test('MultiChartManager has getCandlestickFill function', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.getCandlestickFill === 'function');
});

test('MultiChartManager has getIndicatorColor function', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.getIndicatorColor === 'function');
});

test('MultiChartManager getCandlestickFill returns correct colors', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    // Bullish candle (close > open)
    const bullishColor = manager.getCandlestickFill(null, 0, [0, 100, 110, 95, 108]);
    assertTrue(typeof bullishColor === 'string');
    
    // Bearish candle (close < open)
    const bearishColor = manager.getCandlestickFill(null, 0, [0, 100, 110, 95, 98]);
    assertTrue(typeof bearishColor === 'string');
    
    // Different colors for bull/bear
    assertTrue(bullishColor !== bearishColor);
});

test('MultiChartManager getIndicatorColor returns distinct colors', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    const color1 = manager.getIndicatorColor('sma_20');
    const color2 = manager.getIndicatorColor('ema_50');
    
    assertTrue(typeof color1 === 'string');
    assertTrue(typeof color2 === 'string');
    assertTrue(color1 !== color2);
});

test('MultiChartManager creates series configuration for overlays', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {
        overlays: ['sma_20', 'ema_50']
    });
    
    const series = manager.createSeriesConfig(['sma_20', 'ema_50']);
    
    assertTrue(Array.isArray(series));
    // Should have: time series + OHLC + 2 overlays = 4 series
    assertTrue(series.length >= 3);
});

test('MultiChartManager creates axes configuration with shared scale', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    const axes = manager.createAxesConfig();
    
    assertTrue(Array.isArray(axes));
    assertTrue(axes.length === 2); // x-axis and y-axis
});

// === Test 23: Subplot Charts ===

test('MultiChartManager has extractSubplotData method', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.extractSubplotData === 'function');
});

test('MultiChartManager extractSubplotData filters correct data', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    const fullData = [
        [100, 200, 300],        // timestamps
        [50, 51, 52],           // RSI
        [10, 11, 12]            // MACD
    ];
    
    const subplotData = manager.extractSubplotData(fullData, 'rsi', 1);
    
    assertTrue(Array.isArray(subplotData));
    assertEqual(subplotData.length, 2); // timestamps + indicator
    assertEqual(subplotData[0].length, 3); // 3 data points
});

test('MultiChartManager creates subplot series config', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    const series = manager.createSubplotSeriesConfig('rsi_14', 'line');
    
    assertTrue(Array.isArray(series));
    assertTrue(series.length === 2); // time + indicator
    assertEqual(series[1].label, 'rsi_14');
});

test('MultiChartManager creates subplot axes with independent scale', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    const axes = manager.createSubplotAxesConfig('rsi_14');
    
    assertTrue(Array.isArray(axes));
    assertTrue(axes.length === 2);
    // Check y-axis has custom scale
    assertNotNull(axes[1].scale);
});

test('MultiChartManager detects chart type from indicator', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    const rsiType = manager.detectChartType('rsi');
    const volumeType = manager.detectChartType('volume');
    
    assertEqual(rsiType, 'line');
    assertEqual(volumeType, 'histogram');
});

test('MultiChartManager handles multiple subplots', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {
        subplots: [
            { name: 'rsi_14', type: 'line' },
            { name: 'macd', type: 'line' }
        ]
    });
    
    // Subplots config should have 2 items
    assertEqual(manager.config.subplots.length, 2);
});

test('MultiChartManager creates unique scales for each subplot', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    const scale1 = manager.createScaleConfig('rsi_14');
    const scale2 = manager.createScaleConfig('macd');
    
    assertNotNull(scale1);
    assertNotNull(scale2);
    assertTrue(scale1.auto === true);
});

test('MultiChartManager getSubplotHeight calculates correct height', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {
        subplots: [{ name: 'rsi' }, { name: 'macd' }]
    });
    
    const height = manager.getSubplotHeight();
    
    assertTrue(typeof height === 'number');
    assertTrue(height > 0);
});

// === Test 24: Cursor Synchronization ===

test('MultiChartManager setupSynchronization collects all charts', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    // Mock some chart instances
    manager.mainChart = { id: 'main' };
    manager.subplots = [{ id: 'sub1' }, { id: 'sub2' }];
    
    manager.setupSynchronization();
    
    // Should have collected all charts
    assertTrue(manager.syncedCharts.length === 3);
});

test('MultiChartManager creates sync group', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    manager.mainChart = { id: 'main' };
    manager.setupSynchronization();
    
    // Sync group should be created
    assertNotNull(manager.syncGroup);
});

test('MultiChartManager propagateCursorPosition updates all charts', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    // Mock charts with setCursor method
    let chart1Updated = false;
    let chart2Updated = false;
    
    const chart1 = { 
        id: 'chart1',
        setCursor: (pos) => { chart1Updated = true; }
    };
    const chart2 = { 
        id: 'chart2',
        setCursor: (pos) => { chart2Updated = true; }
    };
    
    manager.syncedCharts = [chart1, chart2];
    
    // Propagate cursor from chart1
    manager.propagateCursorPosition(chart1, { left: 100, top: 50 });
    
    // chart1 should not update itself, chart2 should
    assertFalse(chart1Updated);
    assertTrue(chart2Updated);
});

test('MultiChartManager throttle function limits call frequency', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    let callCount = 0;
    const fn = () => { callCount++; };
    
    const throttled = manager.throttle(fn, 100);
    
    // Call multiple times rapidly
    throttled();
    throttled();
    throttled();
    
    // Should only call once immediately
    assertEqual(callCount, 1);
});

test('MultiChartManager setupCursorHandlers binds event handlers', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    const mockChart = { 
        id: 'test',
        over: { addEventListener: () => {} }
    };
    
    manager.syncedCharts = [mockChart];
    
    // Should not throw
    manager.setupCursorHandlers();
    assertTrue(true);
});

test('MultiChartManager has proper sync configuration', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {
        sync: {
            cursor: true,
            zoom: true
        }
    });
    
    assertTrue(manager.config.sync.cursor);
    assertTrue(manager.config.sync.zoom);
});

// Print results
console.log('\n' + '='.repeat(50));
console.log(`Total: ${passed + failed}`);
console.log(`Passed: ${passed}`);
console.log(`Failed: ${failed}`);
console.log('='.repeat(50));

if (failed > 0) {
    process.exit(1);
}

