# Quality Checklists

Accessibility and performance checklists for web frontends.

---

## Web Accessibility Guide (WCAG AAA Compliance)

### Overview

Comprehensive guide to web accessibility compliance following WCAG 2.1/2.2 Level AAA standards. This guide covers the most critical accessibility requirements for modern web design.

**Target Standard**: WCAG 2.1 Level AAA (where practical) with Level AA as minimum baseline.

---

### Table of Contents

1. [Color & Contrast](#color--contrast)
2. [Typography & Readability](#typography--readability)
3. [Keyboard Navigation](#keyboard-navigation)
4. [Screen Reader Support](#screen-reader-support)
5. [Motion & Animation](#motion--animation)
6. [Touch Targets & Mobile](#touch-targets--mobile)
7. [Forms & Input](#forms--input)
8. [Focus Management](#focus-management)
9. [Semantic HTML](#semantic-html)
10. [Testing & Auditing](#testing--auditing)

---

### Color & Contrast

#### WCAG Contrast Requirements

**Level AA (Minimum)**:
- Normal text (< 18pt): 4.5:1 contrast ratio
- Large text (≥ 18pt or 14pt bold): 3:1 contrast ratio

**Level AAA (Enhanced)**:
- Normal text: **7:1 contrast ratio**
- Large text: **4.5:1 contrast ratio**

#### Checking Contrast

**Manual Calculation**:
```javascript
function getLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

function getContrastRatio(rgb1, rgb2) {
  const l1 = getLuminance(...rgb1);
  const l2 = getLuminance(...rgb2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

// Example usage
const textColor = [0, 0, 0]; // Black
const bgColor = [255, 255, 255]; // White
const ratio = getContrastRatio(textColor, bgColor);
console.log(ratio); // 21:1 (AAA compliant)
```

**Tools**:
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- Stark (Figma plugin)
- Chrome DevTools Accessibility Panel

#### Color System (AAA Compliant)

**Using OKLCH Color Space**:
```css
:root {
  /* Text on white background (AAA compliant) */
  --color-text-primary: oklch(20% 0 0); /* #1a1a1a, 11.6:1 */
  --color-text-secondary: oklch(40% 0 0); /* #666666, 7.3:1 */

  /* Backgrounds */
  --color-bg-primary: oklch(98% 0 0); /* Near white */
  --color-bg-secondary: oklch(95% 0 0); /* Light gray */

  /* Accent colors (AAA on white) */
  --color-accent-blue: oklch(45% 0.2 250); /* 7.1:1 */
  --color-accent-green: oklch(50% 0.15 140); /* 7.2:1 */

  /* Interactive states */
  --color-link: oklch(40% 0.2 250); /* Blue, 8.3:1 */
  --color-link-hover: oklch(35% 0.25 250); /* Darker blue, 10.5:1 */
}
```

#### Color Blindness Considerations

**Avoid**:
- Red-green as only distinguisher (affects 8% of males)
- Relying on color alone for meaning

**Best Practices**:
- Use patterns, shapes, or icons alongside color
- Test with color blindness simulators
- Provide high-contrast mode

**Simulation Tools**:
- Chrome DevTools: Rendering > Emulate vision deficiencies
- Colorblindly (browser extension)
- Stark (Figma)

---

### Typography & Readability

#### Font Size Requirements

**WCAG Guidelines**:
- Body text: Minimum 16px (1rem)
- Small text: Minimum 14px (0.875rem)
- Users must be able to zoom to 200% without loss of functionality

**Recommended Sizes**:
```css
:root {
  /* Fluid typography */
  --font-size-sm: clamp(0.875rem, 0.8rem + 0.375vw, 1rem);
  --font-size-base: clamp(1rem, 0.9rem + 0.5vw, 1.25rem);
  --font-size-lg: clamp(1.25rem, 1.1rem + 0.75vw, 1.75rem);
  --font-size-xl: clamp(1.75rem, 1.5rem + 1.25vw, 2.5rem);
}

body {
  font-size: var(--font-size-base);
  line-height: 1.5; /* WCAG minimum for body text */
}
```

#### Line Height & Spacing

**WCAG 1.4.12 (Level AAA)**:
- Line height: Minimum 1.5× font size
- Paragraph spacing: Minimum 2× font size
- Letter spacing: Minimum 0.12× font size
- Word spacing: Minimum 0.16× font size

**Implementation**:
```css
p {
  font-size: 1rem;
  line-height: 1.6; /* 1.5× minimum */
  margin-bottom: 2rem; /* 2× font size */
  letter-spacing: 0.01em; /* Slight increase */
  word-spacing: 0.05em;
}
```

#### Font Choices

**Accessible Fonts**:
- Sans-serif: Inter, Roboto, Open Sans, Atkinson Hyperlegible
- Serif: Georgia, Merriweather, Lora
- Avoid: Overly decorative, thin weights (< 300), all-caps for long text

**Dyslexia-Friendly**:
- OpenDyslexic
- Atkinson Hyperlegible
- Comic Sans (surprisingly good for dyslexia)

---

### Keyboard Navigation

#### Requirements

**All interactive elements must be**:
- Focusable with Tab key
- Activatable with Enter or Space
- Dismissible with Escape (modals, dropdowns)
- Navigable with arrow keys (where appropriate)

#### Tab Order

**Logical Tab Order**:
```html
<!-- Natural DOM order is best -->
<button tabindex="0">First</button>
<button tabindex="0">Second</button>
<button tabindex="0">Third</button>

<!-- Avoid tabindex > 0 (creates unpredictable order) -->
<button tabindex="3">Third</button> <!-- BAD -->
<button tabindex="1">First</button> <!-- BAD -->
```

**Skip Links**:
```html
<a href="#main-content" class="skip-link">
  Skip to main content
</a>

<nav>...</nav>

<main id="main-content">
  <!-- Main content -->
</main>
```

```css
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: #000;
  color: #fff;
  padding: 8px;
  text-decoration: none;
  z-index: 100;
}

.skip-link:focus {
  top: 0;
}
```

#### Focus Indicators

**WCAG 2.4.7 (Level AA)**:
- Focus indicator must be visible
- Minimum 2px thick
- Sufficient contrast (3:1 against background)

**Modern Focus Styles**:
```css
/* Remove default outline */
*:focus {
  outline: none;
}

/* Custom focus indicator */
:focus-visible {
  outline: 3px solid var(--color-accent);
  outline-offset: 2px;
  border-radius: 4px;
}

/* Remove focus ring for mouse users */
:focus:not(:focus-visible) {
  outline: none;
}

/* Button focus */
button:focus-visible {
  outline: 3px solid #3b82f6;
  outline-offset: 2px;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2);
}
```

#### Keyboard Patterns

**Modal Dialogs**:
```javascript
function trapFocus(element) {
  const focusableElements = element.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const firstFocusable = focusableElements[0];
  const lastFocusable = focusableElements[focusableElements.length - 1];

  element.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      if (e.shiftKey && document.activeElement === firstFocusable) {
        e.preventDefault();
        lastFocusable.focus();
      } else if (!e.shiftKey && document.activeElement === lastFocusable) {
        e.preventDefault();
        firstFocusable.focus();
      }
    }

    if (e.key === 'Escape') {
      closeModal();
    }
  });

  firstFocusable.focus();
}
```

**Dropdown Menus**:
```javascript
function handleDropdownKeys(e) {
  const items = Array.from(dropdown.querySelectorAll('[role="menuitem"]'));
  const currentIndex = items.indexOf(document.activeElement);

  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault();
      const nextIndex = (currentIndex + 1) % items.length;
      items[nextIndex].focus();
      break;

    case 'ArrowUp':
      e.preventDefault();
      const prevIndex = (currentIndex - 1 + items.length) % items.length;
      items[prevIndex].focus();
      break;

    case 'Home':
      e.preventDefault();
      items[0].focus();
      break;

    case 'End':
      e.preventDefault();
      items[items.length - 1].focus();
      break;

    case 'Escape':
      closeDropdown();
      triggerButton.focus();
      break;
  }
}
```

---

### Screen Reader Support

#### ARIA Attributes

**Essential ARIA**:

**Landmarks**:
```html
<header role="banner">
  <nav role="navigation" aria-label="Main">
    <!-- Navigation -->
  </nav>
</header>

<main role="main">
  <!-- Main content -->
</main>

<aside role="complementary" aria-label="Related articles">
  <!-- Sidebar -->
</aside>

<footer role="contentinfo">
  <!-- Footer -->
</footer>
```

**Buttons**:
```html
<!-- Icon button needs label -->
<button aria-label="Close menu">
  <svg>...</svg>
</button>

<!-- Button with visible text -->
<button>
  <svg aria-hidden="true">...</svg>
  Submit
</button>
```

**Live Regions**:
```html
<!-- Announce loading state -->
<div role="status" aria-live="polite" aria-atomic="true">
  Loading content...
</div>

<!-- Announce errors -->
<div role="alert" aria-live="assertive">
  Error: Form submission failed.
</div>
```

**Custom Components**:
```html
<!-- Accordion -->
<div class="accordion">
  <h3>
    <button
      aria-expanded="false"
      aria-controls="panel-1"
      id="button-1"
    >
      Section 1
    </button>
  </h3>
  <div
    id="panel-1"
    role="region"
    aria-labelledby="button-1"
    hidden
  >
    Content...
  </div>
</div>

<!-- Tab panel -->
<div role="tablist" aria-label="Content sections">
  <button role="tab" aria-selected="true" aria-controls="panel-1">
    Tab 1
  </button>
  <button role="tab" aria-selected="false" aria-controls="panel-2">
    Tab 2
  </button>
</div>
<div role="tabpanel" id="panel-1" aria-labelledby="tab-1">
  Panel content...
</div>
```

#### Alt Text Guidelines

**Images**:
```html
<!-- Informative image -->
<img src="chart.png" alt="Bar chart showing 50% increase in sales">

<!-- Decorative image -->
<img src="decorative.png" alt="" role="presentation">

<!-- Complex image -->
<img src="infographic.png" alt="Sales data for Q4" longdesc="sales-data.html">
```

**Best Practices**:
- Describe the content/function, not "image of..."
- Keep under 150 characters (screen readers pause)
- Use empty alt (`alt=""`) for decorative images
- Provide long descriptions for complex images

---

### Motion & Animation

#### Reduced Motion Preference

**WCAG 2.3.3 (Level AAA)**:
Users must be able to disable non-essential motion.

**Implementation**:
```css
/* Default: animations enabled */
.animated-element {
  animation: slide-in 0.5s ease;
}

/* Respect user preference */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }

  /* Keep essential animations but reduce */
  .loading-spinner {
    animation-duration: 1s; /* Slower */
  }
}
```

**JavaScript Detection**:
```javascript
const prefersReducedMotion = window.matchMedia(
  '(prefers-reduced-motion: reduce)'
).matches;

if (prefersReducedMotion) {
  // Disable or simplify animations
  gsap.config({ nullTargetWarn: false, force3D: false });

  // Skip scroll animations
  ScrollTrigger.getAll().forEach(st => st.kill());
}
```

#### Animation Guidelines

**Safe Animations**:
- Fade in/out (opacity)
- Slide short distances (< 50px)
- Scale small amounts (0.95-1.05)
- Avoid: flashing, rapid movement, parallax

**Vestibular Disorders**:
Avoid animations that can cause dizziness or nausea:
- Large parallax effects
- Continuous rotation
- Zoom effects
- Perspective transforms

---

### Touch Targets & Mobile

#### WCAG 2.5.5 (Level AAA)

**Target Size**: Minimum 44×44px (iOS) or 48×48px (Android)

**Spacing**: Minimum 8px between targets

**Implementation**:
```css
button, a {
  min-height: 44px;
  min-width: 44px;
  padding: 12px 24px;
  /* Touch target includes padding */
}

/* Increase tap target without changing visual size */
button::before {
  content: '';
  position: absolute;
  inset: -8px; /* Extends tap target by 8px all sides */
}
```

#### Mobile Considerations

**Viewport**:
```html
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
```
*Note*: Allow zoom up to 5× (WCAG requirement)

**Touch Gestures**:
- Avoid complex gestures (multi-finger, long-press)
- Provide alternative interactions
- Don't rely on hover states

---

### Forms & Input

#### Labels & Instructions

**WCAG 3.3.2 (Level A)**:
Every input must have a visible label.

**Implementation**:
```html
<!-- Explicit label -->
<label for="email">Email address</label>
<input id="email" type="email" required aria-describedby="email-help">
<small id="email-help">We'll never share your email.</small>

<!-- Error state -->
<input
  id="email"
  type="email"
  aria-invalid="true"
  aria-describedby="email-error"
>
<div id="email-error" role="alert">
  Please enter a valid email address.
</div>
```

#### Form Validation

**Accessible Validation**:
```javascript
function validateEmail(input) {
  const isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value);

  if (isValid) {
    input.setAttribute('aria-invalid', 'false');
    input.removeAttribute('aria-describedby');
    removeError(input);
  } else {
    input.setAttribute('aria-invalid', 'true');
    input.setAttribute('aria-describedby', `${input.id}-error`);
    showError(input, 'Please enter a valid email address.');
  }
}

function showError(input, message) {
  const errorElement = document.getElementById(`${input.id}-error`) ||
                       createErrorElement(input.id);
  errorElement.textContent = message;
  errorElement.setAttribute('role', 'alert'); // Announces to screen readers
}
```

#### Required Fields

**Indication**:
```html
<label for="name">
  Full name
  <abbr title="required" aria-label="required">*</abbr>
</label>
<input id="name" type="text" required aria-required="true">
```

**Visual + Programmatic**:
- Visual indicator (asterisk, "required")
- `required` attribute
- `aria-required="true"`

---

### Focus Management

#### Managing Focus States

**After Modal Opens**:
```javascript
function openModal() {
  modal.style.display = 'block';
  modal.setAttribute('aria-hidden', 'false');

  // Focus first focusable element
  const firstFocusable = modal.querySelector('button, [href], input');
  firstFocusable.focus();

  // Trap focus
  trapFocus(modal);
}
```

**After Modal Closes**:
```javascript
function closeModal() {
  modal.style.display = 'none';
  modal.setAttribute('aria-hidden', 'true');

  // Return focus to trigger button
  triggerButton.focus();
}
```

#### Focus Order

**Best Practices**:
- Follow visual order (top to bottom, left to right)
- Group related elements
- Use `tabindex="-1"` for programmatic focus only
- Avoid `tabindex > 0` (creates unpredictable order)

---

### Semantic HTML

#### Heading Hierarchy

**WCAG 1.3.1 (Level A)**:
Use proper heading levels (h1-h6) without skipping.

**Correct**:
```html
<h1>Page Title</h1>
<h2>Section</h2>
<h3>Subsection</h3>
<h3>Another Subsection</h3>
<h2>Another Section</h2>
```

**Incorrect**:
```html
<h1>Page Title</h1>
<h3>Section</h3> <!-- Skipped h2 -->
```

#### Landmark Regions

**Essential Landmarks**:
```html
<header>
  <nav aria-label="Main navigation">
    <!-- Primary nav -->
  </nav>
</header>

<main>
  <article>
    <header>
      <h1>Article Title</h1>
    </header>
    <!-- Article content -->
  </article>

  <aside aria-label="Related links">
    <!-- Sidebar -->
  </aside>
</main>

<footer>
  <nav aria-label="Footer navigation">
    <!-- Footer nav -->
  </nav>
</footer>
```

#### Lists & Tables

**Lists**:
```html
<!-- Use proper list elements -->
<ul>
  <li>Item 1</li>
  <li>Item 2</li>
</ul>

<!-- Not divs styled as lists -->
```

**Tables**:
```html
<table>
  <caption>Sales Data Q4 2024</caption>
  <thead>
    <tr>
      <th scope="col">Month</th>
      <th scope="col">Sales</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>October</td>
      <td>$50,000</td>
    </tr>
  </tbody>
</table>
```

---

### Testing & Auditing

#### Automated Testing Tools

**Browser Extensions**:
- axe DevTools (Chrome/Firefox)
- WAVE (Web Accessibility Evaluation Tool)
- Lighthouse (Chrome DevTools)

**Command Line**:
```bash
## pa11y
pa11y https://example.com

## axe-core CLI
axe https://example.com
```

#### Manual Testing Checklist

**Keyboard Navigation**:
- [ ] Tab through all interactive elements
- [ ] Activate with Enter/Space
- [ ] Close modals with Escape
- [ ] Navigate dropdowns with arrow keys

**Screen Reader Testing**:
- [ ] Test with NVDA (Windows), VoiceOver (Mac), JAWS
- [ ] Check heading structure
- [ ] Verify alt text
- [ ] Test form labels and errors

**Visual Testing**:
- [ ] Zoom to 200%
- [ ] Test color contrast
- [ ] Check focus indicators
- [ ] Review with color blindness simulator

**Motion Testing**:
- [ ] Enable `prefers-reduced-motion`
- [ ] Verify animations are disabled/reduced
- [ ] Check for essential animations that remain

#### Screen Reader Testing Commands

**NVDA (Windows)**:
- Toggle: Caps Lock or Insert
- Next heading: H
- Next landmark: D
- Read all: Caps Lock + Down Arrow

**VoiceOver (Mac)**:
- Toggle: Cmd + F5
- Rotor: Ctrl + Option + U
- Next heading: Ctrl + Option + Cmd + H

**JAWS (Windows)**:
- List headings: Insert + F6
- List links: Insert + F7
- Next heading: H

---

### Common Accessibility Patterns

#### Accessible Modal

```jsx
function AccessibleModal({ isOpen, onClose, children }) {
  const modalRef = useRef(null);
  const triggerRef = useRef(document.activeElement);

  useEffect(() => {
    if (isOpen) {
      // Trap focus
      trapFocus(modalRef.current);

      // Focus first element
      const firstFocusable = modalRef.current.querySelector('button, [href], input');
      firstFocusable?.focus();

      // Prevent body scroll
      document.body.style.overflow = 'hidden';
    } else {
      // Return focus
      triggerRef.current?.focus();
      document.body.style.overflow = '';
    }

    // Listen for Escape key
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEscape);

    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="modal-backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div
        ref={modalRef}
        className="modal"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="modal-title">Modal Title</h2>
        {children}
        <button onClick={onClose} aria-label="Close modal">
          ×
        </button>
      </div>
    </div>
  );
}
```

#### Accessible Accordion

```html
<div class="accordion">
  <h3>
    <button
      aria-expanded="false"
      aria-controls="panel-1"
      id="accordion-button-1"
    >
      <span class="accordion-title">Section 1</span>
      <svg class="accordion-icon" aria-hidden="true">...</svg>
    </button>
  </h3>
  <div
    id="panel-1"
    role="region"
    aria-labelledby="accordion-button-1"
    hidden
  >
    <p>Content for section 1...</p>
  </div>
</div>
```

```javascript
function initAccordion() {
  const buttons = document.querySelectorAll('.accordion button');

  buttons.forEach(button => {
    button.addEventListener('click', () => {
      const expanded = button.getAttribute('aria-expanded') === 'true';
      const panel = document.getElementById(button.getAttribute('aria-controls'));

      button.setAttribute('aria-expanded', !expanded);
      panel.hidden = expanded;
    });
  });
}
```

---

### WCAG Quick Reference

**Level A (Must Have)**:
- Text alternatives (alt text)
- Keyboard accessible
- Color not only means of conveying info
- Labeled form inputs
- Proper heading hierarchy

**Level AA (Should Have)**:
- 4.5:1 contrast for normal text
- 3:1 contrast for large text
- Resize text to 200%
- Focus visible
- Multiple ways to find pages

**Level AAA (Nice to Have)**:
- 7:1 contrast for normal text
- 4.5:1 contrast for large text
- Target size 44×44px minimum
- No timing restrictions
- Help available

---

*Last updated: 2024*
*Based on WCAG 2.1 and WCAG 2.2 standards*

---

## Web Performance Optimization Checklist

### Overview

Comprehensive performance optimization guide targeting Core Web Vitals and 60 FPS experiences. This checklist covers measurement, optimization strategies, and modern best practices.

**Performance Budget Targets**:
- Largest Contentful Paint (LCP): < 2.5s
- First Input Delay (FID): < 100ms
- Cumulative Layout Shift (CLS): < 0.1
- Interaction to Next Paint (INP): < 200ms
- Time to Interactive (TTI): < 3.8s
- First Contentful Paint (FCP): < 1.8s

---

### Table of Contents

1. [Core Web Vitals](#core-web-vitals)
2. [Animation Performance](#animation-performance)
3. [Image Optimization](#image-optimization)
4. [Font Loading](#font-loading)
5. [JavaScript Optimization](#javascript-optimization)
6. [CSS Optimization](#css-optimization)
7. [3D & WebGL Optimization](#3d--webgl-optimization)
8. [Loading Strategies](#loading-strategies)
9. [Caching & CDN](#caching--cdn)
10. [Monitoring & Measurement](#monitoring--measurement)

---

### Core Web Vitals

#### Largest Contentful Paint (LCP)

**Target**: < 2.5 seconds

**What it measures**: Time until largest content element is visible.

**Optimization Checklist**:
- [ ] Optimize hero images (WebP/AVIF, < 100KB)
- [ ] Preload critical resources (`<link rel="preload">`)
- [ ] Eliminate render-blocking resources
- [ ] Use CDN for static assets
- [ ] Implement efficient server response time (< 200ms TTFB)
- [ ] Remove unused CSS/JS
- [ ] Enable compression (Brotli/gzip)

**Implementation**:
```html
<!-- Preload critical resources -->
<link rel="preload" as="image" href="hero.webp" type="image/webp">
<link rel="preload" as="font" href="inter-var.woff2" type="font/woff2" crossorigin>

<!-- Modern image formats -->
<picture>
  <source srcset="hero.avif" type="image/avif">
  <source srcset="hero.webp" type="image/webp">
  <img src="hero.jpg" alt="Hero" loading="eager" fetchpriority="high">
</picture>
```

**Debugging**:
```javascript
// Measure LCP
new PerformanceObserver((list) => {
  const entries = list.getEntries();
  const lastEntry = entries[entries.length - 1];
  console.log('LCP:', lastEntry.renderTime || lastEntry.loadTime);
}).observe({ entryTypes: ['largest-contentful-paint'] });
```

---

#### First Input Delay (FID) / Interaction to Next Paint (INP)

**Target**: FID < 100ms, INP < 200ms

**What it measures**: Responsiveness to user interactions.

**Optimization Checklist**:
- [ ] Split long tasks (< 50ms each)
- [ ] Defer non-critical JavaScript
- [ ] Use web workers for heavy computation
- [ ] Implement code splitting
- [ ] Avoid long-running event handlers
- [ ] Debounce scroll/resize listeners
- [ ] Use passive event listeners

**Implementation**:
```javascript
// Split long tasks
function yieldToMain() {
  return new Promise(resolve => {
    setTimeout(resolve, 0);
  });
}

async function processLargeArray(array) {
  for (let i = 0; i < array.length; i++) {
    processItem(array[i]);

    // Yield every 50 items
    if (i % 50 === 0) {
      await yieldToMain();
    }
  }
}

// Passive event listeners
window.addEventListener('scroll', handleScroll, { passive: true });

// Debounced resize handler
const debouncedResize = debounce(() => {
  handleResize();
}, 150);

window.addEventListener('resize', debouncedResize);
```

---

#### Cumulative Layout Shift (CLS)

**Target**: < 0.1

**What it measures**: Visual stability during page load.

**Optimization Checklist**:
- [ ] Reserve space for images (use `aspect-ratio`)
- [ ] Reserve space for ads and embeds
- [ ] Avoid inserting content above existing content
- [ ] Use CSS transforms instead of position changes
- [ ] Set explicit dimensions for iframes
- [ ] Avoid web fonts that cause FOUT/FOIT
- [ ] Use `font-display: swap` or `font-display: optional`

**Implementation**:
```css
/* Reserve space for images */
img {
  aspect-ratio: attr(width) / attr(height);
  width: 100%;
  height: auto;
}

/* Or explicit aspect ratio */
.hero-image {
  aspect-ratio: 16 / 9;
}

/* Animations: use transform, not position */
.animated {
  transform: translateX(0);
  transition: transform 0.3s;
}

.animated.active {
  transform: translateX(100px); /* Good */
  /* left: 100px; Bad - causes layout shift */
}
```

**Debugging**:
```javascript
// Measure CLS
let clsValue = 0;
new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (!entry.hadRecentInput) {
      clsValue += entry.value;
      console.log('CLS:', clsValue);
    }
  }
}).observe({ entryTypes: ['layout-shift'] });
```

---

### Animation Performance

#### 60 FPS Checklist

**Target**: < 16.67ms per frame

**GPU-Accelerated Properties (Use These)**:
- `transform` (translate, scale, rotate)
- `opacity`
- `filter` (some, like blur - be careful)

**Avoid Animating**:
- `top`, `left`, `right`, `bottom`
- `width`, `height`
- `margin`, `padding`
- `border-width`

**Implementation**:
```css
/* Good: GPU-accelerated */
.animated {
  transform: translateX(0);
  opacity: 1;
  transition: transform 0.3s, opacity 0.3s;
}

.animated.active {
  transform: translateX(100px) scale(1.1);
  opacity: 0.8;
}

/* Bad: triggers layout/paint */
.animated-bad {
  left: 0;
  width: 100px;
  transition: left 0.3s, width 0.3s;
}
```

#### Will-Change Optimization

**Use Sparingly**:
```css
/* Only during animation */
.will-animate {
  /* Don't set will-change here */
}

.will-animate.animating {
  will-change: transform; /* Set on animation start */
}

.will-animate.done {
  will-change: auto; /* Remove after animation */
}
```

**JavaScript Control**:
```javascript
element.addEventListener('mouseenter', () => {
  element.style.willChange = 'transform';
});

element.addEventListener('mouseleave', () => {
  // Remove after animation completes
  element.addEventListener('transitionend', () => {
    element.style.willChange = 'auto';
  }, { once: true });
});
```

#### RequestAnimationFrame

**Always use for JavaScript animations**:
```javascript
// Good
function animate() {
  element.style.transform = `translateX(${x}px)`;
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);

// Bad
setInterval(() => {
  element.style.transform = `translateX(${x}px)`;
}, 16); // Not synced with browser paint
```

#### Performance Monitoring

**Chrome DevTools**:
```javascript
// Mark start of expensive operation
performance.mark('animation-start');

// ... do animation work ...

// Mark end
performance.mark('animation-end');

// Measure duration
performance.measure('animation-duration', 'animation-start', 'animation-end');

// Get measurement
const measure = performance.getEntriesByName('animation-duration')[0];
console.log(`Animation took ${measure.duration}ms`);
```

---

### Image Optimization

#### Format Selection

**Decision Tree**:
1. **Photos**: AVIF > WebP > JPEG
2. **Graphics/logos**: SVG > WebP > PNG
3. **Animations**: WebP animated > GIF
4. **Icons**: SVG or icon fonts

**Implementation**:
```html
<picture>
  <!-- Modern browsers: AVIF (best compression) -->
  <source srcset="image.avif" type="image/avif">

  <!-- Fallback: WebP (good compression) -->
  <source srcset="image.webp" type="image/webp">

  <!-- Final fallback: JPEG -->
  <img src="image.jpg" alt="Description" loading="lazy">
</picture>
```

#### Responsive Images

**Checklist**:
- [ ] Use `srcset` for multiple resolutions
- [ ] Define `sizes` attribute
- [ ] Serve appropriately sized images (not full-res everywhere)
- [ ] Use lazy loading for below-fold images
- [ ] Set explicit dimensions to prevent CLS

**Implementation**:
```html
<img
  src="image-800.jpg"
  srcset="
    image-400.jpg 400w,
    image-800.jpg 800w,
    image-1200.jpg 1200w,
    image-1600.jpg 1600w
  "
  sizes="
    (max-width: 640px) 100vw,
    (max-width: 1024px) 50vw,
    33vw
  "
  alt="Description"
  loading="lazy"
  width="1200"
  height="800"
>
```

#### Image Compression

**Tools**:
- **CLI**: ImageMagick, Sharp (Node.js)
- **GUI**: Squoosh (web), ImageOptim (Mac)
- **Build tools**: imagemin, @squoosh/lib

**Example (Sharp)**:
```javascript
const sharp = require('sharp');

await sharp('input.jpg')
  .resize(1200, 800, { fit: 'cover' })
  .webp({ quality: 80 })
  .toFile('output.webp');

await sharp('input.jpg')
  .resize(1200, 800, { fit: 'cover' })
  .avif({ quality: 70 })
  .toFile('output.avif');
```

#### Lazy Loading

**Native Lazy Loading**:
```html
<!-- Lazy load below-fold images -->
<img src="image.jpg" loading="lazy" alt="Description">

<!-- Eager load above-fold images -->
<img src="hero.jpg" loading="eager" fetchpriority="high" alt="Hero">
```

**Intersection Observer (Advanced)**:
```javascript
const imageObserver = new IntersectionObserver((entries, observer) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      img.classList.remove('lazy');
      observer.unobserve(img);
    }
  });
});

document.querySelectorAll('img[data-src]').forEach(img => {
  imageObserver.observe(img);
});
```

---

### Font Loading

#### Font Display Strategy

**Options**:
- `swap`: Show fallback, swap when loaded (FOUT - Flash of Unstyled Text)
- `optional`: Use cached font if available, otherwise use fallback
- `fallback`: Brief block, swap if fast, fallback if slow

**Recommended**:
```css
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-var.woff2') format('woff2-variations');
  font-weight: 100 900;
  font-display: swap; /* Show fallback immediately */
}
```

#### Font Subsetting

**Reduce file size by including only needed characters**:

**Tools**: `pyftsubset` (part of fonttools)

```bash
## Include only Latin characters
pyftsubset input.ttf \
  --output-file=output.woff2 \
  --flavor=woff2 \
  --layout-features=* \
  --unicodes=U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD
```

#### Preload Critical Fonts

```html
<link
  rel="preload"
  as="font"
  href="/fonts/inter-var.woff2"
  type="font/woff2"
  crossorigin
>
```

#### System Font Stack

**Performance-first approach**:
```css
body {
  font-family:
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    Roboto,
    Oxygen,
    Ubuntu,
    Cantarell,
    sans-serif;
}
```

---

### JavaScript Optimization

#### Code Splitting

**Route-based splitting**:
```javascript
// React Router
const Home = lazy(() => import('./pages/Home'));
const About = lazy(() => import('./pages/About'));
const Gallery = lazy(() => import('./pages/Gallery'));

<Suspense fallback={<Loading />}>
  <Routes>
    <Route path="/" element={<Home />} />
    <Route path="/about" element={<About />} />
    <Route path="/gallery" element={<Gallery />} />
  </Routes>
</Suspense>
```

**Component-based splitting**:
```javascript
// Load heavy components only when needed
const HeavyChart = lazy(() => import('./components/HeavyChart'));

function Dashboard() {
  const [showChart, setShowChart] = useState(false);

  return (
    <div>
      <button onClick={() => setShowChart(true)}>Show Chart</button>
      {showChart && (
        <Suspense fallback={<Skeleton />}>
          <HeavyChart />
        </Suspense>
      )}
    </div>
  );
}
```

#### Tree Shaking

**Ensure tree shaking works**:
```javascript
// Good: Named imports
import { map, filter } from 'lodash-es';

// Bad: Default import (imports entire library)
import _ from 'lodash';
```

#### Bundle Analysis

**Webpack Bundle Analyzer**:
```bash

## Add to webpack.config.js
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

plugins: [
  new BundleAnalyzerPlugin()
]
```

**Vite**:
```bash

## vite.config.js
import { visualizer } from 'rollup-plugin-visualizer';

export default {
  plugins: [visualizer({ open: true })]
}
```

---

### CSS Optimization

#### Critical CSS

**Inline above-the-fold CSS**:
```html
<style>
  /* Critical CSS inlined */
  body { font-family: sans-serif; }
  .hero { height: 100vh; }
</style>

<!-- Defer non-critical CSS -->
<link rel="preload" href="styles.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="styles.css"></noscript>
```

**Tools**:
- Critical (npm package)
- Critters (Vite/Webpack plugin)

#### Remove Unused CSS

**PurgeCSS**:
```javascript
// postcss.config.js
module.exports = {
  plugins: [
    require('@fullhuman/postcss-purgecss')({
      content: ['./src/**/*.html', './src/**/*.jsx'],
      defaultExtractor: content => content.match(/[\w-/:]+(?<!:)/g) || []
    })
  ]
}
```

#### CSS Containment

**Improve rendering performance**:
```css
.card {
  /* Isolate layout calculations */
  contain: layout style paint;
}

.article {
  /* More aggressive containment */
  contain: strict;
}
```

---

### 3D & WebGL Optimization

#### Loading Strategy

**Checklist**:
- [ ] Show placeholder while loading
- [ ] Load 3D content below fold lazily
- [ ] Use low-poly models initially
- [ ] Progressive enhancement with high-poly

**Implementation**:
```javascript
// Lazy load Three.js scene
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      loadThreeJSScene();
      observer.unobserve(entry.target);
    }
  });
});

observer.observe(document.querySelector('.3d-container'));
```

#### Runtime Performance

**Checklist**:
- [ ] Implement object pooling (reuse objects)
- [ ] Use LOD (Level of Detail)
- [ ] Frustum culling (don't render off-screen objects)
- [ ] Texture compression (Basis Universal, KTX2)
- [ ] Reduce polygon count (< 100k for real-time)
- [ ] Limit draw calls (< 100 per frame)
- [ ] Use instancing for repeated geometry

**Three.js Example**:
```javascript
// Object pooling
const objectPool = [];

function getObject() {
  return objectPool.length > 0 ? objectPool.pop() : createNewObject();
}

function releaseObject(obj) {
  objectPool.push(obj);
}

// LOD (Level of Detail)
const lod = new THREE.LOD();
lod.addLevel(highPolyMesh, 0);   // 0-50m
lod.addLevel(mediumPolyMesh, 50); // 50-100m
lod.addLevel(lowPolyMesh, 100);   // 100m+
scene.add(lod);

// Instancing
const geometry = new THREE.BoxGeometry();
const material = new THREE.MeshStandardMaterial();
const count = 10000;

const mesh = new THREE.InstancedMesh(geometry, material, count);
scene.add(mesh);
```

#### Texture Optimization

**Checklist**:
- [ ] Use power-of-two dimensions (512, 1024, 2048)
- [ ] Compress textures (Basis, KTX2)
- [ ] Use texture atlases
- [ ] Reduce texture resolution (don't use 4K everywhere)
- [ ] Enable mipmaps

---

### Loading Strategies

#### Critical Rendering Path

**Optimize the order**:

1. **HTML** (initial)
2. **Critical CSS** (inlined)
3. **Critical JavaScript** (defer rest)
4. **Fonts** (preload, font-display: swap)
5. **Images** (lazy load below-fold)

**Implementation**:
```html
<!DOCTYPE html>
<html>
<head>
  <!-- Critical CSS inlined -->
  <style>/* Critical styles */</style>

  <!-- Preload critical resources -->
  <link rel="preload" as="font" href="font.woff2" type="font/woff2" crossorigin>
  <link rel="preload" as="image" href="hero.webp">

  <!-- Defer non-critical CSS -->
  <link rel="preload" href="styles.css" as="style" onload="this.onload=null;this.rel='stylesheet'">

  <!-- Defer JavaScript -->
  <script defer src="main.js"></script>
</head>
<body>
  <!-- Content -->
</body>
</html>
```

#### Resource Hints

**Preconnect** (DNS, TCP, TLS):
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://cdn.example.com">
```

**DNS-Prefetch**:
```html
<link rel="dns-prefetch" href="https://analytics.example.com">
```

**Prefetch** (next page):
```html
<link rel="prefetch" href="/next-page.html">
```

---

### Caching & CDN

#### HTTP Caching Headers

**Static Assets** (immutable):
```
Cache-Control: public, max-age=31536000, immutable
```

**HTML** (revalidate):
```
Cache-Control: no-cache
```

**API Responses**:
```
Cache-Control: public, max-age=3600, must-revalidate
```

#### Service Worker Caching

**Workbox**:
```javascript
import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { CacheFirst, NetworkFirst } from 'workbox-strategies';

// Precache build assets
precacheAndRoute(self.__WB_MANIFEST);

// Cache images
registerRoute(
  ({ request }) => request.destination === 'image',
  new CacheFirst({ cacheName: 'images' })
);

// Network-first for HTML
registerRoute(
  ({ request }) => request.mode === 'navigate',
  new NetworkFirst({ cacheName: 'pages' })
);
```

---

### Monitoring & Measurement

#### Real User Monitoring (RUM)

**Web Vitals**:

```javascript
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendToAnalytics({ name, value, id }) {
  // Send to your analytics endpoint
  fetch('/analytics', {
    method: 'POST',
    body: JSON.stringify({ name, value, id })
  });
}

getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);
```

#### Performance Budget

**Lighthouse CI**:
```json
// lighthouserc.json
{
  "ci": {
    "collect": {
      "numberOfRuns": 3
    },
    "assert": {
      "assertions": {
        "first-contentful-paint": ["error", {"maxNumericValue": 1800}],
        "largest-contentful-paint": ["error", {"maxNumericValue": 2500}],
        "cumulative-layout-shift": ["error", {"maxNumericValue": 0.1}],
        "total-blocking-time": ["error", {"maxNumericValue": 200}]
      }
    }
  }
}
```

#### Chrome DevTools

**Performance Panel**:
1. Open DevTools (F12)
2. Performance tab
3. Click Record
4. Interact with page
5. Stop recording
6. Analyze flame chart

**Look for**:
- Long tasks (> 50ms)
- Excessive layout thrashing
- Forced synchronous layouts
- Paint flashing

---

### Quick Wins Checklist

**Immediate Impact**:
- [ ] Enable Brotli/gzip compression
- [ ] Implement lazy loading for images
- [ ] Add `width` and `height` to images (prevent CLS)
- [ ] Use modern image formats (WebP/AVIF)
- [ ] Preload critical resources
- [ ] Defer non-critical JavaScript
- [ ] Use CDN for static assets
- [ ] Enable HTTP/2 or HTTP/3
- [ ] Minify CSS and JavaScript
- [ ] Remove unused CSS/JS

**High Impact**:
- [ ] Implement code splitting
- [ ] Optimize images (< 100KB)
- [ ] Use system fonts or preload web fonts
- [ ] Inline critical CSS
- [ ] Implement service worker caching
- [ ] Optimize animation performance (use transforms)
- [ ] Reduce JavaScript bundle size (< 200KB)
- [ ] Set up performance monitoring

---

*Last updated: 2024*
*Benchmarks based on median 4G mobile connections*
