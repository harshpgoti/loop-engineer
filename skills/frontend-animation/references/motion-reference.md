# Motion Library Reference

Deep-dive API and spring-physics reference for the Motion library (motion.dev).

---

## Motion.dev Complete API Reference

Complete reference for Motion.dev (formerly Framer Motion) components, hooks, and utilities.

---

### Core Components (React)

#### motion.element

Every HTML and SVG element has a motion component: `motion.div`, `motion.button`, `motion.svg`, etc.

```tsx
import { motion } from "motion/react"

<motion.div
  // Animation props
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  exit={{ opacity: 0 }}

  // Transition
  transition={{ duration: 0.5, ease: "easeOut" }}

  // Gestures
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
  whileFocus={{ outline: "2px solid blue" }}
  whileInView={{ opacity: 1 }}

  // Drag
  drag
  dragConstraints={{ left: 0, right: 300 }}
  dragElastic={0.2}

  // Layout
  layout
  layoutId="unique-id"

  // Style
  style={{ x: motionValue }}
/>
```

---

### Animation Props

#### initial
Starting state before component mounts.

```tsx
<motion.div initial={{ opacity: 0, y: 20 }} />
<motion.div initial={false} /> // Disable initial animation
<motion.div initial="hidden" variants={variants} />
```

#### animate
Target state to animate to.

```tsx
<motion.div animate={{ opacity: 1, y: 0 }} />
<motion.div animate="visible" variants={variants} />
<motion.div animate={isOpen ? "open" : "closed"} />
```

#### exit
State when component unmounts (requires AnimatePresence).

```tsx
<AnimatePresence>
  {isVisible && (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    />
  )}
</AnimatePresence>
```

#### transition
Controls animation behavior.

```tsx
<motion.div
  animate={{ x: 100 }}
  transition={{
    duration: 0.5,
    delay: 0.2,
    ease: "easeOut",
    type: "spring",
    stiffness: 300,
    damping: 20,
  }}
/>
```

**Transition Types:**
- `tween` (default) - Duration-based
- `spring` - Physics-based
- `inertia` - Momentum-based

**Easing:**
- `"linear"`, `"easeIn"`, `"easeOut"`, `"easeInOut"`
- Custom: `[0.17, 0.67, 0.83, 0.67]` (cubic bezier)

---

### Gesture Props

#### whileHover
Animation state during hover.

```tsx
<motion.button
  whileHover={{
    scale: 1.1,
    backgroundColor: "#3b82f6",
  }}
/>
```

#### whileTap
Animation state during tap/click.

```tsx
<motion.button
  whileTap={{ scale: 0.95 }}
/>
```

#### whileFocus
Animation state during keyboard focus.

```tsx
<motion.button
  whileFocus={{
    outline: "2px solid blue",
    outlineOffset: "2px",
  }}
/>
```

#### whileInView
Animation state when element enters viewport.

```tsx
<motion.div
  whileInView={{ opacity: 1 }}
  viewport={{
    once: true, // Only animate once
    amount: 0.3, // Trigger when 30% visible
    margin: "0px 0px -100px 0px", // Offset trigger
  }}
/>
```

#### whileDrag
Animation state while dragging.

```tsx
<motion.div
  drag
  whileDrag={{ scale: 1.1, cursor: "grabbing" }}
/>
```

---

### Drag Props

#### drag
Enable dragging.

```tsx
<motion.div drag /> // Both x and y
<motion.div drag="x" /> // Horizontal only
<motion.div drag="y" /> // Vertical only
```

#### dragConstraints
Limit drag area.

```tsx
// Pixel values
<motion.div
  drag
  dragConstraints={{ left: 0, right: 300, top: 0, bottom: 300 }}
/>

// Ref to parent
const constraintsRef = useRef(null)
<div ref={constraintsRef}>
  <motion.div drag dragConstraints={constraintsRef} />
</div>
```

#### dragElastic
Resistance when dragging outside constraints.

```tsx
<motion.div drag dragElastic={0.2} /> // Low resistance
<motion.div drag dragElastic={0} /> // No overscroll
<motion.div drag dragElastic={1} /> // Full freedom
```

#### dragMomentum
Enable momentum scrolling on release.

```tsx
<motion.div drag dragMomentum={true} />
```

---

### Layout Animations

#### layout
Automatically animate layout changes (position, size).

```tsx
<motion.div layout />
```

**How it works:**
- Uses FLIP technique (First, Last, Invert, Play)
- Animates transforms, not actual layout properties
- Very performant

#### layoutId
Shared layout between different components.

```tsx
// Component A
<motion.div layoutId="shared-element" />

// Component B (different location)
<motion.div layoutId="shared-element" /> // Morphs between them
```

---

### Variants

Define animation states for orchestration.

```tsx
const variants = {
  hidden: {
    opacity: 0,
    y: 20,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      staggerChildren: 0.1, // Delay between children
      delayChildren: 0.2, // Delay before first child
    },
  },
}

<motion.ul
  variants={variants}
  initial="hidden"
  animate="visible"
>
  {items.map(item => (
    <motion.li variants={itemVariants} /> // Inherits parent state
  ))}
</motion.ul>
```

---

### Hooks

#### useMotionValue
Create a motion value (doesn't trigger re-renders).

```tsx
import { useMotionValue } from "motion/react"

const x = useMotionValue(0)
x.set(100) // Update value
const current = x.get() // Read value
```

#### useTransform
Transform one motion value into another.

```tsx
import { useTransform } from "motion/react"

const x = useMotionValue(0)
const opacity = useTransform(x, [0, 100], [0, 1])
const scale = useTransform(x, [0, 100], [0.5, 1])
```

#### useScroll
Track scroll progress.

```tsx
import { useScroll } from "motion/react"

const { scrollYProgress, scrollY } = useScroll({
  target: ref, // Element to track
  offset: ["start start", "end start"], // When to start/end
})

// scrollY: absolute pixels
// scrollYProgress: 0 to 1
```

#### useSpring
Create spring-animated motion value.

```tsx
import { useSpring } from "motion/react"

const x = useMotionValue(0)
const springX = useSpring(x, { stiffness: 300, damping: 20 })
```

#### useInView
Detect when element is in viewport.

```tsx
import { useInView } from "motion/react"

const ref = useRef(null)
const isInView = useInView(ref, {
  once: true,
  amount: 0.3,
})

return <div ref={ref}>{isInView && "In view!"}</div>
```

#### useAnimate
Imperative animations.

```tsx
import { useAnimate } from "motion/react"

const [scope, animate] = useAnimate()

const handleClick = () => {
  animate(scope.current, { x: 100 }, { duration: 0.5 })
}

return <div ref={scope} onClick={handleClick} />
```

#### useReducedMotion
Detect user's motion preference.

```tsx
import { useReducedMotion } from "motion/react"

const shouldReduceMotion = useReducedMotion()

return (
  <motion.div
    animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
  />
)
```

---

### Utilities

#### AnimatePresence
Enable exit animations.

```tsx
import { AnimatePresence } from "motion/react"

<AnimatePresence mode="wait">
  {isVisible && (
    <motion.div
      key="item"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    />
  )}
</AnimatePresence>
```

**Modes:**
- `sync` (default) - Exit and enter simultaneously
- `wait` - Wait for exit before entering new
- `popLayout` - Exiting elements don't affect layout

#### MotionConfig
Set default transition for all children.

```tsx
import { MotionConfig } from "motion/react"

<MotionConfig transition={{ duration: 0.5, ease: "easeOut" }}>
  <motion.div animate={{ x: 100 }} /> // Uses default
  <motion.div animate={{ y: 100 }} /> // Uses default
</MotionConfig>
```

---

### Vanilla JavaScript API

#### animate()
Animate any element.

```javascript
import { animate } from "motion"

animate("#element", { x: 100, opacity: 1 }, { duration: 1 })
```

#### stagger()
Stagger animations for multiple elements.

```javascript
import { animate, stagger } from "motion"

animate("li", { opacity: 1 }, { delay: stagger(0.1) })
```

#### scroll()
Scroll-linked animations.

```javascript
import { scroll } from "motion"

scroll(({ y }) => {
  animate("#element", { opacity: y.progress })
})
```

#### inView()
Intersection Observer wrapper.

```javascript
import { inView } from "motion"

inView("#element", ({ target }) => {
  animate(target, { opacity: 1 })
})
```

---

### TypeScript Types

```tsx
import { motion, AnimationProps, Variant, Transition } from "motion/react"

const variants: { [key: string]: Variant } = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
}

const transition: Transition = {
  duration: 0.5,
  ease: "easeOut",
}
```

---

### Performance Tips

1. **Use transforms** - `x`, `y`, `scale`, `rotate` (GPU-accelerated)
2. **Avoid layout properties** - `width`, `height`, `top`, `left`
3. **Use will-change** - Hint browser for optimization
4. **Use layout prop** - For size/position changes
5. **Limit simultaneous animations** - Max 10-15 elements
6. **Use variants** - Better performance than inline props
7. **Respect reduced motion** - Honor user preferences

---

### Common Patterns

#### Fade In
```tsx
initial={{ opacity: 0 }}
animate={{ opacity: 1 }}
transition={{ duration: 0.5 }}
```

#### Slide Up
```tsx
initial={{ opacity: 0, y: 20 }}
animate={{ opacity: 1, y: 0 }}
transition={{ duration: 0.6, ease: "easeOut" }}
```

#### Scale Up
```tsx
initial={{ scale: 0.8, opacity: 0 }}
animate={{ scale: 1, opacity: 1 }}
transition={{ type: "spring", stiffness: 300, damping: 20 }}
```

#### Stagger Children
```tsx
variants={{
  visible: {
    transition: { staggerChildren: 0.1 }
  }
}}
```

#### Exit Animation
```tsx
<AnimatePresence>
  {isVisible && (
    <motion.div exit={{ opacity: 0, scale: 0.8 }} />
  )}
</AnimatePresence>
```

---

## Spring Physics Guide

Understanding and tuning spring animations in Motion.dev for natural, organic motion.

---

### What Are Spring Animations?

Springs simulate real-world physics:
- **Natural bounce** - Like a physical spring
- **No fixed duration** - Animation completes when physics settle
- **Responsive** - Adapts to interrupted animations
- **Organic feel** - More lifelike than tween animations

**When to use:**
- Gestures (drag, hover, tap)
- Interactive elements
- Layout animations
- Any animation that should feel "alive"

**When NOT to use:**
- Fixed-duration requirements (e.g., timed with audio)
- Very long distances (can be slow)
- Simple fade-ins (tween is simpler)

---

### Basic Spring Syntax

```tsx
<motion.div
  animate={{ x: 100 }}
  transition={{
    type: "spring",
    stiffness: 300,
    damping: 20,
  }}
/>
```

---

### Spring Parameters

#### stiffness
How "tight" the spring is. Higher = faster, snappier.

```tsx
stiffness: 100  // Slow, gentle
stiffness: 300  // Default, balanced
stiffness: 500  // Fast, snappy
stiffness: 1000 // Very fast, rigid
```

**Recommendations:**
- **100-200** - Soft, gentle (modals, large elements)
- **300-400** - Standard (buttons, cards, most UI)
- **500-700** - Snappy (micro-interactions, toggles)
- **800-1000** - Very responsive (cursor tracking, instant feedback)

#### damping
Resistance, controls oscillation. Lower = more bounce.

```tsx
damping: 10  // Very bouncy
damping: 20  // Default, some bounce
damping: 30  // Minimal bounce
damping: 50  // No bounce (critically damped)
```

**Recommendations:**
- **10-15** - Playful, bouncy (fun brands, games)
- **20-25** - Balanced, professional (most applications)
- **30-40** - Subtle bounce (serious, professional)
- **50+** - No bounce (when you need precision)

#### mass
"Weight" of the animated object. Higher = slower, heavier feel.

```tsx
mass: 0.5  // Light, quick
mass: 1    // Default
mass: 2    // Heavy, slow
mass: 5    // Very heavy
```

**Use cases:**
- **0.5** - Small, light elements (icons, badges)
- **1** - Standard elements (buttons, cards)
- **2** - Large elements (modals, panels)
- **3-5** - Very large elements (full-screen overlays)

#### velocity
Initial velocity (pixels per second).

```tsx
velocity: 0     // Start from rest
velocity: 100   // Moving towards target
velocity: -100  // Moving away from target
```

**Use cases:**
- Inherit velocity from drag/gesture
- Create momentum effects
- Chain animations smoothly

---

### Common Spring Presets

#### Gentle (Default)
Balanced, professional feel.

```tsx
transition={{
  type: "spring",
  stiffness: 300,
  damping: 20,
  mass: 1,
}}
```

#### Snappy
Fast, responsive, modern.

```tsx
transition={{
  type: "spring",
  stiffness: 500,
  damping: 25,
  mass: 0.8,
}}
```

#### Bouncy
Playful, fun, energetic.

```tsx
transition={{
  type: "spring",
  stiffness: 400,
  damping: 12,
  mass: 1,
}}
```

#### Slow & Smooth
Elegant, luxurious.

```tsx
transition={{
  type: "spring",
  stiffness: 100,
  damping: 30,
  mass: 2,
}}
```

#### Critically Damped
No bounce, precise.

```tsx
transition={{
  type: "spring",
  stiffness: 300,
  damping: 50,
  mass: 1,
}}
```

---

### Real-World Examples

#### Button Hover
Fast, responsive feedback.

```tsx
<motion.button
  whileHover={{ scale: 1.05 }}
  transition={{
    type: "spring",
    stiffness: 400,
    damping: 20,
  }}
/>
```

#### Modal Entrance
Soft, gentle appearance.

```tsx
<motion.div
  initial={{ opacity: 0, scale: 0.9 }}
  animate={{ opacity: 1, scale: 1 }}
  transition={{
    type: "spring",
    stiffness: 200,
    damping: 25,
    mass: 1.5,
  }}
/>
```

#### Drag Release
Bouncy snap back.

```tsx
<motion.div
  drag
  dragElastic={0.2}
  transition={{
    type: "spring",
    stiffness: 300,
    damping: 15,
  }}
/>
```

#### Magnetic Button
Smooth cursor following.

```tsx
const springConfig = {
  type: "spring",
  stiffness: 300,
  damping: 20,
}

<motion.button style={{ x: springX, y: springY }} />
```

#### Toggle Switch
Quick, satisfying flip.

```tsx
<motion.div
  animate={{ x: isOn ? 20 : 0 }}
  transition={{
    type: "spring",
    stiffness: 600,
    damping: 30,
  }}
/>
```

---

### Spring vs. Tween

| Aspect | Spring | Tween |
|--------|--------|-------|
| Duration | Dynamic (physics-based) | Fixed |
| Interruption | Seamlessly adapts | Can feel abrupt |
| Feel | Organic, natural | Mechanical |
| Control | Stiffness, damping, mass | Duration, easing |
| Best for | Gestures, interactions | Entrance/exit, timing-critical |

---

### useSpring Hook

For motion values that update frequently.

```tsx
import { useMotionValue, useSpring } from "motion/react"

const x = useMotionValue(0)
const springX = useSpring(x, {
  stiffness: 300,
  damping: 20,
  mass: 1,
})

// Update x, springX follows with spring physics
x.set(100)
```

**Benefits:**
- No re-renders (motion values)
- Smooth interpolation
- Perfect for cursor tracking, scroll effects

---

### Tuning Springs (Step-by-Step)

#### 1. Start with defaults
```tsx
stiffness: 300
damping: 20
mass: 1
```

#### 2. Adjust speed (stiffness)
- Too slow? Increase stiffness (400, 500)
- Too fast? Decrease stiffness (200, 100)

#### 3. Adjust bounce (damping)
- Too bouncy? Increase damping (30, 40)
- Not bouncy enough? Decrease damping (15, 10)

#### 4. Adjust weight (mass)
- Feels too light? Increase mass (1.5, 2)
- Feels too heavy? Decrease mass (0.8, 0.5)

#### 5. Test edge cases
- Very short distances
- Very long distances
- Rapid changes (spam clicking)

---

### Common Mistakes

#### ❌ Too Stiff + Too Bouncy
```tsx
stiffness: 1000
damping: 5 // Creates harsh, jarring motion
```

**Fix:** Balance stiffness and damping
```tsx
stiffness: 500
damping: 25
```

#### ❌ Too Soft + Heavy Mass
```tsx
stiffness: 100
mass: 5 // Painfully slow
```

**Fix:** Increase stiffness or reduce mass
```tsx
stiffness: 200
mass: 2
```

#### ❌ Using Spring for Everything
Some animations are better with tween:
- Simple fades
- Timed sequences
- Entrance animations

---

### Performance Tips

1. **Use useSpring** for frequently updating values (no re-renders)
2. **Avoid overly bouncy** springs (more calculations)
3. **Test on low-end devices** - springs can be CPU-intensive
4. **Critically damp when possible** (damping: 50) - faster to settle

---

### Accessibility

For users with `prefers-reduced-motion`:

```tsx
import { useReducedMotion } from "motion/react"

const shouldReduceMotion = useReducedMotion()

const transition = shouldReduceMotion
  ? { duration: 0.01 } // Instant
  : {
      type: "spring",
      stiffness: 300,
      damping: 20,
    }
```

---

### Design Philosophy (Apple/Jon Ive)

Springs align with minimalist design:

- **Natural** - Mimics real-world physics
- **Responsive** - Adapts to user input
- **Delightful** - Subtle bounce adds personality
- **Unobtrusive** - Feels right, doesn't distract

**Golden rules:**
1. Start gentle, add energy only if needed
2. Higher stiffness for smaller elements
3. Match spring energy to brand personality
4. Test on real devices (physics feel different)
