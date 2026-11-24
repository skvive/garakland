package site.lexid.garakland;

import static org.junit.Assert.*;
import org.junit.Test;

public final class AppConfigTest {
    @Test public void entrypointUsesTrustedHttps() {
        assertTrue(AppConfig.isTrustedUrl(AppConfig.START_URL));
        assertEquals("https://garakland.lexid.site/map.html", AppConfig.START_URL);
    }

    @Test public void externalUrlsAreNotEmbedded() {
        assertFalse(AppConfig.isTrustedUrl("http://garakland.lexid.site/map.html"));
        assertFalse(AppConfig.isTrustedUrl("https://garakland.lexid.site.evil.example"));
        assertFalse(AppConfig.isTrustedUrl("https://user@garakland.lexid.site"));
        assertFalse(AppConfig.isTrustedUrl("https://www.google.com/maps"));
        assertFalse(AppConfig.isTrustedUrl("javascript:alert(1)"));
    }

    @Test public void onlyNavigationFeaturesEmbedInsideApp() {
        assertTrue(AppConfig.isEmbeddedRoute("/map.html"));
        assertTrue(AppConfig.isEmbeddedRoute("/indoor-map.html"));
        assertFalse(AppConfig.isEmbeddedRoute("/login.html"));
        assertFalse(AppConfig.isEmbeddedRoute("/mypage.html"));
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectSchemeRelativeUrl() {
        AppConfig.page("//evil.test");
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectCrLfPath() {
        AppConfig.page("/map.html\nHost: evil.test");
    }
}
