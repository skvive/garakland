import assert from 'node:assert/strict';
import {template,validateLayout,makeDraft,safeFloorRoute} from '../indoor/layout-schema.mjs';
const clone=x=>structuredClone(x);

const original=clone(template);
const originalVerdict=validateLayout(original);
assert.equal(originalVerdict.ok,true,'initial draft must parse');
assert.equal(originalVerdict.canPublish,false,'an illustrative floor is never public');
assert.equal(safeFloorRoute(original,'a','b').status,'unavailable');
assert.equal(validateLayout(null).ok,false);
assert.equal(validateLayout({}).ok,false);
const invalid=clone(original);
invalid.source.title='<img src=x onerror=alert(1)>';
assert.equal(validateLayout(invalid).ok,false,'reject markup in metadata');
const invalidCoord=clone(original);
invalidCoord.outline=[[3,5],[109,8],[10,20]];
assert.equal(validateLayout(invalidCoord).ok,false,'reject coordinates outside normalized canvas');
const invalidHuge=clone(original);
invalidHuge.shops=new Array(5001).fill(0);
assert.equal(validateLayout(invalidHuge).ok,false,'reject oversized structures');

const surveyed=clone(template);
surveyed.source={id:'test-owner-floor',title:'TEST-ONLY simulated floor plan',kind:'owner-authorized-drawing',
    status:'approved',permissionRef:'SIMULATED-NOT-REAL',reviewer:'TEST-PERSON',reviewDate:'2026-11-02'};
surveyed.shops=[{id:'test-shop',name:'TEST STORE',category:'grocery',polygon:[[42,22],[52,22],[52,32],[42,32]],verified:true}];
surveyed.nodes=[
  {id:'start',xy:[10,10],type:'entry',verified:true},
  {id:'hall',xy:[50,12],type:'passage',verified:true},
  {id:'end',xy:[80,20],type:'passage',verified:true}
];
surveyed.edges=[
  {id:'short-stairs',from:'start',to:'end',mode:'stairs',lengthMeters:12,verified:true},
  {id:'walk-a',from:'start',to:'hall',mode:'walk',lengthMeters:21,verified:true},
  {id:'walk-b',from:'hall',to:'end',mode:'walk',lengthMeters:31,verified:true}
];
const good=validateLayout(surveyed);
assert.equal(good.ok,true,good.errors.join('\n'));
assert.equal(good.canPublish,true,'synthetic fixtures can pass schema; this is NOT real authorization');
let route=safeFloorRoute(surveyed,'start','end');
assert.equal(route.status,'verified-plan');
assert.deepEqual(route.path,['start','end']);
assert.equal(route.distanceMeters,12);
route=safeFloorRoute(surveyed,'start','end',{wheelchair:true});
assert.equal(route.status,'verified-plan');
assert.deepEqual(route.path,['start','hall','end']);
assert.equal(route.distanceMeters,52);
assert.equal(safeFloorRoute(surveyed,'start','missing').status,'unavailable');

const revoked=clone(surveyed);
revoked.source.kind='signboard-photo';
assert.equal(validateLayout(revoked).canPublish,false,'signage cannot be a surveyed publication source');
assert.equal(safeFloorRoute(revoked,'start','end').status,'unavailable');
const missingRights=clone(surveyed);
missingRights.source.permissionRef='';
assert.equal(validateLayout(missingRights).ok,false);
const spoof=clone(surveyed);
spoof.edges[0].verified=false;
assert.equal(safeFloorRoute(spoof,'start','end').status,'unavailable');
const duplicate=clone(surveyed);
duplicate.nodes[1].id='start';
assert.equal(validateLayout(duplicate).ok,false);
const draft=makeDraft(surveyed);
assert.equal(draft.source.status,'draft');
assert.equal(draft.source.reviewer,'');
assert.equal(draft.shops[0].verified,false);
assert.equal(draft.edges[0].verified,false);
assert.equal(validateLayout(draft).canPublish,false);
assert.equal(validateLayout(surveyed).canPublish,true,'draft copy must not mutate source');
console.log('PASS indoor approved layout schema: source rights, safe geometry, data limits, draft export, accessible Dijkstra');
