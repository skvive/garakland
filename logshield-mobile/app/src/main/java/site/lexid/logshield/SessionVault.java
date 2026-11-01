package site.lexid.logshield;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.security.SecureRandom;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** API key is encrypted under an Android Keystore non-exportable AES-GCM key. */
public final class SessionVault {
    private static final String ALIAS = "logshield-console-key-v1";
    private static final String PREF = "logshield_device_local";
    private final SharedPreferences pref;
    public SessionVault(Context c) { pref = c.getSharedPreferences(PREF, Context.MODE_PRIVATE); }

    private SecretKey key() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore"); store.load(null);
        if (store.containsAlias(ALIAS)) return (SecretKey) store.getKey(ALIAS, null);
        KeyGenerator gen = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        gen.init(new KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true).setKeySize(256).build());
        return gen.generateKey();
    }
    public void save(String server, String user, String token) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key(), new SecureRandom());
        byte[] cipherText = cipher.doFinal(token.getBytes(StandardCharsets.UTF_8));
        pref.edit().putString("server", server).putString("actor", user)
                .putString("iv", Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP))
                .putString("secret", Base64.encodeToString(cipherText, Base64.NO_WRAP)).apply();
    }
    public String server() { return pref.getString("server", ""); }
    public String actor() { return pref.getString("actor", ""); }
    public boolean hasKey() { return pref.contains("secret") && pref.contains("iv"); }
    public String getToken() throws Exception {
        if (!hasKey()) throw new IllegalStateException("로그인이 필요합니다.");
        byte[] iv = Base64.decode(pref.getString("iv", ""), Base64.NO_WRAP);
        byte[] encrypted = Base64.decode(pref.getString("secret", ""), Base64.NO_WRAP);
        Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
        c.init(Cipher.DECRYPT_MODE, key(), new GCMParameterSpec(128, iv));
        return new String(c.doFinal(encrypted), StandardCharsets.UTF_8);
    }
    public void clear() { pref.edit().clear().apply(); }
}
