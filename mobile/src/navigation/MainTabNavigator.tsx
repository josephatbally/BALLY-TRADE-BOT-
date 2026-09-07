
import React from 'react';

import {
  StyleSheet,
  View,
} from 'react-native';

import {
  createBottomTabNavigator,
} from '@react-navigation/bottom-tabs';

import {
  NativeStackScreenProps,
} from '@react-navigation/native-stack';

import {
  Gauge,
  CandlestickChart,
  Workflow,
  BriefcaseBusiness,
  UserRound,
} from 'lucide-react-native';

import DashboardScreen from '../screens/DashboardScreen';
import MarketsScreen from '../screens/MarketsScreen';
import ProfileScreen from '../screens/ProfileScreen';

const FlowScreen =
  require('../screens/FlowScreen').default as React.ComponentType<any>;

const TradesScreen =
  require('../screens/TradesScreen').default as React.ComponentType<any>;

import {
  AuthenticatedUser,
  RootStackParamList,
} from './navigationTypes';

import {useTheme} from '../theme/ThemeContext';

export type MainTabParamList = {
  Dashboard: AuthenticatedUser;
  Markets: AuthenticatedUser;
  Flow: AuthenticatedUser;
  Trades: AuthenticatedUser;
  Profile: AuthenticatedUser;
};

type MainTabNavigatorProps = NativeStackScreenProps<
  RootStackParamList,
  'MainTabs'
>;

const Tab = createBottomTabNavigator<MainTabParamList>();

/**
 * Profile icon
 *
 * Uses the same visual language as the other navigation icons.
 * The circular frame identifies the account/profile section.
 */
function ProfileTabIcon({
  color,
  focused,
}: {
  color: string;
  focused: boolean;
}) {
  return (
    <View
      style={[
        styles.profileIcon,
        {
          borderColor: focused ? color : 'transparent',
        },
      ]}
    >
      <UserRound
        size={18}
        color={color}
        strokeWidth={focused ? 2.2 : 1.8}
      />
    </View>
  );
}

export default function MainTabNavigator({
  route,
}: MainTabNavigatorProps) {
  const user = route.params;
  const {theme} = useTheme();
  const colors = theme.colors;

  return (
    <Tab.Navigator
      initialRouteName="Dashboard"
      screenOptions={({route: tabRoute}) => ({
        headerShown: false,
        tabBarHideOnKeyboard: true,

        /**
         * BALLY FLOW bottom navigation.
         *
         * Fixed futuristic navigation palette:
         *
         * Background: #0A0E18
         * Border:     #1B2435
         * Active:     #7083FF
         * Inactive:   #56627A
         */
        tabBarStyle: {
          backgroundColor: '#0A0E18',
          borderTopColor: '#1B2435',
          borderTopWidth: StyleSheet.hairlineWidth,
          height: 64,
          paddingTop: 5,
          paddingBottom: 5,
          elevation: 0,
          shadowOpacity: 0,
        },

        tabBarActiveTintColor: '#7083FF',
        tabBarInactiveTintColor: '#56627A',

        tabBarLabelStyle: {
          fontSize: 9,
          fontWeight: '800',
          letterSpacing: 0.4,
          marginTop: 1,
        },

        tabBarIconStyle: {
          marginBottom: 0,
        },

        tabBarItemStyle: {
          paddingVertical: 1,
        },

        tabBarIcon: ({focused, color}) => {
          const size = 19;
          const strokeWidth = focused ? 2.2 : 1.7;

          switch (tabRoute.name) {
            /**
             * DASHBOARD
             *
             * Gauge = portfolio/system overview.
             */
            case 'Dashboard':
              return (
                <Gauge
                  size={size}
                  color={color}
                  strokeWidth={strokeWidth}
                />
              );

            /**
             * MARKETS
             *
             * Candlestick chart = market analysis.
             */
            case 'Markets':
              return (
                <CandlestickChart
                  size={size}
                  color={color}
                  strokeWidth={strokeWidth}
                />
              );

            /**
             * FLOW
             *
             * Workflow icon = BALLY Trading Intelligence pipeline.
             */
            case 'Flow':
              return (
                <Workflow
                  size={size}
                  color={color}
                  strokeWidth={strokeWidth}
                />
              );

            /**
             * TRADES
             *
             * Briefcase/activity representation for actual
             * trading activity.
             */
            case 'Trades':
              return (
                <BriefcaseBusiness
                  size={size}
                  color={color}
                  strokeWidth={strokeWidth}
                />
              );

            /**
             * PROFILE
             *
             * Circular frame distinguishes the account area.
             */
            case 'Profile':
              return (
                <ProfileTabIcon
                  color={color}
                  focused={focused}
                />
              );

            default:
              return null;
          }
        },
      })}
    >
      {/* ============================================================
          DASHBOARD
      ============================================================ */}
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        initialParams={user}
        options={{
          tabBarLabel: 'Dashboard',
        }}
      />

      {/* ============================================================
          MARKETS
      ============================================================ */}
      <Tab.Screen
        name="Markets"
        component={MarketsScreen}
        initialParams={user}
        options={{
          tabBarLabel: 'Markets',
        }}
      />

      {/* ============================================================
          BALLY FLOW
      ============================================================ */}
      <Tab.Screen
        name="Flow"
        component={FlowScreen}
        initialParams={user}
        options={{
          tabBarLabel: 'Flow',
        }}
      />

      {/* ============================================================
          TRADES
      ============================================================ */}
      <Tab.Screen
        name="Trades"
        component={TradesScreen}
        initialParams={user}
        options={{
          tabBarLabel: 'Trades',
        }}
      />

      {/* ============================================================
          PROFILE
      ============================================================ */}
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        initialParams={user}
        options={{
          tabBarLabel: 'Profile',
        }}
      />
    </Tab.Navigator>
  );
}

const styles = StyleSheet.create({
  profileIcon: {
    width: 25,
    height: 25,
    borderRadius: 12.5,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
});