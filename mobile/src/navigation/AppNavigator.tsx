
import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {
  createNativeStackNavigator,
} from '@react-navigation/native-stack';

// Authentication
import LoginScreen from '../screens/LoginScreen';
import BrokerSetupScreen from '../screens/BrokerSetupScreen';

// Theme
import {useTheme} from '../theme/ThemeContext';

// Main application
import MainTabNavigator from './MainTabNavigator';

// General application screens
import HistoryScreen from '../screens/HistoryScreen';
import NotificationsScreen from '../screens/NotificationsScreen';
import SettingsScreen from '../screens/SettingsScreen';
import ThemeSelectionScreen from '../screens/ThemeSelectionScreen';
import BotControlScreen from '../screens/BotControlScreen';
import TradingPreferencesScreen from '../screens/TradingPreferencesScreen';
import RiskConfigurationScreen from '../screens/RiskConfigurationScreen';
import SecurityScreen from '../screens/SecurityScreen';
import AccountInformationScreen from '../screens/AccountInformationScreen';

// BALLY FLOW screens
import FlowMarketSelectionScreen from '../screens/flow/FlowMarketSelectionScreen';
import FlowAnalysisScreen from '../screens/flow/FlowAnalysisScreen';
import FlowConfluenceScreen from '../screens/flow/FlowConfluenceScreen';
import FlowConfidenceScreen from '../screens/flow/FlowConfidenceScreen';
import FlowDecisionScreen from '../screens/flow/FlowDecisionScreen';
import FlowValidationScreen from '../screens/flow/FlowValidationScreen';
import FlowExecutionScreen from '../screens/flow/FlowExecutionScreen';
import SplashScreen from '../screens/SplashScreen';

// Navigation types
import {RootStackParamList} from './navigationTypes';

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function AppNavigator() {
  const {theme} = useTheme();

  /**
   * React Navigation theme.
   *
   * This keeps the navigation system synchronized with
   * the BALLY FLOW application theme.
   */
  const navigationTheme = React.useMemo(
    () => ({
      dark: theme.isDark,

      colors: {
        primary: theme.colors.primary,
        background: theme.colors.background,
        card: theme.colors.surface,
        text: theme.colors.text,
        border: theme.colors.border,
        notification: theme.colors.danger,
      },

      fonts: {
        regular: {
          fontFamily: 'System',
          fontWeight: '400' as const,
        },
        bold: {
          fontFamily: 'System',
          fontWeight: '700' as const,
        },
        heavy: {
          fontFamily: 'System',
          fontWeight: '900' as const,
        },
        medium: {
          fontFamily: 'System',
          fontWeight: '500' as const,
        },
      },
    }),
    [theme],
  );

  return (
    <NavigationContainer theme={navigationTheme}>
      <Stack.Navigator
        initialRouteName="Splash"
        screenOptions={{
          headerShown: false,

          animation: 'slide_from_right',

          contentStyle: {
            backgroundColor: theme.colors.background,
          },

          animationTypeForReplace: 'push',
        }}
      >
        {/* ============================================================
            AUTHENTICATION
        ============================================================ */}
<Stack.Screen
  name="Splash"
  component={SplashScreen}
/>
        <Stack.Screen
          name="Login"
          component={LoginScreen}
        />
        <Stack.Screen
          name="BrokerSetup"
          component={BrokerSetupScreen}
        />

        {/* ============================================================
            MAIN APPLICATION
        ============================================================ */}

        <Stack.Screen
          name="MainTabs"
          component={MainTabNavigator}
        />

        {/* ============================================================
            GENERAL APPLICATION SCREENS
        ============================================================ */}

        <Stack.Screen
          name="History"
          component={HistoryScreen}
        />

        <Stack.Screen
          name="Notifications"
          component={NotificationsScreen}
        />

        <Stack.Screen
          name="Settings"
          component={SettingsScreen}
        />

        <Stack.Screen
          name="ThemeSelection"
          component={ThemeSelectionScreen}
        />

        <Stack.Screen
          name="BotControl"
          component={BotControlScreen}
        />

        <Stack.Screen
          name="TradingPreferences"
          component={TradingPreferencesScreen}
        />

        <Stack.Screen
          name="RiskConfiguration"
          component={RiskConfigurationScreen}
        />

        <Stack.Screen
          name="Security"
          component={SecurityScreen}
        />

        <Stack.Screen
          name="AccountInformation"
          component={AccountInformationScreen}
        />

        {/* ============================================================
            BALLY FLOW
            TRADING INTELLIGENCE PIPELINE
        ============================================================ */}

        {/* 01 — MARKET */}
        <Stack.Screen
          name="FlowMarketSelection"
          component={FlowMarketSelectionScreen}
        />

        {/* 02 — ANALYSIS */}
        <Stack.Screen
          name="FlowAnalysis"
          component={FlowAnalysisScreen}
        />

        {/* 03 — CONFLUENCE */}
        <Stack.Screen
          name="FlowConfluence"
          component={FlowConfluenceScreen}
        />

        {/* 04 — CONFIDENCE */}
        <Stack.Screen
          name="FlowConfidence"
          component={FlowConfidenceScreen}
        />

        {/* 05 — DECISION */}
        <Stack.Screen
          name="FlowDecision"
          component={FlowDecisionScreen}
        />

        {/* 06 — VALIDATION */}
        <Stack.Screen
          name="FlowValidation"
          component={FlowValidationScreen}
        />

        {/* 07 — EXECUTION */}
        <Stack.Screen
          name="FlowExecution"
          component={FlowExecutionScreen}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
