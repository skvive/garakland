import {MARKET,BUILDINGS,ZONE_IMAGES,verifiedCoords,escapeHTML as esc} from './catalog.js';

const MARKET_CENTER={lat:MARKET.lat,lng:MARKET.lng};
const VIEW={
  satellite:{zoom:18,minZoom:15,maxZoom:21,tilt:0},
  terrain:{zoom:14,minZoom:11,maxZoom:16,tilt:0},
  roadmap:{zoom:16,minZoom:13,maxZoom:20,tilt:0}
};

let googlePromise=null;
function loadGoogle(key){
  if(window.google?.maps?.importLibrary) return Promise.resolve(window.google);
  if(googlePromise) return googlePromise;
  googlePromise=new Promise((resolve,reject)=>{
    let done=false;
    const callback='__garaklandMapsReady';
    const timer=setTimeout(()=>finish(new Error('Google Maps 로딩 시간이 초과되었습니다. API 키/도메인 제한을 확인하세요.')),20000);
    function finish(err){
      if(done) return;
      done=true;
      clearTimeout(timer);
      delete window[callback];
      if(err){googlePromise=null;reject(err);}
      else resolve(window.google);
    }
    window[callback]=()=>finish();
    const s=document.createElement('script');
    s.src=`https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}&v=beta&loading=async&callback=${callback}&language=ko&region=KR`;
    s.async=true;
    s.onerror=()=>finish(new Error('Google Maps 스크립트를 불러오지 못했습니다.'));
    document.head.append(s);
  });
  return googlePromise;
}

export class MapEngine{
  constructor(container,{onShopClick,onBuildingClick,onToast,onCoordinatePick,onFloorSelect}={}){
    this.el=container;
    this.onShopClick=onShopClick||(()=>{});
    this.onBuildingClick=onBuildingClick||(()=>{});
    this.onToast=onToast||(()=>{});
    this.onCoordinatePick=onCoordinatePick||(()=>{});
    this.onFloorSelect=onFloorSelect||(()=>{});
    this.mode='concept';
    this.google=null;
    this.map=null;
    this.mapsLib=null;
    this.type=null;
    this.shops=[];
    this.models=[];
    this.markers=[];
    this.modelElements=[];
    this.lastSelection=null;
    this.lastCenter=MARKET_CENTER;
    this.picking=false;
    this.user=null;
    this.clickListener=null;
    this._ro=null;
    this.watchSize();
    this.renderConcept();
  }

  hostBox(){
    const host=this.el.parentElement||this.el;
    const r=host.getBoundingClientRect();
    return {
      w:Math.max(Math.round(r.width||host.clientWidth||this.el.clientWidth||320),1),
      h:Math.max(Math.round(r.height||host.clientHeight||this.el.clientHeight||320),1)
    };
  }

  fitMap(){
    if(this.type!=='2d' && this.type!=='3d') return;
    const {w,h}=this.hostBox();
    if(this._lastFit && this._lastFit.w===w && this._lastFit.h===h && this._lastFit.type===this.type) return;
    this._lastFit={w,h,type:this.type};
    this.el.style.width='100%';
    this.el.style.height='100%';
    const canvas=this.el.querySelector('.google-map-canvas, gmp-map-3d');
    if(canvas){
      canvas.style.display='block';
      canvas.style.width='100%';
      canvas.style.height='100%';
      canvas.style.minHeight='0';
      canvas.style.maxHeight='none';
    }
    if(this.type==='2d' && this.map && this.google?.maps?.event){
      this.google.maps.event.trigger(this.map,'resize');
      const center=this.currentCenter();
      if(this.map.setCenter) this.map.setCenter(center);
    }
  }

  watchSize(){
    if(this._ro || typeof ResizeObserver==='undefined') return;
    const host=this.el.parentElement||this.el;
    this._ro=new ResizeObserver(()=>this.fitMap());
    this._ro.observe(host);
  }

  waitFrames(n=2){
    return new Promise(resolve=>{
      const step=()=>{n-=1; if(n<=0) resolve(); else requestAnimationFrame(step);};
      requestAnimationFrame(step);
    });
  }

  renderConcept(){
    if(this.markers?.length) this.clearMarkers();
    this.destroyGoogleMap();
    this.type='concept';
    this.el.innerHTML=`<div class="concept-map concept-map-3d"><img class="concept-3d-art" src="${ZONE_IMAGES.campus}" alt="가락시장 실사 기반 3D 시설 모식도"><div class="concept-bottom-tag">실사·3D 건물 모식도 — Google 실측 지도와 공식 도면을 대체하지 않습니다</div></div>`;
    const host=this.el.querySelector('.concept-map');
    for(const b of BUILDINGS){
      const el=document.createElement('button');
      el.type='button';
      el.className='concept-building concept-building-3d'+(['sales','seafood','produce','theme1'].includes(b.id)?' is-primary':'');
      el.style.setProperty('--x',b.illustrative[0]+'%');
      el.style.setProperty('--y',b.illustrative[1]+'%');
      el.style.setProperty('--b',b.accent);
      el.innerHTML=`<i></i><span class="concept-name">${b.name.replace('가락몰 ','')}</span>`;
      el.title=b.name+' / 실사 기반 3D 시설';
      el.addEventListener('click',()=>this.onBuildingClick(b.id));
      host.append(el);
    }
  }

  async connect(key){
    if(!key) throw new Error('Google Maps API 키를 입력해 주세요.');
    this.google=await loadGoogle(key);
    this.mapsLib=await this.google.maps.importLibrary('maps');
    return true;
  }

  currentCenter(){
    if(this.type==='2d' && this.map?.getCenter){
      const c=this.map.getCenter();
      if(c) return {lat:c.lat(),lng:c.lng()};
    }
    if(this.type==='3d' && this.map?.center){
      const c=this.map.center;
      if(c && Number.isFinite(Number(c.lat)) && Number.isFinite(Number(c.lng))){
        return {lat:Number(c.lat),lng:Number(c.lng)};
      }
    }
    return this.lastCenter||MARKET_CENTER;
  }

  rememberCenter(center){
    if(center && Number.isFinite(center.lat) && Number.isFinite(center.lng)) this.lastCenter=center;
  }

  mapTypeIdFor(mode){
    const {MapTypeId}=this.mapsLib||{};
    if(mode==='terrain') return MapTypeId?.TERRAIN||'terrain';
    if(mode==='satellite') return MapTypeId?.SATELLITE||'satellite';
    return MapTypeId?.ROADMAP||'roadmap';
  }

  viewFor(mode){
    return VIEW[mode]||VIEW.satellite;
  }

  destroyGoogleMap(){
    this.clearMarkers();
    if(this.clickListener && typeof this.clickListener.remove==='function') this.clickListener.remove();
    this.clickListener=null;
    this.map=null;
    this.type=null;
    this._lastFit=null;
    this.el.replaceChildren();
  }

  async setMode(mode,opts={}){
    this.mode=mode;
    if(mode==='concept'){
      this.renderConcept();
      return;
    }
    if(mode==='floor'){
      this.renderFloorMap(opts.plan,opts.meta||{});
      return;
    }
    if(!this.google) throw new Error('Google 지도 연동을 먼저 설정하세요.');
    if(!this.mapsLib) this.mapsLib=await this.google.maps.importLibrary('maps');
    if(mode==='3d') await this.make3D();
    else await this.make2D(mode);
    this.drawMarkers();
  }

  renderFloorMap(plan,meta={}){
    this.destroyGoogleMap();
    this.type='floor';
    const title=meta.title||'층별 안내도';
    const caption=meta.caption||'';
    const floors=Array.isArray(meta.floors)&&meta.floors.length?meta.floors:['all'];
    const current=meta.floor||'all';
    const src=plan?.imageUrl||'';
    const w=plan?.width||1200;
    const h=plan?.height||780;
    const pills=floors.map(f=>`<button type="button" class="floor-map-pill${f===current?' active':''}" data-map-floor="${esc(f)}">${esc(f==='all'?'전체':f)}</button>`).join('');
    const stage=src
      ?`<img src="${esc(src)}" alt="${esc(title)}" width="${w}" height="${h}">`
      :`<div class="indoor-placeholder"><span>▦</span><strong>층별 도면 등록 전</strong><small>이 구역·층의 공식 안내 모식도가 아직 없습니다.</small></div>`;
    this.el.innerHTML=`<div class="floor-map-viewer">
      <div class="floor-map-head"><strong>${esc(title)}</strong><span>${esc(caption)}</span></div>
      <div class="floor-map-pills" role="tablist">${pills}</div>
      <div class="floor-map-stage">${stage}</div>
    </div>`;
    this.el.querySelectorAll('[data-map-floor]').forEach(btn=>{
      btn.addEventListener('click',()=>this.onFloorSelect(btn.dataset.mapFloor));
    });
  }

  async make2D(mode){
    const {Map}=this.mapsLib;
    const view=this.viewFor(mode);
    const typeId=this.mapTypeIdFor(mode);
    const center=this.currentCenter();
    this.rememberCenter(center);

    if(this.type==='2d' && this.map && typeof this.map.setMapTypeId==='function'){
      this.map.setOptions({
        mapTypeId:typeId,
        tilt:0,
        heading:0,
        zoom:view.zoom,
        minZoom:view.minZoom,
        maxZoom:view.maxZoom
      });
      this.map.setCenter(center);
      await this.waitFrames(2);
      this.fitMap();
      return;
    }

    this.destroyGoogleMap();
    const mapEl=document.createElement('div');
    mapEl.className='google-map-canvas';
    this.el.append(mapEl);
    this.type='2d';
    this.fitMap();
    this.map=new Map(mapEl,{
      center,
      zoom:view.zoom,
      mapTypeId:typeId,
      tilt:0,
      heading:0,
      minZoom:view.minZoom,
      maxZoom:view.maxZoom,
      fullscreenControl:false,
      streetViewControl:false,
      mapTypeControl:false,
      rotateControl:false,
      clickableIcons:true,
      gestureHandling:'greedy'
    });
    this.clickListener=this.map.addListener('click',e=>{
      if(!this.picking) return;
      this.onCoordinatePick({lat:e.latLng.lat(),lng:e.latLng.lng()});
      this.picking=false;
      this.onToast('지도 클릭 좌표를 입력했습니다. 정확성은 현장 검증 후 확정하세요.');
    });
    this.map.addListener('center_changed',()=>{
      const c=this.map.getCenter();
      if(c) this.rememberCenter({lat:c.lat(),lng:c.lng()});
    });
    const kick=()=>{
      if(this.type!=='2d'||!this.map) return;
      this._lastFit=null;
      this.fitMap();
      if(typeof this.map.setZoom==='function') this.map.setZoom(this.map.getZoom());
    };
    await this.waitFrames(2);
    kick();
    this.google.maps.event.addListenerOnce(this.map,'idle',kick);
    setTimeout(kick,400);
  }

  wait3DReady(el){
    return new Promise(resolve=>{
      let done=false;
      const finish=()=>{
        if(done) return;
        done=true;
        resolve();
      };
      const timer=setTimeout(finish,2500);
      el.addEventListener('gmp-steadystate',()=>{clearTimeout(timer);finish();},{once:true});
      el.addEventListener('gmp-error',()=>{clearTimeout(timer);finish();},{once:true});
    });
  }

  apply3DCamera(center){
    if(!this.map) return;
    const cam={center:{lat:center.lat,lng:center.lng,altitude:0},range:720,tilt:67.5,heading:28};
    this.map.center=cam.center;
    this.map.range=cam.range;
    this.map.tilt=cam.tilt;
    this.map.heading=cam.heading;
    if(typeof this.map.flyCameraTo==='function'){
      try{
        this.map.flyCameraTo({endCamera:cam,durationMillis:700});
      }catch{}
    }
  }

  async make3D(){
    const center=this.currentCenter();
    this.rememberCenter(center);
    this.destroyGoogleMap();
    this.type='3d';
    const {Map3DElement,MapMode}=await this.google.maps.importLibrary('maps3d');
    this.map=new Map3DElement({
      center:{lat:center.lat,lng:center.lng,altitude:0},
      range:720,
      tilt:67.5,
      heading:28,
      mode:MapMode?.HYBRID||'HYBRID'
    });
    this.map.className='google-map-canvas';
    this.el.append(this.map);
    await this.waitFrames(2);
    this.fitMap();
    this.apply3DCamera(center);
    await this.wait3DReady(this.map);
    this.fitMap();
    this.apply3DCamera(center);
  }

  clearMarkers(){
    for(const marker of this.markers){
      if(typeof marker.setMap==='function') marker.setMap(null);
      else if(typeof marker.remove==='function') marker.remove();
    }
    this.markers=[];
    for(const model of this.modelElements){
      if(typeof model.remove==='function') model.remove();
    }
    this.modelElements=[];
    if(this.userMarker && typeof this.userMarker.setMap==='function') this.userMarker.setMap(null);
    this.userMarker=null;
  }

  drawMarkers(){
    if(!this.map||!this.google) return;
    this.clearMarkers();
    const good=this.shops.filter(verifiedCoords);
    if(this.type==='2d'){
      const g=this.google;
      for(const s of good){
        const m=new g.maps.Marker({
          map:this.map,
          position:{lat:+s.latitude,lng:+s.longitude},
          title:s.name,
          label:{text:s.featured?'★':'●',color:'#172c2a',fontSize:'11px'},
          icon:{path:g.maps.SymbolPath.CIRCLE,scale:12,fillColor:'#f4b66c',fillOpacity:1,strokeColor:'#ffffff',strokeWeight:2}
        });
        m.addListener('click',()=>this.onShopClick(s.id));
        this.markers.push(m);
      }
      if(!good.length){
        const m=new g.maps.Marker({
          map:this.map,
          position:MARKET_CENTER,
          title:'가락시장 기준점(근사)',
          label:'?'
        });
        m.addListener('click',()=>this.onToast('이 표시는 정확한 매장 좌표가 아닌 가락시장 안내용 근사 기준점입니다.'));
        this.markers.push(m);
      }
    }else if(this.type==='3d'){
      this.render3DMarkers(good).catch(err=>this.onToast('3D 매장 마커 오류: '+err.message));
    }
  }

  async render3DMarkers(good){
    const {Marker3DInteractiveElement}=await this.google.maps.importLibrary('maps3d');
    for(const s of good.slice(0,3000)){
      if(this.type!=='3d') return;
      const m=new Marker3DInteractiveElement({
        position:{lat:+s.latitude,lng:+s.longitude,altitude:9},
        label:s.name,
        sizePreserved:true,
        extruded:true
      });
      m.addEventListener('gmp-click',()=>this.onShopClick(s.id));
      this.map.append(m);
      this.markers.push(m);
    }
    await this.render3DModels();
  }

  async render3DModels(){
    if(this.type!=='3d'||!this.map||!this.models.length) return;
    const {Model3DElement}=await this.google.maps.importLibrary('maps3d');
    for(const item of this.models){
      if(!item.approved||!/^\.\/assets\/models3d\/[a-zA-Z0-9_-]+\.glb$/.test(item.src||'')) continue;
      const lat=Number(item.latitude),lng=Number(item.longitude),scale=Number(item.scale||1);
      if(!Number.isFinite(lat)||!Number.isFinite(lng)||!Number.isFinite(scale)||scale<=0) continue;
      const model=new Model3DElement({
        src:new URL(item.src,location.href).href,
        position:{lat,lng,altitude:Number(item.altitude||0)},
        scale,
        altitudeMode:'RELATIVE_TO_GROUND'
      });
      this.map.append(model);
      this.modelElements.push(model);
    }
  }

  setModels(models){
    this.models=Array.isArray(models)?models:[];
    if(this.type==='3d') this.render3DModels().catch(err=>this.onToast('3D 모델 표시 오류: '+err.message));
  }

  setShops(items){
    this.shops=items;
    this.drawMarkers();
  }

  focus(shop){
    this.lastSelection=shop;
    if(!verifiedCoords(shop)){
      this.onToast('정확한 실내 매장 좌표가 미등록입니다. 건물·층·호실 및 Google 검색을 참고하세요.');
      return;
    }
    const pos={lat:+shop.latitude,lng:+shop.longitude};
    this.rememberCenter(pos);
    if(this.type==='2d'){
      this.map.panTo(pos);
      this.map.setZoom(this.mode==='terrain'?15:19);
    }else if(this.type==='3d'){
      this.map.center={...pos,altitude:0};
      this.map.range=360;
      this.map.tilt=60;
    }
  }

  focusBuilding(building){
    if(!building||!Number.isFinite(building.lat)||!Number.isFinite(building.lng)) return;
    const pos={lat:building.lat,lng:building.lng};
    this.rememberCenter(pos);
    if(this.type==='2d'&&this.map){
      this.map.panTo(pos);
      this.map.setZoom(this.mode==='terrain'?14:18);
    }else if(this.type==='3d'&&this.map){
      this.map.center={...pos,altitude:0};
      this.map.range=900;
      this.map.tilt=62;
      this.map.heading=-18;
    }
  }

  locate(user){
    this.user=user;
    this.rememberCenter(user);
    if(this.type==='2d'&&this.map){
      this.map.panTo(user);
      this.map.setZoom(this.mode==='terrain'?14:17);
      if(this.userMarker) this.userMarker.setMap(null);
      this.userMarker=new this.google.maps.Marker({
        map:this.map,
        position:user,
        title:'내 위치',
        icon:{path:this.google.maps.SymbolPath.CIRCLE,scale:9,fillColor:'#397cea',fillOpacity:1,strokeColor:'#fff',strokeWeight:3}
      });
    }else if(this.type==='3d'&&this.map){
      this.map.center={...user,altitude:0};
      this.map.range=550;
    }
  }

  startPick(){
    if(this.type!=='2d') throw new Error('좌표 지정은 Google 2D 지도 모드에서만 가능합니다.');
    this.picking=true;
    this.onToast('지도에서 실제 매장 출입구 위치를 클릭하세요. 위치 검증 상태는 별도 지정해야 합니다.');
  }

  reset(){
    this.rememberCenter(MARKET_CENTER);
    if(this.type==='2d'&&this.map){
      const view=this.viewFor(this.mode);
      this.map.panTo(MARKET_CENTER);
      this.map.setZoom(view.zoom);
      this.map.setTilt(0);
      this.map.setHeading(0);
    }else if(this.type==='3d'&&this.map){
      this.apply3DCamera(MARKET_CENTER);
    }
  }
}
