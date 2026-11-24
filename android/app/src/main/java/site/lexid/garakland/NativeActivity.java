package site.lexid.garakland;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import java.util.List;

/** Native Android navigation, search, demo directory and member gateway.
 * Existing 3D Atlas is a separate restricted WebView, Google OAuth is browser-only.
 */
public final class NativeActivity extends Activity {
    private static final int NAVY=0xFF0A3053, BLUE=0xFF116E86, ORANGE=0xFFFFAA2B;
    private static final int WHITE=Color.WHITE, INK=0xFF1E3E54, MUTED=0xFF6E838C, PALE=0xFFF5F8FA;
    private static final String[] NAMES={"홈","매장","쿠폰","지도","MY"};
    private static final String[] SYMBOLS={"⌂","▦","🎟","⌖","◉"};
    private int tab=0;
    private String category="전체", query="";
    private LinearLayout content, navigation;

    private int dp(float n){return Math.round(n*getResources().getDisplayMetrics().density);}
    private LinearLayout vertical(){LinearLayout v=new LinearLayout(this);v.setOrientation(LinearLayout.VERTICAL);return v;}
    private LinearLayout horizontal(){LinearLayout v=new LinearLayout(this);v.setOrientation(LinearLayout.HORIZONTAL);v.setGravity(Gravity.CENTER_VERTICAL);return v;}
    private LinearLayout.LayoutParams params(int w,int h){return new LinearLayout.LayoutParams(w<0?w:dp(w),h<0?h:dp(h));}
    private GradientDrawable shape(int color,int radius){
        GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(radius));return d;
    }
    private TextView textView(String text,int size,int color,boolean bold){
        TextView t=new TextView(this);t.setText(text);t.setTextSize(size);t.setTextColor(color);
        t.setLineSpacing(dp(2),1f);
        if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        return t;
    }
    private void text(LinearLayout parent,String t,int size,int color,boolean bold){
        parent.addView(textView(t,size,color,bold),params(-1,-2));
    }
    private void space(LinearLayout parent,int h){parent.addView(new View(this),params(1,h));}
    private TextView button(String title,int bg,int fg,Runnable action){
        TextView b=textView(title,14,fg,true);b.setGravity(Gravity.CENTER);
        b.setPadding(dp(12),dp(10),dp(12),dp(10));b.setMinHeight(dp(48));
        b.setBackground(shape(bg,12));b.setContentDescription(title);
        b.setFocusable(true);b.setOnClickListener(v->action.run());return b;
    }
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        getWindow().setStatusBarColor(NAVY);getWindow().setNavigationBarColor(NAVY);
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        if(state!=null){tab=state.getInt("tab",0);category=state.getString("cat","전체");query=state.getString("query","");}
        createShell();show(tab);
    }
    @Override public void onSaveInstanceState(Bundle b){
        b.putInt("tab",tab);b.putString("cat",category);b.putString("query",query);
        super.onSaveInstanceState(b);
    }
    private void createShell(){
        LinearLayout root=vertical();root.setBackgroundColor(PALE);setContentView(root);
        LinearLayout header=horizontal();header.setBackgroundColor(WHITE);
        header.setPadding(dp(17),dp(12),dp(14),dp(12));
        LinearLayout title=vertical();text(title,"가락랜드",26,NAVY,true);
        text(title,"MARKET · CULTURE · DIGITAL",9,ORANGE,true);
        header.addView(title,new LinearLayout.LayoutParams(0,-2,1));
        header.addView(button("내 계정",NAVY,WHITE,()->show(4)),params(-2,44));
        root.addView(header,params(-1,78));
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);
        content=vertical();content.setPadding(dp(17),dp(20),dp(17),dp(32));
        scroll.addView(content,new ScrollView.LayoutParams(-1,-2));
        root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        navigation=horizontal();navigation.setId(R.id.native_bottom_navigation);
        navigation.setBackgroundColor(WHITE);navigation.setPadding(dp(3),dp(6),dp(3),dp(6));
        root.addView(navigation,params(-1,69));
    }
    private void drawNavigation(){
        navigation.removeAllViews();
        for(int i=0;i<NAMES.length;i++){
            final int index=i;
            LinearLayout item=vertical();item.setGravity(Gravity.CENTER);
            TextView symbol=textView(SYMBOLS[i],22,index==tab?ORANGE:MUTED,true);
            TextView title=textView(NAMES[i],11,index==tab?NAVY:MUTED,index==tab);
            symbol.setGravity(Gravity.CENTER);title.setGravity(Gravity.CENTER);
            item.addView(symbol);item.addView(title);
            item.setFocusable(true);item.setContentDescription(NAMES[i]+" 화면");
            if(index==tab)item.setBackground(shape(0xFFECF3F8,12));
            item.setOnClickListener(v->show(index));
            navigation.addView(item,new LinearLayout.LayoutParams(0,-1,1));
        }
    }
    private void show(int index){
        if(index==3){openMap("/map.html");return;}
        if(index<0||index>=NAMES.length)return;
        tab=index;content.removeAllViews();drawNavigation();
        if(index==0)home();else if(index==1)stores();else if(index==2)coupons();else member();
    }
    private LinearLayout card(){
        LinearLayout c=vertical();c.setPadding(dp(17),dp(18),dp(17),dp(19));
        c.setBackground(shape(WHITE,18));
        LinearLayout.LayoutParams p=params(-1,-2);p.bottomMargin=dp(13);
        content.addView(c,p);return c;
    }
    private void section(String top,String heading,String sub){
        text(content,top,12,BLUE,true);space(content,8);
        text(content,heading,27,NAVY,true);space(content,10);
        text(content,sub,13,MUTED,false);space(content,21);
    }
    private void demo(){
        LinearLayout c=card();c.setBackground(shape(0xFFFFF5DF,16));
        text(c,"시연용 정보 · 실제 거래 불가",13,0xFF815518,true);space(c,7);
        text(c,"현재 업소·가격·쿠폰은 실제 등록 정보가 아닌 체험용 데이터입니다. 방문과 결제 전에 반드시 확인하세요.",12,0xFF715D3D,false);
    }
    private void home(){
        LinearLayout hero=vertical();hero.setPadding(dp(23),dp(28),dp(23),dp(24));
        GradientDrawable g=new GradientDrawable(GradientDrawable.Orientation.TL_BR,
                new int[]{NAVY,0xFF145270,0xFF25899C});g.setCornerRadius(dp(22));hero.setBackground(g);
        LinearLayout.LayoutParams p=params(-1,-2);p.bottomMargin=dp(19);content.addView(hero,p);
        text(hero,"GARAKLAND · MARKET THEME PARK",11,0xFFFFD294,true);space(hero,12);
        text(hero,"가락시장을\n온라인 테마파크로",28,WHITE,true);space(hero,11);
        text(hero,"시장 탐험 · 먹거리 · 상인 이야기 · 온라인 유통",13,0xFFD8EEF4,false);
        space(hero,24);hero.addView(button("3D 시장 탐험  ↗",ORANGE,NAVY,()->openMap("/map.html")),params(-1,50));
        text(content,"오늘의 가락랜드",21,INK,true);space(content,13);
        LinearLayout c=card();text(c,"시장 탐험과 쇼핑",18,NAVY,true);
        space(c,7);text(c,"가락시장의 제철 먹거리와 시연 업소를 네이티브 화면에서 둘러보세요.",13,MUTED,false);
        space(c,16);c.addView(button("매장 찾아보기",BLUE,WHITE,()->show(1)),params(-1,49));
        LinearLayout actions=horizontal();
        TextView left=button("🎟 쿠폰",0xFFFBE3BD,NAVY,()->show(2));
        TextView right=button("◉ 마이페이지",0xFFE4EFF4,NAVY,()->show(4));
        LinearLayout.LayoutParams l=new LinearLayout.LayoutParams(0,dp(51),1);l.rightMargin=dp(9);
        actions.addView(left,l);actions.addView(right,new LinearLayout.LayoutParams(0,dp(51),1));
        content.addView(actions,params(-1,-2));space(content,13);demo();
    }
    private void stores(){
        section("GARAKLAND STORE DIRECTORY","매장 찾기","카테고리와 검색어로 시연 매장을 탐색합니다.");
        EditText search=new EditText(this);search.setSingleLine(true);search.setTextSize(15);
        search.setHint("매장명 · 업종 · 상품 검색");search.setHintTextColor(MUTED);search.setTextColor(INK);
        search.setPadding(dp(14),dp(6),dp(14),dp(6));search.setBackground(shape(WHITE,13));
        search.setText(query);content.addView(search,params(-1,52));space(content,12);
        HorizontalScrollView h=new HorizontalScrollView(this);h.setHorizontalScrollBarEnabled(false);
        LinearLayout filters=horizontal();
        for(String cat:new String[]{"전체","청과","수산","축산","먹거리"}){
            TextView chip=button(cat,cat.equals(category)?BLUE:0xFFE5EDF1,cat.equals(category)?WHITE:INK,
                ()->{query=search.getText().toString();category=cat;show(1);});
            LinearLayout.LayoutParams p=params(-2,40);p.rightMargin=dp(7);filters.addView(chip,p);
        }
        h.addView(filters);content.addView(h);space(content,15);
        LinearLayout list=vertical();content.addView(list,params(-1,-2));fillStores(list,query);
        search.addTextChangedListener(new TextWatcher(){
            @Override public void beforeTextChanged(CharSequence s,int a,int c,int x){}
            @Override public void onTextChanged(CharSequence s,int a,int b,int c){query=s.toString();fillStores(list,query);}
            @Override public void afterTextChanged(Editable e){}
        });
        space(content,12);demo();
    }
    private void fillStores(LinearLayout list,String term){
        list.removeAllViews();List<NativeCatalog.Store> items=NativeCatalog.find(category,term);
        text(list,items.size()+"개 시연 매장",13,MUTED,true);space(list,12);
        if(items.isEmpty()){text(list,"검색 결과가 없습니다.",16,INK,true);return;}
        for(NativeCatalog.Store s:items){
            LinearLayout c=vertical();c.setPadding(dp(16),dp(17),dp(16),dp(16));c.setBackground(shape(WHITE,16));
            LinearLayout.LayoutParams p=params(-1,-2);p.bottomMargin=dp(12);list.addView(c,p);
            text(c,s.symbol+"  "+s.category+" · 시연 업소",13,BLUE,true);space(c,6);
            text(c,s.name,20,NAVY,true);space(c,6);text(c,s.location,12,MUTED,false);
            space(c,9);text(c,s.summary,13,INK,false);space(c,14);
            c.addView(button("매장 상세·회원 즐겨찾기  ↗",BLUE,WHITE,
                ()->openBrowser("/store.html?id="+s.id)),params(-1,47));
        }
    }
    private void coupons(){
        section("GARAKLAND BENEFITS","쿠폰 체험","회원 지갑은 웹 Google 로그인과 연동됩니다.");
        demo();
        for(NativeCatalog.Coupon c:NativeCatalog.COUPONS){
            LinearLayout v=card();text(v,"🎟  DEMO · 현장 사용 불가",12,BLUE,true);space(v,9);
            text(v,c.title,18,NAVY,true);space(v,6);text(v,c.benefit,23,ORANGE,true);space(v,7);
            text(v,c.note,12,MUTED,false);space(v,14);
            v.addView(button("웹 쿠폰 지갑에서 확인  ↗",BLUE,WHITE,()->openBrowser("/coupons.html")),params(-1,48));
        }
    }
    private void member(){
        section("MY GARAKLAND","나의 가락랜드","Google 로그인 · 회원별 쿠폰 · 찜한 업소");
        LinearLayout a=card();text(a,"◉  Google 계정",19,NAVY,true);space(a,9);
        text(a,"로그인은 Chrome 등 시스템 브라우저에서 안전하게 진행합니다. 앱에 비밀번호를 저장하지 않습니다.",13,MUTED,false);space(a,14);
        a.addView(button("Google 로그인 · 회원가입  ↗",ORANGE,NAVY,
                ()->openBrowser("/login.html?next=%2Fmypage.html")),params(-1,50));
        space(a,9);a.addView(button("내 마이페이지 열기  ↗",BLUE,WHITE,
                ()->openBrowser("/mypage.html")),params(-1,50));
        LinearLayout b=card();text(b,"🎟 쿠폰 · ♡ 즐겨찾기",19,NAVY,true);space(b,8);
        text(b,"현재 회원별 저장 기능은 웹사이트의 Neon Auth 세션에서 운영됩니다. 네이티브 앱은 회원 비밀번호나 인증 토큰을 공유·복제하지 않습니다.",13,MUTED,false);space(b,14);
        b.addView(button("내 쿠폰 지갑",0xFFE4EFF4,NAVY,
                ()->openBrowser("/mypage.html?tab=coupons")),params(-1,49));
        space(b,8);
        b.addView(button("내가 찜한 업소",0xFFE4EFF4,NAVY,
                ()->openBrowser("/mypage.html?tab=favorites")),params(-1,49));
    }
    private void openMap(String path){
        if(!AppConfig.isEmbeddedRoute(path))return;
        Intent i=new Intent(this,MainActivity.class);i.putExtra("page",path);startActivity(i);
    }
    private void openBrowser(String path){
        try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(AppConfig.page(path))));}
        catch(IllegalArgumentException|ActivityNotFoundException e){
            Toast.makeText(this,R.string.external_error,Toast.LENGTH_LONG).show();
        }
    }
    @Override public void onBackPressed(){if(tab!=0)show(0);else super.onBackPressed();}
}
