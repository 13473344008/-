const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,(a.z||0)-(b.z||0));
function straight(a,b,c){const u=[a.x-b.x,a.y-b.y,(a.z||0)-(b.z||0)],v=[c.x-b.x,c.y-b.y,(c.z||0)-(b.z||0)];const denom=Math.hypot(...u)*Math.hypot(...v);return denom ? -(u[0]*v[0]+u[1]*v[1]+u[2]*v[2])/denom : 0;}
export function classifyHand(lm,world=null,aspect=1){
 if(!lm||lm.length!==21||lm.some(p=>!Number.isFinite(p.x)||!Number.isFinite(p.y)))return null;
 // Metric world coordinates avoid stretching angles with the camera aspect ratio.
 // Screen landmarks remain a fallback when orientation/world tracking is unavailable.
 const validWorld=world?.length===21&&world.every(p=>[p.x,p.y,p.z].every(Number.isFinite))&&dist(world[0],world[9])>.0001;
 lm=validWorld?world:lm.map(p=>({x:p.x*(Number.isFinite(aspect)&&aspect>0?aspect:1),y:p.y,z:0}));
 const palm=dist(lm[0],lm[9]);if(palm<.0001)return null;
 const fingers=[[5,6,8],[9,10,12],[13,14,16],[17,18,20]];
 const flex=fingers.map(([base,pip,tip])=>{
  const length=dist(lm[base],lm[pip])+dist(lm[pip],lm[tip-1])+dist(lm[tip-1],lm[tip]);
  const reach=dist(lm[base],lm[tip])/Math.max(.00001,length);
  const bend=straight(lm[base],lm[pip],lm[tip]);
  const outward=dist(lm[tip],lm[0])/Math.max(.00001,dist(lm[pip],lm[0]));
  return {open:bend>.35&&reach>.72&&outward>1.05,relaxed:bend>.1&&reach>.60&&outward>1.02,
   folded:bend<.15||reach<.55||dist(lm[tip],lm[0])<dist(lm[base],lm[0])*1.15};
 });
 const thumbDistance=dist(lm[4],lm[5])/palm;
 const thumbStraight=straight(lm[2],lm[3],lm[4]);
 const thumbOpen=thumbDistance>.65&&thumbStraight>.65;
 const thumbClosed=thumbDistance<.48;
 const folded=flex.map(f=>f.folded);
 const openPalm=flex.every(f=>f.open)||(flex.filter(f=>f.open).length>=3&&flex.every(f=>f.relaxed));
 let shape=null;
 if(folded.every(Boolean))shape=thumbOpen?3:thumbClosed?0:null;
 else if(flex[0].open&&flex[1].open&&folded[2]&&folded[3])shape=1;
 else if(openPalm)shape=2;
 return {shape};
}
