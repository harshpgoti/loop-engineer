# Motion Patterns (Examples)

Copy-paste motion examples: hero fade-up, scroll reveal, card hover, magnetic button, parallax layers.

---

## Hero Fade Up - Classic Apple-Style Animation

**Design Principle**: Simplicity and elegance. Elements gently fade in while sliding up, creating a sense of content emerging from below.

**Use Case**: Landing pages, product launches, portfolio hero sections

**Performance**: GPU-accelerated (transform + opacity only), 60fps+

---

### React / Next.js Implementation

```tsx
import { motion } from "motion/react"

export function HeroFadeUp() {
  return (
    <section className="min-h-screen flex items-center justify-center bg-black text-white">
      <div className="max-w-4xl px-8 text-center">
        {/* Title */}
        <motion.h1
          className="text-6xl md:text-8xl font-bold mb-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.8,
            ease: [0.22, 1, 0.36, 1], // Custom ease-out curve
          }}
        >
          Think Different
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          className="text-xl md:text-2xl text-gray-400 mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.8,
            delay: 0.1, // Stagger after title
            ease: [0.22, 1, 0.36, 1],
          }}
        >
          The people who are crazy enough to think they can change the world
          are the ones who do.
        </motion.p>

        {/* CTA Button */}
        <motion.button
          className="px-8 py-4 bg-white text-black rounded-full font-medium hover:bg-gray-200 transition-colors"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.8,
            delay: 0.2, // Stagger after subtitle
            ease: [0.22, 1, 0.36, 1],
          }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          Learn More
        </motion.button>
      </div>
    </section>
  )
}
```

---

### Vanilla JavaScript / Astro

```javascript
import { animate, stagger } from "motion"

// Animate all hero elements on page load
const heroElements = document.querySelectorAll(".hero-element")

animate(
  heroElements,
  { opacity: [0, 1], y: [20, 0] },
  {
    duration: 0.8,
    easing: [0.22, 1, 0.36, 1],
    delay: stagger(0.1), // 0.1s between each element
  }
)
```

**HTML**:
```html
<section class="hero">
  <h1 class="hero-element">Think Different</h1>
  <p class="hero-element">The people who are crazy enough...</p>
  <button class="hero-element">Learn More</button>
</section>
```

---

### With Reduced Motion Support

```tsx
import { motion, useReducedMotion } from "motion/react"

export function AccessibleHeroFadeUp() {
  const shouldReduceMotion = useReducedMotion()

  const animationProps = shouldReduceMotion
    ? {} // No animation if user prefers reduced motion
    : {
        initial: { opacity: 0, y: 20 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.8, ease: [0.22, 1, 0.36, 1] },
      }

  return (
    <motion.h1 {...animationProps}>
      Think Different
    </motion.h1>
  )
}
```

---

### Customization Options

#### Faster Animation (Snappier Feel)
```tsx
transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
```

#### Softer Animation (More Dramatic)
```tsx
transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
```

#### Larger Distance (More Dramatic Entry)
```tsx
initial={{ opacity: 0, y: 40 }} // Start further down
```

#### Spring Physics (Natural Bounce)
```tsx
transition={{
  type: "spring",
  stiffness: 100,
  damping: 20,
}}
```

---

### Design Notes

**Why this works:**
- **Opacity fade** - Gentle appearance, not jarring
- **Small y offset** (20px) - Subtle movement, not dramatic
- **Ease-out curve** - Starts fast, ends slow (natural deceleration)
- **Stagger delay** - Creates reading order hierarchy
- **GPU-accelerated** - Uses transform, not top/margin

**When to use:**
- Landing pages
- Product hero sections
- Portfolio headers
- Blog post headers
- Feature announcements

**Avoid when:**
- User has prefers-reduced-motion
- Page has many simultaneous animations
- Content is critical (don't delay important info)

---

## Scroll Reveal - Intersection Observer Fade-In

**Design Principle**: Progressive disclosure. Elements reveal themselves as user scrolls, creating a sense of discovery and maintaining engagement.

**Use Case**: Feature sections, testimonials, blog content, product showcases

**Performance**: Uses Intersection Observer (native browser API), GPU-accelerated

---

### React / Next.js Implementation

#### Simple Scroll Reveal

```tsx
import { motion } from "motion/react"
import { useRef } from "react"

export function ScrollReveal({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.3 }} // Trigger when 30% visible
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  )
}
```

**Usage**:
```tsx
<ScrollReveal>
  <h2>This fades in when scrolled into view</h2>
  <p>Beautiful, performant, accessible.</p>
</ScrollReveal>
```

---

#### Advanced: Different Directions

```tsx
type Direction = "up" | "down" | "left" | "right"

interface ScrollRevealProps {
  children: React.ReactNode
  direction?: Direction
  delay?: number
}

export function ScrollReveal({
  children,
  direction = "up",
  delay = 0,
}: ScrollRevealProps) {
  const directions = {
    up: { y: 50 },
    down: { y: -50 },
    left: { x: 50 },
    right: { x: -50 },
  }

  return (
    <motion.div
      initial={{ opacity: 0, ...directions[direction] }}
      whileInView={{ opacity: 1, x: 0, y: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      transition={{
        duration: 0.6,
        delay,
        ease: [0.22, 1, 0.36, 1],
      }}
    >
      {children}
    </motion.div>
  )
}
```

**Usage**:
```tsx
<ScrollReveal direction="left" delay={0.1}>
  <h2>From left</h2>
</ScrollReveal>

<ScrollReveal direction="right" delay={0.2}>
  <p>From right</p>
</ScrollReveal>
```

---

#### Staggered List Reveal

```tsx
import { motion } from "motion/react"

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1, // 0.1s between each child
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5 },
  },
}

export function FeatureList({ features }: { features: string[] }) {
  return (
    <motion.ul
      variants={containerVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
      className="space-y-4"
    >
      {features.map((feature, i) => (
        <motion.li
          key={i}
          variants={itemVariants}
          className="p-6 bg-white rounded-xl shadow-lg"
        >
          {feature}
        </motion.li>
      ))}
    </motion.ul>
  )
}
```

---

### Vanilla JavaScript / Astro

```javascript
import { inView, animate } from "motion"

// Reveal all elements with class "reveal"
const revealElements = document.querySelectorAll(".reveal")

revealElements.forEach((element) => {
  inView(
    element,
    () => {
      animate(
        element,
        { opacity: [0, 1], y: [50, 0] },
        { duration: 0.6, easing: "ease-out" }
      )
    },
    { amount: 0.3 } // Trigger when 30% visible
  )
})
```

**HTML**:
```html
<div class="reveal">
  <h2>Appears on scroll</h2>
</div>

<div class="reveal">
  <p>This too!</p>
</div>
```

---

### With useInView Hook (More Control)

```tsx
import { motion } from "motion/react"
import { useInView } from "motion/react"
import { useRef } from "react"

export function AdvancedScrollReveal({ children }: { children: React.ReactNode }) {
  const ref = useRef(null)
  const isInView = useInView(ref, {
    once: true, // Only animate once
    amount: 0.3, // Trigger when 30% visible
    margin: "0px 0px -100px 0px", // Offset trigger point
  })

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 50 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  )
}
```

---

### Complete Example: Feature Section

```tsx
import { motion } from "motion/react"

const features = [
  { title: "Fast", description: "Lightning quick performance" },
  { title: "Beautiful", description: "Stunning visual design" },
  { title: "Accessible", description: "Works for everyone" },
]

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
      delayChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: [0.22, 1, 0.36, 1],
    },
  },
}

export function FeaturesSection() {
  return (
    <section className="py-24 px-8 bg-gray-50">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="max-w-4xl mx-auto text-center mb-16"
      >
        <h2 className="text-4xl font-bold mb-4">Why Choose Us</h2>
        <p className="text-xl text-gray-600">
          Three reasons we're different
        </p>
      </motion.div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.2 }}
        className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto"
      >
        {features.map((feature, i) => (
          <motion.div
            key={i}
            variants={itemVariants}
            className="bg-white p-8 rounded-2xl shadow-lg"
          >
            <h3 className="text-2xl font-bold mb-3">{feature.title}</h3>
            <p className="text-gray-600">{feature.description}</p>
          </motion.div>
        ))}
      </motion.div>
    </section>
  )
}
```

---

### Customization Options

#### Reveal Multiple Times (Not Just Once)
```tsx
viewport={{ once: false }}
```

#### Trigger Earlier (Before Element Is Visible)
```tsx
viewport={{ margin: "0px 0px -200px 0px" }} // Trigger 200px before
```

#### Only Trigger When Fully Visible
```tsx
viewport={{ amount: 1 }} // 100% visible required
```

#### Slower, More Dramatic
```tsx
transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
```

---

### Design Notes

**Why this works:**
- **Intersection Observer** - Native browser API, very performant
- **once: true** - Prevents animation on every scroll (less distracting)
- **amount: 0.3** - Triggers early enough to complete before fully visible
- **Stagger** - Creates natural rhythm for lists

**When to use:**
- Feature grids
- Testimonial sections
- Blog post paragraphs
- Image galleries
- Pricing tables

**Avoid when:**
- Critical content (don't hide important info)
- Many elements on page (performance)
- User has prefers-reduced-motion
- Above the fold content (should be visible immediately)

---

## Card Hover - Elegant Lift with Shadow

**Design Principle**: Delightful feedback. Cards gently lift and cast a shadow on hover, creating tactile depth and encouraging interaction.

**Use Case**: Product cards, blog posts, portfolio items, feature grids

**Performance**: GPU-accelerated transforms, instant response

---

### React / Next.js Implementation

#### Basic Card Hover

```tsx
import { motion } from "motion/react"

export function HoverCard({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      className="bg-white rounded-2xl p-6 cursor-pointer"
      whileHover={{
        y: -8, // Lift up 8px
        boxShadow: "0 20px 40px rgba(0, 0, 0, 0.12)", // Elevated shadow
      }}
      transition={{
        type: "spring",
        stiffness: 300,
        damping: 20,
      }}
    >
      {children}
    </motion.div>
  )
}
```

**Usage**:
```tsx
<HoverCard>
  <h3>Product Name</h3>
  <p>Beautiful description</p>
</HoverCard>
```

---

#### Advanced: Scale + Shadow + Border Glow

```tsx
import { motion } from "motion/react"

export function PremiumCard({
  title,
  description,
  image,
}: {
  title: string
  description: string
  image: string
}) {
  return (
    <motion.article
      className="bg-white rounded-2xl overflow-hidden cursor-pointer border-2 border-transparent"
      initial={{ boxShadow: "0 2px 8px rgba(0, 0, 0, 0.08)" }}
      whileHover={{
        y: -12,
        scale: 1.02,
        boxShadow: "0 24px 48px rgba(0, 0, 0, 0.15)",
        borderColor: "rgba(59, 130, 246, 0.5)", // Blue glow
      }}
      transition={{
        type: "spring",
        stiffness: 260,
        damping: 20,
      }}
    >
      <motion.img
        src={image}
        alt={title}
        className="w-full h-48 object-cover"
        whileHover={{ scale: 1.05 }}
        transition={{ duration: 0.4 }}
      />

      <div className="p-6">
        <h3 className="text-2xl font-bold mb-2">{title}</h3>
        <p className="text-gray-600">{description}</p>

        <motion.button
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg"
          whileHover={{ scale: 1.05, backgroundColor: "#2563eb" }}
          whileTap={{ scale: 0.95 }}
        >
          Learn More
        </motion.button>
      </div>
    </motion.article>
  )
}
```

---

#### Apple-Style: Minimal Lift + Subtle Scale

```tsx
import { motion } from "motion/react"

export function AppleCard({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      className="bg-white rounded-3xl p-8 shadow-sm"
      whileHover={{
        y: -4, // Very subtle lift
        scale: 1.01, // Barely noticeable scale
        boxShadow: "0 12px 24px rgba(0, 0, 0, 0.08)",
      }}
      transition={{
        type: "spring",
        stiffness: 400,
        damping: 30,
      }}
      style={{ willChange: "transform" }} // Performance hint
    >
      {children}
    </motion.div>
  )
}
```

---

### Grid of Cards with Stagger

```tsx
import { motion } from "motion/react"

const products = [
  { id: 1, title: "Product 1", price: "$99" },
  { id: 2, title: "Product 2", price: "$149" },
  { id: 3, title: "Product 3", price: "$199" },
]

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
}

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
}

export function ProductGrid() {
  return (
    <motion.div
      className="grid md:grid-cols-3 gap-8"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {products.map((product) => (
        <motion.div
          key={product.id}
          variants={cardVariants}
          whileHover={{
            y: -8,
            boxShadow: "0 20px 40px rgba(0, 0, 0, 0.12)",
          }}
          className="bg-white rounded-2xl p-6 cursor-pointer"
        >
          <h3 className="text-xl font-bold">{product.title}</h3>
          <p className="text-2xl font-bold mt-2">{product.price}</p>
        </motion.div>
      ))}
    </motion.div>
  )
}
```

---

### Vanilla JavaScript

```javascript
import { animate } from "motion"

const cards = document.querySelectorAll(".card")

cards.forEach((card) => {
  // Hover in
  card.addEventListener("mouseenter", () => {
    animate(
      card,
      {
        y: -8,
        boxShadow: "0 20px 40px rgba(0, 0, 0, 0.12)",
      },
      {
        type: "spring",
        stiffness: 300,
        damping: 20,
      }
    )
  })

  // Hover out
  card.addEventListener("mouseleave", () => {
    animate(
      card,
      {
        y: 0,
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.08)",
      },
      {
        type: "spring",
        stiffness: 300,
        damping: 20,
      }
    )
  })
})
```

---

### With Click Animation

```tsx
import { motion } from "motion/react"

export function InteractiveCard({ onClick }: { onClick: () => void }) {
  return (
    <motion.div
      className="bg-white rounded-2xl p-6 cursor-pointer"
      whileHover={{
        y: -8,
        boxShadow: "0 20px 40px rgba(0, 0, 0, 0.12)",
      }}
      whileTap={{
        scale: 0.98, // Slight press-down effect
        y: -4, // Less lift when tapping
      }}
      transition={{
        type: "spring",
        stiffness: 300,
        damping: 20,
      }}
      onClick={onClick}
    >
      <h3>Click me</h3>
    </motion.div>
  )
}
```

---

### Accessibility: Keyboard Focus State

```tsx
import { motion } from "motion/react"

export function AccessibleCard({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      className="bg-white rounded-2xl p-6 cursor-pointer focus:outline-none"
      tabIndex={0} // Make keyboard focusable
      whileHover={{
        y: -8,
        boxShadow: "0 20px 40px rgba(0, 0, 0, 0.12)",
      }}
      whileFocus={{
        y: -8,
        boxShadow: "0 20px 40px rgba(0, 0, 0, 0.12)",
        outline: "2px solid #3b82f6", // Blue focus ring
        outlineOffset: "2px",
      }}
      transition={{
        type: "spring",
        stiffness: 300,
        damping: 20,
      }}
    >
      {children}
    </motion.div>
  )
}
```

---

### Customization Options

#### Subtle (Apple-Style)
```tsx
whileHover={{ y: -2, scale: 1.005 }}
```

#### Dramatic (Product Showcase)
```tsx
whileHover={{ y: -16, scale: 1.05, rotate: 2 }}
```

#### Glow Effect
```tsx
whileHover={{
  y: -8,
  boxShadow: "0 20px 60px rgba(59, 130, 246, 0.4)", // Blue glow
}}
```

#### Slower, Smoother
```tsx
transition={{ duration: 0.4, ease: "easeOut" }}
```

---

### Design Notes

**Why this works:**
- **Lift (y: -8)** - Creates tactile depth, suggests clickability
- **Shadow** - Reinforces elevation, adds realism
- **Spring physics** - Natural, organic response
- **Instant feedback** - User knows it's interactive

**When to use:**
- Product cards
- Blog post previews
- Portfolio items
- Feature grids
- Team member cards
- Pricing tables

**Avoid when:**
- Too many cards (overwhelming)
- Small touch targets on mobile
- User has prefers-reduced-motion
- Cards are purely informational (not interactive)

**Performance tips:**
- Use `will-change: transform` CSS
- Avoid animating width/height
- Limit number of simultaneously hoverable elements
- Test on mobile devices

---

## Magnetic Button - Cursor-Following Effect

**Design Principle**: Playful interaction. Button subtly follows cursor, creating tactile magnetism and encouraging clicks.

**Use Case**: CTAs, primary buttons, interactive elements, portfolio showcases

**Performance**: Uses useMotionValue for 60fps tracking

---

### React / Next.js Implementation

#### Basic Magnetic Button

```tsx
import { motion, useMotionValue, useSpring } from "motion/react"
import { useRef, MouseEvent } from "react"

export function MagneticButton({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLButtonElement>(null)

  // Motion values for x and y position
  const x = useMotionValue(0)
  const y = useMotionValue(0)

  // Spring physics for smooth following
  const springX = useSpring(x, { stiffness: 300, damping: 20 })
  const springY = useSpring(y, { stiffness: 300, damping: 20 })

  const handleMouseMove = (e: MouseEvent<HTMLButtonElement>) => {
    if (!ref.current) return

    const rect = ref.current.getBoundingClientRect()
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2

    // Distance from center
    const distanceX = e.clientX - centerX
    const distanceY = e.clientY - centerY

    // Move towards cursor (max 20px)
    x.set(distanceX * 0.3)
    y.set(distanceY * 0.3)
  }

  const handleMouseLeave = () => {
    x.set(0)
    y.set(0)
  }

  return (
    <motion.button
      ref={ref}
      className="px-8 py-4 bg-blue-500 text-white rounded-full font-medium"
      style={{
        x: springX,
        y: springY,
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      whileTap={{ scale: 0.95 }}
    >
      {children}
    </motion.button>
  )
}
```

---

#### Advanced: With Scale + Glow

```tsx
import { motion, useMotionValue, useSpring, useTransform } from "motion/react"
import { useRef, MouseEvent } from "react"

export function AdvancedMagneticButton({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLButtonElement>(null)

  const x = useMotionValue(0)
  const y = useMotionValue(0)

  const springX = useSpring(x, { stiffness: 300, damping: 20 })
  const springY = useSpring(y, { stiffness: 300, damping: 20 })

  // Scale based on distance (closer = larger)
  const scale = useTransform(
    [x, y],
    ([latestX, latestY]) => {
      const distance = Math.sqrt(latestX ** 2 + latestY ** 2)
      return 1 + distance * 0.003 // Subtle scale
    }
  )

  const handleMouseMove = (e: MouseEvent<HTMLButtonElement>) => {
    if (!ref.current) return

    const rect = ref.current.getBoundingClientRect()
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2

    const distanceX = e.clientX - centerX
    const distanceY = e.clientY - centerY

    x.set(distanceX * 0.4)
    y.set(distanceY * 0.4)
  }

  const handleMouseLeave = () => {
    x.set(0)
    y.set(0)
  }

  return (
    <motion.button
      ref={ref}
      className="relative px-10 py-5 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-full font-bold text-lg overflow-hidden"
      style={{
        x: springX,
        y: springY,
        scale,
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      whileTap={{ scale: 0.92 }}
    >
      {/* Glow effect */}
      <motion.div
        className="absolute inset-0 bg-white opacity-0"
        whileHover={{ opacity: 0.2 }}
        transition={{ duration: 0.3 }}
      />

      <span className="relative z-10">{children}</span>
    </motion.button>
  )
}
```

---

#### Magnetic Card (Large Area)

```tsx
import { motion, useMotionValue, useSpring } from "motion/react"
import { useRef, MouseEvent } from "react"

export function MagneticCard({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null)

  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const rotateX = useMotionValue(0)
  const rotateY = useMotionValue(0)

  const springX = useSpring(x, { stiffness: 200, damping: 20 })
  const springY = useSpring(y, { stiffness: 200, damping: 20 })
  const springRotateX = useSpring(rotateX, { stiffness: 200, damping: 20 })
  const springRotateY = useSpring(rotateY, { stiffness: 200, damping: 20 })

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    if (!ref.current) return

    const rect = ref.current.getBoundingClientRect()
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2

    const distanceX = e.clientX - centerX
    const distanceY = e.clientY - centerY

    // Translate
    x.set(distanceX * 0.1)
    y.set(distanceY * 0.1)

    // 3D rotation based on cursor position
    rotateX.set((distanceY / rect.height) * -10) // Tilt up/down
    rotateY.set((distanceX / rect.width) * 10) // Tilt left/right
  }

  const handleMouseLeave = () => {
    x.set(0)
    y.set(0)
    rotateX.set(0)
    rotateY.set(0)
  }

  return (
    <motion.div
      ref={ref}
      className="bg-white rounded-3xl p-8 shadow-lg cursor-pointer"
      style={{
        x: springX,
        y: springY,
        rotateX: springRotateX,
        rotateY: springRotateY,
        transformPerspective: 1000,
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {children}
    </motion.div>
  )
}
```

---

#### Magnetic Cursor (Global Effect)

```tsx
import { motion, useMotionValue, useSpring } from "motion/react"
import { useEffect } from "react"

export function MagneticCursor() {
  const cursorX = useMotionValue(0)
  const cursorY = useMotionValue(0)

  const springX = useSpring(cursorX, { stiffness: 500, damping: 30 })
  const springY = useSpring(cursorY, { stiffness: 500, damping: 30 })

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      cursorX.set(e.clientX - 16) // Offset for center
      cursorY.set(e.clientY - 16)
    }

    window.addEventListener("mousemove", handleMouseMove)
    return () => window.removeEventListener("mousemove", handleMouseMove)
  }, [])

  return (
    <>
      {/* Custom cursor */}
      <motion.div
        className="fixed top-0 left-0 w-8 h-8 bg-blue-500 rounded-full pointer-events-none z-50 mix-blend-difference"
        style={{
          x: springX,
          y: springY,
        }}
      />

      {/* Hide default cursor */}
      <style jsx global>{`
        * {
          cursor: none !important;
        }
      `}</style>
    </>
  )
}
```

---

### Vanilla JavaScript

```javascript
import { animate, spring } from "motion"

const button = document.querySelector(".magnetic-btn")

let currentX = 0
let currentY = 0

button.addEventListener("mousemove", (e) => {
  const rect = button.getBoundingClientRect()
  const centerX = rect.left + rect.width / 2
  const centerY = rect.top + rect.height / 2

  const distanceX = e.clientX - centerX
  const distanceY = e.clientY - centerY

  const targetX = distanceX * 0.3
  const targetY = distanceY * 0.3

  // Animate with spring physics
  animate(
    (progress) => {
      currentX = currentX + (targetX - currentX) * progress
      currentY = currentY + (targetY - currentY) * progress
      button.style.transform = `translate(${currentX}px, ${currentY}px)`
    },
    { duration: 0.3, easing: spring({ stiffness: 300, damping: 20 }) }
  )
})

button.addEventListener("mouseleave", () => {
  animate(
    (progress) => {
      currentX = currentX * (1 - progress)
      currentY = currentY * (1 - progress)
      button.style.transform = `translate(${currentX}px, ${currentY}px)`
    },
    { duration: 0.5, easing: spring({ stiffness: 300, damping: 20 }) }
  )
})
```

---

### Customization Options

#### Stronger Magnetism
```tsx
x.set(distanceX * 0.6) // More movement
y.set(distanceY * 0.6)
```

#### Weaker Magnetism (Subtle)
```tsx
x.set(distanceX * 0.15) // Less movement
y.set(distanceY * 0.15)
```

#### Faster Response
```tsx
const springX = useSpring(x, { stiffness: 500, damping: 25 })
```

#### Slower, Smoother
```tsx
const springX = useSpring(x, { stiffness: 150, damping: 15 })
```

#### Maximum Distance Cap
```tsx
const maxDistance = 30
x.set(Math.min(Math.max(distanceX * 0.4, -maxDistance), maxDistance))
```

---

### Design Notes

**Why this works:**
- **Playful** - Creates delight and encourages interaction
- **Tactile** - Feels responsive and alive
- **Attention** - Draws eye to important CTAs
- **Spring physics** - Natural, organic following motion

**When to use:**
- Primary CTAs
- Portfolio showcases
- Interactive demos
- Playful brand experiences
- Hero buttons

**Avoid when:**
- Mobile devices (no cursor)
- Too many buttons (overwhelming)
- Accessibility concerns
- Professional/serious contexts
- User has prefers-reduced-motion

**Performance tips:**
- Use useMotionValue (no re-renders)
- Apply spring physics (smooth interpolation)
- Limit effect area (don't track entire page)
- Test on lower-end devices
- Provide reduced-motion fallback

**Accessibility:**
- Works with keyboard navigation (no magnetic effect)
- Ensure button remains clickable at all positions
- Provide hover state for non-cursor devices
- Test with screen readers

---

## Parallax Layers - Multi-Speed Scroll Effect

**Design Principle**: Depth through motion. Different layers move at different speeds, creating a sense of 3D depth and immersion.

**Use Case**: Hero backgrounds, storytelling sections, product showcases

**Performance**: Uses useScroll + useTransform, GPU-accelerated

---

### React / Next.js Implementation

#### Simple Two-Layer Parallax

```tsx
import { motion, useScroll, useTransform } from "motion/react"
import { useRef } from "react"

export function ParallaxHero() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"], // Track from element start to end
  })

  // Background moves slower (0.5x speed)
  const backgroundY = useTransform(scrollYProgress, [0, 1], ["0%", "50%"])

  // Foreground moves normal (1x speed is default scroll)
  const foregroundY = useTransform(scrollYProgress, [0, 1], ["0%", "30%"])

  return (
    <section ref={ref} className="relative h-screen overflow-hidden">
      {/* Background Layer - Slowest */}
      <motion.div
        className="absolute inset-0 z-0"
        style={{ y: backgroundY }}
      >
        <img
          src="/mountains-bg.jpg"
          alt="Mountains"
          className="w-full h-[120%] object-cover"
        />
      </motion.div>

      {/* Foreground Layer - Faster */}
      <motion.div
        className="absolute inset-0 z-10 flex items-center justify-center"
        style={{ y: foregroundY }}
      >
        <h1 className="text-6xl font-bold text-white">
          Explore the Mountains
        </h1>
      </motion.div>
    </section>
  )
}
```

---

#### Advanced: Multi-Layer Parallax (3+ Layers)

```tsx
import { motion, useScroll, useTransform } from "motion/react"
import { useRef } from "react"

export function MultiLayerParallax() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  })

  // Different speeds for different layers
  const backgroundY = useTransform(scrollYProgress, [0, 1], ["0%", "50%"])
  const midgroundY = useTransform(scrollYProgress, [0, 1], ["0%", "30%"])
  const foregroundY = useTransform(scrollYProgress, [0, 1], ["0%", "15%"])
  const textY = useTransform(scrollYProgress, [0, 1], ["0%", "-50%"]) // Moves up

  return (
    <section ref={ref} className="relative h-[150vh]">
      {/* Far Background - Slowest (Mountains) */}
      <motion.div
        className="absolute inset-0 z-0"
        style={{ y: backgroundY }}
      >
        <img
          src="/mountains.jpg"
          alt="Mountains"
          className="w-full h-full object-cover opacity-70"
        />
      </motion.div>

      {/* Midground (Trees) */}
      <motion.div
        className="absolute inset-0 z-10"
        style={{ y: midgroundY }}
      >
        <img
          src="/trees.png"
          alt="Trees"
          className="w-full h-full object-cover"
        />
      </motion.div>

      {/* Foreground (Grass) */}
      <motion.div
        className="absolute inset-0 z-20"
        style={{ y: foregroundY }}
      >
        <img
          src="/grass.png"
          alt="Grass"
          className="w-full h-full object-cover"
        />
      </motion.div>

      {/* Text - Moves opposite direction */}
      <motion.div
        className="absolute inset-0 z-30 flex items-center justify-center"
        style={{ y: textY }}
      >
        <div className="text-center text-white">
          <h1 className="text-7xl font-bold mb-4">Journey Through Nature</h1>
          <p className="text-2xl">Discover the untold stories</p>
        </div>
      </motion.div>
    </section>
  )
}
```

---

#### Horizontal Parallax (Cards)

```tsx
import { motion, useScroll, useTransform } from "motion/react"
import { useRef } from "react"

export function HorizontalParallax() {
  const containerRef = useRef(null)
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"],
  })

  // Different cards move at different speeds
  const x1 = useTransform(scrollYProgress, [0, 1], ["-10%", "10%"])
  const x2 = useTransform(scrollYProgress, [0, 1], ["-5%", "5%"])
  const x3 = useTransform(scrollYProgress, [0, 1], ["0%", "0%"]) // Static
  const x4 = useTransform(scrollYProgress, [0, 1], ["5%", "-5%"])

  return (
    <section ref={containerRef} className="py-24 overflow-hidden">
      <div className="flex gap-8 px-8">
        <motion.div style={{ x: x1 }} className="card">
          Card 1
        </motion.div>
        <motion.div style={{ x: x2 }} className="card">
          Card 2
        </motion.div>
        <motion.div style={{ x: x3 }} className="card">
          Card 3
        </motion.div>
        <motion.div style={{ x: x4 }} className="card">
          Card 4
        </motion.div>
      </div>
    </section>
  )
}
```

---

### Vanilla JavaScript

```javascript
import { scroll } from "motion"

scroll(
  ({ y }) => {
    // Background layer - slow
    const background = document.querySelector(".parallax-bg")
    if (background) {
      background.style.transform = `translateY(${y.current * 0.5}px)`
    }

    // Foreground layer - faster
    const foreground = document.querySelector(".parallax-fg")
    if (foreground) {
      foreground.style.transform = `translateY(${y.current * 0.3}px)`
    }

    // Text - opposite direction
    const text = document.querySelector(".parallax-text")
    if (text) {
      text.style.transform = `translateY(${-y.current * 0.2}px)`
    }
  },
  { target: document.querySelector(".parallax-section") }
)
```

---

### With Scale + Opacity

```tsx
import { motion, useScroll, useTransform } from "motion/react"
import { useRef } from "react"

export function ParallaxWithScale() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  })

  const y = useTransform(scrollYProgress, [0, 1], ["0%", "50%"])
  const scale = useTransform(scrollYProgress, [0, 1], [1, 1.2]) // Zoom in
  const opacity = useTransform(scrollYProgress, [0, 1], [1, 0]) // Fade out

  return (
    <section ref={ref} className="relative h-screen overflow-hidden">
      <motion.div
        className="absolute inset-0"
        style={{
          y,
          scale,
          opacity,
        }}
      >
        <img
          src="/hero-bg.jpg"
          alt="Background"
          className="w-full h-full object-cover"
        />
      </motion.div>

      <div className="relative z-10 flex items-center justify-center h-full">
        <h1 className="text-6xl font-bold text-white">
          Parallax with Scale
        </h1>
      </div>
    </section>
  )
}
```

---

### Performance Optimization

```tsx
import { motion, useScroll, useTransform } from "motion/react"
import { useRef } from "react"

export function OptimizedParallax() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  })

  const y = useTransform(scrollYProgress, [0, 1], ["0%", "50%"])

  return (
    <section ref={ref} className="relative h-screen overflow-hidden">
      <motion.div
        className="absolute inset-0"
        style={{
          y,
          willChange: "transform", // Performance hint
        }}
      >
        <img
          src="/bg.jpg"
          alt="Background"
          className="w-full h-full object-cover"
          loading="eager" // Load immediately for above-fold
          fetchPriority="high"
        />
      </motion.div>
    </section>
  )
}
```

---

### With Reduced Motion Support

```tsx
import { motion, useScroll, useTransform, useReducedMotion } from "motion/react"
import { useRef } from "react"

export function AccessibleParallax() {
  const ref = useRef(null)
  const shouldReduceMotion = useReducedMotion()

  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  })

  // Disable parallax if user prefers reduced motion
  const y = useTransform(
    scrollYProgress,
    [0, 1],
    shouldReduceMotion ? ["0%", "0%"] : ["0%", "50%"]
  )

  return (
    <section ref={ref} className="relative h-screen overflow-hidden">
      <motion.div className="absolute inset-0" style={{ y }}>
        <img src="/bg.jpg" alt="Background" className="w-full h-full object-cover" />
      </motion.div>
    </section>
  )
}
```

---

### Design Notes

**Why this works:**
- **Depth perception** - Different speeds create 3D illusion
- **Engagement** - Encourages scrolling, creates discovery
- **Visual interest** - More dynamic than static backgrounds
- **Storytelling** - Can reveal elements progressively

**Parallax speeds:**
- **0.1-0.3x** - Very slow (far background, mountains)
- **0.4-0.6x** - Medium (mid-ground, trees)
- **0.7-0.9x** - Fast (foreground, grass)
- **1.0x** - Normal scroll speed (default)
- **-0.2x to -0.5x** - Reverse (text moving up)

**When to use:**
- Hero sections
- Product showcases
- Storytelling pages
- Portfolio headers
- Landing pages

**Avoid when:**
- User has prefers-reduced-motion
- Mobile with poor performance
- Critical content (accessibility concern)
- Too many layers (performance)
- Horizontal scrolling sections

**Performance tips:**
- Use transforms only (not top/left)
- Add `will-change: transform`
- Limit number of layers (3-5 max)
- Use `offset` to only animate when in view
- Test on lower-end devices
