import React, { useEffect, useState } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import {
  Image,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { RootStackParamList } from "../navigation/navigationTypes";

type Props = NativeStackScreenProps<RootStackParamList, "AccountInformation">;

type InfoRowProps = {
  icon: string;
  title: string;
  value: string;
};

function InfoRow({ icon, title, value }: InfoRowProps) {
  return (
    <View style={styles.infoRow}>
      <View style={styles.rowIcon}>
        <Text style={styles.rowIconText}>{icon}</Text>
      </View>
      <View style={styles.rowContent}>
        <Text style={styles.rowLabel} allowFontScaling={false}>
          {title}
        </Text>
        <Text style={styles.rowValue} allowFontScaling={false}>
          {value}
        </Text>
      </View>
    </View>
  );
}

function SectionHeader({ title }: { title: string }) {
  return (
    <Text style={styles.sectionTitle} allowFontScaling={false}>
      {title}
    </Text>
  );
}

export default function AccountInformationScreen({ navigation, route }: Props) {
  const insets = useSafeAreaInsets();
  const [photoUri, setPhotoUri] = useState<string | null>(null);

  useEffect(() => {
    AsyncStorage.getItem('@bally_profile_photo')
      .then((saved) => {
        if (saved) setPhotoUri(saved);
      })
      .catch(() => {});
  }, []);
  const user = route.params;

  const firstName = user.firstName?.trim() || "Trader";
  const displayName = user.displayName?.trim() || firstName;
  const profileLetter = firstName.charAt(0).toUpperCase();

  const broker = user.broker;
  const brokerServer = broker?.server || "Exness-Trial7 (Demo)";
  const accountNumber = broker?.accountNumber || "DEMO-DESK";
  const currency = broker?.currency || "USD";
  const leverage = broker?.leverage ? `1:${broker.leverage}` : "1:500 (Auto)";

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      <View style={styles.glowTop} pointerEvents="none" />
      <View style={styles.glowBottom} pointerEvents="none" />

      {/* HEADER */}
      <View style={[styles.header, { paddingTop: Math.max(insets.top + 8, 20) }]}>
        <Pressable
          onPress={() => navigation.goBack()}
          style={({ pressed }) => [styles.backBtn, pressed && styles.backBtnPressed]}
          accessibilityRole="button"
          accessibilityLabel="Back"
        >
          <Text style={styles.backBtnText} allowFontScaling={false}>
            ←
          </Text>
        </Pressable>

        <View style={styles.headerTitleWrap}>
          <Text style={styles.headerTitle} allowFontScaling={false}>
            Account Credentials
          </Text>
          <Text style={styles.headerSubtitle} allowFontScaling={false}>
            IDENTITY & MT5 DESK PROFILES
          </Text>
        </View>

        <View style={styles.headerRightSpacer} />
      </View>

      <ScrollView
        contentContainerStyle={[
          styles.scrollContent,
          { paddingBottom: Math.max(insets.bottom + 24, 32) },
        ]}
        showsVerticalScrollIndicator={false}
      >
        {/* AVATAR HERO CARD */}
        <View style={styles.heroCard}>
          <View style={styles.avatarWrap}>
            {photoUri ? (
              <Image source={{ uri: photoUri }} style={styles.avatarImage} />
            ) : (
              <Text style={styles.avatarLetter} allowFontScaling={false}>
                {profileLetter}
              </Text>
            )}
          </View>

          <Text style={styles.heroName} allowFontScaling={false}>
            {displayName}
          </Text>
          <Text style={styles.heroEmail} allowFontScaling={false}>
            {user.email || "trader@ballyflow.com"}
          </Text>

          <View style={styles.statusBadge}>
            <View style={styles.statusDot} />
            <Text style={styles.statusBadgeText} allowFontScaling={false}>
              VERIFIED ACTIVE TRADER
            </Text>
          </View>
        </View>

        {/* 1. PERSONAL CREDENTIALS */}
        <SectionHeader title="PERSONAL IDENTITY CREDENTIALS" />
        <View style={styles.card}>
          <InfoRow icon="👤" title="FULL TRADER NAME" value={displayName} />
          <View style={styles.divider} />
          <InfoRow icon="✉️" title="VERIFIED EMAIL" value={user.email || "None"} />
          <View style={styles.divider} />
          <InfoRow
            icon="📱"
            title="PHONE NUMBER"
            value={user.phone || "+255 712 345 678"}
          />
          <View style={styles.divider} />
          <InfoRow
            icon="🌐"
            title="COUNTRY / REGION"
            value={user.countryCode ? `Country Code (${user.countryCode})` : "East Africa (+255)"}
          />
        </View>

        {/* 2. MT5 BROKERAGE CREDENTIALS */}
        <SectionHeader title="MT5 BROKERAGE CREDENTIALS" />
        <View style={styles.card}>
          <InfoRow icon="🏦" title="CONNECTED BROKER SERVER" value={brokerServer} />
          <View style={styles.divider} />
          <InfoRow icon="🔑" title="MT5 ACCOUNT NUMBER (LOGIN)" value={accountNumber} />
          <View style={styles.divider} />
          <InfoRow
            icon="💵"
            title="BASE CURRENCY (AUTO-DETECTED)"
            value={currency}
          />
          <View style={styles.divider} />
          <InfoRow
            icon="⚡"
            title="ACCOUNT LEVERAGE (AUTO-DETECTED)"
            value={leverage}
          />
          <View style={styles.divider} />
          <InfoRow
            icon="🛡️"
            title="EXECUTION BRIDGE STATUS"
            value="DIRECT PIPELINE ACTIVE"
          />
        </View>

        {/* RE-LINK BUTTON */}
        <Pressable
          style={({ pressed }) => [styles.relinkBtn, pressed && styles.relinkBtnPressed]}
          onPress={() => navigation.navigate("BrokerSetup", user)}
        >
          <Text style={styles.relinkBtnText} allowFontScaling={false}>
            RE-CONFIGURE MT5 BROKER CREDENTIALS
          </Text>
        </Pressable>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#05070D",
  },
  glowTop: {
    position: "absolute",
    width: 240,
    height: 240,
    borderRadius: 120,
    backgroundColor: "#7083FF14",
    top: -60,
    right: -40,
  },
  glowBottom: {
    position: "absolute",
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: "#35E68A10",
    bottom: -60,
    left: -40,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 20,
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#131D31",
  },
  backBtn: {
    width: 38,
    height: 38,
    borderRadius: 10,
    backgroundColor: "#0A0E18",
    borderWidth: 1,
    borderColor: "#1E293B",
    alignItems: "center",
    justifyContent: "center",
  },
  backBtnPressed: {
    opacity: 0.7,
  },
  backBtnText: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "700",
  },
  headerTitleWrap: {
    alignItems: "center",
  },
  headerTitle: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "800",
    letterSpacing: 0.8,
  },
  headerSubtitle: {
    color: "#64748B",
    fontSize: 9,
    fontWeight: "700",
    letterSpacing: 1.2,
    marginTop: 2,
  },
  headerRightSpacer: {
    width: 38,
  },
  scrollContent: {
    paddingHorizontal: 18,
    paddingTop: 18,
  },
  heroCard: {
    backgroundColor: "#0A0E18",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#1E293B",
    alignItems: "center",
    paddingVertical: 22,
    paddingHorizontal: 16,
    marginBottom: 20,
  },
  avatarWrap: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: "#7083FF20",
    borderWidth: 1.5,
    borderColor: "#7083FF",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
    overflow: "hidden",
  },
  avatarImage: {
    width: "100%",
    height: "100%",
    borderRadius: 34,
  },
  avatarLetter: {
    color: "#7083FF",
    fontSize: 26,
    fontWeight: "900",
  },
  heroName: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "800",
    letterSpacing: 0.5,
  },
  heroEmail: {
    color: "#7D8AA8",
    fontSize: 12,
    marginTop: 4,
    marginBottom: 12,
  },
  statusBadge: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#10B98118",
    borderWidth: 1,
    borderColor: "#10B98135",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: "#35E68A",
    marginRight: 6,
  },
  statusBadgeText: {
    color: "#35E68A",
    fontSize: 9,
    fontWeight: "800",
    letterSpacing: 1,
  },
  sectionTitle: {
    color: "#64748B",
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 1.2,
    marginBottom: 8,
    marginTop: 6,
    marginLeft: 4,
  },
  card: {
    backgroundColor: "#0A0E18",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#1E293B",
    paddingHorizontal: 14,
    paddingVertical: 4,
    marginBottom: 18,
  },
  infoRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 12,
  },
  rowIcon: {
    width: 34,
    height: 34,
    borderRadius: 8,
    backgroundColor: "#05070D",
    borderWidth: 1,
    borderColor: "#1E293B",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },
  rowIconText: {
    fontSize: 14,
  },
  rowContent: {
    flex: 1,
  },
  rowLabel: {
    color: "#64748B",
    fontSize: 9,
    fontWeight: "800",
    letterSpacing: 0.8,
  },
  rowValue: {
    color: "#E2E8F0",
    fontSize: 13,
    fontWeight: "700",
    marginTop: 2,
  },
  divider: {
    height: 1,
    backgroundColor: "#131D31",
  },
  relinkBtn: {
    height: 48,
    borderRadius: 12,
    backgroundColor: "#0A0E18",
    borderWidth: 1,
    borderColor: "#7083FF55",
    alignItems: "center",
    justifyContent: "center",
    marginTop: 4,
    marginBottom: 12,
  },
  relinkBtnPressed: {
    backgroundColor: "#7083FF18",
  },
  relinkBtnText: {
    color: "#7083FF",
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1,
  },
});
