import AsyncStorage from '@react-native-async-storage/async-storage';
﻿
import React from 'react';
import {
  Alert,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import {useSafeAreaInsets} from 'react-native-safe-area-context';

import {RootStackParamList} from '../navigation/navigationTypes';
import {BRANDING} from '../config/branding';

type TradingPreferencesScreenProps =
  NativeStackScreenProps<
    RootStackParamList,
    'TradingPreferences'
  >;

type TradingMode = 'Technical' | 'Hybrid';

type Market = {
  symbol: string;
  name: string;
  description: string;
};

const MARKETS: Market[] = [
  {
    symbol: 'XAUUSD',
    name: 'Gold / US Dollar',
    description: 'Gold against the US Dollar',
  },
  {
    symbol: 'EURUSD',
    name: 'Euro / US Dollar',
    description: 'Euro against the US Dollar',
  },
  {
    symbol: 'GBPUSD',
    name: 'Pound / US Dollar',
    description: 'British Pound against the US Dollar',
  },
  {
    symbol: 'USDJPY',
    name: 'US Dollar / Yen',
    description: 'US Dollar against the Japanese Yen',
  },
  {
    symbol: 'XAGUSD',
    name: 'Silver / US Dollar',
    description: 'Silver against the US Dollar',
  },
  {
    symbol: 'NASDAQ',
    name: 'NASDAQ',
    description: 'NASDAQ market instrument',
  },
];

const DEFAULT_LOT_SIZE = '0.01';

export default function TradingPreferencesScreen({
  navigation,
}: TradingPreferencesScreenProps) {
  const insets = useSafeAreaInsets();


  /*
   * ============================================================
   * LOCAL PREFERENCE STATE
   * ============================================================
   *
   * These preferences intentionally remain local at this stage.
   *
   * Future backend integration can synchronize these values
   * with the authenticated user's account.
   */

  const [tradingMode, setTradingMode] =
    React.useState<TradingMode>('Technical');

  const [lotSize, setLotSize] =
    React.useState(DEFAULT_LOT_SIZE);

  const [selectedMarkets, setSelectedMarkets] =
    React.useState<string[]>([
      'XAUUSD',
      'EURUSD',
      'GBPUSD',
      'USDJPY',
      'XAGUSD',
      'NASDAQ',
    ]);

  const [saved, setSaved] =
    React.useState(false);/*
   * ============================================================
   * NAVIGATION
   * ============================================================
   */

  const handleBack = () => {
    navigation.goBack();
  };

  /*
   * ============================================================
   * TRADING MODE
   * ============================================================
   */

  const selectTradingMode = (
    mode: TradingMode,
  ) => {
    setTradingMode(mode);
    setSaved(false);
  };

  /*
   * ============================================================
   * LOT SIZE
   * ============================================================
   */

  const handleLotSizeChange = (
    value: string,
  ) => {
    /*
     * Allow only digits and one decimal point.
     */
    const sanitized = value
      .replace(/[^0-9.]/g, '')
      .replace(/(\..*)\./g, '$1');

    setLotSize(sanitized);
    setSaved(false);
  };

  /*
   * ============================================================
   * MARKET SELECTION
   * ============================================================
   */

  const toggleMarket = (
    symbol: string,
  ) => {
    setSelectedMarkets(current => {
      if (current.includes(symbol)) {
        /*
         * Do not allow the user to remove the
         * final selected market.
         */
        if (current.length === 1) {
          return current;
        }

        return current.filter(
          market => market !== symbol,
        );
      }

      return [...current, symbol];
    });

    setSaved(false);
  };

  /*
   * ============================================================
   * VALIDATION
   * ============================================================
   */

  const validatePreferences = (): boolean => {
    const numericLotSize = Number(lotSize);

    if (!lotSize || Number.isNaN(numericLotSize)) {
      Alert.alert(
        'Invalid Lot Size',
        'Please enter a valid lot size.',
      );

      return false;
    }

    if (numericLotSize <= 0) {
      Alert.alert(
        'Invalid Lot Size',
        'Lot size must be greater than 0.',
      );

      return false;
    }

    if (selectedMarkets.length === 0) {
      Alert.alert(
        'Select a Market',
        'At least one market must be selected.',
      );

      return false;
    }

    return true;
  };

  /*
   * ============================================================
   * SAVE
   * ============================================================
   *
   * Local save only.
   *
   * Backend synchronization is intentionally NOT performed here.
   */

  const savePreferences = () => {
    if (!validatePreferences()) {
      return;
    }

    setSaved(true);

    Alert.alert(
      'Preferences Saved',
      'Your trading preferences have been saved locally.',
      [
        {
          text: 'OK',
        },
      ],
    );
  };

  /*
   * ============================================================
   * RESET
   * ============================================================
   */

  const resetPreferences = () => {
    Alert.alert(
      'Reset Preferences?',
      'This will restore the default trading preferences.',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Reset',
          style: 'destructive',
          onPress: () => {
            setTradingMode('Technical');
            setLotSize(DEFAULT_LOT_SIZE);
            setSelectedMarkets([
              'XAUUSD',
              'EURUSD',
              'GBPUSD',
              'USDJPY',
              'XAGUSD',
              'NASDAQ',
            ]);
            setSaved(false);
          },
        },
      ],
    );
  };

  const selectedCount =
    selectedMarkets.length;

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      <View style={styles.glowTop} />
      <View style={styles.glowBottom} />

      <ScrollView
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={[
          styles.scrollContent,
          {
            paddingTop: Math.max(
              insets.top,
              18,
            ),
            paddingBottom: Math.max(
              insets.bottom + 100,
              40,
            ),
          },
        ]}>

        {/* ================================================== */}
        {/* HEADER */}
        {/* ================================================== */}

        <View style={styles.header}>
          <Pressable
            onPress={handleBack}
            style={({pressed}) => [
              styles.backButton,
              pressed && styles.buttonPressed,
            ]}
            accessibilityRole="button"
            accessibilityLabel="Go back">
            <Text style={styles.backIcon}>
              â€¹
            </Text>
          </Pressable>

          <View style={styles.headerText}>
            <Text style={styles.appName}>
              {BRANDING.appName}
            </Text>

            <Text style={styles.screenTitle}>
              TRADING PREFERENCES
            </Text>

            <Text style={styles.screenSubtitle}>
              Configure your trading behavior
            </Text>
          </View>

          <View style={styles.localBadge}>
            <View style={styles.localDot} />

            <Text style={styles.localText}>
              LOCAL
            </Text>
          </View>
        </View>

        {/* ================================================== */}
        {/* INTRO CARD */}
        {/* ================================================== */}

        <View style={styles.introCard}>
          <View style={styles.introIcon}>
            <Text style={styles.introIconText}>
              T
            </Text>
          </View>

          <View style={styles.introContent}>
            <Text style={styles.introTitle}>
              TRADING CONFIGURATION
            </Text>

            <Text style={styles.introText}>
              Choose how BALLY FLOW should prepare
              trading decisions, define your preferred
              lot size, and select the markets you want
              to monitor.
            </Text>
          </View>
        </View>

        {/* ================================================== */}
        {/* TRADING MODE */}
        {/* ================================================== */}

        <Text style={styles.sectionTitle}>
          TRADING MODE
        </Text>

        <View style={styles.modeCard}>
          <View style={styles.sectionTop}>
            <View>
              <Text style={styles.cardTitle}>
                Decision Engine
              </Text>

              <Text style={styles.cardSubtitle}>
                Select one active trading mode
              </Text>
            </View>

            <View style={styles.modeCountBadge}>
              <Text style={styles.modeCountText}>
                2 MODES
              </Text>
            </View>
          </View>

          <View style={styles.modeSelector}>

            {/* TECHNICAL */}

            <Pressable
              onPress={() =>
                selectTradingMode('Technical')
              }
              style={({pressed}) => [
                styles.modeOption,
                tradingMode === 'Technical' &&
                  styles.modeOptionActive,
                pressed && styles.modeOptionPressed,
              ]}>
              <View
                style={[
                  styles.modeRadio,
                  tradingMode === 'Technical' &&
                    styles.modeRadioActive,
                ]}>
                {tradingMode === 'Technical' ? (
                  <View
                    style={styles.modeRadioInner}
                  />
                ) : null}
              </View>

              <View style={styles.modeOptionContent}>
                <Text
                  style={[
                    styles.modeOptionTitle,
                    tradingMode === 'Technical' &&
                      styles.modeOptionTitleActive,
                  ]}>
                  TECHNICAL MODE
                </Text>

                <Text style={styles.modeOptionText}>
                  SMC and technical market analysis
                </Text>
              </View>

              {tradingMode === 'Technical' ? (
                <Text style={styles.activeLabel}>
                  ACTIVE
                </Text>
              ) : null}
            </Pressable>

            {/* HYBRID */}

            <Pressable
              onPress={() =>
                selectTradingMode('Hybrid')
              }
              style={({pressed}) => [
                styles.modeOption,
                tradingMode === 'Hybrid' &&
                  styles.modeOptionActive,
                pressed && styles.modeOptionPressed,
              ]}>
              <View
                style={[
                  styles.modeRadio,
                  tradingMode === 'Hybrid' &&
                    styles.modeRadioActive,
                ]}>
                {tradingMode === 'Hybrid' ? (
                  <View
                    style={styles.modeRadioInner}
                  />
                ) : null}
              </View>

              <View style={styles.modeOptionContent}>
                <Text
                  style={[
                    styles.modeOptionTitle,
                    tradingMode === 'Hybrid' &&
                      styles.modeOptionTitleActive,
                  ]}>
                  HYBRID MODE
                </Text>

                <Text style={styles.modeOptionText}>
                  Technical analysis with fundamental context
                </Text>
              </View>

              {tradingMode === 'Hybrid' ? (
                <Text style={styles.activeLabel}>
                  ACTIVE
                </Text>
              ) : null}
            </Pressable>
          </View>

          <View style={styles.modeInfo}>
            <Text style={styles.modeInfoLabel}>
              SELECTED MODE
            </Text>

            <Text style={styles.modeInfoValue}>
              {tradingMode.toUpperCase()}
            </Text>
          </View>
        </View>

        {/* ================================================== */}
        {/* LOT SIZE */}
        {/* ================================================== */}

        <Text style={styles.sectionTitle}>
          LOT SIZE
        </Text>

        <View style={styles.lotCard}>
          <View style={styles.lotHeader}>
            <View style={styles.lotIcon}>
              <Text style={styles.lotIconText}>
                L
              </Text>
            </View>

            <View style={styles.lotHeaderContent}>
              <Text style={styles.cardTitle}>
                Preferred Lot Size
              </Text>

              <Text style={styles.cardSubtitle}>
                Your preferred trading volume
              </Text>
            </View>
          </View>

          <View style={styles.lotInputWrapper}>
            <Text style={styles.lotPrefix}>
              LOT
            </Text>

            <TextInput
              value={lotSize}
              onChangeText={handleLotSizeChange}
              keyboardType="decimal-pad"
              placeholder="0.01"
              placeholderTextColor="#3F4960"
              style={styles.lotInput}
              maxLength={10}
              accessibilityLabel="Lot size"
            />
          </View>

          <View style={styles.lotQuickRow}>
            {['0.01', '0.05', '0.10', '0.50'].map(
              value => {
                const active =
                  lotSize === value;

                return (
                  <Pressable
                    key={value}
                    onPress={() => {
                      setLotSize(value);
                      setSaved(false);
                    }}
                    style={({pressed}) => [
                      styles.quickLot,
                      active &&
                        styles.quickLotActive,
                      pressed &&
                        styles.quickLotPressed,
                    ]}>
                    <Text
                      style={[
                        styles.quickLotText,
                        active &&
                          styles.quickLotTextActive,
                      ]}>
                      {value}
                    </Text>
                  </Pressable>
                );
              },
            )}
          </View>

          <View style={styles.lotNotice}>
            <View style={styles.noticeDot} />

            <Text style={styles.noticeText}>
              Final position sizing remains subject to
              backend risk management, broker limits,
              margin and execution validation.
            </Text>
          </View>
        </View>

        {/* ================================================== */}
        {/* MARKETS */}
        {/* ================================================== */}

        <View style={styles.marketSectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              PREFERRED MARKETS
            </Text>

            <Text style={styles.marketSectionSubtitle}>
              Select the markets BALLY FLOW should monitor
            </Text>
          </View>

          <View style={styles.selectedBadge}>
            <Text style={styles.selectedBadgeText}>
              {selectedCount}/6
            </Text>
          </View>
        </View>

        <View style={styles.marketCard}>
          {MARKETS.map(
            (market, index) => {
              const selected =
                selectedMarkets.includes(
                  market.symbol,
                );

              return (
                <React.Fragment
                  key={market.symbol}>
                  <Pressable
                    onPress={() =>
                      toggleMarket(
                        market.symbol,
                      )
                    }
                    style={({pressed}) => [
                      styles.marketRow,
                      pressed &&
                        styles.marketRowPressed,
                    ]}>

                    <View
                      style={[
                        styles.marketCheckbox,
                        selected &&
                          styles.marketCheckboxActive,
                      ]}>
                      {selected ? (
                        <Text
                          style={
                            styles.marketCheck
                          }>
                          âœ“
                        </Text>
                      ) : null}
                    </View>

                    <View
                      style={
                        styles.marketSymbolBox
                      }>
                      <Text
                        style={
                          styles.marketSymbol
                        }>
                        {market.symbol}
                      </Text>
                    </View>

                    <View
                      style={
                        styles.marketContent
                      }>
                      <Text
                        style={
                          styles.marketName
                        }>
                        {market.name}
                      </Text>

                      <Text
                        style={
                          styles.marketDescription
                        }>
                        {market.description}
                      </Text>
                    </View>

                    <View
                      style={[
                        styles.marketStatus,
                        selected &&
                          styles.marketStatusActive,
                      ]}>
                      <Text
                        style={[
                          styles.marketStatusText,
                          selected &&
                            styles.marketStatusTextActive,
                        ]}>
                        {selected
                          ? 'ON'
                          : 'OFF'}
                      </Text>
                    </View>
                  </Pressable>

                  {index <
                  MARKETS.length - 1 ? (
                    <View
                      style={
                        styles.marketDivider
                      }
                    />
                  ) : null}
                </React.Fragment>
              );
            },
          )}
        </View>

        {/* ================================================== */}
        {/* CURRENT SUMMARY */}
        {/* ================================================== */}

        <Text style={styles.sectionTitle}>
          CURRENT CONFIGURATION
        </Text>

        <View style={styles.summaryCard}>
          <View style={styles.summaryHeader}>
            <Text style={styles.summaryTitle}>
              PREFERENCE SUMMARY
            </Text>

            <View
              style={[
                styles.savedBadge,
                !saved &&
                  styles.savedBadgePending,
              ]}>
              <View
                style={[
                  styles.savedDot,
                  !saved &&
                    styles.savedDotPending,
                ]}
              />

              <Text
                style={[
                  styles.savedText,
                  !saved &&
                    styles.savedTextPending,
                ]}>
                {saved
                  ? 'SAVED'
                  : 'UNSAVED CHANGES'}
              </Text>
            </View>
          </View>

          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>
              MODE
            </Text>

            <Text style={styles.summaryValue}>
              {tradingMode.toUpperCase()}
            </Text>
          </View>

          <View style={styles.summaryDivider} />

          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>
              LOT SIZE
            </Text>

            <Text style={styles.summaryValue}>
              {lotSize || '--'}
            </Text>
          </View>

          <View style={styles.summaryDivider} />

          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>
              MARKETS
            </Text>

            <Text style={styles.summaryValue}>
              {selectedCount} SELECTED
            </Text>
          </View>
        </View>

        {/* ================================================== */}
        {/* BACKEND NOTICE */}
        {/* ================================================== */}

        <View style={styles.backendNotice}>
          <View style={styles.backendIcon}>
            <Text style={styles.backendIconText}>
              i
            </Text>
          </View>

          <View style={styles.backendContent}>
            <Text style={styles.backendTitle}>
              BACKEND SYNCHRONIZATION
            </Text>

            <Text style={styles.backendText}>
              These preferences are currently stored
              in the mobile application state. Secure
              backend synchronization will be connected
              during the integration stage.
            </Text>
          </View>
        </View>

        {/* ================================================== */}
        {/* ACTIONS */}
        {/* ================================================== */}

        <Pressable
          onPress={savePreferences}
          style={({pressed}) => [
            styles.saveButton,
            pressed && styles.buttonPressed,
          ]}>
          <Text style={styles.saveButtonText}>
            SAVE TRADING PREFERENCES
          </Text>

          <Text style={styles.saveButtonArrow}>
            â†’
          </Text>
        </Pressable>

        <Pressable
          onPress={resetPreferences}
          style={({pressed}) => [
            styles.resetButton,
            pressed && styles.buttonPressed,
          ]}>
          <Text style={styles.resetButtonText}>
            RESET TO DEFAULTS
          </Text>
        </Pressable>

        {/* ================================================== */}
        {/* FOOTER */}
        {/* ================================================== */}

        <View style={styles.footer}>
          <View style={styles.footerDot} />

          <Text style={styles.footerText}>
            BALLY FLOW LOCAL TRADING PREFERENCES
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

  /* ========================================================
     HEADER
     ======================================================== */

  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 24,
  },

  backButton: {
    width: 40,
    height: 40,
    borderRadius: 13,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
    marginTop: 5,
  },

  backIcon: {
    color: '#7083FF',
    fontSize: 30,
    fontWeight: '300',
    lineHeight: 32,
    marginTop: -2,
  },

  headerText: {
    flex: 1,
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
    fontSize: 23,
    fontWeight: '900',
    letterSpacing: 0.2,
  },

  screenSubtitle: {
    color: '#69758E',
    fontSize: 11,
    marginTop: 6,
  },

  localBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#111A38',
    borderRadius: 20,
    paddingHorizontal: 9,
    paddingVertical: 7,
    marginTop: 8,
    marginLeft: 7,
  },

  localDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#7083FF',
    marginRight: 6,
  },

  localText: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  /* ========================================================
     INTRO
     ======================================================== */

  introCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 19,
    padding: 16,
    flexDirection: 'row',
    marginBottom: 27,
  },

  introIcon: {
    width: 42,
    height: 42,
    borderRadius: 13,
    backgroundColor: '#111A38',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },

  introIconText: {
    color: '#7083FF',
    fontSize: 15,
    fontWeight: '900',
  },

  introContent: {
    flex: 1,
  },

  introTitle: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  introText: {
    color: '#69758E',
    fontSize: 9,
    lineHeight: 15,
    marginTop: 5,
  },

  /* ========================================================
     SECTIONS
     ======================================================== */

  sectionTitle: {
    color: '#A8B2C7',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 1.6,
    marginBottom: 10,
    marginTop: 4,
  },

  cardTitle: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '900',
  },

  cardSubtitle: {
    color: '#647087',
    fontSize: 8,
    marginTop: 4,
  },

  /* ========================================================
     MODE
     ======================================================== */

  modeCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 19,
    padding: 15,
    marginBottom: 25,
  },

  sectionTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 15,
  },

  modeCountBadge: {
    backgroundColor: '#111A38',
    borderWidth: 1,
    borderColor: '#27345C',
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 5,
  },

  modeCountText: {
    color: '#7083FF',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  modeSelector: {
    gap: 9,
  },

  modeOption: {
    minHeight: 72,
    borderRadius: 14,
    backgroundColor: '#080C15',
    borderWidth: 1,
    borderColor: '#182133',
    paddingHorizontal: 12,
    flexDirection: 'row',
    alignItems: 'center',
  },

  modeOptionActive: {
    backgroundColor: '#0F1730',
    borderColor: '#334BFF',
  },

  modeOptionPressed: {
    opacity: 0.8,
  },

  modeRadio: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#39445A',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
  },

  modeRadioActive: {
    borderColor: '#7083FF',
  },

  modeRadioInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#7083FF',
  },

  modeOptionContent: {
    flex: 1,
  },

  modeOptionTitle: {
    color: '#D0D6E4',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  modeOptionTitleActive: {
    color: '#FFFFFF',
  },

  modeOptionText: {
    color: '#647087',
    fontSize: 8,
    marginTop: 4,
  },

  activeLabel: {
    color: '#35E68A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  modeInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 14,
    paddingTop: 13,
    borderTopWidth: 1,
    borderTopColor: '#172032',
  },

  modeInfoLabel: {
    color: '#59657B',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  modeInfoValue: {
    color: '#7083FF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 0.6,
  },

  /* ========================================================
     LOT SIZE
     ======================================================== */

  lotCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 19,
    padding: 15,
    marginBottom: 25,
  },

  lotHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },

  lotIcon: {
    width: 42,
    height: 42,
    borderRadius: 13,
    backgroundColor: '#111A38',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
  },

  lotIconText: {
    color: '#7083FF',
    fontSize: 14,
    fontWeight: '900',
  },

  lotHeaderContent: {
    flex: 1,
  },

  lotInputWrapper: {
    height: 58,
    borderRadius: 13,
    backgroundColor: '#080C15',
    borderWidth: 1,
    borderColor: '#26314A',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
  },

  lotPrefix: {
    color: '#56627A',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1,
    marginRight: 13,
  },

  lotInput: {
    flex: 1,
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: '900',
    paddingVertical: 0,
  },

  lotQuickRow: {
    flexDirection: 'row',
    gap: 7,
    marginTop: 10,
  },

  quickLot: {
    flex: 1,
    height: 37,
    borderRadius: 9,
    backgroundColor: '#0D1322',
    borderWidth: 1,
    borderColor: '#1D2940',
    alignItems: 'center',
    justifyContent: 'center',
  },

  quickLotActive: {
    backgroundColor: '#111A38',
    borderColor: '#334BFF',
  },

  quickLotPressed: {
    opacity: 0.75,
  },

  quickLotText: {
    color: '#69758E',
    fontSize: 8,
    fontWeight: '900',
  },

  quickLotTextActive: {
    color: '#7083FF',
  },

  lotNotice: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginTop: 14,
  },

  noticeDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#7083FF',
    marginTop: 4,
    marginRight: 7,
  },

  noticeText: {
    flex: 1,
    color: '#59657B',
    fontSize: 7,
    lineHeight: 13,
  },

  /* ========================================================
     MARKETS
     ======================================================== */

  marketSectionHeader: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    marginBottom: 10,
  },

  marketSectionSubtitle: {
    color: '#59657B',
    fontSize: 8,
    marginTop: -4,
    marginBottom: 10,
  },

  selectedBadge: {
    backgroundColor: '#111A38',
    borderWidth: 1,
    borderColor: '#27345C',
    borderRadius: 11,
    paddingHorizontal: 9,
    paddingVertical: 6,
    marginBottom: 10,
  },

  selectedBadgeText: {
    color: '#7083FF',
    fontSize: 8,
    fontWeight: '900',
  },

  marketCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 19,
    overflow: 'hidden',
    marginBottom: 25,
  },

  marketRow: {
    minHeight: 76,
    paddingHorizontal: 12,
    flexDirection: 'row',
    alignItems: 'center',
  },

  marketRowPressed: {
    backgroundColor: '#0E1423',
  },

  marketCheckbox: {
    width: 22,
    height: 22,
    borderRadius: 7,
    borderWidth: 1,
    borderColor: '#39445A',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },

  marketCheckboxActive: {
    backgroundColor: '#334BFF',
    borderColor: '#334BFF',
  },

  marketCheck: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '900',
  },

  marketSymbolBox: {
    width: 68,
    alignItems: 'flex-start',
  },

  marketSymbol: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 0.2,
  },

  marketContent: {
    flex: 1,
    paddingRight: 7,
  },

  marketName: {
    color: '#C4CCDA',
    fontSize: 8,
    fontWeight: '800',
  },

  marketDescription: {
    color: '#59657B',
    fontSize: 7,
    marginTop: 3,
  },

  marketStatus: {
    minWidth: 31,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 7,
    backgroundColor: '#171A22',
    paddingVertical: 5,
    paddingHorizontal: 5,
  },

  marketStatusActive: {
    backgroundColor: '#0D211A',
  },

  marketStatusText: {
    color: '#59657B',
    fontSize: 6,
    fontWeight: '900',
  },

  marketStatusTextActive: {
    color: '#35E68A',
  },

  marketDivider: {
    height: 1,
    backgroundColor: '#172032',
    marginLeft: 44,
  },

  /* ========================================================
     SUMMARY
     ======================================================== */

  summaryCard: {
    backgroundColor: '#0B1020',
    borderWidth: 1,
    borderColor: '#1C2949',
    borderRadius: 18,
    padding: 15,
    marginBottom: 25,
  },

  summaryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },

  summaryTitle: {
    color: '#7083FF',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1,
  },

  savedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0D211A',
    borderRadius: 9,
    paddingHorizontal: 7,
    paddingVertical: 5,
  },

  savedBadgePending: {
    backgroundColor: '#211C12',
  },

  savedDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 5,
  },

  savedDotPending: {
    backgroundColor: '#E6B84A',
  },

  savedText: {
    color: '#35E68A',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.6,
  },

  savedTextPending: {
    color: '#E6B84A',
  },

  summaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    minHeight: 31,
  },

  summaryLabel: {
    color: '#59657B',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  summaryValue: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '900',
  },

  summaryDivider: {
    height: 1,
    backgroundColor: '#202B42',
  },

  /* ========================================================
     BACKEND NOTICE
     ======================================================== */

  backendNotice: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 17,
    padding: 14,
    flexDirection: 'row',
    marginBottom: 24,
  },

  backendIcon: {
    width: 31,
    height: 31,
    borderRadius: 10,
    backgroundColor: '#111A38',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },

  backendIconText: {
    color: '#7083FF',
    fontSize: 12,
    fontWeight: '900',
  },

  backendContent: {
    flex: 1,
  },

  backendTitle: {
    color: '#A8B2C7',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  backendText: {
    color: '#59657B',
    fontSize: 7,
    lineHeight: 13,
    marginTop: 5,
  },

  /* ========================================================
     ACTIONS
     ======================================================== */

  saveButton: {
    minHeight: 55,
    borderRadius: 14,
    backgroundColor: '#334BFF',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    paddingHorizontal: 18,
    marginBottom: 10,
  },

  saveButtonText: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 0.9,
  },

  saveButtonArrow: {
    color: '#FFFFFF',
    fontSize: 19,
    fontWeight: '300',
    marginLeft: 10,
  },

  resetButton: {
    minHeight: 49,
    borderRadius: 13,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    alignItems: 'center',
    justifyContent: 'center',
  },

  resetButtonText: {
    color: '#69758E',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  buttonPressed: {
    opacity: 0.78,
    transform: [
      {
        scale: 0.985,
      },
    ],
  },

  /* ========================================================
     FOOTER
     ======================================================== */

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
    backgroundColor: '#7083FF',
    marginRight: 6,
  },

  footerText: {
    color: '#46526A',
    fontSize: 7,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
});





