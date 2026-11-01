package site.lexid.garakland;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import org.junit.Test;

public final class AppConfigTest {
    @Test public void entrypointUsesTrustedHttps() {
        assertTrue(AppConfig.isTrustedUrl(AppConfig.START_URL));
    }

    @Test public void externalUrlsAreNotEmbedded() {
        assertFalse(AppConfig.isTrustedUrl("http://garakland.lexid.site/market.html"));
        assertFalse(AppConfig.isTrustedUrl("https://garakland.lexid.site.evil.example"));
        assertFalse(AppConfig.isTrustedUrl("https://user@garakland.lexid.site"));
        assertFalse(AppConfig.isTrustedUrl("https://www.google.com/maps"));
        assertFalse(AppConfig.isTrustedUrl("javascript:alert(1)"));
    }
}
