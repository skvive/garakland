"""Responsive real-browser acceptance for the public map mode simplification."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import socket,sys,subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'qa-artifacts'/'map-mode'
OUT.mkdir(parents=True,exist_ok=True)
def run():
  with socket.socket() as sock:
    sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  server=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  checks=0
  try:
    with sync_playwright() as pw:
      browser=pw.chromium.launch(headless=True)
      for label,w,h in [('desktop',1440,900),('mobile',390,844),('compact',360,740)]:
        context=browser.new_context(viewport={'width':w,'height':h},reduced_motion='reduce')
        page=context.new_page()
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        response=page.goto(f'http://127.0.0.1:{port}/map.html?mode=satellite',wait_until='networkidle',timeout=30000)
        assert response and response.status==200
        modes=page.locator('.mode-switch [data-mode]')
        assert modes.count()==4
        assert modes.evaluate_all("(els)=>els.map(x=>x.dataset.mode)")==['concept','terrain','3d','floor']
        assert page.locator('[data-mode="satellite"]').count()==0
        assert page.locator('[data-mode="concept"]').get_attribute('aria-pressed')=='true'
        assert page.locator('.concept-map').count()==1
        checks+=1
        page.locator('[data-mode="floor"]').click()
        assert page.locator('.floor-map-viewer').count()==1
        assert page.locator('[data-mode="floor"]').get_attribute('aria-pressed')=='true'
        page.locator('[data-mode="concept"]').click()
        assert page.locator('.concept-map').count()==1
        assert page.locator('[data-mode="concept"]').get_attribute('aria-pressed')=='true'
        checks+=1
        page.locator('[data-mode="3d"]').click()
        assert page.locator('#settingsDialog').evaluate("(el)=>el.open")
        assert page.locator('.concept-map').count()==1
        assert page.locator('[data-mode="satellite"]').count()==0
        page.locator('#settingsDialog button[aria-label="닫기"]').click()
        checks+=1
        if label!='compact':page.screenshot(path=str(OUT/f'{label}-map-no-satellite.png'),full_page=True)
        assert not errors,errors
        context.close()
      browser.close()
    print(f'PASS public map: {checks} browser checks, 3 viewports, satellite tab absent, mode transitions verified, 0 JS errors')
  finally:
    server.terminate()
    try:server.wait(timeout=5)
    except subprocess.TimeoutExpired:server.kill()
if __name__=='__main__':run()
