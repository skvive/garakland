package site.lexid.garakland;

import java.net.URI;
import java.net.URISyntaxException;

/** One trusted public origin; do not allow arbitrary hosts or embedded OAuth. */
public final class AppConfig {
    public static final String ORIGIN = "https://garakland.lexid.site";
    public static final String START_URL = ORIGIN + "/map.html";
    private AppConfig() {}

    public static String page(String relativePath) {
        if (relativePath == null || !relativePath.startsWith("/") ||
                relativePath.startsWith("//") || relativePath.contains("\\") ||
                relativePath.contains("#") || relativePath.contains("\n")) {
            throw new IllegalArgumentException("invalid relative path");
        }
        String url = ORIGIN + relativePath;
        if (!isTrustedUrl(url)) throw new IllegalArgumentException("invalid target");
        return url;
    }

    public static boolean isEmbeddedRoute(String path) {
        return "/map.html".equals(path) || "/indoor-map.html".equals(path) ||
                "/market-map.html".equals(path) || "/ar-quest.html".equals(path);
    }

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
