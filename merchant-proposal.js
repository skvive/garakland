(()=>{'use strict';
const ids=['views','rate','basket'];const fmt=new Intl.NumberFormat('ko-KR');
function recalc(){const v=Number(document.getElementById('views')?.value||500),r=Number(document.getElementById('rate')?.value||2),b=Number(document.getElementById('basket')?.value||30000);const sales=Math.round(v*r/100);document.getElementById('views-number').textContent=fmt.format(v);document.getElementById('rate-number').textContent=fmt.format(r);document.getElementById('basket-number').textContent=fmt.format(b);document.getElementById('sales-count').textContent=fmt.format(sales)+'건';document.getElementById('sales-value').textContent=fmt.format(sales*b)+'원';}
ids.forEach(id=>document.getElementById(id)?.addEventListener('input',recalc));recalc();
document.getElementById('print-proposal')?.addEventListener('click',()=>window.print());
})();