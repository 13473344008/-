import {ParticleGlow} from './glow.js?v=orbit';
import {PlanetSurface} from './surface.js?v=orbit';
import {makePoint,perspective,CAMERA,RING,ORIENTATION} from './geometry.mjs?v=orbit';
import {smootherstep,quatMatrix,identity} from './motion.mjs?v=orbit';
const VERT=`
precision highp float;
attribute vec4 aSeed;
attribute vec3 aCore,aRing,aCluster,aNova;
uniform vec4 uProjection;
uniform vec3 uColor,uRadii;
uniform float uCamera;
uniform float uTime,uSpin,uScale,uDpr,uHeight,uRoll;
uniform float uWeights[4];
uniform vec2 uRotate,uCenter;uniform mat3 uHand;
varying vec3 vColor;varying float vAlpha,vGrain;
mat2 rot(float a){return mat2(cos(a),-sin(a),sin(a),cos(a));}
vec3 state(float kind,vec4 s,float t){
 vec3 p;
 if(kind<.5)p=aCore;
 else if(kind<1.5)p=aRing;
 else if(kind<2.5)p=aCluster*.72;
 else p=aNova*.72;
 // One common angular phase: matched particles never reverse direction or
 // cross through the center merely because their destination changes.
 // Differential orbits keep grains moving while the ring plane stays fixed.
 // The same per-particle phase is shared by every shape to keep morphs coherent.
 float speed=s.w<.42?.14:(.09+.16*pow(1.-s.z,1.4));
 p.xz=rot(uSpin+t*speed)*p.xz;
 return p;
}
void main(){
 vec3 p=vec3(0.);for(int i=0;i<4;i++){if(uWeights[i]>.0001)p+=state(float(i),aSeed,uTime)*uWeights[i];}
 p.xz=rot(uRotate.x)*p.xz;p.yz=rot(${ORIENTATION.pitch}+uRotate.y)*p.yz;p.xy=rot(${ORIENTATION.roll}+uRoll)*p.xy;p=uHand*p;p*=uScale;
 float depth=uCamera-p.z;
 // True clip-space projection: perspective divide and depth use the same camera.
 gl_Position=vec4(uProjection.x*p.x+uCenter.x*depth,uProjection.y*p.y+uCenter.y*depth,uProjection.z*depth+uProjection.w,depth);
 float spark=pow(aSeed.w,18.);
 gl_PointSize=clamp(mix(1.55+spark*.65,1.65+spark*.70,uWeights[1])*uDpr*(uHeight/850.)*(${CAMERA.distance.toFixed(1)}/depth),1.,9.);
 // One fixed chromaticity for every particle, shape and transition.
 // A fixed particle exposure avoids shape-dependent dimming during morphs.
 vColor=uColor;vGrain=uWeights[1];
 vAlpha=(.76+.22*aSeed.z)*(.90+.10*smoothstep(-2.5,2.5,p.z));
 float grain=step(.42,aSeed.w)*uWeights[1];
 vAlpha*=mix(1.,.76+.30*smoothstep(-2.85,2.85,p.z/uScale),grain);
 vec3 lighting=normalize(vec3(-.75,.65,.85));
 float along=dot(-p,lighting),miss=length(p+lighting*max(0.,along));
 float castShadow=smoothstep(uRadii.x*uScale*.88,uRadii.x*uScale*1.12,miss);
 vAlpha*=mix(1.,.58+.42*castShadow,grain*smoothstep(.45,1.,uWeights[1]));
 // A subtle limb accent reads as curvature, without a shape-wide exposure change.
 float planet=uWeights[1]*(1.-step(.42,aSeed.w));
 float limb=1.-abs(dot(normalize(p),normalize(vec3(0.,0.,uCamera)-p)));
 float diffuse=max(0.,dot(normalize(p),normalize(vec3(-.75,.65,.85))));
 float sculpt=.24+.68*diffuse+.40*pow(limb,3.);
 vec3 viewDir=normalize(vec3(0.,0.,uCamera)-p);
 float facing=dot(normalize(p),viewDir);
 // Ring material gets a solid front hemisphere instead of back-side sparkle.
 vAlpha*=1.-planet*(1.-smoothstep(-.035,.035,facing));
 vec3 ringNormal=vec3(0.,1.,0.);ringNormal.yz=rot(${ORIENTATION.pitch}+uRotate.y)*ringNormal.yz;ringNormal.xy=rot(${ORIENTATION.roll}+uRoll)*ringNormal.xy;ringNormal=uHand*ringNormal;
 float lDenom=dot(lighting,ringNormal);
 if(abs(lDenom)>.001){float t=-dot(p,ringNormal)/lDenom;float radius=length(p+lighting*t)/uScale;
  float ringShadow=step(.02,t)*smoothstep(uRadii.y-.06,uRadii.y+.06,radius)*(1.-smoothstep(uRadii.z-.06,uRadii.z+.06,radius));
  sculpt*=1.-.52*ringShadow*smoothstep(.5,1.,uWeights[1]);
 }
 float glint=pow(max(0.,dot(reflect(-lighting,normalize(p)),viewDir)),30.);
 sculpt+=.16*glint;
 vAlpha*=mix(1.,sculpt,planet);
 // Soft key light and rim make the volume readable; the cluster retains its emissive core.
 vAlpha*=mix(1.,.70+.30*diffuse+.22*pow(limb,3.),uWeights[0]);
 vAlpha*=mix(1.,.76+.22*diffuse+.24*pow(limb,2.),uWeights[3]);
 gl_PointSize*=1.+.20*planet*pow(limb,6.);
 // The near annulus also occludes globe particles between the ring's individual grains.
 if(aSeed.w<.42&&uWeights[1]>.001){
  vec3 n=vec3(0.,1.,0.);n.yz=rot(${ORIENTATION.pitch}+uRotate.y)*n.yz;n.xy=rot(${ORIENTATION.roll}+uRoll)*n.xy;n=uHand*n;
  vec3 eye=vec3(0.,0.,uCamera),ray=normalize(p-eye);float denom=dot(ray,n);
  if(abs(denom)>.0001){float distance=-dot(eye,n)/denom;vec3 hitPoint=eye+ray*distance;float radius=length(hitPoint)/uScale;
   float annulus=smoothstep(uRadii.y-.01,uRadii.y+.01,radius)*(1.-smoothstep(uRadii.z-.01,uRadii.z+.01,radius));
   float front=step(0.,distance)*(1.-smoothstep(length(p-eye)-.035,length(p-eye)-.005,distance));
   vAlpha*=1.-annulus*front*smoothstep(.45,1.,uWeights[1]);
  }
 }
 // The opaque planetary silhouette hides the far annulus even between point sprites.
 // Blend the geometric mask in as the planet assembles; never change global exposure.
 if(aSeed.w>=.42&&uWeights[1]>.001){
  vec3 eye=vec3(0.,0.,uCamera),ray=normalize(p-eye);
  float closest=-dot(eye,ray),d2=dot(eye,eye)-closest*closest;
  float radius=uRadii.x*.986*uScale;
  float hit=closest-sqrt(max(0.,radius*radius-d2));
  float silhouette=1.-smoothstep(radius*radius-.025,radius*radius+.025,d2);
  float behind=smoothstep(hit+.015,hit+.045,length(p-eye));
  vAlpha*=1.-silhouette*behind*smoothstep(.45,1.,uWeights[1]);
 }
 vAlpha=min(vAlpha,.98);
}`;
const FRAG=`precision mediump float;varying vec3 vColor;varying float vAlpha,vGrain;void main(){float r=length(gl_PointCoord-.5)*2.;if(r>1.)discard;float a=(1.-smoothstep(mix(.18,.46,vGrain),1.,r))*vAlpha;if(a<.035)discard;gl_FragColor=vec4(vColor*a,a);}`;
export class ParticleEngine{
 constructor(canvas){this.canvas=canvas;this.gl=canvas.getContext('webgl',{alpha:false,antialias:false,powerPreference:'high-performance'});if(!this.gl)throw Error('当前浏览器不支持 WebGL，请用 Chrome 或 Safari 打开。');const gl=this.gl;
 const shader=(type,src)=>{const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
 const p=gl.createProgram();gl.attachShader(p,shader(gl.VERTEX_SHADER,VERT));gl.attachShader(p,shader(gl.FRAGMENT_SHADER,FRAG));gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));gl.useProgram(p);this.program=p;this.count=innerWidth<761?52000:96000;this.weights=new Float32Array(4);this.weights[1]=1;this.fromWeights=new Float32Array(this.weights);this.morphTarget=1;this.morphTime=1;
 const data=new Float32Array(this.count*4);let seed=734123;const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};for(let i=0;i<data.length;i++)data[i]=rand();
 this.attributes=[];const bind=(name,values,size)=>{const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,values,gl.STATIC_DRAW);const loc=gl.getAttribLocation(p,name);gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,size,gl.FLOAT,false,0,0);this.attributes.push({loc,size,buffer});};
 bind('aSeed',data,4);for(const [kind,name] of ['aCore','aRing','aCluster','aNova'].entries()){const points=new Float32Array(this.count*3);for(let i=0;i<this.count;i++)points.set(makePoint(data.subarray(i*4,i*4+4),kind),i*3);bind(name,points,3);}
 this.color=new Float32Array([.98,.88,.78]);this.targetColor=new Float32Array(this.color);this.u={};for(const n of ['Color','Radii','Projection','Camera','Roll','Time','Spin','Scale','Dpr','Height','Rotate','Center','Hand'])this.u[n]=gl.getUniformLocation(p,'u'+n);this.u.Weights=gl.getUniformLocation(p,'uWeights[0]');
 this.radii=new Float32Array([RING.planet,RING.inner,RING.outer]);this.surface=new PlanetSurface(gl);this.glow=new ParticleGlow(gl);gl.useProgram(this.program);gl.enable(gl.BLEND);gl.blendFunc(gl.ONE,gl.ONE_MINUS_SRC_ALPHA);gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);this.resize();}
 setPalette(name){const colors={champagne:[.98,.88,.78],purple:[.64,.39,.94]};if(colors[name])this.targetColor.set(colors[name]);}
 resize(){this.w=innerWidth;this.h=innerHeight;this.dpr=Math.min(devicePixelRatio||1,2);this.canvas.width=Math.round(this.w*this.dpr);this.canvas.height=Math.round(this.h*this.dpr);this.gl.viewport(0,0,this.canvas.width,this.canvas.height);}
 render(time,target,rx,ry,scale,dt,roll=0,spin=0,hand=identity()){
  const g=this.gl,u=this.u;
  if(target!==this.morphTarget){this.fromWeights.set(this.weights);this.morphTarget=target;this.morphTime=0;}
  this.morphTime=Math.min(1,this.morphTime+dt/1.25);const blend=smootherstep(this.morphTime);
  for(let i=0;i<4;i++)this.weights[i]=this.fromWeights[i]*(1-blend)+(i===target?blend:0);
  for(let i=0;i<3;i++)this.color[i]+=(this.targetColor[i]-this.color[i])*(1-Math.exp(-dt*10));
  const projection=perspective(this.w/this.h),center=[0,.14],fit=Math.min(1.08,this.w/(this.h*1.22)),actualScale=fit,camera=CAMERA.distance/Math.max(.6,Math.min(1.5,scale)),handMatrix=quatMatrix(hand);
  this.glow.begin(this.canvas.width,this.canvas.height);g.clearColor(.027,.018,.045,1);g.depthMask(true);g.clear(g.COLOR_BUFFER_BIT|g.DEPTH_BUFFER_BIT);
  const w=this.weights[1],surfaceRadii=[this.radii[0]*(.7+.3*w),this.radii[1]*(.3+.7*w),this.radii[2]*(.3+.7*w)];
  this.surface.draw({color:this.color,radii:surfaceRadii,projection,center,rotate:[rx,ry],camera,scale:actualScale,roll,hand:handMatrix,weight:this.weights[1]});
  g.useProgram(this.program);for(const {loc,size,buffer}of this.attributes){g.bindBuffer(g.ARRAY_BUFFER,buffer);g.enableVertexAttribArray(loc);g.vertexAttribPointer(loc,size,g.FLOAT,false,0,0);}
  g.uniform3fv(u.Color,this.color);g.uniform3fv(u.Radii,this.radii);g.uniform1f(u.Roll,roll);g.uniform4fv(u.Projection,projection);g.uniform1f(u.Camera,camera);g.uniformMatrix3fv(u.Hand,false,handMatrix);g.uniform1f(u.Time,time);g.uniform1f(u.Spin,spin);g.uniform1fv(u.Weights,this.weights);g.uniform1f(u.Scale,actualScale);g.uniform1f(u.Dpr,this.dpr);g.uniform1f(u.Height,this.h);g.uniform2f(u.Rotate,rx,ry);g.uniform2fv(u.Center,center);
  g.colorMask(false,false,false,false);g.disable(g.BLEND);g.drawArrays(g.POINTS,0,this.count);
  g.colorMask(true,true,true,true);g.enable(g.BLEND);g.depthMask(false);g.drawArrays(g.POINTS,0,this.count);g.depthMask(true);this.glow.end(time,this.color);
 }
}
