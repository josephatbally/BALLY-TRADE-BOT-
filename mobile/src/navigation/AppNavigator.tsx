
import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {createNativeStackNavigator} from '@react-navigation/native-stack';

import LoginScreen from '../screens/LoginScreenProviderOtp';
import BrokerSetupScreen from '../screens/BrokerSetupScreen';
import {useTheme} from '../theme/ThemeContext';
import MainTabNavigator from './MainTabNavigator';
import HistoryScreen from '../screens/HistoryScreen';
import NotificationsScreen from '../screens/NotificationsScreen';
import SettingsScreen from '../screens/SettingsScreen';
import ThemeSelectionScreen from '../screens/ThemeSelectionScreen';
import BotControlScreen from '../screens/BotControlScreen';
import TradingPreferencesScreen from '../screens/TradingPreferencesScreen';
import RiskConfigurationScreen from '../screens/RiskConfigurationScreen';
import SecurityScreen from '../screens/SecurityScreen';
import AccountInformationScreen from '../screens/AccountInformationScreen';
import FlowMarketSelectionScreen from '../screens/flow/FlowMarketSelectionScreen';
import FlowAnalysisScreen from '../screens/flow/FlowAnalysisScreen';
import FlowConfluenceScreen from '../screens/flow/FlowConfluenceScreen';
import FlowConfidenceScreen from '../screens/flow/FlowConfidenceScreen';
import FlowDecisionScreen from '../screens/flow/FlowDecisionScreen';
import FlowValidationScreen from '../screens/flow/FlowValidationScreen';
import FlowExecutionScreen from '../screens/flow/FlowExecutionScreen';
import SplashScreen from '../screens/SplashScreen';
import {RootStackParamList} from './navigationTypes';

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function AppNavigator() {
  const {theme} = useTheme();
  const navigationTheme = React.useMemo(() => ({
    dark: theme.isDark,
    colors: {primary: theme.colors.primary, background: theme.colors.background, card: theme.colors.surface, text: theme.colors.text, border: theme.colors.border, notification: theme.colors.danger},
    fonts: {
      regular: {fontFamily: 'System', fontWeight: '400' as const},
      bold: {fontFamily: 'System', fontWeight: '700' as const},
      heavy: {fontFamily: 'System', fontWeight: '900' as const},
      medium: {fontFamily: 'System', fontWeight: '500' as const},
    },
  }), [theme]);

  return (
    <NavigationContainer theme={navigationTheme}>
      <Stack.Navigator initialRouteName="Splash" screenOptions={{headerShown: false, animation: 'slide_from_right', contentStyle: {backgroundColor: theme.colors.background}, animationTypeForReplace: 'push'}}>
        <Stack.Screen name="Splash" component={SplashScreen}/>
        <Stack.Screen name="Login" component={LoginScreen}/>
        <Stack.Screen name="BrokerSetup" component={BrokerSetupScreen}/>
        <Stack.Screen name="MainTabs" component={MainTabNavigator}/>
        <Stack.Screen name="History" component={HistoryScreen}/>
        <Stack.Screen name="Notifications" component={NotificationsScreen}/>
        <Stack.Screen name="Settings" component={SettingsScreen}/>
        <Stack.Screen name="ThemeSelection" component={ThemeSelectionScreen}/>
        <Stack.Screen name="BotControl" component={BotControlScreen}/>
        <Stack.Screen name="TradingPreferences" component={TradingPreferencesScreen}/>
        <Stack.Screen name="RiskConfiguration" component={RiskConfigurationScreen}/>
        <Stack.Screen name="Security" component={SecurityScreen}/>
        <Stack.Screen name="AccountInformation" component={AccountInformationScreen}/>
        <Stack.Screen name="FlowMarketSelection" component={FlowMarketSelectionScreen}/>
        <Stack.Screen name="FlowAnalysis" component={FlowAnalysisScreen}/>
        <Stack.Screen name="FlowConfluence" component={FlowConfluenceScreen}/>
        <Stack.Screen name="FlowConfidence" component={FlowConfidenceScreen}/>
        <Stack.Screen name="FlowDecision" component={FlowDecisionScreen}/>
        <Stack.Screen name="FlowValidation" component={FlowValidationScreen}/>
        <Stack.Screen name="FlowExecution" component={FlowExecutionScreen}/>
      </Stack.Navigator>
    </NavigationContainer>
  );
}
