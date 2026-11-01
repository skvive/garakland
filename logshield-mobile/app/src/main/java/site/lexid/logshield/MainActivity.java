package site.lexid.logshield;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Native Android management console. PC endpoint protection remains on Windows. */
public final class MainActivity extends Activity {
    private static final int BG = 0xFF0A1524, PANEL = 0xFF13243A, INK = 0xFFE8F1FA;
    private static final int MUTED = 0xFF9CB1C7, ACCENT = 0xFF18B8A2, WARN = 0xFFFFB669;
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private SessionVault vault;
    private ApiClient api;
    private JSONObject profile;
    private String selected = "대시보드";
    private LinearLayout screen, content;
    private volatile boolean active = true;
    private final UiEpoch uiEpoch = new UiEpoch();
    private int policyFetchSerial = 0;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_SECURE, WindowManager.LayoutParams.FLAG_SECURE);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        vault = new SessionVault(this);
        if (vault.hasKey()) restoreSession();
        else showLogin(null);
    }
    @Override protected void onDestroy() { active = false; uiEpoch.invalidate(); worker.shutdownNow(); super.onDestroy(); }

    /** Transient server/network errors MUST NOT erase device-encrypted credentials. */
    private void restoreSession() {
        execute(null, () -> {
            ApiClient candidate = new ApiClient(vault.server(), vault.actor(), vault.getToken(), false);
            JSONObject identity = candidate.get("/api/admin/me");
            api = candidate;
            return identity;
        }, this::loggedIn, reason -> {
            if (reason.startsWith("AUTH_REVOKED:")) {
                vault.clear();
                showLogin("관리자 인증이 만료 또는 회수되었습니다. 다시 로그인하세요.");
            } else {
                showLogin("서버 연결 실패. 저장된 인증키는 삭제되지 않았습니다.");
            }
        });
    }

    private interface Work { JSONObject perform() throws Exception; }
    private interface Success { void accept(JSONObject result); }
    private interface Failure { void accept(String reason); }
    private void execute(String placeholder, Work work, Success done, Failure failure) {
        if (placeholder != null && content != null) label(content, placeholder, 14, MUTED);
        final long issuedAt = uiEpoch.current();
        worker.submit(() -> {
            try {
                JSONObject result = work.perform();
                runOnUiThread(() -> { if (active && uiEpoch.isCurrent(issuedAt)) done.accept(result); });
            } catch (Exception ex) {
                String msg;
                if (ex instanceof ApiClient.ApiHttpException &&
                      ((((ApiClient.ApiHttpException) ex).statusCode == 401) ||
                       (((ApiClient.ApiHttpException) ex).statusCode == 403))) {
                    msg = "AUTH_REVOKED: 관리자 인증 오류";
                } else {
                    msg = ex.getMessage() == null ? "요청 처리 실패" : ex.getMessage();
                }
                final String message = msg;
                runOnUiThread(() -> { if (active && uiEpoch.isCurrent(issuedAt)) failure.accept(message); });
            }
        });
    }
    private void execute(String placeholder, Work work, Success done) {
        execute(placeholder, work, done, err -> error(err));
    }
    private int dp(int n) { return Math.round(getResources().getDisplayMetrics().density * n); }
    private LinearLayout vertical() { LinearLayout v = new LinearLayout(this); v.setOrientation(LinearLayout.VERTICAL); return v; }
    private void pad(View view, int n) { view.setPadding(dp(n), dp(n), dp(n), dp(n)); }
    private TextView label(LinearLayout into, String message, int size, int color) {
        TextView t = new TextView(this); t.setText(message); t.setTextColor(color); t.setTextSize(size);
        t.setLineSpacing(dp(3), 1f); t.setPadding(0, dp(5), 0, dp(5)); into.addView(t); return t;
    }
    private void title(LinearLayout parent, String text) { TextView v = label(parent, text, 22, INK); v.setTypeface(null, Typeface.BOLD); }
    private Button button(LinearLayout into, String text, Runnable action) {
        Button b = new Button(this); b.setAllCaps(false); b.setText(text); b.setTextColor(INK);
        b.setBackgroundTintList(android.content.res.ColorStateList.valueOf(PANEL));
        into.addView(b, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(50)));
        b.setOnClickListener(v -> action.run()); return b;
    }
    private EditText field(LinearLayout into, String hint, String value, boolean secret) {
        EditText e = new EditText(this); e.setSingleLine(true); e.setTextColor(INK); e.setHintTextColor(MUTED);
        e.setHint(hint); e.setText(value == null ? "" : value); e.setTextSize(15);
        if (secret) e.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        into.addView(e, new LinearLayout.LayoutParams(-1, dp(56))); return e;
    }
    private LinearLayout card(LinearLayout parent) {
        LinearLayout panel = vertical(); pad(panel, 14); panel.setBackgroundColor(PANEL);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1,-2); lp.bottomMargin=dp(12); parent.addView(panel, lp);
        return panel;
    }
    private void surface() {
        ScrollView scroll = new ScrollView(this); scroll.setFillViewport(true); scroll.setBackgroundColor(BG);
        screen = vertical(); pad(screen, 18); scroll.addView(screen); setContentView(scroll);
    }
    private void error(String message) { new AlertDialog.Builder(this).setTitle("LogShield 알림").setMessage(message).setPositiveButton("확인", null).show(); }
    private void confirm(String message, Runnable yes) {
        new AlertDialog.Builder(this).setTitle("관리 작업 확인").setMessage(message)
            .setNegativeButton("취소", null).setPositiveButton("계속", (d,w)->yes.run()).show();
    }
    private void showLogin(String notice) {
        uiEpoch.invalidate();
        profile = null; api = null; surface();
        label(screen,"LOGSHIELD  /  ENTERPRISE",13,ACCENT);
        title(screen,"모바일 보안 관제");
        label(screen,"직원 PC 보안 상태, 알림 및 정책을 승인된 관리자만 확인합니다.",14,MUTED);
        if (notice != null) label(screen,notice,14,WARN);
        LinearLayout panel = card(screen);
        EditText server = field(panel,"중앙 서버 HTTPS 주소",vault.server(), false);
        EditText actor = field(panel,"관리자 ID",vault.actor(),false);
        EditText key = field(panel,"관리자 API 키", "", true);
        if (vault.hasKey()) {
            button(panel, "저장된 인증키로 다시 연결", this::restoreSession);
        }
        button(panel, "보안 연결 및 로그인", () -> {
            final String url = server.getText().toString(), user = actor.getText().toString(), token = key.getText().toString();
            key.setText("");
            execute(null, () -> {
                ApiClient candidate = new ApiClient(url, user, token, false);
                return candidate.get("/api/admin/me");
            }, who -> {
                try {
                    vault.save(SecurityRules.normalizeServer(url, false), user, token);
                    api = new ApiClient(url, user, token, false);
                    loggedIn(who);
                } catch (Exception e) { error("인증정보 보호 저장 실패. 로그인하지 않았습니다."); }
            });
        });
        label(screen,"HTTPS 인증 필수 · Android Keystore 암호화 저장 · 화면 캡처 제한",12,MUTED);
        label(screen,"이 앱은 모바일 관리 콘솔이며 Windows USB 차단·프린터 드라이버를 대체하지 않습니다.",12,MUTED);
    }
    private boolean permitted(String p) {
        JSONArray list = profile == null ? null : profile.optJSONArray("permissions");
        if (list == null) return false;
        for (int i=0;i<list.length();i++) if(p.equals(list.optString(i))) return true;
        return false;
    }
    private void loggedIn(JSONObject who) {
        profile = who;
        selected = "대시보드"; showMain();
    }
    private void showMain() {
        uiEpoch.invalidate();
        surface();
        label(screen,"LOGSHIELD   •   CONTROL PLANE",12,ACCENT);
        title(screen,"모바일 보안 관제");
        label(screen,profile.optString("username")+" · "+profile.optString("role")+" · "+profile.optString("department"),13,MUTED);
        LinearLayout top = vertical(); screen.addView(top);
        button(top,"새로고침",this::showMain);
        HorizontalScrollView bar = new HorizontalScrollView(this);
        LinearLayout tabs = new LinearLayout(this); tabs.setOrientation(LinearLayout.HORIZONTAL);
        bar.addView(tabs); screen.addView(bar);
        List<String> visible = new ArrayList<>();
        if(permitted("endpoint.read")) visible.add("대시보드");
        if(permitted("endpoint.read")) visible.add("PC 목록");
        if(permitted("audit.read")) visible.add("보안 알림");
        if(permitted("policy.read")) visible.add("정책");
        if(permitted("invitation.create")) visible.add("설치 초대장");
        if(permitted("audit.read")) visible.add("보안 신호");
        if(permitted("print.read")) visible.add("출력 감사");
        if(permitted("audit.read")) visible.add("감사 검증");
        for (String tab : visible) {
            Button b = new Button(this); b.setText(tab); b.setAllCaps(false); b.setTextColor(tab.equals(selected)?ACCENT:INK);
            tabs.addView(b); b.setOnClickListener(v->{selected=tab;showMain();});
        }
        content = vertical(); screen.addView(content);
        title(content,selected);
        switch (selected) {
            case "대시보드": loadDashboard(); break;
            case "PC 목록": loadEndpoints(); break;
            case "보안 알림": loadAlerts(); break;
            case "정책": loadPolicy(); break;
            case "설치 초대장": loadInvitations(); break;
            case "보안 신호": loadSecuritySignals(); break;
            case "출력 감사": loadPrints(); break;
            case "감사 검증": loadAudit(); break;
            default: label(content,"이 역할에 허가된 메뉴가 없습니다.",14,MUTED);
        }
        LinearLayout footer = card(screen);
        button(footer,"로그아웃 및 저장된 키 삭제",()->confirm("저장된 관리자 인증정보를 기기에서 삭제할까요?",()->{
            vault.clear();showLogin(null);
        }));
    }
    private void loadDashboard() {
        execute("장치·알림 현황 조회 중…", () -> {
            JSONObject combined = new JSONObject();
            combined.put("eps",api.get("/api/admin/endpoints"));
            if(permitted("audit.read")) combined.put("alerts",api.get("/api/admin/alerts"));
            return combined;
        }, result -> {
            content.removeAllViews(); title(content,"보안 요약");
            JSONObject ep = result.optJSONObject("eps");
            JSONArray pcs = ep == null ? new JSONArray() : ep.optJSONArray("endpoints");
            if(pcs == null) pcs = new JSONArray();
            int online=0;
            for(int i=0;i<pcs.length();i++) if("online".equals(pcs.optJSONObject(i).optString("status"))) online++;
            LinearLayout card=card(content);
            label(card,"등록 PC   " + pcs.length(),20,INK);
            label(card,"온라인   " + online + "   /   오프라인·폐기   " +(pcs.length()-online),15,ACCENT);
            JSONObject al=result.optJSONObject("alerts");
            JSONArray alerts=al==null?null:al.optJSONArray("alerts");
            if(alerts!=null) {
                int open=0; for(int i=0;i<alerts.length();i++) if(alerts.optJSONObject(i).isNull("ack_by"))open++;
                LinearLayout a=card(content); label(a,"미처리 경고   " + open,20,open>0?WARN:ACCENT);
                button(a,"경고 확인",()->{selected="보안 알림";showMain();});
            }
        });
    }
    private void loadEndpoints() {
        execute("장치 조회 중…",()->api.get("/api/admin/endpoints"),res->{
            content.removeAllViews(); title(content,"직원 PC 목록");
            JSONArray arr=res.optJSONArray("endpoints"); if(arr==null) return;
            for(int i=0;i<arr.length();i++) {
                JSONObject pc=arr.optJSONObject(i); if(pc==null)continue;
                String id=pc.optString("id"); LinearLayout row=card(content);
                label(row,pc.optString("hostname"),18,INK);
                label(row,pc.optString("department")+"  ·  "+pc.optString("status"),13,MUTED);
                label(row,"공인 IP: "+pc.optString("public_ip","-")+"    최근 통신: "+pc.optString("last_seen","-"),12,MUTED);
                if(permitted("inventory.read"))button(row,"장치 상세·프로세스",()->execute(null,()->api.get("/api/admin/endpoints/"+id+"/inventory"),
                    data->error(data.toString())));
                if(permitted("command.create") && !"revoked".equals(pc.optString("status"))) {
                    button(row,"PC 현황 갱신 명령",()->confirm(pc.optString("hostname")+"의 현황 갱신을 요청합니까?",()->{
                        try{JSONObject body=new JSONObject();body.put("endpoint_id",id);body.put("kind","refresh_inventory");body.put("detail","");
                            execute(null,()->api.post("/api/admin/command",body),r->error("요청 등록: "+r.optString("command_id")));
                        }catch(Exception e){error("요청 데이터 오류");}
                    }));
                }
                if(permitted("command.create") && !"revoked".equals(pc.optString("status"))) {
                    button(row,"PC에 보안 안내 보내기",()->{
                        EditText text = new EditText(this); text.setSingleLine(false); text.setHint("직원에게 보낼 보안 안내");
                        new AlertDialog.Builder(this).setTitle("안내문 전송").setView(text)
                            .setNegativeButton("취소",null).setPositiveButton("전송",(d,w)->{
                                String msg=text.getText().toString().trim();
                                if(msg.isEmpty()||msg.length()>500){error("안내 문구는 1~500자여야 합니다.");return;}
                                try {JSONObject b=new JSONObject().put("endpoint_id",id).put("kind","notify").put("detail",msg);
                                    execute(null,()->api.post("/api/admin/command",b),r->error("전송 대기: "+r.optString("command_id")));
                                }catch(Exception e){error("요청 데이터 오류");}
                            }).show();
                    });
                }
                if(permitted("endpoint.write") && !"revoked".equals(pc.optString("status"))) {
                    button(row,"장치 등록 폐기",()->confirm(pc.optString("hostname")+"의 인증키를 폐기하고 통신을 차단합니까? 취소할 수 없습니다.",()->{
                        execute(null,()->api.delete("/api/admin/endpoints/"+id),r->{error("장치 등록이 폐기되었습니다.");showMain();});
                    }));
                }
            }
        });
    }
    private void loadAlerts() {
        execute("경고 조회 중…",()->api.get("/api/admin/alerts"),res->{
            content.removeAllViews(); title(content,"보안 경고·처리 기록");
            if(permitted("alert.manage"))button(content,"오프라인 PC 검사 실행",()->confirm("최근 통신이 없는 PC를 검사하고 신규 경고를 기록할까요?",()->
                execute(null,()->api.post("/api/admin/endpoints/sweep",new JSONObject()),r->{error("신규 오프라인 PC: "+r.optInt("count"));showMain();})));
            JSONArray arr=res.optJSONArray("alerts"); if(arr==null)return;
            for(int i=0;i<arr.length();i++) {
                JSONObject alert=arr.optJSONObject(i);if(alert==null)continue;
                LinearLayout row=card(content); int id=alert.optInt("id");
                label(row,alert.optString("severity").toUpperCase()+"  ·  "+alert.optString("kind"),17,WARN);
                label(row,alert.optString("endpoint_id")+"  ·  "+alert.optString("timestamp"),12,MUTED);
                label(row,alert.optString("detail"),13,INK);
                if(!alert.isNull("ack_by")) label(row,"처리: "+alert.optString("ack_by"),12,ACCENT);
                else if(permitted("alert.manage"))button(row,"이 경고 확인 처리",()->confirm("알림 #"+id+"을 확인 처리합니까?",()->
                    execute(null,()->api.post("/api/admin/alerts/"+id+"/ack",new JSONObject()),r->loadAlerts())));
            }
        });
    }
    private String department() {return profile.optString("department","IT").isEmpty()?"IT":profile.optString("department");}
    private void loadPolicy() {
        LinearLayout panel=card(content);
        EditText dept=field(panel,"부서 이름",department(),false);
        button(panel,"부서 정책 조회",()->renderPolicy(dept.getText().toString()));
        renderPolicy(department());
    }
    private void renderPolicy(String dept) {
        final int requestedPolicy = ++policyFetchSerial;
        try {
            final String path="/api/admin/policy/"+SecurityRules.segment(dept);
            execute("정책과 변경 이력 로딩…",()->{
                JSONObject all=new JSONObject();all.put("current",api.get(path));
                all.put("history",api.get(path+"/history")); return all;
            },res->{
                if (requestedPolicy != policyFetchSerial) return;
                LinearLayout result=card(content);
                JSONObject current=res.optJSONObject("current");if(current==null)return;
                int version=current.optInt("version");
                label(result,"현재 정책 v"+version+"  ·  부서: "+dept,17,ACCENT);
                label(result,current.optString("config"),12,INK);
                if(permitted("policy.write"))button(result,"정책 편집·버전 저장",()->showPolicyEditor(dept,version,current.optString("config")));
                JSONArray history=res.optJSONObject("history").optJSONArray("versions");
                for(int i=0;history!=null && i<history.length();i++) {
                    JSONObject h=history.optJSONObject(i);if(h==null)continue;
                    int old=h.optInt("version");
                    LinearLayout line=card(result);
                    label(line,"v"+old+" · "+h.optString("changed_by")+" · "+h.optString("changed_at"),13,MUTED);
                    if(permitted("policy.write")&&old<version)button(line,"v"+old+" 복원",()->confirm("기존 정책을 복원하면 새 버전이 생성됩니다. 진행합니까?",()->{
                        try {JSONObject payload=new JSONObject().put("department",dept).put("target_version",old).put("expected_version",version);
                            execute(null,()->api.post("/api/admin/policy/rollback",payload),r->{error("새 버전 v"+r.optInt("version")+"으로 복원됨");showMain();});
                        }catch(Exception e){error("요청 데이터 오류");}
                    }));
                }
            });
        }catch(Exception e){error(e.getMessage());}
    }
    private void showPolicyEditor(String dept, int expectedVersion, String configRaw) {
        try {
            JSONObject config = new JSONObject(configRaw);
            LinearLayout form = vertical(); pad(form,16);
            EditText label = field(form,"출력 워터마크",config.optString("watermark_label","CONFIDENTIAL"),false);
            EditText processCollection = field(form,"프로세스 이름 수집 (true/false)",String.valueOf(config.optBoolean("collect_process_names",false)),false);
            JSONArray allowed=config.optJSONArray("allowed_process_names");
            StringBuilder list=new StringBuilder();
            if(allowed!=null)for(int i=0;i<allowed.length();i++){if(i>0)list.append(", ");list.append(allowed.optString(i));}
            EditText allow=field(form,"수집 허용 프로세스 (쉼표 구분)",list.toString(),false);
            new AlertDialog.Builder(this).setTitle("부서별 보안정책 편집").setView(form)
                .setNegativeButton("취소",null).setPositiveButton("저장",(dialog,which)->{
                    try {
                        String w=label.getText().toString().trim();
                        String flag=processCollection.getText().toString().trim();
                        if(w.isEmpty()||w.length()>80||(!"true".equals(flag)&&!"false".equals(flag))){error("워터마크는 1~80자, 수집 설정은 true/false만 허용합니다.");return;}
                        JSONArray names=new JSONArray();
                        if(!allow.getText().toString().trim().isEmpty()) {
                            for(String x:allow.getText().toString().split(",")){
                                x=x.trim();if(!x.isEmpty())names.put(x);
                                if(names.length()>30){error("허용 프로세스는 최대 30개입니다.");return;}
                            }
                        }
                        JSONObject payload=new JSONObject().put("department",dept).put("expected_version",expectedVersion)
                            .put("watermark_label",w).put("collect_process_names",Boolean.parseBoolean(flag)).put("allowed_process_names",names);
                        execute(null,()->api.put("/api/admin/policy",payload),r->{error("보안정책이 v"+r.optInt("version")+"으로 저장되었습니다.");showMain();});
                    } catch(Exception e) { error("정책 형식 오류"); }
                }).show();
        } catch(Exception e){error("서버 정책 데이터를 읽을 수 없습니다.");}
    }
    private void loadInvitations() {
        LinearLayout row=card(content); EditText dept=field(row,"설치 대상 부서",department(),false);
        button(row,"1시간 유효한 PC 설치 초대장 발급",()->confirm("초대장은 한 번만 표시됩니다. 인증키를 안전하게 전달하세요.",()->{
            try {JSONObject payload=new JSONObject().put("department",dept.getText().toString()).put("ttl_minutes",60);
                execute(null,()->api.post("/api/admin/invitations",payload),r->{
                    final String token=r.optString("token");
                    new AlertDialog.Builder(this).setTitle("등록 초대장 (1회 표시)")
                        .setMessage("ID: "+r.optString("id")+"\n만료: "+r.optString("expires_at")+"\n\n"+token)
                        .setPositiveButton("닫기",(d,w)->showMain())
                        .setNeutralButton("복사",(d,w)->{
                            ClipboardManager clip=(ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
                            if(clip!=null)clip.setPrimaryClip(ClipData.newPlainText("등록 초대장",token));
                            showMain();
                        }).show();
                });
            }catch(Exception e){error("초대장 요청 오류");}
        }));
        execute("초대장 목록 조회 중…",()->api.get("/api/admin/invitations"),r->{
            JSONArray arr=r.optJSONArray("invitations");if(arr==null)return;
            for(int i=0;i<arr.length();i++){
                JSONObject invite=arr.optJSONObject(i);if(invite==null)continue;
                LinearLayout it=card(content);String id=invite.optString("id");
                label(it,id+" · "+invite.optString("department"),15,INK);
                label(it,"만료: "+invite.optString("expires_at")+" · 사용: "+invite.optString("used_at"),12,MUTED);
                if(invite.isNull("used_at")&&invite.isNull("revoked_at"))button(it,"이 초대장 폐기",()->confirm("초대장 "+id+"을 폐기합니까?",()->
                    execute(null,()->api.delete("/api/admin/invitations/"+id),rr->showMain())));
            }
        });
    }
    private void loadSecuritySignals() {
        execute("Defender·USB 보안 신호 조회 중…",()->api.get("/api/admin/security-signals"),res->{
            content.removeAllViews();title(content,"보안 신호");
            JSONArray a=res.optJSONArray("signals");if(a==null)return;
            for(int i=0;i<a.length();i++){
                JSONObject x=a.optJSONObject(i);if(x==null)continue;
                LinearLayout row=card(content);
                label(row,x.optString("kind"),16,WARN);
                label(row,x.optString("endpoint_id")+" · "+x.optString("observed_at"),12,MUTED);
            }
        });
    }
    private void loadPrints() {
        execute("출력 감사 조회 중…",()->api.get("/api/admin/print"),res->{
            content.removeAllViews();title(content,"보안 출력 기록");
            JSONArray a=res.optJSONArray("print_events");if(a==null)return;
            for(int i=0;i<a.length();i++){
                JSONObject x=a.optJSONObject(i);if(x==null)continue;
                LinearLayout row=card(content);
                label(row,x.optString("endpoint_id")+" · "+x.optString("created_at"),14,INK);
                label(row,"SHA256: "+x.optString("document_sha256"),12,MUTED);
                label(row,"워터마크: "+x.optString("watermark"),13,ACCENT);
            }
        });
    }
    private void loadAudit() {
        execute("감사 체인 검증 요청 중…",()->api.get("/api/admin/audit/verify"),res->{
            content.removeAllViews();title(content,"감사 로그 무결성");
            LinearLayout card=card(content);
            label(card,res.optBoolean("valid")?"검증 성공":"무결성 이상",22,res.optBoolean("valid")?ACCENT:WARN);
            label(card,"검증된 기록: "+res.optInt("checked"),16,INK);
        });
    }
}
