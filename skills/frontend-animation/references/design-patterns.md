# Design Patterns

Modern design trends and interaction patterns.

---

## Web Design Trends 2024-2025

### Overview

This document catalogs the dominant web design trends, aesthetic movements, and interaction paradigms shaping modern web experiences in 2024-2025. Updated regularly based on industry analysis, award-winning sites, and emerging patterns.

### Visual Design Trends

#### 1. Bold Minimalism

**Definition**: Minimalist foundations enhanced with bold typography, intentional color, and confident white space.

**Key Characteristics**:
- Ultra-large typography (80px-200px+ headlines)
- Limited color palettes (2-4 colors max)
- Generous white space (breathing room)
- High contrast (black/white, bold accent colors)
- Geometric shapes and clean lines
- Sans-serif dominance (Inter, Space Grotesk, Sora)

**Examples**:
- Apple product pages
- Linear.app
- Stripe documentation
- Vercel website

**Implementation Tips**:
```css
/* Fluid typography for bold headlines */
h1 {
  font-size: clamp(3rem, 8vw, 10rem);
  font-weight: 700;
  line-height: 0.95;
  letter-spacing: -0.03em;
}

/* Generous spacing */
section {
  padding: clamp(3rem, 10vw, 8rem) 0;
}
```

**Why It Works**: Reduces cognitive load, focuses attention, loads fast, works across devices.

---

#### 2. Kinetic Typography

**Definition**: Text that moves, transforms, and responds to user interaction.

**Patterns**:

**a) Variable Font Animations**:
- Weight transitions (100 → 900)
- Width morphing (condensed → expanded)
- Slant/italic transformations
- Multiple axes animating simultaneously

**Implementation**:
```css
@font-face {
  font-family: 'Inter';
  src: url('Inter-Variable.woff2') format('woff2-variations');
  font-weight: 100 900;
}

h1 {
  font-variation-settings: 'wght' 300;
  transition: font-variation-settings 0.3s;
}

h1:hover {
  font-variation-settings: 'wght' 900;
}
```

**b) Text Split & Stagger**:
- Reveal by character, word, or line
- Staggered entrance animations
- 3D text transformations

**c) Scroll-Linked Text**:
- Text color change on scroll
- Weight increase/decrease
- Size transformations
- Parallax text layers

**Related Skills**: `scroll-animation` for text animations, `ui-motion` for React text effects

---

#### 3. Glassmorphism 2.0

**Evolution**: Refined frosted-glass aesthetic with better accessibility and performance.

**Modern Approach** (2024):
```css
.glass-card {
  /* More subtle, accessible backgrounds */
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px) saturate(150%);

  /* Higher contrast borders */
  border: 1px solid rgba(255, 255, 255, 0.18);

  /* Softer, more realistic shadows */
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);

  border-radius: 16px;
}

/* Dark mode variant */
@media (prefers-color-scheme: dark) {
  .glass-card {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
}
```

**Accessibility Considerations**:
- Ensure text has 4.5:1+ contrast on glass backgrounds
- Test with screen readers (ensure content is readable)
- Provide high-contrast mode alternative

**Performance**:
- `backdrop-filter` can be expensive on mobile
- Use sparingly (2-3 glass elements max per viewport)
- Consider `will-change: backdrop-filter` during animations only

---

#### 4. Gradient Mesh Backgrounds

**Definition**: Complex, multi-color gradients with organic blob shapes.

**Tools**:
- CSS: `background: radial-gradient()` layering
- SVG: Gradient mesh filters
- Canvas/WebGL: Shader-based gradients (Vanta.js)

**Modern Gradient System**:
```css
:root {
  /* Define gradient stops */
  --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --gradient-2: radial-gradient(circle at 20% 50%, #f093fb 0%, #f5576c 100%);
  --gradient-mesh:
    radial-gradient(at 27% 37%, hsla(215, 98%, 61%, 1) 0px, transparent 50%),
    radial-gradient(at 97% 21%, hsla(125, 98%, 72%, 1) 0px, transparent 50%),
    radial-gradient(at 52% 99%, hsla(354, 98%, 61%, 1) 0px, transparent 50%),
    radial-gradient(at 10% 29%, hsla(256, 96%, 67%, 1) 0px, transparent 50%);
}

.hero {
  background: var(--gradient-mesh);
  background-size: 400% 400%;
  animation: gradient-shift 15s ease infinite;
}

@keyframes gradient-shift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}
```

**Animated Gradients** (WebGL approach with Vanta.js):
- WAVES effect with custom colors
- CELLS effect for organic feel
- FOG for atmospheric backgrounds

**Related Skills**: `lightweight-3d-effects` (Vanta.js backgrounds)

---

#### 5. Neumorphism (Evolved)

**Status**: Declining but still used for specific contexts (iOS apps, dashboards).

**Modern Implementation** (Improved contrast):
```css
.neomorphic-card {
  background: #e0e5ec;
  box-shadow:
    /* Light shadow */
    8px 8px 16px rgba(163, 177, 198, 0.6),
    /* Dark shadow */
    -8px -8px 16px rgba(255, 255, 255, 0.8);

  border-radius: 16px;
  padding: 2rem;

  /* CRITICAL: Ensure contrast for accessibility */
  color: #1a1a1a; /* 11.6:1 contrast ratio */
}

/* Interactive state */
.neomorphic-card:active {
  box-shadow:
    inset 4px 4px 8px rgba(163, 177, 198, 0.6),
    inset -4px -4px 8px rgba(255, 255, 255, 0.8);
}
```

**Why It's Declining**: Accessibility concerns (low contrast), limited color palette, heavy shadows impact performance.

---

#### 6. Dark Mode as Default

**Trend**: Many sites now default to dark mode with light mode as alternative.

**Best Practices** (2024):
```css
/* Use system preference as default */
:root {
  color-scheme: light dark;
}

/* Dark mode first */
:root {
  --color-bg: #0a0a0a;
  --color-text: #e5e5e5;
  --color-accent: #3b82f6;
}

/* Light mode override */
@media (prefers-color-scheme: light) {
  :root {
    --color-bg: #ffffff;
    --color-text: #171717;
    --color-accent: #2563eb;
  }
}

/* Manual toggle support */
[data-theme="light"] {
  --color-bg: #ffffff;
  --color-text: #171717;
}

[data-theme="dark"] {
  --color-bg: #0a0a0a;
  --color-text: #e5e5e5;
}
```

**Color Adjustments for Dark Mode**:
- Reduce saturation by 10-20%
- Lower brightness for vibrant colors
- Use warmer blacks (#0a0a0a, not pure #000)
- Increase contrast for text (7:1+ ratio)

---

#### 7. Asymmetric Layouts

**Definition**: Breaking the grid for visual interest and hierarchy.

**Patterns**:
- Split-screen layouts (60/40, 70/30)
- Overlapping elements with z-index
- Diagonal sections
- Off-grid text positioning
- Broken grid systems

**CSS Grid Implementation**:
```css
.asymmetric-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 2rem;
}

.feature-1 {
  /* Spans 7 columns, offset by 1 */
  grid-column: 2 / 9;
  grid-row: 1;
}

.feature-2 {
  /* Overlaps with feature-1 */
  grid-column: 8 / 13;
  grid-row: 1;
  margin-top: 4rem; /* Offset vertically */
  z-index: 2;
}
```

**Examples**:
- Awwwards winners (70%+ use asymmetry)
- Design agency portfolios
- Product launch pages

---

### Interaction Trends

#### 8. Micro-Interactions Everywhere

**Definition**: Small, delightful animations that provide feedback and enhance usability.

**Categories & Examples**:

**a) Button Interactions**:
- Hover lift (transform: translateY(-2px))
- Press down (scale: 0.98)
- Ripple effect on click
- Color shift transitions

**b) Form Feedback**:
- Input focus animations (border glow)
- Success/error state transitions
- Character count with progress ring
- Password strength indicator

**c) Loading States**:
- Skeleton screens (better than spinners)
- Progress indicators
- Optimistic UI updates
- Staggered content reveals

**d) Navigation**:
- Hamburger to X transitions
- Dropdown reveals with stagger
- Active state indicators
- Scroll progress bars

**Implementation** (Framer Motion):
```jsx
const buttonVariants = {
  idle: { scale: 1, y: 0 },
  hover: { scale: 1.05, y: -2 },
  tap: { scale: 0.98, y: 0 }
};

<motion.button
  variants={buttonVariants}
  initial="idle"
  whileHover="hover"
  whileTap="tap"
  transition={{ type: "spring", stiffness: 400, damping: 17 }}
>
  Click me
</motion.button>
```

**Related Skills**: `ui-motion`, `react-spring-physics`, `animejs`

---

#### 9. Scroll-Driven Storytelling

**Definition**: Content reveals, transforms, and tells a story as the user scrolls.

**Techniques**:

**a) Pinned Sections with Scrubbing**:
```javascript
// Pin section while content scrubs through
gsap.to(".content", {
  scrollTrigger: {
    trigger: ".section",
    start: "top top",
    end: "+=3000", // 3000px of scroll
    scrub: 1,
    pin: true
  },
  opacity: 1,
  scale: 1.2
});
```

**b) Horizontal Scroll Galleries**:
- Card-based portfolios
- Timeline experiences
- Product showcases

**c) Parallax Layers**:
- Foreground, midground, background at different speeds
- 3D depth illusion
- Hero section parallax

**d) Progress Indicators**:
- Reading progress bars
- Section progress dots
- Animated SVG paths

**Examples**:
- Apple product pages (iPhone, MacBook)
- Stripe's annual reports
- Web agency showcases

**Related Skills**: `scroll-animation`, `locomotive-scroll`

---

#### 10. Cursor Effects & Custom Cursors

**Trend**: Custom cursors that enhance interaction and provide visual delight.

**Patterns**:

**a) Dot Follower**:
```javascript
const cursor = { x: 0, y: 0 };
const follower = { x: 0, y: 0 };

document.addEventListener('mousemove', (e) => {
  cursor.x = e.clientX;
  cursor.y = e.clientY;
});

function updateCursor() {
  // Smooth follow with easing
  follower.x += (cursor.x - follower.x) * 0.1;
  follower.y += (cursor.y - follower.y) * 0.1;

  cursorDot.style.transform = `translate(${follower.x}px, ${follower.y}px)`;
  requestAnimationFrame(updateCursor);
}
```

**b) Contextual Cursors**:
- "View" on images
- "Drag" on sliders
- "Play" on videos
- Magnetic attraction to buttons

**c) Blend Mode Cursors**:
```css
.cursor {
  mix-blend-mode: difference;
  /* Inverts colors underneath */
}
```

**Accessibility**:
- Hide on touch devices
- Respect `prefers-reduced-motion`
- Don't hide native cursor completely (layer on top)

---

#### 11. 3D Elements & WebGL

**Status**: Increasingly mainstream with improved performance and tooling.

**Use Cases**:
- Hero backgrounds (Vanta.js waves, particles)
- Product viewers (rotate, zoom, configure)
- Data visualization (3D charts, globes)
- Immersive experiences (games, virtual tours)

**Performance-First Approach**:
```javascript
// Lazy load 3D content
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      // Load 3D scene
      loadThreeJSScene();
      observer.unobserve(entry.target);
    }
  });
});

observer.observe(document.querySelector('.3d-container'));
```

**Lightweight 3D Options**:
- Vanta.js for backgrounds (uses Three.js)
- Zdog for flat-style 3D illustrations
- Spline for designer-friendly 3D

**Full 3D Engines**:
- Three.js for custom scenes
- React Three Fiber for React apps
- Babylon.js for physics and VR

**Related Skills**: `webgl-3d`, `react-3d`, `lightweight-3d-effects`

---

#### 12. Voice & Conversational UI

**Emerging Trend**: Voice commands and conversational interfaces.

**Patterns**:
- Voice search integration
- Chatbot interfaces (natural language)
- Voice-controlled navigation
- Audio feedback for interactions

**Implementation Considerations**:
- Web Speech API for voice input
- Text-to-speech for feedback
- Fallback to text input
- Accessibility: don't require voice-only

---

### Technical Trends

#### 13. Performance-First Design

**Core Web Vitals as Design Constraints**:

**LCP (Largest Contentful Paint) < 2.5s**:
- Optimize hero images (WebP/AVIF)
- Inline critical CSS
- Preload key resources
- Avoid layout shifts

**FID (First Input Delay) < 100ms**:
- Defer non-critical JavaScript
- Split code bundles
- Use passive event listeners
- Minimize main thread work

**CLS (Cumulative Layout Shift) < 0.1**:
- Reserve space for images (aspect-ratio)
- Avoid inserting content above existing content
- Use CSS transforms, not position changes

**Design Implications**:
- Avoid web fonts that cause FOIT/FOUT
- Use system fonts for body text
- Lazy load below-fold content
- Progressive enhancement mindset

---

#### 14. Component-Driven Design Systems

**Approach**: Design and build in reusable components.

**Tools**:
- Figma with variants and auto-layout
- Storybook for component documentation
- Design tokens (JSON format)
- Automated design-to-code (Figma plugins)

**Component Architecture**:
```
Design System/
├── Foundations/
│   ├── Colors (tokens)
│   ├── Typography (scales)
│   ├── Spacing (scales)
│   └── Shadows (elevation)
├── Components/
│   ├── Atoms (Button, Input, Icon)
│   ├── Molecules (SearchBar, Card)
│   ├── Organisms (Header, Footer)
│   └── Templates (PageLayout)
└── Patterns/
    ├── Navigation patterns
    ├── Form patterns
    └── Animation patterns
```

**Related Skills**: `animated-component-libraries`

---

#### 15. AI-Enhanced Design

**Applications**:

**a) Content Generation**:
- AI-written copy (with human editing)
- Image generation (Midjourney, DALL-E)
- Icon generation
- Design variations

**b) Personalization**:
- Dynamic layouts based on user behavior
- A/B testing with AI optimization
- Adaptive color schemes
- Content recommendations

**c) Accessibility**:
- AI-generated alt text
- Automatic color contrast adjustments
- Smart keyboard navigation
- Content simplification

**Implementation**:
- Edge functions for fast personalization
- Client-side ML models (TensorFlow.js)
- Privacy-preserving personalization

---

#### 16. Progressive Web Apps (PWAs)

**Status**: Mainstream adoption, especially for mobile-first products.

**Key Features**:
- Offline functionality
- Install to home screen
- Push notifications
- Background sync
- Native-like performance

**Design Considerations**:
- Mobile-first responsive design
- Touch-friendly interactions (44px+ targets)
- Offline-first content strategy
- Loading states for sync
- Native-feeling animations

---

### Color Trends

#### 17. Color Palette Trends (2024-2025)

**Trending Color Schemes**:

**a) High Contrast Duotone**:
- Black + bright accent (electric blue, hot pink, lime green)
- Minimal, punchy, attention-grabbing

**b) Muted Earth Tones**:
- Terracotta, sage green, warm beige
- Natural, calming, sustainable aesthetic

**c) Neon Gradients**:
- Bright, saturated gradient meshes
- Cyberpunk aesthetic
- Gaming and tech brands

**d) Monochromatic + Accent**:
- Single hue with varying lightness
- One bold accent color
- Sophisticated, cohesive

**Color Space Evolution**:
```css
/* OKLCH for perceptual uniformity */
:root {
  --color-primary: oklch(60% 0.2 250);
  /* 60% lightness, 0.2 chroma, 250° hue */

  /* Benefits: */
  /* - Perceptually uniform lightness */
  /* - Wider color gamut than RGB */
  /* - Easier to create accessible palettes */
}
```

---

### Typography Trends

#### 18. Variable Fonts Mainstream

**Adoption**: Major sites now using variable fonts by default.

**Popular Variable Fonts**:
- Inter (UI text)
- Space Grotesk (headlines)
- Recursive (code & UI)
- Fraunces (display serif)
- Outfit (geometric sans)

**Advantages**:
- Single file, multiple weights/styles
- Animation possibilities
- Fine-grained control (weight: 347)
- Smaller file size than multiple weights

**Implementation**:
```css
@font-face {
  font-family: 'Inter';
  src: url('Inter-Variable.woff2') format('woff2-variations');
  font-weight: 100 900;
  font-display: swap;
}

h1 {
  font-family: 'Inter', sans-serif;
  font-weight: 750; /* Any value 100-900 */
}
```

---

#### 19. Oversized Typography

**Trend**: Headlines at 100px-300px for desktop.

**Fluid Typography System**:
```css
:root {
  --font-size-base: clamp(1rem, 0.9rem + 0.5vw, 1.25rem);
  --font-size-lg: clamp(1.5rem, 1.2rem + 1.5vw, 2.5rem);
  --font-size-xl: clamp(2rem, 1.5rem + 2.5vw, 4rem);
  --font-size-2xl: clamp(3rem, 2rem + 5vw, 8rem);
  --font-size-3xl: clamp(4rem, 2rem + 10vw, 12rem);
}

h1 {
  font-size: var(--font-size-3xl);
  line-height: 0.95;
  letter-spacing: -0.03em;
}
```

**Design Considerations**:
- Tight line-height (0.9-1.0)
- Negative letter-spacing (-0.02 to -0.04em)
- Strong font weight (700-900)
- Responsive scaling with clamp()

---

### Layout Trends

#### 20. Broken Grid Layouts

**Definition**: Intentionally breaking traditional grid systems for visual interest.

**Techniques**:
- Overlapping elements
- Off-grid positioning
- Diagonal layouts
- Negative space as design element
- Z-axis layering

**CSS Grid + Subgrid**:
```css
.parent-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 2rem;
}

.child {
  /* Subgrid inherits parent's columns */
  display: grid;
  grid-template-columns: subgrid;
  grid-column: span 6;
}
```

---

#### 21. Single-Page Experiences

**Trend**: Entire site on one scrollable page.

**Patterns**:
- Section-based navigation (anchor links)
- Full-screen sections
- Scroll-driven reveals
- Smooth scrolling between sections

**Benefits**:
- Cohesive narrative flow
- No page load transitions
- Mobile-friendly (swipe to scroll)
- Performance (single bundle)

**Challenges**:
- SEO (use meaningful sections with h2-h6)
- Deep linking (use hash routing)
- Back button behavior
- Large bundle size

---

### Emerging & Experimental

#### 22. AI-Generated Visuals

**Tools**:
- Midjourney for illustrations
- DALL-E 3 for specific images
- Stable Diffusion for customization

**Use Cases**:
- Hero backgrounds
- Blog post headers
- Icon generation
- Abstract patterns

**Ethical Considerations**:
- Disclose AI-generated content
- Review for bias and appropriateness
- Ensure licensing rights
- Don't replace human designers for key visuals

---

#### 23. Web3 Design Patterns

**Characteristics**:
- Wallet connection UIs
- NFT galleries
- Token-gated content
- Blockchain transaction states
- Decentralized identity

**Design Challenges**:
- Explaining complex concepts simply
- Transaction loading states (slow blockchains)
- Error handling (failed transactions)
- Gas fee transparency

---

#### 24. Spatial Computing & 3D Interfaces

**Future Trend**: Preparing for AR/VR mainstream adoption.

**Patterns**:
- Depth-based layering
- 3D navigation
- Gesture controls
- Spatial audio cues

**Implementation**: WebXR API, A-Frame, Babylon.js

**Related Skills**: `aframe-webxr`, `babylonjs-engine`

---

### Anti-Trends (What to Avoid)

#### Declining Patterns:

1. **Carousels**: Low engagement, poor accessibility
2. **Auto-Playing Videos**: Annoying, data-hungry
3. **Hamburger Menus Only**: Hide navigation
4. **Stock Photos**: Generic, unauthentic
5. **Neumorphism**: Accessibility issues
6. **Long Scroll Animations**: Frustrating on mobile
7. **Overuse of Parallax**: Motion sickness, poor performance
8. **Chatbots as First Contact**: Often unhelpful, annoying
9. **Cookie Banners That Block Content**: Poor UX
10. **Infinite Scroll Without Pagination**: SEO and UX issues

---

### Resources & Inspiration

**Award Sites**:
- Awwwards.com (daily winners)
- CSS Design Awards
- The FWA

**Trend Reports**:
- Webflow's Annual Design Report
- Dribbble Year in Review
- Behance Featured Projects

**Design Systems**:
- Material Design 3 (Google)
- Fluent 2 (Microsoft)
- Polaris (Shopify)
- Carbon (IBM)

**Tools**:
- Figma (design)
- Webflow (visual development)
- Framer (design + code)
- Spline (3D design)

---

### Forecasts (2025+)

**Emerging Trends to Watch**:

1. **AI-Personalized Experiences**: Every user sees a unique layout
2. **Voice-First Interfaces**: Beyond chatbots to full voice navigation
3. **Spatial Web**: 3D interfaces for AR/VR headsets
4. **Sustainability Indicators**: Carbon footprint of web experiences
5. **Ethical Design Standards**: Privacy, accessibility, inclusivity as default
6. **Real-Time Collaboration**: Multiplayer web experiences
7. **Generative Art**: Unique visuals for each visitor
8. **Biometric Interfaces**: Face/voice recognition for auth and personalization

**Technology Shifts**:
- WebGPU mainstream adoption (faster 3D)
- Container queries (component-based responsive design)
- View Transitions API (smooth SPA transitions)
- CSS Houdini (custom CSS magic)

---

*Last updated: 2024*
*Review quarterly for updates*

---

## Micro-Interaction Patterns Catalog

### Overview

Comprehensive catalog of micro-interactions for modern web interfaces. Each pattern includes implementation code, accessibility considerations, and performance notes.

Micro-interactions are small, purposeful animations that provide feedback, guide users, and enhance perceived performance.

---

### Table of Contents

1. [Button Interactions](#button-interactions)
2. [Form & Input Interactions](#form--input-interactions)
3. [Loading States](#loading-states)
4. [Navigation Interactions](#navigation-interactions)
5. [Hover Effects](#hover-effects)
6. [Toggle & Switch Interactions](#toggle--switch-interactions)
7. [Card Interactions](#card-interactions)
8. [Scroll Interactions](#scroll-interactions)
9. [Modal & Dialog Interactions](#modal--dialog-interactions)
10. [Toast & Notification Interactions](#toast--notification-interactions)

---

### Button Interactions

#### 1.1 Hover Lift

**Effect**: Button lifts up slightly on hover, creating depth.

**Implementation** (CSS):
```css
.button-lift {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.button-lift:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.button-lift:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
```

**Framer Motion**:
```jsx
<motion.button
  whileHover={{ y: -2, boxShadow: "0 4px 12px rgba(0,0,0,0.15)" }}
  whileTap={{ y: 0, boxShadow: "0 2px 4px rgba(0,0,0,0.1)" }}
  transition={{ type: "spring", stiffness: 400, damping: 17 }}
>
  Click me
</motion.button>
```

**Accessibility**: Preserve for keyboard focus states.

---

#### 1.2 Ripple Effect

**Effect**: Material Design-style ripple on click.

**Implementation** (JavaScript):
```javascript
function createRipple(event) {
  const button = event.currentTarget;
  const ripple = document.createElement('span');
  const rect = button.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);
  const x = event.clientX - rect.left - size / 2;
  const y = event.clientY - rect.top - size / 2;

  ripple.style.width = ripple.style.height = `${size}px`;
  ripple.style.left = `${x}px`;
  ripple.style.top = `${y}px`;
  ripple.classList.add('ripple');

  button.appendChild(ripple);

  setTimeout(() => ripple.remove(), 600);
}

document.querySelectorAll('.button-ripple').forEach(button => {
  button.addEventListener('click', createRipple);
});
```

**CSS**:
```css
.button-ripple {
  position: relative;
  overflow: hidden;
}

.ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.6);
  transform: scale(0);
  animation: ripple-animation 0.6s ease-out;
}

@keyframes ripple-animation {
  to {
    transform: scale(4);
    opacity: 0;
  }
}
```

**Performance**: Use `will-change: transform` sparingly.

---

#### 1.3 Magnetic Button

**Effect**: Button magnetically attracts cursor on proximity.

**Implementation** (GSAP):
```javascript
const button = document.querySelector('.magnetic-button');
const magneticStrength = 0.3;

button.addEventListener('mousemove', (e) => {
  const rect = button.getBoundingClientRect();
  const centerX = rect.left + rect.width / 2;
  const centerY = rect.top + rect.height / 2;
  const distanceX = (e.clientX - centerX) * magneticStrength;
  const distanceY = (e.clientY - centerY) * magneticStrength;

  gsap.to(button, {
    x: distanceX,
    y: distanceY,
    duration: 0.3,
    ease: "power2.out"
  });
});

button.addEventListener('mouseleave', () => {
  gsap.to(button, {
    x: 0,
    y: 0,
    duration: 0.5,
    ease: "elastic.out(1, 0.3)"
  });
});
```

**Accessibility**: Disable on mobile/touch devices.

---

#### 1.4 Loading Button State

**Effect**: Button morphs into loading spinner.

**Framer Motion**:
```jsx
function LoadingButton() {
  const [isLoading, setIsLoading] = useState(false);

  return (
    <motion.button
      onClick={() => setIsLoading(true)}
      animate={isLoading ? "loading" : "idle"}
      disabled={isLoading}
      style={{ position: 'relative', overflow: 'hidden' }}
    >
      <motion.span
        variants={{
          idle: { opacity: 1 },
          loading: { opacity: 0 }
        }}
      >
        Submit
      </motion.span>

      <motion.div
        className="spinner"
        variants={{
          idle: { opacity: 0, scale: 0 },
          loading: { opacity: 1, scale: 1 }
        }}
        style={{ position: 'absolute', inset: 0 }}
      >
        <Spinner />
      </motion.div>
    </motion.button>
  );
}
```

**Accessibility**: Announce loading state to screen readers.

---

### Form & Input Interactions

#### 2.1 Floating Label

**Effect**: Label floats up when input is focused or filled.

**Implementation**:
```css
.input-wrapper {
  position: relative;
  margin: 1rem 0;
}

.input-field {
  width: 100%;
  padding: 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
}

.input-field:focus {
  outline: none;
  border-color: #3b82f6;
}

.input-label {
  position: absolute;
  left: 1rem;
  top: 1rem;
  pointer-events: none;
  transition: all 0.2s ease;
  color: #666;
}

.input-field:focus + .input-label,
.input-field:not(:placeholder-shown) + .input-label {
  top: -0.5rem;
  left: 0.75rem;
  font-size: 0.75rem;
  background: white;
  padding: 0 0.25rem;
  color: #3b82f6;
}
```

**HTML**:
```html
<div class="input-wrapper">
  <input
    class="input-field"
    type="text"
    placeholder=" "
    required
  />
  <label class="input-label">Email address</label>
</div>
```

---

#### 2.2 Input Validation Feedback

**Effect**: Instant feedback on validation state.

**React + Framer Motion**:
```jsx
function ValidatedInput({ label, validator }) {
  const [value, setValue] = useState('');
  const [isValid, setIsValid] = useState(null);

  const handleChange = (e) => {
    const newValue = e.target.value;
    setValue(newValue);
    setIsValid(validator(newValue));
  };

  return (
    <div className="input-wrapper">
      <motion.input
        value={value}
        onChange={handleChange}
        animate={{
          borderColor: isValid === null ? '#ccc' :
                      isValid ? '#10b981' : '#ef4444'
        }}
        transition={{ duration: 0.2 }}
      />

      <AnimatePresence>
        {isValid === true && (
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
            className="success-icon"
          >
            ✓
          </motion.div>
        )}

        {isValid === false && (
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
            className="error-icon"
          >
            ✗
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
```

**Accessibility**: Provide error messages, not just icons.

---

#### 2.3 Password Strength Indicator

**Effect**: Visual indicator of password strength.

**Implementation**:
```jsx
function PasswordStrengthIndicator({ password }) {
  const strength = calculateStrength(password);

  const variants = {
    weak: { width: '33%', backgroundColor: '#ef4444' },
    medium: { width: '66%', backgroundColor: '#f59e0b' },
    strong: { width: '100%', backgroundColor: '#10b981' }
  };

  return (
    <div className="strength-bar-container">
      <motion.div
        className="strength-bar"
        variants={variants}
        animate={strength}
        transition={{ duration: 0.3 }}
      />
      <p className="strength-label">
        Password strength: <strong>{strength}</strong>
      </p>
    </div>
  );
}

function calculateStrength(password) {
  if (password.length < 6) return 'weak';
  if (password.length < 10) return 'medium';
  return 'strong';
}
```

---

#### 2.4 Character Count with Progress

**Effect**: Shows remaining characters with visual indicator.

**Implementation**:
```jsx
function TextareaWithCount({ maxLength = 280 }) {
  const [text, setText] = useState('');
  const remaining = maxLength - text.length;
  const percentage = (text.length / maxLength) * 100;

  return (
    <div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        maxLength={maxLength}
      />

      <div className="count-indicator">
        <motion.svg
          width="40"
          height="40"
          style={{ transform: 'rotate(-90deg)' }}
        >
          <circle
            cx="20"
            cy="20"
            r="16"
            stroke="#e5e7eb"
            strokeWidth="3"
            fill="none"
          />
          <motion.circle
            cx="20"
            cy="20"
            r="16"
            stroke={remaining < 20 ? '#ef4444' : '#3b82f6'}
            strokeWidth="3"
            fill="none"
            strokeDasharray={`${2 * Math.PI * 16}`}
            animate={{
              strokeDashoffset: (1 - percentage / 100) * (2 * Math.PI * 16)
            }}
          />
        </motion.svg>
        <span className="count-text">{remaining}</span>
      </div>
    </div>
  );
}
```

---

### Loading States

#### 3.1 Skeleton Screen

**Effect**: Content placeholder that mimics layout.

**Implementation**:
```css
.skeleton {
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 50%,
    #f0f0f0 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
  border-radius: 4px;
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.skeleton-text {
  height: 1rem;
  margin-bottom: 0.5rem;
}

.skeleton-title {
  height: 2rem;
  width: 60%;
  margin-bottom: 1rem;
}

.skeleton-image {
  width: 100%;
  aspect-ratio: 16 / 9;
}
```

**React Component**:
```jsx
function SkeletonCard() {
  return (
    <div className="card">
      <div className="skeleton skeleton-image" />
      <div className="skeleton skeleton-title" />
      <div className="skeleton skeleton-text" />
      <div className="skeleton skeleton-text" style={{ width: '80%' }} />
    </div>
  );
}
```

---

#### 3.2 Progress Bar

**Effect**: Linear progress indicator.

**Framer Motion**:
```jsx
function ProgressBar({ progress }) {
  return (
    <div className="progress-container">
      <motion.div
        className="progress-bar"
        initial={{ width: 0 }}
        animate={{ width: `${progress}%` }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      />
    </div>
  );
}
```

**CSS**:
```css
.progress-container {
  width: 100%;
  height: 4px;
  background: #e5e7eb;
  border-radius: 9999px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  border-radius: 9999px;
}
```

---

#### 3.3 Spinner

**Effect**: Rotating loading indicator.

**CSS**:
```css
.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(59, 130, 246, 0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

**Framer Motion (Advanced)**:
```jsx
function Spinner() {
  return (
    <motion.div
      className="spinner-container"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
    >
      <motion.div
        className="spinner"
        animate={{ rotate: 360 }}
        transition={{
          duration: 1,
          repeat: Infinity,
          ease: "linear"
        }}
      />
    </motion.div>
  );
}
```

---

### Navigation Interactions

#### 4.1 Hamburger Menu Animation

**Effect**: Hamburger transforms into X on click.

**CSS**:
```css
.hamburger {
  width: 30px;
  height: 20px;
  position: relative;
  cursor: pointer;
}

.hamburger span {
  display: block;
  position: absolute;
  height: 3px;
  width: 100%;
  background: #333;
  border-radius: 3px;
  transition: all 0.3s ease;
}

.hamburger span:nth-child(1) { top: 0; }
.hamburger span:nth-child(2) { top: 50%; transform: translateY(-50%); }
.hamburger span:nth-child(3) { bottom: 0; }

.hamburger.active span:nth-child(1) {
  top: 50%;
  transform: translateY(-50%) rotate(45deg);
}

.hamburger.active span:nth-child(2) {
  opacity: 0;
}

.hamburger.active span:nth-child(3) {
  bottom: 50%;
  transform: translateY(50%) rotate(-45deg);
}
```

---

#### 4.2 Dropdown Menu Reveal

**Effect**: Dropdown slides down with stagger.

**Framer Motion**:
```jsx
const menuVariants = {
  closed: {
    opacity: 0,
    y: -20,
    transition: { staggerChildren: 0.05, staggerDirection: -1 }
  },
  open: {
    opacity: 1,
    y: 0,
    transition: { staggerChildren: 0.07, delayChildren: 0.1 }
  }
};

const itemVariants = {
  closed: { opacity: 0, x: -20 },
  open: { opacity: 1, x: 0 }
};

function DropdownMenu({ isOpen }) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.ul
          className="dropdown"
          variants={menuVariants}
          initial="closed"
          animate="open"
          exit="closed"
        >
          {items.map((item) => (
            <motion.li key={item} variants={itemVariants}>
              {item}
            </motion.li>
          ))}
        </motion.ul>
      )}
    </AnimatePresence>
  );
}
```

---

#### 4.3 Active Link Indicator

**Effect**: Animated underline follows active link.

**Framer Motion**:
```jsx
function TabNavigation() {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <nav className="tabs">
      {tabs.map((tab, index) => (
        <button
          key={tab}
          onClick={() => setActiveTab(index)}
          className={activeTab === index ? 'active' : ''}
        >
          {tab}
          {activeTab === index && (
            <motion.div
              className="active-indicator"
              layoutId="activeTab"
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            />
          )}
        </button>
      ))}
    </nav>
  );
}
```

**CSS**:
```css
.tabs {
  display: flex;
  gap: 2rem;
  border-bottom: 2px solid #e5e7eb;
}

.tabs button {
  position: relative;
  padding: 1rem 0;
  background: none;
  border: none;
  cursor: pointer;
}

.active-indicator {
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: #3b82f6;
}
```

---

### Hover Effects

#### 5.1 Image Zoom on Hover

**Effect**: Image scales up slightly on hover.

**CSS**:
```css
.image-container {
  overflow: hidden;
  border-radius: 8px;
}

.image-container img {
  transition: transform 0.3s ease;
  display: block;
  width: 100%;
}

.image-container:hover img {
  transform: scale(1.05);
}
```

---

#### 5.2 Tilt Effect

**Effect**: Card tilts based on mouse position.

**Vanilla-Tilt**:
```javascript
VanillaTilt.init(document.querySelectorAll(".tilt-card"), {
  max: 15,
  speed: 400,
  glare: true,
  "max-glare": 0.3
});
```

**Manual Implementation**:
```javascript
const card = document.querySelector('.tilt-card');

card.addEventListener('mousemove', (e) => {
  const rect = card.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  const centerX = rect.width / 2;
  const centerY = rect.height / 2;

  const rotateX = (y - centerY) / 10;
  const rotateY = (centerX - x) / 10;

  card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
});

card.addEventListener('mouseleave', () => {
  card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0)';
});
```

---

#### 5.3 Reveal on Hover

**Effect**: Content reveals on hover with slide/fade.

**CSS**:
```css
.card {
  position: relative;
  overflow: hidden;
}

.card-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transform: translateY(100%);
  transition: all 0.3s ease;
}

.card:hover .card-overlay {
  opacity: 1;
  transform: translateY(0);
}
```

---

### Toggle & Switch Interactions

#### 6.1 Toggle Switch

**Effect**: Smooth toggle with spring animation.

**Framer Motion**:
```jsx
function ToggleSwitch({ enabled, setEnabled }) {
  return (
    <motion.div
      className="switch"
      data-enabled={enabled}
      onClick={() => setEnabled(!enabled)}
      animate={{ backgroundColor: enabled ? '#3b82f6' : '#d1d5db' }}
    >
      <motion.div
        className="switch-handle"
        layout
        transition={{ type: "spring", stiffness: 500, damping: 30 }}
        style={{ justifyContent: enabled ? 'flex-end' : 'flex-start' }}
      />
    </motion.div>
  );
}
```

**CSS**:
```css
.switch {
  width: 50px;
  height: 28px;
  border-radius: 14px;
  padding: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.switch-handle {
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
```

---

### Card Interactions

#### 7.1 Card Expand

**Effect**: Card expands to full screen on click.

**Framer Motion with `layout`**:
```jsx
function ExpandableCard() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <motion.div
      layout
      className={isExpanded ? 'card-expanded' : 'card'}
      onClick={() => setIsExpanded(!isExpanded)}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
    >
      <motion.h2 layout="position">Title</motion.h2>
      <motion.p layout="position">Content</motion.p>

      {isExpanded && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          Additional content...
        </motion.div>
      )}
    </motion.div>
  );
}
```

---

### Scroll Interactions

#### 8.1 Fade In on Scroll

**Effect**: Elements fade in as they enter viewport.

**Framer Motion + `useInView`**:
```jsx
function FadeInSection({ children }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.3 });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6 }}
    >
      {children}
    </motion.div>
  );
}
```

---

#### 8.2 Scroll Progress Indicator

**Effect**: Shows reading progress.

**Implementation**:
```jsx
function ScrollProgress() {
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const updateProgress = () => {
      const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = (window.scrollY / scrollHeight) * 100;
      setScrollProgress(progress);
    };

    window.addEventListener('scroll', updateProgress);
    return () => window.removeEventListener('scroll', updateProgress);
  }, []);

  return (
    <motion.div
      className="progress-bar"
      style={{ scaleX: scrollProgress / 100, transformOrigin: 'left' }}
    />
  );
}
```

---

### Modal & Dialog Interactions

#### 9.1 Modal Fade & Scale

**Effect**: Modal fades in and scales up.

**Framer Motion**:
```jsx
function Modal({ isOpen, onClose, children }) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            className="modal-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          <motion.div
            className="modal"
            initial={{ opacity: 0, scale: 0.8, y: 50 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 50 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
          >
            {children}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

**Accessibility**: Trap focus, close on Escape key, focus first element.

---

### Toast & Notification Interactions

#### 10.1 Toast Notification

**Effect**: Toast slides in from top/bottom with auto-dismiss.

**Framer Motion**:
```jsx
function Toast({ message, type, onDismiss }) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 3000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  return (
    <motion.div
      className={`toast toast-${type}`}
      initial={{ opacity: 0, y: -50, scale: 0.8 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -50, scale: 0.8 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
    >
      {message}
      <button onClick={onDismiss}>×</button>
    </motion.div>
  );
}
```

---

### Accessibility Checklist

For all micro-interactions:

- [ ] **Respect `prefers-reduced-motion`**: Disable or simplify animations
- [ ] **Keyboard accessible**: All interactions work without mouse
- [ ] **Focus indicators**: Visible focus states
- [ ] **Screen reader friendly**: Announce state changes with `aria-live`
- [ ] **Touch targets**: Minimum 44x44px for mobile
- [ ] **Escape key**: Close modals/overlays
- [ ] **Loading states**: Indicate when actions are processing
- [ ] **Error states**: Clear error messages, not just visual indicators

---

### Performance Checklist

- [ ] **GPU-accelerated properties**: Use `transform` and `opacity` only
- [ ] **Avoid layout thrash**: Batch DOM reads/writes
- [ ] **RequestAnimationFrame**: For JavaScript animations
- [ ] **Will-change sparingly**: Only during active animations
- [ ] **Debounce scroll/resize**: Avoid excessive repaints
- [ ] **Lazy load**: Defer non-critical animations
- [ ] **Test on low-end devices**: Ensure 60 FPS

---

*This catalog is a living document. Patterns are updated based on modern web standards and user research.*
