export const wrapAngle=a=>Math.atan2(Math.sin(a),Math.cos(a));
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const norm=a=>{const n=Math.hypot(...a);return n>1e-8?a.map(x=>x/n):null;};
const sub=(a,b)=>a.map((x,i)=>x-b[i]);
export const identity=()=>[0,0,0,1];
export function quatMultiply(a,b){const [x,y,z,w]=a,[X,Y,Z,W]=b;return norm([w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]);}
export const quatInverse=q=>[-q[0],-q[1],-q[2],q[3]];
export const quatAngle=(a,b)=>2*Math.acos(clamp(Math.abs(dot(a,b)),-1,1));
export function quatSlerp(a,b,t){let d=dot(a,b);if(d<0){b=b.map(x=>-x);d=-d;}if(d>.9995)return norm(a.map((x,i)=>x+(b[i]-x)*t));const angle=Math.acos(clamp(d,-1,1)),s=Math.sin(angle);return a.map((x,i)=>(Math.sin((1-t)*angle)*x+Math.sin(t*angle)*b[i])/s);}
export function quatMatrix(q){const [x,y,z,w]=q;return [1-2*(y*y+z*z),2*(x*y+z*w),2*(x*z-y*w),2*(x*y-z*w),1-2*(x*x+z*z),2*(y*z+x*w),2*(x*z+y*w),2*(y*z-x*w),1-2*(x*x+y*y)];}
// Only palm heading drives local-Y rotation. Pitch, roll and distance are ignored.
export function palmPose(lm,world,hand='hand'){
 const valid=a=>a?.length===21&&a.every(p=>[p.x,p.y,p.z].every(Number.isFinite));
 if(!valid(lm)||!valid(world))return null;
 if([0,5,9,17].some(i=>lm[i].x<.015||lm[i].x>.985||lm[i].y<.015||lm[i].y>.985))return null;
 const v=i=>[-world[i].x,-world[i].y,-world[i].z];
 const x=norm(sub(v(5),v(17))),up=norm(sub(v(9),v(0)));if(!x||!up)return null;
 const z=norm(cross(x,up));if(!z)return null;// A near-vertical normal has no reliable horizontal heading.
 if(Math.hypot(z[0],z[2])<.3)return null;
 const heading=Math.atan2(z[0],z[2]);
 return {rotation:[0,Math.sin(heading/2),0,Math.cos(heading/2)],hand};
}
export class PalmFollow{
 constructor(){this.reset();}
 reset(rotation=identity()){
  this.rotation=[...rotation];this.mode='waiting';this.lastTime=null;this.lastPose=null;
  this.samples=[];this.anchor=null;this.acquireStart=null;this.outliers=0;
  this.heldRotation=[...rotation];this.hand=null;this.candidateHand=null;this.handCount=0;
 }
 suspend(){this.mode='waiting';this.lastTime=null;this.lastPose=null;this.samples=[];this.acquireStart=null;this.anchor=null;}
 update(pose,now){
  if(!pose||pose.rotation?.length!==4||!pose.rotation.every(Number.isFinite)){this.suspend();return this.snapshot();}
  if(this.lastTime!==null&&now-this.lastTime<=300&&pose.hand!==this.hand){
   this.handCount=this.candidateHand===pose.hand?this.handCount+1:1;this.candidateHand=pose.hand;
   if(this.handCount<3){this.lastTime=now;return this.snapshot();}
  }else this.handCount=0;
  if(this.lastTime===null||now-this.lastTime>300||pose.hand!==this.hand){
   this.mode='acquiring';this.acquireStart=now;this.samples=[];this.lastPose=null;this.anchor=null;this.outliers=0;this.hand=pose.hand;
  }
  const dt=clamp(this.lastTime===null?.04:(now-this.lastTime)/1000,.008,.08);this.lastTime=now;
  if(this.lastPose&&(quatAngle(pose.rotation,this.lastPose.rotation)>1.2)&&this.outliers++<2){return this.snapshot();}
  this.outliers=0;this.lastPose=pose;
  this.samples.push({rotation:[...pose.rotation]});
  if(this.samples.length>5)this.samples.shift();
  // A quaternion medoid rejects single-frame impulses without angle wrapping.
  const recent=this.samples.slice(-3);
  const filtered=recent.reduce((best,p)=>recent.reduce((v,r)=>v+quatAngle(p.rotation,r.rotation),0)<recent.reduce((v,r)=>v+quatAngle(best.rotation,r.rotation),0)?p:best,recent[0]);
  if(this.mode==='acquiring'){
   const spread=Math.max(...this.samples.map(p=>quatAngle(p.rotation,filtered.rotation)));
   if(now-this.acquireStart<180||this.samples.length<4||spread>.24)return this.snapshot();
   this.anchor={rotation:[...filtered.rotation],view:[...this.rotation]};
   this.heldRotation=[...this.rotation];this.mode='following';
   return this.snapshot();
  }
  const relative=quatMultiply(filtered.rotation,quatInverse(this.anchor.rotation));
  const desired=quatMultiply(relative,this.anchor.view);
  const angle=quatAngle(this.heldRotation,desired);
  // Hysteresis: hand tremor is held; sustained motion crosses the deadband.
  if(angle>.038)this.heldRotation=quatSlerp(this.heldRotation,desired,(angle-.022)/angle);
  const error=quatAngle(this.rotation,this.heldRotation);
  const rotationTau=.19-.145*smootherstep(clamp((error-.035)/.20,0,1));
  const step=Math.min(1-Math.exp(-dt/rotationTau),error>1e-7?2.5*dt/error:1);
  this.rotation=quatSlerp(this.rotation,this.heldRotation,step);
  return this.snapshot();
 }
 snapshot(){return {rotation:[...this.rotation],mode:this.mode};}
}
export class GestureGate{
 constructor(){this.clear();this.lockUntil=0;}
 clear(){this.pending=null;this.samples=0;this.last=null;}
 update(shape,now,current){
  if(this.last!==null&&now-this.last>180)this.clear();this.last=now;
  if(shape===null||shape===current||now<this.lockUntil){this.pending=null;this.samples=0;return null;}
  if(this.pending!==shape){this.pending=shape;this.samples=1;return null;}
  if(++this.samples<3)return null;
  this.pending=null;this.samples=0;this.lockUntil=now+220;return shape;
 }
}
export function smootherstep(t){t=Math.max(0,Math.min(1,t));return t*t*t*(t*(t*6-15)+10);}
