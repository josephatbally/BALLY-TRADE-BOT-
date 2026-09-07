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
import {BRANDING} from '../config/branding';

type Props = NativeStackScreenProps<
  RootStackParamList,
  'BotControl'
>;

type BotStatus =
  | 'OFFLINE'
  | 'DISABLED'
  | 'AUTHORIZED'
  | 'ACTIVE';

type StatusTone =
  | 'red'
  | 'yellow'
  | 'blue'
  | 'green';

type StatusItemProps = {
  label: string;
  value: string;
  tone: StatusTone;
};

function StatusItem({
  label,
  value,
  tone,
}: StatusItemProps) {
  return (
    <View style={styles.statusItem}>
      <View
        style={[
          styles.statusDot,
          tone === 'red' && styles.statusDotRed,
          tone === 'yellow' && styles.statusDotYellow,
          tone === 'blue' && styles.statusDotBlue,
          tone === 'green' && styles.statusDotGreen,
        ]}
      />

      <View style={styles.statusCopy}>
        <Text style={styles.statusLabel}>{label}</Text>
        <Text style={styles.statusValue}>{value}</Text>
      </View>
    </View>
  );
}

type ControlRowProps = {
  icon: string;
  title: string;
  subtitle: string;
  right: React.ReactNode;
};

function ControlRow({
  icon,
  title,
  subtitle,
  right,
}: ControlRowProps) {
  return (
    <View style={styles.controlRow}>
      <View style={styles.controlIcon}>
        <Text style={styles.controlIconText}>{icon}</Text>
      </View>

      <View style={styles.controlCopy}>
        <Text style={styles.controlTitle}>{title}</Text>
        <Text style={styles.controlSubtitle}>{subtitle}</Text>
      </View>

      {right}
    </View>
  );
}

export default function BotControlScreen({
  route,
  navigation,
}: Props) {
  const insets = useSafeAreaInsets();

  /*
   * ============================================================
   * BACKEND SAFETY MODEL
   * ============================================================
   *
   * This screen is a mobile control surface only.
   *
   * It NEVER:
   * - initializes MT5
   * - sends orders
   * - enables LIVE_TRADING
   * - changes backend execution flags
   * - bypasses risk validation
   *
   * The backend remains authoritative for all trading permissions.
   */

  const [botRequested, setBotRequested] =
    React.useState(false);

  const [autoExecutionRequested, setAutoExecutionRequested] =
    React.useState(false);

  /*
   * These are intentionally false until real authenticated
   * backend APIs are connected.
   */
  const backendConnected = false;
  const backendAuthorized = false;
  const executionEnabled = false;
  const liveTradingEnabled = false;

  const botStatus: BotStatus =
    !backendConnected
      ? 'OFFLINE'
      : !backendAuthorized
        ? 'DISABLED'
        : executionEnabled
          ? 'ACTIVE'
          : 'AUTHORIZED';

  const displayName =
    route.params?.displayName ||
    route.params?.firstName ||
    'Trader';

  const handleBotToggle = (value: boolean) => {
    if (!value) {
      setBotRequested(false);
      setAutoExecutionRequested(false);
      return;
    }

    if (!backendConnected) {
      Alert.alert(
        'Backend Offline',
        'BALLY FLOW cannot request bot activation because the authenticated backend is not connected.',
      );
      return;
    }

    if (!backendAuthorized) {
      Alert.alert(
        'Authorization Required',
        'Bot activation must be explicitly authorized by the authenticated BALLY TRADES BOT backend.',
      );
      return;
    }

    Alert.alert(
      'Request Bot Activation',
      'This requests bot activation from the backend. Live trading remains disabled unless every backend risk and execution safety control explicitly authorizes execution.',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Request Activation',
          onPress: () => {
            setBotRequested(true);
          },
        },
      ],
    );
  };

  const handleAutoExecutionToggle = (value: boolean) => {
    if (!value) {
      setAutoExecutionRequested(false);
      return;
    }

    if (!botRequested) {
      Alert.alert(
        'Bot Not Requested',
        'Request bot activation before requesting automated execution.',
      );
      return;
    }

    if (!backendAuthorized) {
      Alert.alert(
        'Backend Authorization Required',
        'Automated execution cannot be enabled from the mobile application without explicit backend authorization.',
      );
      return;
    }

    Alert.alert(
      'Execution Request',
      'This does not enable live trading directly. Final execution permission must be granted by the backend after all safety checks pass.',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Request Permission',
          onPress: () => {
            setAutoExecutionRequested(true);
          },
        },
      ],
    );
  };

  const getStatusTone = (): StatusTone => {
    switch (botStatus) {
      case 'ACTIVE':
        return 'green';

      case 'AUTHORIZED':
        return 'blue';

      case 'DISABLED':
        return 'yellow';

      case 'OFFLINE':
      default:
        return 'red';
    }
  };

  const getStatusDescription = () => {
    switch (botStatus) {
      case 'ACTIVE':
        return 'Backend-authorized bot operation';

      case 'AUTHORIZED':
        return 'Authorized but execution is not enabled';

      case 'DISABLED':
        return 'Backend has not authorized activation';

      case 'OFFLINE':
      default:
        return 'Waiting for authenticated backend connection';
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
            paddingBottom: Math.max(insets.bottom + 36, 36),
          },
        ]}>

        {/* HEADER */}

        <View style={styles.header}>
          <View>
            <Text style={styles.appName}>
              {BRANDING.appName}
            </Text>

            <Text style={styles.title}>
              BOT CONTROL
            </Text>

            <Text style={styles.subtitle}>
              Control and monitor trading automation
            </Text>
          </View>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Close bot control"
            onPress={() => navigation.goBack()}
            style={styles.closeButton}>
            <Text style={styles.closeButtonText}>×</Text>
          </Pressable>
        </View>

        {/* USER */}

        <View style={styles.userCard}>
          <View style={styles.userAvatar}>
            <Text style={styles.userAvatarText}>
              {displayName.charAt(0).toUpperCase()}
            </Text>
          </View>

          <View style={styles.userCopy}>
            <Text style={styles.userLabel}>
              AUTHENTICATED USER
            </Text>

            <Text style={styles.userName}>
              {displayName}
            </Text>

            <Text style={styles.userEmail}>
              {route.params?.email}
            </Text>
          </View>
        </View>

        {/* STATUS */}

        <Text style={styles.sectionTitle}>
          BOT STATUS
        </Text>

        <View style={styles.statusCard}>
          <View style={styles.statusHeader}>
            <View>
              <Text style={styles.statusMainLabel}>
                CURRENT STATUS
              </Text>

              <Text
                style={[
                  styles.statusMainValue,
                  botStatus === 'OFFLINE' &&
                    styles.statusTextRed,
                  botStatus === 'DISABLED' &&
                    styles.statusTextYellow,
                  botStatus === 'AUTHORIZED' &&
                    styles.statusTextBlue,
                  botStatus === 'ACTIVE' &&
                    styles.statusTextGreen,
                ]}>
                {botStatus}
              </Text>
            </View>

            <View
              style={[
                styles.statusBadge,
                botStatus === 'OFFLINE' &&
                  styles.statusBadgeRed,
                botStatus === 'DISABLED' &&
                  styles.statusBadgeYellow,
                botStatus === 'AUTHORIZED' &&
                  styles.statusBadgeBlue,
                botStatus === 'ACTIVE' &&
                  styles.statusBadgeGreen,
              ]}>
              <View
                style={[
                  styles.statusBadgeDot,
                  getStatusTone() === 'red' &&
                    styles.statusDotRed,
                  getStatusTone() === 'yellow' &&
                    styles.statusDotYellow,
                  getStatusTone() === 'blue' &&
                    styles.statusDotBlue,
                  getStatusTone() === 'green' &&
                    styles.statusDotGreen,
                ]}
              />
            </View>
          </View>

          <Text style={styles.statusDescription}>
            {getStatusDescription()}
          </Text>

          <View style={styles.statusDivider} />

          <StatusItem
            label="BACKEND CONNECTION"
            value={
              backendConnected
                ? 'CONNECTED'
                : 'OFFLINE'
            }
            tone={
              backendConnected
                ? 'green'
                : 'red'
            }
          />

          <StatusItem
            label="BACKEND AUTHORIZATION"
            value={
              backendAuthorized
                ? 'AUTHORIZED'
                : 'NOT AUTHORIZED'
            }
            tone={
              backendAuthorized
                ? 'green'
                : 'yellow'
            }
          />

          <StatusItem
            label="EXECUTION ENGINE"
            value={
              executionEnabled
                ? 'ENABLED'
                : 'DISABLED'
            }
            tone={
              executionEnabled
                ? 'green'
                : 'red'
            }
          />

          <StatusItem
            label="LIVE TRADING"
            value={
              liveTradingEnabled
                ? 'ENABLED'
                : 'DISABLED'
            }
            tone={
              liveTradingEnabled
                ? 'green'
                : 'red'
            }
          />
        </View>

        {/* AUTOMATION */}

        <Text style={styles.sectionTitle}>
          AUTOMATION CONTROL
        </Text>

        <View style={styles.card}>
          <ControlRow
            icon="◈"
            title="Bot Activation"
            subtitle={
              botRequested
                ? 'Activation request pending backend synchronization'
                : 'Request bot activation from the authenticated backend'
            }
            right={
              <Switch
                accessibilityLabel="Bot activation"
                value={botRequested}
                onValueChange={handleBotToggle}
                trackColor={{
                  false: '#273044',
                  true: '#3449A0',
                }}
                thumbColor={
                  botRequested
                    ? '#7083FF'
                    : '#8995B1'
                }
              />
            }
          />

          <View style={styles.divider} />

          <ControlRow
            icon="ϟ"
            title="Automated Execution"
            subtitle={
              autoExecutionRequested
                ? 'Execution permission requested from backend'
                : 'Requires explicit backend execution approval'
            }
            right={
              <Switch
                accessibilityLabel="Automated execution"
                value={autoExecutionRequested}
                onValueChange={handleAutoExecutionToggle}
                trackColor={{
                  false: '#273044',
                  true: '#3449A0',
                }}
                thumbColor={
                  autoExecutionRequested
                    ? '#7083FF'
                    : '#8995B1'
                }
              />
            }
          />
        </View>

        {/* SAFETY */}

        <Text style={styles.sectionTitle}>
          EXECUTION SAFETY
        </Text>

        <View style={styles.safetyCard}>
          <View style={styles.safetyHeader}>
            <View style={styles.safetyIcon}>
              <Text style={styles.safetyIconText}>
                !
              </Text>
            </View>

            <View style={styles.safetyCopy}>
              <Text style={styles.safetyTitle}>
                LIVE TRADING PROTECTION
              </Text>

              <Text style={styles.safetySubtitle}>
                Mobile controls cannot bypass backend safety
              </Text>
            </View>
          </View>

          <View style={styles.safetyList}>
            <Text style={styles.safetyItem}>
              • Backend authentication required
            </Text>

            <Text style={styles.safetyItem}>
              • Risk validation required
            </Text>

            <Text style={styles.safetyItem}>
              • Broker and margin validation required
            </Text>

            <Text style={styles.safetyItem}>
              • MT5 execution safety controls required
            </Text>

            <Text style={styles.safetyItem}>
              • Explicit backend authorization required
            </Text>
          </View>
        </View>

        {/* BACKEND */}

        <Text style={styles.sectionTitle}>
          BACKEND INTEGRATION
        </Text>

        <View style={styles.backendCard}>
          <View
            style={[
              styles.backendDot,
              backendConnected &&
                styles.backendDotOnline,
            ]}
          />

          <View style={styles.backendContent}>
            <Text style={styles.backendTitle}>
              AUTHENTICATED BACKEND
            </Text>

            <Text style={styles.backendText}>
              The mobile application is prepared to
              synchronize bot status with the BALLY TRADES
              BOT backend. Until authenticated backend APIs
              explicitly authorize activation and execution,
              live trading remains disabled.
            </Text>
          </View>
        </View>

        {/* NAVIGATION */}

        <View style={styles.navigationRow}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Open settings"
            onPress={() =>
              navigation.navigate(
                'Settings',
                route.params,
              )
            }
            style={styles.secondaryButton}>
            <Text style={styles.secondaryButtonText}>
              SETTINGS
            </Text>
          </Pressable>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Open dashboard"
            onPress={() =>
              navigation.navigate(
                'MainTabs',
                route.params,
              )
            }
            style={styles.primaryButton}>
            <Text style={styles.primaryButtonText}>
              DASHBOARD
            </Text>
          </Pressable>
        </View>

        {/* FOOTER */}

        <View style={styles.footer}>
          <Text style={styles.footerBrand}>
            {BRANDING.appName}
          </Text>

          <Text style={styles.footerText}>
            Execute your edge
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
    width: 320,
    height: 320,
    borderRadius: 160,
    backgroundColor: '#111B5B',
    opacity: 0.16,
    top: -190,
    right: -110,
  },

  glowBottom: {
    position: 'absolute',
    width: 280,
    height: 280,
    borderRadius: 140,
    backgroundColor: '#15204B',
    opacity: 0.12,
    bottom: -130,
    left: -130,
  },

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

  title: {
    color: '#FFFFFF',
    fontSize: 28,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  subtitle: {
    color: '#69758E',
    fontSize: 11,
    marginTop: 6,
  },

  closeButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#11182A',
    borderWidth: 1,
    borderColor: '#273044',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 5,
  },

  closeButtonText: {
    color: '#A8B2C7',
    fontSize: 23,
    fontWeight: '300',
    lineHeight: 25,
  },

  userCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 17,
    padding: 14,
    marginBottom: 25,
  },

  userAvatar: {
    width: 45,
    height: 45,
    borderRadius: 23,
    backgroundColor: '#111B35',
    borderWidth: 1,
    borderColor: '#31416A',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },

  userAvatarText: {
    color: '#7083FF',
    fontSize: 18,
    fontWeight: '900',
  },

  userCopy: {
    flex: 1,
  },

  userLabel: {
    color: '#647087',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1.2,
  },

  userName: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '900',
    marginTop: 4,
  },

  userEmail: {
    color: '#69758E',
    fontSize: 9,
    marginTop: 3,
  },

  sectionTitle: {
    color: '#7C879D',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1.5,
    marginBottom: 10,
  },

  statusCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 17,
    padding: 15,
    marginBottom: 24,
  },

  statusHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },

  statusMainLabel: {
    color: '#647087',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1.1,
  },

  statusMainValue: {
    color: '#FFFFFF',
    fontSize: 21,
    fontWeight: '900',
    marginTop: 5,
    letterSpacing: 0.6,
  },

  statusTextRed: {
    color: '#FF7185',
  },

  statusTextYellow: {
    color: '#FFBE63',
  },

  statusTextBlue: {
    color: '#7083FF',
  },

  statusTextGreen: {
    color: '#58D7A0',
  },

  statusBadge: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
  },

  statusBadgeRed: {
    backgroundColor: '#25131B',
  },

  statusBadgeYellow: {
    backgroundColor: '#2A2114',
  },

  statusBadgeBlue: {
    backgroundColor: '#111B35',
  },

  statusBadgeGreen: {
    backgroundColor: '#10261F',
  },

  statusBadgeDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },

  statusDescription: {
    color: '#69758E',
    fontSize: 9,
    marginTop: 8,
    lineHeight: 15,
  },

  statusDivider: {
    height: 1,
    backgroundColor: '#172032',
    marginVertical: 14,
  },

  statusItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },

  statusDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    marginRight: 10,
  },

  statusDotRed: {
    backgroundColor: '#FF7185',
  },

  statusDotYellow: {
    backgroundColor: '#FFBE63',
  },

  statusDotBlue: {
    backgroundColor: '#7083FF',
  },

  statusDotGreen: {
    backgroundColor: '#58D7A0',
  },

  statusCopy: {
    flexDirection: 'row',
    flex: 1,
    justifyContent: 'space-between',
    alignItems: 'center',
  },

  statusLabel: {
    color: '#647087',
    fontSize: 8,
    fontWeight: '800',
    letterSpacing: 0.4,
  },

  statusValue: {
    color: '#A8B2C7',
    fontSize: 8,
    fontWeight: '900',
  },

  card: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 17,
    overflow: 'hidden',
    marginBottom: 24,
  },

  controlRow: {
    minHeight: 76,
    paddingHorizontal: 14,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
  },

  controlIcon: {
    width: 37,
    height: 37,
    borderRadius: 11,
    backgroundColor: '#11182A',
    borderWidth: 1,
    borderColor: '#202B40',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
  },

  controlIconText: {
    color: '#7083FF',
    fontSize: 15,
    fontWeight: '800',
  },

  controlCopy: {
    flex: 1,
    paddingRight: 10,
  },

  controlTitle: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '900',
  },

  controlSubtitle: {
    color: '#647087',
    fontSize: 8,
    lineHeight: 13,
    marginTop: 4,
  },

  divider: {
    height: 1,
    backgroundColor: '#172032',
    marginLeft: 62,
  },

  safetyCard: {
    backgroundColor: '#0B1020',
    borderRadius: 17,
    borderWidth: 1,
    borderColor: '#202C49',
    padding: 14,
    marginBottom: 24,
  },

  safetyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  safetyIcon: {
    width: 37,
    height: 37,
    borderRadius: 11,
    backgroundColor: '#211821',
    borderWidth: 1,
    borderColor: '#493143',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
  },

  safetyIconText: {
    color: '#FF7185',
    fontSize: 16,
    fontWeight: '900',
  },

  safetyCopy: {
    flex: 1,
  },

  safetyTitle: {
    color: '#FFB2BE',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  safetySubtitle: {
    color: '#66738C',
    fontSize: 8,
    marginTop: 4,
  },

  safetyList: {
    marginTop: 15,
    paddingTop: 13,
    borderTopWidth: 1,
    borderTopColor: '#1B2841',
  },

  safetyItem: {
    color: '#71809A',
    fontSize: 8,
    lineHeight: 17,
  },

  backendCard: {
    flexDirection: 'row',
    backgroundColor: '#0B1020',
    borderRadius: 13,
    borderWidth: 1,
    borderColor: '#202C49',
    padding: 13,
    marginBottom: 24,
  },

  backendDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: '#FF7185',
    marginTop: 4,
    marginRight: 9,
  },

  backendDotOnline: {
    backgroundColor: '#58D7A0',
  },

  backendContent: {
    flex: 1,
  },

  backendTitle: {
    color: '#8995B1',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1,
    marginBottom: 5,
  },

  backendText: {
    color: '#5E6B83',
    fontSize: 8,
    lineHeight: 14,
  },

  navigationRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 25,
  },

  secondaryButton: {
    flex: 1,
    height: 48,
    borderRadius: 13,
    borderWidth: 1,
    borderColor: '#273044',
    backgroundColor: '#0A0E18',
    alignItems: 'center',
    justifyContent: 'center',
  },

  secondaryButtonText: {
    color: '#A8B2C7',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1,
  },

  primaryButton: {
    flex: 1,
    height: 48,
    borderRadius: 13,
    backgroundColor: '#253A9A',
    borderWidth: 1,
    borderColor: '#5067E5',
    alignItems: 'center',
    justifyContent: 'center',
  },

  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1,
  },

  footer: {
    alignItems: 'center',
    marginTop: 2,
  },

  footerBrand: {
    color: '#7083FF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 2,
  },

  footerText: {
    color: '#46526A',
    fontSize: 7,
    marginTop: 5,
    letterSpacing: 0.7,
  },
});
