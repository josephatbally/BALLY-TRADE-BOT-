import React, { useEffect, useRef, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  Animated,
  StatusBar,
  Easing,
} from "react-native";
import { NativeStackScreenProps } from "@react-navigation/native-stack";
import AppLogo from "../components/branding/AppLogo";
import { BRANDING } from "../config/branding";
import { RootStackParamList } from "../navigation/navigationTypes";

type SplashScreenProps = NativeStackScreenProps<
  RootStackParamList,
  "Splash"
>;

const TELEMETRY_STAGES = [
  { time: 0, text: "INITIALIZING BALLY ENGINE & CORE PROTOCOLS..." },
  { time: 2200, text: "ESTABLISHING MT5 LIVE BROKER BRIDGE..." },
  { time: 4800, text: "SYNCING FLOW SCANNER & RISK GATES..." },
  { time: 7400, text: "CALIBRATING QUANTUM EXECUTION PIPELINE..." },
  { time: 9000, text: "SYSTEM ONLINE • ALL GATES ARMED" },
];

export default function SplashScreen({ navigation }: SplashScreenProps) {
  const [telemetryText, setTelemetryText] = useState(TELEMETRY_STAGES[0].text);

  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.92)).current;
  const pulseAnim = useRef(new Animated.Value(0.3)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    let active = true;
    const timeouts: NodeJS.Timeout[] = [];

    // 1. Entrance animation (fade & scale in)
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 900,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        friction: 7,
        tension: 40,
        useNativeDriver: true,
      }),
    ]).start();

    // 2. Ambient pulse glow loop
    const pulseLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 0.7,
          duration: 1800,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 0.3,
          duration: 1800,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    );
    pulseLoop.start();

    // 3. Smooth continuous progress bar across 9.2 seconds
    Animated.timing(progressAnim, {
      toValue: 1,
      duration: 9200,
      easing: Easing.bezier(0.25, 0.1, 0.25, 1),
      useNativeDriver: false,
    }).start();

    // 4. Staged telemetry checkpoints across 10 seconds
    TELEMETRY_STAGES.slice(1).forEach((stage) => {
      const t = setTimeout(() => {
        if (active) {
          setTelemetryText(stage.text);
        }
      }, stage.time);
      timeouts.push(t);
    });

    // 5. Navigate to Login at exactly 10.0 seconds
    const navTimeout = setTimeout(() => {
      if (active) {
        navigation.replace("Login");
      }
    }, 10000);
    timeouts.push(navTimeout);

    return () => {
      active = false;
      pulseLoop.stop();
      timeouts.forEach(clearTimeout);
    };
  }, [navigation, fadeAnim, scaleAnim, pulseAnim, progressAnim]);

  const progressWidth = progressAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ["0%", "100%"],
  });

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      {/* Dynamic ambient glowing orbs */}
      <Animated.View
        style={[styles.glowTop, { opacity: pulseAnim }]}
        pointerEvents="none"
      />
      <Animated.View
        style={[styles.glowBottom, { opacity: pulseAnim }]}
        pointerEvents="none"
      />

      <Animated.View
        style={[
          styles.content,
          {
            opacity: fadeAnim,
            transform: [{ scale: scaleAnim }],
          },
        ]}
      >
        <AppLogo size={116} />

        <Text style={styles.appName} allowFontScaling={false}>
          {BRANDING.appName}
        </Text>

        <Text style={styles.tagline} allowFontScaling={false}>
          {BRANDING.tagline}
        </Text>

        {/* 10-Second Quantum Progress Bar */}
        <View style={styles.progressBarBackground}>
          <Animated.View
            style={[styles.progressBarFill, { width: progressWidth }]}
          />
        </View>

        {/* Dynamic Telemetry Status */}
        <View style={styles.statusRow}>
          <View style={styles.statusDot} />
          <Text style={styles.statusText} allowFontScaling={false}>
            {telemetryText}
          </Text>
        </View>
      </Animated.View>

      {/* Footer Branding */}
      <View style={styles.footer}>
        <Text style={styles.footerText} allowFontScaling={false}>
          {BRANDING.appName.toUpperCase()} • BALLY QUANTUM SUITE
        </Text>
        <Text style={styles.versionText} allowFontScaling={false}>
          HIGH-FREQUENCY TRADING & FLOW ENGINE
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#05070D",
    alignItems: "center",
    justifyContent: "center",
  },
  glowTop: {
    position: "absolute",
    width: 320,
    height: 320,
    borderRadius: 160,
    backgroundColor: "#7083FF",
    top: -120,
    right: -90,
  },
  glowBottom: {
    position: "absolute",
    width: 340,
    height: 340,
    borderRadius: 170,
    backgroundColor: "#35E68A",
    bottom: -130,
    left: -100,
  },
  content: {
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 30,
    width: "100%",
  },
  appName: {
    color: "#FFFFFF",
    fontSize: 32,
    fontWeight: "900",
    letterSpacing: 4,
    marginTop: 22,
  },
  tagline: {
    color: "#7D8AA8",
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 2,
    marginTop: 8,
    textAlign: "center",
  },
  progressBarBackground: {
    width: 220,
    height: 3,
    backgroundColor: "#131D31",
    borderRadius: 2,
    marginTop: 36,
    overflow: "hidden",
  },
  progressBarFill: {
    height: "100%",
    backgroundColor: "#7083FF",
    borderRadius: 2,
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 18,
    paddingHorizontal: 16,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: "#35E68A",
    marginRight: 8,
  },
  statusText: {
    color: "#7083FF",
    fontSize: 9.5,
    fontWeight: "800",
    letterSpacing: 1.4,
    textAlign: "center",
  },
  footer: {
    position: "absolute",
    bottom: 32,
    alignItems: "center",
  },
  footerText: {
    color: "#424D64",
    fontSize: 8.5,
    fontWeight: "800",
    letterSpacing: 1.5,
  },
  versionText: {
    color: "#303A50",
    fontSize: 7.5,
    fontWeight: "700",
    letterSpacing: 1,
    marginTop: 4,
  },
});
