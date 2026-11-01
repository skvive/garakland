package site.lexid.garakland;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import android.webkit.WebView;
import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.Test;
import org.junit.runner.RunWith;

@RunWith(AndroidJUnit4.class)
public final class SmokeTest {
    @Test
    public void appLaunchesWithWebView() {
        try (ActivityScenario<MainActivity> scene = ActivityScenario.launch(MainActivity.class)) {
            scene.onActivity(activity -> {
                WebView view = activity.findViewById(R.id.browser);
                assertNotNull("WebView is required", view);
                assertTrue("WebView must be visible", view.isShown());
            });
        }
    }
}
