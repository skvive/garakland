plugins {
    id("com.android.application")
}

android {
    namespace = "site.lexid.garakland"
    compileSdk = 35

    defaultConfig {
        applicationId = "site.lexid.garakland"
        minSdk = 26
        targetSdk = 35
        versionCode = 2
        versionName = "0.2.0-native-dev"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    testOptions {
        animationsDisabled = true
    }
}

dependencies {
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test:core:1.6.1")
    androidTestImplementation("androidx.test:rules:1.6.1")
}
