import assert from 'node:assert/strict';
import {buildDirections,hasVerifiedGps,MARKET_ADDRESS} from '../game/navigation.mjs';
const real={id:'test-store',name:'위치 확인 매장',isDemo:false,latitude:37.494321,longitude:127.112345,coordinateStatus:'verified',building:'sales',floor:'1F',room:'A-103'};
assert.equal(hasVerifiedGps(real),true);
const route=buildDirections(real);const u=new URL(route.url);
assert.equal(u.protocol,'https:');assert.equal(u.hostname,'www.google.com');assert.equal(u.pathname,'/maps/dir/');
assert.equal(u.searchParams.get('api'),'1');assert.equal(u.searchParams.get('destination'),'37.494321,127.112345');
assert.equal(u.searchParams.get('travelmode'),'walking');assert.equal(u.searchParams.get('dir_action'),'navigate');
assert.equal(route.mode,'store');assert.equal(route.verified,true);assert.match(route.locationLabel,/A-103/);
assert.equal(new URL(buildDirections(real,'driving').url).searchParams.get('travelmode'),'driving');
assert.equal(new URL(buildDirections(real,'malicious').url).searchParams.get('travelmode'),'walking');
const unknown={...real,coordinateStatus:'unverified'};const general=buildDirections(unknown);
assert.equal(general.mode,'market');assert.equal(new URL(general.url).searchParams.get('destination'),MARKET_ADDRESS);
assert.match(general.notice,/확인/);
const imaginary={...real,isDemo:true};assert.equal(buildDirections(imaginary).mode,'market');assert.match(buildDirections(imaginary).notice,/가상/);
for(const bad of [{...real,latitude:null},{...real,longitude:NaN},{...real,latitude:0,longitude:0},{...real,latitude:'NaN'},null,undefined]){
 assert.equal(buildDirections(bad).mode,'market');
}
console.log('Google Maps route unit checks PASSED (verified / unverified / demo / missing / invalid / driving / URL encoding)');
