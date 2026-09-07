import React, {useState} from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import {useSafeAreaInsets} from 'react-native-safe-area-context';
import {
  AuthenticatedUser,
  RootStackParamList,
} from '../navigation/navigationTypes';
import AppLogo from '../components/branding/AppLogo';
import {BRANDING} from '../config/branding';

type LoginScreenProps = NativeStackScreenProps<
  RootStackParamList,
  'Login'
>;

export default function LoginScreen({navigation}: LoginScreenProps) {
  const insets = useSafeAreaInsets();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

const handleLogin = () => {
  if (loading) {
    return;
  }

  setLoading(true);

  setTimeout(() => {
    const normalizedEmail = email.trim().toLowerCase();

    const emailName =
      normalizedEmail.split('@')[0] || 'Trader';

    const firstName =
      emailName
        .split(/[._-]/)[0]
        .replace(/\d+/g, '')
        .replace(/^./, character => character.toUpperCase()) ||
      'Trader';

    const user: AuthenticatedUser = {
      id: normalizedEmail || 'development-user',
      email: normalizedEmail,
      firstName,
      displayName: firstName,
    };

    setLoading(false);

    navigation.replace('MainTabs', user);
  }, 1200);
};

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      <View style={styles.glowTop} />
      <View style={styles.glowBottom} />

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView
          contentContainerStyle={[
            styles.scrollContent,
            {
              paddingTop: Math.max(insets.top, 24),
              paddingBottom: Math.max(insets.bottom, 24),
            },
          ]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}>
          
          {/* BRAND HEADER */}
          <View style={styles.header}>
            <AppLogo size={74} />

            <Text style={styles.brand}>
              {BRANDING.appName}
            </Text>

            <Text style={styles.tagline}>
              {BRANDING.tagline}
            </Text>
          </View>

          {/* SYSTEM STATUS */}
          <View style={styles.statusRow}>
            <View style={styles.statusDot} />

            <Text style={styles.statusText}>
              SYSTEM READY
            </Text>
          </View>

          {/* LOGIN CARD */}
          <View style={styles.card}>
            <Text style={styles.welcome}>
              Welcome to {BRANDING.appName}
            </Text>

            <Text style={styles.subtitle}>
              Sign in to continue to your trading dashboard.
            </Text>

            {/* EMAIL */}
            <View style={styles.fieldContainer}>
              <Text style={styles.fieldLabel}>
                EMAIL
              </Text>

              <TextInput
                value={email}
                onChangeText={setEmail}
                placeholder="Enter your email"
                placeholderTextColor="#667085"
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="email-address"
                style={styles.input}
              />
            </View>

            {/* PASSWORD */}
            <View style={styles.fieldContainer}>
              <Text style={styles.fieldLabel}>
                PASSWORD
              </Text>

              <View style={styles.passwordWrapper}>
                <TextInput
                  value={password}
                  onChangeText={setPassword}
                  placeholder="Enter your password"
                  placeholderTextColor="#667085"
                  secureTextEntry={!showPassword}
                  autoCapitalize="none"
                  autoCorrect={false}
                  style={styles.passwordInput}
                />

                <Pressable
                  onPress={() =>
                    setShowPassword(previous => !previous)
                  }
                  style={styles.visibilityButton}
                  accessibilityRole="button"
                  accessibilityLabel={
                    showPassword
                      ? 'Hide password'
                      : 'Show password'
                  }>
                  <Text style={styles.visibilityText}>
                    {showPassword ? 'HIDE' : 'SHOW'}
                  </Text>
                </Pressable>
              </View>
            </View>

            {/* OPTIONS */}
            <View style={styles.optionsRow}>
              <View style={styles.rememberContainer}>
                <Switch
                  value={rememberMe}
                  onValueChange={setRememberMe}
                  trackColor={{
                    false: '#252B38',
                    true: '#334BFF',
                  }}
                  thumbColor="#FFFFFF"
                  accessibilityLabel="Remember me"
                />

                <Text style={styles.rememberText}>
                  Remember me
                </Text>
              </View>

              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Forgot password">
                <Text style={styles.forgotText}>
                  Forgot password?
                </Text>
              </Pressable>
            </View>

            {/* LOGIN BUTTON */}
            <Pressable
              onPress={handleLogin}
              disabled={loading}
              accessibilityRole="button"
              accessibilityLabel="Login"
              style={({pressed}) => [
                styles.loginButton,
                pressed && styles.loginButtonPressed,
                loading && styles.loginButtonLoading,
              ]}>
              {loading ? (
                <View style={styles.loadingRow}>
                  <ActivityIndicator
                    size="small"
                    color="#FFFFFF"
                  />

                  <Text style={styles.loginButtonText}>
                    AUTHENTICATING...
                  </Text>
                </View>
              ) : (
                <Text style={styles.loginButtonText}>
                  LOGIN
                </Text>
              )}
            </Pressable>

            {/* DIVIDER */}
            <View style={styles.dividerRow}>
              <View style={styles.divider} />

              <Text style={styles.dividerText}>
                OR
              </Text>

              <View style={styles.divider} />
            </View>

            {/* CREATE ACCOUNT */}
            <View style={styles.createRow}>
              <Text style={styles.createText}>
                Don't have an account?
              </Text>

              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Create account">
                <Text style={styles.createLink}>
                  {' '}Create account
                </Text>
              </Pressable>
            </View>
          </View>

          {/* FOOTER */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>
              {BRANDING.appName.toUpperCase()} • SMART TRADING PLATFORM
            </Text>

            <View style={styles.securityRow}>
              <View style={styles.securityDot} />

              <Text style={styles.securityText}>
                SECURE CONNECTION
              </Text>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#05070D',
  },

  flex: {
    flex: 1,
  },

  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 22,
    justifyContent: 'center',
  },

  glowTop: {
    position: 'absolute',
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: '#101B5C',
    opacity: 0.22,
    top: -150,
    right: -80,
  },

  glowBottom: {
    position: 'absolute',
    width: 280,
    height: 280,
    borderRadius: 140,
    backgroundColor: '#17204A',
    opacity: 0.18,
    bottom: -170,
    left: -100,
  },

  header: {
    alignItems: 'center',
    marginBottom: 22,
  },

  brand: {
    color: '#FFFFFF',
    fontSize: 27,
    fontWeight: '900',
    letterSpacing: 3,
    marginTop: 14,
  },

  tagline: {
    color: '#7D8AA8',
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 2,
    marginTop: 7,
    textAlign: 'center',
  },

  statusRow: {
    alignSelf: 'center',
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 18,
  },

  statusDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: '#35E68A',
    marginRight: 7,
  },

  statusText: {
    color: '#7D8AA8',
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 1.5,
  },

  card: {
    backgroundColor: '#0A0E18',
    borderRadius: 22,
    borderWidth: 1,
    borderColor: '#1B2435',
    padding: 22,
    shadowColor: '#000000',
    shadowOpacity: 0.35,
    shadowRadius: 20,
    shadowOffset: {
      width: 0,
      height: 10,
    },
    elevation: 8,
  },

  welcome: {
    color: '#FFFFFF',
    fontSize: 25,
    fontWeight: '800',
    marginBottom: 7,
  },

  subtitle: {
    color: '#7D8AA8',
    fontSize: 13,
    lineHeight: 20,
    marginBottom: 24,
  },

  fieldContainer: {
    marginBottom: 18,
  },

  fieldLabel: {
    color: '#8995B1',
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 1.4,
    marginBottom: 8,
  },

  input: {
    height: 54,
    borderRadius: 13,
    borderWidth: 1,
    borderColor: '#202A3B',
    backgroundColor: '#070A11',
    color: '#FFFFFF',
    paddingHorizontal: 15,
    fontSize: 14,
  },

  passwordWrapper: {
    height: 54,
    borderRadius: 13,
    borderWidth: 1,
    borderColor: '#202A3B',
    backgroundColor: '#070A11',
    flexDirection: 'row',
    alignItems: 'center',
  },

  passwordInput: {
    flex: 1,
    height: 52,
    color: '#FFFFFF',
    paddingHorizontal: 15,
    fontSize: 14,
  },

  visibilityButton: {
    paddingHorizontal: 14,
    paddingVertical: 12,
  },

  visibilityText: {
    color: '#7083FF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1,
  },

  optionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 22,
  },

  rememberContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  rememberText: {
    color: '#9AA5BB',
    fontSize: 12,
    marginLeft: 5,
  },

  forgotText: {
    color: '#7083FF',
    fontSize: 11,
    fontWeight: '700',
  },

  loginButton: {
    height: 56,
    borderRadius: 14,
    backgroundColor: '#334BFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#334BFF',
    shadowOpacity: 0.3,
    shadowRadius: 12,
    shadowOffset: {
      width: 0,
      height: 6,
    },
    elevation: 6,
  },

  loginButtonPressed: {
    opacity: 0.78,
    transform: [{scale: 0.985}],
  },

  loginButtonLoading: {
    opacity: 0.9,
  },

  loginButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 2,
  },

  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 23,
  },

  divider: {
    flex: 1,
    height: 1,
    backgroundColor: '#1B2435',
  },

  dividerText: {
    color: '#56627A',
    fontSize: 9,
    fontWeight: '800',
    marginHorizontal: 12,
  },

  createRow: {
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },

  createText: {
    color: '#78849D',
    fontSize: 12,
  },

  createLink: {
    color: '#7083FF',
    fontSize: 12,
    fontWeight: '800',
  },

  footer: {
    alignItems: 'center',
    marginTop: 22,
  },

  footerText: {
    color: '#424D64',
    fontSize: 8,
    fontWeight: '800',
    letterSpacing: 1.1,
    textAlign: 'center',
  },

  securityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },

  securityDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 6,
  },

  securityText: {
    color: '#4E5A72',
    fontSize: 8,
    fontWeight: '700',
    letterSpacing: 0.8,
  },
});
