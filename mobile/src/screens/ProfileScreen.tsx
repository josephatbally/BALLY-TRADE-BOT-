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
  Image,
} from 'react-native';
import {BottomTabScreenProps} from '@react-navigation/bottom-tabs';
import {CompositeScreenProps} from '@react-navigation/native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import {useSafeAreaInsets} from 'react-native-safe-area-context';
import {RootStackParamList} from '../navigation/navigationTypes';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {MainTabParamList} from '../navigation/MainTabNavigator';
import {launchImageLibrary} from 'react-native-image-picker';

import {BRANDING} from '../config/branding';

type ProfileScreenProps = CompositeScreenProps<
  BottomTabScreenProps<MainTabParamList, 'Profile'>,
  NativeStackScreenProps<RootStackParamList>
>;

type ProfileRowProps = {
  icon: string;
  title: string;
  subtitle: string;
  onPress?: () => void;
  danger?: boolean;
};

function ProfileRow({
  icon,
  title,
  subtitle,
  onPress,
  danger = false,
}: ProfileRowProps) {
  return (
    <Pressable
      onPress={onPress}
      disabled={!onPress}
      style={({pressed}) => [
        styles.profileRow,
        pressed && onPress && styles.profileRowPressed,
      ]}>
      <View
        style={[
          styles.rowIcon,
          danger && styles.rowIconDanger,
        ]}>
        <Text
          style={[
            styles.rowIconText,
            danger && styles.rowIconTextDanger,
          ]}>
          {icon}
        </Text>
      </View>

      <View style={styles.rowContent}>
        <Text
          style={[
            styles.rowTitle,
            danger && styles.rowTitleDanger,
          ]}>
          {title}
        </Text>

        <Text style={styles.rowSubtitle}>
          {subtitle}
        </Text>
      </View>

      {onPress ? (
        <Text
          style={[
            styles.rowArrow,
            danger && styles.rowArrowDanger,
          ]}>
          ›
        </Text>
      ) : null}
    </Pressable>
  );
}

function SectionHeader({
  title,
}: {
  title: string;
}) {
  return (
    <Text style={styles.sectionTitle}>
      {title}
    </Text>
  );
}

export default function ProfileScreen({
  navigation,
  route,
}: ProfileScreenProps) {
  const insets = useSafeAreaInsets();

  const user = route.params;

  /*
   * Temporary UI state.
   *
   * These values should later come from the authenticated
   * backend/API and user database.
   */
  const [botEnabled, setBotEnabled] =
    React.useState(false);

  const [avatarUri, setAvatarUri] = useState<string | null>(null);

  useEffect(() => {
    AsyncStorage.getItem('@bally_profile_photo')
      .then(stored => {
        if (stored) {
          setAvatarUri(stored);
        }
      })
      .catch(() => {});
  }, []);

  const handlePickPhoto = async () => {
    try {
      const response = await launchImageLibrary({
        mediaType: 'photo',
        maxWidth: 600,
        maxHeight: 600,
        quality: 0.85,
        selectionLimit: 1,
      });

      if (response.didCancel) {
        return;
      }
      if (response.errorCode) {
        Alert.alert('Photo Selection', response.errorMessage || 'Unable to open photos.');
        return;
      }
      const asset = response.assets?.[0];
      if (asset?.uri) {
        setAvatarUri(asset.uri);
        await AsyncStorage.setItem('@bally_profile_photo', asset.uri);
      }
    } catch (err: any) {
      Alert.alert('Error', err?.message || 'Failed to select photo');
    }
  };

  const [biometricEnabled, setBiometricEnabled] =
    React.useState(false);

  const [notificationsEnabled, setNotificationsEnabled] =
    React.useState(true);

  /*
   * Backend connection state.
   *
   * Keep false until the real API/backend connection
   * provides the actual system status.
   */
  const [isLive] = React.useState(false);

  const firstName =
    user?.firstName ?? 'Trader';

  const fullName =
    user?.displayName || firstName;

  const email =
    user?.email ?? 'Account information';

  const profileLetter =
    firstName.charAt(0).toUpperCase();

  const openHistory = () => {
    /*
     * Change 'History' only if your Stack Navigator
     * uses a different route name.
     */
    navigation.navigate('History', user);
  };

  const openNotifications = () => {
    navigation.navigate('Notifications', user);
  };

  const openSettings = () => {
    navigation.navigate('Settings', user);
  };

  const openBotControl = () => {
    navigation.navigate('BotControl', user);
  };

  const openPreferences = () => {
    navigation.navigate('TradingPreferences', user);
  };

  const openRiskConfiguration = () => {
    navigation.navigate('RiskConfiguration', user);
  };

  const openSecurity = () => {
    navigation.navigate('Security', user);
  };

  const openAccountInformation = () => {
    navigation.navigate('AccountInformation', user);
  };

  const confirmLogout = () => {
    Alert.alert(
      'Log out?',
      'You will need to sign in again to access your BALLY FLOW account.',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Log Out',
          style: 'destructive',
          onPress: async () => {
            try {
              await AsyncStorage.removeItem('@bally_auth_user');
              await AsyncStorage.removeItem('@bally_auth_token');
              await AsyncStorage.removeItem('@bally_broker_credentials');
            } catch {
              // ignore
            }
            navigation.reset({
              index: 0,
              routes: [
                {
                  name: 'Login' as never,
                },
              ],
            });
          },
        },
      ],
    );
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
            paddingBottom: Math.max(
              insets.bottom + 100,
              40,
            ),
          },
        ]}>

        {/* =============================================== */}
        {/* HEADER */}
        {/* =============================================== */}

        <View style={styles.header}>
          <View>
            <Text style={styles.appName}>
              {BRANDING.appName}
            </Text>

            <Text style={styles.screenTitle}>
              PROFILE
            </Text>

            <Text style={styles.screenSubtitle}>
              Account and trading configuration
            </Text>
          </View>

          <View
            style={[
              styles.connectionBadge,
              !isLive && styles.connectionBadgeOffline,
            ]}>
            <View
              style={[
                styles.connectionDot,
                !isLive && styles.connectionDotOffline,
              ]}
            />

            <Text
              style={[
                styles.connectionText,
                !isLive && styles.connectionTextOffline,
              ]}>
              {isLive ? 'LIVE' : 'OFFLINE'}
            </Text>
          </View>
        </View>

        {/* =============================================== */}
        {/* PROFILE CARD */}
        {/* =============================================== */}

        <View style={styles.profileCard}>
          <Pressable
            onPress={handlePickPhoto}
            style={({pressed}) => [
              styles.avatarWrapper,
              pressed && styles.avatarPressed,
            ]}>
            <View style={styles.avatar}>
              {avatarUri ? (
                <Image source={{uri: avatarUri}} style={styles.avatarImage} />
              ) : (
                <Text style={styles.avatarText}>
                  {profileLetter}
                </Text>
              )}
            </View>
            <View style={styles.avatarCameraBadge}>
              <Text style={styles.avatarCameraBadgeText}>📷</Text>
            </View>
          </Pressable>

          <View style={styles.profileInfo}>
            <Text style={styles.profileName}>
              {fullName}
            </Text>

            <Text style={styles.profileEmail}>
              {email}
            </Text>

            <View style={styles.accountStatus}>
              <View style={styles.accountStatusDot} />

              <Text style={styles.accountStatusText}>
                ACTIVE ACCOUNT
              </Text>
            </View>
          </View>
        </View>

        {/* =============================================== */}
        {/* ACCOUNT */}
        {/* =============================================== */}

        <SectionHeader title="ACCOUNT" />

        <View style={styles.sectionCard}>
          <ProfileRow
            icon="A"
            title="Account Information"
            subtitle="Profile and account details"
            onPress={openAccountInformation}
          />

          <View style={styles.rowDivider} />

          <ProfileRow
            icon="●"
            title="Account Status"
            subtitle={
              isLive
                ? 'Trading system connected'
                : 'Waiting for backend connection'
            }
          />

          <View style={styles.rowDivider} />

          <ProfileRow
            icon="M"
            title="Trading Account"
            subtitle="Broker and MT5 account connection"
            onPress={openAccountInformation}
          />
        </View>

        {/* =============================================== */}
        {/* BOT CONTROL */}
        {/* =============================================== */}

        <SectionHeader title="BOT & TRADING" />

        <View style={styles.botCard}>
          <View style={styles.botTop}>
            <View style={styles.botIcon}>
              <Text style={styles.botIconText}>
                B
              </Text>
            </View>

            <View style={styles.botInfo}>
              <Text style={styles.botTitle}>
                BALLY TRADES BOT
              </Text>

              <Text style={styles.botSubtitle}>
                Controlled through the secure backend
              </Text>
            </View>

            <Switch
              value={botEnabled}
              onValueChange={setBotEnabled}
              trackColor={{
                false: '#252B38',
                true: '#334BFF',
              }}
              thumbColor="#FFFFFF"
              accessibilityLabel="Bot enabled"
            />
          </View>

          <View style={styles.botDivider} />

          <View style={styles.botMetrics}>
            <View style={styles.botMetric}>
              <Text style={styles.botMetricLabel}>
                STATUS
              </Text>

              <Text
                style={[
                  styles.botMetricValue,
                  botEnabled
                    ? styles.botOn
                    : styles.botOff,
                ]}>
                {botEnabled ? 'ON' : 'OFF'}
              </Text>
            </View>

            <View style={styles.botMetricDivider} />

            <View style={styles.botMetric}>
              <Text style={styles.botMetricLabel}>
                MODE
              </Text>

              <Text style={styles.botMetricValue}>
                TECHNICAL
              </Text>
            </View>

            <View style={styles.botMetricDivider} />

            <View style={styles.botMetric}>
              <Text style={styles.botMetricLabel}>
                ACCESS
              </Text>

              <Text style={styles.botMetricValue}>
                ENABLED
              </Text>
            </View>
          </View>

          <Pressable
            onPress={openBotControl}
            style={({pressed}) => [
              styles.manageBotButton,
              pressed && styles.buttonPressed,
            ]}>
            <Text style={styles.manageBotButtonText}>
              MANAGE BOT CONTROL →
            </Text>
          </Pressable>
        </View>

        {/* =============================================== */}
        {/* TRADING PREFERENCES */}
        {/* =============================================== */}

        <SectionHeader title="TRADING PREFERENCES" />

        <View style={styles.sectionCard}>
          <ProfileRow
            icon="L"
            title="Lot Size"
            subtitle="Configure your preferred lot size"
            onPress={openPreferences}
          />

          <View style={styles.rowDivider} />

          <ProfileRow
            icon="R"
            title="Risk Configuration"
            subtitle="Risk percentage and trading limits"
            onPress={openRiskConfiguration}
          />

          <View style={styles.rowDivider} />

          <ProfileRow
            icon="M"
            title="Preferred Markets"
            subtitle="XAUUSD, EURUSD, GBPUSD and more"
            onPress={openPreferences}
          />

          <View style={styles.rowDivider} />

          <ProfileRow
            icon="T"
            title="Trading Preferences"
            subtitle="Configure your trading behavior"
            onPress={openPreferences}
          />
        </View>

        {/* =============================================== */}
        {/* RISK SUMMARY */}
        {/* =============================================== */}

        <View style={styles.riskSummary}>
          <Text style={styles.riskSummaryTitle}>
            RISK MANAGEMENT
          </Text>

          <View style={styles.riskMetrics}>
            <View style={styles.riskMetric}>
              <Text style={styles.riskMetricValue}>
                1%
              </Text>

              <Text style={styles.riskMetricLabel}>
                BASE RISK
              </Text>
            </View>

            <View style={styles.riskMetricDivider} />

            <View style={styles.riskMetric}>
              <Text style={styles.riskMetricValue}>
                2%
              </Text>

              <Text style={styles.riskMetricLabel}>
                HARD MAX
              </Text>
            </View>

            <View style={styles.riskMetricDivider} />

            <View style={styles.riskMetric}>
              <Text style={styles.riskMetricValue}>
                1:3
              </Text>

              <Text style={styles.riskMetricLabel}>
                RISK / REWARD
              </Text>
            </View>
          </View>

          <Text style={styles.riskSummaryText}>
            Final position sizing and execution remain
            controlled by the BALLY TRADES BOT backend
            safety and validation pipeline.
          </Text>
        </View>

        {/* =============================================== */}
        {/* ACTIVITY */}
        {/* =============================================== */}

        <SectionHeader title="ACTIVITY" />

        <View style={styles.sectionCard}>
          <ProfileRow
            icon="N"
            title="Notifications"
            subtitle="Signals, system alerts and announcements"
            onPress={openNotifications}
          />

          <View style={styles.rowDivider} />

          <View style={styles.toggleRow}>
            <View style={styles.rowIcon}>
              <Text style={styles.rowIconText}>
                ●
              </Text>
            </View>

            <View style={styles.rowContent}>
              <Text style={styles.rowTitle}>
                Notification Alerts
              </Text>

              <Text style={styles.rowSubtitle}>
                Receive important trading updates
              </Text>
            </View>

            <Switch
              value={notificationsEnabled}
              onValueChange={setNotificationsEnabled}
              trackColor={{
                false: '#252B38',
                true: '#334BFF',
              }}
              thumbColor="#FFFFFF"
              accessibilityLabel="Notification alerts"
            />
          </View>

          <View style={styles.rowDivider} />

          <ProfileRow
            icon="H"
            title="Trading History"
            subtitle="Completed trades and performance"
            onPress={openHistory}
          />
        </View>

        {/* =============================================== */}
        {/* HISTORY FEATURE CARD */}
        {/* =============================================== */}

        <Pressable
          onPress={openHistory}
          style={({pressed}) => [
            styles.historyFeatureCard,
            pressed && styles.buttonPressed,
          ]}>
          <View>
            <Text style={styles.historyFeatureLabel}>
              PERFORMANCE
            </Text>

            <Text style={styles.historyFeatureTitle}>
              Trading History
            </Text>

            <Text style={styles.historyFeatureText}>
              Review completed trades, profit and loss,
              win rate and overall trading performance.
            </Text>
          </View>

          <Text style={styles.historyFeatureArrow}>
            →
          </Text>
        </Pressable>

        {/* =============================================== */}
        {/* SECURITY */}
        {/* =============================================== */}

        <SectionHeader title="SECURITY" />

        <View style={styles.sectionCard}>
          <View style={styles.toggleRow}>
            <View style={styles.rowIcon}>
              <Text style={styles.rowIconText}>
                B
              </Text>
            </View>

            <View style={styles.rowContent}>
              <Text style={styles.rowTitle}>
                Biometric Login
              </Text>

              <Text style={styles.rowSubtitle}>
                Secure access using biometrics
              </Text>
            </View>

            <Switch
              value={biometricEnabled}
              onValueChange={setBiometricEnabled}
              trackColor={{
                false: '#252B38',
                true: '#334BFF',
              }}
              thumbColor="#FFFFFF"
              accessibilityLabel="Biometric login"
            />
          </View>

          <View style={styles.rowDivider} />

          <ProfileRow
            icon="S"
            title="Security"
            subtitle="Password and login protection"
            onPress={openSecurity}
          />
        </View>

        {/* =============================================== */}
        {/* SETTINGS */}
        {/* =============================================== */}

        <SectionHeader title="APPLICATION" />

        <View style={styles.sectionCard}>
          <ProfileRow
            icon="⚙"
            title="Settings"
            subtitle="Application preferences and configuration"
            onPress={openSettings}
          />
        </View>

        {/* =============================================== */}
        {/* LOGOUT */}
        {/* =============================================== */}

        <Pressable
          onPress={confirmLogout}
          style={({pressed}) => [
            styles.logoutButton,
            pressed && styles.buttonPressed,
          ]}>
          <Text style={styles.logoutText}>
            LOG OUT
          </Text>
        </Pressable>

        {/* =============================================== */}
        {/* FOOTER */}
        {/* =============================================== */}

        <View style={styles.footer}>
          <View
            style={[
              styles.footerDot,
              !isLive && styles.footerDotOffline,
            ]}
          />

          <Text style={styles.footerText}>
            {isLive
              ? 'BALLY FLOW ACCOUNT CONNECTED'
              : 'BALLY FLOW WAITING FOR BACKEND CONNECTION'}
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
    width: 330,
    height: 330,
    borderRadius: 165,
    backgroundColor: '#111B5B',
    opacity: 0.16,
    top: -190,
    right: -120,
  },

  glowBottom: {
    position: 'absolute',
    width: 300,
    height: 300,
    borderRadius: 150,
    backgroundColor: '#15204B',
    opacity: 0.12,
    bottom: -150,
    left: -150,
  },

  /* HEADER */

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 24,
  },

  appName: {
    color: '#7083FF',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 2.2,
    marginBottom: 7,
  },

  screenTitle: {
    color: '#FFFFFF',
    fontSize: 27,
    fontWeight: '900',
    letterSpacing: 0.3,
  },

  screenSubtitle: {
    color: '#69758E',
    fontSize: 11,
    marginTop: 6,
  },

  connectionBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0D211A',
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 7,
    marginTop: 8,
  },

  connectionBadgeOffline: {
    backgroundColor: '#20191B',
  },

  connectionDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 6,
  },

  connectionDotOffline: {
    backgroundColor: '#FF7185',
  },

  connectionText: {
    color: '#35E68A',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1,
  },

  connectionTextOffline: {
    color: '#FF7185',
  },

  /* PROFILE */

  profileCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 20,
    padding: 17,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 27,
  },

  avatarWrapper: {
    position: 'relative',
    marginRight: 15,
  },

  avatarPressed: {
    opacity: 0.8,
    transform: [{scale: 0.97}],
  },

  avatarImage: {
    width: 66,
    height: 66,
    borderRadius: 33,
  },

  avatarCameraBadge: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#334BFF',
    borderWidth: 1.5,
    borderColor: '#0A0E18',
    alignItems: 'center',
    justifyContent: 'center',
  },

  avatarCameraBadgeText: {
    fontSize: 11,
  },

  avatar: {
    width: 66,
    height: 66,
    borderRadius: 33,
    backgroundColor: '#111A38',
    borderWidth: 1,
    borderColor: '#334BFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 15,
  },

  avatarText: {
    color: '#FFFFFF',
    fontSize: 25,
    fontWeight: '900',
  },

  profileInfo: {
    flex: 1,
  },

  profileName: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '900',
  },

  profileEmail: {
    color: '#68748B',
    fontSize: 10,
    marginTop: 4,
  },

  accountStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 9,
  },

  accountStatusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 6,
  },

  accountStatusText: {
    color: '#35E68A',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  /* SECTIONS */

  sectionTitle: {
    color: '#A8B2C7',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 1.6,
    marginBottom: 10,
    marginTop: 4,
  },

  sectionCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 18,
    overflow: 'hidden',
    marginBottom: 25,
  },

  profileRow: {
    minHeight: 70,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
  },

  profileRowPressed: {
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

  rowIconDanger: {
    backgroundColor: '#251317',
  },

  rowIconText: {
    color: '#7083FF',
    fontSize: 12,
    fontWeight: '900',
  },

  rowIconTextDanger: {
    color: '#FF7185',
  },

  rowContent: {
    flex: 1,
  },

  rowTitle: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '800',
  },

  rowTitleDanger: {
    color: '#FF7185',
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

  rowArrowDanger: {
    color: '#FF7185',
  },

  rowDivider: {
    height: 1,
    backgroundColor: '#172032',
    marginLeft: 62,
  },

  toggleRow: {
    minHeight: 70,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
  },

  /* BOT */

  botCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 19,
    padding: 16,
    marginBottom: 25,
  },

  botTop: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  botIcon: {
    width: 42,
    height: 42,
    borderRadius: 13,
    backgroundColor: '#111A38',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
  },

  botIconText: {
    color: '#7083FF',
    fontSize: 15,
    fontWeight: '900',
  },

  botInfo: {
    flex: 1,
  },

  botTitle: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 0.3,
  },

  botSubtitle: {
    color: '#647087',
    fontSize: 8,
    marginTop: 4,
  },

  botDivider: {
    height: 1,
    backgroundColor: '#1B2435',
    marginVertical: 16,
  },

  botMetrics: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  botMetric: {
    flex: 1,
    alignItems: 'center',
  },

  botMetricDivider: {
    width: 1,
    height: 30,
    backgroundColor: '#20293A',
  },

  botMetricLabel: {
    color: '#5D6981',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  botMetricValue: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '900',
    marginTop: 5,
  },

  botOn: {
    color: '#35E68A',
  },

  botOff: {
    color: '#8995B1',
  },

  manageBotButton: {
    height: 44,
    borderRadius: 11,
    backgroundColor: '#111A38',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 17,
    borderWidth: 1,
    borderColor: '#27345C',
  },

  manageBotButtonText: {
    color: '#7083FF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  /* RISK */

  riskSummary: {
    backgroundColor: '#0B1020',
    borderWidth: 1,
    borderColor: '#1C2949',
    borderRadius: 17,
    padding: 15,
    marginTop: -8,
    marginBottom: 25,
  },

  riskSummaryTitle: {
    color: '#7083FF',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1.1,
    marginBottom: 14,
  },

  riskMetrics: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  riskMetric: {
    flex: 1,
    alignItems: 'center',
  },

  riskMetricDivider: {
    width: 1,
    height: 33,
    backgroundColor: '#25304A',
  },

  riskMetricValue: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '900',
  },

  riskMetricLabel: {
    color: '#68748B',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.7,
    marginTop: 4,
  },

  riskSummaryText: {
    color: '#68748B',
    fontSize: 8,
    lineHeight: 14,
    marginTop: 15,
  },

  /* HISTORY */

  historyFeatureCard: {
    minHeight: 115,
    backgroundColor: '#101A38',
    borderWidth: 1,
    borderColor: '#263765',
    borderRadius: 18,
    padding: 16,
    marginTop: -8,
    marginBottom: 25,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },

  historyFeatureLabel: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.2,
  },

  historyFeatureTitle: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '900',
    marginTop: 6,
  },

  historyFeatureText: {
    color: '#8490A8',
    fontSize: 9,
    lineHeight: 15,
    marginTop: 6,
    maxWidth: 250,
  },

  historyFeatureArrow: {
    color: '#7083FF',
    fontSize: 26,
    marginLeft: 10,
  },

  /* LOGOUT */

  logoutButton: {
    minHeight: 52,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#542832',
    backgroundColor: '#1B1014',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 4,
  },

  logoutText: {
    color: '#FF7185',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 1.1,
  },

  buttonPressed: {
    opacity: 0.78,
    transform: [{scale: 0.985}],
  },

  /* FOOTER */

  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 24,
  },

  footerDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 6,
  },

  footerDotOffline: {
    backgroundColor: '#FF7185',
  },

  footerText: {
    color: '#46526A',
    fontSize: 7,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
});





