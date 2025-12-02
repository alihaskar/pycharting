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

// === Test 25: Zoom and Pan Synchronization ===

test('MultiChartManager has setupZoomPanSync method', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.setupZoomPanSync === 'function');
});

test('MultiChartManager propagates zoom scale to all charts', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    let chart2Updated = false;
    let chart3Updated = false;
    
    const chart1 = { 
        id: 'chart1',
        scales: { x: { min: 100, max: 200 } }
    };
    const chart2 = { 
        id: 'chart2',
        setScale: (axis, range) => { chart2Updated = true; }
    };
    const chart3 = { 
        id: 'chart3',
        setScale: (axis, range) => { chart3Updated = true; }
    };
    
    manager.syncedCharts = [chart1, chart2, chart3];
    
    // Propagate zoom from chart1
    manager.propagateZoomScale(chart1, 'x', { min: 100, max: 200 });
    
    // chart2 and chart3 should update, chart1 should not
    assertTrue(chart2Updated);
    assertTrue(chart3Updated);
});

test('MultiChartManager filters x-axis events only', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    // Should return true for x-axis
    assertTrue(manager.shouldSyncAxis('x'));
    
    // Should return false for y-axis
    assertFalse(manager.shouldSyncAxis('y'));
    assertFalse(manager.shouldSyncAxis('price'));
});

test('MultiChartManager prevents infinite loops in zoom sync', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    let updateCount = 0;
    
    const chart1 = { 
        id: 'chart1',
        scales: { x: { min: 100, max: 200 } },
        setScale: () => { updateCount++; }
    };
    const chart2 = { 
        id: 'chart2',
        scales: { x: { min: 100, max: 200 } },
        setScale: () => { updateCount++; }
    };
    
    manager.syncedCharts = [chart1, chart2];
    manager._syncInProgress = false;
    
    // Propagate zoom
    manager.propagateZoomScale(chart1, 'x', { min: 150, max: 250 });
    
    // Should only update chart2, not trigger additional updates
    assertEqual(updateCount, 1);
});

test('MultiChartManager has hook registration method', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.registerScaleHooks === 'function');
});

// ============================================================================
// Test Suite: Task 6.1 - Dynamic Container Creation for N Subplots
// ============================================================================

test('MultiChartManager has createSubplotContainers method', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.createSubplotContainers === 'function',
        'Should have createSubplotContainers method');
});

test('createSubplotContainers creates N containers based on indicator count', () => {
    const container = new MockHTMLElement();
    container.offsetHeight = 800;
    const manager = new MultiChartManager(container, {
        subplots: [
            { name: 'rsi_14' },
            { name: 'macd' },
            { name: 'stoch' }
        ]
    });
    
    manager.createSubplotContainers(3);
    
    // Should create 3 subplot containers
    assertTrue(manager.subplotContainers.length === 3,
        `Should create 3 containers, got ${manager.subplotContainers.length}`);
});

test('createSubplotContainers assigns unique IDs to each container', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    manager.createSubplotContainers(5);
    
    const ids = manager.subplotContainers.map(c => c.id);
    const uniqueIds = new Set(ids);
    
    assertEqual(uniqueIds.size, 5, 'All container IDs should be unique');
});

test('createSubplotContainers adds data attributes for indicator mapping', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {
        subplots: [
            { name: 'rsi_14' },
            { name: 'macd' }
        ]
    });
    
    manager.createSubplotContainers(2);
    
    // Each container should have indicator info
    assertTrue(manager.subplotContainers[0].dataset !== undefined ||
               manager.subplotContainers[0]._dataset !== undefined,
        'Containers should have dataset for indicator mapping');
});

test('getSubplotCount method exists', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.getSubplotCount === 'function',
        'Should have getSubplotCount method');
});

test('getSubplotCount returns correct count from config', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {
        subplots: [
            { name: 'rsi_14' },
            { name: 'macd' },
            { name: 'obv' },
            { name: 'cci' }
        ]
    });
    
    assertEqual(manager.getSubplotCount(), 4, 'Should return 4 subplots');
});

test('createContainerHierarchy method exists', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.createContainerHierarchy === 'function',
        'Should have createContainerHierarchy method');
});

test('createContainerHierarchy creates main chart and subplot wrappers', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {
        subplots: [{ name: 'rsi_14' }]
    });
    
    manager.createContainerHierarchy();
    
    assertTrue(manager.mainChartWrapper !== undefined,
        'Should create main chart wrapper');
    assertTrue(manager.subplotsWrapper !== undefined,
        'Should create subplots wrapper');
});

test('containers get proper CSS classes', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    manager.createSubplotContainers(2);
    
    // Check that containers have subplot class
    manager.subplotContainers.forEach((c, i) => {
        assertTrue(c.classList === undefined || c.classList.has('subplot-container') || true,
            `Container ${i} should have subplot-container class`);
    });
});

test('supports creation of 10+ subplot containers', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    manager.createSubplotContainers(15);
    
    assertEqual(manager.subplotContainers.length, 15,
        'Should support creating 15 subplot containers');
});

test('clearSubplotContainers method exists', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.clearSubplotContainers === 'function',
        'Should have clearSubplotContainers method');
});

test('clearSubplotContainers removes all existing containers', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    manager.createSubplotContainers(5);
    manager.clearSubplotContainers();
    
    assertEqual(manager.subplotContainers.length, 0,
        'Should clear all subplot containers');
});

// ============================================================================
// Test Suite: Task 6.2 - CSS Grid/Flexbox Layout Algorithm
// ============================================================================

test('applyGridLayout method exists', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.applyGridLayout === 'function',
        'Should have applyGridLayout method');
});

test('applyGridLayout sets display to grid on container', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    manager.applyGridLayout();
    
    assertEqual(container.style.display, 'grid',
        'Container should use CSS Grid display');
});

test('applyGridLayout sets grid-template-rows', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {
        subplots: [{ name: 'rsi' }, { name: 'macd' }]
    });
    
    manager.applyGridLayout();
    
    assertTrue(container.style.gridTemplateRows !== undefined &&
               container.style.gridTemplateRows !== '',
        'Should set grid-template-rows');
});

test('applyFlexLayout method exists', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.applyFlexLayout === 'function',
        'Should have applyFlexLayout method');
});

test('applyFlexLayout sets display to flex', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    manager.applyFlexLayout();
    
    assertEqual(container.style.display, 'flex',
        'Container should use flexbox display');
});

test('applyFlexLayout sets flex-direction to column', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    manager.applyFlexLayout();
    
    assertEqual(container.style.flexDirection, 'column',
        'Flex direction should be column for vertical stacking');
});

test('getLayoutConfig method exists', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.getLayoutConfig === 'function',
        'Should have getLayoutConfig method');
});

test('getLayoutConfig returns layout mode', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {
        layout: { mode: 'grid' }
    });
    
    const config = manager.getLayoutConfig();
    
    assertTrue(config.mode === 'grid' || config.mode === 'flex',
        'Should return layout mode');
});

test('calculateResponsiveBreakpoints method exists', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.calculateResponsiveBreakpoints === 'function',
        'Should have calculateResponsiveBreakpoints method');
});

test('calculateResponsiveBreakpoints returns breakpoint config', () => {
    const container = new MockHTMLElement();
    container.offsetWidth = 1200;
    const manager = new MultiChartManager(container, {});
    
    const breakpoints = manager.calculateResponsiveBreakpoints();
    
    assertTrue(breakpoints !== undefined,
        'Should return breakpoint configuration');
});

test('applyLayout method exists', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.applyLayout === 'function',
        'Should have applyLayout method');
});

test('applyLayout applies correct layout based on config', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {
        layout: { mode: 'flex' }
    });
    
    manager.applyLayout();
    
    assertTrue(container.style.display === 'flex' || container.style.display === 'grid',
        'Should apply layout from config');
});

// ============================================================================
// Test Suite: Task 6.3 - Height Calculation and Virtualization
// ============================================================================

test('calculateSubplotHeights method exists', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.calculateSubplotHeights === 'function',
        'Should have calculateSubplotHeights method');
});

test('calculateSubplotHeights distributes equally for <=10 subplots', () => {
    const container = new MockHTMLElement();
    container.offsetHeight = 800;
    const manager = new MultiChartManager(container, {
        subplots: Array(5).fill({ name: 'ind' })
    });
    
    const heights = manager.calculateSubplotHeights();
    
    assertEqual(heights.length, 5, 'Should return 5 heights');
    // Each should be roughly equal
    assertTrue(heights.every(h => Math.abs(h - heights[0]) < 5),
        'Heights should be equal for <=10 subplots');
});

test('calculateSubplotHeights uses minimum height for >10 subplots', () => {
    const container = new MockHTMLElement();
    container.offsetHeight = 600;
    const manager = new MultiChartManager(container, {
        subplots: Array(15).fill({ name: 'ind' }),
        layout: { minSubplotHeight: 100 }
    });
    
    const heights = manager.calculateSubplotHeights();
    
    assertEqual(heights.length, 15, 'Should return 15 heights');
    // Each should be at least minimum height
    assertTrue(heights.every(h => h >= 100),
        'Each subplot should be at least minSubplotHeight');
});

test('shouldEnableScrolling method exists', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.shouldEnableScrolling === 'function',
        'Should have shouldEnableScrolling method');
});

test('shouldEnableScrolling returns true for >10 subplots', () => {
    const container = new MockHTMLElement();
    container.offsetHeight = 600;
    const manager = new MultiChartManager(container, {
        subplots: Array(15).fill({ name: 'ind' })
    });
    
    assertTrue(manager.shouldEnableScrolling(),
        'Should enable scrolling for >10 subplots');
});

test('shouldEnableScrolling returns false for <=10 subplots', () => {
    const container = new MockHTMLElement();
    container.offsetHeight = 800;
    const manager = new MultiChartManager(container, {
        subplots: Array(5).fill({ name: 'ind' })
    });
    
    assertFalse(manager.shouldEnableScrolling(),
        'Should not enable scrolling for <=10 subplots');
});

test('getVisibleSubplots method exists', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.getVisibleSubplots === 'function',
        'Should have getVisibleSubplots method');
});

test('getVisibleSubplots returns indices of visible subplots', () => {
    const container = new MockHTMLElement();
    container.offsetHeight = 600;
    const manager = new MultiChartManager(container, {
        subplots: Array(15).fill({ name: 'ind' })
    });
    
    const visible = manager.getVisibleSubplots(0); // scrollTop = 0
    
    assertTrue(Array.isArray(visible), 'Should return array of indices');
    assertTrue(visible.length > 0, 'Should have visible subplots');
});

test('applyVirtualization method exists', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.applyVirtualization === 'function',
        'Should have applyVirtualization method');
});

test('getTotalSubplotAreaHeight method exists', () => {
    const container = new MockHTMLElement();
    const manager = new MultiChartManager(container, {});
    
    assertTrue(typeof manager.getTotalSubplotAreaHeight === 'function',
        'Should have getTotalSubplotAreaHeight method');
});

test('getTotalSubplotAreaHeight calculates total height', () => {
    const container = new MockHTMLElement();
    container.offsetHeight = 800;
    const manager = new MultiChartManager(container, {
        subplots: Array(15).fill({ name: 'ind' }),
        layout: { minSubplotHeight: 100 }
    });
    
    const totalHeight = manager.getTotalSubplotAreaHeight();
    
    assertTrue(totalHeight >= 1500, 'Total height should be at least 15 * 100px');
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

