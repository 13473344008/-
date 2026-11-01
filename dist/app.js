import {VIEW_SCALE} from './geometry.mjs?v=orbit';
import {palmPose,PalmFollow,GestureGate,identity,quatMultiply,quatSlerp} from './motion.mjs?v=orbit';
import {ParticleEngine} from './engine.js?v=orbit';
import {classifyHand} from './gestures.mjs?v=v-gesture';
const $=s=>document.querySelector(s),canvas=$('#universe'),video=$('#camera'),skeleton=$('#skeleton'),ctx=skeleton.getContext('2d');
let engine;try{engine=new ParticleEngine(canvas);}catch(e){$('#fatal').hidden=false;$('#fatal').textContent=e.message;throw e;}
let shape=1,palette='champagne',rotation=identity(),targetRotation=identity(),clock=0,lastFrame=performance.now(),lastGesture=null;
let cameraOn=false,starting=false,worker=null,stream=null,busy=false,ready=false,lastVideo=-1,lastCapture=0,lastHand=0,run=0,initTimer=null,frameTimer=null,drag=null;
const follow=new PalmFollow(),gate=new GestureGate(),reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
function status(text){if($('#status').textContent!==text)$('#status').textContent=text;}
function chooseShape(n){if(!Number.isInteger(n)||n<0||n>3)return;shape=n;gate.clear();}
$('#palette').onchange=e=>{palette=e.target.value;engine.setPalette(palette);document.documentElement.dataset.palette=palette;};
$('#shapeGestureToggle').onchange=()=>{gate.clear();};
function reset(){rotation=targetRotation=identity();follow.reset();gate.clear();status(cameraOn?'手掌入镜即可跟随':'');}
$('#resetButton').onclick=()=>{reset();$('#settings').open=false;};
const axis=(x,y,z,a)=>[x*Math.sin(a/2),y*Math.sin(a/2),z*Math.sin(a/2),Math.cos(a/2)];
canvas.addEventListener('pointerdown',e=>{if(cameraOn)return;$('#settings').open=false;drag={id:e.pointerId,x:e.clientX,q:[...targetRotation]};canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointermove',e=>{if(!drag||cameraOn||drag.id!==e.pointerId)return;const yaw=axis(0,1,0,(e.clientX-drag.x)/innerWidth*3.2);targetRotation=quatMultiply(yaw,drag.q);});
for(const event of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(event,()=>drag=null);
addEventListener('keydown',e=>{if(e.target.closest('input,select,summary'))return;if(/^[1-4]$/.test(e.key))chooseShape(+e.key-1);if(e.key.toLowerCase()==='r')reset();});
addEventListener('resize',()=>engine.resize());
canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();$('#fatal').hidden=false;$('#fatal').textContent='图形连接中断，请刷新页面。';});
const edges=[[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[5,9],[9,10],[10,11],[11,12],[9,13],[13,14],[14,15],[15,16],[13,17],[0,17],[17,18],[18,19],[19,20]];
function drawHand(lm){ctx.clearRect(0,0,skeleton.width,skeleton.height);if(!lm)return;ctx.strokeStyle=palette==='champagne'?'#ebcda8':'#c9a5f2';ctx.lineWidth=2;ctx.beginPath();for(const[a,b]of edges){ctx.moveTo(lm[a].x*skeleton.width,lm[a].y*skeleton.height);ctx.lineTo(lm[b].x*skeleton.width,lm[b].y*skeleton.height);}ctx.stroke();}
function freeze(resetGesture=true){if(follow.mode==='following'||follow.mode==='acquiring'){targetRotation=[...rotation];follow.rotation=[...rotation];follow.suspend();}if(resetGesture)gate.clear();}
function stopCamera(show=true){freeze();drag=null;run++;clearTimeout(initTimer);clearTimeout(frameTimer);stream?.getTracks().forEach(t=>t.stop());stream=null;video.srcObject=null;worker?.terminate();worker=null;cameraOn=starting=ready=busy=false;$('#cameraWindow').hidden=true;$('#cameraButton').disabled=false;$('#cameraButton').textContent='开启手势';$('#cameraButton').classList.remove('active');if(show)status('');}
function failCamera(message){stopCamera(false);status(message);}
async function startCamera(){
 if(cameraOn||starting){stopCamera();return;}starting=true;const current=++run;$('#cameraButton').disabled=true;$('#cameraButton').textContent='连接中…';status('请允许摄像头访问');
 try{
  if(!navigator.mediaDevices?.getUserMedia)throw Error('请在 localhost 或 HTTPS 下开启手势');
  const acquired=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:640},height:{ideal:360},facingMode:'user'},audio:false});
  if(current!==run){acquired.getTracks().forEach(t=>t.stop());return;}stream=acquired;video.srcObject=stream;await video.play();if(current!==run)return;
  cameraOn=true;starting=false;follow.reset(rotation);lastGesture=null;drag=null;gate.clear();lastHand=performance.now();lastVideo=-1;lastCapture=0;
  skeleton.width=640;skeleton.height=Math.round(640*video.videoHeight/video.videoWidth);$('#cameraWindow').style.aspectRatio=video.videoWidth/video.videoHeight;$('#cameraWindow').hidden=false;
  $('#cameraButton').disabled=false;$('#cameraButton').textContent='关闭手势';$('#cameraButton').classList.add('active');status('正在加载手势模型…');
  worker=new Worker(new URL('./hand-worker.js?v=orbit',import.meta.url));
  initTimer=setTimeout(()=>{if(current===run)failCamera('模型加载超时，请重试');},45000);
  worker.onerror=()=>{if(current===run)failCamera('手势模型启动失败，请使用 Chrome 重试');};
  worker.onmessage=({data})=>{
   if(current!==run)return;
   if(data.type==='ready'){clearTimeout(initTimer);ready=true;status('手掌入镜即可跟随');}
   if(data.type==='error')failCamera('手势识别暂时不可用，请重试');
   if(data.type==='result'){
    clearTimeout(frameTimer);busy=false;const now=performance.now();
    if(document.hidden||now-data.time>500){freeze();return;}
    drawHand(data.landmarks);const pose=palmPose(data.landmarks,data.worldLandmarks,data.hand);
    if(pose){lastHand=now;const state=follow.update(pose,now);targetRotation=state.rotation;status(state.mode==='acquiring'?'正在稳住画面…':`${['星核','星环','星团','超新星'][shape]} · 平稳跟随`);
    }else if(now-lastHand>160){freeze(false);status('等待有效转向');}
    // Shape recognition does not wait for rotation calibration or world pose recovery.
    lastGesture=classifyHand(data.landmarks,data.worldLandmarks,video.videoWidth/video.videoHeight)?.shape??null;
    if($('#shapeGestureToggle').checked){const next=gate.update(lastGesture,now,shape);if(next!==null)chooseShape(next);}else gate.clear();
   }
  };worker.postMessage({type:'init'});
 }catch(e){if(current!==run)return;const messages={NotAllowedError:'摄像头未获授权',NotFoundError:'未找到摄像头',NotReadableError:'摄像头被其他应用占用'};failCamera(messages[e.name]||e.message||'无法启动摄像头');}
}
$('#cameraButton').onclick=startCamera;
async function capture(now){if(!cameraOn||!ready||busy||video.readyState<2||now-lastCapture<40||lastVideo===video.currentTime)return;busy=true;lastCapture=now;lastVideo=video.currentTime;const current=run;
 try{const frame=await createImageBitmap(video);if(current!==run||!worker){frame.close();return;}frameTimer=setTimeout(()=>{if(current===run)failCamera('手势识别响应超时，请重试');},10000);worker.postMessage({type:'frame',frame,time:now},[frame]);}catch{if(current===run)failCamera('无法读取摄像头画面');}}
function render(now){const dt=Math.min((now-lastFrame)/1000,.05);lastFrame=now;clock+=dt;
 if(cameraOn&&ready&&now-lastHand>300){freeze(false);status('等待手掌入镜');}
 if(!document.hidden){const smooth=1-Math.exp(-dt/(cameraOn?.035:.06));rotation=quatSlerp(rotation,targetRotation,smooth);engine.render(reduced?clock*.25:clock,shape,.25+2*Math.atan2(rotation[1],rotation[3]),.2,VIEW_SCALE,dt,0,0);capture(now);
 }
 requestAnimationFrame(render);
}
requestAnimationFrame(render);
addEventListener('visibilitychange',()=>{if(document.hidden&&cameraOn)freeze();});addEventListener('pagehide',()=>stopCamera(false));
