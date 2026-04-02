
import { useEffect, useRef } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader";
import { VRMLoaderPlugin } from "@pixiv/three-vrm";

export default function AvatarViewer({ avatar, audio }) {

const sceneRef = useRef();
const cameraRef = useRef();
const rendererRef = useRef();
const vrmRef = useRef();

const analyserRef = useRef();
const dataArrayRef = useRef();

let mouseX = 0;
let mouseY = 0;

// ---------- Scene Setup ----------
useEffect(() => {

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x222222);

  const camera = new THREE.PerspectiveCamera(
    35,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
  );

  camera.position.set(0,1.6,8);

  const renderer = new THREE.WebGLRenderer({ antialias:true });
  renderer.setSize(window.innerWidth,window.innerHeight);

  document.body.appendChild(renderer.domElement);

  const light = new THREE.DirectionalLight(0xffffff,1);
  light.position.set(1,1,1);
  scene.add(light);

  sceneRef.current = scene;
  cameraRef.current = camera;
  rendererRef.current = renderer;

  const clock = new THREE.Clock();

  function animate(){

    requestAnimationFrame(animate);

    const delta = clock.getDelta();

    if(vrmRef.current){
      vrmRef.current.update(delta);
    }

    // Lip sync
    if(vrmRef.current && analyserRef.current){

      analyserRef.current.getByteFrequencyData(dataArrayRef.current);

      const volume = dataArrayRef.current.reduce((a,b)=>a+b)/dataArrayRef.current.length;

      if(vrmRef.current.expressionManager){
        vrmRef.current.expressionManager.setValue("aa", volume/255);
      }
    }

    // Head follow cursor
    if(vrmRef.current){

      const head = vrmRef.current.humanoid.getNormalizedBoneNode("head");

      if(head){
        head.rotation.y = mouseX * 0.6;
        head.rotation.x = -mouseY * 0.4;
      }
    }

    renderer.render(scene,camera);
  }

  animate();

  window.addEventListener("mousemove",(event)=>{
    mouseX = (event.clientX / window.innerWidth) - 0.5;
    mouseY = (event.clientY / window.innerHeight) - 0.5;
  });

},[]);


// ---------- Avatar Loader ----------
useEffect(()=>{

  const loader = new GLTFLoader();
  loader.register(parser => new VRMLoaderPlugin(parser));

  if(vrmRef.current){
    sceneRef.current.remove(vrmRef.current.scene);
    vrmRef.current = null;
  }

  loader.load(avatar,(gltf)=>{

    const vrm = gltf.userData.vrm;

    vrm.scene.rotation.y = Math.PI;
    vrm.scene.scale.set(2,2,2);

    // smooth fade in
    vrm.scene.traverse(obj=>{
      if(obj.material){
        obj.material.transparent = true;
        obj.material.opacity = 0;
      }
    });

    sceneRef.current.add(vrm.scene);
    vrmRef.current = vrm;

    // Fix arms
    const leftArm = vrm.humanoid.getNormalizedBoneNode("leftUpperArm");
    const rightArm = vrm.humanoid.getNormalizedBoneNode("rightUpperArm");

    if(leftArm) leftArm.rotation.z = 1.3;
    if(rightArm) rightArm.rotation.z = -1.3;

    // fade animation
    let opacity = 0;

    function fade(){
      opacity += 0.05;

      vrm.scene.traverse(obj=>{
        if(obj.material){
          obj.material.opacity = Math.min(opacity,1);
        }
      });

      if(opacity < 1){
        requestAnimationFrame(fade);
      }
    }

    fade();

  });

},[avatar]);


// ---------- Audio Lip Sync ----------
useEffect(()=>{

  if(!audio) return;

  const audioContext = new AudioContext();
  const source = audioContext.createMediaElementSource(audio);

  const analyser = audioContext.createAnalyser();

  source.connect(analyser);
  analyser.connect(audioContext.destination);

  analyserRef.current = analyser;
  dataArrayRef.current = new Uint8Array(analyser.frequencyBinCount);

},[audio]);

return null;

}

