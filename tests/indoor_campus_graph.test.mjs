import assert from 'node:assert/strict';
import {validateCampus,routeCampus,makeCampusDraft,sampleCampus} from '../indoor/campus-graph.mjs';
const source=n=>({id:'test-'+n,title:'TEST ONLY synthetic '+n,kind:'on-site-survey',
 status:'approved',permissionRef:'TEST-NOT-REAL',reviewer:'QA-SIMULATED',reviewDate:'2026-11-02'});
const layout=(hall,floor,nodes,edges)=>({
 schemaVersion:1,hall,floor,source:source(hall+'-'+floor),
 outline:[[8,10],[88,11],[90,75],[10,73]],
 entrances:[],
 shops:[{id:'shop-'+hall+'-'+floor,name:'TEST SHOP',category:'test',
   polygon:[[35,32],[45,32],[45,42],[35,42]],verified:true}],
 nodes:nodes.map((n,i)=>({id:n[0],xy:[10+i*12,22],type:n[1],verified:true})),
 edges:edges.map((e,i)=>({id:'edge-'+i,from:e[0],to:e[1],mode:e[2],lengthMeters:e[3],verified:true}))
});
const floorA=layout('5','1F',[['gate','entry'],['lift','elevator'],['steps','stairs']],
  [['gate','lift','walk',10],['gate','steps','walk',3]]);
const floorB=layout('5','2F',[['lift','elevator'],['steps','stairs'],['hallway','passage']],
  [['lift','hallway','walk',10],['steps','hallway','walk',4]]);
const floorC=layout('3','2F',[['hallway','passage'],['shop','passage']],
  [['hallway','shop','walk',8]]);
const bundle={
 schemaVersion:1,name:'Synthetic campus TEST ONLY',
 floors:[floorA,floorB,floorC],publication:'disabled',
 transfers:[
  {id:'lift-5',from:{hall:'5',floor:'1F',node:'lift'},to:{hall:'5',floor:'2F',node:'lift'},
   mode:'elevator',lengthMeters:7,bidirectional:true,accessible:true,
   verified:true,evidenceId:'test-elevator',sourceKind:'survey'},
  {id:'stairs-5',from:{hall:'5',floor:'1F',node:'steps'},to:{hall:'5',floor:'2F',node:'steps'},
   mode:'stairs',lengthMeters:2,bidirectional:true,accessible:false,
   verified:true,evidenceId:'test-stair',sourceKind:'survey'},
  {id:'hall-3-5',from:{hall:'5',floor:'2F',node:'hallway'},to:{hall:'3',floor:'2F',node:'hallway'},
   mode:'walk',lengthMeters:30,bidirectional:true,accessible:true,
   verified:true,evidenceId:'test-corridor',sourceKind:'owner-approved-plan'}
 ]
};
const a={hall:'5',floor:'1F',node:'gate'};
const b={hall:'3',floor:'2F',node:'shop'};
const deep=x=>structuredClone(x);
assert.equal(validateCampus(sampleCampus).routeReady,false);
let v=validateCampus(bundle);
assert.equal(v.ok,true,v.errors.join('\n'));
assert.equal(v.routeReady,true,v.warnings.join('\n'));
assert.equal(v.stats.floors,3);
assert.equal(v.stats.transfers,3);
let walk=routeCampus(bundle,a,b);
assert.equal(walk.status,'verified-plan');
assert.equal(walk.distanceMeters,47);
assert.ok(walk.path.some(p=>p.type==='stairs'));
let access=routeCampus(bundle,a,b,{wheelchair:true});
assert.equal(access.status,'verified-plan');
assert.equal(access.distanceMeters,65);
assert.ok(access.path.some(p=>p.type==='elevator'));
assert.ok(!access.path.some(p=>p.type==='stairs'));
let reverse=routeCampus(bundle,b,a,{wheelchair:true});
assert.equal(reverse.status,'verified-plan');
assert.equal(reverse.distanceMeters,65);
let oneWay=deep(bundle);
oneWay.transfers[2].bidirectional=false;
assert.equal(routeCampus(oneWay,b,a).status,'unavailable');
let wrongType=deep(bundle);
wrongType.transfers[0].mode='stairs';
assert.equal(validateCampus(wrongType).ok,false);
let wrongHall=deep(bundle);
wrongHall.transfers[0].to.hall='3';
assert.equal(validateCampus(wrongHall).ok,false);
let invalidProof=deep(bundle);
invalidProof.transfers[0].evidenceId='';
assert.equal(validateCampus(invalidProof).routeReady,false);
assert.equal(routeCampus(invalidProof,a,b).status,'unavailable');
let revokedFloor=deep(bundle);
revokedFloor.floors[2].source.permissionRef='';
assert.equal(validateCampus(revokedFloor).routeReady,false);
let duplicated=deep(bundle);
duplicated.floors.push(deep(floorA));
assert.equal(validateCampus(duplicated).ok,false);
const draft=makeCampusDraft(bundle);
assert.equal(draft.publication,'disabled');
assert.equal(draft.floors[0].source.status,'draft');
assert.equal(draft.floors[0].edges[0].verified,false);
assert.equal(draft.transfers[0].verified,false);
assert.equal(routeCampus(draft,a,b).status,'unavailable');
assert.equal(validateCampus(bundle).routeReady,true,'export may not mutate fixture');
console.log('PASS synthetic cross-floor routing: 3-floor graph, hall transfer, elevator vs stairs, proof gates, safe draft export');
