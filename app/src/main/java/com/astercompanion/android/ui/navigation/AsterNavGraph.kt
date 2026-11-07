package com.astercompanion.android.ui.navigation

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.astercompanion.android.ui.components.AsterBottomNavigationBar
import com.astercompanion.android.ui.components.AsterTab
import com.astercompanion.android.ui.screens.awareness.AwarenessPanel
import com.astercompanion.android.ui.screens.chat.ChatScreen
import com.astercompanion.android.ui.screens.companion.CompanionStudioScreen
import com.astercompanion.android.ui.screens.memory.MemoriesScreen
import com.astercompanion.android.ui.screens.today.TodayScreen
import com.astercompanion.android.ui.screens.voice.VoiceCallScreen
import com.astercompanion.android.ui.theme.AsterBackground

object AsterDestinations {
    const val TODAY = "today"
    const val CHAT = "chat"
    const val MEMORY = "memory"
    const val COMPANION = "companion"
    const val AWARENESS = "awareness"
    const val VOICE_CALL = "voice_call"
}

@Composable
fun AsterCompanionApp(
    navController: NavHostController = rememberNavController()
) {
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route ?: AsterDestinations.TODAY

    val isBottomBarVisible = currentRoute in listOf(
        AsterDestinations.TODAY,
        AsterDestinations.CHAT,
        AsterDestinations.MEMORY,
        AsterDestinations.COMPANION
    )

    Scaffold(
        containerColor = AsterBackground,
        bottomBar = {
            if (isBottomBarVisible) {
                AsterBottomNavigationBar(
                    currentRoute = currentRoute,
                    onTabSelected = { tab ->
                        navController.navigate(tab.route) {
                            popUpTo(navController.graph.findStartDestination().id) {
                                saveState = true
                            }
                            launchSingleTop = true
                            restoreState = true
                        }
                    }
                )
            }
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            AsterNavGraph(navController = navController)
        }
    }
}

@Composable
fun AsterNavGraph(
    navController: NavHostController,
    startDestination: String = AsterDestinations.TODAY,
    modifier: Modifier = Modifier
) {
    NavHost(
        navController = navController,
        startDestination = startDestination,
        modifier = modifier
    ) {
        composable(AsterDestinations.TODAY) {
            TodayScreen(
                onNavigateToMemories = {
                    navController.navigate(AsterDestinations.MEMORY) {
                        launchSingleTop = true
                    }
                },
                onNavigateToChat = {
                    navController.navigate(AsterDestinations.CHAT) {
                        launchSingleTop = true
                    }
                },
                onNavigateToSettings = {
                    navController.navigate(AsterDestinations.COMPANION) {
                        launchSingleTop = true
                    }
                }
            )
        }

        composable(AsterDestinations.CHAT) {
            ChatScreen(
                onNavigateToVoiceCall = {
                    navController.navigate(AsterDestinations.VOICE_CALL) {
                        launchSingleTop = true
                    }
                },
                onNavigateToAwareness = {
                    navController.navigate(AsterDestinations.AWARENESS) {
                        launchSingleTop = true
                    }
                }
            )
        }

        composable(AsterDestinations.MEMORY) {
            MemoriesScreen()
        }

        composable(AsterDestinations.COMPANION) {
            CompanionStudioScreen(
                onNavigateToSettings = {
                    navController.navigate(AsterDestinations.AWARENESS) {
                        launchSingleTop = true
                    }
                }
            )
        }

        composable(AsterDestinations.AWARENESS) {
            AwarenessPanel(
                onDismiss = {
                    navController.popBackStack()
                }
            )
        }

        composable(AsterDestinations.VOICE_CALL) {
            VoiceCallScreen(
                onCallEnded = {
                    navController.popBackStack()
                }
            )
        }
    }
}
