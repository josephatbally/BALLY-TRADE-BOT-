"""
Upgrade SplashScreen.tsx with 2.8s branding hold, glowing ambient animations,
dynamic system status telemetry, and a sleek neon progress bar.
"""

splash_file = "mobile/src/screens/SplashScreen.tsx"

splash_code = '''import React, { useEffect, useRef, useState } from 'react';
import {
  Animated,
  Dimensions,
  Easing,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import AppLogo from '../components/branding/AppLogo';
import { BRANDING } from '../config/branding';
import { RootStackParamList } from '../navigation/navigationTypes';

const { width } = Dimensions.get('window');

type SplashScreenProps = NativeStackScreenProps<RootStackParamList, 'Splash'>;

const STATUS_STEPS = [
  'INITIALIZING QUANTUM ENGINE...',
  'SYNCING MARKET RADAR & RISK GATES...',
  'SYSTEM ONLINE',
];

export default function SplashScreen({ navigation }: SplashScreenProps) {
  const [statusIndex, setStatusIndex] = useState(0);

  // Animation drivers
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.9)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    let active = true;

    // 1. Entrance Fade & Scale (0ms to 700ms)
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 700,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: 1,
        duration: 800,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
      Animated.timing(progressAnim, {
        toValue: 1,
        duration: 2700,
        easing: Easing.linear,
        useNativeDriver: false,
      }),
    ]).start();

    // 2. Ambient Orb Pulse Loop
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.15,
          duration: 1400,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1.0,
          duration: 1400,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    ).start();

    // 3. Step Through Telemetry Statuses
    const step1 = setTimeout(() => {
      if (active) setStatusIndex(1);
    }, 1100);

    const step2 = setTimeout(() => {
      if (active) setStatusIndex(2);
    }, 2100);

    // 4. Smooth Transition to Login after 2.8s
    const exitTimer = setTimeout(() => {
      if (!active) return;
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 350,
        easing: Easing.in(Easing.cubic),
        useNativeDriver: true,
      }).start(() => {
        if (active) {
          navigation.replace('Login');
        }
      });
    }, 2800);

    return () => {
      active = false;
      clearTimeout(step1);
      clearTimeout(step2);
      clearTimeout(exitTimer);
    };
  }, [navigation]);

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor="#05070D" />

      {/* Ambient Pulsing Glow Orbs */}
      <Animated.View
        style={[
          styles.ambientOrbBlue,
          {
            transform: [{ scale: pulseAnim }],
          },
        ]}
      />
      <Animated.View
        style={[
          styles.ambientOrbGreen,
          {
            transform: [{ scale: pulseAnim }],
          },
        ]}
      />

      {/* Central Brand Identity */}
      <Animated.View
        style={[
          styles.content,
          {
            opacity: fadeAnim,
            transform: [{ scale: scaleAnim }],
          },
        ]}
      >
        <View style={styles.logoWrapper}>
          <AppLogo size={108} />
          <View style={styles.logoHalo} />
        </View>

        <Text style={styles.appName} allowFontScaling={false}>
          {BRANDING.appName}
        </Text>

        <Text style={styles.tagline} allowFontScaling={false}>
          {BRANDING.tagline}
        </Text>

        {/* Telemetry Stage & Status */}
        <View style={styles.statusBox}>
          <View style={styles.statusIndicatorOrb} />
          <Text style={styles.statusText} allowFontScaling={false}>
            {STATUS_STEPS[statusIndex]}
          </Text>
        </View>

        {/* Neon Progress Track */}
        <View style={styles.progressTrack}>
          <Animated.View
            style={[
              styles.progressBar,
              {
                width: progressAnim.interpolate({
                  inputRange: [0, 1],
                  outputRange: ['0%', '100%'],
                }),
              },
            ]}
          />
        </View>
      </Animated.View>

      {/* Footer Branding */}
      <View style={styles.footer}>
        <Text style={styles.footerBrand} allowFontScaling={false}>
          QUANTUM EXECUTION ARCHITECTURE
        </Text>
        <Text style={styles.versionText} allowFontScaling={false}>
          v2.4.0 • HIGH CONVICTION TRADING
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
  ambientOrbBlue: {
    position: 'absolute',
    top: -40,
    left: -40,
    width: 320,
    height: 320,
    borderRadius: 160,
    backgroundColor: '#7083FF18',
  },
  ambientOrbGreen: {
    position: 'absolute',
    bottom: -60,
    right: -40,
    width: 340,
    height: 340,
    borderRadius: 170,
    backgroundColor: '#35E68A10',
  },
  content: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 28,
    width: '100%',
  },
  logoWrapper: {
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoHalo: {
    position: 'absolute',
    width: 140,
    height: 140,
    borderRadius: 70,
    backgroundColor: '#334BFF18',
    zIndex: -1,
  },
  appName: {
    color: '#FFFFFF',
    fontSize: 32,
    fontWeight: '900',
    letterSpacing: 6,
    marginTop: 22,
  },
  tagline: {
    color: '#7D8AA8',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 2.2,
    marginTop: 8,
    textAlign: 'center',
  },
  statusBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0A0E1890',
    borderColor: '#7083FF25',
    borderWidth: 1,
    paddingVertical: 7,
    paddingHorizontal: 16,
    borderRadius: 20,
    marginTop: 38,
  },
  statusIndicatorOrb: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 8,
  },
  statusText: {
    color: '#7083FF',
    fontSize: 9.5,
    fontWeight: '800',
    letterSpacing: 1.5,
  },
  progressTrack: {
    width: width * 0.55,
    height: 3,
    backgroundColor: '#0F1626',
    borderRadius: 2,
    marginTop: 20,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#35E68A',
    borderRadius: 2,
  },
  footer: {
    position: 'absolute',
    bottom: 34,
    alignItems: 'center',
  },
  footerBrand: {
    color: '#424D64',
    fontSize: 8.5,
    fontWeight: '900',
    letterSpacing: 2,
  },
  versionText: {
    color: '#283244',
    fontSize: 7.5,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginTop: 4,
  },
});
'''

with open(splash_file, "w", encoding="utf-8") as f:
    f.write(splash_code)

print("SUCCESS: SplashScreen.tsx updated with 2.8s branding animation.")
