import React, { useState, useEffect } from "react";
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
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import AppLogo from "../components/branding/AppLogo";
import { BRANDING } from "../config/branding";
import { AuthenticatedUser, RootStackParamList } from "../navigation/navigationTypes";

type LoginScreenProps = NativeStackScreenProps<RootStackParamList, "Login">;

const COUNTRY_CODES = [
  { code: "+255", flag: "🇹🇿", label: "Tanzania (+255)" },
  { code: "+254", flag: "🇰🇪", label: "Kenya (+254)" },
  { code: "+1", flag: "🇺🇸", label: "USA/Canada (+1)" },
  { code: "+44", flag: "🇬🇧", label: "UK (+44)" },
  { code: "+971", flag: "🇦🇪", label: "UAE (+971)" },
  { code: "+27", flag: "🇿🇦", label: "South Africa (+27)" },
  { code: "+234", flag: "🇳🇬", label: "Nigeria (+234)" },
];

export default function LoginScreen({ navigation }: LoginScreenProps) {
  const insets = useSafeAreaInsets();

  // Step 1: Personal credentials, Step 2: OTP verification
  const [step, setStep] = useState<"credentials" | "otp">("credentials");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [countryCode, setCountryCode] = useState("+255");
  const [phone, setPhone] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [resendTimer, setResendTimer] = useState(45);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (step === "otp" && resendTimer > 0) {
      interval = setInterval(() => {
        setResendTimer((prev) => (prev > 0 ? prev - 1 : 0));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [step, resendTimer]);

  const handleSendVerification = () => {
    if (!fullName.trim()) {
      Alert.alert("Missing Name", "Please enter your full legal name.");
      return;
    }
    if (!email.trim() || !email.includes("@")) {
      Alert.alert("Invalid Email", "Please enter a valid email address.");
      return;
    }
    if (!phone.trim() || phone.length < 6) {
      Alert.alert("Invalid Phone", "Please enter your valid phone number.");
      return;
    }

    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setStep("otp");
      setResendTimer(45);
      Alert.alert(
        "Verification Code Dispatched",
        `A 6-digit security verification code has been dispatched to ${countryCode} ${phone}.`
      );
    }, 1200);
  };

  const handleVerifyOtp = () => {
    if (!otpCode.trim() || otpCode.length < 4) {
      Alert.alert("Invalid Code", "Please enter the 6-digit verification code.");
      return;
    }

    setLoading(true);

    setTimeout(() => {
      setLoading(false);
      const nameParts = fullName.trim().split(" ");
      const firstName = nameParts[0] || "Trader";

      const authenticatedUser: AuthenticatedUser = {
        id: email.trim().toLowerCase(),
        email: email.trim().toLowerCase(),
        firstName,
        displayName: fullName.trim(),
        phone: `${countryCode} ${phone.trim()}`,
        countryCode,
      };

      // Proceed to MT5 Broker setup
      navigation.replace("BrokerSetup", authenticatedUser);
    }, 1200);
  };

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      <View style={styles.glowTop} pointerEvents="none" />
      <View style={styles.glowBottom} pointerEvents="none" />

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView
          contentContainerStyle={[
            styles.scrollContent,
            {
              paddingTop: Math.max(insets.top, 24),
              paddingBottom: Math.max(insets.bottom, 24),
            },
          ]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* BRAND HEADER */}
          <View style={styles.header}>
            <AppLogo size={70} />
            <Text style={styles.brand} allowFontScaling={false}>
              {BRANDING.appName}
            </Text>
            <Text style={styles.tagline} allowFontScaling={false}>
              {BRANDING.tagline}
            </Text>
          </View>

          {/* STATUS PILL */}
          <View style={styles.statusRow}>
            <View style={styles.statusDot} />
            <Text style={styles.statusText} allowFontScaling={false}>
              {step === "credentials" ? "TRADER IDENTITY ACCESS" : "2FA CODE VERIFICATION"}
            </Text>
          </View>

          {/* CARD CONTAINER */}
          <View style={styles.card}>
            {step === "credentials" ? (
              <>
                <Text style={styles.welcome} allowFontScaling={false}>
                  Trader Sign In
                </Text>
                <Text style={styles.subtitle} allowFontScaling={false}>
                  Enter your verified personal credentials to access your trading cockpit.
                </Text>

                {/* FULL NAME */}
                <View style={styles.fieldContainer}>
                  <Text style={styles.fieldLabel} allowFontScaling={false}>
                    FULL TRADER NAME
                  </Text>
                  <TextInput
                    value={fullName}
                    onChangeText={setFullName}
                    placeholder="e.g. Josephat Bally"
                    placeholderTextColor="#64748B"
                    autoCapitalize="words"
                    style={styles.input}
                    allowFontScaling={false}
                  />
                </View>

                {/* EMAIL */}
                <View style={styles.fieldContainer}>
                  <Text style={styles.fieldLabel} allowFontScaling={false}>
                    EMAIL ADDRESS
                  </Text>
                  <TextInput
                    value={email}
                    onChangeText={setEmail}
                    placeholder="trader@ballyflow.com"
                    placeholderTextColor="#64748B"
                    autoCapitalize="none"
                    keyboardType="email-address"
                    style={styles.input}
                    allowFontScaling={false}
                  />
                </View>

                {/* PHONE & COUNTRY CODE */}
                <View style={styles.fieldContainer}>
                  <Text style={styles.fieldLabel} allowFontScaling={false}>
                    MOBILE PHONE NUMBER
                  </Text>
                  <View style={styles.phoneRow}>
                    <ScrollView
                      horizontal
                      showsHorizontalScrollIndicator={false}
                      style={styles.countryScroll}
                    >
                      {COUNTRY_CODES.map((item) => {
                        const active = item.code === countryCode;
                        return (
                          <TouchableOpacity
                            key={item.code}
                            style={[
                              styles.countryChip,
                              active && styles.countryChipActive,
                            ]}
                            onPress={() => setCountryCode(item.code)}
                          >
                            <Text style={styles.countryChipFlag}>
                              {item.flag}
                            </Text>
                            <Text
                              style={[
                                styles.countryChipText,
                                active && styles.countryChipTextActive,
                              ]}
                              allowFontScaling={false}
                            >
                              {item.code}
                            </Text>
                          </TouchableOpacity>
                        );
                      })}
                    </ScrollView>
                  </View>

                  <TextInput
                    value={phone}
                    onChangeText={setPhone}
                    placeholder="712 345 678"
                    placeholderTextColor="#64748B"
                    keyboardType="phone-pad"
                    style={styles.input}
                    allowFontScaling={false}
                  />
                </View>

                {/* SUBMIT BUTTON */}
                <TouchableOpacity
                  style={[styles.primaryBtn, loading && styles.primaryBtnDisabled]}
                  onPress={handleSendVerification}
                  disabled={loading}
                >
                  {loading ? (
                    <ActivityIndicator color="#FFFFFF" size="small" />
                  ) : (
                    <Text style={styles.primaryBtnText} allowFontScaling={false}>
                      CONTINUE TO VERIFY →
                    </Text>
                  )}
                </TouchableOpacity>
              </>
            ) : (
              <>
                <Text style={styles.welcome} allowFontScaling={false}>
                  Security Verification
                </Text>
                <Text style={styles.subtitle} allowFontScaling={false}>
                  Enter the 6-digit confirmation code dispatched to {countryCode} {phone}.
                </Text>

                {/* OTP INPUT */}
                <View style={styles.fieldContainer}>
                  <Text style={styles.fieldLabel} allowFontScaling={false}>
                    6-DIGIT VERIFICATION CODE
                  </Text>
                  <TextInput
                    value={otpCode}
                    onChangeText={setOtpCode}
                    placeholder="• • • • • •"
                    placeholderTextColor="#64748B"
                    keyboardType="number-pad"
                    maxLength={6}
                    style={[styles.input, styles.otpInput]}
                    allowFontScaling={false}
                  />
                </View>

                {/* RESEND ROW */}
                <View style={styles.resendRow}>
                  {resendTimer > 0 ? (
                    <Text style={styles.resendTimerText} allowFontScaling={false}>
                      Resend code in {resendTimer}s
                    </Text>
                  ) : (
                    <TouchableOpacity onPress={handleSendVerification}>
                      <Text style={styles.resendLinkText} allowFontScaling={false}>
                        Resend verification code
                      </Text>
                    </TouchableOpacity>
                  )}
                </View>

                {/* VERIFY BUTTON */}
                <TouchableOpacity
                  style={[styles.primaryBtn, loading && styles.primaryBtnDisabled]}
                  onPress={handleVerifyOtp}
                  disabled={loading}
                >
                  {loading ? (
                    <ActivityIndicator color="#FFFFFF" size="small" />
                  ) : (
                    <Text style={styles.primaryBtnText} allowFontScaling={false}>
                      VERIFY & LINK MT5 DESK →
                    </Text>
                  )}
                </TouchableOpacity>

                {/* BACK TO PHONE */}
                <TouchableOpacity
                  style={styles.backBtn}
                  onPress={() => setStep("credentials")}
                >
                  <Text style={styles.backBtnText} allowFontScaling={false}>
                    ← Edit phone number or email
                  </Text>
                </TouchableOpacity>
              </>
            )}
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#05070D",
  },
  flex: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 22,
    justifyContent: "center",
    paddingVertical: 30,
  },
  glowTop: {
    position: "absolute",
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: "#7083FF18",
    top: -80,
    right: -60,
  },
  glowBottom: {
    position: "absolute",
    width: 280,
    height: 280,
    borderRadius: 140,
    backgroundColor: "#35E68A14",
    bottom: -100,
    left: -70,
  },
  header: {
    alignItems: "center",
    marginBottom: 20,
  },
  brand: {
    color: "#FFFFFF",
    fontSize: 26,
    fontWeight: "900",
    letterSpacing: 3,
    marginTop: 12,
  },
  tagline: {
    color: "#7D8AA8",
    fontSize: 9,
    fontWeight: "700",
    letterSpacing: 1.8,
    marginTop: 6,
    textAlign: "center",
  },
  statusRow: {
    alignSelf: "center",
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 16,
    backgroundColor: "#10B98118",
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#10B98135",
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: "#35E68A",
    marginRight: 6,
  },
  statusText: {
    color: "#35E68A",
    fontSize: 9,
    fontWeight: "800",
    letterSpacing: 1.2,
  },
  card: {
    backgroundColor: "#0A0E18",
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "#1E293B",
    padding: 22,
  },
  welcome: {
    color: "#FFFFFF",
    fontSize: 22,
    fontWeight: "800",
    marginBottom: 6,
  },
  subtitle: {
    color: "#7D8AA8",
    fontSize: 12.5,
    lineHeight: 19,
    marginBottom: 20,
  },
  fieldContainer: {
    marginBottom: 16,
  },
  fieldLabel: {
    color: "#8995B1",
    fontSize: 9.5,
    fontWeight: "800",
    letterSpacing: 1.2,
    marginBottom: 8,
  },
  input: {
    height: 50,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#1E293B",
    backgroundColor: "#05070D",
    color: "#FFFFFF",
    paddingHorizontal: 14,
    fontSize: 13.5,
  },
  otpInput: {
    fontSize: 20,
    fontWeight: "800",
    letterSpacing: 6,
    textAlign: "center",
  },
  phoneRow: {
    marginBottom: 10,
  },
  countryScroll: {
    flexDirection: "row",
  },
  countryChip: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: "#05070D",
    borderWidth: 1,
    borderColor: "#1E293B",
    marginRight: 6,
  },
  countryChipActive: {
    borderColor: "#7083FF",
    backgroundColor: "#7083FF22",
  },
  countryChipFlag: {
    fontSize: 12,
    marginRight: 4,
  },
  countryChipText: {
    color: "#94A3B8",
    fontSize: 11,
    fontWeight: "700",
  },
  countryChipTextActive: {
    color: "#7083FF",
  },
  primaryBtn: {
    height: 52,
    borderRadius: 12,
    backgroundColor: "#334BFF",
    alignItems: "center",
    justifyContent: "center",
    marginTop: 8,
    shadowColor: "#334BFF",
    shadowOpacity: 0.35,
    shadowRadius: 10,
    elevation: 6,
  },
  primaryBtnDisabled: {
    opacity: 0.6,
  },
  primaryBtnText: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 1.5,
  },
  resendRow: {
    alignItems: "center",
    marginBottom: 16,
  },
  resendTimerText: {
    color: "#64748B",
    fontSize: 11,
    fontWeight: "600",
  },
  resendLinkText: {
    color: "#7083FF",
    fontSize: 11.5,
    fontWeight: "700",
  },
  backBtn: {
    alignItems: "center",
    marginTop: 16,
  },
  backBtnText: {
    color: "#64748B",
    fontSize: 11.5,
    fontWeight: "700",
  },
});
