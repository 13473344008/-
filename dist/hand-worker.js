self.exports = {};
importScripts('./vendor/vision_bundle.js');
const {FilesetResolver,HandLandmarker} = self.exports;
let detector;
self.onmessage=async({data})=>{
 if(data.type==='init'){
  try {const files=await FilesetResolver.forVisionTasks(new URL('./vendor/wasm',self.location.href).href);detector=await HandLandmarker.createFromOptions(files,{baseOptions:{modelAssetPath:new URL('./vendor/hand_landmarker.task',self.location.href).href,delegate:'CPU'},runningMode:'VIDEO',numHands:1,minHandDetectionConfidence:.6,minHandPresenceConfidence:.6,minTrackingConfidence:.6});self.postMessage({type:'ready'});}catch(e){self.postMessage({type:'error',message:e.message});}
 }else if(data.type==='frame'){
  try{const result=detector.detectForVideo(data.frame,data.time);self.postMessage({type:'result',landmarks:result.landmarks[0]||null,worldLandmarks:result.worldLandmarks[0]||null,hand:result.handedness[0]?.[0]?.categoryName||'hand',time:data.time});}catch(e){self.postMessage({type:'error',message:e.message});}finally{data.frame.close();}
 }
};
