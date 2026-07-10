# 3D Rendering

Vanilla Three.js/WebGL scenes and React Three Fiber, in one reference.

---

## Three.js WebGL/WebGPU Development

### Overview

Three.js is the industry-standard JavaScript library for creating 3D graphics in web browsers using WebGL and WebGPU. This skill provides comprehensive guidance for building performant, interactive 3D experiences including scenes, cameras, renderers, geometries, materials, lights, textures, and animations.

### Core Concepts

#### Scene Graph Architecture

Three.js uses a hierarchical scene graph where all 3D objects are organized in a tree structure:

```javascript
Scene
├── Camera
├── Lights
│   ├── AmbientLight
│   ├── DirectionalLight
│   └── PointLight
├── Meshes
│   ├── Mesh (Geometry + Material)
│   └── InstancedMesh
└── Groups
```

#### Essential Components

Every Three.js application requires these core elements:

1. **Scene**: Container for all 3D objects
2. **Camera**: Defines the viewing perspective
3. **Renderer**: Draws the scene to canvas (WebGL or WebGPU)
4. **Geometry**: Defines the shape of objects
5. **Material**: Defines the surface appearance
6. **Mesh**: Combines geometry and material

### Quick Start Pattern

#### Basic Scene Setup

```javascript
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// Scene, Camera, Renderer
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x333333);

const camera = new THREE.PerspectiveCamera(
  75, // FOV
  window.innerWidth / window.innerHeight, // Aspect ratio
  0.1, // Near clipping plane
  1000 // Far clipping plane
);
camera.position.set(0, 2, 5);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.shadowMap.enabled = true;
document.body.appendChild(renderer.domElement);

// Lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
directionalLight.position.set(5, 10, 7.5);
directionalLight.castShadow = true;
scene.add(directionalLight);

// Controls
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;

// Animation Loop
function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}

animate();

// Handle Resize
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
```

#### WebGPU Setup (Modern Alternative)

```javascript
import * as THREE from 'three/webgpu';

const renderer = new THREE.WebGPURenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setAnimationLoop(animate);
renderer.toneMapping = THREE.LinearToneMapping;
renderer.toneMappingExposure = 1;
document.body.appendChild(renderer.domElement);
```

### Common Patterns

#### 1. Creating Meshes with Materials

```javascript
// Basic Mesh
const geometry = new THREE.BoxGeometry(1, 1, 1);
const material = new THREE.MeshStandardMaterial({
  color: 0x00ff00,
  roughness: 0.5,
  metalness: 0.5
});
const cube = new THREE.Mesh(geometry, material);
scene.add(cube);

// Textured Mesh
const loader = new THREE.TextureLoader();
const texture = loader.load('texture.jpg');
texture.colorSpace = THREE.SRGBColorSpace;

const texturedMaterial = new THREE.MeshStandardMaterial({
  map: texture
});
const mesh = new THREE.Mesh(geometry, texturedMaterial);
scene.add(mesh);
```

#### 2. Lighting Strategies

```javascript
// Three-Point Lighting Setup
function setupThreePointLight(scene) {
  // Key Light (Main)
  const keyLight = new THREE.DirectionalLight(0xffffff, 3);
  keyLight.position.set(5, 10, 7.5);
  keyLight.castShadow = true;
  scene.add(keyLight);

  // Fill Light (Softens shadows)
  const fillLight = new THREE.DirectionalLight(0xffffff, 1);
  fillLight.position.set(-5, 5, -5);
  scene.add(fillLight);

  // Rim Light (Edge definition)
  const rimLight = new THREE.DirectionalLight(0xffffff, 0.5);
  rimLight.position.set(0, 5, -10);
  scene.add(rimLight);

  // Ambient (Base illumination)
  const ambient = new THREE.AmbientLight(0x404040, 0.5);
  scene.add(ambient);
}

// Physical Light (Realistic)
const bulbLight = new THREE.PointLight(0xffee88, 1, 100, 2);
bulbLight.power = 1700; // Lumens (100W bulb equivalent)
bulbLight.castShadow = true;
scene.add(bulbLight);

// Hemisphere Light (Sky + Ground)
const hemiLight = new THREE.HemisphereLight(
  0xddeeff, // Sky color
  0x0f0e0d, // Ground color
  0.02
);
scene.add(hemiLight);
```

#### 3. Instanced Geometry (Performance)

```javascript
// For rendering thousands of similar objects efficiently
const geometry = new THREE.SphereGeometry(0.1, 16, 16);
const material = new THREE.MeshStandardMaterial({ color: 0xff0000 });
const instancedMesh = new THREE.InstancedMesh(geometry, material, 1000);

const matrix = new THREE.Matrix4();
const color = new THREE.Color();

for (let i = 0; i < 1000; i++) {
  matrix.setPosition(
    Math.random() * 10 - 5,
    Math.random() * 10 - 5,
    Math.random() * 10 - 5
  );
  instancedMesh.setMatrixAt(i, matrix);
  instancedMesh.setColorAt(i, color.setHex(Math.random() * 0xffffff));
}

instancedMesh.instanceMatrix.needsUpdate = true;
scene.add(instancedMesh);
```

#### 4. Loading 3D Models (glTF)

```javascript
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';

// Setup loaders
const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('/draco/');

const gltfLoader = new GLTFLoader();
gltfLoader.setDRACOLoader(dracoLoader);

// Load model
gltfLoader.load('model.glb', (gltf) => {
  const model = gltf.scene;

  // Enable shadows
  model.traverse((child) => {
    if (child.isMesh) {
      child.castShadow = true;
      child.receiveShadow = true;
    }
  });

  scene.add(model);

  // Handle animations
  if (gltf.animations.length > 0) {
    const mixer = new THREE.AnimationMixer(model);
    const action = mixer.clipAction(gltf.animations[0]);
    action.play();

    // In animation loop:
    // mixer.update(deltaTime);
  }
});
```

#### 5. Shadow Configuration

```javascript
// Enable shadows on renderer
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap; // or VSMShadowMap

// Configure light shadows
directionalLight.castShadow = true;
directionalLight.shadow.mapSize.width = 2048;
directionalLight.shadow.mapSize.height = 2048;
directionalLight.shadow.camera.near = 0.5;
directionalLight.shadow.camera.far = 50;
directionalLight.shadow.camera.left = -10;
directionalLight.shadow.camera.right = 10;
directionalLight.shadow.camera.top = 10;
directionalLight.shadow.camera.bottom = -10;
directionalLight.shadow.radius = 4;
directionalLight.shadow.blurSamples = 8;

// Objects casting/receiving shadows
mesh.castShadow = true;
mesh.receiveShadow = true;
```

#### 6. Raycasting (Interaction)

```javascript
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

function onMouseClick(event) {
  mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObjects(scene.children, true);

  if (intersects.length > 0) {
    const object = intersects[0].object;
    object.material.color.set(0xff0000);
  }
}

window.addEventListener('click', onMouseClick);
```

### Integration Patterns

#### With GSAP for Animation

```javascript
import gsap from 'gsap';

// Animate camera
gsap.to(camera.position, {
  x: 5,
  y: 3,
  z: 10,
  duration: 2,
  ease: "power2.inOut",
  onUpdate: () => {
    camera.lookAt(scene.position);
  }
});

// Animate mesh properties
gsap.to(mesh.rotation, {
  y: Math.PI * 2,
  duration: 3,
  repeat: -1,
  ease: "none"
});
```

#### With React (see react-3d skill)

```javascript
// Three.js integrates naturally with React Three Fiber
// Use the react-3d skill for React integration patterns
```

#### With Post-Processing

```javascript
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));

const bloomPass = new UnrealBloomPass(
  new THREE.Vector2(window.innerWidth, window.innerHeight),
  1.5, // strength
  0.4, // radius
  0.85 // threshold
);
composer.addPass(bloomPass);

// In animation loop:
composer.render();
```

### Performance Optimization

#### 1. Geometry Reuse
```javascript
// Bad: Creates new geometry for each mesh
for (let i = 0; i < 100; i++) {
  const geometry = new THREE.BoxGeometry(1, 1, 1);
  const mesh = new THREE.Mesh(geometry, material);
  scene.add(mesh);
}

// Good: Reuse geometry
const sharedGeometry = new THREE.BoxGeometry(1, 1, 1);
for (let i = 0; i < 100; i++) {
  const mesh = new THREE.Mesh(sharedGeometry, material);
  scene.add(mesh);
}
```

#### 2. Use InstancedMesh for Repeated Objects
For hundreds/thousands of identical objects, use `InstancedMesh` (see pattern above).

#### 3. Texture Optimization
```javascript
// Compress textures
texture.generateMipmaps = true;
texture.minFilter = THREE.LinearMipmapLinearFilter;
texture.magFilter = THREE.LinearFilter;

// Use power-of-two dimensions (512, 1024, 2048)
// Consider texture atlases for multiple small textures
```

#### 4. Level of Detail (LOD)
```javascript
const lod = new THREE.LOD();
lod.addLevel(highDetailMesh, 0);    // 0-50 units
lod.addLevel(mediumDetailMesh, 50);  // 50-100 units
lod.addLevel(lowDetailMesh, 100);    // 100+ units
scene.add(lod);
```

#### 5. Frustum Culling
Three.js automatically culls objects outside the camera's view. Ensure objects have correct bounding spheres:

```javascript
mesh.geometry.computeBoundingSphere();
```

#### 6. Dispose Resources
```javascript
function disposeScene() {
  scene.traverse((object) => {
    if (object.geometry) object.geometry.dispose();
    if (object.material) {
      if (Array.isArray(object.material)) {
        object.material.forEach(material => material.dispose());
      } else {
        object.material.dispose();
      }
    }
  });
  renderer.dispose();
}
```

### Best Practices

#### 1. Use Animation Clocks for Consistent Timing
```javascript
const clock = new THREE.Clock();

function animate() {
  const deltaTime = clock.getDelta();
  const elapsedTime = clock.getElapsedTime();

  // Use deltaTime for frame-independent animations
  mesh.rotation.y += deltaTime * Math.PI * 0.5; // 90° per second

  renderer.render(scene, camera);
}
```

#### 2. Camera Setup Guidelines
- **FOV**: 45-75° for most applications
- **Near plane**: As far as possible (avoid z-fighting)
- **Far plane**: As close as possible (precision)
- **Aspect ratio**: Always match canvas dimensions

#### 3. Material Selection
- **MeshBasicMaterial**: Unlit, flat colors (debugging, UI)
- **MeshLambertMaterial**: Cheap diffuse lighting (mobile)
- **MeshPhongMaterial**: Specular highlights (older standard)
- **MeshStandardMaterial**: PBR, realistic (recommended)
- **MeshPhysicalMaterial**: Advanced PBR (clearcoat, transmission)

#### 4. Coordinate System
- Three.js uses right-handed coordinate system
- +Y is up, +Z is toward camera, +X is right
- Rotations use radians (Math.PI = 180°)

#### 5. Scene Organization
```javascript
// Group related objects
const building = new THREE.Group();
building.add(walls, roof, windows);
scene.add(building);

// Use meaningful names
mesh.name = 'player-character';
const found = scene.getObjectByName('player-character');
```

### Common Pitfalls

#### 1. Not Updating Aspect Ratio on Resize
Always update camera aspect ratio and projection matrix when window resizes.

#### 2. Creating New Objects in Animation Loop
```javascript
// Bad: Memory leak
function animate() {
  const geometry = new THREE.BoxGeometry(); // Created every frame!
  // ...
}

// Good: Create once outside loop
const geometry = new THREE.BoxGeometry();
function animate() {
  // Reuse geometry
}
```

#### 3. Forgetting to Enable Shadows
Remember to enable shadows on renderer, lights, and objects.

#### 4. Z-Fighting (Flickering)
- Increase near plane distance
- Decrease far plane distance
- Avoid overlapping coplanar surfaces
- Use `material.polygonOffset = true` with `material.polygonOffsetFactor`

#### 5. Color Space Issues
```javascript
// Always set color space for textures
texture.colorSpace = THREE.SRGBColorSpace;

// Set renderer output encoding
renderer.outputColorSpace = THREE.SRGBColorSpace;
```

#### 6. Not Disposing Resources
Always call `.dispose()` on geometries, materials, textures, and renderers when no longer needed.

### Resources

This skill includes bundled resources to accelerate Three.js development:

#### References
- `3d-reference.md` (same folder): Three.js API, materials guide, optimization checklist

#### Scripts
- `../scripts/setup_scene.py`: Generate boilerplate Three.js scene setup code

#### Assets
- `../assets/starter_scene/`: Complete HTML/JS boilerplate project

### Advanced Topics

#### Custom Shaders (GLSL)
```javascript
const material = new THREE.ShaderMaterial({
  uniforms: {
    uTime: { value: 0.0 },
    uColor: { value: new THREE.Color(0x00ff00) }
  },
  vertexShader: `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: `
    uniform float uTime;
    uniform vec3 uColor;
    varying vec2 vUv;
    void main() {
      gl_FragColor = vec4(uColor * vUv.x, 1.0);
    }
  `
});
```

#### Render Targets (Render-to-Texture)
```javascript
const renderTarget = new THREE.WebGLRenderTarget(512, 512);

// Render scene to texture
renderer.setRenderTarget(renderTarget);
renderer.render(scene, camera);
renderer.setRenderTarget(null);

// Use texture
const material = new THREE.MeshBasicMaterial({
  map: renderTarget.texture
});
```

#### GPU Computation (GPGPU)
Use `GPUComputationRenderer` for particle simulations, cloth physics, etc.

### When to Use This Skill

Use this skill when:
- Building interactive 3D web experiences
- Creating product configurators or visualizers
- Implementing WebGL/WebGPU rendering
- Working with 3D models, scenes, or animations
- Optimizing Three.js performance
- Integrating Three.js with other libraries (GSAP, React, etc.)
- Debugging Three.js rendering issues

For React integration, use the **react-3d** skill.
For animation, combine with the **scroll-animation** skill.
For UI animations, use the **motion-framer** skill.

---

## React Three Fiber

### Overview

React Three Fiber (R3F) is a React renderer for Three.js that brings declarative, component-based 3D development to React applications. Instead of imperatively creating and managing Three.js objects, you build 3D scenes using JSX components that map directly to Three.js objects.

**When to Use This Skill**:
- Building 3D experiences within React applications
- Creating interactive product configurators or showcases
- Developing 3D portfolios, galleries, or storytelling experiences
- Building games or simulations in React
- Adding 3D elements to existing React projects
- When you need state management and React hooks with 3D graphics
- When working with React frameworks (Next.js, Gatsby, Remix)

**Key Benefits**:
- **Declarative**: Write 3D scenes like React components
- **React Integration**: Full access to hooks, context, state management
- **Reusability**: Create and share 3D component libraries
- **Performance**: Automatic render optimization and reconciliation
- **Ecosystem**: Works with Drei helpers, Zustand, Framer Motion, etc.
- **TypeScript Support**: Full type safety for Three.js objects

---

### Core Concepts

#### 1. Canvas Component

The `<Canvas>` component sets up a Three.js scene, camera, renderer, and render loop.

```jsx
import { Canvas } from '@react-three/fiber'

function App() {
  return (
    <Canvas
      camera={{ position: [0, 0, 5], fov: 75 }}
      gl={{ antialias: true }}
      dpr={[1, 2]}
    >
      {/* 3D content goes here */}
    </Canvas>
  )
}
```

**Canvas Props**:
- `camera` - Camera configuration (position, fov, near, far)
- `gl` - WebGL renderer settings
- `dpr` - Device pixel ratio (default: [1, 2])
- `shadows` - Enable shadow mapping (default: false)
- `frameloop` - "always" (default), "demand", or "never"
- `flat` - Disable color management for simpler colors
- `linear` - Use linear color space instead of sRGB

#### 2. Declarative 3D Objects

Three.js objects are created using JSX with kebab-case props:

```jsx
// THREE.Mesh + THREE.BoxGeometry + THREE.MeshStandardMaterial
<mesh position={[0, 0, 0]} rotation={[0, Math.PI / 4, 0]}>
  <boxGeometry args={[1, 1, 1]} />
  <meshStandardMaterial color="hotpink" />
</mesh>
```

**Prop Mapping**:
- `position` → `object.position.set(x, y, z)`
- `rotation` → `object.rotation.set(x, y, z)`
- `scale` → `object.scale.set(x, y, z)`
- `args` → Constructor arguments for geometry/material
- `attach` → Attach to parent property (e.g., `attach="material"`)

**Shorthand Notation**:
```jsx
// Full notation
<mesh position={[1, 2, 3]} />

// Axis-specific (dash notation)
<mesh position-x={1} position-y={2} position-z={3} />
```

#### 3. useFrame Hook

Execute code on every frame (animation loop):

```jsx
import { useFrame } from '@react-three/fiber'
import { useRef } from 'react'

function RotatingBox() {
  const meshRef = useRef()

  useFrame((state, delta) => {
    // Rotate mesh on every frame
    meshRef.current.rotation.x += delta
    meshRef.current.rotation.y += delta * 0.5

    // Access scene state
    const time = state.clock.elapsedTime
    meshRef.current.position.y = Math.sin(time) * 2
  })

  return (
    <mesh ref={meshRef}>
      <boxGeometry />
      <meshStandardMaterial color="orange" />
    </mesh>
  )
}
```

**useFrame Parameters**:
- `state` - Scene state (camera, scene, gl, clock, etc.)
- `delta` - Time since last frame (for frame-rate independence)
- `xrFrame` - XR frame data (for VR/AR)

**Important**: Never use `setState` inside `useFrame` - it causes unnecessary re-renders!

#### 4. useThree Hook

Access scene state and methods:

```jsx
import { useThree } from '@react-three/fiber'

function CameraInfo() {
  const { camera, gl, scene, size, viewport } = useThree()

  // Selective subscription (only re-render on size change)
  const size = useThree((state) => state.size)

  // Get state non-reactively
  const get = useThree((state) => state.get)
  const freshState = get() // Latest state without triggering re-render

  return null
}
```

**Available State**:
- `camera` - Default camera
- `scene` - Three.js scene
- `gl` - WebGL renderer
- `size` - Canvas dimensions
- `viewport` - Viewport dimensions in 3D units
- `clock` - Three.js clock
- `pointer` - Normalized mouse coordinates
- `invalidate()` - Manually trigger render
- `setSize()` - Manually resize canvas

#### 5. useLoader Hook

Load assets with automatic caching and Suspense integration:

```jsx
import { Suspense } from 'react'
import { useLoader } from '@react-three/fiber'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
import { TextureLoader } from 'three'

function Model() {
  const gltf = useLoader(GLTFLoader, '/model.glb')
  return <primitive object={gltf.scene} />
}

function TexturedMesh() {
  const texture = useLoader(TextureLoader, '/texture.jpg')
  return (
    <mesh>
      <boxGeometry />
      <meshStandardMaterial map={texture} />
    </mesh>
  )
}

function App() {
  return (
    <Canvas>
      <Suspense fallback={<LoadingIndicator />}>
        <Model />
        <TexturedMesh />
      </Suspense>
    </Canvas>
  )
}
```

**Loading Multiple Assets**:
```jsx
const [texture1, texture2, texture3] = useLoader(TextureLoader, [
  '/tex1.jpg',
  '/tex2.jpg',
  '/tex3.jpg'
])
```

**Loader Extensions**:
```jsx
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader'

useLoader(GLTFLoader, '/model.glb', (loader) => {
  const dracoLoader = new DRACOLoader()
  dracoLoader.setDecoderPath('/draco/')
  loader.setDRACOLoader(dracoLoader)
})
```

**Pre-loading**:
```jsx
// Pre-load assets before component mounts
useLoader.preload(GLTFLoader, '/model.glb')
```

---

### Common Patterns

#### Pattern 1: Basic Scene Setup

```jsx
import { Canvas } from '@react-three/fiber'

function Scene() {
  return (
    <>
      {/* Lights */}
      <ambientLight intensity={0.5} />
      <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} />

      {/* Objects */}
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color="hotpink" />
      </mesh>
    </>
  )
}

function App() {
  return (
    <Canvas camera={{ position: [0, 0, 5], fov: 75 }}>
      <Scene />
    </Canvas>
  )
}
```

#### Pattern 2: Interactive Objects (Click, Hover)

```jsx
import { useState } from 'react'

function InteractiveBox() {
  const [hovered, setHovered] = useState(false)
  const [active, setActive] = useState(false)

  return (
    <mesh
      scale={active ? 1.5 : 1}
      onClick={() => setActive(!active)}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
    >
      <boxGeometry />
      <meshStandardMaterial color={hovered ? 'hotpink' : 'orange'} />
    </mesh>
  )
}
```

#### Pattern 3: Animated Component with useFrame

```jsx
import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'

function AnimatedSphere() {
  const meshRef = useRef()

  useFrame((state, delta) => {
    // Rotate
    meshRef.current.rotation.y += delta

    // Oscillate position
    const time = state.clock.elapsedTime
    meshRef.current.position.y = Math.sin(time) * 2
  })

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[1, 32, 32]} />
      <meshStandardMaterial color="cyan" />
    </mesh>
  )
}
```

#### Pattern 4: Loading GLTF Models

```jsx
import { Suspense } from 'react'
import { useLoader } from '@react-three/fiber'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'

function Model({ url }) {
  const gltf = useLoader(GLTFLoader, url)

  return (
    <primitive
      object={gltf.scene}
      scale={0.5}
      position={[0, 0, 0]}
    />
  )
}

function App() {
  return (
    <Canvas>
      <Suspense fallback={<LoadingPlaceholder />}>
        <Model url="/model.glb" />
      </Suspense>
    </Canvas>
  )
}

function LoadingPlaceholder() {
  return (
    <mesh>
      <boxGeometry />
      <meshBasicMaterial wireframe />
    </mesh>
  )
}
```

#### Pattern 5: Multiple Lights

```jsx
function Lighting() {
  return (
    <>
      {/* Ambient light for base illumination */}
      <ambientLight intensity={0.3} />

      {/* Directional light with shadows */}
      <directionalLight
        position={[5, 5, 5]}
        intensity={1}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />

      {/* Point light for accent */}
      <pointLight position={[-5, 5, -5]} intensity={0.5} color="blue" />

      {/* Spot light for focused illumination */}
      <spotLight
        position={[10, 10, 10]}
        angle={0.3}
        penumbra={1}
        intensity={1}
      />
    </>
  )
}
```

#### Pattern 6: Instancing (Many Objects)

```jsx
import { useMemo, useRef } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'

function Particles({ count = 1000 }) {
  const meshRef = useRef()

  // Generate random positions
  const particles = useMemo(() => {
    const temp = []
    for (let i = 0; i < count; i++) {
      const t = Math.random() * 100
      const factor = 20 + Math.random() * 100
      const speed = 0.01 + Math.random() / 200
      const x = Math.random() * 2 - 1
      const y = Math.random() * 2 - 1
      const z = Math.random() * 2 - 1
      temp.push({ t, factor, speed, x, y, z, mx: 0, my: 0 })
    }
    return temp
  }, [count])

  const dummy = useMemo(() => new THREE.Object3D(), [])

  useFrame(() => {
    particles.forEach((particle, i) => {
      let { t, factor, speed, x, y, z } = particle
      t = particle.t += speed / 2
      const a = Math.cos(t) + Math.sin(t * 1) / 10
      const b = Math.sin(t) + Math.cos(t * 2) / 10
      const s = Math.cos(t)

      dummy.position.set(
        x + Math.cos((t / 10) * factor) + (Math.sin(t * 1) * factor) / 10,
        y + Math.sin((t / 10) * factor) + (Math.cos(t * 2) * factor) / 10,
        z + Math.cos((t / 10) * factor) + (Math.sin(t * 3) * factor) / 10
      )
      dummy.scale.set(s, s, s)
      dummy.updateMatrix()
      meshRef.current.setMatrixAt(i, dummy.matrix)
    })
    meshRef.current.instanceMatrix.needsUpdate = true
  })

  return (
    <instancedMesh ref={meshRef} args={[null, null, count]}>
      <sphereGeometry args={[0.05, 8, 8]} />
      <meshBasicMaterial color="white" />
    </instancedMesh>
  )
}
```

#### Pattern 7: Groups and Nesting

```jsx
function Robot() {
  return (
    <group position={[0, 0, 0]}>
      {/* Body */}
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[1, 2, 1]} />
        <meshStandardMaterial color="gray" />
      </mesh>

      {/* Head */}
      <mesh position={[0, 1.5, 0]}>
        <sphereGeometry args={[0.5, 32, 32]} />
        <meshStandardMaterial color="silver" />
      </mesh>

      {/* Arms */}
      <group position={[-0.75, 0.5, 0]}>
        <mesh>
          <cylinderGeometry args={[0.1, 0.1, 1.5]} />
          <meshStandardMaterial color="darkgray" />
        </mesh>
      </group>

      <group position={[0.75, 0.5, 0]}>
        <mesh>
          <cylinderGeometry args={[0.1, 0.1, 1.5]} />
          <meshStandardMaterial color="darkgray" />
        </mesh>
      </group>
    </group>
  )
}
```

---

### Integration with Drei Helpers

[Drei](https://github.com/pmndrs/drei) is the essential helper library for R3F, providing ready-to-use components:

#### OrbitControls

```jsx
import { OrbitControls } from '@react-three/drei'

<Canvas>
  <OrbitControls
    makeDefault
    enableDamping
    dampingFactor={0.05}
    minDistance={3}
    maxDistance={20}
  />
  <Box />
</Canvas>
```

#### Environment & Lighting

```jsx
import { Environment, ContactShadows } from '@react-three/drei'

<Canvas>
  {/* HDRI environment map */}
  <Environment preset="sunset" />

  {/* Or custom */}
  <Environment files="/hdri.hdr" />

  {/* Soft contact shadows */}
  <ContactShadows
    opacity={0.5}
    scale={10}
    blur={1}
    far={10}
    resolution={256}
  />

  <Model />
</Canvas>
```

#### Text

```jsx
import { Text, Text3D } from '@react-three/drei'

// 2D Billboard text
<Text
  position={[0, 2, 0]}
  fontSize={1}
  color="white"
  anchorX="center"
  anchorY="middle"
>
  Hello World
</Text>

// 3D extruded text
<Text3D
  font="/fonts/helvetiker_regular.typeface.json"
  size={1}
  height={0.2}
>
  3D Text
  <meshNormalMaterial />
</Text3D>
```

#### useGLTF Hook (Drei)

```jsx
import { useGLTF } from '@react-three/drei'

function Model() {
  const { scene, materials, nodes } = useGLTF('/model.glb')

  return <primitive object={scene} />
}

// Pre-load
useGLTF.preload('/model.glb')
```

#### Center & Bounds

```jsx
import { Center, Bounds, useBounds } from '@react-three/drei'

// Auto-center objects
<Center>
  <Model />
</Center>

// Auto-fit camera to bounds
<Bounds fit clip observe margin={1.2}>
  <Model />
</Bounds>
```

#### HTML Overlay

```jsx
import { Html } from '@react-three/drei'

<mesh>
  <boxGeometry />
  <meshStandardMaterial />

  <Html
    position={[0, 1, 0]}
    center
    distanceFactor={10}
  >
    <div className="annotation">
      This is a box
    </div>
  </Html>
</mesh>
```

#### Scroll Controls

```jsx
import { ScrollControls, Scroll, useScroll } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'

function AnimatedScene() {
  const scroll = useScroll()
  const meshRef = useRef()

  useFrame(() => {
    const offset = scroll.offset // 0-1 normalized scroll position
    meshRef.current.position.y = offset * 10
  })

  return <mesh ref={meshRef}>...</mesh>
}

<Canvas>
  <ScrollControls pages={3} damping={0.5}>
    <Scroll>
      <AnimatedScene />
    </Scroll>

    {/* HTML overlay */}
    <Scroll html>
      <div style={{ height: '100vh' }}>
        <h1>Scrollable content</h1>
      </div>
    </Scroll>
  </ScrollControls>
</Canvas>
```

---

### Integration with Other Libraries

#### With GSAP

```jsx
import { useRef, useEffect } from 'react'
import { useFrame } from '@react-three/fiber'
import gsap from 'gsap'

function AnimatedBox() {
  const meshRef = useRef()

  useEffect(() => {
    // GSAP timeline animation
    const tl = gsap.timeline({ repeat: -1, yoyo: true })

    tl.to(meshRef.current.position, {
      y: 2,
      duration: 1,
      ease: 'power2.inOut'
    })
    .to(meshRef.current.rotation, {
      y: Math.PI * 2,
      duration: 2,
      ease: 'none'
    }, 0)

    return () => tl.kill()
  }, [])

  return (
    <mesh ref={meshRef}>
      <boxGeometry />
      <meshStandardMaterial color="orange" />
    </mesh>
  )
}
```

#### With Framer Motion

```jsx
import { motion } from 'framer-motion-3d'

function AnimatedSphere() {
  return (
    <motion.mesh
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ duration: 1 }}
    >
      <sphereGeometry />
      <meshStandardMaterial color="hotpink" />
    </motion.mesh>
  )
}
```

#### With Zustand (State Management)

```jsx
import create from 'zustand'

const useStore = create((set) => ({
  color: 'orange',
  setColor: (color) => set({ color })
}))

function Box() {
  const color = useStore((state) => state.color)
  const setColor = useStore((state) => state.setColor)

  return (
    <mesh onClick={() => setColor('hotpink')}>
      <boxGeometry />
      <meshStandardMaterial color={color} />
    </mesh>
  )
}
```

---

### Performance Optimization

#### 1. On-Demand Rendering

```jsx
<Canvas frameloop="demand">
  {/* Only renders when needed */}
</Canvas>

// Manually trigger render
function MyComponent() {
  const invalidate = useThree((state) => state.invalidate)

  return (
    <mesh onClick={() => invalidate()}>
      <boxGeometry />
      <meshStandardMaterial />
    </mesh>
  )
}
```

#### 2. Instancing

Use `<instancedMesh>` for rendering many identical objects:

```jsx
function Particles({ count = 10000 }) {
  const meshRef = useRef()

  useEffect(() => {
    const temp = new THREE.Object3D()

    for (let i = 0; i < count; i++) {
      temp.position.set(
        Math.random() * 10 - 5,
        Math.random() * 10 - 5,
        Math.random() * 10 - 5
      )
      temp.updateMatrix()
      meshRef.current.setMatrixAt(i, temp.matrix)
    }

    meshRef.current.instanceMatrix.needsUpdate = true
  }, [count])

  return (
    <instancedMesh ref={meshRef} args={[null, null, count]}>
      <sphereGeometry args={[0.1, 8, 8]} />
      <meshBasicMaterial color="white" />
    </instancedMesh>
  )
}
```

#### 3. Frustum Culling

Objects outside the camera view are automatically culled.

```jsx
// Disable for always-visible objects
<mesh frustumCulled={false}>
  <boxGeometry />
  <meshStandardMaterial />
</mesh>
```

#### 4. LOD (Level of Detail)

```jsx
import { Detailed } from '@react-three/drei'

<Detailed distances={[0, 10, 20]}>
  {/* High detail - close to camera */}
  <mesh geometry={highPolyGeometry} />

  {/* Medium detail */}
  <mesh geometry={mediumPolyGeometry} />

  {/* Low detail - far from camera */}
  <mesh geometry={lowPolyGeometry} />
</Detailed>
```

#### 5. Adaptive Performance

```jsx
import { AdaptiveDpr, AdaptiveEvents, PerformanceMonitor } from '@react-three/drei'

<Canvas>
  {/* Reduce DPR when performance drops */}
  <AdaptiveDpr pixelated />

  {/* Reduce raycast frequency */}
  <AdaptiveEvents />

  {/* Monitor and respond to performance */}
  <PerformanceMonitor
    onIncline={() => console.log('Performance improved')}
    onDecline={() => console.log('Performance degraded')}
  >
    <Scene />
  </PerformanceMonitor>
</Canvas>
```

#### 6. Selective Re-renders

Use `useThree` selectors to avoid unnecessary re-renders:

```jsx
// ❌ Re-renders on any state change
const state = useThree()

// ✅ Only re-renders when size changes
const size = useThree((state) => state.size)

// ✅ Only re-renders when camera changes
const camera = useThree((state) => state.camera)
```

---

### Common Pitfalls & Solutions

#### ❌ Pitfall 1: setState in useFrame

```jsx
// ❌ BAD: Triggers React re-renders every frame
const [x, setX] = useState(0)
useFrame(() => setX((x) => x + 0.1))
return <mesh position-x={x} />
```

✅ **Solution**: Mutate refs directly

```jsx
// ✅ GOOD: Direct mutation, no re-renders
const meshRef = useRef()
useFrame((state, delta) => {
  meshRef.current.position.x += delta
})
return <mesh ref={meshRef} />
```

#### ❌ Pitfall 2: Creating Objects in Render

```jsx
// ❌ BAD: Creates new Vector3 every render
<mesh position={new THREE.Vector3(1, 2, 3)} />
```

✅ **Solution**: Use arrays or useMemo

```jsx
// ✅ GOOD: Use array notation
<mesh position={[1, 2, 3]} />

// Or useMemo for complex objects
const position = useMemo(() => new THREE.Vector3(1, 2, 3), [])
<mesh position={position} />
```

#### ❌ Pitfall 3: Not Using useLoader Cache

```jsx
// ❌ BAD: Loads texture every render
function Component() {
  const [texture, setTexture] = useState()
  useEffect(() => {
    new TextureLoader().load('/texture.jpg', setTexture)
  }, [])
  return texture ? <meshBasicMaterial map={texture} /> : null
}
```

✅ **Solution**: Use useLoader (automatic caching)

```jsx
// ✅ GOOD: Cached and reused
function Component() {
  const texture = useLoader(TextureLoader, '/texture.jpg')
  return <meshBasicMaterial map={texture} />
}
```

#### ❌ Pitfall 4: Conditional Mounting (Expensive)

```jsx
// ❌ BAD: Unmounts and remounts (expensive)
{stage === 1 && <Stage1 />}
{stage === 2 && <Stage2 />}
{stage === 3 && <Stage3 />}
```

✅ **Solution**: Use visibility prop

```jsx
// ✅ GOOD: Components stay mounted, just hidden
<Stage1 visible={stage === 1} />
<Stage2 visible={stage === 2} />
<Stage3 visible={stage === 3} />

function Stage1({ visible, ...props }) {
  return <group {...props} visible={visible}>...</group>
}
```

#### ❌ Pitfall 5: useThree Outside Canvas

```jsx
// ❌ BAD: Crashes - useThree must be inside Canvas
function App() {
  const { size } = useThree()
  return <Canvas>...</Canvas>
}
```

✅ **Solution**: Use hooks inside Canvas children

```jsx
// ✅ GOOD: useThree inside Canvas child
function CameraInfo() {
  const { size } = useThree()
  return null
}

function App() {
  return (
    <Canvas>
      <CameraInfo />
    </Canvas>
  )
}
```

#### ❌ Pitfall 6: Not Disposing Resources

```jsx
// ❌ BAD: Memory leak - textures not disposed
const texture = useLoader(TextureLoader, '/texture.jpg')
```

✅ **Solution**: R3F handles disposal automatically, but be careful with manual Three.js objects

```jsx
// ✅ GOOD: Manual cleanup when needed
useEffect(() => {
  const geometry = new THREE.SphereGeometry(1)
  const material = new THREE.MeshBasicMaterial()

  return () => {
    geometry.dispose()
    material.dispose()
  }
}, [])
```

---

### Best Practices

#### 1. Component Composition

Break scenes into reusable components:

```jsx
function Lights() {
  return (
    <>
      <ambientLight intensity={0.5} />
      <spotLight position={[10, 10, 10]} angle={0.15} />
    </>
  )
}

function Scene() {
  return (
    <>
      <Lights />
      <Model />
      <Ground />
      <Effects />
    </>
  )
}

<Canvas>
  <Scene />
</Canvas>
```

#### 2. Suspend Heavy Assets

Always wrap async operations in Suspense:

```jsx
<Canvas>
  <Suspense fallback={<Loader />}>
    <Model />
    <Environment />
  </Suspense>
</Canvas>
```

#### 3. Use TypeScript

```typescript
import { ThreeElements } from '@react-three/fiber'

function Box(props: ThreeElements['mesh']) {
  return (
    <mesh {...props}>
      <boxGeometry />
      <meshStandardMaterial />
    </mesh>
  )
}
```

#### 4. Organize by Feature

```
src/
  components/
    3d/
      Scene.tsx
      Lights.tsx
      Camera.tsx
    models/
      Robot.tsx
      Character.tsx
    effects/
      PostProcessing.tsx
```

#### 5. Test with React DevTools Profiler

Monitor re-renders and optimize components causing performance issues.

---

### Resources

#### References
- `3d-reference.md` (same folder) - Complete Three.js, R3F & Drei API documentation

#### Scripts
- `../scripts/component_generator.py` - Generate R3F component boilerplate
- `../scripts/scene_setup.py` - Initialize R3F scene with common patterns

#### Assets
- `../assets/starter_r3f/` - Complete R3F + Vite starter template
- `../assets/r3f-examples/` - Real-world R3F component examples

#### External Resources
- [Official Docs](https://docs.pmnd.rs/react-3d)
- [Drei Docs](https://github.com/pmndrs/drei)
- [Three.js Docs](https://threejs.org/docs/)
- [R3F Discord](https://discord.gg/ZZjjNvJ)
- [Poimandres (pmnd.rs)](https://pmnd.rs/) - Ecosystem overview
