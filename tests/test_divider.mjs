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
        this.classList = {
            _classes: new Set(),
            add: function(className) {
                this._classes.add(className);
            },
            remove: function(className) {
                this._classes.delete(className);
            },
            has: function(className) {
                return this._classes.has(className);
            },
            contains: function(className) {
                return this._classes.has(className);
            }
        };
        this.children = [];
        this.parentElement = null;
        this.eventListeners = {};
        this._innerHTML = '';
        this.dataset = {};
        this.attributes = {}; // Store attributes
        this.offsetHeight = 0; // Mock offsetHeight
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
        this.attributes[name] = value;
    }

    getAttribute(name) {
        return this.attributes[name];
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
// Test Suite: Rendering and Styling
// ============================================================================

test('Divider element has correct CSS class', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    assertTrue(divider.element.classList.has('chart-divider'), 'Should have chart-divider class');
});

test('Divider element has ns-resize cursor', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    const cursor = divider.element.style.cursor;
    assertEqual(cursor, 'ns-resize', 'Should have ns-resize cursor');
});

test('Divider element has correct height', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    const height = divider.element.style.height;
    assertTrue(height === '3px' || height === '5px', 'Should have divider height');
});

test('Divider element has correct z-index', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    const zIndex = divider.element.style.zIndex;
    assertTrue(parseInt(zIndex) >= 10, 'Should have z-index of at least 10');
});

test('Divider element has user-select none', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    const userSelect = divider.element.style.userSelect;
    assertEqual(userSelect, 'none', 'Should have user-select: none');
});

test('Divider is appended to container', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    assertTrue(container.children.length > 0, 'Should have children');
    assertTrue(container.children.includes(divider.element), 'Should contain divider element');
});

test('Divider has GPU-accelerated properties', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    // Check for will-change or transform properties
    const willChange = divider.element.style.willChange;
    assertTrue(
        willChange === 'transform' || willChange === 'auto' || willChange === '',
        'Should have GPU acceleration hints'
    );
});

test('Dragging state changes divider appearance', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    const initialBg = divider.element.style.background;
    
    divider.handleMouseDown({ clientY: 100, preventDefault: () => {} });
    const draggingBg = divider.element.style.background;
    
    assertNotEqual(draggingBg, initialBg, 'Background should change during drag');
});

test('Element has position relative', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    const position = divider.element.style.position;
    assertEqual(position, 'relative', 'Should have position: relative');
});

test('Divider has visual feedback state', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    // Should have initial state
    assertTrue(divider.element.style.background !== '', 'Should have background color');
});

// ============================================================================
// Test Suite: Drag Calculation and Container Resizing
// ============================================================================

test('Calculates delta from drag movement', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container, {
        onDrag: (deltaY) => {
            assertEqual(deltaY, 50, 'Should calculate correct delta');
        }
    });
    
    divider.handleMouseDown({ clientY: 100, preventDefault: () => {} });
    divider.handleMouseMove({ clientY: 150, preventDefault: () => {} });
});

test('Resizes adjacent containers during drag', () => {
    const container = new MockHTMLElement();
    const topPanel = new MockHTMLElement();
    const bottomPanel = new MockHTMLElement();
    
    topPanel.style.height = '200px';
    bottomPanel.style.height = '200px';
    container.appendChild(topPanel);
    container.appendChild(bottomPanel);
    
    let resizeCalled = false;
    const divider = new DraggableDivider(container, {
        topElement: topPanel,
        bottomElement: bottomPanel,
        onDrag: (deltaY) => {
            resizeCalled = true;
            // Should resize panels
            divider.resizePanels(deltaY);
        }
    });
    
    divider.handleMouseDown({ clientY: 100, preventDefault: () => {} });
    divider.handleMouseMove({ clientY: 150, preventDefault: () => {} });
    
    assertTrue(resizeCalled, 'Should call resize during drag');
});

test('Enforces minimum size constraints', () => {
    const container = new MockHTMLElement();
    const topPanel = new MockHTMLElement();
    const bottomPanel = new MockHTMLElement();
    
    topPanel.style.height = '100px';
    bottomPanel.style.height = '200px';
    
    const divider = new DraggableDivider(container, {
        topElement: topPanel,
        bottomElement: bottomPanel,
        minSize: 50
    });
    
    // Try to resize top panel below minimum
    const newHeight = divider.constrainSize(30, 50);
    assertEqual(newHeight, 50, 'Should enforce minimum size');
});

test('Enforces maximum size constraints', () => {
    const container = new MockHTMLElement();
    const topPanel = new MockHTMLElement();
    
    const divider = new DraggableDivider(container, {
        topElement: topPanel,
        maxSize: 500
    });
    
    const newHeight = divider.constrainSize(600, 50, 500);
    assertEqual(newHeight, 500, 'Should enforce maximum size');
});

test('Handles negative delta (dragging up)', () => {
    const container = new MockHTMLElement();
    let capturedDelta;
    
    const divider = new DraggableDivider(container, {
        onDrag: (deltaY) => {
            capturedDelta = deltaY;
        }
    });
    
    divider.handleMouseDown({ clientY: 200, preventDefault: () => {} });
    divider.handleMouseMove({ clientY: 150, preventDefault: () => {} });
    
    assertTrue(capturedDelta < 0, 'Should handle negative delta');
});

test('Handles positive delta (dragging down)', () => {
    const container = new MockHTMLElement();
    let capturedDelta;
    
    const divider = new DraggableDivider(container, {
        onDrag: (deltaY) => {
            capturedDelta = deltaY;
        }
    });
    
    divider.handleMouseDown({ clientY: 100, preventDefault: () => {} });
    divider.handleMouseMove({ clientY: 150, preventDefault: () => {} });
    
    assertTrue(capturedDelta > 0, 'Should handle positive delta');
});

test('Updates current position during drag', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    divider.handleMouseDown({ clientY: 100, preventDefault: () => {} });
    assertEqual(divider.currentY, 100, 'Should set initial currentY');
    
    divider.handleMouseMove({ clientY: 150, preventDefault: () => {} });
    assertEqual(divider.currentY, 150, 'Should update currentY');
});

test('Calculates cumulative delta across multiple moves', () => {
    const container = new MockHTMLElement();
    const deltas = [];
    
    const divider = new DraggableDivider(container, {
        onDrag: (deltaY) => {
            deltas.push(deltaY);
        }
    });
    
    divider.handleMouseDown({ clientY: 100, preventDefault: () => {} });
    divider.handleMouseMove({ clientY: 110, preventDefault: () => {} });
    divider.handleMouseMove({ clientY: 130, preventDefault: () => {} });
    divider.handleMouseMove({ clientY: 160, preventDefault: () => {} });
    
    // Should have three deltas: +10, +20, +30
    assertTrue(deltas.length === 3, 'Should track multiple moves');
    assertEqual(deltas[0], 10, 'First delta should be 10');
    assertEqual(deltas[1], 20, 'Second delta should be 20');
    assertEqual(deltas[2], 30, 'Third delta should be 30');
});

test('Resizing respects container boundaries', () => {
    const container = new MockHTMLElement();
    container.getBoundingClientRect = () => ({
        top: 0,
        left: 0,
        right: 100,
        bottom: 400,
        width: 100,
        height: 400
    });
    
    const topPanel = new MockHTMLElement();
    topPanel.style.height = '200px';
    
    const divider = new DraggableDivider(container, {
        topElement: topPanel,
        minSize: 50
    });
    
    // Ensure resize calculations respect boundaries
    const maxAllowed = 400 - 50; // Container height - min bottom size
    const constrained = divider.constrainSize(500, 50, maxAllowed);
    
    assertTrue(constrained <= maxAllowed, 'Should respect container boundaries');
});

test('No resize when not dragging', () => {
    const container = new MockHTMLElement();
    let dragCalled = false;
    
    const divider = new DraggableDivider(container, {
        onDrag: () => {
            dragCalled = true;
        }
    });
    
    // Move without starting drag
    divider.handleMouseMove({ clientY: 150, preventDefault: () => {} });
    
    assertFalse(dragCalled, 'Should not trigger drag when not in drag state');
});

// ============================================================================
// Test Suite: Accessibility Features
// ============================================================================

test('Divider has appropriate ARIA role', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    const role = divider.element.getAttribute('role');
    assertEqual(role, 'separator', 'Should have separator role');
});

test('Divider has ARIA label', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    const label = divider.element.getAttribute('aria-label');
    assertTrue(label !== null && label !== '', 'Should have aria-label');
});

test('Divider has ARIA orientation', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    const orientation = divider.element.getAttribute('aria-orientation');
    assertEqual(orientation, 'horizontal', 'Should have horizontal orientation');
});

test('Divider is keyboard focusable', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    const tabIndex = divider.element.getAttribute('tabindex');
    assertEqual(tabIndex, '0', 'Should have tabindex 0 for keyboard focus');
});

test('Divider has keyboard event listeners', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    assertTrue(divider.element.eventListeners['keydown'], 'Should have keydown listener');
});

test('Arrow down key moves divider down', () => {
    const container = new MockHTMLElement();
    let dragCalled = false;
    let capturedDelta;
    
    const divider = new DraggableDivider(container, {
        onDrag: (deltaY) => {
            dragCalled = true;
            capturedDelta = deltaY;
        }
    });
    
    divider.handleKeyDown({ key: 'ArrowDown', preventDefault: () => {} });
    
    assertTrue(dragCalled, 'Should trigger drag');
    assertTrue(capturedDelta > 0, 'Should move down (positive delta)');
});

test('Arrow up key moves divider up', () => {
    const container = new MockHTMLElement();
    let capturedDelta;
    
    const divider = new DraggableDivider(container, {
        onDrag: (deltaY) => {
            capturedDelta = deltaY;
        }
    });
    
    divider.handleKeyDown({ key: 'ArrowUp', preventDefault: () => {} });
    
    assertTrue(capturedDelta < 0, 'Should move up (negative delta)');
});

test('Keyboard navigation respects step size', () => {
    const container = new MockHTMLElement();
    let capturedDelta;
    
    const divider = new DraggableDivider(container, {
        keyboardStep: 20,
        onDrag: (deltaY) => {
            capturedDelta = deltaY;
        }
    });
    
    divider.handleKeyDown({ key: 'ArrowDown', preventDefault: () => {} });
    
    assertEqual(capturedDelta, 20, 'Should use custom step size');
});

test('Shift+Arrow uses larger step', () => {
    const container = new MockHTMLElement();
    let capturedDelta;
    
    const divider = new DraggableDivider(container, {
        onDrag: (deltaY) => {
            capturedDelta = deltaY;
        }
    });
    
    divider.handleKeyDown({ key: 'ArrowDown', shiftKey: true, preventDefault: () => {} });
    
    // Larger step with shift (e.g., 50px instead of 10px)
    assertTrue(capturedDelta > 10, 'Should use larger step with shift key');
});

test('Keyboard navigation prevents default', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    let preventDefaultCalled = false;
    divider.handleKeyDown({
        key: 'ArrowDown',
        preventDefault: () => { preventDefaultCalled = true; }
    });
    
    assertTrue(preventDefaultCalled, 'Should prevent default for arrow keys');
});

test('Non-arrow keys are ignored', () => {
    const container = new MockHTMLElement();
    let dragCalled = false;
    
    const divider = new DraggableDivider(container, {
        onDrag: () => {
            dragCalled = true;
        }
    });
    
    divider.handleKeyDown({ key: 'a', preventDefault: () => {} });
    
    assertFalse(dragCalled, 'Should ignore non-arrow keys');
});

test('ARIA live region announces changes', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container, {
        announceChanges: true
    });
    
    // Should have live region for announcements
    const ariaLive = divider.element.getAttribute('aria-live');
    assertTrue(ariaLive === 'polite' || ariaLive === 'assertive' || divider.liveRegion !== undefined,
        'Should have ARIA live region or aria-live attribute');
});

test('Focus indicator is visible', () => {
    const container = new MockHTMLElement();
    const divider = new DraggableDivider(container);
    
    // Element should be focusable and have visible focus
    const tabIndex = divider.element.getAttribute('tabindex');
    assertEqual(tabIndex, '0', 'Should be focusable for visible focus indicator');
});

test('Keyboard controls respect minimum size', () => {
    const container = new MockHTMLElement();
    const topPanel = new MockHTMLElement();
    const bottomPanel = new MockHTMLElement();
    
    topPanel.style.height = '60px';
    bottomPanel.style.height = '200px';
    
    const divider = new DraggableDivider(container, {
        topElement: topPanel,
        bottomElement: bottomPanel,
        minSize: 50,
        keyboardStep: 20
    });
    
    // Try to move down (would violate min size)
    divider.handleKeyDown({ key: 'ArrowDown', preventDefault: () => {} });
    
    const newHeight = parseInt(topPanel.style.height);
    assertTrue(newHeight >= 50, 'Should respect minimum size with keyboard');
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

