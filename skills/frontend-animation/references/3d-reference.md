# 3D API Reference

Deep-dive Three.js API, materials, optimization checklist, and React Three Fiber/Drei API.

---

## Three.js API Quick Reference

### Core Classes

#### Scene
```javascript
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000);
scene.fog = new THREE.Fog(0xffffff, 10, 100);
scene.add(object);
scene.remove(object);
scene.getObjectByName('name');
```

#### Camera

##### PerspectiveCamera
```javascript
new THREE.PerspectiveCamera(fov, aspect, near, far);
camera.position.set(x, y, z);
camera.lookAt(target);
camera.updateProjectionMatrix(); // Call after changing properties
```

**Common FOVs:**
- 45° - Natural perspective
- 50° - Default for many apps
- 75° - Wide, immersive feel

##### OrthographicCamera
```javascript
new THREE.OrthographicCamera(left, right, top, bottom, near, far);
// Useful for 2D/isometric views
```

#### Renderer

##### WebGLRenderer
```javascript
const renderer = new THREE.WebGLRenderer({
  antialias: true,
  alpha: true,
  powerPreference: "high-performance"
});
renderer.setSize(width, height);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
```

##### WebGPURenderer
```javascript
const renderer = new THREE.WebGPURenderer({ antialias: true });
renderer.setAnimationLoop(animate);
```

### Geometry

#### Built-in Geometries
```javascript
new THREE.BoxGeometry(width, height, depth);
new THREE.SphereGeometry(radius, widthSegments, heightSegments);
new THREE.PlaneGeometry(width, height);
new THREE.CylinderGeometry(radiusTop, radiusBottom, height, radialSegments);
new THREE.TorusGeometry(radius, tube, radialSegments, tubularSegments);
```

#### BufferGeometry (Custom)
```javascript
const geometry = new THREE.BufferGeometry();
const vertices = new Float32Array([...]);
geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
geometry.computeVertexNormals();
geometry.computeBoundingSphere();
```

#### Geometry Operations
```javascript
geometry.dispose(); // Free memory
geometry.center(); // Center geometry at origin
geometry.scale(x, y, z);
geometry.rotateX(angle);
geometry.translate(x, y, z);
```

### Materials

#### Common Properties
```javascript
{
  color: 0xff0000,
  transparent: true,
  opacity: 0.5,
  side: THREE.DoubleSide, // FrontSide, BackSide, DoubleSide
  depthWrite: true,
  depthTest: true,
  wireframe: false
}
```

#### Material Types
```javascript
new THREE.MeshBasicMaterial({}); // Unlit
new THREE.MeshLambertMaterial({}); // Simple diffuse
new THREE.MeshPhongMaterial({ shininess: 30 }); // Specular
new THREE.MeshStandardMaterial({ roughness: 0.5, metalness: 0.5 }); // PBR
new THREE.MeshPhysicalMaterial({ // Advanced PBR
  roughness: 0.0,
  metalness: 0.0,
  clearcoat: 1.0,
  clearcoatRoughness: 0.1,
  transmission: 1.0,
  ior: 1.5
});
```

### Lights

#### AmbientLight
```javascript
new THREE.AmbientLight(0xffffff, 0.5);
// Illuminates all objects equally
```

#### DirectionalLight
```javascript
const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(5, 10, 7.5);
light.castShadow = true;
// Parallel rays (like sunlight)
```

#### PointLight
```javascript
const light = new THREE.PointLight(0xffffff, 1, distance, decay);
light.castShadow = true;
// Radiates in all directions
```

#### SpotLight
```javascript
const light = new THREE.SpotLight(0xffffff, 1, distance, angle, penumbra, decay);
light.target.position.set(x, y, z);
light.castShadow = true;
```

#### HemisphereLight
```javascript
new THREE.HemisphereLight(skyColor, groundColor, intensity);
// Sky and ground hemisphere lighting
```

#### Light Properties
```javascript
light.intensity = 1.0;
light.color.set(0xff0000);
light.power = 1700; // Lumens (for PointLight)
light.visible = false;
```

### Textures

#### TextureLoader
```javascript
const loader = new THREE.TextureLoader();
const texture = loader.load('texture.jpg', onLoad, onProgress, onError);

texture.colorSpace = THREE.SRGBColorSpace;
texture.wrapS = THREE.RepeatWrapping;
texture.wrapT = THREE.RepeatWrapping;
texture.repeat.set(2, 2);
texture.offset.set(0.5, 0.5);
texture.rotation = Math.PI / 4;
texture.minFilter = THREE.LinearMipmapLinearFilter;
texture.magFilter = THREE.LinearFilter;
texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
```

#### Texture Types
```javascript
material.map = diffuseTexture;
material.normalMap = normalTexture;
material.roughnessMap = roughnessTexture;
material.metalnessMap = metalnessTexture;
material.emissiveMap = emissiveTexture;
material.aoMap = aoTexture;
material.bumpMap = bumpTexture;
material.displacementMap = displacementTexture;
material.alphaMap = alphaTexture;
```

### Mesh

#### Creation
```javascript
const mesh = new THREE.Mesh(geometry, material);
mesh.position.set(x, y, z);
mesh.rotation.set(x, y, z); // Radians
mesh.scale.set(x, y, z);
mesh.castShadow = true;
mesh.receiveShadow = true;
mesh.visible = true;
mesh.name = 'my-mesh';
```

#### Transformations
```javascript
mesh.translateX(distance);
mesh.translateY(distance);
mesh.translateZ(distance);
mesh.rotateX(angle);
mesh.rotateY(angle);
mesh.rotateZ(angle);
mesh.lookAt(targetVector);
```

#### Matrix Operations
```javascript
mesh.updateMatrix();
mesh.updateMatrixWorld(force);
mesh.applyMatrix4(matrix);
```

### Groups
```javascript
const group = new THREE.Group();
group.add(mesh1, mesh2, mesh3);
group.position.set(x, y, z);
scene.add(group);
```

### Animation

#### AnimationMixer
```javascript
const mixer = new THREE.AnimationMixer(model);
const action = mixer.clipAction(gltf.animations[0]);
action.play();

// In animation loop:
const delta = clock.getDelta();
mixer.update(delta);
```

#### AnimationAction Methods
```javascript
action.play();
action.stop();
action.pause();
action.reset();
action.setLoop(THREE.LoopRepeat, Infinity);
action.setDuration(seconds);
action.clampWhenFinished = true;
action.fadeIn(duration);
action.fadeOut(duration);
action.crossFadeTo(otherAction, duration);
```

### Loaders

#### GLTFLoader
```javascript
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const loader = new GLTFLoader();
loader.load('model.glb', (gltf) => {
  scene.add(gltf.scene);
}, onProgress, onError);
```

#### DRACOLoader
```javascript
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('/draco/');
gltfLoader.setDRACOLoader(dracoLoader);
```

#### OBJLoader, FBXLoader
```javascript
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';
```

### Controls

#### OrbitControls
```javascript
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.minDistance = 5;
controls.maxDistance = 50;
controls.maxPolarAngle = Math.PI / 2;
controls.target.set(0, 0, 0);
controls.update(); // Call in animation loop if damping enabled
```

#### MapControls, TrackballControls, FlyControls
```javascript
import { MapControls } from 'three/addons/controls/MapControls.js';
import { TrackballControls } from 'three/addons/controls/TrackballControls.js';
import { FlyControls } from 'three/addons/controls/FlyControls.js';
```

### Raycaster
```javascript
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

function onMouseMove(event) {
  mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
}

raycaster.setFromCamera(mouse, camera);
const intersects = raycaster.intersectObjects(scene.children, true);

if (intersects.length > 0) {
  const object = intersects[0].object;
  const point = intersects[0].point; // Intersection point
  const face = intersects[0].face; // Intersected face
  const distance = intersects[0].distance;
}
```

### Math Utilities

#### Vector3
```javascript
const v = new THREE.Vector3(x, y, z);
v.set(x, y, z);
v.add(otherVector);
v.sub(otherVector);
v.multiply(otherVector);
v.multiplyScalar(scalar);
v.normalize();
v.length();
v.distanceTo(otherVector);
v.lerp(otherVector, alpha);
v.cross(otherVector);
v.dot(otherVector);
```

#### Quaternion
```javascript
const q = new THREE.Quaternion();
q.setFromEuler(euler);
q.setFromAxisAngle(axis, angle);
mesh.quaternion.copy(q);
```

#### Clock
```javascript
const clock = new THREE.Clock();
const delta = clock.getDelta(); // Time since last call
const elapsed = clock.getElapsedTime(); // Total time
clock.start();
clock.stop();
```

### Post-Processing

#### EffectComposer
```javascript
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
composer.render();
```

#### Common Passes
```javascript
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { SSAOPass } from 'three/addons/postprocessing/SSAOPass.js';
import { SMAAPass } from 'three/addons/postprocessing/SMAAPass.js';
import { OutlinePass } from 'three/addons/postprocessing/OutlinePass.js';
```

### Helpers

```javascript
new THREE.AxesHelper(size);
new THREE.GridHelper(size, divisions);
new THREE.CameraHelper(camera);
new THREE.DirectionalLightHelper(light, size);
new THREE.SpotLightHelper(light);
new THREE.BoxHelper(object, color);
```

### Constants

#### Side
- `THREE.FrontSide` (default)
- `THREE.BackSide`
- `THREE.DoubleSide`

#### Blending Modes
- `THREE.NormalBlending` (default)
- `THREE.AdditiveBlending`
- `THREE.SubtractiveBlending`
- `THREE.MultiplyBlending`

#### Shadow Map Types
- `THREE.BasicShadowMap`
- `THREE.PCFShadowMap`
- `THREE.PCFSoftShadowMap`
- `THREE.VSMShadowMap`

#### Tone Mapping
- `THREE.NoToneMapping`
- `THREE.LinearToneMapping`
- `THREE.ReinhardToneMapping`
- `THREE.CineonToneMapping`
- `THREE.ACESFilmicToneMapping`

#### Color Spaces
- `THREE.SRGBColorSpace`
- `THREE.LinearSRGBColorSpace`

### Performance Tips

```javascript
// Dispose resources
geometry.dispose();
material.dispose();
texture.dispose();
renderer.dispose();

// Frustum culling (automatic)
mesh.frustumCulled = true;

// Matrix updates
mesh.matrixAutoUpdate = false; // Manual control
mesh.updateMatrix();

// Render on demand
function render() {
  renderer.render(scene, camera);
}
// Call render() only when needed

// Use InstancedMesh for repeated objects
const instancedMesh = new THREE.InstancedMesh(geometry, material, count);
```

### Common Gotchas

1. **Always update projection matrix after changing camera properties**
2. **Set texture.colorSpace = THREE.SRGBColorSpace for diffuse textures**
3. **Enable shadows on renderer, lights, and objects**
4. **Dispose geometries, materials, and textures to prevent memory leaks**
5. **Use Clock.getDelta() for frame-independent animations**
6. **Call controls.update() in animation loop if damping is enabled**

---

## Three.js Materials Comprehensive Guide

### Material Selection Decision Tree

```
Need lighting?
├─ NO → MeshBasicMaterial
└─ YES → Need PBR realism?
    ├─ NO → Need specular highlights?
    │   ├─ YES → MeshPhongMaterial
    │   └─ NO → MeshLambertMaterial
    └─ YES → Need advanced effects?
        ├─ YES → MeshPhysicalMaterial
        └─ NO → MeshStandardMaterial
```

### Material Comparison Table

| Material | Lighting | PBR | Performance | Use Case |
|----------|----------|-----|-------------|----------|
| MeshBasicMaterial | ✗ | ✗ | Excellent | UI, debugging, unlit scenes |
| MeshLambertMaterial | ✓ | ✗ | Very Good | Mobile, simple diffuse |
| MeshPhongMaterial | ✓ | ✗ | Good | Legacy, specular highlights |
| MeshStandardMaterial | ✓ | ✓ | Moderate | Most realistic scenes |
| MeshPhysicalMaterial | ✓ | ✓✓ | Lower | Advanced materials (glass, car paint) |
| MeshToonMaterial | ✓ | ✗ | Very Good | Cel-shaded / cartoon style |
| ShaderMaterial | Custom | Custom | Varies | Complete custom control |

### MeshBasicMaterial

**Use for:** UI elements, debugging, flat-colored objects, unlit scenes

```javascript
const material = new THREE.MeshBasicMaterial({
  color: 0xff0000,
  wireframe: false,
  transparent: false,
  opacity: 1.0,
  side: THREE.FrontSide,
  map: texture,
  alphaMap: alphaTexture,
  envMap: environmentMap,
  combine: THREE.MultiplyOperation, // For envMap
  reflectivity: 1.0,
  refractionRatio: 0.98
});
```

**Key Features:**
- No lighting calculations (fastest)
- Flat, unshaded appearance
- Always visible regardless of lights
- Good for backgrounds, UI, or stylized looks

**Performance:** ⭐⭐⭐⭐⭐

### MeshLambertMaterial

**Use for:** Mobile devices, simple diffuse surfaces, performance-critical scenes

```javascript
const material = new THREE.MeshLambertMaterial({
  color: 0xff0000,
  emissive: 0x000000,
  emissiveIntensity: 1.0,
  emissiveMap: null,
  map: texture,
  lightMap: lightMapTexture,
  lightMapIntensity: 1.0,
  aoMap: aoTexture,
  aoMapIntensity: 1.0
});
```

**Key Features:**
- Simple diffuse (matte) lighting
- No specular highlights
- Cheaper than Phong/Standard
- Good for organic, non-reflective surfaces

**Performance:** ⭐⭐⭐⭐

### MeshPhongMaterial

**Use for:** Legacy projects, objects with visible specular highlights

```javascript
const material = new THREE.MeshPhongMaterial({
  color: 0xff0000,
  specular: 0x111111,
  shininess: 30,
  emissive: 0x000000,
  emissiveIntensity: 1.0,
  map: texture,
  normalMap: normalTexture,
  normalScale: new THREE.Vector2(1, 1),
  bumpMap: bumpTexture,
  bumpScale: 1.0,
  specularMap: specTexture
});
```

**Key Features:**
- Diffuse + specular highlights
- Adjustable shininess
- Per-pixel lighting
- Legacy, prefer MeshStandardMaterial for new projects

**Performance:** ⭐⭐⭐

### MeshStandardMaterial (PBR)

**Use for:** Realistic materials, production-quality scenes, modern workflows

```javascript
const material = new THREE.MeshStandardMaterial({
  color: 0xffffff,
  roughness: 0.5, // 0 = mirror, 1 = matte
  metalness: 0.5, // 0 = dielectric, 1 = metal
  map: diffuseTexture,
  normalMap: normalTexture,
  normalScale: new THREE.Vector2(1, 1),
  roughnessMap: roughnessTexture,
  metalnessMap: metalnessTexture,
  aoMap: aoTexture,
  aoMapIntensity: 1.0,
  emissive: 0x000000,
  emissiveMap: emissiveTexture,
  emissiveIntensity: 1.0,
  envMap: environmentMap,
  envMapIntensity: 1.0,
  bumpMap: bumpTexture,
  bumpScale: 1.0,
  displacementMap: dispTexture,
  displacementScale: 1.0,
  displacementBias: 0.0,
  alphaMap: alphaTexture,
  flatShading: false
});
```

**Key Features:**
- Physically Based Rendering (PBR)
- Energy-conserving reflections
- Works with HDR environment maps
- Industry-standard workflow (glTF)

**Roughness Guide:**
- 0.0 - Perfect mirror (chrome, polished metal)
- 0.2 - Very glossy (wet surfaces, varnished wood)
- 0.5 - Moderate (painted metal, plastic)
- 0.8 - Matte (fabric, unpolished wood)
- 1.0 - Completely diffuse (clay, concrete)

**Metalness Guide:**
- 0.0 - Non-metal (wood, plastic, skin, fabric)
- 1.0 - Metal (gold, silver, copper, iron)
- Avoid values between 0-1 (physically incorrect)

**Performance:** ⭐⭐⭐

### MeshPhysicalMaterial (Advanced PBR)

**Use for:** Glass, car paint, clearcoat, transmission, iridescence

```javascript
const material = new THREE.MeshPhysicalMaterial({
  // All MeshStandardMaterial properties, plus:

  clearcoat: 1.0, // 0-1, adds glossy layer on top
  clearcoatRoughness: 0.1,
  clearcoatMap: clearcoatTexture,
  clearcoatRoughnessMap: clearcoatRoughnessTexture,
  clearcoatNormalMap: clearcoatNormalTexture,
  clearcoatNormalScale: new THREE.Vector2(1, 1),

  transmission: 1.0, // 0-1, for glass/transparency
  thickness: 1.0, // Subsurface thickness
  thicknessMap: thicknessTexture,

  ior: 1.5, // Index of refraction (glass ~1.5, water ~1.33, diamond ~2.4)

  sheen: 1.0, // Fabric-like sheen
  sheenRoughness: 0.5,
  sheenColor: new THREE.Color(0xffffff),

  iridescence: 1.0, // Soap bubble, oil slick effect
  iridescenceIOR: 1.3,
  iridescenceThicknessRange: [100, 400]
});
```

**Use Cases:**

#### Glass
```javascript
{
  roughness: 0.0,
  metalness: 0.0,
  transmission: 1.0,
  thickness: 1.0,
  ior: 1.5
}
```

#### Car Paint
```javascript
{
  roughness: 0.4,
  metalness: 0.8,
  clearcoat: 1.0,
  clearcoatRoughness: 0.1,
  color: 0xff0000
}
```

#### Fabric (Velvet, Satin)
```javascript
{
  roughness: 0.8,
  metalness: 0.0,
  sheen: 1.0,
  sheenRoughness: 0.5,
  sheenColor: new THREE.Color(0xffffff)
}
```

#### Soap Bubble
```javascript
{
  roughness: 0.0,
  metalness: 0.0,
  transmission: 1.0,
  thickness: 0.5,
  iridescence: 1.0,
  iridescenceIOR: 1.3
}
```

**Performance:** ⭐⭐

### MeshToonMaterial

**Use for:** Cel-shaded, cartoon, or stylized looks

```javascript
const material = new THREE.MeshToonMaterial({
  color: 0xff0000,
  map: texture,
  gradientMap: gradientTexture, // Controls toon shading steps
  emissive: 0x000000
});
```

**Key Features:**
- Discrete shading levels (cel-shaded)
- Stylized, non-realistic look
- Good performance

**Performance:** ⭐⭐⭐⭐

### Material Properties Deep Dive

#### Common Properties (All Materials)

```javascript
{
  // Visibility
  visible: true,
  transparent: false,
  opacity: 1.0,
  alphaTest: 0.5, // Discard pixels below this alpha

  // Rendering
  side: THREE.FrontSide, // FrontSide, BackSide, DoubleSide
  depthTest: true,
  depthWrite: true,
  blending: THREE.NormalBlending,

  // Color
  color: 0xffffff,
  vertexColors: false,

  // Wireframe
  wireframe: false,
  wireframeLinewidth: 1, // Not all platforms support

  // Clipping
  clipShadows: false,
  clipIntersection: false,
  clippingPlanes: [],

  // Precision
  precision: "highp", // "lowp", "mediump", "highp"

  // Fog
  fog: true
}
```

#### Texture Properties

```javascript
const texture = loader.load('texture.jpg');

// Color space (IMPORTANT!)
texture.colorSpace = THREE.SRGBColorSpace; // For diffuse/color maps
texture.colorSpace = THREE.LinearSRGBColorSpace; // For data maps (normal, roughness)

// Wrapping
texture.wrapS = THREE.RepeatWrapping; // ClampToEdgeWrapping, MirroredRepeatWrapping
texture.wrapT = THREE.RepeatWrapping;

// Repeat & Offset
texture.repeat.set(2, 2); // Tile 2x2
texture.offset.set(0.5, 0.5);
texture.rotation = Math.PI / 4;
texture.center.set(0.5, 0.5); // Rotation center

// Filtering
texture.minFilter = THREE.LinearMipmapLinearFilter; // Minification
texture.magFilter = THREE.LinearFilter; // Magnification
texture.anisotropy = renderer.capabilities.getMaxAnisotropy(); // Reduce blur at angles

// Mipmaps
texture.generateMipmaps = true;
```

#### Texture Types & Color Spaces

| Texture Type | Color Space | Purpose |
|--------------|-------------|---------|
| map (diffuse) | SRGB | Base color |
| normalMap | Linear | Surface detail |
| roughnessMap | Linear | Surface roughness |
| metalnessMap | Linear | Metallic areas |
| aoMap | Linear | Ambient occlusion |
| emissiveMap | SRGB | Glow |
| bumpMap | Linear | Height data |
| displacementMap | Linear | Vertex displacement |
| alphaMap | Linear | Transparency mask |

### Material Optimization Tips

#### 1. Texture Atlas
Combine multiple textures into one to reduce draw calls.

#### 2. Share Materials
```javascript
// Good: Share material across meshes
const sharedMaterial = new THREE.MeshStandardMaterial({...});
const mesh1 = new THREE.Mesh(geo1, sharedMaterial);
const mesh2 = new THREE.Mesh(geo2, sharedMaterial);

// Bad: New material per mesh
const mesh1 = new THREE.Mesh(geo1, new THREE.MeshStandardMaterial({...}));
```

#### 3. Texture Size
- Use power-of-two dimensions (512, 1024, 2048)
- Compress textures (JPEG for photos, PNG for alpha)
- Consider KTX2/Basis Universal for web

#### 4. Disable Unnecessary Features
```javascript
material.needsUpdate = false; // After initial setup
renderer.shadowMap.autoUpdate = false; // If shadows don't change
```

#### 5. Use InstancedMesh with Materials
For identical objects with the same material.

### Custom Shaders (ShaderMaterial)

**Use for:** Complete custom control, special effects, optimizations

```javascript
const material = new THREE.ShaderMaterial({
  uniforms: {
    uTime: { value: 0.0 },
    uColor: { value: new THREE.Color(0xff0000) },
    uTexture: { value: texture }
  },
  vertexShader: `
    uniform float uTime;
    varying vec2 vUv;
    varying vec3 vNormal;

    void main() {
      vUv = uv;
      vNormal = normal;

      vec3 pos = position;
      pos.z += sin(pos.x * 10.0 + uTime) * 0.1;

      gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
    }
  `,
  fragmentShader: `
    uniform vec3 uColor;
    uniform sampler2D uTexture;
    varying vec2 vUv;
    varying vec3 vNormal;

    void main() {
      vec4 texColor = texture2D(uTexture, vUv);
      gl_FragColor = vec4(uColor * texColor.rgb, 1.0);
    }
  `,
  transparent: false,
  side: THREE.DoubleSide
});

// Update uniforms in animation loop
material.uniforms.uTime.value = elapsedTime;
```

### Material Disposal

Always dispose materials when no longer needed:

```javascript
material.dispose();

// Dispose textures too
if (material.map) material.map.dispose();
if (material.normalMap) material.normalMap.dispose();
if (material.roughnessMap) material.roughnessMap.dispose();
// ... etc
```

### Troubleshooting

#### Material Appears Black
- No lights in scene (for Lambert/Phong/Standard)
- Normals inverted
- Material side setting incorrect

#### Material Too Shiny
- Reduce roughness (Standard/Physical)
- Reduce shininess (Phong)
- Check roughnessMap is loaded

#### Material Not Transparent
```javascript
material.transparent = true;
material.opacity = 0.5;
material.depthWrite = false; // For glass-like materials
```

#### Texture Not Showing
- Check texture.colorSpace (SRGB for diffuse)
- Ensure geometry has UV coordinates
- Verify texture loaded successfully

#### Z-Fighting / Flickering
- Adjust material.polygonOffset
```javascript
material.polygonOffset = true;
material.polygonOffsetFactor = -1;
material.polygonOffsetUnits = -1;
```

### Material Performance Ranking

1. **MeshBasicMaterial** - Fastest
2. **MeshToonMaterial** - Very Fast
3. **MeshLambertMaterial** - Fast
4. **MeshPhongMaterial** - Moderate
5. **MeshStandardMaterial** - Moderate-Slow
6. **MeshPhysicalMaterial** - Slowest

Use the simplest material that achieves your visual goals.

---

## Three.js Performance Optimization Checklist

### Quick Wins (High Impact, Low Effort)

#### ✅ Geometry Optimization

- [ ] **Reuse geometries** across multiple meshes
  ```javascript
  const sharedGeometry = new THREE.BoxGeometry(1, 1, 1);
  // Use for all boxes instead of creating new geometry each time
  ```

- [ ] **Use InstancedMesh** for repeated objects (>50 identical objects)
  ```javascript
  const mesh = new THREE.InstancedMesh(geometry, material, 1000);
  ```

- [ ] **Reduce polygon count** where not visible
  - Use simpler geometries for distant objects
  - Implement LOD (Level of Detail)

- [ ] **Dispose unused geometries**
  ```javascript
  geometry.dispose();
  ```

#### ✅ Material Optimization

- [ ] **Share materials** across meshes when possible
- [ ] **Use simpler materials**:
  - MeshBasicMaterial for unlit objects
  - MeshLambertMaterial for mobile
  - MeshStandardMaterial only when PBR needed
- [ ] **Dispose unused materials**
  ```javascript
  material.dispose();
  ```

#### ✅ Texture Optimization

- [ ] **Use power-of-two dimensions** (512, 1024, 2048)
- [ ] **Compress textures**:
  - JPEG for photos (smaller file size)
  - PNG for transparency
  - Consider KTX2/Basis Universal for web
- [ ] **Set correct color space**:
  ```javascript
  diffuseTexture.colorSpace = THREE.SRGBColorSpace;
  normalMap.colorSpace = THREE.LinearSRGBColorSpace;
  ```
- [ ] **Limit texture resolution**:
  - 2048x2048 max for most cases
  - 1024x1024 for mobile
  - 512x512 for background/UI elements
- [ ] **Enable mipmaps and anisotropy**:
  ```javascript
  texture.generateMipmaps = true;
  texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
  ```
- [ ] **Dispose unused textures**:
  ```javascript
  texture.dispose();
  ```

#### ✅ Rendering Optimization

- [ ] **Set pixel ratio appropriately**:
  ```javascript
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  // Don't use full devicePixelRatio on high-DPI displays
  ```
- [ ] **Disable antialiasing on mobile**
- [ ] **Use render-on-demand** when scene is static:
  ```javascript
  function render() {
    renderer.render(scene, camera);
  }
  // Call only when needed, not in requestAnimationFrame loop
  ```

#### ✅ Shadow Optimization

- [ ] **Limit number of shadow-casting lights** (2-3 max)
- [ ] **Reduce shadow map size**:
  ```javascript
  light.shadow.mapSize.width = 1024; // Lower for mobile
  light.shadow.mapSize.height = 1024;
  ```
- [ ] **Optimize shadow camera frustum**:
  ```javascript
  light.shadow.camera.near = 1;
  light.shadow.camera.far = 20; // Only as far as needed
  light.shadow.camera.left = -10;
  light.shadow.camera.right = 10;
  // ... etc - Tight bounds around scene
  ```
- [ ] **Disable shadow updates** when static:
  ```javascript
  renderer.shadowMap.autoUpdate = false;
  renderer.shadowMap.needsUpdate = true; // Only when changed
  ```

### Medium Effort Optimizations

#### 🔧 Culling & Visibility

- [ ] **Enable frustum culling** (enabled by default):
  ```javascript
  mesh.frustumCulled = true;
  ```
- [ ] **Compute bounding spheres** for custom geometries:
  ```javascript
  geometry.computeBoundingSphere();
  ```
- [ ] **Hide offscreen objects**:
  ```javascript
  if (distanceToCamera > threshold) {
    mesh.visible = false;
  }
  ```
- [ ] **Use layers** for selective rendering:
  ```javascript
  mesh.layers.set(1);
  camera.layers.enable(1);
  ```

#### 🔧 Level of Detail (LOD)

- [ ] **Implement LOD** for complex objects:
  ```javascript
  const lod = new THREE.LOD();
  lod.addLevel(highDetailMesh, 0);
  lod.addLevel(mediumDetailMesh, 50);
  lod.addLevel(lowDetailMesh, 100);
  scene.add(lod);
  ```

#### 🔧 Draw Call Reduction

- [ ] **Merge static geometries**:
  ```javascript
  import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
  const merged = mergeGeometries([geo1, geo2, geo3]);
  ```
- [ ] **Use texture atlases** to combine multiple textures
- [ ] **Batch similar materials** together

#### 🔧 Animation Optimization

- [ ] **Use Clock.getDelta()** for frame-independent animations:
  ```javascript
  const delta = clock.getDelta();
  mixer.update(delta);
  ```
- [ ] **Pause animations** when offscreen:
  ```javascript
  if (!mesh.visible) {
    mixer.stop();
  }
  ```
- [ ] **Limit AnimationMixer updates** to visible objects

#### 🔧 Post-Processing Optimization

- [ ] **Reduce effect quality** on mobile
- [ ] **Limit bloom/blur passes**
- [ ] **Use lower resolution render targets**:
  ```javascript
  const renderTarget = new THREE.WebGLRenderTarget(
    window.innerWidth * 0.5,
    window.innerHeight * 0.5
  );
  ```

### Advanced Optimizations

#### ⚙️ Memory Management

- [ ] **Dispose all resources** when removing from scene:
  ```javascript
  function disposeObject(obj) {
    if (obj.geometry) obj.geometry.dispose();
    if (obj.material) {
      if (Array.isArray(obj.material)) {
        obj.material.forEach(m => m.dispose());
      } else {
        obj.material.dispose();
      }
    }
    if (obj.dispose) obj.dispose();
  }

  scene.traverse(disposeObject);
  ```

- [ ] **Clear render targets** when done:
  ```javascript
  renderTarget.dispose();
  ```

- [ ] **Monitor memory usage**:
  ```javascript
  console.log(renderer.info.memory);
  console.log(renderer.info.render);
  ```

#### ⚙️ Matrix Optimization

- [ ] **Disable auto-update** for static objects:
  ```javascript
  mesh.matrixAutoUpdate = false;
  mesh.updateMatrix();
  ```

- [ ] **Update world matrix** manually when needed:
  ```javascript
  mesh.matrixWorldNeedsUpdate = true;
  ```

#### ⚙️ Custom Shaders

- [ ] **Use low precision** where possible:
  ```glsl
  precision mediump float; // Instead of highp
  ```

- [ ] **Minimize texture samples** in fragment shader
- [ ] **Move calculations** to vertex shader when possible
- [ ] **Use built-in GLSL functions** (faster than custom)

#### ⚙️ Lighting Optimization

- [ ] **Limit number of real-time lights** (3-5 max)
- [ ] **Use baked lighting** for static scenes:
  - Lightmaps
  - AO maps
  - Environment maps
- [ ] **Combine directional lights** where possible
- [ ] **Use AmbientLight + DirectionalLight** as base setup

#### ⚙️ Model Optimization

- [ ] **Use glTF with Draco compression**:
  ```javascript
  const dracoLoader = new DRACOLoader();
  dracoLoader.setDecoderPath('/draco/');
  gltfLoader.setDRACOLoader(dracoLoader);
  ```

- [ ] **Remove unused data** from models:
  - Multiple UV sets
  - Unused vertex colors
  - Unused morph targets

- [ ] **Optimize mesh topology**:
  - Remove hidden faces
  - Reduce triangle count
  - Use instancing for repeated elements

### Mobile-Specific Optimizations

#### 📱 Mobile Best Practices

- [ ] **Lower pixel ratio**:
  ```javascript
  renderer.setPixelRatio(1);
  ```

- [ ] **Disable antialiasing**
- [ ] **Use simpler materials** (MeshLambertMaterial)
- [ ] **Reduce texture resolution** (512-1024px max)
- [ ] **Limit particle count** (<1000)
- [ ] **Disable shadows** or use lower resolution
- [ ] **Reduce geometry complexity** by 50%
- [ ] **Disable post-processing** or use minimal effects
- [ ] **Implement aggressive LOD**
- [ ] **Pause rendering** when tab is hidden:
  ```javascript
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      // Stop animation loop
    } else {
      // Resume animation loop
    }
  });
  ```

### Profiling & Debugging

#### 🔍 Performance Monitoring

- [ ] **Use Stats.js**:
  ```javascript
  import Stats from 'three/examples/jsm/libs/stats.module.js';
  const stats = new Stats();
  document.body.appendChild(stats.dom);
  ```

- [ ] **Monitor renderer info**:
  ```javascript
  console.log('Geometries:', renderer.info.memory.geometries);
  console.log('Textures:', renderer.info.memory.textures);
  console.log('Draw Calls:', renderer.info.render.calls);
  console.log('Triangles:', renderer.info.render.triangles);
  ```

- [ ] **Use browser DevTools**:
  - Performance tab (frame rate)
  - Memory tab (heap snapshots)
  - Rendering tab (FPS meter, paint flashing)

- [ ] **WebGL Performance Tools**:
  - Spector.js (WebGL inspector)
  - Chrome GPU Profiler

#### 🔍 Common Performance Bottlenecks

1. **Too many draw calls** → Merge geometries, use instancing
2. **Too many triangles** → Reduce geometry complexity, use LOD
3. **Large textures** → Compress, reduce resolution
4. **Too many lights** → Limit lights, use baked lighting
5. **Complex shaders** → Simplify materials
6. **Memory leaks** → Dispose resources properly
7. **Expensive post-processing** → Reduce effects, lower resolution

### Performance Targets

#### 🎯 Desktop
- **60 FPS** (16.67ms per frame)
- **Draw calls**: <100
- **Triangles**: <1M visible
- **Texture memory**: <500MB
- **Pixel ratio**: 1-2

#### 🎯 Mobile
- **30-60 FPS** (16.67-33ms per frame)
- **Draw calls**: <50
- **Triangles**: <100K visible
- **Texture memory**: <200MB
- **Pixel ratio**: 1

### Optimization Workflow

1. **Profile first** - Identify actual bottlenecks
2. **Optimize bottlenecks** - Focus on highest impact
3. **Measure improvement** - Verify gains
4. **Iterate** - Repeat process

**Remember:** Premature optimization is the root of all evil. Profile before optimizing!

### Quick Optimization Checklist Summary

```
✅ Reuse geometries and materials
✅ Use InstancedMesh for repeated objects
✅ Optimize texture size and format
✅ Set pixel ratio to max 2
✅ Limit shadow-casting lights
✅ Dispose unused resources
✅ Implement LOD for complex objects
✅ Reduce draw calls via merging
✅ Profile with Stats.js
✅ Test on target devices (mobile!)
```

---

## React Three Fiber API Reference

Complete API reference for React Three Fiber core and essential Drei helpers.

---

### Table of Contents

1. [Canvas Component](#canvas-component)
2. [Hooks](#hooks)
3. [Events](#events)
4. [Three.js Object Props](#threejs-object-props)
5. [Drei Helpers](#drei-helpers)

---

### Canvas Component

The `<Canvas>` component is the root of every R3F scene. It sets up the renderer, scene, and camera.

#### Props

```typescript
interface CanvasProps {
  children: React.ReactNode

  // Rendering
  gl?: Partial<WebGLRendererParameters> | ((canvas: HTMLCanvasElement) => WebGLRenderer)
  dpr?: number | [min: number, max: number]
  frameloop?: 'always' | 'demand' | 'never'
  flat?: boolean
  linear?: boolean
  legacy?: boolean

  // Camera
  camera?: Partial<PerspectiveCamera> | Partial<OrthographicCamera>
  orthographic?: boolean

  // Scene
  shadows?: boolean | Partial<WebGLShadowMap>
  raycaster?: Partial<Raycaster>

  // Events
  events?: EventManager
  eventSource?: HTMLElement | React.RefObject<HTMLElement>
  eventPrefix?: 'offset' | 'client' | 'page' | 'layer' | 'screen'

  // Size
  resize?: { scroll?: boolean; debounce?: number | { scroll: number; resize: number } }

  // Performance
  performance?: {
    current?: number
    min?: number
    max?: number
    debounce?: number
  }

  // Callbacks
  onCreated?: (state: RootState) => void
  onPointerMissed?: (event: MouseEvent) => void
}
```

#### Examples

```jsx
// Basic setup
<Canvas>
  <Scene />
</Canvas>

// Custom camera
<Canvas camera={{ position: [0, 0, 5], fov: 75, near: 0.1, far: 1000 }}>
  <Scene />
</Canvas>

// Orthographic camera
<Canvas orthographic camera={{ zoom: 50, position: [0, 0, 5] }}>
  <Scene />
</Canvas>

// Enable shadows
<Canvas shadows>
  <Scene />
</Canvas>

// Custom renderer settings
<Canvas
  gl={{
    antialias: true,
    alpha: true,
    powerPreference: 'high-performance'
  }}
  dpr={[1, 2]}
>
  <Scene />
</Canvas>

// On-demand rendering
<Canvas frameloop="demand">
  <Scene />
</Canvas>

// Performance monitoring
<Canvas
  performance={{ min: 0.5, max: 1, debounce: 200 }}
  onCreated={(state) => console.log('Canvas created:', state)}
>
  <Scene />
</Canvas>
```

---

### Hooks

#### useFrame

Execute code on every rendered frame.

```typescript
useFrame(
  callback: (state: RootState, delta: number, xrFrame?: XRFrame) => void,
  renderPriority?: number
): void
```

**Parameters**:
- `callback` - Function called every frame
- `renderPriority` - Execution order (default: 0, higher = later)

**State Object**:
```typescript
interface RootState {
  gl: WebGLRenderer
  scene: Scene
  camera: Camera
  raycaster: Raycaster
  pointer: Vector2
  mouse: Vector2 // Deprecated, use pointer
  clock: Clock
  size: { width: number; height: number; top: number; left: number }
  viewport: {
    width: number
    height: number
    initialDpr: number
    dpr: number
    factor: number
    distance: number
    aspect: number
  }
  performance: { current: number; min: number; max: number; debounce: number }
  frameloop: 'always' | 'demand' | 'never'
  controls: any
  invalidate: (frames?: number) => void
  advance: (timestamp: number, runGlobalEffects?: boolean) => void
  setSize: (width: number, height: number) => void
  setDpr: (dpr: number) => void
  setFrameloop: (frameloop: 'always' | 'demand' | 'never') => void
  get: () => RootState
  set: (partial: Partial<RootState>) => void
}
```

**Examples**:

```jsx
// Basic animation
function RotatingBox() {
  const meshRef = useRef()

  useFrame((state, delta) => {
    meshRef.current.rotation.x += delta
    meshRef.current.rotation.y += delta * 0.5
  })

  return <mesh ref={meshRef}>...</mesh>
}

// Access clock for time-based animations
function FloatingBox() {
  const meshRef = useRef()

  useFrame((state) => {
    const time = state.clock.elapsedTime
    meshRef.current.position.y = Math.sin(time) * 2
  })

  return <mesh ref={meshRef}>...</mesh>
}

// Control render loop
function CustomRender() {
  useFrame(({ gl, scene, camera }) => {
    gl.render(scene, camera)
  }, 1) // renderPriority = 1 (takes over rendering)
}

// Ordered execution
function First() {
  useFrame(() => console.log('First'), -1)
}

function Second() {
  useFrame(() => console.log('Second'), 0)
}

function Third() {
  useFrame(() => console.log('Third'), 1)
}
```

---

#### useThree

Access R3F state and scene objects.

```typescript
useThree<T = RootState>(
  selector?: (state: RootState) => T,
  equalityFn?: (a: T, b: T) => boolean
): T
```

**Parameters**:
- `selector` - Function to select specific state (optional)
- `equalityFn` - Custom equality function for optimization

**Examples**:

```jsx
// Get all state (re-renders on any change)
function Component() {
  const state = useThree()
  const { gl, scene, camera, size } = state
  return null
}

// Selective subscription (only re-renders when size changes)
function Component() {
  const size = useThree((state) => state.size)
  console.log(size.width, size.height)
  return null
}

// Multiple selections
function Component() {
  const camera = useThree((state) => state.camera)
  const viewport = useThree((state) => state.viewport)
  const gl = useThree((state) => state.gl)
  return null
}

// Get state non-reactively
function Component() {
  const get = useThree((state) => state.get)

  function handleClick() {
    const freshState = get()
    console.log(freshState.camera.position)
  }

  return <mesh onClick={handleClick}>...</mesh>
}

// Manual invalidation (trigger render)
function Component() {
  const invalidate = useThree((state) => state.invalidate)

  return (
    <mesh onClick={() => invalidate()}>
      <boxGeometry />
      <meshStandardMaterial />
    </mesh>
  )
}

// Set frame loop
function Component() {
  const setFrameloop = useThree((state) => state.setFrameloop)

  useEffect(() => {
    setFrameloop('demand') // Switch to on-demand rendering
  }, [])

  return null
}
```

---

#### useLoader

Load assets with automatic caching and Suspense integration.

```typescript
useLoader<T>(
  loader: LoaderConstructor<T>,
  url: string | string[],
  extensions?: (loader: LoaderProto<T>) => void,
  onProgress?: (event: ProgressEvent) => void
): T | T[]

// Static methods
useLoader.preload<T>(
  loader: LoaderConstructor<T>,
  url: string | string[],
  extensions?: (loader: LoaderProto<T>) => void
): void

useLoader.clear<T>(
  loader: LoaderConstructor<T>,
  url: string | string[]
): void
```

**Examples**:

```jsx
import { useLoader } from '@react-three/fiber'
import { TextureLoader, GLTFLoader } from 'three'

// Load texture
function TexturedBox() {
  const texture = useLoader(TextureLoader, '/texture.jpg')

  return (
    <mesh>
      <boxGeometry />
      <meshStandardMaterial map={texture} />
    </mesh>
  )
}

// Load GLTF model
function Model() {
  const gltf = useLoader(GLTFLoader, '/model.glb')
  return <primitive object={gltf.scene} />
}

// Load multiple assets
function Scene() {
  const [texture1, texture2, texture3] = useLoader(TextureLoader, [
    '/tex1.jpg',
    '/tex2.jpg',
    '/tex3.jpg'
  ])

  return (
    <>
      <mesh><meshStandardMaterial map={texture1} /></mesh>
      <mesh><meshStandardMaterial map={texture2} /></mesh>
      <mesh><meshStandardMaterial map={texture3} /></mesh>
    </>
  )
}

// Loader extensions (e.g., DRACO compression)
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader'

function CompressedModel() {
  const gltf = useLoader(
    GLTFLoader,
    '/compressed.glb',
    (loader) => {
      const dracoLoader = new DRACOLoader()
      dracoLoader.setDecoderPath('/draco/')
      loader.setDRACOLoader(dracoLoader)
    }
  )

  return <primitive object={gltf.scene} />
}

// Progress tracking
function ModelWithProgress() {
  const [progress, setProgress] = useState(0)

  const gltf = useLoader(
    GLTFLoader,
    '/large-model.glb',
    undefined,
    (event) => {
      setProgress((event.loaded / event.total) * 100)
    }
  )

  return <primitive object={gltf.scene} />
}

// Pre-loading
function Preloader() {
  useEffect(() => {
    useLoader.preload(GLTFLoader, '/model.glb')
    useLoader.preload(TextureLoader, '/texture.jpg')
  }, [])

  return null
}

// Clear cache
function Component() {
  useEffect(() => {
    return () => {
      useLoader.clear(GLTFLoader, '/model.glb')
    }
  }, [])
}
```

---

#### useGraph

Access GLTF scene graph with typed nodes and materials.

```typescript
useGraph(object: Object3D): {
  nodes: { [name: string]: Object3D }
  materials: { [name: string]: Material }
}
```

**Example**:

```jsx
import { useLoader } from '@react-three/fiber'
import { useGraph } from '@react-three/fiber'
import { GLTFLoader } from 'three'

function Model() {
  const gltf = useLoader(GLTFLoader, '/model.glb')
  const { nodes, materials } = useGraph(gltf.scene)

  return (
    <group>
      <mesh geometry={nodes.Mesh.geometry} material={materials.Material} />
      <mesh geometry={nodes.OtherMesh.geometry}>
        <meshStandardMaterial color="red" />
      </mesh>
    </group>
  )
}
```

---

### Events

R3F supports pointer events on any Object3D.

#### Supported Events

```typescript
// Pointer events
onPointerOver?: (event: ThreeEvent<PointerEvent>) => void
onPointerOut?: (event: ThreeEvent<PointerEvent>) => void
onPointerEnter?: (event: ThreeEvent<PointerEvent>) => void
onPointerLeave?: (event: ThreeEvent<PointerEvent>) => void
onPointerMove?: (event: ThreeEvent<PointerEvent>) => void
onPointerDown?: (event: ThreeEvent<PointerEvent>) => void
onPointerUp?: (event: ThreeEvent<PointerEvent>) => void
onPointerCancel?: (event: ThreeEvent<PointerEvent>) => void
onPointerMissed?: (event: MouseEvent) => void

// Click events
onClick?: (event: ThreeEvent<MouseEvent>) => void
onContextMenu?: (event: ThreeEvent<MouseEvent>) => void
onDoubleClick?: (event: ThreeEvent<MouseEvent>) => void

// Wheel event
onWheel?: (event: ThreeEvent<WheelEvent>) => void
```

#### ThreeEvent Object

```typescript
interface ThreeEvent<T> extends Omit<T, 'target'> {
  // Three.js specific
  intersections: Intersection[]
  object: Object3D
  eventObject: Object3D
  unprojectedPoint: Vector3
  ray: Ray
  camera: Camera
  sourceEvent: T
  delta: number

  // Helpers
  stopPropagation: () => void
  nativeEvent: T
  pointer: Vector2
  pointerId: number
  distance: number
  point: Vector3
  uv: Vector2
  face: Face | null
  faceIndex: number | null
}
```

#### Examples

```jsx
// Basic click handler
<mesh onClick={(e) => console.log('Clicked!', e.point)}>
  <boxGeometry />
  <meshStandardMaterial />
</mesh>

// Hover states
function InteractiveBox() {
  const [hovered, setHovered] = useState(false)

  return (
    <mesh
      onPointerOver={(e) => {
        e.stopPropagation()
        setHovered(true)
        document.body.style.cursor = 'pointer'
      }}
      onPointerOut={(e) => {
        setHovered(false)
        document.body.style.cursor = 'auto'
      }}
    >
      <boxGeometry />
      <meshStandardMaterial color={hovered ? 'hotpink' : 'orange'} />
    </mesh>
  )
}

// Stop event propagation
<group onClick={(e) => e.stopPropagation()}>
  <mesh onClick={() => console.log('Mesh clicked')} />
  <mesh onClick={() => console.log('This will also fire without stopPropagation')} />
</group>

// Access intersection data
<mesh
  onClick={(e) => {
    console.log('Hit point:', e.point)
    console.log('Hit face:', e.face)
    console.log('UV coordinates:', e.uv)
    console.log('Distance from camera:', e.distance)
    console.log('All intersections:', e.intersections)
  }}
>
  <sphereGeometry />
  <meshStandardMaterial />
</mesh>

// Pointer missed (clicked on empty space)
<Canvas onPointerMissed={() => console.log('Clicked on background')}>
  <mesh />
</Canvas>
```

---

### Three.js Object Props

R3F translates JSX props to Three.js object properties.

#### Prop Mapping

```jsx
// Array notation → .set()
<mesh position={[1, 2, 3]} />  // mesh.position.set(1, 2, 3)
<mesh rotation={[0, Math.PI, 0]} />  // mesh.rotation.set(0, Math.PI, 0)
<mesh scale={[2, 2, 2]} />  // mesh.scale.set(2, 2, 2)

// Dash notation (axis-specific)
<mesh position-x={1} position-y={2} position-z={3} />
<mesh scale-x={2} scale-y={1} />

// Direct property assignment
<mesh visible={false} />  // mesh.visible = false
<mesh castShadow receiveShadow />  // mesh.castShadow = true, mesh.receiveShadow = true

// Constructor arguments
<boxGeometry args={[1, 1, 1]} />  // new BoxGeometry(1, 1, 1)
<meshStandardMaterial args={[{ color: 'red' }]} />  // new MeshStandardMaterial({ color: 'red' })

// Attach to specific parent property
<mesh>
  <meshStandardMaterial attach="material" />  // mesh.material = material
</mesh>

// Nested properties
<meshStandardMaterial color="red" roughness={0.5} metalness={0.8} />

// Set (for Vector-like properties)
<pointLight position={[10, 10, 10]} />
```

#### Special Props

```jsx
// attach: Attach to parent property
<mesh>
  <meshStandardMaterial attach="material" />
  <boxGeometry attach="geometry" />
</mesh>

// attach-array: Attach to array index
<group>
  <mesh attach="children-0" />
  <mesh attach="children-1" />
</group>

// dispose: Control automatic disposal
<mesh dispose={null}>  {/* Never dispose */}
  <boxGeometry />
  <meshStandardMaterial />
</mesh>

// args: Constructor arguments
<sphereGeometry args={[1, 32, 32]} />  // radius, widthSegments, heightSegments

// object: Pass pre-existing Three.js object
<primitive object={myThreeJsObject} />

// ref: Get reference to underlying Three.js object
<mesh ref={meshRef} />
```

---

### Drei Helpers

Essential Drei components and hooks.

#### OrbitControls

```typescript
interface OrbitControlsProps {
  makeDefault?: boolean
  camera?: Camera
  domElement?: HTMLElement
  target?: Vector3
  enableDamping?: boolean
  dampingFactor?: number
  enableZoom?: boolean
  enableRotate?: boolean
  enablePan?: boolean
  minDistance?: number
  maxDistance?: number
  minPolarAngle?: number
  maxPolarAngle?: number
  onChange?: (e?: Event) => void
  onStart?: (e?: Event) => void
  onEnd?: (e?: Event) => void
}
```

```jsx
import { OrbitControls } from '@react-three/drei'

<OrbitControls
  makeDefault
  enableDamping
  dampingFactor={0.05}
  minDistance={3}
  maxDistance={20}
  maxPolarAngle={Math.PI / 2}
  target={[0, 1, 0]}
/>
```

#### Environment

```jsx
import { Environment } from '@react-three/drei'

// Preset HDRI
<Environment preset="sunset" background />

// Custom HDRI
<Environment files="/hdri.hdr" />

// Ground reflection
<Environment preset="city" ground={{ height: 15, radius: 60, scale: 100 }} />
```

#### useGLTF

```jsx
import { useGLTF } from '@react-three/drei'

function Model() {
  const { scene, nodes, materials } = useGLTF('/model.glb')
  return <primitive object={scene} />
}

// Pre-load
useGLTF.preload('/model.glb')
```

#### Text & Text3D

```jsx
import { Text, Text3D } from '@react-three/drei'

// 2D billboard text
<Text
  position={[0, 2, 0]}
  fontSize={1}
  color="white"
  anchorX="center"
  anchorY="middle"
  maxWidth={5}
  lineHeight={1}
  letterSpacing={0.02}
  textAlign="center"
  font="/fonts/font.woff"
  outlineWidth={0.1}
  outlineColor="#000000"
>
  Hello World
</Text>

// 3D extruded text
<Text3D
  font="/fonts/helvetiker_regular.typeface.json"
  size={1}
  height={0.2}
  curveSegments={12}
  bevelEnabled
  bevelThickness={0.02}
  bevelSize={0.02}
  bevelOffset={0}
  bevelSegments={5}
>
  3D Text
  <meshNormalMaterial />
</Text3D>
```

#### Center & Bounds

```jsx
import { Center, Bounds, useBounds } from '@react-three/drei'

// Auto-center
<Center>
  <Model />
</Center>

// Auto-fit camera
<Bounds fit clip observe margin={1.2}>
  <Model />
</Bounds>

// Manual control
function SelectToZoom() {
  const bounds = useBounds()

  return (
    <mesh onClick={(e) => {
      e.stopPropagation()
      bounds.refresh(e.object).fit()
    }}>
      <boxGeometry />
      <meshStandardMaterial />
    </mesh>
  )
}
```

#### Html

```jsx
import { Html } from '@react-three/drei'

<mesh>
  <boxGeometry />
  <meshStandardMaterial />

  <Html
    position={[0, 1, 0]}
    center
    distanceFactor={10}
    occlude
    transform
    sprite
  >
    <div className="annotation">Label</div>
  </Html>
</mesh>
```

#### ScrollControls

```jsx
import { ScrollControls, Scroll, useScroll } from '@react-three/drei'

function Scene() {
  const scroll = useScroll()
  const meshRef = useRef()

  useFrame(() => {
    const offset = scroll.offset // 0-1
    meshRef.current.position.y = offset * 10
  })

  return <mesh ref={meshRef}>...</mesh>
}

<Canvas>
  <ScrollControls pages={3} damping={0.5}>
    <Scroll>
      <Scene />
    </Scroll>
    <Scroll html>
      <h1>HTML Content</h1>
    </Scroll>
  </ScrollControls>
</Canvas>
```

#### ContactShadows

```jsx
import { ContactShadows } from '@react-three/drei'

<ContactShadows
  position={[0, -0.8, 0]}
  opacity={0.5}
  scale={10}
  blur={1}
  far={10}
  resolution={256}
  color="#000000"
/>
```

#### Sky

```jsx
import { Sky } from '@react-three/drei'

<Sky
  distance={450000}
  sunPosition={[0, 1, 0]}
  inclination={0}
  azimuth={0.25}
  rayleigh={2}
  turbidity={10}
  mieCoefficient={0.005}
  mieDirectionalG={0.8}
/>
```

#### Stars

```jsx
import { Stars } from '@react-three/drei'

<Stars
  radius={100}
  depth={50}
  count={5000}
  factor={4}
  saturation={0}
  fade
  speed={1}
/>
```

---

### Performance Helpers (Drei)

#### AdaptiveDpr

```jsx
import { AdaptiveDpr } from '@react-three/drei'

<AdaptiveDpr pixelated />
```

#### AdaptiveEvents

```jsx
import { AdaptiveEvents } from '@react-three/drei'

<AdaptiveEvents />
```

#### PerformanceMonitor

```jsx
import { PerformanceMonitor } from '@react-three/drei'

<PerformanceMonitor
  onIncline={() => console.log('Performance improved')}
  onDecline={() => console.log('Performance degraded')}
  onFallback={() => console.log('Fallback triggered')}
  onChange={({ factor }) => console.log('Factor:', factor)}
  flipflops={3}
  bounds={(refreshRate) => [50, 90]}
>
  <Scene />
</PerformanceMonitor>
```

#### Preload

```jsx
import { Preload } from '@react-three/drei'

<Canvas>
  <Scene />
  <Preload all />  {/* Preload all assets */}
</Canvas>
```

---

### Resources

- [Official R3F Docs](https://docs.pmnd.rs/react-3d)
- [Drei Documentation](https://github.com/pmndrs/drei)
- [Three.js Documentation](https://threejs.org/docs/)
- [R3F Examples](https://docs.pmnd.rs/react-3d/examples)
