// The body: the compiled MuJoCo meshes (app/build/body bundle, from
// scripts/export_geometry.py) posed each frame from the recording's world
// poses. Units are the model's (mm). Ported from viz/index.html.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { fetchJSON } from "./io.js";

const LEGS = ["lf", "lm", "lh", "rf", "rm", "rh"];

export class BodyView {
  constructor(canvas) {
    this.canvas = canvas;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(35, 1, 0.05, 500);
    this.camera.up.set(0, 0, 1);
    this.camera.position.set(6.5, -6.5, 4.5);
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.target.set(0, 0, 1);
    this.controls.enableDamping = false;
    this.follow = true;
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x445566, 1.6));
    const sun = new THREE.DirectionalLight(0xffffff, 1.6);
    sun.position.set(3, -4, 8);
    this.scene.add(sun);
    this.floor = new THREE.Mesh(new THREE.CircleGeometry(60, 64), new THREE.MeshBasicMaterial({ color: 0xe9e6de }));
    this.floor.position.z = -0.002;
    this.scene.add(this.floor);
    const grid = new THREE.GridHelper(120, 120, 0x888888, 0x888888);
    grid.rotation.x = Math.PI / 2;
    grid.material.transparent = true;
    grid.material.opacity = 0.25;
    this.scene.add(grid);
    this.groups = [];
    this.tint = [];
    this.legLoad = new Float32Array(LEGS.length);
    this._lastTarget = new THREE.Vector3(0, 0, 1);
  }

  setTheme(dark) {
    this.scene.background = new THREE.Color(dark ? 0x15171a : 0xf3f1ec);
    this.loadColour = new THREE.Color(dark ? 0x4fd1c5 : 0x0f8a7e);
    this.floor.material.color.set(dark ? 0x1d2024 : 0xe9e6de);
  }

  async load(base, rec) {
    const [index, buf] = await Promise.all([
      fetchJSON(`${base}/geometry.json`),
      fetch(`${base}/geometry.bin`).then(r => r.arrayBuffer()),
    ]);
    const V = new Float32Array(buf, 0, index.vertex_bytes / 4);
    const F = new Uint32Array(buf, index.vertex_bytes, index.n_triangles * 3);
    const names = rec.manifest.names.bodies;
    for (let b = 0; b < names.length; b++) {
      const g = new THREE.Group();
      this.scene.add(g);
      this.groups.push(g);
    }
    this.unmatched = [];
    for (const gd of index.geoms) {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(
        V.slice(gd.vert_offset * 3, (gd.vert_offset + gd.vert_count) * 3), 3));
      geo.setIndex(new THREE.BufferAttribute(
        F.slice(gd.face_offset * 3, (gd.face_offset + gd.face_count) * 3), 1));
      geo.computeVertexNormals();
      const [r, g, b, a] = gd.rgba;
      const mat = new THREE.MeshPhongMaterial({
        color: new THREE.Color(r, g, b), opacity: a, transparent: a < 0.99,
        shininess: 18, specular: 0x222222, side: a < 0.99 ? THREE.DoubleSide : THREE.FrontSide,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.fromArray(gd.pos);
      const q = gd.quat_wxyz;                       // MuJoCo (w,x,y,z) -> three (x,y,z,w)
      mesh.quaternion.set(q[1], q[2], q[3], q[0]);
      // bind by body name: geometry and recording may come from different builds
      const bname = index.body_names[gd.body];
      const bi = names.indexOf(bname);
      if (bi < 0) this.unmatched.push(bname);
      (bi >= 0 ? this.groups[bi] : this.scene).add(mesh);
      if (/_tarsus/.test(gd.name || "")) {
        const L = LEGS.findIndex(l => (gd.name || "").includes("/" + l + "_"));
        if (L >= 0) this.tint.push({ mat, leg: L, base: mat.color.clone() });
      }
    }
    this.rec = rec;
    this.contactLeg = rec.manifest.names.contacts.map(n => LEGS.findIndex(l => n.startsWith(l)));
    this.thorax = Math.max(1, names.findIndex(n => /c_thorax$/.test(n)));
  }

  pose(t) {
    const rec = this.rec;
    if (!rec || !rec.nFrames) return;
    const f = rec.frameAt(t), NB = rec.nBodies;
    const xp = rec.xpos, xq = rec.xquat;
    for (let b = 1; b < Math.min(NB, this.groups.length); b++) {
      const o = (f * NB + b) * 3, oq = (f * NB + b) * 4;
      this.groups[b].position.set(xp[o], xp[o + 1], xp[o + 2]);
      this.groups[b].quaternion.set(xq[oq + 1], xq[oq + 2], xq[oq + 3], xq[oq]);
    }
    // tarsal load: contact force summed per leg, shown as a tint on the feet
    this.legLoad.fill(0);
    const NC = rec.nContact;
    for (let k = 0; k < NC; k++) {
      const L = this.contactLeg[k];
      if (L >= 0) this.legLoad[L] += rec.contact[f * NC + k];
    }
    for (const tt of this.tint)
      tt.mat.color.copy(tt.base).lerp(this.loadColour, Math.min(1, this.legLoad[tt.leg] / 10));
    if (this.follow) {
      const o = (f * NB + this.thorax) * 3;
      const tgt = new THREE.Vector3(xp[o], xp[o + 1], Math.max(xp[o + 2], 0.6));
      const d = tgt.clone().sub(this._lastTarget);
      this.camera.position.add(d);
      this.controls.target.copy(tgt);
      this._lastTarget.copy(tgt);
    }
    this.thoraxHeight = xp[(f * NB + this.thorax) * 3 + 2];
  }

  resize() {
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    if (!w || !h) return;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  render() {
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}
