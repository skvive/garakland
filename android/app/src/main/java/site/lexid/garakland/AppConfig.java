package site.lexid.garakland;

import java.net.URI;
import java.net.URISyntaxException;

public final class AppConfig {
    public static final String START_URL = "https://garakland.lexid.site/market.html";
    private AppConfig() {}

    public static boolean isTrustedUrl(String url) {
        try {
            URI uri = new URI(url);
            return "https".equalsIgnoreCase(uri.getScheme())
                    && "garakland.lexid.site".equalsIgnoreCase(uri.getHost())
                    && uri.getRawUserInfo() == null
                    && (uri.getPort() == -1 || uri.getPort() == 443);
        } catch (URISyntaxException | NullPointerException exception) {
            return false;
        }
    }
}
