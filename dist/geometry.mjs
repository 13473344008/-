export const VIEW_SCALE=1.32;
export const ORIENTATION={pitch:-.68,roll:-.32};
export const RING={planet:1.18,inner:1.65,outer:2.85,thickness:.028};
export const CAMERA={distance:9,near:.2,far:40,fov:42*Math.PI/180};
export function perspective(aspect){const f=1/Math.tan(CAMERA.fov/2),n=CAMERA.near,far=CAMERA.far;return [f/aspect,f,(far+n)/(far-n),-2*far*n/(far-n)];}
export function projectPoint([x,y,z],aspect){const [fx,fy,a,b]=perspective(aspect),d=CAMERA.distance-z;return [fx*x/d,fy*y/d,a+b/d];}
// Shared azimuth preserves coherent trajectories while the outer particles form an annulus.
export function makePoint(s,kind){const [u,v,w,q]=s,a=u*Math.PI*2,z=v*2-1,r=Math.sqrt(1-z*z);
 if(kind===0){const radius=1.18*Math.cbrt(w);return [r*Math.cos(a)*radius,z*radius,r*Math.sin(a)*radius];}
 if(kind===1){
  if(q<.42){const radius=RING.planet*(.985+.015*w);return [r*Math.cos(a)*radius,z*radius,r*Math.sin(a)*radius];}
  // Area-uniform single broad annulus: a continuous sheet of fine grains.
  const rad=Math.sqrt(RING.inner**2+(RING.outer**2-RING.inner**2)*w);
  return [Math.cos(a)*rad,(v-.5)*RING.thickness,Math.sin(a)*rad];
 }
 if(kind===2){const radius=2.7*Math.pow(w,1.35);return [r*Math.cos(a)*radius,z*radius,r*Math.sin(a)*radius];}
 if(kind===3){
  // Preserve radial ordering from the cluster. A hollow expanding shell,
  // with a sparse outer fringe, never reassigns inner particles to random rays.
  const radius=1.82+.36*Math.pow(w,.6)+(q>.87?.5*Math.pow(w,3):0);
  return [r*Math.cos(a)*radius,z*radius,r*Math.sin(a)*radius];
 }
 throw new Error('Unknown static geometry');
}
