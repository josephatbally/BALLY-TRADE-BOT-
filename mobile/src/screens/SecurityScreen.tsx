import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { useEffect, useState } from 'react';
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
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import ReactNativeBiometrics, { BiometryTypes } from 'react-native-biometrics';

import { RootStackParamList } from '../navigation/navigationTypes';

type Props = NativeStackScreenProps<RootStackParamList, 'Security'>;

type SecurityRowProps = {
  icon: string;
  title: string;
  subtitle: string;
  onPress?: () => void;
};

function SecurityRow({ icon, title, subtitle, onPress }: SecurityRowProps) {
  return (
    <Pressable
      disabled={!onPress}
      onPress={onPress}
      style={({ pressed }) => [
        styles.securityRow,
        pressed && onPress && styles.rowPressed,
      ]}
    >
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

function SectionHeader({ title }: { title: string }) {
  return <Text style={styles.sectionTitle}>{title}</Text>;
}

function StatusPill({ label, active = false }: { label: string; active?: boolean }) {
  return (
    <View
      style={[
        styles.statusPill,
        active ? styles.statusPillActive : styles.statusPillInactive,
      ]}
    >
      <View
        style={[
          styles.statusDot,
          active ? styles.statusDotActive : styles.statusDotInactive,
        ]}
      />
      <Text
        style={[
          styles.statusText,
          active ? styles.statusTextActive : styles.statusTextInactive,
        ]}
      >
        {label}
      </Text>
    </View>
  );
}

export default function SecurityScreen({ route, navigation }: Props) {
  const insets = useSafeAreaInsets();
  const [biometricEnabled, setBiometricEnabled] = useState(false);
  const [sensorAvailable, setSensorAvailable] = useState(false);
  const [sensorType, setSensorType] = useState<string>('Biometrics');

  const email = route.params?.email ?? 'Trader';

  useEffect(() => {
    let mounted = true;
    const checkSensor = async () => {
      try {
        const stored = await AsyncStorage.getItem('@bally_biometric_enabled');
        if (mounted && stored === 'true') {
          setBiometricEnabled(true);
        }

        const rnBiometrics = new ReactNativeBiometrics();
        const { available, biometryType } = await rnBiometrics.isSensorAvailable();
        if (mounted) {
          setSensorAvailable(available);
          if (biometryType === BiometryTypes.FaceID) {
            setSensorType('Face ID');
          } else if (biometryType === BiometryTypes.TouchID) {
            setSensorType('Fingerprint / Touch ID');
          } else if (biometryType === BiometryTypes.Biometrics) {
            setSensorType('Fingerprint Sensor');
          } else {
            setSensorType('Biometrics');
          }
        }
      } catch {
        // ignore sensor check error
      }
    };

    checkSensor();
    return () => {
      mounted = false;
    };
  }, []);

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

  const toggleBiometric = async (value: boolean) => {
    const rnBiometrics = new ReactNativeBiometrics();

    if (value) {
      try {
        const { available } = await rnBiometrics.isSensorAvailable();
        if (!available) {
          Alert.alert(
            'Biometrics Unavailable',
            'No biometric hardware (fingerprint or face recognition) was detected on this device, or none is enrolled in your phone settings.',
          );
          setBiometricEnabled(false);
          await AsyncStorage.setItem('@bally_biometric_enabled', 'false');
          return;
        }

        const promptRes = await rnBiometrics.simplePrompt({
          promptMessage: 'Confirm fingerprint or face recognition for BALLY FLOW',
          cancelButtonText: 'Cancel',
        });

        if (promptRes.success) {
          setBiometricEnabled(true);
          await AsyncStorage.setItem('@bally_biometric_enabled', 'true');
          Alert.alert('Biometric Login', 'Biometric recognition successfully activated.');
        } else {
          setBiometricEnabled(false);
          await AsyncStorage.setItem('@bally_biometric_enabled', 'false');
        }
      } catch (err: any) {
        setBiometricEnabled(false);
        await AsyncStorage.setItem('@bally_biometric_enabled', 'false');
        Alert.alert('Verification Cancelled', err?.message || 'Biometric verification was not completed.');
      }
    } else {
      setBiometricEnabled(false);
      await AsyncStorage.setItem('@bally_biometric_enabled', 'false');
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
          styles.scrollContent,
          {
            paddingTop: Math.max(insets.top, 20),
            paddingBottom: Math.max(insets.bottom + 60, 40),
          },
        ]}
      >
        <View style={styles.header}>
          <Pressable
            onPress={handleGoBack}
            style={({ pressed }) => [
              styles.backButton,
              pressed && styles.backButtonPressed,
            ]}
          >
            <Text style={styles.backButtonArrow}>←</Text>
            <Text style={styles.backButtonText}>BACK</Text>
          </Pressable>

          <View style={styles.titleContainer}>
            <Text style={styles.screenTag}>ACCOUNT SECURITY</Text>
            <Text style={styles.screenTitle}>SECURITY & PRIVACY</Text>
            <Text style={styles.screenSubtitle}>
              Protection, credentials and device authentication
            </Text>
          </View>
        </View>

        <View style={styles.accountCard}>
          <View style={styles.accountCardHeader}>
            <View style={styles.accountIcon}>
              <Text style={styles.accountIconText}>🔒</Text>
            </View>

            <View style={styles.accountInfo}>
              <Text style={styles.accountName}>BALLY FLOW SHIELD</Text>
              <Text style={styles.accountEmail}>{email}</Text>
            </View>

            <StatusPill
              label={sensorAvailable ? (biometricEnabled ? 'SECURED' : 'READY') : 'PASSWORD'}
              active={biometricEnabled}
            />
          </View>

          <View style={styles.accountCardDivider} />

          <View style={styles.cardInfoRow}>
            <Text style={styles.cardInfoLabel}>HARDWARE STATUS</Text>
            <Text style={styles.cardInfoValue}>
              {sensorAvailable ? (sensorType + ' Detected') : 'No Sensor Enrolled'}
            </Text>
          </View>
        </View>

        <SectionHeader title="DEVICE & BIOMETRIC AUTHENTICATION" />

        <View style={styles.sectionCard}>
          <View style={styles.toggleRow}>
            <View style={styles.rowIcon}>
              <Text style={styles.rowIconText}>👆</Text>
            </View>

            <View style={styles.rowContent}>
              <Text style={styles.rowTitle}>Biometric Login</Text>
              <Text style={styles.rowSubtitle}>
                {sensorAvailable
                  ? 
                  : 'Enroll biometric credentials in device settings to enable'}
              </Text>
            </View>

            <Switch
              value={biometricEnabled}
              onValueChange={toggleBiometric}
              trackColor={{ false: '#252B38', true: '#334BFF' }}
              thumbColor="#FFFFFF"
              accessibilityLabel="Biometric login"
            />
          </View>
        </View>

        <SectionHeader title="PASSWORD & CREDENTIALS" />

        <View style={styles.sectionCard}>
          <SecurityRow
            icon="🔑"
            title="Change Password"
            subtitle="Update your BALLY FLOW login password"
            onPress={openPasswordSecurity}
          />

          <View style={styles.rowDivider} />

          <SecurityRow
            icon="📱"
            title="Active Sessions"
            subtitle="Manage logged in devices and tokens"
            onPress={openSessions}
          />
        </View>

        <SectionHeader title="AUDIT & LOGS" />

        <View style={styles.sectionCard}>
          <SecurityRow
            icon="📜"
            title="Security Activity"
            subtitle="Review recent login and verification attempts"
            onPress={openSecurityActivity}
          />
        </View>

        <View style={styles.footer}>
          <View style={styles.footerDot} />
          <Text style={styles.footerText}>
            PROTECTED BY BALLY FLOW ZERO-TRUST ENGINE
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
  scrollContent: {
    paddingHorizontal: 18,
  },
  glowTop: {
    position: 'absolute',
    width: 320,
    height: 320,
    borderRadius: 160,
    backgroundColor: '#111B5B',
    opacity: 0.16,
    top: -180,
    right: -100,
  },
  glowBottom: {
    position: 'absolute',
    width: 280,
    height: 280,
    borderRadius: 140,
    backgroundColor: '#15204B',
    opacity: 0.12,
    bottom: -140,
    left: -120,
  },
  header: {
    marginBottom: 20,
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: '#0C1322',
    borderWidth: 1,
    borderColor: '#1D2A45',
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 7,
    marginBottom: 16,
  },
  backButtonPressed: {
    backgroundColor: '#17233D',
  },
  backButtonArrow: {
    color: '#7083FF',
    fontSize: 14,
    fontWeight: '900',
    marginRight: 6,
  },
  backButtonText: {
    color: '#8999BC',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1.2,
  },
  titleContainer: {
    marginTop: 4,
  },
  screenTag: {
    color: '#7083FF',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 2,
    marginBottom: 6,
  },
  screenTitle: {
    color: '#FFFFFF',
    fontSize: 24,
    fontWeight: '900',
    letterSpacing: 0.4,
  },
  screenSubtitle: {
    color: '#69758E',
    fontSize: 11,
    marginTop: 4,
  },
  accountCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 18,
    padding: 16,
    marginBottom: 24,
  },
  accountCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  accountIcon: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: '#111A38',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  accountIconText: {
    fontSize: 18,
  },
  accountInfo: {
    flex: 1,
  },
  accountName: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '900',
  },
  accountEmail: {
    color: '#68748B',
    fontSize: 10,
    marginTop: 3,
  },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 16,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  statusPillActive: {
    backgroundColor: '#0D2B1B',
  },
  statusPillInactive: {
    backgroundColor: '#201A24',
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 6,
  },
  statusDotActive: {
    backgroundColor: '#35E68A',
  },
  statusDotInactive: {
    backgroundColor: '#8995B1',
  },
  statusText: {
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  statusTextActive: {
    color: '#35E68A',
  },
  statusTextInactive: {
    color: '#8995B1',
  },
  accountCardDivider: {
    height: 1,
    backgroundColor: '#172032',
    marginVertical: 12,
  },
  cardInfoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardInfoLabel: {
    color: '#5B6881',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1,
  },
  cardInfoValue: {
    color: '#8CA1CF',
    fontSize: 10,
    fontWeight: '700',
  },
  sectionTitle: {
    color: '#A8B2C7',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1.4,
    marginBottom: 10,
    marginTop: 6,
  },
  sectionCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 20,
  },
  securityRow: {
    minHeight: 64,
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
    fontSize: 14,
  },
  rowContent: {
    flex: 1,
  },
  rowTitle: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '800',
  },
  rowSubtitle: {
    color: '#647087',
    fontSize: 9,
    marginTop: 3,
  },
  rowArrow: {
    color: '#65718A',
    fontSize: 22,
    fontWeight: '300',
    marginLeft: 8,
  },
  rowDivider: {
    height: 1,
    backgroundColor: '#172032',
    marginLeft: 62,
  },
  toggleRow: {
    minHeight: 64,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 20,
  },
  footerDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#334BFF',
    marginRight: 6,
  },
  footerText: {
    color: '#46526A',
    fontSize: 8,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
});
