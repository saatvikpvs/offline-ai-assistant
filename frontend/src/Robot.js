import React, { useEffect, useRef } from 'react';
import { useFrame, useLoader } from '@react-three/fiber';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { VRMLoaderPlugin } from '@pixiv/three-vrm';
import { Html } from '@react-three/drei'; 
import * as THREE from 'three';

const Robot = ({ action, modelPath }) => {
  const vrmRef = useRef();
  const targetRotation = useRef(Math.PI);

  const gltf = useLoader(GLTFLoader, modelPath, (loader) => {
    loader.register((parser) => new VRMLoaderPlugin(parser));
  });

  useEffect(() => {
    if (gltf?.userData.vrm) {
      vrmRef.current = gltf.userData.vrm;
      vrmRef.current.scene.position.set(0, 0, 0); 
      vrmRef.current.scene.rotation.y = Math.PI;
      vrmRef.current.scene.traverse(obj => { 
        obj.frustumCulled = false; 
        if (obj.isMesh) obj.castShadow = true;
      });
    }
  }, [gltf, modelPath]);

  useFrame((state, delta) => {
    if (!vrmRef.current) return;
    const vrm = vrmRef.current;
    const t = state.clock.elapsedTime;
    vrm.update(delta);

    vrm.scene.position.set(0, 0, 0);

    const bones = vrm.humanoid;
    const em = vrm.expressionManager;

    const lerpRot = (boneName, x, y, z, speed = 0.1) => {
      const node = bones.getNormalizedBoneNode(boneName);
      if (node) {
        node.rotation.x = THREE.MathUtils.lerp(node.rotation.x, x, speed);
        node.rotation.y = THREE.MathUtils.lerp(node.rotation.y, y, speed);
        node.rotation.z = THREE.MathUtils.lerp(node.rotation.z, z, speed);
      }
    };

    // Reset expressions safely to avoid stuck faces
    ["happy", "surprised", "blink", "a", "o", "aa"].forEach((exp) => {
      try { em.setValue(exp, 0); } catch(e) {}
    });

    if (action === 'wave') {
      try { em.setValue('happy', 1.0); } catch(e) {}
      lerpRot('rightUpperArm', 0.2, 0.4, 1.2, 0.2); 
      const elbow = bones.getNormalizedBoneNode('rightLowerArm');
      if (elbow) elbow.rotation.x = Math.sin(t * 12) * 0.8;
      
      // keep left arm symmetrical to idle
      lerpRot('leftUpperArm', -0.1, -0.5, 1.39, 0.1);
    } 
    else if (action === 'talk') {
      // Mouth movement
      try { em.setValue('a', Math.abs(Math.sin(t * 10)) * 0.5); } catch(e) {}
      try { em.setValue('aa', Math.abs(Math.sin(t * 10)) * 0.5); } catch(e) {} // For VRM 1.0 compatibility
      
      // Occasional blink
      if (Math.sin(t * 4) > 0.95) {
        try { em.setValue('blink', 1); } catch (e) {}
      }

      // SYMMETRICAL POSE
      lerpRot('rightUpperArm', -0.1, 0.5, -1.39, 0.1);
      lerpRot('leftUpperArm', -0.1, -0.5, 1.39, 0.1);
      lerpRot('head', 0, Math.sin(t * 2) * 0.15, 0, 0.1);
    } 
    else {
      // SYMMETRICAL IDLE
      lerpRot('rightUpperArm', -0.1, 0.5, -1.39, 0.1);
      lerpRot('leftUpperArm', -0.1, -0.5, 1.39, 0.1);
      
      // Occasional blink in idle
      if (Math.sin(t * 0.5) > 0.98) {
        try { em.setValue('blink', 1); } catch(e) {}
      }
    }

    // Left/Right rotation from user (if implemented in App.js)
    if (action === 'turn_left') targetRotation.current += delta * 1.5;
    if (action === 'turn_right') targetRotation.current -= delta * 1.5;
    vrm.scene.rotation.y = THREE.MathUtils.lerp(vrm.scene.rotation.y, targetRotation.current, 0.1);
  });

  return (
    <group>
      <primitive object={gltf.scene} />
      {/* THE CHATBOT TEXT ON THE SIDE OF AVATAR */}
      <Html position={[0.6, 1.4, 0]} center>
        <div className="avatar-speech">
          {action === 'talk' ? "Processing Offline LLM Response..." : "System Standby"}
        </div>
      </Html>
    </group>
  );
};

export default Robot;