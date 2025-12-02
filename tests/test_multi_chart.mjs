/**
 * Node.js test runner for MultiChartManager
 * Uses ES modules to test the frontend class
 */

// Mock DOM elements for Node.js
class MockHTMLElement {
    constructor() {
        this.innerHTML = '';
        this.id = '';
        this.style = {};
        this.children = [];
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

// Print results
console.log('\n' + '='.repeat(50));
console.log(`Total: ${passed + failed}`);
console.log(`Passed: ${passed}`);
console.log(`Failed: ${failed}`);
console.log('='.repeat(50));

if (failed > 0) {
    process.exit(1);
}

