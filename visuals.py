"""Animated 3D scenes (Three.js) embedded in Streamlit.

Two scenes are provided:
  * staircase_html(): the roadmap as a slowly rotating staircase with a bobbing orb and a waving flag.
  * globe_html():     a rotating globe of career paths with pulsing, labelled nodes.

Both are drawn with WebGL in the browser (Three.js loaded from a CDN) and can also be dragged with the mouse or finger.
"""
from __future__ import annotations

import json

THREE_URL = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"

_PAGE = """<!doctype html><html><head><meta charset="utf-8">
<style>
html,body{margin:0;background:transparent;overflow:hidden;font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
#c{width:100%;height:__H__px;position:relative;cursor:grab;touch-action:pan-y;user-select:none}
#c:active{cursor:grabbing}
#c canvas{display:block}
.legend{position:absolute;left:0;right:0;bottom:4px;text-align:center;font-size:12px;color:#94a3b8;pointer-events:none}
.legend span{margin:0 8px;white-space:nowrap}
.legend i{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px}
.hint{position:absolute;right:10px;top:6px;font-size:11px;color:#94a3b8;pointer-events:none;letter-spacing:.06em}
</style></head><body><div id="c"></div>
<script src="__THREE__"></script>
<script>
__COMMON__
__SCENE__
</script></body></html>"""

_COMMON = r"""
const el = document.getElementById('c');
const S = {drag: false, vel: 0};

function setup(fov, camPos, lookAt) {
  let renderer;
  try {
    if (typeof THREE === 'undefined') throw new Error('three.js not loaded');
    renderer = new THREE.WebGLRenderer({antialias: true, alpha: true});
  } catch (e) {
    el.innerHTML = '<p style="padding:24px;color:#94a3b8">The 3D view needs WebGL and an internet connection (it loads three.js). Please use a recent Chrome, Edge, Firefox or Safari.</p>';
    return null;
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  el.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(fov, 1, 0.1, 100);
  camera.position.set(camPos[0], camPos[1], camPos[2]);
  camera.lookAt(lookAt[0], lookAt[1], lookAt[2]);
  function resize() {
    const w = el.clientWidth || 600, h = el.clientHeight || 380;
    renderer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  if (window.ResizeObserver) new ResizeObserver(resize).observe(el);
  window.addEventListener('resize', resize);
  resize();
  return {renderer: renderer, scene: scene, camera: camera};
}

function enableDrag(spin) {
  let lx = 0;
  el.addEventListener('pointerdown', function (e) {
    S.drag = true; lx = e.clientX;
    try { el.setPointerCapture(e.pointerId); } catch (_) {}
  });
  el.addEventListener('pointermove', function (e) {
    if (!S.drag) return;
    const dx = (e.clientX - lx) * 0.01; lx = e.clientX;
    spin.rotation.y += dx; S.vel = dx;
  });
  const end = function () { S.drag = false; };
  el.addEventListener('pointerup', end);
  el.addEventListener('pointercancel', end);
  el.addEventListener('pointerleave', end);
}

function spinStep(spin, auto) {
  if (!S.drag) { spin.rotation.y += S.vel + auto; S.vel *= 0.93; }
}

function addHint(text) {
  const h = document.createElement('div'); h.className = 'hint'; h.textContent = text; el.appendChild(h);
}
"""

_STAIRCASE = r"""
(function () {
  const DATA = __DATA__;
  const ctx = setup(36, [0, 4.8, 12.5], [0, 1.6, 0]);
  if (!ctx) return;
  const renderer = ctx.renderer, scene = ctx.scene, camera = ctx.camera;

  scene.add(new THREE.AmbientLight(0xffffff, 0.62));
  const sun = new THREE.DirectionalLight(0xffffff, 0.95); sun.position.set(5, 9, 7); scene.add(sun);
  const rim = new THREE.DirectionalLight(0x7dd3fc, 0.35); rim.position.set(-6, 3, -5); scene.add(rim);

  const spin = new THREE.Group(); scene.add(spin);
  const grid = new THREE.GridHelper(15, 15, 0x64748b, 0x334155);
  grid.material.transparent = true; grid.material.opacity = 0.35; spin.add(grid);

  const heights = [1.0, 1.8, 2.6, 3.4], cur = DATA.current;
  const xs = [0, 1, 2, 3].map(function (i) { return (i - 1.5) * 1.75; });
  DATA.phases.forEach(function (ph, i) {
    const geo = new THREE.BoxGeometry(1.45, heights[i], 1.45);
    let mesh;
    if (i <= cur) {
      mesh = new THREE.Mesh(geo, new THREE.MeshPhongMaterial({color: i < cur ? 0x2dd4bf : 0xfb8f68, shininess: 45}));
    } else {
      mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({color: 0x94a3b8, transparent: true, opacity: 0.1, depthWrite: false}));
      mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({color: 0xcbd5e1, transparent: true, opacity: 0.6})));
    }
    mesh.position.set(xs[i], heights[i] / 2, 0);
    spin.add(mesh);
  });

  // orb that marks your position, with a soft shadow on the step
  const orbTop = heights[cur];
  const orb = new THREE.Mesh(new THREE.SphereGeometry(0.3, 40, 40), new THREE.MeshPhongMaterial({color: 0xf4a37f, shininess: 120, specular: 0xffffff}));
  orb.position.set(xs[cur], orbTop + 0.45, 0); spin.add(orb);
  const shadow = new THREE.Mesh(new THREE.CircleGeometry(0.3, 32), new THREE.MeshBasicMaterial({color: 0x000000, transparent: true, opacity: 0.3}));
  shadow.rotation.x = -Math.PI / 2; shadow.position.set(xs[cur], orbTop + 0.01, 0); spin.add(shadow);

  // flag on the last step
  const fx = xs[3], ftop = heights[3];
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 1.3, 12), new THREE.MeshPhongMaterial({color: 0xe2e8f0}));
  pole.position.set(fx, ftop + 0.65, 0); spin.add(pole);
  const flagGeo = new THREE.PlaneGeometry(0.75, 0.42, 14, 1); flagGeo.translate(0.375, 0, 0);
  const flag = new THREE.Mesh(flagGeo, new THREE.MeshPhongMaterial({color: 0xfb8f68, side: THREE.DoubleSide}));
  flag.position.set(fx, ftop + 1.07, 0); spin.add(flag);
  const flagBase = Array.from(flagGeo.attributes.position.array);

  // drifting dust
  const N = 70, pos = new Float32Array(N * 3);
  for (let i = 0; i < N; i++) { pos[i * 3] = (Math.random() - 0.5) * 12; pos[i * 3 + 1] = Math.random() * 6; pos[i * 3 + 2] = (Math.random() - 0.5) * 12; }
  const dustGeo = new THREE.BufferGeometry(); dustGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const dust = new THREE.Points(dustGeo, new THREE.PointsMaterial({color: 0x94a3b8, size: 0.05, transparent: true, opacity: 0.6}));
  spin.add(dust);

  spin.rotation.y = -0.6;
  enableDrag(spin);
  addHint('DRAG TO ROTATE');

  const lg = document.createElement('div'); lg.className = 'legend';
  lg.innerHTML = DATA.phases.map(function (ph, i) {
    const col = i < cur ? '#2dd4bf' : i === cur ? '#fb8f68' : '#64748b';
    return '<span><i style="background:' + col + '"></i>' + String(i + 1).padStart(2, '0') + ' ' + ph.title + '</span>';
  }).join('');
  el.appendChild(lg);

  function frame(now) {
    const t = now / 1000;
    spinStep(spin, 0.005);
    orb.position.y = orbTop + 0.45 + Math.sin(t * 2.2) * 0.1;
    shadow.scale.setScalar(1 - Math.sin(t * 2.2) * 0.12);
    const p = flagGeo.attributes.position;
    for (let i = 0; i < p.count; i++) { const x = flagBase[i * 3]; p.setZ(i, Math.sin(x * 6 + t * 5) * 0.09 * x); }
    p.needsUpdate = true;
    dust.rotation.y += 0.0007;
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
"""

_GLOBE = r"""
(function () {
  const DATA = __DATA__;
  const ctx = setup(40, [0, 0, 9.6], [0, 0, 0]);
  if (!ctx) return;
  const renderer = ctx.renderer, scene = ctx.scene, camera = ctx.camera;

  const tilt = new THREE.Group(); tilt.rotation.z = 0.32; tilt.rotation.x = 0.18; scene.add(tilt);
  const spin = new THREE.Group(); tilt.add(spin);

  // points on a sphere (Fibonacci spiral), faded by depth
  const N = 260, R = 2.3, golden = Math.PI * (3 - Math.sqrt(5)), pts = [];
  for (let i = 0; i < N; i++) {
    const y = 1 - 2 * i / (N - 1), r = Math.sqrt(Math.max(0, 1 - y * y)), a = golden * i;
    pts.push(new THREE.Vector3(Math.cos(a) * r * R, y * R, Math.sin(a) * r * R));
  }
  const arr = new Float32Array(N * 3);
  pts.forEach(function (p, i) { arr[i * 3] = p.x; arr[i * 3 + 1] = p.y; arr[i * 3 + 2] = p.z; });
  const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(arr, 3));
  const mat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false,
    uniforms: {c: {value: new THREE.Color(0x2dd4bf)}, px: {value: renderer.getPixelRatio()}},
    vertexShader: 'varying float vA; uniform float px; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); vA = clamp(1.0 - (-mv.z - 7.0) / 5.0, 0.12, 1.0); gl_PointSize = (2.5 + 4.0 * vA) * px; gl_Position = projectionMatrix * mv; }',
    fragmentShader: 'uniform vec3 c; varying float vA; void main(){ float d = length(gl_PointCoord - 0.5); if (d > 0.5) discard; gl_FragColor = vec4(c, vA * (1.0 - d)); }'
  });
  spin.add(new THREE.Points(geo, mat));

  // neighbour links
  const seg = [];
  for (let i = 0; i < N; i++) {
    const near = [];
    for (let j = 0; j < N; j++) if (i !== j) near.push([pts[i].distanceToSquared(pts[j]), j]);
    near.sort(function (a, b) { return a[0] - b[0]; });
    for (let k = 0; k < 2; k++) {
      const j = near[k][1];
      if (j > i) seg.push(pts[i].x, pts[i].y, pts[i].z, pts[j].x, pts[j].y, pts[j].z);
    }
  }
  const lg = new THREE.BufferGeometry(); lg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(seg), 3));
  spin.add(new THREE.LineSegments(lg, new THREE.LineBasicMaterial({color: 0x2dd4bf, transparent: true, opacity: 0.16})));

  // career nodes with labels
  function label(text) {
    const c = document.createElement('canvas'); c.width = 640; c.height = 96;
    const g = c.getContext('2d');
    g.font = '600 32px system-ui, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.lineWidth = 8; g.strokeStyle = 'rgba(10,12,16,0.85)'; g.strokeText(text, 320, 48);
    g.fillStyle = '#f1f5f9'; g.fillText(text, 320, 48);
    const s = new THREE.Sprite(new THREE.SpriteMaterial({map: new THREE.CanvasTexture(c), transparent: true, depthTest: false}));
    s.scale.set(3.0, 0.45, 1); return s;
  }
  const nodes = DATA.careers.map(function (name, i) {
    const base = pts[Math.floor((i + 0.5) * N / DATA.careers.length)];
    const m = new THREE.Mesh(new THREE.SphereGeometry(0.085, 16, 16), new THREE.MeshBasicMaterial({color: 0x2dd4bf}));
    m.position.copy(base); spin.add(m);
    const s = label(name); s.position.copy(base.clone().multiplyScalar(1.2)); spin.add(s);
    return {mesh: m, sprite: s};
  });

  // tilted orbit ring with a small satellite
  const ringPts = [];
  for (let i = 0; i <= 96; i++) { const a = i / 96 * Math.PI * 2; ringPts.push(new THREE.Vector3(Math.cos(a) * 3.5, 0, Math.sin(a) * 3.5)); }
  const ring = new THREE.Group(); ring.rotation.x = 0.35; ring.rotation.z = -0.2; scene.add(ring);
  ring.add(new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(ringPts), new THREE.LineBasicMaterial({color: 0x94a3b8, transparent: true, opacity: 0.3})));
  const sat = new THREE.Mesh(new THREE.SphereGeometry(0.11, 16, 16), new THREE.MeshBasicMaterial({color: 0xfb8f68})); ring.add(sat);

  enableDrag(spin);
  addHint('DRAG THE GLOBE · ' + DATA.careers.length + ' CAREER PATHS');

  const wp = new THREE.Vector3();
  function frame(now) {
    const t = now / 1000, hi = Math.floor(t / 2.4) % nodes.length;
    spinStep(spin, 0.004);
    nodes.forEach(function (n, i) {
      n.mesh.getWorldPosition(wp);
      const front = (wp.z + R) / (2 * R);                 // 0 at the back of the globe, 1 at the front
      const on = i === hi, pulse = on ? 1 + Math.sin(t * 6) * 0.25 : 1;
      n.mesh.scale.setScalar((on ? 1.9 : 1) * pulse);
      n.mesh.material.color.setHex(on ? 0xfb8f68 : 0x2dd4bf);
      n.sprite.material.opacity = Math.max(0.1, Math.min(1, front * 1.4)) * (on ? 1 : 0.8);
      n.sprite.scale.set(on ? 3.4 : 3.0, on ? 0.51 : 0.45, 1);
    });
    const a = t * 0.6; sat.position.set(Math.cos(a) * 3.5, 0, Math.sin(a) * 3.5);
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
"""


def _safe_json(data: object) -> str:
    """JSON that is safe to place inside a <script> tag."""
    return json.dumps(data).replace("</", "<\\/")


def _page(scene_js: str, data: object, height: int) -> str:
    scene = scene_js.replace("__DATA__", _safe_json(data))
    return (_PAGE.replace("__H__", str(height)).replace("__THREE__", THREE_URL)
            .replace("__COMMON__", _COMMON).replace("__SCENE__", scene))


def staircase_html(phases: list[dict], current: int, height: int = 380) -> str:
    """Rotating roadmap staircase. Finished steps are teal, the current step is orange (with the orb)."""
    data = {"phases": [{"title": p["title"], "weeks": p["weeks"]} for p in phases], "current": int(current)}
    return _page(_STAIRCASE, data, height)


def globe_html(careers: list[str], height: int = 420) -> str:
    """Rotating globe of career paths with pulsing, labelled nodes."""
    return _page(_GLOBE, {"careers": list(careers)}, height)
