import { loadUserProfilePhoto } from '../utils/userPhoto';
import BrokerLogo from '../components/broker/BrokerLogo';
import PairLogo from '../components/broker/PairLogo';
﻿import Svg, { Defs, LinearGradient, Stop, Polygon, Polyline, Circle } from 'react-native-svg';
import { getMarketQuotes, MarketQuote } from '../api/marketsApi';
import { getHistorySummary, HistorySummaryResponse } from '../api/historyApi';
import React, { useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  Dimensions,
  Image,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Switch,
  Text,
  View,
  Platform } from 'react-native';
import {BottomTabScreenProps} from '@react-navigation/bottom-tabs';
import {useSafeAreaInsets} from 'react-native-safe-area-context';

import {MainTabParamList} from '../navigation/MainTabNavigator';
import {BRANDING} from '../config/branding';
import {
  getApplicationStatus,
  getHealth,
  updateApplicationMode,
  getBotTelemetry,
  toggleBotAutoTrade,
} from '../api/appApi';
import {AccountResponse} from '../api/accountApi';
import * as accountApiModule from '../api/accountApi';
import {getOpenPositions, PositionsResponse} from '../api/positionsApi';

const getAccount =
  (accountApiModule as any).getAccount ??
  (accountApiModule as any).getAccountData ??
  (accountApiModule as any).fetchAccountData ??
  (accountApiModule as any).getAccountSummary ??
  (accountApiModule as any).getAccounts;

type DashboardScreenProps = BottomTabScreenProps<
  MainTabParamList,
  'Dashboard'
>;

type TradingMode = 'TECHNICAL' | 'HYBRID';

type MarketDirection = 'BULLISH' | 'BEARISH' | 'NEUTRAL';

type Market = {
  symbol: string;
  direction: MarketDirection;
  change: string;
  price: string;
  points: number[];
};

/*
 * ============================================================
 * MARKET DATA
 * ============================================================
 *
 * These points are chart fallback values only.
 *
 * IMPORTANT:
 * They must be replaced by real backend market prices when
 * the BALLY FLOW market-data API is connected.
 */
const MARKETS: Market[] = [
  {
    symbol: 'XAUUSD',
    direction: 'BULLISH',
    change: '+0.42%',
    price: '�',
    points: [38, 41, 39, 46, 44, 51, 49, 57, 54, 63],
  },
  {
    symbol: 'EURUSD',
    direction: 'BEARISH',
    change: '-0.18%',
    price: '�',
    points: [62, 59, 61, 56, 58, 51, 49, 46, 44, 42],
  },
  {
    symbol: 'GBPUSD',
    direction: 'BULLISH',
    change: '+0.21%',
    price: '�',
    points: [35, 38, 37, 43, 41, 48, 46, 52, 55, 59],
  },
  {
    symbol: 'USDJPY',
    direction: 'BEARISH',
    change: '-0.11%',
    price: '�',
    points: [64, 61, 63, 57, 59, 53, 51, 47, 45, 42],
  },
  {
    symbol: 'XAGUSD',
    direction: 'NEUTRAL',
    change: '0.01%',
    price: '�',
    points: [49, 51, 50, 52, 49, 51, 50, 51, 49, 50],
  },
  {
    symbol: 'NASDAQ',
    direction: 'BULLISH',
    change: '+0.35%',
    price: '�',
    points: [34, 38, 42, 40, 47, 45, 51, 55, 58, 64],
  },
];

/*
 * ============================================================
 * TRADINGVIEW-STYLE LINE CHART
 * ============================================================
 */

function MarketLineChart({
  points,
  direction,
}: {
  points: number[];
  direction: 'BULLISH' | 'BEARISH';
}) {
  if (!points || !points.length) {
    return (
      <View style={{ width: 80, height: 30, justifyContent: 'center', alignItems: 'center' }}>
        <Text style={{ fontSize: 10, color: '#64748B' }}>--</Text>
      </View>
    );
  }

  const isBull = direction === 'BULLISH';
  const strokeCol = isBull ? '#10B981' : '#EF4444';
  const fillCol = isBull ? 'rgba(16, 185, 129, 0.20)' : 'rgba(239, 68, 68, 0.20)';

  const chartW = 76;
  const chartH = 26;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;

  const step = chartW / (points.length - 1);
  const coords = points.map((p, i) => {
    const x = Math.round(i * step);
    const y = Math.round(chartH - 4 - ((p - min) / range) * (chartH - 8));
    return `${x},${y}`;
  });

  const polylineCoords = coords.join(' ');
  const lastX = chartW;
  const lastY = Math.round(chartH - 4 - ((points[points.length - 1] - min) / range) * (chartH - 8));
  const polygonCoords = `0,${chartH} ${polylineCoords} ${lastX},${chartH}`;

  return (
    <View style={{ width: 80, height: 30, justifyContent: 'center', alignItems: 'center' }}>
      <Svg width={chartW} height={chartH} viewBox={`0 0 ${chartW} ${chartH}`}>
        <Polygon points={polygonCoords} fill={fillCol} />
        <Polyline points={polylineCoords} fill="none" stroke={strokeCol} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        <Circle cx={lastX} cy={lastY} r={3} fill={strokeCol} />
      </Svg>
    </View>
  );
}

export default function DashboardScreen({
  navigation,
  route,
}: DashboardScreenProps) {
  const insets = useSafeAreaInsets();

  const user = route.params;

  const [botEnabled, setBotEnabled] =
    React.useState(false);

  const [tradingMode, setTradingMode] =
    React.useState<TradingMode>('TECHNICAL');

  const [profilePhoto, setProfilePhoto] = React.useState<string | null>(null);

  React.useEffect(() => {
    let active = true;
    const loadPhoto = () => {
      loadUserProfilePhoto(user)
        .then(val => {
          if (active) {
            setProfilePhoto(val);
          }
        })
        .catch(() => {});
    };
    loadPhoto();
    const interval = setInterval(loadPhoto, 4000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  /*
   * ============================================================
   * LIVE BROKER ACCOUNT DATA
   * ============================================================
   *
   * These values come directly from the BALLY FLOW backend.
   */
  const [accountData, setAccountData] =
    React.useState<AccountResponse | null>(null);
  const [historySummary, setHistorySummary] = React.useState<HistorySummaryResponse | null>(null);
  const [liveMarkets, setLiveMarkets] = React.useState<MarketQuote[]>([]);

  const [positionsData, setPositionsData] =
    React.useState<PositionsResponse | null>(null);


  /*
   * ============================================================
   * BACKEND CONNECTION STATE
   * ============================================================
   *
   * isApiLive:
   *   True when the BALLY FLOW FastAPI backend responds
   *   successfully to /health.
   *
   * applicationRunning:
   *   Reflects the actual backend application state.
   *
   * These are intentionally separate from MT5/broker state.
   */
  const [isApiLive, setIsApiLive] =
    React.useState(false);

  const [applicationRunning, setApplicationRunning] =
    React.useState(false);

  const [backendLoading, setBackendLoading] =
    React.useState(true);

  const [modeUpdating, setModeUpdating] =
    React.useState(false);

  const [debugError, setDebugError] = React.useState<string | null>(null);

  const toggleBotAutoTradeBackend = async (enabled: boolean): Promise<void> => {
    try {
      const response = await toggleBotAutoTrade(enabled);
      if (mountedRef.current) {
        setBotEnabled(Boolean(response?.auto_trading_enabled));
      }
    } catch (error) {
      if (mountedRef.current) {
        setDebugError(error instanceof Error ? error.message : String(error));
      }
    }
  };
  /*
   * Prevent state updates after the screen has unmounted.
   */
  const mountedRef = React.useRef(true);

  /*
   * ============================================================
   * BACKEND STATUS REFRESH
   * ============================================================
   */

  const refreshBackendStatus = React.useCallback(
    async () => {
      try {
        /*
         * Health check.
         *
         * This determines whether the FastAPI service itself
         * is reachable.
         */
        const health = await getHealth();

        if (!mountedRef.current) {
          return;
        }

        const healthOnline =
          health?.status === 'ONLINE';

        setIsApiLive(healthOnline);
        /*
         * Retrieve live broker account and open-position data.
         *
         * These endpoints are independent of application RUNNING/STOPPED
         * state, so account data can remain visible whenever the backend
         * and MT5 connection are available.
         */
        if (healthOnline) {
          try {
            const account = await getAccount();
            try {
              const summary = await getHistorySummary(7);
              try {
                const quotesRes = await getMarketQuotes();
                if (mountedRef.current && quotesRes?.quotes) {
                  setLiveMarkets(quotesRes.quotes);
                }
              } catch {
                // ignore quotes error
              }
              if (mountedRef.current) {
                setHistorySummary(summary);
              }
            } catch {
              // ignore history summary error on refresh
            }

            if (mountedRef.current) {
              setAccountData(account);
            }
          } catch {
            if (mountedRef.current) {
              setAccountData(null);
            }
          }

          try {
            const positions = await getOpenPositions();

            if (mountedRef.current) {
              setPositionsData(positions);
            }
          } catch {
            if (mountedRef.current) {
              setPositionsData(null);
            }
          }
        } else {
          setAccountData(null);
          setPositionsData(null);
        }

        /*
         * If the API is reachable, retrieve the actual
         * BALLY FLOW application status.
         */
        if (healthOnline) {
          try {
            const status =
              await getApplicationStatus();

            if (!mountedRef.current) {
              return;
            }

            /*
             * The backend status uses RUNNING / STOPPED.
             */
            setApplicationRunning(
              status?.status === 'RUNNING',
            );

            /*
             * Keep the dashboard mode synchronized
             * with the backend.
             */
            const backendMode =
              status?.mode;

            if (backendMode === 'technical') {
              setTradingMode('TECHNICAL');
            } else if (
              backendMode === 'hybrid'
            ) {
              setTradingMode('HYBRID');
            }
          } catch {
            /*
             * API health is still valid, but the application
             * status endpoint failed.
             *
             * Do not mark the whole API offline.
             */
            if (mountedRef.current) {
              setApplicationRunning(false);
            }
          }
        } else {
          /*
           * Backend is unreachable.
           */
          setApplicationRunning(false);
        }
            } catch (err) {
        if (!mountedRef.current) {
          return;
        }

        setIsApiLive(false);
        setApplicationRunning(false);
        setDebugError(
          err instanceof Error ? err.message : String(err),
        );
      } finally {
        if (mountedRef.current) {
          setBackendLoading(false);
        }
      }
    },
    [],
  );

  /*
   * ============================================================
   * INITIAL BACKEND CONNECTION
   * ============================================================
   */

  React.useEffect(() => {
    mountedRef.current = true;

    refreshBackendStatus();

    /*
     * Keep dashboard status reasonably fresh.
     */
    const interval = setInterval(() => {
      refreshBackendStatus();
    }, 15000);

    return () => {
      mountedRef.current = false;
      clearInterval(interval);
    };
  }, [refreshBackendStatus]);

  /*
   * ============================================================
   * RESYNC WHEN DASHBOARD BECOMES ACTIVE
   * ============================================================
   *
   * This makes the dashboard update when the user comes back
   * from another screen.
   */
  React.useEffect(() => {
    const unsubscribe =
      navigation.addListener('focus', () => {
        refreshBackendStatus();
      });

    return unsubscribe;
  }, [navigation, refreshBackendStatus]);

  /*
   * ============================================================
   * TRADING MODE
   * ============================================================
   */

  const openTechnicalMode = async () => {
    if (modeUpdating) {
      return;
    }

    /*
     * Optimistic UI update.
     */
    setTradingMode('TECHNICAL');

    try {
      setModeUpdating(true);

      const response =
        await updateApplicationMode(
          'technical',
        );

      /*
       * Backend accepted the mode change.
       */
      if (
        response?.mode === 'technical' ||
        response?.status === 'UPDATED'
      ) {
        if (mountedRef.current) {
          setTradingMode('TECHNICAL');
        }
      } else {
        /*
         * Re-read the backend state if the response shape
         * does not confirm the requested mode.
         */
        await refreshBackendStatus();
      }
    } catch {
      /*
       * Restore actual backend state after a failed update.
       */
      await refreshBackendStatus();
    } finally {
      if (mountedRef.current) {
        setModeUpdating(false);
      }
    }

    navigation.navigate('Flow', user);
  };

  const openHybridMode = async () => {
    if (modeUpdating) {
      return;
    }

    /*
     * Optimistic UI update.
     */
    setTradingMode('HYBRID');

    try {
      setModeUpdating(true);

      const response =
        await updateApplicationMode(
          'hybrid',
        );

      /*
       * Backend accepted the mode change.
       */
      if (
        response?.mode === 'hybrid' ||
        response?.status === 'UPDATED'
      ) {
        if (mountedRef.current) {
          setTradingMode('HYBRID');
        }
      } else {
        /*
         * Re-read actual backend state.
         */
        await refreshBackendStatus();
      }
    } catch {
      /*
       * Restore actual backend state after a failed update.
       */
      await refreshBackendStatus();
    } finally {
      if (mountedRef.current) {
        setModeUpdating(false);
      }
    }

    navigation.navigate('Flow', user);
  };

  /*
   * ============================================================
   * QUICK ACCESS / NAVIGATION
   * ============================================================
   */

  const openTrades = () => {
    navigation.navigate('Trades', user);
  };

  const openHistory = () => {
    (navigation as any).navigate('History', user);
  };

  const openMarkets = () => {
    navigation.navigate('Markets', user);
  };

  const openLiveSignals = () => {
    navigation.navigate('Flow', user);
  };

  /*
   * ============================================================
   * DERIVED BACKEND STATUS
   * ============================================================
   *
   * The dashboard's CONNECTION status represents the
   * BALLY FLOW API, not the broker account.
   */
  const connectionLabel = backendLoading
    ? 'CONNECTING'
    : isApiLive
    ? 'LIVE'
    : 'OFFLINE';

  const connectionDescription = backendLoading
    ? 'Checking BALLY FLOW backend'
    : isApiLive
    ? 'BALLY FLOW API connected'
    : 'BALLY FLOW API unavailable';

  /*
   * The application state is separate from API connectivity.
   */
  const systemStatusText =
    !isApiLive
      ? 'BALLY FLOW SYSTEM OFFLINE'
      : applicationRunning
      ? 'BALLY FLOW SYSTEM RUNNING'
      : 'BALLY FLOW SYSTEM READY';

  return (
    <View style={styles.root}>
      <StatusBar
        barStyle="light-content"
      />

      <View style={styles.glowTop} />
      <View style={styles.glowBottom} />

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[
          styles.scrollContent,
          {
            paddingTop: Math.max(insets.top, 20),
            paddingBottom: Math.max(
              insets.bottom + 90,
              36,
            ),
          },
        ]}>

        {/* ================================================== */}
        {/* HEADER */}
        {/* ================================================== */}

        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <Text style={styles.appName}>
              {BRANDING.appName}
            </Text>

            <Text style={styles.greeting}>
              Hello, {user.firstName} 👋
            </Text>

            <Text style={styles.headerSubtitle}>
              Make your trade smarter
            </Text>
          </View>

          <Pressable
            onPress={() => (navigation as any).navigate('Profile')}
            style={styles.profileButton}
            accessibilityRole="button"
            accessibilityLabel="Open profile">
            {profilePhoto ? (
              <Image source={{ uri: profilePhoto }} style={styles.profileAvatarImage} />
            ) : (
              <Text style={styles.profileLetter}>
                {user.firstName
                  ? user.firstName.charAt(0).toUpperCase()
                  : 'J'}
              </Text>
            )}
          </Pressable>
        </View>

        {/* ================================================== */}
        {/* PORTFOLIO TOP */}
        {/* ================================================== */}

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            PORTFOLIO
          </Text>

          <Text
            style={[
              styles.sectionMeta,
              !isApiLive && styles.offlineMeta,
            ]}>
            {isApiLive
              ? 'CONNECTED'
              : 'OFFLINE'}
          </Text>
        </View>

        <View style={styles.portfolioCard}>
          <View style={styles.balanceBlock}>
            <Text style={styles.portfolioLabel}>
              BALANCE
            </Text>

            <Text allowFontScaling={false} style={[styles.balanceValue, styles.metricGreen]}>
              {accountData
                ? `${accountData.currency} ${accountData.balance.toFixed(2)}`
                : '0.00'}
            </Text>

            <Text style={styles.accountStatus}>
              {isApiLive
                ? 'MT5 broker account LIVE'
                : 'Backend data unavailable'}
            </Text>
          </View>

          <View style={styles.portfolioDivider} />

          <View style={styles.portfolioGrid}>
            <View style={styles.portfolioMetric}>
              <Text style={styles.portfolioLabel}>P&L</Text>
              <Text allowFontScaling={false} style={[styles.portfolioValue, { color: (accountData?.profit ?? 0) < 0 ? '#EF4444' : '#10B981', fontWeight: '700' }]}>
                {accountData
                  ? `${accountData.currency} ${accountData.profit >= 0 ? '+' : ''}${accountData.profit.toFixed(2)}`
                  : '0.00'}
              </Text>
            </View>
            <View style={styles.portfolioMetric}>
              <Text style={styles.portfolioLabel}>EQUITY</Text>
              <Text allowFontScaling={false} style={[styles.portfolioValue, { color: '#10B981', fontWeight: '700' }]}>
                {accountData
                  ? `${accountData.currency} ${accountData.equity.toFixed(2)}`
                  : '0.00'}
              </Text>
            </View>
            <View style={styles.portfolioMetric}>
              <Text style={styles.portfolioLabel}>MARGIN</Text>
              <Text allowFontScaling={false} style={[styles.portfolioValue, { color: '#10B981', fontWeight: '700' }]}>
                {accountData
                  ? `${accountData.currency} ${accountData.margin.toFixed(2)}`
                  : '0.00'}
              </Text>
            </View>
            <View style={styles.portfolioMetric}>
              <Text style={styles.portfolioLabel}>OPEN TRADES</Text>
              <Text allowFontScaling={false} style={[styles.portfolioValue, { color: '#10B981', fontWeight: '700' }]}>
                {positionsData?.positions ? positionsData.positions.length : (accountData?.open_trades ?? 0)}
              </Text>
            </View>
          </View>
        </View>

        {/* ================================================== */}
        {/* CONNECTION / BOT */}
        {/* ================================================== */}

        <View style={styles.statusCard}>
          <View style={styles.statusItem}>
            <View
              style={[
                styles.liveDot,
                !isApiLive && styles.offlineDot,
              ]}
            />

            <View>
              <Text style={styles.statusLabel}>
                CONNECTION
              </Text>

              <Text
                style={[
                  styles.liveText,
                  !isApiLive && styles.offlineText,
                ]}>
                {connectionLabel}
              </Text>
            </View>
          </View>

          <View style={styles.statusDivider} />

          <View style={styles.statusItem}>
            <View
              style={[
                styles.botDot,
                botEnabled && styles.botDotActive,
              ]}
            />

            <View>
              <Text style={styles.statusLabel}>
                BOT STATUS
              </Text>

              <Text
                style={[
                  styles.botStatusText,
                  botEnabled &&
                    styles.botStatusActive,
                ]}>
                {botEnabled ? 'ON' : 'OFF'}
              </Text>
            </View>
          </View>

          <Switch
            value={botEnabled}
            onValueChange={async (newValue) => {
              await toggleBotAutoTradeBackend(newValue);
              try {
                await toggleBotAutoTrade(newValue);
              } catch (err) {
                console.log('Failed to toggle bot state on backend:', err);
              }
            }}
            trackColor={{
              false: '#252B38',
              true: '#334BFF',
            }}
            thumbColor="#FFFFFF"
            accessibilityLabel="Trading bot status"
          />
        </View>

        {/* ================================================== */}
        {/* TRADING MODE */}
        {/* ================================================== */}

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            TRADING MODE
          </Text>

          <Text style={styles.sectionMeta}>
            {modeUpdating
              ? 'UPDATING'
              : isApiLive
              ? 'SYNCED'
              : 'LOCAL'}
          </Text>
        </View>

        <View style={styles.modeCard}>
          <View style={styles.modeHeader}>
            <View>
              <Text style={styles.modeTitle}>
                {tradingMode}
              </Text>

              <Text style={styles.modeDescription}>
                {tradingMode === 'TECHNICAL'
                  ? 'SMC technical market analysis'
                  : 'Technical + fundamental analysis'}
              </Text>
            </View>

            <View style={styles.activePill}>
              <View style={styles.activePillDot} />

              <Text style={styles.activePillText}>
                {modeUpdating
                  ? 'SYNCING'
                  : 'ACTIVE'}
              </Text>
            </View>
          </View>

          <View style={styles.modeButtons}>
            <Pressable
              disabled={modeUpdating}
              onPress={openTechnicalMode}
              style={({pressed}) => [
                styles.modeButton,
                tradingMode === 'TECHNICAL' &&
                  styles.modeButtonActive,
                modeUpdating &&
                  styles.modeButtonDisabled,
                pressed &&
                  styles.quickCardPressed,
              ]}>
              <Text
                style={[
                  styles.modeButtonText,
                  tradingMode === 'TECHNICAL' &&
                    styles.modeButtonTextActive,
                ]}>
                TECHNICAL
              </Text>
            </Pressable>

            <Pressable
              disabled={modeUpdating}
              onPress={openHybridMode}
              style={({pressed}) => [
                styles.modeButton,
                tradingMode === 'HYBRID' &&
                  styles.modeButtonActive,
                modeUpdating &&
                  styles.modeButtonDisabled,
                pressed &&
                  styles.quickCardPressed,
              ]}>
              <Text
                style={[
                  styles.modeButtonText,
                  tradingMode === 'HYBRID' &&
                    styles.modeButtonTextActive,
                ]}>
                HYBRID
              </Text>
            </Pressable>
          </View>
        </View>

        {/* ================================================== */}
        {/* QUICK ACCESS */}
        {/* ================================================== */}

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            QUICK ACCESS
          </Text>
        </View>

        <View style={styles.quickGrid}>
          <Pressable
            onPress={openTechnicalMode}
            style={({pressed}) => [
              styles.quickCard,
              pressed && styles.quickCardPressed,
            ]}>
            <View style={styles.quickIcon}>
              <Text style={styles.quickIconText}>
                T
              </Text>
            </View>

            <Text style={styles.quickTitle}>
              Technical Mode
            </Text>

            <Text style={styles.quickSubtitle}>
              SMC analysis
            </Text>
          </Pressable>

          <Pressable
            onPress={openHybridMode}
            style={({pressed}) => [
              styles.quickCard,
              pressed && styles.quickCardPressed,
            ]}>
            <View style={styles.quickIcon}>
              <Text style={styles.quickIconText}>
                H
              </Text>
            </View>

            <Text style={styles.quickTitle}>
              Hybrid Mode
            </Text>

            <Text style={styles.quickSubtitle}>
              Combined analysis
            </Text>
          </Pressable>

          <Pressable
            onPress={openTrades}
            style={({pressed}) => [
              styles.quickCard,
              pressed && styles.quickCardPressed,
            ]}>
            <View style={styles.quickIcon}>
              <Text style={styles.quickIconText}>
                O
              </Text>
            </View>

            <Text style={styles.quickTitle}>
              Open Trades
            </Text>

            <Text style={styles.quickSubtitle}>
              Active positions
            </Text>
          </Pressable>

          <Pressable
            onPress={openHistory}
            style={({pressed}) => [
              styles.quickCard,
              pressed && styles.quickCardPressed,
            ]}>
            <View style={styles.quickIcon}>
              <Text style={styles.quickIconText}>
                H
              </Text>
            </View>

            <Text style={styles.quickTitle}>
              History
            </Text>

            <Text style={styles.quickSubtitle}>
              Trade history
            </Text>
          </Pressable>
        </View>

        {/* ================================================== */}
        {/* LIVE SIGNALS */}
        {/* ================================================== */}

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            LIVE SIGNALS
          </Text>

          <Pressable onPress={openLiveSignals}>
            <Text style={styles.viewAll}>
              VIEW ALL 
            </Text>
          </Pressable>
        </View>

        <Pressable
          onPress={openLiveSignals}
          style={({pressed}) => [
            styles.signalCard,
            pressed && styles.quickCardPressed,
          ]}>
          <View style={styles.signalTop}>
            <View
              style={[
                styles.liveSignalBadge,
                !isApiLive &&
                  styles.offlineSignalBadge,
              ]}>
              <View
                style={[
                  styles.liveDotSmall,
                  !isApiLive &&
                    styles.offlineDotSmall,
                ]}
              />

              <Text
                style={[
                  styles.liveSignalText,
                  !isApiLive &&
                    styles.offlineSignalText,
                ]}>
                {isApiLive ? ' LIVE' : 'OFFLINE'}
              </Text>
            </View>

            <Text style={styles.signalMode}>
              {tradingMode}
            </Text>
          </View>

          <View style={styles.signalMain}>
            <View style={{flex: 1}}>
              <Text style={styles.signalSymbol}>
                MARKET SIGNAL FEED
              </Text>

              <Text style={styles.signalStatus}>
                {!isApiLive
                  ? 'Waiting for BALLY FLOW backend'
                  : applicationRunning
                  ? 'Backend application is running'
                  : 'Backend connected  scanner not running'}
              </Text>
            </View>

            <Text style={styles.signalArrow}>
              
            </Text>
          </View>

          <View style={styles.signalFooter}>
            <Text style={styles.signalFooterText}>
              {!isApiLive
                ? 'Live signals will appear here when the BALLY FLOW backend and market-data feed are connected.'
                : applicationRunning
                ? 'BALLY FLOW backend is running. Live market signals will populate this section when the market-data API is connected.'
                : 'BALLY FLOW backend is reachable, but the application is currently stopped.'}
            </Text>
          </View>
        </Pressable>

        {/* ================================================== */}
        {/* BROKER IDENTITY */}
        {/* ================================================== */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>BROKER IDENTITY</Text>
          <View style={styles.badgeLive}>
            <View style={[styles.noticeDot, isApiLive && accountData?.connected ? styles.noticeDotLive : styles.noticeDotOffline]} />
            <Text style={styles.badgeLiveText}>{accountData?.connected ? (accountData?.broker?.trade_mode || 'LIVE') : 'OFFLINE'}</Text>
          </View>
        </View>

        <View style={styles.brokerCard}>
          <View style={styles.brokerHeader}>
            <BrokerLogo
              company={accountData?.broker?.company}
              server={accountData?.broker?.server}
              size={46}
              style={{ marginRight: 12 }}
            />
            <View style={styles.brokerMainInfo}>
              <Text style={styles.brokerName} numberOfLines={1}>
                {accountData?.broker?.company || 'MetaQuotes / MT5 Terminal'}
              </Text>
              <Text style={styles.brokerServer} numberOfLines={1}>
                Server: {accountData?.broker?.server || 'Standard Gateway'}
              </Text>
            </View>
          </View>

          <View style={styles.brokerMetricsRow}>
            <View style={styles.brokerMetric}>
              <Text style={styles.brokerMetricLabel}>LOGIN ID</Text>
              <Text style={styles.brokerMetricValue}>
                {accountData?.broker?.login ? accountData.broker.login.toString() : '�'}
              </Text>
            </View>
            <View style={styles.brokerMetricDivider} />
            <View style={styles.brokerMetric}>
              <Text style={styles.brokerMetricLabel}>LEVERAGE</Text>
              <Text style={styles.brokerMetricValue}>
                {accountData?.broker?.leverage ? `1:${accountData.broker.leverage}` : '1:100'}
              </Text>
            </View>
            <View style={styles.brokerMetricDivider} />
            <View style={styles.brokerMetric}>
              <Text style={styles.brokerMetricLabel}>CURRENCY</Text>
              <Text style={styles.brokerMetricValue}>{accountData?.currency || 'USD'}</Text>
            </View>
          </View>
        </View>

        {/* ================================================== */}
        {/* WIN RATE & PERFORMANCE CYCLE */}
        {/* ================================================== */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>CYCLE PERFORMANCE (7D)</Text>
          <Text style={styles.sectionSubtitle}>LIVE MT5 DEALS</Text>
        </View>

        <View style={styles.winRateCard}>
          <View style={styles.winRateLeft}>
            <View style={styles.winRateGauge}>
              <Text style={styles.winRatePercent}>
                {historySummary ? `${historySummary.win_rate.toFixed(1)}%` : '0.0%'}
              </Text>
              <Text style={styles.winRateGaugeLabel}>WIN RATE</Text>
            </View>
          </View>

          <View style={styles.winRateStats}>
            <View style={styles.statRow}>
              <Text style={styles.statLabel}>Total Closed Trades</Text>
              <Text style={styles.statValueBold}>{historySummary?.total_trades ?? 0}</Text>
            </View>
            <View style={styles.statRow}>
              <Text style={styles.statLabel}>Wins / Losses</Text>
              <Text style={styles.statValueBold}>
                <Text style={styles.bullishText}>{historySummary?.wins ?? 0}W</Text>
                {' / '}
                <Text style={styles.bearishText}>{historySummary?.losses ?? 0}L</Text>
              </Text>
            </View>
            <View style={styles.statRow}>
              <Text style={styles.statLabel}>Profit Factor</Text>
              <Text style={styles.statValueBold}>
                {historySummary ? historySummary.profit_factor.toFixed(2) : '0.00'}
              </Text>
            </View>
            <View style={styles.statRow}>
              <Text style={styles.statLabel}>Net Closed P&L</Text>
              <Text
                style={[
                  styles.statValueBold,
                  (historySummary?.net_profit ?? 0) >= 0 ? styles.bullishText : styles.bearishText,
                ]}>
                {historySummary ? `${historySummary.net_profit >= 0 ? '+' : ''}${historySummary.net_profit.toFixed(2)} ${accountData?.currency || 'USD'}` : '0.00 USD'}
              </Text>
            </View>
          </View>
        </View>

        {/* ================================================== */}
        {/* 6-PAIR LIVE MARKET TABLE */}
        {/* ================================================== */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>LIVE MARKETS (6 PAIRS)</Text>
          <Pressable onPress={openMarkets}>
            <Text style={styles.viewAll}>SCANNER </Text>
          </Pressable>
        </View>

        <View style={styles.marketTable}>
          <View style={styles.marketTableHeader}>
            <Text style={[styles.marketTh, { flex: 1.5 }]}>PAIR</Text>
            <Text style={[styles.marketTh, { flex: 1.5, textAlign: 'right' }]}>PRICE</Text>
            <Text style={[styles.marketTh, { flex: 1.5, textAlign: 'center' }]}>TREND</Text>
            <Text style={[styles.marketTh, { flex: 1.2, textAlign: 'right' }]}>24H</Text>
          </View>

          {((liveMarkets && liveMarkets.length > 0) ? liveMarkets : MARKETS).map((market: any, idx: number) => (
            <Pressable
              key={market.symbol}
              onPress={openMarkets}
              style={({ pressed }) => [
                styles.marketTableRow,
                idx % 2 === 1 && styles.marketTableRowAlt,
                pressed && styles.quickCardPressed,
              ]}>
              <View style={{ flexDirection: 'row', alignItems: 'center', width: 110 }}>
                <PairLogo symbol={market.symbol} size={28} style={{ marginRight: 6 }} />
                <View>
                  <Text allowFontScaling={false} style={styles.tableSymbol}>{market.symbol}</Text>
                  <Text allowFontScaling={false} style={styles.tablePairType}>
                    {market.symbol.includes('XAU') || market.symbol.includes('XAG') ? 'COMMODITY' : (market.symbol.includes('NAS') || market.symbol.includes('TEC') || market.symbol.includes('100')) ? 'INDEX' : 'FOREX'}
                  </Text>
                </View>
              </View>
              <View style={{ width: 90, paddingRight: 6, alignItems: 'flex-start', justifyContent: 'center' }}>
                <Text allowFontScaling={false} style={[styles.tablePrice, { fontVariant: ['tabular-nums'] }]}>
                  {market.price && market.price !== '�' && market.price !== '--' ? market.price : 'LIVE'}
                </Text>
              </View>
              <View style={{ width: 80, alignItems: 'center', justifyContent: 'center' }}>
                <MarketLineChart points={market.points} direction={market.direction} />
              </View>
              <View style={{ flex: 1, alignItems: 'flex-end', justifyContent: 'center' }}>
                <View
                  style={[
                    styles.changeBadge,
                    market.direction === 'BULLISH' ? styles.changeBadgeBullish : styles.changeBadgeBearish,
                  ]}>
                  <Text
                    allowFontScaling={false}
                    style={[
                      styles.changeBadgeText,
                      market.direction === 'BULLISH' ? styles.bullishText : styles.bearishText,
                      { fontVariant: ['tabular-nums'] },
                    ]}>
                    {market.change_percent || market.change || '+0.00%'}
                  </Text>
                </View>
              </View>
            </Pressable>
          ))}
        </View>

        {/* ================================================== */}
        {/* FOOTER */}{/* ================================================== */}
        {/* FOOTER */}
        {/* ================================================== */}

        <View style={styles.footerStatus}>
          <View
            style={[
              styles.liveDotSmall,
              !isApiLive &&
                styles.offlineDotSmall,
            ]}
          />

          <Text style={styles.footerStatusText}>
            {systemStatusText}
          </Text>
        </View>

                <Text style={styles.backendStatusText}>
          {connectionDescription}
        </Text>

        {debugError && (
          <Text
            style={{
              color: '#FF7185',
              fontSize: 10,
              textAlign: 'center',
              marginTop: 8,
              paddingHorizontal: 20,
            }}>
            DEBUG: {debugError}
          </Text>
        )}
      </ScrollView>
    </View>
  );
}

/*
 * ============================================================
 * STYLES
 * ============================================================
 */

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
    width: 300,
    height: 300,
    borderRadius: 150,
    backgroundColor: '#101B5C',
    opacity: 0.16,
    top: -180,
    right: -100,
  },

  glowBottom: {
    position: 'absolute',
    width: 280,
    height: 280,
    borderRadius: 140,
    backgroundColor: '#17204A',
    opacity: 0.12,
    bottom: -140,
    left: -130,
  },

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },

  headerLeft: {
    flex: 1,
  },

  appName: {
    color: '#7083FF',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 2.2,
    marginBottom: 7,
  },

  greeting: {
    color: '#FFFFFF',
    fontSize: 27,
    fontWeight: '800',
  },

  headerSubtitle: {
    color: '#69758E',
    fontSize: 12,
    marginTop: 5,
  },

  profileButton: {
    overflow: "hidden",
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: '#11182A',
    borderWidth: 1,
    borderColor: '#27314A',
    alignItems: 'center',
    justifyContent: 'center',
  },

  profileLetter: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '800',
  },

  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 11,
    marginTop: 5,
  },

  sectionTitle: {
    color: '#A8B2C7',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 1.6,
  },

  sectionMeta: {
    color: '#35E68A',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1,
  },

  offlineMeta: {
    color: '#FF7185',
  },

  viewAll: {
    color: '#7083FF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  /* ==========================================================
     PORTFOLIO
     ========================================================== */

  portfolioCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 18,
    padding: 16,
    marginBottom: 16,
  },

  balanceBlock: {
    paddingBottom: 14,
  },

  portfolioLabel: {
    color: '#59657C',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.1,
  },

  balanceValue: {
    fontFamily: Platform.OS === 'android' ? 'Roboto' : 'System',
    fontVariant: ['tabular-nums'],
    color: '#FFFFFF',
    fontSize: 29,
    fontWeight: '900',
    marginTop: 6,
  },

  accountStatus: {
    color: '#59657C',
    fontSize: 9,
    marginTop: 4,
  },

  portfolioDivider: {
    height: 1,
    backgroundColor: '#1B2435',
  },

  portfolioGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingTop: 14,
  },

  portfolioMetric: {
    width: '50%',
    paddingVertical: 7,
  },

  portfolioValue: {
    fontFamily: Platform.OS === 'android' ? 'Roboto' : 'System',
    fontVariant: ['tabular-nums'],
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '900',
    marginTop: 5,
  },

  /* ==========================================================
     STATUS
     ========================================================== */

  statusCard: {
    minHeight: 76,
    borderRadius: 17,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    paddingHorizontal: 15,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
  },

  statusItem: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },

  statusDivider: {
    width: 1,
    height: 34,
    backgroundColor: '#1B2435',
    marginHorizontal: 10,
  },

  liveDot: {
    width: 9,
    height: 9,
    borderRadius: 5,
    backgroundColor: '#35E68A',
    marginRight: 9,
  },

  offlineDot: {
    backgroundColor: '#FF7185',
  },

  botDot: {
    width: 9,
    height: 9,
    borderRadius: 5,
    backgroundColor: '#56627A',
    marginRight: 9,
  },

  botDotActive: {
    backgroundColor: '#35E68A',
  },

  statusLabel: {
    color: '#5D6981',
    fontSize: 8,
    fontWeight: '800',
    letterSpacing: 1.2,
  },

  liveText: {
    color: '#35E68A',
    fontSize: 11,
    fontWeight: '900',
    marginTop: 3,
  },

  offlineText: {
    color: '#FF7185',
  },

  botStatusText: {
    color: '#8995B1',
    fontSize: 11,
    fontWeight: '900',
    marginTop: 3,
  },

  botStatusActive: {
    color: '#35E68A',
  },

  /* ==========================================================
     MODE
     ========================================================== */

  modeCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 18,
    padding: 16,
    marginBottom: 24,
  },

  modeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },

  modeTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '900',
  },

  modeDescription: {
    color: '#69758E',
    fontSize: 11,
    marginTop: 4,
  },

  activePill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0D211A',
    borderRadius: 20,
    paddingHorizontal: 9,
    paddingVertical: 6,
  },

  activePillDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 5,
  },

  activePillText: {
    color: '#35E68A',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  modeButtons: {
    flexDirection: 'row',
    marginTop: 15,
    gap: 9,
  },

  modeButton: {
    flex: 1,
    height: 43,
    borderRadius: 11,
    borderWidth: 1,
    borderColor: '#202A3B',
    backgroundColor: '#070A11',
    alignItems: 'center',
    justifyContent: 'center',
  },

  modeButtonActive: {
    backgroundColor: '#334BFF',
    borderColor: '#334BFF',
  },

  modeButtonDisabled: {
    opacity: 0.55,
  },

  modeButtonText: {
    color: '#66738C',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1,
  },

  modeButtonTextActive: {
    color: '#FFFFFF',
  },

  /* ==========================================================
     QUICK ACCESS
     ========================================================== */

  quickGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 24,
  },

  quickCard: {
    width: '48.3%',
    minHeight: 118,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 17,
    padding: 14,
    marginBottom: 10,
  },

  quickCardPressed: {
    opacity: 0.75,
    transform: [{scale: 0.985}],
  },

  quickIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: '#111A38',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 13,
  },

  quickIconText: {
    color: '#7083FF',
    fontSize: 13,
    fontWeight: '900',
  },

  quickTitle: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '800',
  },

  quickSubtitle: {
    color: '#606C83',
    fontSize: 9,
    marginTop: 4,
  },

  /* ==========================================================
     SIGNALS
     ========================================================== */

  signalCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 18,
    padding: 16,
    marginBottom: 24,
  },

  signalTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },

  liveSignalBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0D211A',
    borderRadius: 20,
    paddingHorizontal: 9,
    paddingVertical: 5,
  },

  offlineSignalBadge: {
    backgroundColor: '#241317',
  },

  liveDotSmall: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 6,
  },

  offlineDotSmall: {
    backgroundColor: '#FF7185',
  },

  liveSignalText: {
    color: '#35E68A',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1,
  },

  offlineSignalText: {
    color: '#FF7185',
  },

  signalMode: {
    color: '#7083FF',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1,
  },

  signalMain: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 18,
  },

  signalSymbol: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '900',
  },

  signalStatus: {
    color: '#69758E',
    fontSize: 10,
    marginTop: 4,
  },

  signalArrow: {
    color: '#7083FF',
    fontSize: 22,
    fontWeight: '700',
  },

  signalFooter: {
    borderTopWidth: 1,
    borderTopColor: '#1B2435',
    marginTop: 15,
    paddingTop: 12,
  },

  signalFooterText: {
    color: '#56627A',
    fontSize: 9,
    lineHeight: 15,
  },

  /* ==========================================================
     MARKET DATA
     ========================================================== */

  marketDataNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
    paddingHorizontal: 3,
  },

  noticeDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 7,
  },

  noticeDotLive: {
    backgroundColor: '#35E68A',
  },

  noticeDotOffline: {
    backgroundColor: '#FF7185',
  },

  marketDataNoticeText: {
    color: '#59657C',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  marketCard: {
    minHeight: 82,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 16,
    paddingHorizontal: 11,
    marginBottom: 9,
    flexDirection: 'row',
    alignItems: 'center',
  },

  marketInfo: {
    width: 112,
  },

  marketSymbol: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '900',
    letterSpacing: 0.4,
  },

  directionBadge: {
    alignSelf: 'flex-start',
    borderRadius: 5,
    paddingHorizontal: 5,
    paddingVertical: 3,
    marginTop: 5,
  },

  bullishBadge: {
    backgroundColor: '#0D211A',
  },

  bearishBadge: {
    backgroundColor: '#241317',
  },

  neutralBadge: {
    backgroundColor: '#181B23',
  },

  directionText: {
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  bullishText: {
    color: '#35E68A',
  },

  bearishText: {
    color: '#FF7185',
  },

  neutralText: {
    color: '#8995B1',
  },

  marketChange: {
    color: '#77839B',
    fontSize: 9,
    marginTop: 3,
  },

  marketChartWrapper: {
    flex: 1,
    height: 60,
    justifyContent: 'center',
    overflow: 'hidden',
  },

  lineChart: {
    position: 'relative',
    overflow: 'hidden',
  },

  chartGridLine: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: 1,
    backgroundColor: '#151C2B',
  },

  emptyChart: {
    height: 60,
    alignItems: 'center',
    justifyContent: 'center',
  },

  emptyChartText: {
    color: '#4C5870',
    fontSize: 7,
    fontWeight: '900',
  },

  marketPriceBlock: {
    width: 45,
    alignItems: 'flex-end',
    marginLeft: 5,
  },

  marketPriceLabel: {
    color: '#46526A',
    fontSize: 6,
    fontWeight: '900',
  },

  marketPrice: {
    color: '#8995B1',
    fontSize: 9,
    marginTop: 3,
  },

  marketArrow: {
    color: '#4C5870',
    fontSize: 17,
    marginLeft: 7,
  },

  /* ==========================================================
     FOOTER
     ========================================================== */

  footerStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 10,
  },

  footerStatusText: {
    color: '#46526A',
    fontSize: 8,
    fontWeight: '800',
    letterSpacing: 1,
  },

  backendStatusText: {
    color: '#39445A',
    fontSize: 7,
    fontWeight: '700',
    textAlign: 'center',
    marginTop: 5,
    marginBottom: 5,
  },

  brokerCard: {
    backgroundColor: '#0F1626',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1E293B',
    marginBottom: 20,
  },
  brokerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
  },
  brokerAvatar: {
    overflow: "hidden",
    width: 44,
    height: 44,
    borderRadius: 10,
    backgroundColor: '#0EA5E9',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  profileAvatarImage: {
    width: '100%',
    height: '100%',
    borderRadius: 23,
  },
  brokerAvatarImage: {
    width: '100%',
    height: '100%',
    borderRadius: 22,
  },
  brokerAvatarText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 16,
  },
  brokerMainInfo: {
    flex: 1,
  },
  brokerName: {
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: '700',
  },
  brokerServer: {
    color: '#94A3B8',
    fontSize: 12,
    marginTop: 2,
  },
  brokerMetricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: '#080E1A',
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  brokerMetric: {
    flex: 1,
    alignItems: 'center',
  },
  brokerMetricDivider: {
    width: 1,
    backgroundColor: '#1E293B',
  },
  brokerMetricLabel: {
    color: '#64748B',
    fontSize: 10,
    fontWeight: '600',
    marginBottom: 2,
  },
  brokerMetricValue: {
    color: '#E2E8F0',
    fontSize: 13,
    fontWeight: '700',
  },
  sectionSubtitle: {
    color: '#64748B',
    fontSize: 11,
    fontWeight: '600',
  },
  winRateCard: {
    backgroundColor: '#0F1626',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1E293B',
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  winRateLeft: {
    width: 110,
    alignItems: 'center',
    justifyContent: 'center',
  },
  winRateGauge: {
    width: 90,
    height: 90,
    borderRadius: 45,
    borderWidth: 4,
    borderColor: '#0EA5E9',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#080E1A',
  },
  winRatePercent: {
    color: '#38BDF8',
    fontSize: 18,
    fontWeight: '800',
  },
  winRateGaugeLabel: {
    color: '#64748B',
    fontSize: 9,
    fontWeight: '700',
    marginTop: 2,
  },
  winRateStats: {
    flex: 1,
    paddingLeft: 12,
  },
  statRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 3,
  },
  statLabel: {
    color: '#94A3B8',
    fontSize: 12,
  },
  statValueBold: {
    color: '#F1F5F9',
    fontSize: 12,
    fontWeight: '700',
  },
  marketTable: {
    backgroundColor: '#0F1626',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#1E293B',
    overflow: 'hidden',
    marginBottom: 24,
  },
  marketTableHeader: {
    flexDirection: 'row',
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: '#080E1A',
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
  },
  marketTh: {
    color: '#64748B',
    fontSize: 11,
    fontWeight: '700',
  },
  marketTableRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#141D2E',
  },
  marketTableRowAlt: {
    backgroundColor: '#0A101D',
  },
  tableSymbol: {
    color: '#F8FAFC',
    fontSize: 13,
    fontWeight: '700',
  },
  tablePairType: {
    color: '#64748B',
    fontSize: 10,
    marginTop: 2,
  },
  tablePrice: {
    color: '#E2E8F0',
    fontSize: 13,
    fontWeight: '600',
  },
  changeBadge: {
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  changeBadgeBullish: {
    backgroundColor: 'rgba(34, 197, 94, 0.12)',
  },
  changeBadgeBearish: {
    backgroundColor: 'rgba(239, 68, 68, 0.12)',
  },
  changeBadgeText: {
    fontSize: 11,
    fontWeight: '700',
  },
  badgeLive: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(14, 165, 233, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeLiveText: {
    color: '#38BDF8',
    fontSize: 11,
    fontWeight: '700',
    marginLeft: 5,
  },

  profitPositive: {
    color: '#22C55E',
  },
  profitNegative: {
    color: '#EF4444',
  },
  metricGreen: {
    color: '#22C55E',
  },
});
