
import React from 'react';
import {
  Alert,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import {useSafeAreaInsets} from 'react-native-safe-area-context';

import {RootStackParamList} from '../navigation/navigationTypes';

type Props = NativeStackScreenProps<RootStackParamList, 'Security'>;

type SecurityRowProps = {
  icon: string;
  title: string;
  subtitle: string;
  onPress?: () => void;
};

function SecurityRow({
  icon,
  title,
  subtitle,
  onPress,
}: SecurityRowProps) {
  return (
    <Pressable
      disabled={!onPress}
      onPress={onPress}
      style={({pressed}) => [
        styles.securityRow,
        pressed && onPress && styles.rowPressed,
      ]}>
      <View style={styles.rowIcon}>
        <Text style={styles.rowIconText}>{icon}</Text>
      </View>

      <View style={styles.rowContent}>
        <Text style={styles.rowTitle}>{title}</Text>
        <Text style={styles.rowSubtitle}>{subtitle}</Text>
      </View>

      {onPress ? <Text style={styles.rowArrow}>›</Text> : null}
    </Pressable>
  );
}

function SectionHeader({title}: {title: string}) {
  return <Text style={styles.sectionTitle}>{title}</Text>;
}

function StatusPill({
  label,
  active = false,
}: {
  label: string;
  active?: boolean;
}) {
  return (
    <View
      style={[
        styles.statusPill,
        active
          ? styles.statusPillActive
          : styles.statusPillInactive,
      ]}>
      <View
        style={[
          styles.statusDot,
          active
            ? styles.statusDotActive
            : styles.statusDotInactive,
        ]}
      />

      <Text
        style={[
          styles.statusText,
          active
            ? styles.statusTextActive
            : styles.statusTextInactive,
        ]}>
        {label}
      </Text>
    </View>
  );
}

export default function SecurityScreen({
  route,
  navigation,
}: Props) {
  const insets = useSafeAreaInsets();

  const [biometricEnabled, setBiometricEnabled] =
    React.useState(false);

  const email = route.params.email;

  /**
   * Returns the user to the previous screen.
   *
   * Security is a child screen opened from another settings/profile
   * area, so we preserve the actual navigation history instead of
   * hard-coding a destination.
   */
  const handleGoBack = () => {
    if (navigation.canGoBack()) {
      navigation.goBack();
    }
  };

  const openPasswordSecurity = () => {
    Alert.alert(
      'Password Security',
      'Password management will be connected to the BALLY FLOW authentication service in the authentication integration stage.',
    );
  };

  const openSessions = () => {
    Alert.alert(
      'Active Sessions',
      'Session and device management will be connected to the authentication backend in a later integration stage.',
    );
  };

  const openSecurityActivity = () => {
    Alert.alert(
      'Security Activity',
      'Security event history will be available when backend authentication and audit logging are integrated.',
    );
  };

  const toggleBiometric = (value: boolean) => {
    setBiometricEnabled(value);

    if (value) {
      Alert.alert(
        'Biometric Login',
        'Biometric authentication is enabled locally. Final authentication enforcement will be connected during the security integration stage.',
      );
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      <View style={styles.glowTop} />
      <View style={styles.glowBottom} />

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[
          styles.content,
          {
            paddingTop: Math.max(insets.top, 20),
            paddingBottom: Math.max(insets.bottom + 40, 40),
          },
        ]}>

        {/* ============================================================
            HEADER
        ============================================================ */}

        <View style={styles.topNavigation}>
          <Pressable
            onPress={handleGoBack}
            accessibilityRole="button"
            accessibilityLabel="Go back"
            hitSlop={10}
            style={({pressed}) => [
              styles.backButton,
              pressed && styles.backButtonPressed,
            ]}>
            <Text style={styles.backArrow}>‹</Text>
          </Pressable>

          <Text style={styles.backLabel}>BACK</Text>
        </View>

        <View style={styles.header}>
          <View style={styles.headerText}>
            <Text style={styles.eyebrow}>BALLY FLOW</Text>

            <Text style={styles.title}>SECURITY</Text>

            <Text style={styles.subtitle}>
              Account protection and authentication
            </Text>
          </View>

          <View style={styles.secureBadge}>
            <View style={styles.secureDot} />
            <Text style={styles.secureText}>PROTECTED</Text>
          </View>
        </View>

        {/* ACCOUNT SECURITY */}

        <View style={styles.accountCard}>
          <View style={styles.accountIcon}>
            <Text style={styles.accountIconText}>S</Text>
          </View>

          <View style={styles.accountInfo}>
            <Text style={styles.accountLabel}>
              SECURED ACCOUNT
            </Text>

            <Text style={styles.accountEmail}>
              {email}
            </Text>

            <Text style={styles.accountDescription}>
              Your BALLY FLOW account is protected by the
              application authentication layer.
            </Text>
          </View>
        </View>

        {/* AUTHENTICATION */}

        <SectionHeader title="AUTHENTICATION" />

        <View style={styles.sectionCard}>
          <SecurityRow
            icon="P"
            title="Password & Authentication"
            subtitle="Manage account authentication security"
            onPress={openPasswordSecurity}
          />

          <View style={styles.divider} />

          <View style={styles.toggleRow}>
            <View style={styles.rowIcon}>
              <Text style={styles.rowIconText}>B</Text>
            </View>

            <View style={styles.rowContent}>
              <Text style={styles.rowTitle}>
                Biometric Login
              </Text>

              <Text style={styles.rowSubtitle}>
                Use supported device biometrics for access
              </Text>
            </View>

            <Switch
              value={biometricEnabled}
              onValueChange={toggleBiometric}
              trackColor={{
                false: '#252B38',
                true: '#334BFF',
              }}
              thumbColor="#FFFFFF"
              accessibilityLabel="Biometric login"
            />
          </View>

          <View style={styles.divider} />

          <SecurityRow
            icon="D"
            title="Active Sessions"
            subtitle="Review connected devices and sessions"
            onPress={openSessions}
          />
        </View>

        {/* SECURITY STATUS */}

        <SectionHeader title="SECURITY STATUS" />

        <View style={styles.statusCard}>
          <View style={styles.statusHeader}>
            <View>
              <Text style={styles.statusTitle}>
                PROTECTION STATUS
              </Text>

              <Text style={styles.statusDescription}>
                Local application security controls
              </Text>
            </View>

            <StatusPill
              label="ACTIVE"
              active
            />
          </View>

          <View style={styles.statusDivider} />

          <View style={styles.statusList}>
            <View style={styles.statusItem}>
              <View style={styles.checkCircle}>
                <Text style={styles.checkText}>✓</Text>
              </View>

              <Text style={styles.statusItemText}>
                Authentication layer enabled
              </Text>
            </View>

            <View style={styles.statusItem}>
              <View style={styles.checkCircle}>
                <Text style={styles.checkText}>✓</Text>
              </View>

              <Text style={styles.statusItemText}>
                MT5 credentials are not stored in the app
              </Text>
            </View>

            <View style={styles.statusItem}>
              <View style={styles.checkCircle}>
                <Text style={styles.checkText}>✓</Text>
              </View>

              <Text style={styles.statusItemText}>
                Trading execution remains backend controlled
              </Text>
            </View>
          </View>
        </View>

        {/* MT5 SECURITY */}

        <SectionHeader title="TRADING SECURITY" />

        <View style={styles.mt5Card}>
          <View style={styles.mt5Header}>
            <View style={styles.mt5Icon}>
              <Text style={styles.mt5IconText}>MT5</Text>
            </View>

            <View style={styles.mt5Info}>
              <Text style={styles.mt5Title}>
                MT5 CREDENTIAL PROTECTION
              </Text>

              <Text style={styles.mt5Subtitle}>
                Credentials remain outside the mobile UI
              </Text>
            </View>
          </View>

          <View style={styles.mt5Divider} />

          <Text style={styles.mt5Text}>
            BALLY FLOW does not directly store broker
            passwords or MT5 credentials inside the mobile
            application. Authentication and secure broker
            connectivity remain separated from the UI layer.
          </Text>

          <View style={styles.protectionBadge}>
            <View style={styles.protectionDot} />

            <Text style={styles.protectionText}>
              CREDENTIAL STORAGE PROTECTED
            </Text>
          </View>
        </View>

        {/* ACTIVITY */}

        <SectionHeader title="SECURITY ACTIVITY" />

        <View style={styles.sectionCard}>
          <SecurityRow
            icon="A"
            title="Security Activity"
            subtitle="Review authentication and security events"
            onPress={openSecurityActivity}
          />
        </View>

        {/* INFORMATION */}

        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>
            SECURITY ARCHITECTURE
          </Text>

          <Text style={styles.infoText}>
            Sensitive authentication, broker connectivity,
            credential handling and trading execution must
            remain controlled by the secure backend rather
            than the mobile presentation layer.
          </Text>
        </View>

        {/* FOOTER */}

        <View style={styles.footer}>
          <View style={styles.footerDot} />

          <Text style={styles.footerText}>
            BALLY FLOW SECURITY CONTROLS ACTIVE
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#05070D',
  },

  content: {
    paddingHorizontal: 18,
  },

  glowTop: {
    position: 'absolute',
    width: 330,
    height: 330,
    borderRadius: 165,
    backgroundColor: '#111B5B',
    opacity: 0.15,
    top: -190,
    right: -120,
  },

  glowBottom: {
    position: 'absolute',
    width: 300,
    height: 300,
    borderRadius: 150,
    backgroundColor: '#15204B',
    opacity: 0.11,
    bottom: -150,
    left: -150,
  },

  /* ============================================================
     BACK NAVIGATION
  ============================================================ */

  topNavigation: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    marginBottom: 18,
  },

  backButton: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    alignItems: 'center',
    justifyContent: 'center',
  },

  backButtonPressed: {
    backgroundColor: '#111A2B',
    borderColor: '#334BFF',
  },

  backArrow: {
    color: '#7083FF',
    fontSize: 30,
    fontWeight: '400',
    lineHeight: 34,
    marginTop: -3,
  },

  backLabel: {
    color: '#7083FF',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1.3,
    marginLeft: 9,
  },

  /* ============================================================
     HEADER
  ============================================================ */

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 23,
  },

  headerText: {
    flex: 1,
  },

  eyebrow: {
    color: '#7083FF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 2.1,
    marginBottom: 7,
  },

  title: {
    color: '#FFFFFF',
    fontSize: 27,
    fontWeight: '900',
    letterSpacing: 0.3,
  },

  subtitle: {
    color: '#69758E',
    fontSize: 10,
    marginTop: 6,
  },

  secureBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0D211A',
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 7,
    marginTop: 8,
    marginLeft: 10,
  },

  secureDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 6,
  },

  secureText: {
    color: '#35E68A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  accountCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 19,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 26,
  },

  accountIcon: {
    width: 50,
    height: 50,
    borderRadius: 16,
    backgroundColor: '#111A38',
    borderWidth: 1,
    borderColor: '#334BFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 13,
  },

  accountIconText: {
    color: '#7083FF',
    fontSize: 17,
    fontWeight: '900',
  },

  accountInfo: {
    flex: 1,
  },

  accountLabel: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1,
  },

  accountEmail: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '800',
    marginTop: 5,
  },

  accountDescription: {
    color: '#68748B',
    fontSize: 8,
    lineHeight: 14,
    marginTop: 6,
  },

  sectionTitle: {
    color: '#A8B2C7',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1.6,
    marginBottom: 9,
    marginTop: 2,
  },

  sectionCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 18,
    overflow: 'hidden',
    marginBottom: 25,
  },

  securityRow: {
    minHeight: 70,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
  },

  rowPressed: {
    backgroundColor: '#0E1423',
  },

  rowIcon: {
    width: 36,
    height: 36,
    borderRadius: 11,
    backgroundColor: '#111A38',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },

  rowIconText: {
    color: '#7083FF',
    fontSize: 11,
    fontWeight: '900',
  },

  rowContent: {
    flex: 1,
  },

  rowTitle: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '800',
  },

  rowSubtitle: {
    color: '#647087',
    fontSize: 8,
    marginTop: 4,
  },

  rowArrow: {
    color: '#65718A',
    fontSize: 24,
    fontWeight: '300',
    marginLeft: 8,
  },

  toggleRow: {
    minHeight: 70,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
  },

  divider: {
    height: 1,
    backgroundColor: '#172032',
    marginLeft: 62,
  },

  statusCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 18,
    padding: 16,
    marginBottom: 25,
  },

  statusHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  statusTitle: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 0.6,
  },

  statusDescription: {
    color: '#647087',
    fontSize: 8,
    marginTop: 4,
  },

  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 20,
    paddingHorizontal: 9,
    paddingVertical: 6,
  },

  statusPillActive: {
    backgroundColor: '#0D211A',
  },

  statusPillInactive: {
    backgroundColor: '#20191B',
  },

  statusDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    marginRight: 5,
  },

  statusDotActive: {
    backgroundColor: '#35E68A',
  },

  statusDotInactive: {
    backgroundColor: '#FF7185',
  },

  statusText: {
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  statusTextActive: {
    color: '#35E68A',
  },

  statusTextInactive: {
    color: '#FF7185',
  },

  statusDivider: {
    height: 1,
    backgroundColor: '#1B2435',
    marginVertical: 15,
  },

  statusList: {
    gap: 12,
  },

  statusItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  checkCircle: {
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: '#10261E',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 9,
  },

  checkText: {
    color: '#35E68A',
    fontSize: 9,
    fontWeight: '900',
  },

  statusItemText: {
    flex: 1,
    color: '#8995A9',
    fontSize: 8,
    lineHeight: 13,
  },

  mt5Card: {
    backgroundColor: '#0B1020',
    borderWidth: 1,
    borderColor: '#1C2949',
    borderRadius: 18,
    padding: 16,
    marginBottom: 25,
  },

  mt5Header: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  mt5Icon: {
    width: 44,
    height: 44,
    borderRadius: 13,
    backgroundColor: '#111A38',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
  },

  mt5IconText: {
    color: '#7083FF',
    fontSize: 9,
    fontWeight: '900',
  },

  mt5Info: {
    flex: 1,
  },

  mt5Title: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 0.3,
  },

  mt5Subtitle: {
    color: '#647087',
    fontSize: 8,
    marginTop: 4,
  },

  mt5Divider: {
    height: 1,
    backgroundColor: '#1C2949',
    marginVertical: 14,
  },

  mt5Text: {
    color: '#78859D',
    fontSize: 8,
    lineHeight: 15,
  },

  protectionBadge: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#101A38',
    borderWidth: 1,
    borderColor: '#27345C',
    borderRadius: 20,
    paddingHorizontal: 9,
    paddingVertical: 6,
    marginTop: 13,
  },

  protectionDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 6,
  },

  protectionText: {
    color: '#7083FF',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  infoCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 17,
    padding: 15,
    marginBottom: 24,
  },

  infoTitle: {
    color: '#7083FF',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1,
    marginBottom: 8,
  },

  infoText: {
    color: '#68748B',
    fontSize: 8,
    lineHeight: 15,
  },

  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },

  footerDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 6,
  },

  footerText: {
    color: '#46526A',
    fontSize: 7,
    fontWeight: '800',
    letterSpacing: 0.7,
  },
});
