import assert from 'node:assert/strict';
import {floorOrder,stores,floorZones,defaultOrigin} from '../indoor/data.mjs';
import {knownFloor,knownHall,readSelection,lookupStores,findShop,findZone,buildSchematicRoute,qualityStats} from '../indoor/nav-model.mjs';

assert.deepEqual(floorOrder,['B3','B2','B1','1F','2F','3F']);
assert.equal(new Set(floorOrder).size,6);
for(const floor of floorOrder){
  assert.ok(floorZones[floor]?.length>0,'missing zones '+floor);
  for(const z of floorZones[floor]){
    assert.ok(z.x>=0&&z.y>=0&&z.x+z.w<=100&&z.y+z.h<=100,'off-canvas zone '+z.id);
    assert.equal(z.accuracy,'concept');
  }
}
assert.equal(knownHall('4'),true);
assert.equal(knownHall('9'),false);
assert.equal(knownFloor('4F'),false);
assert.deepEqual(readSelection(new URLSearchParams('floor=4F&hall=9')),{floor:'1F',hall:'all',search:''});
assert.equal(stores.length,14);
assert.ok(stores.every(s=>s.x===null&&s.y===null&&s.unit===null));
assert.ok(stores.every(s=>s.source==='현장 안내판 사진'));
assert.equal(lookupStores({hall:'3',floor:'3F'}).length,3);
assert.equal(lookupStores({hall:'5',floor:'3F'}).length,4);
assert.equal(lookupStores({hall:'4',floor:'1F'}).length,0);
assert.equal(lookupStores({query:'이디야',allFloors:true}).length,1);
assert.equal(lookupStores({query:'회센터',allFloors:true}).length,0); // category-only, not a verified shop
assert.ok(findShop('h5-dolgorae'));
assert.equal(findShop('unknown'),null);
assert.ok(findZone('1F','f1-seafood'));
assert.equal(findZone('B3','f1-seafood'),null);
const route=buildSchematicRoute(defaultOrigin,{hall:'3',floor:'3F',name:'다미정'});
assert.equal(route.supported,true);
assert.equal(route.distanceMeters,null);
assert.equal(route.etaMinutes,null);
assert.equal(route.indoorLocationVerified,false);
assert.ok(route.steps.some(s=>s.type==='floor'));
assert.ok(route.steps.some(s=>s.type==='hall'));
assert.ok(route.warning.includes('검증되지'));
const sameFloor=buildSchematicRoute(defaultOrigin,{hall:'5',floor:'1F',name:'회센터'});
assert.equal(sameFloor.steps.filter(s=>s.type==='floor').length,0);
assert.equal(buildSchematicRoute(defaultOrigin,{hall:'6',floor:'B1'}).supported,false);
assert.equal(qualityStats().locatedStores,0);
assert.equal(qualityStats().routeSurveyed,false);
console.log('PASS indoor nav model: 6 floors, 14 sign-listed tenants, safe route uncertainty, filters and inputs');
