package site.lexid.logshield;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/** Android/Java HTTP adapter. No WebView, no cleartext fallback or cross-host redirects. */
public final class ApiClient {
    public static final class ApiHttpException extends IllegalStateException {
        public final int statusCode;
        public ApiHttpException(int statusCode) {
            super("관리자 API 오류 " + statusCode);
            this.statusCode = statusCode;
        }
    }
    private final String baseUrl;
    private final String actor;
    private final String token;

    public ApiClient(String serverUrl, String actor, String token, boolean debugLab) {
        this.baseUrl = SecurityRules.normalizeServer(serverUrl, debugLab);
        if (actor == null || actor.trim().isEmpty() || actor.length() > 128) throw new IllegalArgumentException("관리자 아이디 오류");
        if (token == null || token.length() < 16) throw new IllegalArgumentException("관리자 인증키 오류");
        this.actor = actor.trim();
        this.token = token;
    }

    public JSONObject get(String path) throws Exception { return call("GET", path, null); }
    public JSONObject post(String path, JSONObject body) throws Exception { return call("POST", path, body); }
    public JSONObject put(String path, JSONObject body) throws Exception { return call("PUT", path, body); }
    public JSONObject delete(String path) throws Exception { return call("DELETE", path, null); }

    private JSONObject call(String verb, String path, JSONObject body) throws Exception {
        String safePath = SecurityRules.validatedPath(path);
        HttpURLConnection conn = (HttpURLConnection) new URL(baseUrl + safePath).openConnection();
        try {
            conn.setInstanceFollowRedirects(false);
            conn.setRequestMethod(verb);
            conn.setConnectTimeout(7000);
            conn.setReadTimeout(12000);
            conn.setUseCaches(false);
            conn.setRequestProperty("Accept", "application/json");
            conn.setRequestProperty("X-Actor", actor);
            conn.setRequestProperty("X-Admin-Key", token);
            if (body != null) {
                byte[] bytes = body.toString().getBytes(StandardCharsets.UTF_8);
                conn.setDoOutput(true);
                conn.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                try (OutputStream out = conn.getOutputStream()) { out.write(bytes); }
            }
            int status = conn.getResponseCode();
            InputStream raw = status >= 200 && status < 300 ? conn.getInputStream() : conn.getErrorStream();
            String reply = "";
            if (raw != null) {
                try (InputStream in = raw; ByteArrayOutputStream bytes = new ByteArrayOutputStream()) {
                    byte[] part = new byte[4096]; int n;
                    while ((n = in.read(part)) != -1) {
                        if (bytes.size() + n > 2_000_000) throw new IllegalStateException("응답 크기 초과");
                        bytes.write(part, 0, n);
                    }
                    reply = bytes.toString(StandardCharsets.UTF_8.name());
                }
            }
            if (status < 200 || status >= 300) {
                // Do not surface attacker-controlled server error bodies in privileged UI.
                throw new ApiHttpException(status);
            }
            return reply.isEmpty() ? new JSONObject() : new JSONObject(reply);
        } finally { conn.disconnect(); }
    }
}
