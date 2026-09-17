import React, { useState, useEffect, useMemo } from "react";
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
  Modal,
  FlatList,
} from "react-native";
import { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import AsyncStorage from "@react-native-async-storage/async-storage";
import ReactNativeBiometrics from "react-native-biometrics";
import AppLogo from "../components/branding/AppLogo";
import { BRANDING } from "../config/branding";
import { AuthenticatedUser, RootStackParamList } from "../navigation/navigationTypes";
import {
  initiateRegistration,
  initiateLogin,
  verifySecurityCode,
  resendSecurityCode,
} from "../api/authApi";

type LoginScreenProps = NativeStackScreenProps<RootStackParamList, "Login">;

interface CountryItem {
  code: string;
  flag: string;
  name: string;
}

const GLOBAL_COUNTRIES: CountryItem[] = [
  { code: "+255", flag: "🇹🇿", name: "Tanzania" },
  { code: "+254", flag: "🇰🇪", name: "Kenya" },
  { code: "+256", flag: "🇺🇬", name: "Uganda" },
  { code: "+250", flag: "🇷🇼", name: "Rwanda" },
  { code: "+234", flag: "🇳🇬", name: "Nigeria" },
  { code: "+27", flag: "🇿🇦", name: "South Africa" },
  { code: "+233", flag: "🇬🇭", name: "Ghana" },
  { code: "+20", flag: "🇪🇬", name: "Egypt" },
  { code: "+971", flag: "🇦🇪", name: "United Arab Emirates" },
  { code: "+1", flag: "🇺🇸", name: "United States" },
  { code: "+1", flag: "🇨🇦", name: "Canada" },
  { code: "+44", flag: "🇬🇧", name: "United Kingdom" },
  { code: "+49", flag: "🇩🇪", name: "Germany" },
  { code: "+33", flag: "🇫🇷", name: "France" },
  { code: "+39", flag: "🇮🇹", name: "Italy" },
  { code: "+34", flag: "🇪🇸", name: "Spain" },
  { code: "+31", flag: "🇳🇱", name: "Netherlands" },
  { code: "+41", flag: "🇨🇭", name: "Switzerland" },
  { code: "+91", flag: "🇮🇳", name: "India" },
  { code: "+86", flag: "🇨🇳", name: "China" },
  { code: "+81", flag: "🇯🇵", name: "Japan" },
  { code: "+82", flag: "🇰🇷", name: "South Korea" },
  { code: "+65", flag: "🇸🇬", name: "Singapore" },
  { code: "+60", flag: "🇲🇾", name: "Malaysia" },
  { code: "+61", flag: "🇦🇺", name: "Australia" },
  { code: "+64", flag: "🇳🇿", name: "New Zealand" },
  { code: "+966", flag: "🇸🇦", name: "Saudi Arabia" },
  { code: "+974", flag: "🇶🇦", name: "Qatar" },
  { code: "+965", flag: "🇰🇼", name: "Kuwait" },
  { code: "+968", flag: "🇴🇲", name: "Oman" },
  { code: "+90", flag: "🇹🇷", name: "Turkey" },
  { code: "+55", flag: "🇧🇷", name: "Brazil" },
  { code: "+52", flag: "🇲🇽", name: "Mexico" },
  { code: "+54", flag: "🇦🇷", name: "Argentina" },
  { code: "+265", flag: "🇲🇼", name: "Malawi" },
  { code: "+260", flag: "🇿🇲", name: "Zambia" },
  { code: "+263", flag: "🇿🇼", name: "Zimbabwe" },
  { code: "+243", flag: "🇨🇩", name: "DR Congo" },
  { code: "+251", flag: "🇪🇹", name: "Ethiopia" },
  { code: "+237", flag: "🇨🇲", name: "Cameroon" },
  { code: "+225", flag: "🇨🇮", name: "Ivory Coast" },
  { code: "+221", flag: "🇸🇳", name: "Senegal" },
];

export default function LoginScreen({ navigation }: LoginScreenProps) {
  const insets = useSafeAreaInsets();

  // Navigation tab mode: 'signin' | 'register'
  const [authMode, setAuthMode] = useState<"signin" | "register">("signin");
  // Step: 'credentials' | 'otp'
  const [step, setStep] = useState<"credentials" | "otp">("credentials");

  // Form fields
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [loginIdentifier, setLoginIdentifier] = useState("");
  const [selectedCountry, setSelectedCountry] = useState<CountryItem>(GLOBAL_COUNTRIES[0]);
  const [phone, setPhone] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [rememberMe, setRememberMe] = useState(true);

  // Country Search Modal
  const [countryModalVisible, setCountryModalVisible] = useState(false);
  const [countrySearch, setCountrySearch] = useState("");

  // Optional Biometrics State
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  const [savedUserSession, setSavedUserSession] = useState<AuthenticatedUser | null>(null);

  // Execution state
  const [loading, setLoading] = useState(false);
  const [resendTimer, setResendTimer] = useState(45);
  const [activeIdentifier, setActiveIdentifier] = useState("");
  const [devHintCode, setDevHintCode] = useState<string | null>(null);

  // 1. Check for Remember Me credentials and optional biometrics on load
  useEffect(() => {
    let mounted = true;

    const checkStoredData = async () => {
      try {
        const [remembered, storedUser, bioEnabled] = await Promise.all([
          AsyncStorage.getItem("@bally_remembered_identifier"),
          AsyncStorage.getItem("@bally_auth_user"),
          AsyncStorage.getItem("@bally_biometric_enabled"),
        ]);

        if (mounted && remembered) {
          setLoginIdentifier(remembered);
          setEmail(remembered);
        }

        if (mounted && storedUser && bioEnabled === "true") {
          try {
            const parsed = JSON.parse(storedUser);
            if (parsed && (parsed.email || parsed.id)) {
              setSavedUserSession(parsed);
              const rnBiometrics = new ReactNativeBiometrics();
              const { available } = await rnBiometrics.isSensorAvailable();
              if (mounted && available) {
                setBiometricAvailable(true);
              }
            }
          } catch {
            // ignore JSON parse error
          }
        }
      } catch {
        // ignore read error
      }
    };

    checkStoredData();
    return () => {
      mounted = false;
    };
  }, []);

  // 2. OTP Timer countdown
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (step === "otp" && resendTimer > 0) {
      interval = setInterval(() => {
        setResendTimer((prev) => (prev > 0 ? prev - 1 : 0));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [step, resendTimer]);

  // Filter countries for modal
  const filteredCountries = useMemo(() => {
    const q = countrySearch.trim().toLowerCase();
    if (!q) return GLOBAL_COUNTRIES;
    return GLOBAL_COUNTRIES.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.code.includes(q) ||
        c.code.replace("+", "").includes(q)
    );
  }, [countrySearch]);

  // OPTIONAL 1-TAP BIOMETRIC SIGN-IN (Never blocks or prohibits standard sign-in/registration)
  const handleOptionalBiometricSignIn = async () => {
    if (!savedUserSession) return;
    try {
      const rnBiometrics = new ReactNativeBiometrics();
      const promptRes = await rnBiometrics.simplePrompt({
        promptMessage: "Sign in to BALLY FLOW with Biometrics",
        cancelButtonText: "Use Verification Code",
      });

      if (promptRes.success) {
        // Authenticated successfully via biometrics
        navigation.replace("MainTabs", savedUserSession);
      }
    } catch {
      // User cancelled or sensor failure: seamlessly stay on login screen
    }
  };

  // SEND VERIFICATION CODE (Sign-in vs Register)
  const handleSendVerification = async () => {
    if (authMode === "signin") {
      const iden = loginIdentifier.trim();
      if (!iden) {
        Alert.alert("Input Required", "Please enter your registered email address or phone number.");
        return;
      }

      setLoading(true);
      try {
        if (rememberMe) {
          await AsyncStorage.setItem("@bally_remembered_identifier", iden);
        } else {
          await AsyncStorage.removeItem("@bally_remembered_identifier");
        }

        const res = await initiateLogin({
          identifier: iden,
          channel: "email",
        });

        setActiveIdentifier(res.identifier || iden);
        if (res.dev_code) setDevHintCode(res.dev_code);
        setStep("otp");
        setResendTimer(45);

        const notice = res.email_sent
          ? `A 6-digit verification code has been dispatched to ${res.identifier}. Check your Gmail inbox or spam folder.`
          : `Verification code generated.\n\nCode: ${res.dev_code || "Logged to server terminal"}\n\n(Displayed in backend Uvicorn console)`;

        Alert.alert("Verification Dispatched", notice);
      } catch (err: any) {
        Alert.alert(
          "Sign In Notice",
          err?.message || "Failed to initiate sign-in. Check your server connection."
        );
      } finally {
        setLoading(false);
      }
    } else {
      // Register Mode
      if (!fullName.trim()) {
        Alert.alert("Missing Name", "Please enter your full legal name.");
        return;
      }
      if (!email.trim() || !email.includes("@")) {
        Alert.alert("Invalid Email", "Please enter a valid email address.");
        return;
      }
      if (!phone.trim() || phone.length < 5) {
        Alert.alert("Invalid Phone", "Please enter your mobile phone number.");
        return;
      }

      setLoading(true);
      try {
        if (rememberMe) {
          await AsyncStorage.setItem("@bally_remembered_identifier", email.trim().toLowerCase());
        }

        const res = await initiateRegistration({
          full_name: fullName.trim(),
          email: email.trim().toLowerCase(),
          phone: phone.trim(),
          country_code: selectedCountry.code,
          channel: "email",
        });

        setActiveIdentifier(email.trim().toLowerCase());
        if (res.dev_code) setDevHintCode(res.dev_code);
        setStep("otp");
        setResendTimer(45);

        const notice = res.email_sent
          ? `A 6-digit verification code has been dispatched to ${email.trim()}. Check your Gmail inbox or spam folder.`
          : `Verification code generated.\n\nCode: ${res.dev_code || "Logged to server terminal"}\n\n(Displayed in backend Uvicorn console)`;

        Alert.alert("Account Registration", notice);
      } catch (err: any) {
        Alert.alert(
          "Registration Error",
          err?.message || "Failed to reach authentication backend. Ensure FastAPI server is running."
        );
      } finally {
        setLoading(false);
      }
    }
  };

  // VERIFY 6-DIGIT OTP
  const handleVerifyOtp = async () => {
    if (!otpCode.trim() || otpCode.length < 4) {
      Alert.alert("Invalid Code", "Please enter the 6-digit verification code.");
      return;
    }

    setLoading(true);
    try {
      const idenToVerify = activeIdentifier || (authMode === "signin" ? loginIdentifier : email);
      const res = await verifySecurityCode({
        identifier: idenToVerify.trim().toLowerCase(),
        code: otpCode.trim(),
      });

      const nameParts = (res.user?.full_name || fullName.trim() || "Trader").split(" ");
      const firstName = nameParts[0] || "Trader";

      const authenticatedUser: AuthenticatedUser = {
        id: String(res.user?.id || idenToVerify.trim().toLowerCase()),
        email: res.user?.email || idenToVerify.trim().toLowerCase(),
        firstName,
        displayName: res.user?.full_name || fullName.trim() || firstName,
        phone: res.user?.phone || `${selectedCountry.code} ${phone.trim()}`,
        countryCode: res.user?.country_code || selectedCountry.code,
      };

      // Proceed to MT5 Broker setup
      navigation.replace("BrokerSetup", authenticatedUser);
    } catch (err: any) {
      Alert.alert(
        "Verification Failed",
        err?.message || "The verification code entered is invalid or has expired."
      );
    } finally {
      setLoading(false);
    }
  };

  // RESEND OTP
  const handleResend = async () => {
    if (resendTimer > 0) return;
    setLoading(true);
    try {
      const idenToResend = activeIdentifier || (authMode === "signin" ? loginIdentifier : email);
      const res = await resendSecurityCode({
        identifier: idenToResend.trim().toLowerCase(),
        channel: "email",
      });
      setResendTimer(45);
      if (res.dev_code) setDevHintCode(res.dev_code);

      Alert.alert(
        "Code Resent",
        `A fresh 6-digit code has been generated.\n${
          res.email_sent ? "Dispatched to your email inbox." : `Code: ${res.dev_code || "Check backend terminal."}`
        }`
      );
    } catch (err: any) {
      Alert.alert("Resend Failed", err?.message || "Unable to resend code right now.");
    } finally {
      setLoading(false);
    }
  };

  const handleHelpPress = () => {
    Alert.alert(
      "BALLY FLOW Security Access",
      "BALLY FLOW uses passwordless institutional authentication with 6-digit OTP verification codes sent securely to your Gmail address or registered phone number.\n\nIf you have forgotten your registered details, contact system administrator."
    );
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
              {step === "credentials" ? "ZERO-TRUST TRADER PORTAL" : "2FA CODE VERIFICATION"}
            </Text>
          </View>

          {/* CARD CONTAINER */}
          <View style={styles.card}>
            {step === "credentials" ? (
              <>
                {/* MODE SWITCHER TABS: SIGN IN vs CREATE ACCOUNT */}
                <View style={styles.tabContainer}>
                  <TouchableOpacity
                    style={[styles.tabButton, authMode === "signin" && styles.tabButtonActive]}
                    onPress={() => setAuthMode("signin")}
                  >
                    <Text
                      style={[styles.tabText, authMode === "signin" && styles.tabTextActive]}
                      allowFontScaling={false}
                    >
                      Sign In
                    </Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[styles.tabButton, authMode === "register" && styles.tabButtonActive]}
                    onPress={() => setAuthMode("register")}
                  >
                    <Text
                      style={[styles.tabText, authMode === "register" && styles.tabTextActive]}
                      allowFontScaling={false}
                    >
                      Create Account
                    </Text>
                  </TouchableOpacity>
                </View>

                {/* OPTIONAL 1-TAP BIOMETRIC PROMPT (Strictly Optional, Never Blocks) */}
                {authMode === "signin" && biometricAvailable && savedUserSession ? (
                  <TouchableOpacity
                    style={styles.biometricQuickBtn}
                    onPress={handleOptionalBiometricSignIn}
                  >
                    <View style={styles.biometricIconBox}>
                      <Text style={styles.biometricIconText}>⚡</Text>
                    </View>
                    <View style={styles.biometricTextBox}>
                      <Text style={styles.biometricTitle} allowFontScaling={false}>
                        Instant Biometric Sign In
                      </Text>
                      <Text style={styles.biometricSubtitle} allowFontScaling={false}>
                        Tap to unlock for {savedUserSession.email}
                      </Text>
                    </View>
                    <Text style={styles.biometricArrow}>›</Text>
                  </TouchableOpacity>
                ) : null}

                {authMode === "signin" ? (
                  <>
                    <Text style={styles.welcome} allowFontScaling={false}>
                      Welcome Back
                    </Text>
                    <Text style={styles.subtitle} allowFontScaling={false}>
                      Enter your registered Gmail or phone to receive a 6-digit verification code.
                    </Text>

                    {/* IDENTIFIER FIELD */}
                    <View style={styles.fieldContainer}>
                      <Text style={styles.fieldLabel} allowFontScaling={false}>
                        EMAIL OR PHONE NUMBER
                      </Text>
                      <TextInput
                        value={loginIdentifier}
                        onChangeText={setLoginIdentifier}
                        placeholder="e.g. trader@gmail.com"
                        placeholderTextColor="#64748B"
                        autoCapitalize="none"
                        keyboardType="email-address"
                        style={styles.input}
                        allowFontScaling={false}
                      />
                    </View>
                  </>
                ) : (
                  <>
                    <Text style={styles.welcome} allowFontScaling={false}>
                      Register Cockpit
                    </Text>
                    <Text style={styles.subtitle} allowFontScaling={false}>
                      Enter your details to create an institutional trader account.
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
                        GMAIL / EMAIL ADDRESS
                      </Text>
                      <TextInput
                        value={email}
                        onChangeText={setEmail}
                        placeholder="josephatbally5@gmail.com"
                        placeholderTextColor="#64748B"
                        autoCapitalize="none"
                        keyboardType="email-address"
                        style={styles.input}
                        allowFontScaling={false}
                      />
                    </View>

                    {/* PHONE WITH COUNTRY CODE SELECTOR ARROW BUTTON */}
                    <View style={styles.fieldContainer}>
                      <Text style={styles.fieldLabel} allowFontScaling={false}>
                        MOBILE PHONE NUMBER
                      </Text>

                      <View style={styles.phoneInputRow}>
                        {/* Country Code Selector Button with Arrow */}
                        <TouchableOpacity
                          style={styles.countryPickerButton}
                          onPress={() => {
                            setCountrySearch("");
                            setCountryModalVisible(true);
                          }}
                        >
                          <Text style={styles.countryPickerFlag}>{selectedCountry.flag}</Text>
                          <Text style={styles.countryPickerCode} allowFontScaling={false}>
                            {selectedCountry.code}
                          </Text>
                          <Text style={styles.countryPickerArrow}>▼</Text>
                        </TouchableOpacity>

                        {/* Phone Number Input */}
                        <TextInput
                          value={phone}
                          onChangeText={setPhone}
                          placeholder="712 345 678"
                          placeholderTextColor="#64748B"
                          keyboardType="phone-pad"
                          style={[styles.input, styles.phoneTextInput]}
                          allowFontScaling={false}
                        />
                      </View>
                    </View>
                  </>
                )}

                {/* REMEMBER ME & HELP ROW */}
                <View style={styles.metaRow}>
                  <TouchableOpacity
                    style={styles.rememberMeRow}
                    onPress={() => setRememberMe(!rememberMe)}
                  >
                    <View style={[styles.checkbox, rememberMe && styles.checkboxActive]}>
                      {rememberMe ? <Text style={styles.checkmark}>✓</Text> : null}
                    </View>
                    <Text style={styles.rememberMeText} allowFontScaling={false}>
                      Remember login
                    </Text>
                  </TouchableOpacity>

                  <TouchableOpacity onPress={handleHelpPress}>
                    <Text style={styles.helpLinkText} allowFontScaling={false}>
                      Need help?
                    </Text>
                  </TouchableOpacity>
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
                      {authMode === "signin" ? "SEND VERIFICATION CODE →" : "CREATE ACCOUNT & VERIFY →"}
                    </Text>
                  )}
                </TouchableOpacity>
              </>
            ) : (
              <>
                {/* STEP 2: OTP VERIFICATION */}
                <Text style={styles.welcome} allowFontScaling={false}>
                  Security Verification
                </Text>
                <Text style={styles.subtitle} allowFontScaling={false}>
                  Enter the 6-digit confirmation code dispatched to {activeIdentifier || email}.
                </Text>

                {devHintCode ? (
                  <View style={styles.devHintBox}>
                    <Text style={styles.devHintLabel} allowFontScaling={false}>
                      SYSTEM OTP CODE:
                    </Text>
                    <Text style={styles.devHintValue} allowFontScaling={false}>
                      {devHintCode}
                    </Text>
                  </View>
                ) : null}

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
                    <TouchableOpacity onPress={handleResend}>
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

                {/* BACK TO CREDENTIALS */}
                <TouchableOpacity
                  style={styles.backBtn}
                  onPress={() => setStep("credentials")}
                >
                  <Text style={styles.backBtnText} allowFontScaling={false}>
                    ← Edit login credentials
                  </Text>
                </TouchableOpacity>
              </>
            )}
          </View>
        </ScrollView>
      </KeyboardAvoidingView>

      {/* SEARCHABLE COUNTRY CODE MODAL */}
      <Modal
        visible={countryModalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setCountryModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View
            style={[
              styles.modalContent,
              { paddingBottom: Math.max(insets.bottom, 20) },
            ]}
          >
            {/* Modal Header */}
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle} allowFontScaling={false}>
                Select Country Dial Code
              </Text>
              <TouchableOpacity
                style={styles.modalCloseBtn}
                onPress={() => setCountryModalVisible(false)}
              >
                <Text style={styles.modalCloseText}>✕</Text>
              </TouchableOpacity>
            </View>

            {/* Modal Search Bar */}
            <View style={styles.modalSearchContainer}>
              <TextInput
                value={countrySearch}
                onChangeText={setCountrySearch}
                placeholder="Search country or dial code..."
                placeholderTextColor="#64748B"
                style={styles.modalSearchInput}
                autoFocus={false}
                allowFontScaling={false}
              />
            </View>

            {/* Country List */}
            <FlatList
              data={filteredCountries}
              keyExtractor={(item) => `${item.code}-${item.name}`}
              showsVerticalScrollIndicator={true}
              keyboardShouldPersistTaps="handled"
              renderItem={({ item }) => {
                const isSelected = selectedCountry.code === item.code && selectedCountry.name === item.name;
                return (
                  <TouchableOpacity
                    style={[styles.countryRow, isSelected && styles.countryRowSelected]}
                    onPress={() => {
                      setSelectedCountry(item);
                      setCountryModalVisible(false);
                    }}
                  >
                    <Text style={styles.countryFlag}>{item.flag}</Text>
                    <Text style={styles.countryName} allowFontScaling={false}>
                      {item.name}
                    </Text>
                    <Text style={styles.countryDialCode} allowFontScaling={false}>
                      {item.code}
                    </Text>
                  </TouchableOpacity>
                );
              }}
            />
          </View>
        </View>
      </Modal>
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
  tabContainer: {
    flexDirection: "row",
    backgroundColor: "#05070D",
    borderRadius: 12,
    padding: 4,
    marginBottom: 18,
    borderWidth: 1,
    borderColor: "#1E293B",
  },
  tabButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 9,
    alignItems: "center",
    justifyContent: "center",
  },
  tabButtonActive: {
    backgroundColor: "#1E293B",
  },
  tabText: {
    color: "#64748B",
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 0.5,
  },
  tabTextActive: {
    color: "#FFFFFF",
  },
  biometricQuickBtn: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#7083FF14",
    borderWidth: 1,
    borderColor: "#7083FF40",
    borderRadius: 12,
    padding: 12,
    marginBottom: 18,
  },
  biometricIconBox: {
    width: 34,
    height: 34,
    borderRadius: 9,
    backgroundColor: "#7083FF28",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 10,
  },
  biometricIconText: {
    fontSize: 16,
  },
  biometricTextBox: {
    flex: 1,
  },
  biometricTitle: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "800",
  },
  biometricSubtitle: {
    color: "#7D8AA8",
    fontSize: 9.5,
    marginTop: 2,
  },
  biometricArrow: {
    color: "#7083FF",
    fontSize: 18,
    fontWeight: "700",
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
  phoneInputRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  countryPickerButton: {
    height: 50,
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#05070D",
    borderWidth: 1,
    borderColor: "#1E293B",
    borderRadius: 12,
    paddingHorizontal: 12,
    marginRight: 8,
  },
  countryPickerFlag: {
    fontSize: 16,
    marginRight: 6,
  },
  countryPickerCode: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "700",
    marginRight: 6,
  },
  countryPickerArrow: {
    color: "#7083FF",
    fontSize: 9,
  },
  phoneTextInput: {
    flex: 1,
  },
  metaRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 18,
    marginTop: 4,
  },
  rememberMeRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  checkbox: {
    width: 18,
    height: 18,
    borderRadius: 5,
    borderWidth: 1,
    borderColor: "#334155",
    backgroundColor: "#05070D",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 8,
  },
  checkboxActive: {
    borderColor: "#35E68A",
    backgroundColor: "#35E68A22",
  },
  checkmark: {
    color: "#35E68A",
    fontSize: 11,
    fontWeight: "900",
  },
  rememberMeText: {
    color: "#94A3B8",
    fontSize: 11.5,
    fontWeight: "600",
  },
  helpLinkText: {
    color: "#7083FF",
    fontSize: 11.5,
    fontWeight: "700",
  },
  otpInput: {
    fontSize: 22,
    fontWeight: "800",
    letterSpacing: 8,
    textAlign: "center",
    borderColor: "#334BFF",
  },
  devHintBox: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "#334BFF18",
    borderColor: "#334BFF40",
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginBottom: 16,
  },
  devHintLabel: {
    color: "#7083FF",
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 1,
  },
  devHintValue: {
    color: "#35E68A",
    fontSize: 18,
    fontWeight: "900",
    letterSpacing: 3,
  },
  primaryBtn: {
    height: 52,
    borderRadius: 12,
    backgroundColor: "#334BFF",
    alignItems: "center",
    justifyContent: "center",
    marginTop: 6,
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
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.75)",
    justifyContent: "flex-end",
  },
  modalContent: {
    backgroundColor: "#0A0E18",
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    borderWidth: 1,
    borderColor: "#1E293B",
    maxHeight: "75%",
    paddingTop: 18,
  },
  modalHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 20,
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#172032",
  },
  modalTitle: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "800",
  },
  modalCloseBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "#172032",
    alignItems: "center",
    justifyContent: "center",
  },
  modalCloseText: {
    color: "#94A3B8",
    fontSize: 14,
    fontWeight: "800",
  },
  modalSearchContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  modalSearchInput: {
    height: 46,
    backgroundColor: "#05070D",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#1E293B",
    color: "#FFFFFF",
    paddingHorizontal: 14,
    fontSize: 13,
  },
  countryRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#101625",
  },
  countryRowSelected: {
    backgroundColor: "#7083FF14",
  },
  countryFlag: {
    fontSize: 20,
    marginRight: 14,
  },
  countryName: {
    flex: 1,
    color: "#E2E8F0",
    fontSize: 13.5,
    fontWeight: "600",
  },
  countryDialCode: {
    color: "#7083FF",
    fontSize: 13.5,
    fontWeight: "700",
  },
});
