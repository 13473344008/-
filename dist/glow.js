// Spatial bloom only: fixed exposure, no temporal history or brightness pumping.
const vertex=`attribute vec2 aPosition;varying vec2 vUv;void main(){vUv=aPosition*.5+.5;gl_Position=vec4(aPosition,0.,1.);}`;
const fragment=`precision highp float;varying vec2 vUv;uniform sampler2D uScene,uGlow;uniform vec2 uStep;uniform int uPass;uniform vec3 uColor;uniform vec2 uViewport;uniform float uTime;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
vec3 atmosphere(){
 vec2 p=(vUv-.5)*vec2(uViewport.x/uViewport.y,1.);float drift=.035*sin(uTime*.065);
 vec2 a=(p-vec2(-.72,.43))*vec2(.9,1.8),b=(p-vec2(.83,-.32))*vec2(.95,2.);
 float haze=.12*exp(-dot(a,a)*2.1)+.085*exp(-dot(b,b)*2.4)+.028*exp(-dot(p,p)*2.);
 float beam=.043*exp(-pow((p.x*.55+p.y*.84+.14+drift)/.12,2.))*exp(-dot(p,p)*.65);
 float echo=.018*exp(-pow((p.x*.55+p.y*.84-.28-drift)/.23,2.));
 vec2 grid=vUv*vec2(uViewport.x/uViewport.y*80.,80.),cell=floor(grid);float seed=hash(cell);
 vec2 point=fract(grid)-vec2(.18+.64*hash(cell+7.),.18+.64*hash(cell+19.));float d=dot(point,point);
 float stars=step(.989,seed)*(.22*exp(-d/.003)+.035*exp(-d/.025))*smoothstep(.24,.52,length(p));
 return uColor*(haze+beam+echo+stars);
}
vec3 bright(vec2 uv){vec3 c=max(texture2D(uScene,uv).rgb-vec3(.027,.018,.045),vec3(0.));return c*smoothstep(.16,.7,max(c.r,max(c.g,c.b)));}
void main(){vec3 c;
 if(uPass==0){c=(bright(vUv+uStep)+bright(vUv-uStep)+bright(vUv+uStep*vec2(1.,-1.))+bright(vUv+uStep*vec2(-1.,1.)))*.25;}
 else if(uPass==1){c=texture2D(uScene,vUv).rgb*.227027;c+=(texture2D(uScene,vUv+uStep*1.384615).rgb+texture2D(uScene,vUv-uStep*1.384615).rgb)*.316216;c+=(texture2D(uScene,vUv+uStep*3.230769).rgb+texture2D(uScene,vUv-uStep*3.230769).rgb)*.070270;}
 else{vec3 scene=texture2D(uScene,vUv).rgb;float cover=smoothstep(.06,.32,max(scene.r,max(scene.g,scene.b)));c=scene+texture2D(uGlow,vUv).rgb*.65+atmosphere()*(1.-cover*.96);c/=max(1.,max(c.r,max(c.g,c.b)));}
 gl_FragColor=vec4(c,1.);}`;
export class ParticleGlow{
 constructor(gl){this.gl=gl;const compile=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};this.program=gl.createProgram();gl.attachShader(this.program,compile(gl.VERTEX_SHADER,vertex));gl.attachShader(this.program,compile(gl.FRAGMENT_SHADER,fragment));gl.linkProgram(this.program);if(!gl.getProgramParameter(this.program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(this.program));this.position=gl.getAttribLocation(this.program,'aPosition');this.buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);this.u={};for(const name of ['Scene','Glow','Step','Pass','Color','Viewport','Time'])this.u[name]=gl.getUniformLocation(this.program,'u'+name);this.targets=[0,1,2].map(()=>({texture:gl.createTexture(),framebuffer:gl.createFramebuffer()}));this.depth=gl.createRenderbuffer();}
 resize(w,h){if(w===this.w&&h===this.h)return;this.w=w;this.h=h;const g=this.gl;for(const [i,t]of this.targets.entries()){t.w=i?Math.max(1,Math.ceil(w/4)):w;t.h=i?Math.max(1,Math.ceil(h/4)):h;g.bindTexture(g.TEXTURE_2D,t.texture);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MIN_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MAG_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_S,g.CLAMP_TO_EDGE);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_T,g.CLAMP_TO_EDGE);g.texImage2D(g.TEXTURE_2D,0,g.RGBA,t.w,t.h,0,g.RGBA,g.UNSIGNED_BYTE,null);g.bindFramebuffer(g.FRAMEBUFFER,t.framebuffer);g.framebufferTexture2D(g.FRAMEBUFFER,g.COLOR_ATTACHMENT0,g.TEXTURE_2D,t.texture,0);if(i===0){g.bindRenderbuffer(g.RENDERBUFFER,this.depth);g.renderbufferStorage(g.RENDERBUFFER,g.DEPTH_COMPONENT16,w,h);g.framebufferRenderbuffer(g.FRAMEBUFFER,g.DEPTH_ATTACHMENT,g.RENDERBUFFER,this.depth);}if(g.checkFramebufferStatus(g.FRAMEBUFFER)!==g.FRAMEBUFFER_COMPLETE)throw Error('光影缓冲创建失败');}}
 begin(w,h){const g=this.gl;this.resize(w,h);g.bindFramebuffer(g.FRAMEBUFFER,this.targets[0].framebuffer);g.viewport(0,0,w,h);g.enable(g.DEPTH_TEST);g.enable(g.BLEND);g.blendFunc(g.ONE,g.ONE_MINUS_SRC_ALPHA);g.depthMask(true);}
 end(time=0,color=[.98,.88,.78]){const g=this.gl,[scene,a,b]=this.targets,u=this.u;g.disable(g.DEPTH_TEST);g.disable(g.BLEND);g.depthMask(false);g.useProgram(this.program);g.bindBuffer(g.ARRAY_BUFFER,this.buffer);g.enableVertexAttribArray(this.position);g.vertexAttribPointer(this.position,2,g.FLOAT,false,0,0);g.uniform1i(u.Scene,0);g.uniform1i(u.Glow,1);g.uniform3fv(u.Color,color);g.uniform2f(u.Viewport,this.w,this.h);g.uniform1f(u.Time,time);
 const pass=(target,source,kind,x,y)=>{g.bindFramebuffer(g.FRAMEBUFFER,target?.framebuffer||null);g.viewport(0,0,target?.w||this.w,target?.h||this.h);g.activeTexture(g.TEXTURE0);g.bindTexture(g.TEXTURE_2D,source.texture);g.uniform1i(u.Pass,kind);g.uniform2f(u.Step,x,y);g.drawArrays(g.TRIANGLES,0,3);};
 // Never leave a render target bound to the other sampler (WebGL feedback loop).
 g.activeTexture(g.TEXTURE1);g.bindTexture(g.TEXTURE_2D,scene.texture);
 pass(a,scene,0,1/this.w,1/this.h);pass(b,a,1,1/a.w,0);pass(a,b,1,0,1/a.h);
 g.activeTexture(g.TEXTURE1);g.bindTexture(g.TEXTURE_2D,a.texture);pass(null,scene,2,0,0);g.activeTexture(g.TEXTURE0);g.depthMask(true);
 }
}
