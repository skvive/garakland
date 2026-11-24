package site.lexid.garakland;

import static org.junit.Assert.*;
import org.junit.Test;

public final class NativeCatalogTest {
    @Test public void fixturesAreExplicitDemoListings() {
        assertEquals(4, NativeCatalog.STORES.size());
        assertEquals(4, NativeCatalog.COUPONS.size());
        for (NativeCatalog.Store store : NativeCatalog.STORES) {
            assertTrue(store.id.startsWith("demo-"));
            assertNotNull(store.name);
        }
    }

    @Test public void couponReferencesKnownStore() {
        for (NativeCatalog.Coupon coupon : NativeCatalog.COUPONS) {
            assertNotNull(NativeCatalog.byId(coupon.storeId));
        }
    }

    @Test public void nativeSearchFiltersByCategoryAndQuery() {
        assertEquals(4, NativeCatalog.find("전체","").size());
        assertEquals(1, NativeCatalog.find("수산","").size());
        assertEquals("demo-fruit", NativeCatalog.find("전체","색동").get(0).id);
        assertTrue(NativeCatalog.find("축산","과일").isEmpty());
    }
}
