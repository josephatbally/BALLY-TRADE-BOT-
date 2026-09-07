
import React from 'react';
import {
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
import {useTheme} from '../theme/ThemeContext';

type SettingsScreenProps = NativeStackScreenProps<
  RootStackParamList,
  'Settings'
>;

type TradingMode = 'TECHNICAL' | 'HYBRID';

function SettingsRow({
  icon,
  title,
  subtitle,
  right,
  onPress,
  colors,
}: {
  icon: string;
  title: string;
  subtitle: string;
  right?: React.ReactNode;
  onPress?: () => void;
  colors: {
    surface: string;
    inputBackground: string;
    border: string;
    primary: string;
    text: string;
    textSecondary: string;
    textMuted: string;
  };
}) {
  return (
    <Pressable
      onPress={onPress}
      disabled={!onPress}
      style={({pressed}) => [
        styles.settingRow,
        pressed &&
          onPress && {
            backgroundColor: colors.inputBackground,
          },
      ]}>
      <View
        style={[
          styles.settingIcon,
          {
            backgroundColor: colors.inputBackground,
            borderColor: colors.border,
          },
        ]}>
        <Text
          style={[
            styles.settingIconText,
            {
              color: colors.primary,
            },
          ]}>
          {icon}
        </Text>
      </View>

      <View style={styles.settingContent}>
        <Text
          style={[
            styles.settingTitle,
            {
              color: colors.text,
            },
          ]}>
          {title}
        </Text>

        <Text
          style={[
            styles.settingSubtitle,
            {
              color: colors.textMuted,
            },
          ]}>
          {subtitle}
        </Text>
      </View>

      {right ?? (
        <Text
          style={[
            styles.arrow,
            {
              color: colors.textMuted,
            },
          ]}>
          ›
        </Text>
      )}
    </Pressable>
  );
}

function SectionTitle({
  children,
  color,
}: {
  children: string;
  color: string;
}) {
  return (
    <View style={styles.sectionHeader}>
      <Text
        style={[
          styles.sectionTitle,
          {
            color,
          },
        ]}>
        {children}
      </Text>
    </View>
  );
}

export default function SettingsScreen({
  route,
  navigation,
}: SettingsScreenProps) {
  const insets = useSafeAreaInsets();
  const {theme, themeMode} = useTheme();

  const user = route.params;

  const [tradingMode, setTradingMode] =
    React.useState<TradingMode>('TECHNICAL');

  const [lotSize, setLotSize] =
    React.useState('0.01');

  const [notificationsEnabled, setNotificationsEnabled] =
    React.useState(true);

  const [soundEnabled, setSoundEnabled] =
    React.useState(true);

  const [vibrationEnabled, setVibrationEnabled] =
    React.useState(true);

  const [priceAlertsEnabled, setPriceAlertsEnabled] =
    React.useState(true);

  const [confirmationsEnabled, setConfirmationsEnabled] =
    React.useState(true);

  const displayName =
    user?.displayName ||
    user?.firstName ||
    'Trader';

  const themeLabel =
    themeMode === 'DARK'
      ? 'BALLY DARK'
      : themeMode === 'LIGHT'
        ? 'LIGHT'
        : 'SYSTEM';

  const switchTrackColor = {
    false: theme.colors.border,
    true: theme.colors.primaryStrong,
  };

  const switchThumbColor = (
    enabled: boolean,
  ) =>
    enabled
      ? theme.colors.primary
      : theme.colors.textMuted;

  return (
    <View
      style={[
        styles.root,
        {
          backgroundColor: theme.colors.background,
        },
      ]}>
      <StatusBar
        barStyle={
          theme.isDark
            ? 'light-content'
            : 'dark-content'
        }
      />

      <View
        style={[
          styles.glowTop,
          {
            backgroundColor: theme.colors.primaryStrong,
          },
        ]}
      />

      <View
        style={[
          styles.glowBottom,
          {
            backgroundColor: theme.colors.primary,
          },
        ]}
      />

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[
          styles.scrollContent,
          {
            paddingTop: Math.max(insets.top, 20),
            paddingBottom: Math.max(
              insets.bottom + 36,
              36,
            ),
          },
        ]}>

        {/* HEADER */}

        <View style={styles.header}>
          <View style={styles.headerContent}>
            <Text
              style={[
                styles.appName,
                {
                  color: theme.colors.primary,
                },
              ]}>
              {BRANDING.appName}
            </Text>

            <Text
              style={[
                styles.title,
                {
                  color: theme.colors.text,
                },
              ]}>
              SETTINGS
            </Text>

            <Text
              style={[
                styles.subtitle,
                {
                  color: theme.colors.textMuted,
                },
              ]}>
              Configure your BALLY FLOW experience
            </Text>
          </View>

          <Pressable
            onPress={() => navigation.goBack()}
            style={[
              styles.closeButton,
              {
                backgroundColor:
                  theme.colors.inputBackground,
                borderColor: theme.colors.border,
              },
            ]}>
            <Text
              style={[
                styles.closeButtonText,
                {
                  color: theme.colors.textSecondary,
                },
              ]}>
              ×
            </Text>
          </Pressable>
        </View>

        {/* ACCOUNT */}

        <SectionTitle
          color={theme.colors.textMuted}>
          ACCOUNT
        </SectionTitle>

        <View
          style={[
            styles.card,
            {
              backgroundColor: theme.colors.surface,
              borderColor: theme.colors.border,
            },
          ]}>
          <SettingsRow
            icon="◎"
            title="Account Information"
            subtitle={displayName}
            colors={theme.colors}
            onPress={() =>
              navigation.navigate(
                'AccountInformation',
                user,
              )
            }
          />

          <View
            style={[
              styles.divider,
              {
                backgroundColor: theme.colors.divider,
              },
            ]}
          />

          <SettingsRow
            icon="⌁"
            title="Security"
            subtitle="Authentication and account protection"
            colors={theme.colors}
            onPress={() =>
              navigation.navigate(
                'Security',
                user,
              )
            }
          />
        </View>

        {/* TRADING */}

        <SectionTitle
          color={theme.colors.textMuted}>
          TRADING
        </SectionTitle>

        <View
          style={[
            styles.card,
            {
              backgroundColor: theme.colors.surface,
              borderColor: theme.colors.border,
            },
          ]}>

          <View style={styles.modeHeader}>
            <View
              style={[
                styles.settingIcon,
                {
                  backgroundColor:
                    theme.colors.inputBackground,
                  borderColor: theme.colors.border,
                },
              ]}>
              <Text
                style={[
                  styles.settingIconText,
                  {
                    color: theme.colors.primary,
                  },
                ]}>
                ◈
              </Text>
            </View>

            <View style={styles.settingContent}>
              <Text
                style={[
                  styles.settingTitle,
                  {
                    color: theme.colors.text,
                  },
                ]}>
                Trading Mode
              </Text>

              <Text
                style={[
                  styles.settingSubtitle,
                  {
                    color: theme.colors.textMuted,
                  },
                ]}>
                Select the analysis engine used by BALLY FLOW
              </Text>
            </View>
          </View>

          <View style={styles.modeSelector}>
            <Pressable
              onPress={() =>
                setTradingMode('TECHNICAL')
              }
              style={[
                styles.modeButton,
                {
                  backgroundColor:
                    theme.colors.inputBackground,
                  borderColor: theme.colors.border,
                },
                tradingMode === 'TECHNICAL' && {
                  borderColor: theme.colors.primary,
                  backgroundColor:
                    theme.colors.surfaceSecondary,
                },
              ]}>
              <Text
                style={[
                  styles.modeButtonTitle,
                  {
                    color: theme.colors.textSecondary,
                  },
                  tradingMode === 'TECHNICAL' && {
                    color: theme.colors.primary,
                  },
                ]}>
                TECHNICAL
              </Text>

              <Text
                style={[
                  styles.modeButtonSubtitle,
                  {
                    color: theme.colors.textMuted,
                  },
                ]}>
                SMC + technical analysis
              </Text>
            </Pressable>

            <Pressable
              onPress={() =>
                setTradingMode('HYBRID')
              }
              style={[
                styles.modeButton,
                {
                  backgroundColor:
                    theme.colors.inputBackground,
                  borderColor: theme.colors.border,
                },
                tradingMode === 'HYBRID' && {
                  borderColor: theme.colors.primary,
                  backgroundColor:
                    theme.colors.surfaceSecondary,
                },
              ]}>
              <Text
                style={[
                  styles.modeButtonTitle,
                  {
                    color: theme.colors.textSecondary,
                  },
                  tradingMode === 'HYBRID' && {
                    color: theme.colors.primary,
                  },
                ]}>
                HYBRID
              </Text>

              <Text
                style={[
                  styles.modeButtonSubtitle,
                  {
                    color: theme.colors.textMuted,
                  },
                ]}>
                Technical + fundamental
              </Text>
            </Pressable>
          </View>

          <View
            style={[
              styles.divider,
              {
                backgroundColor: theme.colors.divider,
              },
            ]}
          />

          <SettingsRow
            icon="◎"
            title="Bot Control"
            subtitle="Enable or disable automated trading"
            colors={theme.colors}
            onPress={() =>
              navigation.navigate(
                'BotControl',
                user,
              )
            }
          />

          <View
            style={[
              styles.divider,
              {
                backgroundColor: theme.colors.divider,
              },
            ]}
          />

          <SettingsRow
            icon="◌"
            title="Trading Preferences"
            subtitle="Configure preferred trading behaviour"
            colors={theme.colors}
            onPress={() =>
              navigation.navigate(
                'TradingPreferences',
                user,
              )
            }
          />

          <View
            style={[
              styles.divider,
              {
                backgroundColor: theme.colors.divider,
              },
            ]}
          />

          <SettingsRow
            icon="⌁"
            title="Risk Configuration"
            subtitle="Review and configure risk parameters"
            colors={theme.colors}
            onPress={() =>
              navigation.navigate(
                'RiskConfiguration',
                user,
              )
            }
          />

          <View
            style={[
              styles.divider,
              {
                backgroundColor: theme.colors.divider,
              },
            ]}
          />

          {/* LOT SIZE */}

          <View style={styles.lotSizeRow}>
            <View
              style={[
                styles.settingIcon,
                {
                  backgroundColor:
                    theme.colors.inputBackground,
                  borderColor: theme.colors.border,
                },
              ]}>
              <Text
                style={[
                  styles.settingIconText,
                  {
                    color: theme.colors.primary,
                  },
                ]}>
                ◇
              </Text>
            </View>

            <View style={styles.settingContent}>
              <Text
                style={[
                  styles.settingTitle,
                  {
                    color: theme.colors.text,
                  },
                ]}>
                Lot Size
              </Text>

              <Text
                style={[
                  styles.settingSubtitle,
                  {
                    color: theme.colors.textMuted,
                  },
                ]}>
                User trading lot preference
              </Text>
            </View>

            <View
              style={[
                styles.lotSizeValue,
                {
                  backgroundColor:
                    theme.colors.inputBackground,
                  borderColor: theme.colors.border,
                },
              ]}>
              <Text
                style={[
                  styles.lotSizeText,
                  {
                    color: theme.colors.text,
                  },
                ]}>
                {lotSize}
              </Text>
            </View>
          </View>

          <View style={styles.lotSizeControls}>
            <Pressable
              onPress={() =>
                setLotSize(previous => {
                  const value = Math.max(
                    0.01,
                    Number(previous) - 0.01,
                  );

                  return value.toFixed(2);
                })
              }
              style={[
                styles.lotButton,
                {
                  backgroundColor:
                    theme.colors.inputBackground,
                  borderColor: theme.colors.border,
                },
              ]}>
              <Text
                style={[
                  styles.lotButtonText,
                  {
                    color: theme.colors.textSecondary,
                  },
                ]}>
                −
              </Text>
            </Pressable>

            <View
              style={[
                styles.lotSliderTrack,
                {
                  backgroundColor:
                    theme.colors.divider,
                },
              ]}>
              <View
                style={[
                  styles.lotSliderFill,
                  {
                    width: `${Math.min(
                      100,
                      Math.max(
                        8,
                        Number(lotSize) * 100,
                      ),
                    )}%`,
                    backgroundColor:
                      theme.colors.primary,
                  },
                ]}
              />
            </View>

            <Pressable
              onPress={() =>
                setLotSize(previous => {
                  const value = Math.min(
                    1,
                    Number(previous) + 0.01,
                  );

                  return value.toFixed(2);
                })
              }
              style={[
                styles.lotButton,
                {
                  backgroundColor:
                    theme.colors.inputBackground,
                  borderColor: theme.colors.border,
                },
              ]}>
              <Text
                style={[
                  styles.lotButtonText,
                  {
                    color: theme.colors.textSecondary,
                  },
                ]}>
                +
              </Text>
            </Pressable>
          </View>

          <Text
            style={[
              styles.warningText,
              {
                color: theme.colors.textMuted,
              },
            ]}>
            Final position sizing remains subject to backend
            risk validation and broker limits.
          </Text>
        </View>

        {/* NOTIFICATIONS */}

        <SectionTitle
          color={theme.colors.textMuted}>
          NOTIFICATIONS
        </SectionTitle>

        <View
          style={[
            styles.card,
            {
              backgroundColor: theme.colors.surface,
              borderColor: theme.colors.border,
            },
          ]}>
          <SettingsRow
            icon="●"
            title="Notifications"
            subtitle="Receive BALLY FLOW alerts"
            colors={theme.colors}
            right={
              <Switch
                value={notificationsEnabled}
                onValueChange={setNotificationsEnabled}
                trackColor={switchTrackColor}
                thumbColor={switchThumbColor(
                  notificationsEnabled,
                )}
              />
            }
          />

          <View
            style={[
              styles.divider,
              {
                backgroundColor: theme.colors.divider,
              },
            ]}
          />

          <SettingsRow
            icon="♪"
            title="Alert Sound"
            subtitle="Play sound for important alerts"
            colors={theme.colors}
            right={
              <Switch
                value={soundEnabled}
                onValueChange={setSoundEnabled}
                trackColor={switchTrackColor}
                thumbColor={switchThumbColor(
                  soundEnabled,
                )}
              />
            }
          />

          <View
            style={[
              styles.divider,
              {
                backgroundColor: theme.colors.divider,
              },
            ]}
          />

          <SettingsRow
            icon="⌁"
            title="Vibration"
            subtitle="Vibrate when alerts arrive"
            colors={theme.colors}
            right={
              <Switch
                value={vibrationEnabled}
                onValueChange={setVibrationEnabled}
                trackColor={switchTrackColor}
                thumbColor={switchThumbColor(
                  vibrationEnabled,
                )}
              />
            }
          />

          <View
            style={[
              styles.divider,
              {
                backgroundColor: theme.colors.divider,
              },
            ]}
          />

          <SettingsRow
            icon="↗"
            title="Price Alerts"
            subtitle="Receive significant market movement alerts"
            colors={theme.colors}
            right={
              <Switch
                value={priceAlertsEnabled}
                onValueChange={setPriceAlertsEnabled}
                trackColor={switchTrackColor}
                thumbColor={switchThumbColor(
                  priceAlertsEnabled,
                )}
              />
            }
          />

          <View
            style={[
              styles.divider,
              {
                backgroundColor: theme.colors.divider,
              },
            ]}
          />

          <SettingsRow
            icon="✓"
            title="Trade Confirmations"
            subtitle="Confirm trading actions before execution"
            colors={theme.colors}
            right={
              <Switch
                value={confirmationsEnabled}
                onValueChange={setConfirmationsEnabled}
                trackColor={switchTrackColor}
                thumbColor={switchThumbColor(
                  confirmationsEnabled,
                )}
              />
            }
          />
        </View>

        {/* APP EXPERIENCE */}

        <SectionTitle
          color={theme.colors.textMuted}>
          APP EXPERIENCE
        </SectionTitle>

        <View
          style={[
            styles.card,
            {
              backgroundColor: theme.colors.surface,
              borderColor: theme.colors.border,
            },
          ]}>
          <SettingsRow
            icon="◐"
            title="Theme"
            subtitle={`Current appearance: ${themeLabel}`}
            colors={theme.colors}
            onPress={() =>
              navigation.navigate(
                'ThemeSelection',
                user,
              )
            }
          />

          <View
            style={[
              styles.divider,
              {
                backgroundColor: theme.colors.divider,
              },
            ]}
          />

          <SettingsRow
            icon="◉"
            title="Current Interface"
            subtitle={
              theme.isDark
                ? 'Dark interface is active'
                : 'Light interface is active'
            }
            colors={theme.colors}
            right={
              <View
                style={[
                  styles.interfaceBadge,
                  {
                    backgroundColor:
                      theme.colors.inputBackground,
                    borderColor: theme.colors.border,
                  },
                ]}>
                <View
                  style={[
                    styles.interfaceBadgeDot,
                    {
                      backgroundColor:
                        theme.colors.primary,
                    },
                  ]}
                />

                <Text
                  style={[
                    styles.interfaceBadgeText,
                    {
                      color: theme.colors.textSecondary,
                    },
                  ]}>
                  {theme.isDark ? 'DARK' : 'LIGHT'}
                </Text>
              </View>
            }
          />

          <View
            style={[
              styles.divider,
              {
                backgroundColor: theme.colors.divider,
              },
            ]}
          />

          <SettingsRow
            icon="!"
            title="Notifications Center"
            subtitle="View system and trading notifications"
            colors={theme.colors}
            onPress={() =>
              navigation.navigate(
                'Notifications',
                user,
              )
            }
          />
        </View>

        {/* BACKEND STATUS */}

        <View
          style={[
            styles.backendCard,
            {
              backgroundColor:
                theme.colors.surfaceSecondary,
              borderColor: theme.colors.border,
            },
          ]}>
          <View
            style={[
              styles.backendDot,
              {
                backgroundColor:
                  theme.colors.warning,
              },
            ]}
          />

          <View style={styles.backendContent}>
            <Text
              style={[
                styles.backendTitle,
                {
                  color: theme.colors.textSecondary,
                },
              ]}>
              BACKEND CONFIGURATION
            </Text>

            <Text
              style={[
                styles.backendText,
                {
                  color: theme.colors.textMuted,
                },
              ]}>
              Settings are prepared for synchronization
              with the BALLY TRADES BOT backend. Live account,
              risk and execution values must come from the
              authenticated backend.
            </Text>
          </View>
        </View>

        {/* FOOTER */}

        <View style={styles.footer}>
          <Text
            style={[
              styles.footerBrand,
              {
                color: theme.colors.primary,
              },
            ]}>
            {BRANDING.appName}
          </Text>

          <Text
            style={[
              styles.footerText,
              {
                color: theme.colors.textMuted,
              },
            ]}>
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
  },

  scrollContent: {
    paddingHorizontal: 18,
  },

  glowTop: {
    position: 'absolute',
    width: 320,
    height: 320,
    borderRadius: 160,
    opacity: 0.16,
    top: -190,
    right: -110,
  },

  glowBottom: {
    position: 'absolute',
    width: 280,
    height: 280,
    borderRadius: 140,
    opacity: 0.12,
    bottom: -130,
    left: -130,
  },

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 28,
  },

  headerContent: {
    flex: 1,
    paddingRight: 16,
  },

  appName: {
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 2.2,
    marginBottom: 7,
  },

  title: {
    fontSize: 28,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  subtitle: {
    fontSize: 11,
    marginTop: 6,
  },

  closeButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 5,
  },

  closeButtonText: {
    fontSize: 23,
    fontWeight: '300',
    lineHeight: 25,
  },

  sectionHeader: {
    marginBottom: 10,
  },

  sectionTitle: {
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1.5,
  },

  card: {
    borderWidth: 1,
    borderRadius: 17,
    overflow: 'hidden',
    marginBottom: 24,
  },

  settingRow: {
    minHeight: 70,
    paddingHorizontal: 14,
    paddingVertical: 11,
    flexDirection: 'row',
    alignItems: 'center',
  },

  settingContent: {
    flex: 1,
    paddingRight: 8,
  },

  settingIcon: {
    width: 37,
    height: 37,
    borderRadius: 11,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
  },

  settingIconText: {
    fontSize: 16,
    fontWeight: '800',
  },

  settingTitle: {
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 0.2,
  },

  settingSubtitle: {
    fontSize: 8,
    lineHeight: 13,
    marginTop: 4,
  },

  arrow: {
    fontSize: 24,
    fontWeight: '300',
  },

  divider: {
    height: 1,
    marginLeft: 62,
  },

  modeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingTop: 15,
  },

  modeSelector: {
    flexDirection: 'row',
    gap: 8,
    padding: 14,
  },

  modeButton: {
    flex: 1,
    minHeight: 65,
    borderRadius: 12,
    borderWidth: 1,
    padding: 11,
    justifyContent: 'center',
  },

  modeButtonTitle: {
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  modeButtonSubtitle: {
    fontSize: 7,
    lineHeight: 11,
    marginTop: 4,
  },

  lotSizeRow: {
    minHeight: 70,
    paddingHorizontal: 14,
    paddingVertical: 11,
    flexDirection: 'row',
    alignItems: 'center',
  },

  lotSizeValue: {
    minWidth: 55,
    paddingHorizontal: 9,
    paddingVertical: 7,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },

  lotSizeText: {
    fontSize: 12,
    fontWeight: '900',
  },

  lotSizeControls: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingBottom: 13,
    gap: 9,
  },

  lotButton: {
    width: 32,
    height: 32,
    borderRadius: 9,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },

  lotButtonText: {
    fontSize: 19,
    fontWeight: '700',
  },

  lotSliderTrack: {
    flex: 1,
    height: 5,
    borderRadius: 3,
    overflow: 'hidden',
  },

  lotSliderFill: {
    height: 5,
    borderRadius: 3,
  },

  warningText: {
    fontSize: 7,
    lineHeight: 12,
    paddingHorizontal: 14,
    paddingBottom: 14,
  },

  interfaceBadge: {
    minWidth: 66,
    height: 30,
    borderRadius: 9,
    borderWidth: 1,
    paddingHorizontal: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },

  interfaceBadgeDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },

  interfaceBadgeText: {
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  backendCard: {
    flexDirection: 'row',
    borderRadius: 13,
    borderWidth: 1,
    padding: 13,
    marginBottom: 25,
  },

  backendDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    marginTop: 4,
    marginRight: 9,
  },

  backendContent: {
    flex: 1,
  },

  backendTitle: {
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1,
    marginBottom: 5,
  },

  backendText: {
    fontSize: 8,
    lineHeight: 14,
  },

  footer: {
    alignItems: 'center',
    marginTop: 2,
  },

  footerBrand: {
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 2,
  },

  footerText: {
    fontSize: 7,
    marginTop: 5,
    letterSpacing: 0.7,
  },
});
