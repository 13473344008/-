import test from 'node:test';import assert from 'node:assert/strict';import {classifyHand} from '../dist/gestures.mjs';
function hand(fingers=[true,true,true,true],thumb='open'){
 const p=Array.from({length:21},()=>({x:.5,y:.7,z:0}));p[0]={x:.5,y:.9,z:0};
 for(let f=0;f<4;f++){const base=5+f*4,x=.35+f*.1,open=fingers[f];p[base]={x,y:.6,z:0};p[base+1]={x,y:.47,z:0};p[base+2]={x,y:open?.34:.55,z:0};p[base+3]={x,y:open?.2:.69,z:0};}
 p[2]={x:.32,y:.74,z:0};p[3]={x:.22,y:.65,z:0};p[4]=thumb==='open'?{x:.10,y:.55,z:0}:thumb==='closed'?{x:.39,y:.64,z:0}:{x:.19,y:.60,z:0};return p;
}
test('five fingers + spread thumb selects globular cluster',()=>assert.equal(classifyHand(hand()).shape,2));
test('closed fist selects core, not pinch',()=>{const p=hand([false,false,false,false],'closed');p[4]={...p[8]};assert.equal(classifyHand(p).shape,0);});
test('thumb-index contact alone no longer selects the ring',()=>{const p=hand();p[4]={...p[8],x:p[8].x+.02};assert.notEqual(classifyHand(p).shape,1);});
test('V selects the ring',()=>assert.equal(classifyHand(hand([true,true,false,false],'closed')).shape,1));
test('index only is inactive',()=>assert.equal(classifyHand(hand([true,false,false,false],'closed')).shape,null));
test('thumb only selects supernova instead of fist',()=>assert.equal(classifyHand(hand([false,false,false,false],'open')).shape,3));
test('index and little finger no longer changes shape',()=>assert.equal(classifyHand(hand([true,false,false,true],'closed')).shape,null));
test('natural open palm works without requiring thumb abduction',()=>assert.equal(classifyHand(hand([true,true,true,true],'closed')).shape,2));
test('relaxed thumb is accepted while unsupported finger arrangements stay inactive',()=>{assert.equal(classifyHand(hand([true,true,true,true],'unclear')).shape,2);assert.equal(classifyHand(hand([false,true,false,false],'closed')).shape,null);});
test('classification survives scale, translation, mirroring and screen rotation',()=>{for(const p of [hand(),hand([false,false,false,false],'closed'),hand([true,true,false,false],'closed')]){const s=p.map(v=>({x:1-(v.x*.6+.1),y:v.y*.6+.1,z:v.z*.6}));const r=p.map(v=>({x:1-v.y,y:v.x,z:v.z}));assert.equal(classifyHand(s).shape,classifyHand(p).shape);assert.equal(classifyHand(r).shape,classifyHand(p).shape);}});
test('missing or invalid landmarks are ignored',()=>{assert.equal(classifyHand(null),null);assert.equal(classifyHand([]),null);const p=hand();p[8].x=NaN;assert.equal(classifyHand(p),null);});

test('short but straight little finger still counts as an open palm',()=>{const p=hand(undefined,'unclear');p[18].y=.55;p[19].y=.52;p[20].y=.49;assert.equal(classifyHand(p).shape,2);});
test('slightly curved fingers do not require maximum extension',()=>{const p=hand(undefined,'unclear');p[19].x+=.04;p[20].x+=.08;p[20].y=.35;assert.equal(classifyHand(p).shape,2);});
test('three fingers with a fully folded little finger does not become a palm',()=>assert.equal(classifyHand(hand([true,true,true,false],'closed')).shape,null));
test('screen fallback corrects camera aspect and ignores unreliable depth',()=>{const p=hand(undefined,'unclear'),screen=p.map((p,i)=>({...p,x:p.x/(16/9),z:i%2?10:-10}));assert.equal(classifyHand(screen,null,16/9).shape,2);});
test('valid world geometry supports rotated open palms',()=>{const p=hand(undefined,'unclear');for(const a of [0,.5,1.1]){const world=p.map(p=>({x:(p.x-.5)*.2*Math.cos(a),y:(p.y-.7)*.2,z:(p.x-.5)*.2*Math.sin(a)}));assert.equal(classifyHand(p,world,16/9).shape,2);}});
test('missing world landmarks do not block palm recognition',()=>assert.equal(classifyHand(hand(undefined,'unclear'),null).shape,2));
test('degenerate landmarks do not invent a fist',()=>assert.equal(classifyHand(Array.from({length:21},()=>({x:.5,y:.5,z:0}))),null));

test('natural palm reaches the three-frame switch without world-pose calibration',async()=>{const {GestureGate}=await import('../dist/motion.mjs');const gate=new GestureGate(),p=hand(undefined,'unclear');const results=[0,40,80].map(t=>gate.update(classifyHand(p,null).shape,t,1));assert.deepEqual(results,[null,null,2]);});

test('V works with a relaxed, tucked or extended thumb',()=>{for(const thumb of ['open','closed','unclear'])assert.equal(classifyHand(hand([true,true,false,false],thumb)).shape,1);});
test('V tolerates a slight bend in the extended fingers',()=>{const p=hand([true,true,false,false],'unclear');for(const tip of [8,12]){p[tip-1].x+=.03;p[tip].x+=.06;p[tip].y=.32;}assert.equal(classifyHand(p).shape,1);});
test('three extended fingers are not mistaken for V',()=>assert.notEqual(classifyHand(hand([true,true,true,false],'closed')).shape,1));
test('V switches from the cluster after three frames without a long hold',async()=>{const {GestureGate}=await import('../dist/motion.mjs');const gate=new GestureGate(),p=hand([true,true,false,false],'unclear');assert.deepEqual([0,40,80].map(t=>gate.update(classifyHand(p,null).shape,t,2)),[null,null,1]);});
