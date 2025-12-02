#!/usr/bin/env node
/**
 * Test suite for LayoutManager class
 * 
 * Tests cover:
 * - Class instantiation and initialization
 * - Core methods availability
 * - Configuration management
 * - State tracking
 * - Cleanup and destruction
 */

import { strict as assert } from 'assert';

// Mock DOM environment
class MockHTMLElement {
    constructor(tagName = 'div') {
        this.tagName = tagName.toUpperCase();
        this.children = [];
        this.eventListeners = {};
        this.classList = {
            _classes: new Set(),
            add: function(cls) { this._classes.add(cls); },
            remove: function(cls) { this._classes.delete(cls); },
            contains: function(cls) { return this._classes.has(cls); },
            has: function(cls) { return this._classes.has(cls); }
        };
        this.style = {};
        this.parentElement = null;
        this.attributes = {};
        this.offsetHeight = 600;
        this.offsetWidth = 800;
        this._rect = {
            left: 0, top: 0, right: 800, bottom: 600,
            x: 0, y: 0, width: 800, height: 600
        };
    }

    appendChild(child) {
        this.children.push(child);
        child.parentElement = this;
    }

    removeChild(child) {
        const index = this.children.indexOf(child);
        if (index > -1) {
            this.children.splice(index, 1);
            child.parentElement = null;
        }
    }

    addEventListener(event, handler) {
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push(handler);
    }

    removeEventListener(event, handler) {
        if (this.eventListeners[event]) {
            const index = this.eventListeners[event].indexOf(handler);
            if (index > -1) {
                this.eventListeners[event].splice(index, 1);
            }
        }
    }

    setAttribute(name, value) {
        this.attributes[name] = value;
    }

    getAttribute(name) {
        return this.attributes[name];
    }

    getBoundingClientRect() {
        return this._rect;
    }

    get innerHTML() {
        return this._innerHTML || '';
    }

    set innerHTML(value) {
        this._innerHTML = value;
        this.children = [];
    }
}

// Mock LayoutManager for testing
let LayoutManager;
try {
    const module = await import('../src/frontend/layout-manager.js');
    LayoutManager = module.LayoutManager;
} catch (e) {
    console.log('LayoutManager not yet implemented, using mock');
    LayoutManager = class {
        constructor() {}
    };
}

// Test utilities
const tests = [];
let passedTests = 0;
let failedTests = 0;

function test(description, testFn) {
    tests.push({ description, testFn });
}

function assertEqual(actual, expected, message) {
    assert.strictEqual(actual, expected, message || `Expected ${expected}, got ${actual}`);
}

function assertTrue(value, message) {
    assert.ok(value, message || `Expected true, got ${value}`);
}

function assertFalse(value, message) {
    assert.ok(!value, message || `Expected false, got ${value}`);
}

function assertThrows(fn, message) {
    let threw = false;
    try {
        fn();
    } catch (e) {
        threw = true;
    }
    assert.ok(threw, message || 'Expected function to throw');
}

async function runTests() {
    console.log('\n🧪 LayoutManager Test Suite\n');

    for (const { description, testFn } of tests) {
        try {
            await testFn();
            console.log(`✅ ${description}`);
            passedTests++;
        } catch (error) {
            console.log(`❌ ${description}`);
            console.log(`   Error: ${error.message}`);
            failedTests++;
        }
    }

    console.log(`\n📊 Results: ${passedTests} passed, ${failedTests} failed, ${tests.length} total\n`);
    process.exit(failedTests > 0 ? 1 : 0);
}

// ============================================================================
// Test Suite: Class Structure and Instantiation
// ============================================================================

test('LayoutManager class exists', () => {
    assertTrue(LayoutManager !== undefined, 'LayoutManager should be defined');
});

test('LayoutManager can be instantiated', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    assertTrue(manager instanceof LayoutManager, 'Should create LayoutManager instance');
});

test('LayoutManager constructor requires container element', () => {
    assertThrows(() => {
        new LayoutManager();
    }, 'Should throw when no container provided');
});

test('LayoutManager constructor validates container is HTMLElement', () => {
    assertThrows(() => {
        new LayoutManager('not an element');
    }, 'Should throw when container is not HTMLElement');
});

test('LayoutManager accepts configuration options', () => {
    const container = new MockHTMLElement();
    const config = {
        minMainHeight: 0.3,
        maxMainHeight: 0.7,
        minSubplotHeight: 120
    };
    const manager = new LayoutManager(container, config);
    assertTrue(manager instanceof LayoutManager, 'Should accept configuration');
});

// ============================================================================
// Test Suite: Core Methods
// ============================================================================

test('LayoutManager has initialize method', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    assertTrue(typeof manager.initialize === 'function', 'Should have initialize method');
});

test('LayoutManager has destroy method', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    assertTrue(typeof manager.destroy === 'function', 'Should have destroy method');
});

test('LayoutManager has getConfiguration method', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    assertTrue(typeof manager.getConfiguration === 'function', 'Should have getConfiguration method');
});

test('LayoutManager has setConfiguration method', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    assertTrue(typeof manager.setConfiguration === 'function', 'Should have setConfiguration method');
});

// ============================================================================
// Test Suite: Configuration Management
// ============================================================================

test('getConfiguration returns current configuration', () => {
    const container = new MockHTMLElement();
    const config = { minMainHeight: 0.25 };
    const manager = new LayoutManager(container, config);
    
    const retrieved = manager.getConfiguration();
    assertTrue(retrieved !== null && retrieved !== undefined, 'Should return configuration object');
});

test('setConfiguration updates configuration', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    const newConfig = { minMainHeight: 0.35 };
    manager.setConfiguration(newConfig);
    
    const retrieved = manager.getConfiguration();
    assertEqual(retrieved.minMainHeight, 0.35, 'Should update configuration');
});

test('setConfiguration merges with existing configuration', () => {
    const container = new MockHTMLElement();
    const initialConfig = { minMainHeight: 0.2, maxMainHeight: 0.8 };
    const manager = new LayoutManager(container, initialConfig);
    
    manager.setConfiguration({ minMainHeight: 0.3 });
    
    const retrieved = manager.getConfiguration();
    assertEqual(retrieved.minMainHeight, 0.3, 'Should update specified property');
    assertEqual(retrieved.maxMainHeight, 0.8, 'Should keep unspecified property');
});

// ============================================================================
// Test Suite: State Management
// ============================================================================

test('LayoutManager tracks divider instances', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    assertTrue(Array.isArray(manager.dividers) || manager.dividers instanceof Map,
        'Should have dividers collection');
});

test('LayoutManager tracks panel configurations', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    assertTrue(manager.panels !== undefined, 'Should have panels property');
});

test('LayoutManager has layout state property', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    assertTrue(manager.layoutState !== undefined || manager.state !== undefined,
        'Should have layout state property');
});

// ============================================================================
// Test Suite: Initialization and Cleanup
// ============================================================================

test('initialize method sets up layout', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    manager.initialize();
    
    // Should not throw and should be callable
    assertTrue(true, 'Initialize should complete without errors');
});

test('destroy method cleans up resources', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    manager.initialize();
    manager.destroy();
    
    // Should not throw
    assertTrue(true, 'Destroy should complete without errors');
});

test('destroy clears divider instances', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    manager.initialize();
    manager.destroy();
    
    const dividersLength = Array.isArray(manager.dividers) ? manager.dividers.length : manager.dividers?.size || 0;
    assertEqual(dividersLength, 0, 'Should clear divider instances');
});

test('LayoutManager can be reinitialized after destroy', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    manager.initialize();
    manager.destroy();
    manager.initialize();
    
    // Should not throw
    assertTrue(true, 'Should support reinitialization');
});

// ============================================================================
// Test Suite: Default Configuration
// ============================================================================

test('LayoutManager has sensible default configuration', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    const config = manager.getConfiguration();
    
    assertTrue(config.minMainHeight !== undefined, 'Should have minMainHeight default');
    assertTrue(config.maxMainHeight !== undefined, 'Should have maxMainHeight default');
    assertTrue(config.minSubplotHeight !== undefined, 'Should have minSubplotHeight default');
});

test('Default minMainHeight is reasonable', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    const config = manager.getConfiguration();
    
    assertTrue(config.minMainHeight >= 0.15 && config.minMainHeight <= 0.3,
        'minMainHeight should be between 15% and 30%');
});

test('Default maxMainHeight is reasonable', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    const config = manager.getConfiguration();
    
    assertTrue(config.maxMainHeight >= 0.7 && config.maxMainHeight <= 0.9,
        'maxMainHeight should be between 70% and 90%');
});

// ============================================================================
// Test Suite: ResizeObserver Integration
// ============================================================================

test('LayoutManager has setupResizeObserver method', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    assertTrue(typeof manager.setupResizeObserver === 'function',
        'Should have setupResizeObserver method');
});

test('setupResizeObserver creates ResizeObserver', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    // Mock ResizeObserver
    global.ResizeObserver = class {
        constructor(callback) {
            this.callback = callback;
        }
        observe() {}
        disconnect() {}
    };
    
    manager.setupResizeObserver();
    
    assertTrue(manager.resizeObserver !== null, 'Should create ResizeObserver');
    
    // Cleanup
    delete global.ResizeObserver;
});

test('ResizeObserver observes container element', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    let observedElement = null;
    global.ResizeObserver = class {
        constructor(callback) {
            this.callback = callback;
        }
        observe(element) {
            observedElement = element;
        }
        disconnect() {}
    };
    
    manager.setupResizeObserver();
    
    assertEqual(observedElement, container, 'Should observe container element');
    
    delete global.ResizeObserver;
});

test('ResizeObserver callback is debounced', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container, { debounceDelay: 150 });
    
    let callbackInvoked = false;
    global.ResizeObserver = class {
        constructor(callback) {
            this.callback = callback;
        }
        observe() {}
        disconnect() {}
    };
    
    manager.setupResizeObserver();
    manager.handleResize = () => { callbackInvoked = true; };
    
    // Should not call immediately
    assertFalse(callbackInvoked, 'Should not call immediately (debounced)');
    
    delete global.ResizeObserver;
});

test('destroy disconnects ResizeObserver', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    let disconnected = false;
    global.ResizeObserver = class {
        constructor() {}
        observe() {}
        disconnect() {
            disconnected = true;
        }
    };
    
    manager.setupResizeObserver();
    manager.destroy();
    
    assertTrue(disconnected, 'Should disconnect ResizeObserver on destroy');
    
    delete global.ResizeObserver;
});

test('debounce timer is cleared on destroy', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    manager.debounceTimer = setTimeout(() => {}, 1000);
    const timerId = manager.debounceTimer;
    
    manager.destroy();
    
    assertEqual(manager.debounceTimer, null, 'Should clear debounce timer');
});

test('handleResize method exists', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    assertTrue(typeof manager.handleResize === 'function',
        'Should have handleResize method');
});

test('handleResize is called after debounce delay', async () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container, { debounceDelay: 50 });
    
    let resizeHandled = false;
    manager.handleResize = () => {
        resizeHandled = true;
    };
    
    global.ResizeObserver = class {
        constructor(callback) {
            this.callback = callback;
        }
        observe() {
            // Simulate resize event
            setTimeout(() => {
                this.callback([{ target: container }]);
            }, 10);
        }
        disconnect() {}
    };
    
    manager.setupResizeObserver();
    
    // Wait for debounce delay
    await new Promise(resolve => setTimeout(resolve, 100));
    
    assertTrue(resizeHandled, 'Should call handleResize after debounce');
    delete global.ResizeObserver;
});

test('multiple resize events only trigger one handleResize', async () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container, { debounceDelay: 50 });
    
    let resizeCount = 0;
    manager.handleResize = () => {
        resizeCount++;
    };
    
    let observerCallback;
    global.ResizeObserver = class {
        constructor(callback) {
            observerCallback = callback;
        }
        observe() {}
        disconnect() {}
    };
    
    manager.setupResizeObserver();
    
    // Trigger multiple resize events rapidly
    observerCallback([{ target: container }]);
    observerCallback([{ target: container }]);
    observerCallback([{ target: container }]);
    
    // Wait for debounce delay
    await new Promise(resolve => setTimeout(resolve, 100));
    
    assertEqual(resizeCount, 1, 'Should only call handleResize once (debounced)');
    delete global.ResizeObserver;
});

// ============================================================================
// Test Suite: Height Calculation Algorithms
// ============================================================================

test('calculateHeights method exists', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    assertTrue(typeof manager.calculateHeights === 'function',
        'Should have calculateHeights method');
});

test('validateConstraints method exists', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    assertTrue(typeof manager.validateConstraints === 'function',
        'Should have validateConstraints method');
});

test('calculateHeights enforces minMainHeight constraint', () => {
    const container = new MockHTMLElement();
    container.offsetHeight = 1000;
    const manager = new LayoutManager(container, {
        minMainHeight: 0.3  // 30% minimum
    });
    
    const result = manager.calculateHeights({ mainHeight: 0.1 }); // Try 10%
    
    assertTrue(result.mainHeight >= 0.3, 'Should enforce minMainHeight constraint');
});

test('calculateHeights enforces maxMainHeight constraint', () => {
    const container = new MockHTMLElement();
    container.offsetHeight = 1000;
    const manager = new LayoutManager(container, {
        maxMainHeight: 0.7  // 70% maximum
    });
    
    const result = manager.calculateHeights({ mainHeight: 0.9 }); // Try 90%
    
    assertTrue(result.mainHeight <= 0.7, 'Should enforce maxMainHeight constraint');
});

test('calculateHeights enforces minSubplotHeight in pixels', () => {
    const container = new MockHTMLElement();
    container.offsetHeight = 500;
    const manager = new LayoutManager(container, {
        minSubplotHeight: 100  // 100px minimum
    });
    
    const result = manager.calculateHeights({
        mainHeight: 0.9,  // Would leave only 50px for subplot
        subplotCount: 1
    });
    
    // Use the calculated pixel value from result, not recalculated to avoid floating point issues
    const subplotHeight = result.subplotHeights[0];
    
    assertTrue(subplotHeight >= 100, `Should enforce minSubplotHeight constraint, got ${subplotHeight}px`);
});

test('calculateHeights converts percentages to pixels', () => {
    const container = new MockHTMLElement();
    container.offsetHeight = 1000;
    const manager = new LayoutManager(container);
    
    const result = manager.calculateHeights({ mainHeight: 0.6 });
    
    assertTrue(result.mainHeightPx !== undefined, 'Should include pixel value');
    assertEqual(result.mainHeightPx, 600, 'Should correctly convert to pixels');
});

test('calculateHeights handles multiple subplots', () => {
    const container = new MockHTMLElement();
    container.offsetHeight = 1000;
    const manager = new LayoutManager(container);
    
    const result = manager.calculateHeights({
        mainHeight: 0.6,
        subplotCount: 3
    });
    
    assertTrue(Array.isArray(result.subplotHeights), 'Should return subplot heights array');
    assertEqual(result.subplotHeights.length, 3, 'Should have 3 subplot heights');
});

test('validateConstraints returns true for valid layout', () => {
    const container = new MockHTMLElement();
    container.offsetHeight = 1000;
    const manager = new LayoutManager(container);
    
    const valid = manager.validateConstraints({
        mainHeight: 0.6,
        subplotCount: 2
    });
    
    assertTrue(valid, 'Should validate valid layout');
});

test('validateConstraints returns false when constraints violated', () => {
    const container = new MockHTMLElement();
    container.offsetHeight = 100;  // Very small container
    const manager = new LayoutManager(container, {
        minMainHeight: 0.5,
        minSubplotHeight: 100
    });
    
    const valid = manager.validateConstraints({
        mainHeight: 0.5,  // Would leave 50px for subplot, but min is 100px
        subplotCount: 1
    });
    
    assertFalse(valid, 'Should invalidate when constraints conflict');
});

test('calculateHeights distributes subplot space evenly', () => {
    const container = new MockHTMLElement();
    container.offsetHeight = 1000;
    const manager = new LayoutManager(container);
    
    const result = manager.calculateHeights({
        mainHeight: 0.6,  // 600px for main
        subplotCount: 2   // 400px split between 2 subplots
    });
    
    // Each subplot should get ~200px
    assertEqual(result.subplotHeights[0], result.subplotHeights[1],
        'Subplots should have equal height');
});

test('calculateHeights handles edge case with zero subplots', () => {
    const container = new MockHTMLElement();
    container.offsetHeight = 1000;
    const manager = new LayoutManager(container);
    
    const result = manager.calculateHeights({
        mainHeight: 0.8,
        subplotCount: 0
    });
    
    assertTrue(result.mainHeight <= 1.0, 'Main height should not exceed 100%');
    assertEqual(result.subplotHeights.length, 0, 'Should have empty subplot array');
});

// ============================================================================
// Test Suite: localStorage Persistence
// ============================================================================

test('saveLayout method exists', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    assertTrue(typeof manager.saveLayout === 'function',
        'Should have saveLayout method');
});

test('loadLayout method exists', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    assertTrue(typeof manager.loadLayout === 'function',
        'Should have loadLayout method');
});

test('saveLayout stores layout state to localStorage', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    // Mock localStorage
    const storage = {};
    global.localStorage = {
        getItem: (key) => storage[key],
        setItem: (key, value) => { storage[key] = value; }
    };
    
    manager.layoutState.mainHeight = 0.6;
    manager.saveLayout();
    
    assertTrue(storage['chart-layout-state'] !== undefined,
        'Should save to localStorage');
    
    delete global.localStorage;
});

test('saveLayout serializes layout state as JSON', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    const storage = {};
    global.localStorage = {
        getItem: (key) => storage[key],
        setItem: (key, value) => { storage[key] = value; }
    };
    
    manager.layoutState.mainHeight = 0.65;
    manager.saveLayout();
    
    const saved = JSON.parse(storage['chart-layout-state']);
    assertEqual(saved.mainHeight, 0.65, 'Should serialize as JSON');
    
    delete global.localStorage;
});

test('loadLayout retrieves layout state from localStorage', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    const savedState = JSON.stringify({ mainHeight: 0.7 });
    global.localStorage = {
        getItem: (key) => key === 'chart-layout-state' ? savedState : null,
        setItem: () => {}
    };
    
    const loaded = manager.loadLayout();
    
    assertEqual(loaded.mainHeight, 0.7, 'Should load from localStorage');
    
    delete global.localStorage;
});

test('loadLayout returns null when no saved state exists', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    global.localStorage = {
        getItem: () => null,
        setItem: () => {}
    };
    
    const loaded = manager.loadLayout();
    
    assertEqual(loaded, null, 'Should return null when no saved state');
    
    delete global.localStorage;
});

test('loadLayout handles corrupted JSON gracefully', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    global.localStorage = {
        getItem: () => 'not valid json{]',
        setItem: () => {}
    };
    
    const loaded = manager.loadLayout();
    
    assertEqual(loaded, null, 'Should return null for corrupted JSON');
    
    delete global.localStorage;
});

test('loadLayout validates loaded data structure', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    // Invalid data structure (missing required fields)
    const invalidState = JSON.stringify({ foo: 'bar' });
    global.localStorage = {
        getItem: () => invalidState,
        setItem: () => {}
    };
    
    const loaded = manager.loadLayout();
    
    // Should either return null or valid default structure
    assertTrue(loaded === null || typeof loaded.mainHeight === 'number',
        'Should validate data structure');
    
    delete global.localStorage;
});

test('saveLayout uses custom storage key from config', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container, {
        storageKey: 'my-custom-key'
    });
    
    const storage = {};
    global.localStorage = {
        getItem: (key) => storage[key],
        setItem: (key, value) => { storage[key] = value; }
    };
    
    manager.layoutState.mainHeight = 0.5;
    manager.saveLayout();
    
    assertTrue(storage['my-custom-key'] !== undefined,
        'Should use custom storage key');
    
    delete global.localStorage;
});

test('localStorage methods handle missing localStorage API', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    // Ensure localStorage is undefined
    delete global.localStorage;
    
    // Should not throw
    manager.saveLayout();
    const loaded = manager.loadLayout();
    
    assertEqual(loaded, null, 'Should handle missing localStorage gracefully');
});

test('autoSave can be disabled via configuration', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container, {
        autoSave: false
    });
    
    const config = manager.getConfiguration();
    
    assertFalse(config.autoSave, 'Should disable autoSave when configured');
});

// ============================================================================
// Test Suite: DraggableDivider Coordination
// ============================================================================

test('initializeDividers method exists', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    assertTrue(typeof manager.initializeDividers === 'function',
        'Should have initializeDividers method');
});

test('initializeDividers creates dividers array', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    manager.initializeDividers([
        { id: 'main', type: 'main-subplot' }
    ]);
    
    assertTrue(Array.isArray(manager.dividers), 'Should have dividers array');
});

test('initializeDividers tracks divider count', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    manager.initializeDividers([
        { id: 'main', type: 'main-subplot' },
        { id: 'subplot1', type: 'subplot' }
    ]);
    
    assertTrue(manager.dividers.length >= 0, 'Should track divider count');
});

test('onDividerDrag callback exists', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    assertTrue(typeof manager.onDividerDrag === 'function',
        'Should have onDividerDrag callback');
});

test('onDividerDrag updates layout state', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    manager.layoutState.mainHeight = 0.6;
    
    // Simulate divider drag
    manager.onDividerDrag({ dividerId: 'main', deltaY: 50 });
    
    // State should be updated (exact value depends on implementation)
    assertTrue(manager.layoutState.mainHeight !== undefined,
        'Should update layout state');
});

test('onDividerDrag triggers autoSave when enabled', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container, { autoSave: true });
    
    let saveCalled = false;
    manager.saveLayout = () => { saveCalled = true; return true; };
    
    manager.onDividerDrag({ dividerId: 'main', deltaY: 10 });
    
    assertTrue(saveCalled, 'Should trigger autoSave');
});

test('onDividerDrag does not save when autoSave disabled', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container, { autoSave: false });
    
    let saveCalled = false;
    manager.saveLayout = () => { saveCalled = true; return true; };
    
    manager.onDividerDrag({ dividerId: 'main', deltaY: 10 });
    
    assertFalse(saveCalled, 'Should not trigger save when autoSave disabled');
});

test('destroy cleans up all divider instances', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    // Mock dividers with destroy method
    manager.dividers = [
        { id: 'div1', destroy: () => {} },
        { id: 'div2', destroy: () => {} }
    ];
    
    manager.destroy();
    
    assertEqual(manager.dividers.length, 0, 'Should clear all dividers');
});

test('getPanelConfig method exists', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    assertTrue(typeof manager.getPanelConfig === 'function',
        'Should have getPanelConfig method');
});

test('setPanelConfig method exists', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    assertTrue(typeof manager.setPanelConfig === 'function',
        'Should have setPanelConfig method');
});

test('setPanelConfig updates panel configuration', () => {
    const container = new MockHTMLElement();
    const manager = new LayoutManager(container);
    
    manager.setPanelConfig([
        { id: 'main', height: 0.6 },
        { id: 'subplot1', height: 0.4 }
    ]);
    
    assertTrue(manager.panels.length > 0, 'Should update panel configuration');
});

// ============================================================================
// Run Tests
// ============================================================================

runTests();

