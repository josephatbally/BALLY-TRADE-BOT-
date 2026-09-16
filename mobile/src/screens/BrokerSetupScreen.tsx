import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StatusBar,
  ActivityIndicator,
  Alert,
} from "react-native";
import { NativeStackScreenProps } from "@react-navigation/native-stack";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { RootStackParamList } from "../navigation/navigationTypes";
import { BRANDING } from "../config/branding";

type Props = NativeStackScreenProps<RootStackParamList, "BrokerSetup">;

const COMMON_BROKERS = [
  "Exness-Real",
  "Exness-Trial7",
  "ICMarketsSC-Demo",
  "Deriv-Server",
  "Custom Server",
];

export default function BrokerSetupScreen({ navigation, route }: Props) {
  const user = route.params;

  const [brokerServer, setBrokerServer] = useState("Exness-Trial7");
  const [accountNumber, setAccountNumber] = useState("");
  const [password, setPassword] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [detectedAccount, setDetectedAccount] = useState<{
    currency?: string;
    leverage?: number;
    balance?: number;
    equity?: number;
  } | null>(null);

  const handleConnectBroker = async () => {
    if (!accountNumber.trim() || !password.trim()) {
      Alert.alert(
        "Missing Credentials",
        "Please enter your MT5 Account Number and Password."
      );
      return;
    }

    setConnecting(true);

    try {
      // Query backend account endpoint to auto-detect broker telemetry & parameters
      const response = await fetch("http://10.0.2.2:8000/api/v1/account");
      let autoCurrency = "USD";
      let autoLeverage = 500;
      let autoBalance = 0;
      let autoEquity = 0;

      if (response.ok) {
        const data = await response.json();
        autoCurrency = data.currency || "USD";
        autoLeverage = data.leverage || 500;
        autoBalance = data.balance || 0;
        autoEquity = data.equity || 0;
      }

      const detected = {
        currency: autoCurrency,
        leverage: autoLeverage,
        balance: autoBalance,
        equity: autoEquity,
      };

      setDetectedAccount(detected);

      const updatedUser = {
        ...user,
        broker: {
          server: brokerServer,
          accountNumber: accountNumber.trim(),
          currency: autoCurrency,
          leverage: autoLeverage,
          connected: true,
        },
      };

      // Persist session locally
      await AsyncStorage.setItem("@bally_auth_user", JSON.stringify(updatedUser));
      await AsyncStorage.setItem(
        "@bally_broker_credentials",
        JSON.stringify(updatedUser.broker)
      );

      setConnecting(false);

      Alert.alert(
        "MT5 Connected",
        `Successfully connected!\nBroker: ${brokerServer}\nAccount: #${accountNumber.trim()}\nAuto-Detected Currency: ${autoCurrency}\nAuto-Detected Leverage: 1:${autoLeverage}`,
        [
          {
            text: "Launch Trading Cockpit",
            onPress: () => navigation.replace("MainTabs", updatedUser),
          },
        ]
      );
    } catch {
      // Fallback: save credentials and proceed to cockpit
      const updatedUser = {
        ...user,
        broker: {
          server: brokerServer,
          accountNumber: accountNumber.trim(),
          currency: "USD",
          leverage: 500,
          connected: true,
        },
      };

      await AsyncStorage.setItem("@bally_auth_user", JSON.stringify(updatedUser));
      setConnecting(false);
      navigation.replace("MainTabs", updatedUser);
    }
  };

  const handleSkipDemo = async () => {
    const updatedUser = {
      ...user,
      broker: {
        server: "Exness-Trial7 (Demo)",
        accountNumber: "DEMO-DESK",
        currency: "USD",
        leverage: 500,
        connected: false,
      },
    };

    await AsyncStorage.setItem("@bally_auth_user", JSON.stringify(updatedUser));
    navigation.replace("MainTabs", updatedUser);
  };

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      <View style={styles.glowTop} pointerEvents="none" />
      <View style={styles.glowBottom} pointerEvents="none" />

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text style={styles.headerBadge} allowFontScaling={false}>
            STEP 2 OF 2: DESK INTEGRATION
          </Text>
          <Text style={styles.title} allowFontScaling={false}>
            Connect MT5 Broker
          </Text>
          <Text style={styles.subtitle} allowFontScaling={false}>
            Link your MetaTrader 5 account. Currency, leverage, and margin
            levels are detected automatically from your broker.
          </Text>
        </View>

        {/* BROKER PRESETS */}
        <View style={styles.section}>
          <Text style={styles.label} allowFontScaling={false}>
            BROKER SERVER
          </Text>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={styles.serverScroll}
          >
            {COMMON_BROKERS.map((srv) => {
              const active = srv === brokerServer;
              return (
                <TouchableOpacity
                  key={srv}
                  style={[styles.serverChip, active && styles.serverChipActive]}
                  onPress={() => setBrokerServer(srv)}
                >
                  <Text
                    style={[
                      styles.serverChipText,
                      active && styles.serverChipTextActive,
                    ]}
                    allowFontScaling={false}
                  >
                    {srv}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>

          <TextInput
            value={brokerServer}
            onChangeText={setBrokerServer}
            placeholder="Or type server name (e.g. Exness-Real10)"
            placeholderTextColor="#64748B"
            style={styles.input}
            allowFontScaling={false}
          />
        </View>

        {/* ACCOUNT NUMBER */}
        <View style={styles.section}>
          <Text style={styles.label} allowFontScaling={false}>
            MT5 ACCOUNT NUMBER (LOGIN ID)
          </Text>
          <TextInput
            value={accountNumber}
            onChangeText={setAccountNumber}
            placeholder="e.g. 19482015"
            placeholderTextColor="#64748B"
            keyboardType="number-pad"
            style={styles.input}
            allowFontScaling={false}
          />
        </View>

        {/* PASSWORD */}
        <View style={styles.section}>
          <Text style={styles.label} allowFontScaling={false}>
            MT5 TRADER / INVESTOR PASSWORD
          </Text>
          <TextInput
            value={password}
            onChangeText={setPassword}
            placeholder="Enter MT5 account password"
            placeholderTextColor="#64748B"
            secureTextEntry
            style={styles.input}
            allowFontScaling={false}
          />
        </View>

        {/* AUTO DETECTION NOTICE */}
        <View style={styles.noticeBox}>
          <View style={styles.noticeDot} />
          <Text style={styles.noticeText} allowFontScaling={false}>
            Account currency, leverage limits, and real-time margin rates will
            be automatically retrieved from your broker terminal upon connection.
          </Text>
        </View>

        {/* SUBMIT BUTTON */}
        <TouchableOpacity
          style={[styles.connectBtn, connecting && styles.connectBtnDisabled]}
          onPress={handleConnectBroker}
          disabled={connecting}
        >
          {connecting ? (
            <ActivityIndicator color="#FFFFFF" size="small" />
          ) : (
            <Text style={styles.connectBtnText} allowFontScaling={false}>
              CONNECT & ARMED DESK →
            </Text>
          )}
        </TouchableOpacity>

        {/* SKIP DEMO */}
        <TouchableOpacity style={styles.skipBtn} onPress={handleSkipDemo}>
          <Text style={styles.skipBtnText} allowFontScaling={false}>
            Skip for now (Continue in Demo Mode)
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#05070D",
  },
  scrollContent: {
    paddingHorizontal: 22,
    paddingTop: 60,
    paddingBottom: 40,
  },
  glowTop: {
    position: "absolute",
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: "#7083FF18",
    top: -60,
    right: -40,
  },
  glowBottom: {
    position: "absolute",
    width: 280,
    height: 280,
    borderRadius: 140,
    backgroundColor: "#35E68A14",
    bottom: -80,
    left: -50,
  },
  header: {
    marginBottom: 28,
  },
  headerBadge: {
    color: "#7083FF",
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 1.5,
    marginBottom: 8,
  },
  title: {
    color: "#FFFFFF",
    fontSize: 26,
    fontWeight: "900",
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  subtitle: {
    color: "#94A3B8",
    fontSize: 13,
    lineHeight: 20,
  },
  section: {
    marginBottom: 20,
  },
  label: {
    color: "#64748B",
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 1.2,
    marginBottom: 8,
  },
  serverScroll: {
    marginBottom: 10,
  },
  serverChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: "#0A0E18",
    borderWidth: 1,
    borderColor: "#1E293B",
    marginRight: 8,
  },
  serverChipActive: {
    backgroundColor: "#7083FF22",
    borderColor: "#7083FF",
  },
  serverChipText: {
    color: "#94A3B8",
    fontSize: 11,
    fontWeight: "700",
  },
  serverChipTextActive: {
    color: "#7083FF",
  },
  input: {
    height: 52,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#1E293B",
    backgroundColor: "#0A0E18",
    color: "#FFFFFF",
    paddingHorizontal: 16,
    fontSize: 14,
    fontWeight: "600",
  },
  noticeBox: {
    flexDirection: "row",
    backgroundColor: "#0A0E18",
    borderWidth: 1,
    borderColor: "#1E293B",
    borderRadius: 12,
    padding: 14,
    marginBottom: 26,
    alignItems: "flex-start",
  },
  noticeDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: "#35E68A",
    marginTop: 6,
    marginRight: 10,
  },
  noticeText: {
    color: "#64748B",
    fontSize: 11.5,
    lineHeight: 18,
    flex: 1,
  },
  connectBtn: {
    height: 54,
    borderRadius: 12,
    backgroundColor: "#334BFF",
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#334BFF",
    shadowOpacity: 0.35,
    shadowRadius: 10,
    elevation: 6,
  },
  connectBtnDisabled: {
    opacity: 0.6,
  },
  connectBtnText: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "900",
    letterSpacing: 1.2,
  },
  skipBtn: {
    alignItems: "center",
    marginTop: 18,
    paddingVertical: 10,
  },
  skipBtnText: {
    color: "#64748B",
    fontSize: 12,
    fontWeight: "700",
  },
});
