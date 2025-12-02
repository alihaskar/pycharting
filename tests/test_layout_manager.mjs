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
// Run Tests
// ============================================================================

runTests();

