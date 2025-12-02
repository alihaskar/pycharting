/**
 * Tests for DraggableDivider component
 * 
 * Tests cover:
 * - Event handler setup (mouse & touch)
 * - Coordinate extraction
 * - Drag state management
 * - Event cleanup
 */

import { strict as assert } from 'assert';

// Mock DOM elements
class MockHTMLElement {
    constructor(tagName = 'div') {
        this.tagName = tagName;
        this.style = {};
        this.classList = new Set();
        this.children = [];
        this.parentElement = null;
        this.eventListeners = {};
        this._innerHTML = '';
        this.dataset = {};
    }

    get innerHTML() {
        return this._innerHTML;
    }

    set innerHTML(value) {
        this._innerHTML = value;
        // Clear children when innerHTML is set
        this.children = [];
    }

    appendChild(child) {
        this.children.push(child);
        child.parentElement = this;
        return child;
    }

    addEventListener(event, handler, options) {
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push({ handler, options });
    }

    removeEventListener(event, handler) {
        if (this.eventListeners[event]) {
            this.eventListeners[event] = this.eventListeners[event].filter(
                listener => listener.handler !== handler
            );
        }
    }

    getBoundingClientRect() {
        return {
            top: 0,
            left: 0,
            right: 100,
            bottom: 100,
            width: 100,
            height: 100
        };
    }

    setAttribute(name, value) {
        this[name] = value;
    }

    getAttribute(name) {
        return this[name];
    }

    removeChild(child) {
        const index = this.children.indexOf(child);
        if (index > -1) {
            this.children.splice(index, 1);
            child.parentElement = null;
        }
        return child;
    }
}

// Mock document with event listeners
global.document = {
    createElement: (tag) => new MockHTMLElement(tag),
    body: new MockHTMLElement('body'),
    eventListeners: {},
    addEventListener: function(event, handler, options) {
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push({ handler, options });
    },
    removeEventListener: function(event, handler) {
        if (this.eventListeners[event]) {
            this.eventListeners[event] = this.eventListeners[event].filter(
                listener => listener.handler !== handler
            );
        }
    }
};

// Mock window
global.window = {
    addEventListener: () => {},
    removeEventListener: () => {}
};

// Import the module (will be created next)
let DraggableDivider;
try {
    const module = await import('../src/frontend/divider.js');
    DraggableDivider = module.DraggableDivider;
} catch (e) {
    console.log('DraggableDivider not yet implemented, expected in TDD RED phase');
}

// Test runner
const tests = [];
function test(name, fn) {
    tests.push({ name, fn });
}

function assertTrue(condition, message) {
    assert.ok(condition, message);
}

function assertFalse(condition, message) {
    assert.ok(!condition, message);
}

function assertEqual(actual, expected, message) {
    assert.strictEqual(actual, expected, message);
}

function assertNotEqual(actual, expected, message) {
    assert.notStrictEqual(actual, expected, message);
}

function assertThrows(fn, message) {
    assert.throws(fn, message);
}

// ============================================================================
// Test Suite: DraggableDivider Class Structure
// ============================================================================

test('DraggableDivider class exists', () => {
    assertTrue(typeof DraggableDivider === 'function', 'DraggableDivider should be a class/function');
});

test('DraggableDivider constructor accepts container and options', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container, { minSize: 50 });
    
    assertTrue(divider !== null, 'Should create instance');
    assertTrue(divider.container === container, 'Should store container reference');
});

test('DraggableDivider has required methods', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    assertTrue(typeof divider.handleMouseDown === 'function', 'Should have handleMouseDown method');
    assertTrue(typeof divider.handleMouseMove === 'function', 'Should have handleMouseMove method');
    assertTrue(typeof divider.handleMouseUp === 'function', 'Should have handleMouseUp method');
    assertTrue(typeof divider.handleTouchStart === 'function', 'Should have handleTouchStart method');
    assertTrue(typeof divider.handleTouchMove === 'function', 'Should have handleTouchMove method');
    assertTrue(typeof divider.handleTouchEnd === 'function', 'Should have handleTouchEnd method');
});

// ============================================================================
// Test Suite: Event Handler Setup
// ============================================================================

test('Constructor sets up mouse event listeners', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    const dividerElement = divider.element;
    assertTrue(dividerElement.eventListeners['mousedown'], 'Should have mousedown listener');
    assertTrue(dividerElement.eventListeners['mousedown'].length > 0, 'Should have at least one mousedown handler');
});

test('Constructor sets up touch event listeners', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    const dividerElement = divider.element;
    assertTrue(dividerElement.eventListeners['touchstart'], 'Should have touchstart listener');
    assertTrue(dividerElement.eventListeners['touchstart'].length > 0, 'Should have at least one touchstart handler');
});

test('Mouse down sets dragging state to true', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    assertFalse(divider.isDragging, 'Should not be dragging initially');
    
    divider.handleMouseDown({ clientY: 100, preventDefault: () => {} });
    
    assertTrue(divider.isDragging, 'Should be dragging after mousedown');
});

test('Touch start sets dragging state to true', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    assertFalse(divider.isDragging, 'Should not be dragging initially');
    
    divider.handleTouchStart({
        touches: [{ clientY: 100 }],
        preventDefault: () => {}
    });
    
    assertTrue(divider.isDragging, 'Should be dragging after touchstart');
});

// ============================================================================
// Test Suite: Coordinate Extraction
// ============================================================================

test('Extracts Y coordinate from mouse event', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    const mockEvent = { clientY: 150 };
    const y = divider.getEventY(mockEvent);
    
    assertEqual(y, 150, 'Should extract clientY from mouse event');
});

test('Extracts Y coordinate from touch event', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    const mockEvent = { touches: [{ clientY: 200 }] };
    const y = divider.getEventY(mockEvent);
    
    assertEqual(y, 200, 'Should extract clientY from first touch');
});

test('Handles touch event with no touches', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    const mockEvent = { touches: [] };
    const y = divider.getEventY(mockEvent);
    
    assertEqual(y, 0, 'Should return 0 when no touches');
});

// ============================================================================
// Test Suite: Drag State Management
// ============================================================================

test('Stores initial Y position on drag start', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    divider.handleMouseDown({ clientY: 100, preventDefault: () => {} });
    
    assertEqual(divider.startY, 100, 'Should store initial Y position');
});

test('Mouse up resets dragging state', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    divider.handleMouseDown({ clientY: 100, preventDefault: () => {} });
    assertTrue(divider.isDragging, 'Should be dragging');
    
    divider.handleMouseUp();
    assertFalse(divider.isDragging, 'Should not be dragging after mouseup');
});

test('Touch end resets dragging state', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    divider.handleTouchStart({
        touches: [{ clientY: 100 }],
        preventDefault: () => {}
    });
    assertTrue(divider.isDragging, 'Should be dragging');
    
    divider.handleTouchEnd();
    assertFalse(divider.isDragging, 'Should not be dragging after touchend');
});

test('Prevents default on drag start', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    let preventDefaultCalled = false;
    const mockEvent = {
        clientY: 100,
        preventDefault: () => { preventDefaultCalled = true; }
    };
    
    divider.handleMouseDown(mockEvent);
    assertTrue(preventDefaultCalled, 'Should call preventDefault');
});

// ============================================================================
// Test Suite: Event Cleanup
// ============================================================================

test('Destroy method removes event listeners', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    const dividerElement = divider.element;
    const initialMouseDownCount = dividerElement.eventListeners['mousedown']?.length || 0;
    
    divider.destroy();
    
    const finalMouseDownCount = dividerElement.eventListeners['mousedown']?.length || 0;
    assertTrue(finalMouseDownCount < initialMouseDownCount, 'Should remove event listeners');
});

test('Destroy method removes element from container', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    const initialChildCount = container.children.length;
    assertTrue(initialChildCount > 0, 'Should have divider element in container');
    
    divider.destroy();
    
    // Element should be marked for removal or container reference cleared
    assertTrue(divider.element === null || divider.container === null, 'Should cleanup references');
});

// ============================================================================
// Run Tests
// ============================================================================

console.log('\n🧪 Running DraggableDivider Tests...\n');

let passed = 0;
let failed = 0;

for (const { name, fn } of tests) {
    try {
        fn();
        console.log(`✅ ${name}`);
        passed++;
    } catch (error) {
        console.log(`❌ ${name}`);
        console.log(`   Error: ${error.message}`);
        failed++;
    }
}

console.log(`\n📊 Results: ${passed} passed, ${failed} failed, ${tests.length} total\n`);

if (failed > 0) {
    process.exit(1);
}

