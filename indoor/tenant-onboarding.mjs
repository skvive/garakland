/**
 * Garak Mall tenant onboarding, PHASE 4.
 * Client-side only. Signboard names are NOT confirmed current tenants.
 * Every row and imported placement is downgraded to an unverified draft.
 */
import {stores, categories} from './data.mjs';
import {template,validateLayout,makeDraft} from './layout-schema.mjs';

export const MAX_BYTES=1024*1024, MAX_ROWS=5000;
export const columns=['shop_id','name','hall','floor','room','category','source_ref'];
const floors=new Set(['B3','B2','B1','1F','2F','3F']);
const halls=new Set(['3','4','5']);
const idRule=/^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/;
const validText=s=>typeof s==='string'&&s.length<=140&&!/[<>\x00-\x1f]/.test(s);
export const normalizeName=s=>String(s??'').normalize('NFKC').toLocaleLowerCase('ko').replace(/[\s\-_·.,()[\]]/g,'');
const safeValue=s=>String(s??'').trim().normalize('NFC');
const normalizedId=(s,i)=>idRule.test(s)?s:'candidate-'+String(i+1).padStart(4,'0');
export function parseCsv(source){
 if(typeof source!=='string')throw Error('CSV 텍스트가 필요합니다.');
 if(new TextEncoder().encode(source).length>MAX_BYTES)throw Error('CSV 파일은 1MB 이하만 가능합니다.');
 const csv=source.replace(/^\uFEFF/,'');
 const rows=[],row=[];let value='',quoted=false,closed=false;
 for(let i=0;i<csv.length;i++){
   const c=csv[i];
   if(quoted){
     if(c==='"'&&csv[i+1]==='"'){value+='"';i++;}
     else if(c==='"'){quoted=false;closed=true;}
     else value+=c;
   }else{
     if(c==='"'){
       if(value.trim()||closed)throw Error('CSV 따옴표 형식이 잘못되었습니다.');
       quoted=true;
     }else if(c===','){
       row.push(value.trim());value='';closed=false;
     }else if(c==='\r'||c==='\n'){
       if(c==='\r'&&csv[i+1]==='\n')i++;
       row.push(value.trim());value='';closed=false;
       if(row.some(v=>v!==''))rows.push(row.slice());
       row.length=0;
     }else if(closed){
       if(c===' '||c==='\t')continue;
       throw Error('닫는 따옴표 뒤에는 구분자만 올 수 있습니다.');
     }else value+=c;
   }
 }
 if(quoted)throw Error('닫히지 않은 CSV 따옴표가 있습니다.');
 row.push(value.trim());
 if(row.some(v=>v!==''))rows.push(row.slice());
 if(rows.length<1)throw Error('CSV 헤더가 없습니다.');
 if(rows.length>MAX_ROWS+1)throw Error('한 번에 5000개 행까지만 처리할 수 있습니다.');
 const header=rows.shift().map(s=>s.toLowerCase());
 if(new Set(header).size!==header.length)throw Error('CSV 헤더 이름이 중복되었습니다.');
 for(const field of columns)if(!header.includes(field))throw Error('필수 헤더 누락: '+field);
 const records=rows.map((values,i)=>{
   if(values.length!==header.length)throw Error((i+2)+'행 열 개수가 헤더와 다릅니다.');
   const obj={};header.forEach((h,j)=>obj[h]=safeValue(values[j]));
   return obj;
 });
 return records;
}
export function csvExport(records){
 const quote=v=>{
   let s=String(v??'');
   // Spreadsheet formula-injection guard, even when exported as CSV.
   if(/^[\s]*[=+\-@\t\r]/.test(s))s="'"+s;
   return '"'+s.replace(/"/g,'""')+'"';
 };
 return '\uFEFF'+columns.map(quote).join(',')+'\r\n'+records.map(r=>columns.map(c=>quote(r[c])).join(',')).join('\r\n')+'\r\n';
}
export function seedFromSignboard(){
 return stores.map(s=>({
  shop_id:s.id,name:s.name,hall:s.hall,floor:s.floor,room:'',
  category:s.category,source_ref:'photo-signboard-20261102',
  coordinate_status:'unverified',presence_status:'signboard_only'
 }));
}
export function validateCandidates(raw){
 const errors=[],warnings=[],rows=[],seenIds=new Set(),seenName=new Set(),seenRoom=new Map();
 if(!Array.isArray(raw))return {ok:false,errors:['명부 배열이 필요합니다.'],warnings,rows:[],duplicates:[]};
 if(raw.length>MAX_ROWS)return {ok:false,errors:['5000행을 초과했습니다.'],warnings,rows:[],duplicates:[]};
 const duplicates=[];
 raw.forEach((item,i)=>{
   const n=i+1,issues=[];
   if(!item||typeof item!=='object'){errors.push(n+'행 데이터가 잘못되었습니다.');return;}
   const normalized={
     shop_id:normalizedId(safeValue(item.shop_id),i),
     name:safeValue(item.name),hall:safeValue(item.hall),
     floor:safeValue(item.floor).toUpperCase(),room:safeValue(item.room),
     category:safeValue(item.category),source_ref:safeValue(item.source_ref),
     coordinate_status:'unverified',presence_status:'unconfirmed',
     row_number:n
   };
   if(!item.shop_id||!idRule.test(safeValue(item.shop_id)))issues.push('shop_id 누락/형식 오류');
   if(!normalized.name||!validText(normalized.name))issues.push('매장 이름 누락/잘못된 문자');
   if(!halls.has(normalized.hall))issues.push('관 번호는 3, 4, 5 중 하나');
   if(!floors.has(normalized.floor))issues.push('층 번호 B3~3F 형식 오류');
   if(normalized.room&&!validText(normalized.room))issues.push('호실에 잘못된 문자');
   if(!normalized.category||!validText(normalized.category))issues.push('업종 누락/잘못된 문자');
   if(!normalized.source_ref||!validText(normalized.source_ref))issues.push('명부 출처가 없습니다.');
   if(seenIds.has(normalized.shop_id))issues.push('shop_id 중복');
   seenIds.add(normalized.shop_id);
   if(normalized.name&&halls.has(normalized.hall)&&floors.has(normalized.floor)){
     const key=normalized.hall+':'+normalized.floor+':'+normalizeName(normalized.name);
     if(seenName.has(key)){duplicates.push(n+'행: 이름·관·층 중복 ('+normalized.name+')');}
     seenName.add(key);
   }
   if(normalized.room&&halls.has(normalized.hall)&&floors.has(normalized.floor)){
     const key=normalized.hall+':'+normalized.floor+':'+normalizeName(normalized.room);
     if(seenRoom.has(key))duplicates.push(n+'행: 동일 관·층 호실 중복 '+normalized.room);
     else seenRoom.set(key,n);
   }else warnings.push(n+'행 '+(normalized.name||'이름 없음')+': 호실 미확인');
   if(issues.length)errors.push(n+'행 '+issues.join(' / '));
   rows.push(normalized);
 });
 const baseline=new Map(seedFromSignboard().map(s=>[
   s.hall+':'+s.floor+':'+normalizeName(s.name),s
 ]));
 const matched=rows.map(r=>{
   const key=r.hall+':'+r.floor+':'+normalizeName(r.name);
   const signs=baseline.get(key);
   return {...r,signboard_match:!!signs,
    presence_status:signs?'photo-name-only':'unconfirmed',
    coordinate_status:'unverified'};
 });
 const valid=!errors.length&&!duplicates.length;
 if(!valid)warnings.push('중복 또는 형식 오류 해결 전 도면에 일괄 적용할 수 없습니다.');
 return {ok:valid,errors,warnings,duplicates,rows:matched,
   stats:{count:rows.length,signboardMatches:matched.filter(r=>r.signboard_match).length,
     noRoom:rows.filter(r=>!r.room).length}};
}
export function placeCandidateDraft(layout,candidate,xy,{width=5,height=5}={}){
 const verdict=validateLayout(layout);
 if(!verdict.ok)throw Error('기존 층별 도면의 형식을 먼저 수정하세요.');
 if(candidate.hall!==layout.hall||candidate.floor!==layout.floor)throw Error('관·층이 다른 매장입니다.');
 if(!candidate.shop_id||!idRule.test(candidate.shop_id))throw Error('매장 식별자 오류');
 if(!candidate.name||!validText(candidate.name))throw Error('이름 형식 오류');
 if(!Array.isArray(xy)||xy.length!==2||xy.some(v=>!Number.isFinite(v)||v<0||v>100))throw Error('좌표 범위 오류');
 if(!Number.isFinite(width)||!Number.isFinite(height)||width<=0||height<=0||width>30||height>30)throw Error('구획 크기 오류');
 const draft=makeDraft(layout);
 const id='tenant-'+candidate.shop_id;
 if(draft.shops.some(s=>s.id===id))throw Error('이미 위치를 지정한 매장입니다.');
 const [cx,cy]=xy;
 const xmin=Math.max(0,cx-width/2),xmax=Math.min(100,cx+width/2);
 const ymin=Math.max(0,cy-height/2),ymax=Math.min(100,cy+height/2);
 const polygon=[[xmin,ymin],[xmax,ymin],[xmax,ymax],[xmin,ymax]];
 const room=candidate.room?candidate.room:'';
 draft.shops.push({id,name:candidate.name,category:candidate.category,
   room,registryId:candidate.shop_id,sourceRef:candidate.source_ref,
   polygon,verified:false,coordinateStatus:'unverified'});
 return draft;
}
export function prepareRegistryDraft(validation){
 if(!validation.ok)throw Error('명부 오류 또는 중복을 먼저 해결하세요.');
 return {schemaVersion:1,kind:'garak-tenant-review-draft',publication:'disabled',
  reviewer:'',approval:null,rows:validation.rows.map(r=>({
   shop_id:r.shop_id,name:r.name,hall:r.hall,floor:r.floor,
   room:r.room,category:r.category,source_ref:r.source_ref,
   presence_status:r.presence_status,coordinate_status:'unverified',
   verified:false
  }))};
}
