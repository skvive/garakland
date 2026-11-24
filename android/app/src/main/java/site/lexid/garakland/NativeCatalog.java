package site.lexid.garakland;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

/** These are the same four DEMO fixtures as the GARAKLAND web brand/data.js.
 * No entry is asserted to be an active or verified market tenant.
 */
public final class NativeCatalog {
    private NativeCatalog() {}

    public static final class Store {
        public final String id, name, category, location, summary, symbol;
        public Store(String id, String name, String category, String location, String summary, String symbol) {
            this.id = id;
            this.name = name;
            this.category = category;
            this.location = location;
            this.summary = summary;
            this.symbol = symbol;
        }
    }

    public static final class Coupon {
        public final String id, storeId, title, benefit, note;
        public Coupon(String id, String storeId, String title, String benefit, String note) {
            this.id=id;this.storeId=storeId;this.title=title;this.benefit=benefit;this.note=note;
        }
    }

    public static final List<Store> STORES = Collections.unmodifiableList(Arrays.asList(
        new Store("demo-sea", "바다마루 수산", "수산", "수산 구역 · 1층", "제철 해산물과 시장 체험을 소개하는 시연 업소입니다.", "🐟"),
        new Store("demo-fruit", "색동과일", "청과", "청과 구역 · 1층", "제철 과일과 산지 이야기를 전하는 시연 업소입니다.", "🍊"),
        new Store("demo-meat", "고기공방", "축산", "축산 구역 · 1층", "정육 관리와 식재료 장보기를 소개하는 시연 업소입니다.", "🥩"),
        new Store("demo-kitchen", "가락한상 키친", "먹거리", "가락몰 테마존 · 2층", "시장 먹거리를 소개하는 가상의 시연 식당입니다.", "🍽")
    ));

    public static final List<Coupon> COUPONS = Collections.unmodifiableList(Arrays.asList(
        new Coupon("c-sea","demo-sea","수산 장보기 할인 체험권","3,000원 할인","3만원 이상 구매를 가정한 시연 혜택"),
        new Coupon("c-fruit","demo-fruit","제철 과일 체험 쿠폰","10% 할인","실제 할인에 사용할 수 없는 시연 쿠폰"),
        new Coupon("c-meat","demo-meat","축산 한상 체험 쿠폰","5,000원 할인","5만원 이상 구매를 가정한 시연 혜택"),
        new Coupon("c-kitchen","demo-kitchen","한상 방문 체험 쿠폰","2,000원 할인","실제 방문에 사용할 수 없는 시연 쿠폰")
    ));

    public static List<Store> find(String category, String query) {
        String term = query == null ? "" : query.trim().toLowerCase(Locale.ROOT);
        List<Store> results = new ArrayList<>();
        for (Store s : STORES) {
            if (category != null && !category.equals("전체") && !category.equals(s.category)) continue;
            if (!term.isEmpty() && !(s.name + " " + s.category + " " + s.summary + " " + s.location)
                    .toLowerCase(Locale.ROOT).contains(term)) continue;
            results.add(s);
        }
        return results;
    }

    public static Store byId(String id) {
        for (Store s : STORES) if (s.id.equals(id)) return s;
        return null;
    }
}
