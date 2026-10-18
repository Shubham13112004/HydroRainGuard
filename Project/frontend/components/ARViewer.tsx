'use client';

import { useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import { XR } from '@react-three/xr';
import * as THREE from 'three';

import { useI18n } from '@/lib/i18n';
import type { StructureRecommendation } from '@/lib/types';

/* ============================================================
   PALETTE — matches the Tailwind/report theme
============================================================ */

const C = {
  water: '#00bcd4',
  tank: '#0d70b0',
  pit: '#27ae60',
  well: '#e67e22',
  perc: '#8e44ad',
  soak: '#16a085',
  building: '#d8d5cc',
  roof: '#8b6f47',
  ground: '#7ba05b',
  soil: '#8a6a4a',
  pipe: '#5a6472',
};

/* ============================================================
   HELPERS
============================================================ */

function num(d: Record<string, unknown>, key: string, fallback: number) {
  const v = d?.[key];
  return typeof v === 'number' && Number.isFinite(v) ? v : fallback;
}

/** Radius of a cylinder that holds `volume` at height `h`. */
function radiusForVolume(volume: number, h: number) {
  return Math.sqrt(Math.max(volume, 0.1) / (Math.PI * Math.max(h, 0.1)));
}

function clamp(v: number, lo: number, hi: number) {
  return Math.min(hi, Math.max(lo, v));
}

type Dims = Record<string, string | number>;

/* ============================================================
   LABEL
============================================================ */

function Label({
  children,
  position,
  color,
}: {
  children: string;
  position: [number, number, number];
  color: string;
}) {
  return (
    <Html position={position} center distanceFactor={12} zIndexRange={[10, 0]}>
      <div
        className="whitespace-nowrap rounded-full bg-white/95 px-2.5 py-1 text-[11px] font-semibold shadow-md border"
        style={{ color, borderColor: color }}
      >
        {children}
      </div>
    </Html>
  );
}

/* ============================================================
   WATER FLOW — droplets travelling roof → tank → ground
============================================================ */

function FlowParticles({
  points,
  count = 6,
}: {
  points: [number, number, number][];
  count?: number;
}) {
  const ref = useRef<THREE.Group>(null);

  const curve = useMemo(
    () =>
      new THREE.CatmullRomCurve3(
        points.map((p) => new THREE.Vector3(...p)),
      ),
    [points],
  );

  useFrame(({ clock }) => {
    const g = ref.current;
    if (!g) return;
    const t = clock.getElapsedTime();
    g.children.forEach((child, i) => {
      const u = ((t * 0.28 + i / count) % 1);
      const p = curve.getPointAt(u);
      child.position.copy(p);
      const s = 0.9 - 0.45 * u;
      child.scale.setScalar(s);
    });
  });

  return (
    <group ref={ref}>
      {Array.from({ length: count }).map((_, i) => (
        <mesh key={i}>
          <sphereGeometry args={[0.13, 10, 10]} />
          <meshStandardMaterial
            color={C.water}
            emissive={C.water}
            emissiveIntensity={0.5}
            transparent
            opacity={0.9}
          />
        </mesh>
      ))}
    </group>
  );
}

/* ============================================================
   THE STRUCTURE
============================================================ */

function StructureModel({
  name,
  dims,
  cutaway,
}: {
  name: string;
  dims: Dims;
  cutaway: boolean;
}) {
  const d = dims as Record<string, unknown>;

  /* ---- rooftop storage tank (above ground, beside building) ---- */
  if (name.startsWith('Rooftop')) {
    const h = clamp(num(d, 'depth_m', 2), 0.6, 4);
    const r = clamp(num(d, 'diameter_m', 2) / 2, 0.3, 3);
    return (
      <group position={[0, 0, 0]}>
        <mesh position={[0, h / 2, 0]} castShadow>
          <cylinderGeometry args={[r, r, h, 28]} />
          <meshStandardMaterial color={C.tank} roughness={0.35} metalness={0.15} />
        </mesh>
        {/* water inside */}
        <mesh position={[0, h * 0.35, 0]}>
          <cylinderGeometry args={[r * 0.94, r * 0.94, h * 0.68, 28]} />
          <meshStandardMaterial
            color={C.water}
            transparent
            opacity={0.55}
            emissive={C.water}
            emissiveIntensity={0.25}
          />
        </mesh>
        {/* lid */}
        <mesh position={[0, h + 0.05, 0]}>
          <cylinderGeometry args={[r * 1.05, r * 1.05, 0.1, 28]} />
          <meshStandardMaterial color="#0a4a70" />
        </mesh>
      </group>
    );
  }

  /* ---- recharge pit (below ground) ---- */
  if (name.startsWith('Recharge Pit')) {
    const L = clamp(num(d, 'length_m', 1.5), 0.5, 6);
    const W = clamp(num(d, 'width_m', 1.5), 0.5, 6);
    const D = clamp(num(d, 'depth_m', 2), 0.5, 5);
    return (
      <group position={[0, -D / 2, 0]}>
        <mesh>
          <boxGeometry args={[L, D, W]} />
          <meshStandardMaterial
            color={C.pit}
            transparent
            opacity={cutaway ? 0.85 : 0.95}
            roughness={0.9}
          />
        </mesh>
        {/* filter layers */}
        <mesh position={[0, -D / 6, 0]}>
          <boxGeometry args={[L * 1.02, D / 3, W * 1.02]} />
          <meshStandardMaterial color="#9aa5a0" roughness={1} />
        </mesh>
        {/* standing water */}
        <mesh position={[0, -D / 2 + 0.18, 0]}>
          <boxGeometry args={[L * 0.92, 0.3, W * 0.92]} />
          <meshStandardMaterial
            color={C.water}
            transparent
            opacity={0.6}
            emissive={C.water}
            emissiveIntensity={0.3}
          />
        </mesh>
      </group>
    );
  }

  /* ---- recharge well / borewell (deep, below ground) ---- */
  if (name.startsWith('Recharge Well')) {
    const depthM = clamp(num(d, 'depth_m', 20), 3, 40);
    // 250 mm bore -> 0.25 m. Drawn at a visible minimum.
    const boreM = clamp(num(d, 'diameter_mm', 250) / 1000, 0.15, 0.6);
    const shown = Math.min(depthM, 12); // keep the camera sane
    return (
      <group position={[0, -shown / 2, 0]}>
        <mesh>
          <cylinderGeometry args={[boreM, boreM, shown, 20, 1, true]} />
          <meshStandardMaterial
            color={C.well}
            side={THREE.DoubleSide}
            transparent
            opacity={cutaway ? 0.9 : 1}
            roughness={0.6}
          />
        </mesh>
        {/* casing collar at the surface */}
        <mesh position={[0, shown / 2 + 0.08, 0]}>
          <cylinderGeometry args={[boreM * 1.6, boreM * 1.6, 0.16, 20]} />
          <meshStandardMaterial color="#a04000" />
        </mesh>
        {/* water column */}
        <mesh position={[0, -shown / 2 + shown * 0.25, 0]}>
          <cylinderGeometry args={[boreM * 0.85, boreM * 0.85, shown * 0.5, 20]} />
          <meshStandardMaterial
            color={C.water}
            transparent
            opacity={0.55}
            emissive={C.water}
            emissiveIntensity={0.3}
          />
        </mesh>
      </group>
    );
  }

  /* ---- percolation tank (open pond at ground level) ---- */
  if (name.startsWith('Percolation')) {
    const area = clamp(num(d, 'surface_area_m2', 60), 4, 400);
    const side = Math.sqrt(area);
    const depth = clamp(num(d, 'depth_m', 2.5), 0.5, 4);
    return (
      <group position={[0, -depth / 2, 0]}>
        <mesh>
          <boxGeometry args={[side, depth, side]} />
          <meshStandardMaterial color="#6d4c7d" roughness={1} />
        </mesh>
        <mesh position={[0, depth / 2 - depth * 0.35, 0]}>
          <boxGeometry args={[side * 0.96, depth * 0.5, side * 0.96]} />
          <meshStandardMaterial
            color={C.perc}
            transparent
            opacity={0.75}
            emissive={C.perc}
            emissiveIntensity={0.15}
          />
        </mesh>
      </group>
    );
  }

  /* ---- soak pit ---- */
  const r = clamp(num(d, 'diameter_m', 1) / 2, 0.3, 2.5);
  const depth = clamp(num(d, 'depth_m', 1.5), 0.5, 4);
  return (
    <group position={[0, -depth / 2, 0]}>
      <mesh>
        <cylinderGeometry args={[r, r, depth, 24]} />
        <meshStandardMaterial color={C.soak} roughness={0.95} />
      </mesh>
      <mesh position={[0, depth / 2 + 0.04, 0]}>
        <cylinderGeometry args={[r * 1.1, r * 1.1, 0.08, 24]} />
        <meshStandardMaterial color="#4a5a58" />
      </mesh>
    </group>
  );
}

/* ============================================================
   SCENE
============================================================ */

type SceneProps = {
  structure: StructureRecommendation | null;
  roofArea: number;
  cutaway: boolean;
  showLabels: boolean;
  labels: {
    building: string;
    tank: string;
    pipe: string;
    structure: string;
  };
};

function Scene({
  structure,
  roofArea,
  cutaway,
  showLabels,
  labels,
}: SceneProps) {
  const side = clamp(Math.sqrt(Math.max(roofArea, 9)), 3, 22);
  const wallH = 3.2;
  const depth = side * 0.75;

  const name = structure?.structure_type ?? '';
  const dims = (structure?.dimensions ?? {}) as Dims;

  // Lay structures out to the right of the building.
  const structureX = side / 2 + 1.8;

  // Is the chosen structure underground?
  const underground =
    !name.startsWith('Rooftop') && !name.startsWith('Percolation');

  const structureColor = name.startsWith('Rooftop')
    ? C.tank
    : name.startsWith('Recharge Pit')
    ? C.pit
    : name.startsWith('Recharge Well')
    ? C.well
    : name.startsWith('Percolation')
    ? C.perc
    : C.soak;

  return (
    <>
      <ambientLight intensity={0.65} />
      <directionalLight
        position={[6, 10, 6]}
        intensity={1.15}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
      />
      <hemisphereLight args={['#cfe8ff', '#4a6b3a', 0.45]} />

      {/* ---- ground ---- */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
        <planeGeometry args={[120, 120]} />
        <meshStandardMaterial
          color={C.ground}
          transparent={cutaway}
          opacity={cutaway ? 0.35 : 1}
          roughness={1}
        />
      </mesh>

      {/* ---- soil block, only visible in cutaway ---- */}
      {cutaway && (
        <mesh position={[structureX, -3, 0]}>
          <boxGeometry args={[6, 6, 6]} />
          <meshStandardMaterial
            color={C.soil}
            transparent
            opacity={0.22}
            roughness={1}
          />
        </mesh>
      )}

      <gridHelper
        args={[60, 60, '#ffffff', '#ffffff']}
        position={[0, 0.01, 0]}
      />

      {/* ---- building ---- */}
      <group>
        <mesh position={[0, wallH / 2, 0]} castShadow receiveShadow>
          <boxGeometry args={[side, wallH, depth]} />
          <meshStandardMaterial color={C.building} roughness={0.85} />
        </mesh>
        {/* roof slab */}
        <mesh position={[0, wallH + 0.12, 0]} castShadow>
          <boxGeometry args={[side * 1.06, 0.24, depth * 1.06]} />
          <meshStandardMaterial color={C.roof} roughness={0.9} />
        </mesh>
        {/* parapet */}
        <mesh position={[0, wallH + 0.46, 0]}>
          <boxGeometry args={[side * 1.06, 0.42, depth * 1.06]} />
          <meshStandardMaterial
            color={C.roof}
            transparent
            opacity={0.28}
            roughness={0.9}
          />
        </mesh>

        {/* downpipe from roof to the structure */}
        <mesh
          position={[side / 2 + 0.18, wallH / 2, depth / 2 - 0.3]}
          castShadow
        >
          <cylinderGeometry args={[0.09, 0.09, wallH, 12]} />
          <meshStandardMaterial color={C.pipe} metalness={0.4} roughness={0.5} />
        </mesh>
      </group>

      {/* ---- first-flush / filter chamber ---- */}
      <mesh position={[side / 2 + 1.0, 0.35, depth / 2 - 0.3]} castShadow>
        <cylinderGeometry args={[0.26, 0.26, 0.7, 16]} />
        <meshStandardMaterial color="#445" roughness={0.7} />
      </mesh>

      {/* ---- connector pipe: filter -> structure ---- */}
      {structure && (
        <mesh
          position={[
            side / 2 + 1.0 + (structureX - side / 2 - 1.0) / 2,
            underground ? -0.35 : 0.35,
            depth / 2 - 0.3,
          ]}
          rotation={[0, 0, Math.PI / 2]}
        >
          <cylinderGeometry
            args={[0.075, 0.075, Math.abs(structureX - side / 2 - 1.0), 12]}
          />
          <meshStandardMaterial color={C.pipe} metalness={0.4} roughness={0.5} />
        </mesh>
      )}

      {/* ---- the recommended structure ---- */}
      {structure && (
        <group position={[structureX, 0, depth / 2 - 0.3]}>
          <StructureModel name={name} dims={dims} cutaway={cutaway} />
        </group>
      )}

      {/* ---- flowing water ---- */}
      {structure && (
        <FlowParticles
          points={[
            [side / 2 + 0.18, wallH + 0.3, depth / 2 - 0.3],
            [side / 2 + 0.18, 0.8, depth / 2 - 0.3],
            [side / 2 + 1.0, 0.35, depth / 2 - 0.3],
            [structureX, underground ? -0.6 : 0.5, depth / 2 - 0.3],
          ]}
        />
      )}

      {/* ---- labels ---- */}
      {showLabels && (
        <>
          <Label position={[0, wallH + 1.4, 0]} color="#8b6f47">
            {labels.building}
          </Label>
          <Label position={[side / 2 + 1.0, 1.2, depth / 2 - 0.3]} color="#445">
            {labels.pipe}
          </Label>
          {structure && (
            <Label
              position={[structureX, underground ? -0.4 : 2.6, depth / 2 - 0.3]}
              color={structureColor}
            >
              {labels.structure}
            </Label>
          )}
        </>
      )}
    </>
  );
}

/* ============================================================
   CANVAS
============================================================ */

export default function ARViewer({
  structure,
  roofArea,
  cutaway,
  showLabels,
  labels,
}: SceneProps) {
  const cameraDistance = clamp(
    Math.sqrt(Math.max(roofArea, 9)) * 2.2 + 8,
    14,
    60,
  );

  return (
    <Canvas
      shadows
      dpr={[1, 2]}
      camera={{
        position: [cameraDistance * 0.55, cameraDistance * 0.42, cameraDistance],
        fov: 45,
        near: 0.1,
        far: 500,
      }}
      onCreated={({ gl }) => {
        gl.setClearColor('#101820');
      }}
    >
      <XR referenceSpace="local-floor">
        <Scene
          structure={structure}
          roofArea={roofArea}
          cutaway={cutaway}
          showLabels={showLabels}
          labels={labels}
        />
      </XR>
      <OrbitControls
        makeDefault
        enablePan
        enableZoom
        enableDamping
        dampingFactor={0.08}
        maxPolarAngle={Math.PI / 1.9}
        minDistance={3}
        maxDistance={120}
        target={[0, 1.5, 0]}
      />
    </Canvas>
  );
}
