package site.lexid.logshield;

import java.net.URI;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/** Pure-Java security boundaries, runnable without the Android emulator. */
public final class SecurityRules {
    private SecurityRules() {}

    public static String normalizeServer(String value, boolean labMode) {
        if (value == null || value.trim().isEmpty()) throw new IllegalArgumentException("서버 주소가 필요합니다.");
        try {
            URI uri = URI.create(value.trim());
            String scheme = uri.getScheme();
            String host = uri.getHost();
            if (host == null || scheme == null || uri.getUserInfo() != null || uri.getFragment() != null
                    || uri.getQuery() != null || (uri.getPath() != null && !uri.getPath().isEmpty() && !uri.getPath().equals("/"))) {
                throw new IllegalArgumentException("도메인 루트 URL만 허용됩니다.");
            }
            boolean https = scheme.equalsIgnoreCase("https");
            boolean local = (host.equalsIgnoreCase("localhost") || host.equals("127.0.0.1") || host.equals("10.0.2.2"));
            if (!https && !(labMode && scheme.equalsIgnoreCase("http") && local)) {
                throw new IllegalArgumentException("보안을 위해 HTTPS만 허용됩니다.");
            }
            String authority = uri.getRawAuthority();
            if (authority == null || authority.contains("%"))
                throw new IllegalArgumentException("잘못된 서버 주소");
            // URI.getPort() is -1 even when a malformed port such as :99999 was supplied.
            int hostEnd = authority.startsWith("[") ? authority.indexOf(']') + 1 : authority.indexOf(':');
            if (hostEnd < 0) hostEnd = authority.length();
            boolean hasPort = hostEnd < authority.length();
            if ((hasPort && (authority.charAt(hostEnd) != ':' || uri.getPort() < 1)) || uri.getPort() > 65535 || uri.getPort() == 0)
                throw new IllegalArgumentException("잘못된 포트");
            String normalized = scheme.toLowerCase(Locale.ROOT) + "://" + host.toLowerCase(Locale.ROOT);
            if (uri.getPort() > 0) normalized += ":" + uri.getPort();
            return normalized;
        } catch (IllegalArgumentException ex) { throw ex; }
    }

    public static String validatedPath(String path) {
        if (path == null || !path.startsWith("/api/admin/") || path.contains("..") || path.contains("\\")
                || path.contains("//") || path.contains("?") || path.contains("#") || path.toLowerCase(Locale.ROOT).contains("%2f") || path.toLowerCase(Locale.ROOT).contains("%5c") || path.toLowerCase(Locale.ROOT).contains("%2e")) {
            throw new IllegalArgumentException("허용되지 않은 관리자 API 경로");
        }
        return path;
    }

    public static String segment(String value) {
        if (value == null || value.trim().isEmpty() || value.length() > 120)
            throw new IllegalArgumentException("잘못된 값");
        return URLEncoder.encode(value, StandardCharsets.UTF_8).replace("+", "%20");
    }

    public static boolean can(String[] permissions, String desired) {
        if (permissions == null) return false;
        for (String p : permissions) if (desired.equals(p)) return true;
        return false;
    }
}
