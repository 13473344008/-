import test from 'node:test';import assert from 'node:assert/strict';import {CAMERA,makePoint,projectPoint} from '../dist/geometry.mjs';
test('near/far plane map to canonical clip depth',()=>{assert.ok(Math.abs(projectPoint([0,0,CAMERA.distance-CAMERA.near],1)[2]+1)<1e-10);assert.ok(Math.abs(projectPoint([0,0,CAMERA.distance-CAMERA.far],1)[2]-1)<1e-10);});
test('near points appear larger and have smaller depth than far points',()=>{const near=projectPoint([1,0,2],1),far=projectPoint([1,0,-2],1);assert.ok(near[0]>far[0]);assert.ok(near[2]<far[2]);});
test('aspect correction preserves circles in screen pixels',()=>{const a=16/9;assert.ok(Math.abs(projectPoint([1,0,0],a)[0]*a-projectPoint([0,1,0],a)[1])<1e-10);});
test('core remains filled; planetary ring separates its sphere from a thin annulus',()=>{let inner=0,planet=0,disk=0;for(let i=1;i<=1000;i++){const seed=[i*.618%1,i*.417%1,i/1000,i*.719%1],core=makePoint(seed,0),ring=makePoint(seed,1);assert.ok(Math.hypot(...core)<=1.181);if(Math.hypot(...core)<.6)inner++;if(seed[3]<.42){planet++;assert.ok(Math.hypot(...ring)>1.162&&Math.hypot(...ring)<=1.181);}else{disk++;const rad=Math.hypot(ring[0],ring[2]);assert.ok(rad>=1.65&&rad<=2.851);assert.ok(Math.abs(ring[1])<=.015);}}assert.ok(inner>100);assert.ok(planet>400&&disk>550);});
test('core-to-ring outer trajectories preserve azimuth while spreading radially',()=>{const s=[.23,.37,.64,.7],c=makePoint(s,0),r=makePoint(s,1);assert.ok(Math.abs(Math.atan2(c[2],c[0])-Math.atan2(r[2],r[0]))<1e-10);});
test('cluster is centrally concentrated',()=>{let inner=0;for(let i=1;i<=1000;i++){const s=[i*.618%1,i*.417%1,i/1000,i*.719%1];if(Math.hypot(...makePoint(s,2))<1)inner++;}assert.ok(inner>400);});

test('cluster and shock shell retain each particle ray throughout morphs',()=>{
 for(let i=1;i<1000;i++){
  const seed=[i*.618%1,i*.417%1,i/1000,i*.719%1],points=[2,3].map(k=>makePoint(seed,k));
  for(let a=0;a<2;a++)for(let b=a+1;b<2;b++){
   const p=points[a],q=points[b],rp=Math.hypot(...p),rq=Math.hypot(...q);
   assert.ok(p.reduce((s,x,j)=>s+x*q[j],0)/(rp*rq)>1-1e-10);
   for(const t of [.25,.5,.75])assert.ok(Math.hypot(...p.map((x,j)=>x*(1-t)+q[j]*t))>=Math.min(rp,rq)-1e-10);
  }
  assert.ok(Math.hypot(...points[1])>=1.82&&Math.hypot(...points[1])<=2.68);
 }
});
