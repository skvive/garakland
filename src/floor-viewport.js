/* GARAKLAND – interactive floor-plan viewport.
 * Presentation only. Never assigns a position to an unverified store.
 */
export const clampZoom = value => Math.max(1,Math.min(4,Number.isFinite(value)?value:1));
export function clampOffset(value,zoom,extent){
  const max=Math.max(0,(clampZoom(zoom)-1)*Math.max(0,extent)/2);
  return Math.min(max,Math.max(-max,Number.isFinite(value)?value:0));
}
export class FloorViewport {
  constructor(root){
    this.root=root;
    this.surface=root.querySelector('.floor-map-viewport');
    this.image=this.surface?.querySelector('img');
    this.status=root.querySelector('[data-floor-zoom-status]');
    this.zoomIn=root.querySelector('[data-floor-zoom="in"]');
    this.zoomOut=root.querySelector('[data-floor-zoom="out"]');
    this.zoomReset=root.querySelector('[data-floor-zoom="reset"]');
    this.scale=1;
    this.x=0;this.y=0;
    this.pointers=new Map();
    this.lastPinch=null;
    if(!this.surface||!this.image)return;
    this.zoomIn?.addEventListener('click',()=>this.setZoom(this.scale+.35));
    this.zoomOut?.addEventListener('click',()=>this.setZoom(this.scale-.35));
    this.zoomReset?.addEventListener('click',()=>this.reset());
    this.surface.addEventListener('pointerdown',event=>this.pointerDown(event));
    this.surface.addEventListener('pointermove',event=>this.pointerMove(event));
    for(const type of ['pointerup','pointercancel','lostpointercapture']){
      this.surface.addEventListener(type,event=>this.pointerUp(event));
    }
    this.surface.addEventListener('dblclick',event=>{
      event.preventDefault();this.setZoom(this.scale+.5,event.clientX,event.clientY);
    });
    this.surface.addEventListener('wheel',event=>{
      // Intentional map zoom only while the pointer is over the plan.
      event.preventDefault();this.setZoom(this.scale*(event.deltaY>0?.9:1.1),event.clientX,event.clientY);
    },{passive:false});
    this.surface.addEventListener('keydown',event=>{
      if(['+','=','-','_','0','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(event.key)){
        event.preventDefault();
        if(event.key==='+'||event.key==='=')this.setZoom(this.scale+.35);
        else if(event.key==='-'||event.key==='_')this.setZoom(this.scale-.35);
        else if(event.key==='0')this.reset();
        else{
          if(this.scale<=1)return;
          const d=event.shiftKey?70:35;
          this.pan(event.key==='ArrowLeft'?d:event.key==='ArrowRight'?-d:0,
                   event.key==='ArrowUp'?d:event.key==='ArrowDown'?-d:0);
        }
      }
    });
    this.render();
  }
  reset(){this.scale=1;this.x=0;this.y=0;this.render();}
  setZoom(target,clientX,clientY){
    const zoom=clampZoom(target);
    if(zoom===this.scale)return;
    const rect=this.surface.getBoundingClientRect();
    const fx=Number.isFinite(clientX)?clientX-rect.left-rect.width/2:0;
    const fy=Number.isFinite(clientY)?clientY-rect.top-rect.height/2:0;
    const factor=zoom/this.scale;
    this.x=fx*(1-factor)+this.x*factor;
    this.y=fy*(1-factor)+this.y*factor;
    this.scale=zoom;this.render();
  }
  pan(dx,dy){if(this.scale<=1)return;this.x+=dx;this.y+=dy;this.render();}
  render(){
    if(!this.surface||!this.image)return;
    this.x=clampOffset(this.x,this.scale,this.surface.clientWidth);
    this.y=clampOffset(this.y,this.scale,this.surface.clientHeight);
    this.image.style.transform='translate3d('+this.x.toFixed(1)+'px,'+this.y.toFixed(1)+'px,0) scale('+this.scale.toFixed(3)+')';
    this.surface.classList.toggle('is-zoomed',this.scale>1);
    if(this.status)this.status.textContent=Math.round(this.scale*100)+'%';
    if(this.zoomIn)this.zoomIn.disabled=this.scale>=4;
    if(this.zoomOut)this.zoomOut.disabled=this.scale<=1;
    if(this.zoomReset)this.zoomReset.disabled=this.scale<=1;
  }
  pointerDown(event){
    if(event.pointerType==='mouse'&&event.button!==0)return;
    this.pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
    try{this.surface.setPointerCapture(event.pointerId);}catch{}
    this.lastPinch=null;
  }
  pointerMove(event){
    const old=this.pointers.get(event.pointerId);
    if(!old)return;
    this.pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
    if(this.pointers.size>=2){
      const [a,b]=[...this.pointers.values()].slice(0,2);
      const distance=Math.hypot(a.x-b.x,a.y-b.y);
      const cx=(a.x+b.x)/2,cy=(a.y+b.y)/2;
      if(this.lastPinch&&this.lastPinch.distance>0){
        this.setZoom(this.scale*(distance/this.lastPinch.distance),cx,cy);
        this.pan(cx-this.lastPinch.cx,cy-this.lastPinch.cy);
      }
      this.lastPinch={distance,cx,cy};
    }else if(this.scale>1){
      this.pan(event.clientX-old.x,event.clientY-old.y);
    }
  }
  pointerUp(event){this.pointers.delete(event.pointerId);this.lastPinch=null;}
}
