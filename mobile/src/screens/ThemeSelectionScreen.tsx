
import React from 'react';
import {
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import {useSafeAreaInsets} from 'react-native-safe-area-context';

import {RootStackParamList} from '../navigation/navigationTypes';
import {useTheme} from '../theme/ThemeContext';

type ThemeSelectionScreenProps = NativeStackScreenProps<
  RootStackParamList,
  'ThemeSelection'
>;

type ThemeOption = {
  mode: 'DARK' | 'LIGHT' | 'SYSTEM';
  title: string;
  subtitle: string;
  description: string;
};

const THEME_OPTIONS: ThemeOption[] = [
  {
    mode: 'DARK',
    title: 'BALLY DARK',
    subtitle: 'Futuristic dark interface',
    description:
      'The default BALLY FLOW experience with a deep trading-focused interface.',
  },
  {
    mode: 'LIGHT',
    title: 'LIGHT',
    subtitle: 'Clean light interface',
    description:
      'A bright interface designed for users who prefer a lighter visual environment.',
  },
  {
    mode: 'SYSTEM',
    title: 'SYSTEM',
    subtitle: 'Follow device appearance',
    description:
      'Automatically follows the light or dark appearance configured on your device.',
  },
];

function ThemePreview({
  mode,
  isSelected,
}: {
  mode: ThemeOption['mode'];
  isSelected: boolean;
}) {
  const isDark = mode !== 'LIGHT';

  const previewBackground = isDark ? '#05070D' : '#F4F6FB';
  const previewSurface = isDark ? '#0A0E18' : '#FFFFFF';
  const previewBorder = isDark ? '#1B2435' : '#D9DEEA';
  const previewText = isDark ? '#FFFFFF' : '#101522';
  const previewMuted = isDark ? '#69758E' : '#737D92';

  return (
    <View
      style={[
        styles.preview,
        {
          backgroundColor: previewBackground,
          borderColor: previewBorder,
        },
        isSelected && styles.previewSelected,
      ]}>
      <View
        style={[
          styles.previewHeader,
          {
            borderBottomColor: previewBorder,
          },
        ]}>
        <View style={styles.previewLogo}>
          <Text style={styles.previewLogoText}>B</Text>
        </View>

        <View style={styles.previewHeaderLines}>
          <View
            style={[
              styles.previewLine,
              styles.previewLineLong,
              {
                backgroundColor: previewText,
              },
            ]}
          />

          <View
            style={[
              styles.previewLine,
              styles.previewLineShort,
              {
                backgroundColor: previewMuted,
              },
            ]}
          />
        </View>

        <View
          style={[
            styles.previewStatus,
            isDark
              ? styles.previewStatusDark
              : styles.previewStatusLight,
          ]}
        />
      </View>

      <View style={styles.previewBody}>
        <View
          style={[
            styles.previewCard,
            {
              backgroundColor: previewSurface,
              borderColor: previewBorder,
            },
          ]}>
          <View
            style={[
              styles.previewMetric,
              isDark
                ? styles.previewMetricDark
                : styles.previewMetricLight,
            ]}
          />

          <View style={styles.previewMetricLines}>
            <View
              style={[
                styles.previewLine,
                styles.previewMetricLineLong,
                {
                  backgroundColor: previewText,
                },
              ]}
            />

            <View
              style={[
                styles.previewLine,
                styles.previewMetricLineShort,
                {
                  backgroundColor: previewMuted,
                },
              ]}
            />
          </View>
        </View>

        <View
          style={[
            styles.previewChart,
            {
              backgroundColor: previewSurface,
              borderColor: previewBorder,
            },
          ]}>
          <View
            style={[
              styles.previewChartLine,
              styles.previewChartLineColor,
            ]}
          />
        </View>
      </View>
    </View>
  );
}

function ThemeOptionCard({
  option,
  selected,
  onPress,
}: {
  option: ThemeOption;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      style={({pressed}) => [
        styles.themeCard,
        selected && styles.themeCardSelected,
        pressed && styles.themeCardPressed,
      ]}>
      <ThemePreview
        mode={option.mode}
        isSelected={selected}
      />

      <View style={styles.themeInfo}>
        <View style={styles.themeTitleRow}>
          <View style={styles.themeTitleContent}>
            <Text
              style={[
                styles.themeTitle,
                selected && styles.themeTitleSelected,
              ]}>
              {option.title}
            </Text>

            <Text style={styles.themeSubtitle}>
              {option.subtitle}
            </Text>
          </View>

          <View
            style={[
              styles.radioOuter,
              selected && styles.radioOuterSelected,
            ]}>
            {selected && (
              <View style={styles.radioInner} />
            )}
          </View>
        </View>

        <Text style={styles.themeDescription}>
          {option.description}
        </Text>
      </View>
    </Pressable>
  );
}

export default function ThemeSelectionScreen({
  route,
  navigation,
}: ThemeSelectionScreenProps) {
  const insets = useSafeAreaInsets();
  const {theme, themeMode, setThemeMode} = useTheme();

  const user = route.params;

  const handleThemeSelection = async (
    mode: ThemeOption['mode'],
  ) => {
    await setThemeMode(mode);
  };

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
        <View style={styles.header}>
          <View style={styles.headerContent}>
            <Text
              style={[
                styles.appLabel,
                {
                  color: theme.colors.primary,
                },
              ]}>
              BALLY FLOW
            </Text>

            <Text
              style={[
                styles.title,
                {
                  color: theme.colors.text,
                },
              ]}>
              THEMES
            </Text>

            <Text
              style={[
                styles.subtitle,
                {
                  color: theme.colors.textMuted,
                },
              ]}>
              Personalize your trading experience
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

        <View
          style={[
            styles.currentThemeCard,
            {
              backgroundColor:
                theme.colors.surfaceSecondary,
              borderColor: theme.colors.border,
            },
          ]}>
          <View
            style={[
              styles.currentThemeIndicator,
              {
                backgroundColor: theme.colors.primary,
              },
            ]}
          />

          <View style={styles.currentThemeContent}>
            <Text
              style={[
                styles.currentThemeLabel,
                {
                  color: theme.colors.textMuted,
                },
              ]}>
              CURRENT THEME
            </Text>

            <Text
              style={[
                styles.currentThemeValue,
                {
                  color: theme.colors.text,
                },
              ]}>
              {themeMode === 'DARK'
                ? 'BALLY DARK'
                : themeMode === 'LIGHT'
                  ? 'LIGHT'
                  : 'SYSTEM'}
            </Text>
          </View>
        </View>

        <Text
          style={[
            styles.sectionTitle,
            {
              color: theme.colors.textMuted,
            },
          ]}>
          SELECT APPEARANCE
        </Text>

        {THEME_OPTIONS.map(option => (
          <ThemeOptionCard
            key={option.mode}
            option={option}
            selected={themeMode === option.mode}
            onPress={() =>
              handleThemeSelection(option.mode)
            }
          />
        ))}

        <View
          style={[
            styles.infoCard,
            {
              backgroundColor: theme.colors.surface,
              borderColor: theme.colors.border,
            },
          ]}>
          <View
            style={[
              styles.infoIcon,
              {
                backgroundColor:
                  theme.colors.inputBackground,
              },
            ]}>
            <Text
              style={[
                styles.infoIconText,
                {
                  color: theme.colors.primary,
                },
              ]}>
              i
            </Text>
          </View>

          <View style={styles.infoContent}>
            <Text
              style={[
                styles.infoTitle,
                {
                  color: theme.colors.text,
                },
              ]}>
              Theme synchronization
            </Text>

            <Text
              style={[
                styles.infoText,
                {
                  color: theme.colors.textMuted,
                },
              ]}>
              Your selection is saved automatically and
              will be restored when you reopen BALLY FLOW.
            </Text>
          </View>
        </View>

        <Text
          style={[
            styles.footer,
            {
              color: theme.colors.textMuted,
            },
          ]}>
          {user?.displayName ||
            user?.firstName ||
            'Trader'}
          {'  •  '}
          BALLY FLOW
        </Text>
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
    width: 280,
    height: 280,
    borderRadius: 140,
    opacity: 0.08,
    top: -170,
    right: -120,
  },

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 24,
  },

  headerContent: {
    flex: 1,
    paddingRight: 16,
  },

  appLabel: {
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

  currentThemeCard: {
    minHeight: 72,
    borderWidth: 1,
    borderRadius: 16,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 28,
  },

  currentThemeIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 11,
  },

  currentThemeContent: {
    flex: 1,
  },

  currentThemeLabel: {
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1.3,
  },

  currentThemeValue: {
    fontSize: 12,
    fontWeight: '900',
    marginTop: 4,
  },

  sectionTitle: {
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1.5,
    marginBottom: 10,
  },

  themeCard: {
    borderWidth: 1,
    borderColor: '#1B2435',
    backgroundColor: '#0A0E18',
    borderRadius: 17,
    padding: 10,
    marginBottom: 13,
  },

  themeCardSelected: {
    borderColor: '#7083FF',
  },

  themeCardPressed: {
    opacity: 0.82,
  },

  preview: {
    height: 126,
    borderWidth: 1,
    borderRadius: 12,
    overflow: 'hidden',
  },

  previewSelected: {
    borderColor: '#7083FF',
  },

  previewHeader: {
    height: 32,
    borderBottomWidth: 1,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 9,
  },

  previewLogo: {
    width: 18,
    height: 18,
    borderRadius: 5,
    backgroundColor: '#7083FF',
    alignItems: 'center',
    justifyContent: 'center',
  },

  previewLogoText: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '900',
  },

  previewHeaderLines: {
    marginLeft: 7,
    gap: 3,
  },

  previewLine: {
    height: 3,
    borderRadius: 2,
  },

  previewLineLong: {
    width: 58,
  },

  previewLineShort: {
    width: 38,
  },

  previewStatus: {
    width: 18,
    height: 8,
    borderRadius: 4,
    marginLeft: 'auto',
  },

  previewStatusDark: {
    backgroundColor: '#11182A',
  },

  previewStatusLight: {
    backgroundColor: '#EEF1F8',
  },

  previewBody: {
    flex: 1,
    padding: 8,
    flexDirection: 'row',
    gap: 7,
  },

  previewCard: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 8,
    padding: 7,
    flexDirection: 'row',
    alignItems: 'center',
  },

  previewMetric: {
    width: 22,
    height: 22,
    borderRadius: 6,
  },

  previewMetricDark: {
    backgroundColor: '#11182A',
  },

  previewMetricLight: {
    backgroundColor: '#F0F3F9',
  },

  previewMetricLines: {
    marginLeft: 5,
    gap: 4,
  },

  previewMetricLineLong: {
    width: 42,
  },

  previewMetricLineShort: {
    width: 28,
  },

  previewChart: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 8,
    justifyContent: 'center',
    paddingHorizontal: 8,
  },

  previewChartLine: {
    height: 24,
    borderTopWidth: 2,
    transform: [{rotate: '-8deg'}],
  },

  previewChartLineColor: {
    borderTopColor: '#7083FF',
  },

  themeInfo: {
    paddingHorizontal: 4,
    paddingTop: 12,
    paddingBottom: 5,
  },

  themeTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  themeTitleContent: {
    flex: 1,
  },

  themeTitle: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  themeTitleSelected: {
    color: '#7083FF',
  },

  themeSubtitle: {
    color: '#69758E',
    fontSize: 8,
    marginTop: 4,
  },

  radioOuter: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#33405A',
    alignItems: 'center',
    justifyContent: 'center',
  },

  radioOuterSelected: {
    borderColor: '#7083FF',
  },

  radioInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#7083FF',
  },

  themeDescription: {
    color: '#59657C',
    fontSize: 8,
    lineHeight: 13,
    marginTop: 9,
    paddingRight: 20,
  },

  infoCard: {
    flexDirection: 'row',
    borderWidth: 1,
    borderRadius: 15,
    padding: 13,
    marginTop: 9,
  },

  infoIcon: {
    width: 30,
    height: 30,
    borderRadius: 9,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },

  infoIconText: {
    fontSize: 12,
    fontWeight: '900',
  },

  infoContent: {
    flex: 1,
  },

  infoTitle: {
    fontSize: 9,
    fontWeight: '900',
    marginBottom: 4,
  },

  infoText: {
    fontSize: 8,
    lineHeight: 13,
  },

  footer: {
    textAlign: 'center',
    fontSize: 7,
    marginTop: 25,
    letterSpacing: 0.5,
  },
});
