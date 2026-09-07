import React, {useEffect} from 'react';
import {
  ActivityIndicator,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';

import AppLogo from '../components/branding/AppLogo';
import {BRANDING} from '../config/branding';
import {RootStackParamList} from '../navigation/navigationTypes';

type SplashScreenProps = NativeStackScreenProps<
  RootStackParamList,
  'Splash'
>;

export default function SplashScreen({
  navigation,
}: SplashScreenProps) {
  useEffect(() => {
    let active = true;

    const initializeApplication = async () => {
      /*
       * Central startup point.
       *
       * Future initialization can be added here without
       * putting application logic into the Splash UI.
       */
      await Promise.resolve();

      if (!active) {
        return;
      }

      navigation.replace('Login');
    };

    initializeApplication();

    return () => {
      active = false;
    };
  }, [navigation]);

  return (
    <View style={styles.root}>
      <StatusBar
        barStyle="light-content"
      />

      <View style={styles.glowTop} />
      <View style={styles.glowBottom} />

      <View style={styles.content}>
        <AppLogo size={112} />

        <Text style={styles.appName}>
          {BRANDING.appName}
        </Text>

        <Text style={styles.tagline}>
          {BRANDING.tagline}
        </Text>

        <View style={styles.status}>
          <ActivityIndicator
            size="small"
            color={BRANDING.colors.accent}
          />

          <Text style={styles.statusText}>
            INITIALIZING
          </Text>
        </View>
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          {BRANDING.appName.toUpperCase()}
        </Text>

        <Text style={styles.versionText}>
          SMART TRADING PLATFORM
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#05070D',
    alignItems: 'center',
    justifyContent: 'center',
  },

  glowTop: {
    position: 'absolute',
    width: 300,
    height: 300,
    borderRadius: 150,
    backgroundColor: '#101B5C',
    opacity: 0.24,
    top: -170,
    right: -100,
  },

  glowBottom: {
    position: 'absolute',
    width: 320,
    height: 320,
    borderRadius: 160,
    backgroundColor: '#17204A',
    opacity: 0.18,
    bottom: -190,
    left: -120,
  },

  content: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 30,
  },

  appName: {
    color: '#FFFFFF',
    fontSize: 31,
    fontWeight: '900',
    letterSpacing: 4,
    marginTop: 20,
  },

  tagline: {
    color: '#7D8AA8',
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 2,
    marginTop: 9,
    textAlign: 'center',
  },

  status: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 34,
  },

  statusText: {
    color: '#7083FF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1.8,
    marginLeft: 9,
  },

  footer: {
    position: 'absolute',
    bottom: 32,
    alignItems: 'center',
  },

  footerText: {
    color: '#424D64',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1.4,
  },

  versionText: {
    color: '#303A50',
    fontSize: 7,
    fontWeight: '700',
    letterSpacing: 1,
    marginTop: 5,
  },
});