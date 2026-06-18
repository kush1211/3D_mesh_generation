import { Suspense } from "react";
import { Canvas, useLoader } from "@react-three/fiber";
import { Bounds, OrbitControls, Grid, GizmoHelper, GizmoViewport } from "@react-three/drei";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { Box } from "lucide-react";

function Model({ url }: { url: string }) {
  const gltf = useLoader(GLTFLoader, url);
  return <primitive object={gltf.scene} />;
}

export function MeshViewer({ glbUrl }: { glbUrl: string | null }) {
  return (
    <div className="relative h-full w-full overflow-hidden bg-[#0e1116]">
      <Canvas camera={{ position: [0.22, 0.18, 0.22], fov: 45, near: 0.001, far: 100 }} dpr={[1, 2]}>
        <color attach="background" args={["#0e1116"]} />
        <hemisphereLight intensity={0.5} groundColor="#1a1f29" />
        <ambientLight intensity={0.35} />
        <directionalLight position={[3, 5, 2]} intensity={1.3} />
        <directionalLight position={[-3, 2, -2]} intensity={0.4} />

        <Grid
          args={[20, 20]}
          cellSize={0.05}
          cellThickness={0.6}
          sectionSize={0.25}
          sectionThickness={1}
          cellColor="#222b38"
          sectionColor="#33415a"
          infiniteGrid
          fadeDistance={4}
          fadeStrength={1.5}
          position={[0, -0.0005, 0]}
        />

        {glbUrl && (
          <Suspense fallback={null}>
            <Bounds fit clip observe margin={1.4}>
              <Model key={glbUrl} url={glbUrl} />
            </Bounds>
          </Suspense>
        )}

        <OrbitControls makeDefault enableDamping dampingFactor={0.1} />
        <GizmoHelper alignment="bottom-right" margin={[56, 56]}>
          <GizmoViewport axisColors={["#e0533d", "#7cb342", "#3d7fe0"]} labelColor="white" />
        </GizmoHelper>
      </Canvas>

      {!glbUrl && (
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-3 text-slate-600">
          <Box className="h-10 w-10" strokeWidth={1.2} />
          <p className="font-mono text-xs uppercase tracking-widest">no mesh loaded</p>
        </div>
      )}

      <div className="pointer-events-none absolute left-3 top-3 font-mono text-[10px] uppercase tracking-widest text-slate-500">
        viewport · drag to orbit · scroll to zoom
      </div>
    </div>
  );
}
