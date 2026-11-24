package site.lexid.garakland;

import static org.junit.Assert.*;

import android.widget.LinearLayout;
import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.Test;
import org.junit.runner.RunWith;

@RunWith(AndroidJUnit4.class)
public final class SmokeTest {
    @Test
    public void nativeLauncherRendersBottomNavigation() {
        try (ActivityScenario<NativeActivity> scene =
                     ActivityScenario.launch(NativeActivity.class)) {
            scene.onActivity(activity -> {
                LinearLayout navigation = activity.findViewById(R.id.native_bottom_navigation);
                assertNotNull("Native bottom navigation is required", navigation);
                assertTrue("Native navigation must be visible", navigation.isShown());
                assertEquals("Five native tabs required", 5, navigation.getChildCount());
            });
        }
    }
}
