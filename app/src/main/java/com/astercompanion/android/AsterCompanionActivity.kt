package com.astercompanion.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.astercompanion.android.ui.navigation.AsterCompanionApp
import com.astercompanion.android.ui.theme.AsterCompanionTheme

class AsterCompanionActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AsterCompanionTheme {
                AsterCompanionApp()
            }
        }
    }
}
