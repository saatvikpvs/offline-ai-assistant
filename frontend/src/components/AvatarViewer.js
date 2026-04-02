
import { useEffect } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader";
import { VRMLoaderPlugin } from "@pixiv/three-vrm";

export default function AvatarViewer({ audio }) {

let vrm = null;
let analyser = null;
let dataArray = null;

let mouseX = 0;
let mouseY = 0;

useEffect(() => {

  const clock = new THREE.Clock();

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x222222);

  const camera = new THREE.PerspectiveCamera(
    35,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
  );

  camera.position.set(0, 1.6, 8);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);

  document.body.appendChild(renderer.domElement);

  const light = new THREE.DirectionalLight(0xffffff, 1);
  light.position.set(1, 1, 1);
  scene.add(light);

  window.addEventListener("mousemove", (event) => {
    mouseX = (event.clientX / window.innerWidth) - 0.5;
    mouseY = (event.clientY / window.innerHeight) - 0.5;
  });

  const loader = new GLTFLoader();
  loader.register(parser => new VRMLoaderPlugin(parser));

  loader.load("/8329890252317737768.vrm", (gltf) => {

    vrm = gltf.userData.vrm;

    scene.add(vrm.scene);

    vrm.scene.rotation.y = Math.PI;
    vrm.scene.scale.set(2,2,2);

    // Reset pose
    vrm.humanoid.resetNormalizedPose();

    // Fix T-pose (arms down)
    const leftArm = vrm.humanoid.getNormalizedBoneNode("leftUpperArm");
    const rightArm = vrm.humanoid.getNormalizedBoneNode("rightUpperArm");

    if(leftArm) leftArm.rotation.z = 1.3;
    if(rightArm) rightArm.rotation.z = -1.3;
  });

  function animate(){

    requestAnimationFrame(animate);

    const delta = clock.getDelta();

    if(vrm) vrm.update(delta);

    // Lip sync
    if(vrm && analyser){

      analyser.getByteFrequencyData(dataArray);

      const volume = dataArray.reduce((a,b)=>a+b)/dataArray.length;

      if(vrm.expressionManager){
        vrm.expressionManager.setValue("aa", volume/255);
      }
    }

    // Head follow cursor
    if(vrm){

      const head = vrm.humanoid.getNormalizedBoneNode("head");

      if(head){

        head.rotation.y = mouseX * 0.6;
        head.rotation.x = -mouseY * 0.4;

        head.rotation.z = Math.sin(Date.now()*0.002)*0.05;
      }
    }

    renderer.render(scene,camera);
  }

  animate();

},[]);


// Audio analyser for lip sync
useEffect(()=>{

  if(!audio) return;

  const audioContext = new AudioContext();

  const source = audioContext.createMediaElementSource(audio);

  analyser = audioContext.createAnalyser();

  source.connect(analyser);

  analyser.connect(audioContext.destination);

  dataArray = new Uint8Array(analyser.frequencyBinCount);

},[audio]);

return null;

}

