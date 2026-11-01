import {ORIENTATION} from './geometry.mjs?v=orbit';
// Analytic lighting under the particle layer. Uses the same camera and annulus
// as the particles; this supplies continuous form without changing exposure.
const VERT=`attribute vec2 aPosition;varying vec2 vNdc;void main(){vNdc=aPosition;gl_Position=vec4(aPosition,0.,1.);}`;
const FRAG=`precision highp float;
varying vec2 vNdc;
uniform vec3 uColor,uRadii;
uniform vec4 uProjection;
uniform vec2 uCenter,uRotate;uniform mat3 uHand;
uniform float uCamera,uScale,uRoll,uWeight;
mat2 rot(float a){return mat2(cos(a),-sin(a),sin(a),cos(a));}
void main(){
 vec3 eye=vec3(0.,0.,uCamera),ray=normalize(vec3((vNdc-uCenter)/uProjection.xy,-1.));
 float R=uRadii.x*uScale;
 float closest=-dot(eye,ray),d2=dot(eye,eye)-closest*closest;
 float discriminant=R*R-d2;
 float sphereT=1000.;float sphereLight=0.;
 if(discriminant>=0.){
  sphereT=closest-sqrt(discriminant);vec3 normal=normalize(eye+ray*sphereT);
  float facing=max(0.,dot(normal,-ray)),rim=pow(1.-facing,3.);
  float diffuse=max(0.,dot(normal,normalize(vec3(-.75,.65,.85))));
  sphereLight=.025+.21*pow(diffuse,1.3)+.16*rim;
 }
 vec3 normal=vec3(0.,1.,0.);normal.yz=rot(${ORIENTATION.pitch}+uRotate.y)*normal.yz;normal.xy=rot(${ORIENTATION.roll}+uRoll)*normal.xy;normal=uHand*normal;
 float denom=dot(ray,normal),ringT=1000.,ringLight=0.,ringMask=0.;
 if(abs(denom)>.0001){
  float t=-dot(eye,normal)/denom;vec3 p=eye+ray*t;float radius=length(p)/uScale;
  if(t>0.){ringMask=smoothstep(uRadii.y-.009,uRadii.y+.009,radius)*(1.-smoothstep(uRadii.z-.012,uRadii.z+.012,radius));
   if(ringMask>.001){ringT=t;float nearSide=smoothstep(-uRadii.z,uRadii.z,p.z/uScale);
    float bands=.90+.07*sin(radius*57.)+.03*sin(radius*173.);
    // The underlayer only supports the grains; it must not fill their gaps.
    vec3 lightDir=normalize(vec3(-.75,.65,.85));
    float along=dot(-p,lightDir),miss=length(p+lightDir*max(0.,along));
    float shadow=smoothstep(R*.88,R*1.12,miss);
    ringLight=(.035+.07*nearSide)*bands*ringMask*mix(.25,1.,shadow);
   }
  }
 }
 if(sphereT<1000.){
  vec3 hit=eye+ray*sphereT,lightDir=normalize(vec3(-.75,.65,.85));float ld=dot(lightDir,normal);
  if(abs(ld)>.001){float t=-dot(hit,normal)/ld;float r=length(hit+lightDir*t)/uScale;
   float shadow=step(.02,t)*smoothstep(uRadii.y-.06,uRadii.y+.06,r)*(1.-smoothstep(uRadii.z-.06,uRadii.z+.06,r));sphereLight*=1.-.55*shadow;
  }
 }
 float rimDistance=abs(sqrt(max(d2,0.))-R)/uScale;
 float halo=(.12*exp(-rimDistance*90.)+.012*exp(-rimDistance*18.))*(.45+.55*smoothstep(-R,R,-(eye+ray*closest).x));
 float light=sphereT<ringT?sphereLight+halo:ringLight;
 if(sphereT==1000.&&ringT==1000.)light=halo;
 // Material appears continuously with the geometry; no auto-exposure or time flicker.
 float phase=clamp((uWeight-.5)*2.,0.,1.);
 float material=phase*phase*phase*(phase*(phase*6.-15.)+10.);
 float alpha=clamp(light*material,0.,.75);
 if(alpha<.001)discard;
 gl_FragColor=vec4(uColor*alpha,alpha);
}`;
export class PlanetSurface{
 constructor(gl){this.gl=gl;const shader=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};this.program=gl.createProgram();gl.attachShader(this.program,shader(gl.VERTEX_SHADER,VERT));gl.attachShader(this.program,shader(gl.FRAGMENT_SHADER,FRAG));gl.linkProgram(this.program);if(!gl.getProgramParameter(this.program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(this.program));this.position=gl.getAttribLocation(this.program,'aPosition');this.buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);this.u={};for(const n of ['Color','Radii','Projection','Center','Rotate','Camera','Scale','Roll','Weight','Hand'])this.u[n]=gl.getUniformLocation(this.program,'u'+n);}
 draw({color,radii,projection,center,rotate,camera,scale,roll,hand,weight}){if(weight<.001)return;const g=this.gl,u=this.u;g.useProgram(this.program);g.disable(g.DEPTH_TEST);g.depthMask(false);g.enable(g.BLEND);g.bindBuffer(g.ARRAY_BUFFER,this.buffer);g.enableVertexAttribArray(this.position);g.vertexAttribPointer(this.position,2,g.FLOAT,false,0,0);g.uniform3fv(u.Color,color);g.uniform3fv(u.Radii,radii);g.uniform4fv(u.Projection,projection);g.uniform2fv(u.Center,center);g.uniform2fv(u.Rotate,rotate);g.uniform1f(u.Camera,camera);g.uniform1f(u.Scale,scale);g.uniform1f(u.Roll,roll);g.uniformMatrix3fv(u.Hand,false,hand);g.uniform1f(u.Weight,weight);g.drawArrays(g.TRIANGLES,0,6);g.enable(g.DEPTH_TEST);g.depthMask(true);}
}
