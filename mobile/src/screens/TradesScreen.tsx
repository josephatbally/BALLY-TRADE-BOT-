import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {BottomTabScreenProps} from '@react-navigation/bottom-tabs';
import {useSafeAreaInsets} from 'react-native-safe-area-context';

import {MainTabParamList} from '../navigation/MainTabNavigator';
import {BRANDING} from '../config/branding';
import {
  getApplicationMode,
  TradingMode,
} from '../api/appApi';
import {
  getMarketAnalysis,
  getMarkets,
  scanAllMarkets,
  MarketAnalysisItem,
  MarketScanItem,
  TradingDecision,
} from '../api/marketsApi';
import {
  getOpenPositions,
  OpenPosition,
} from '../api/positionsApi';

type TradesScreenProps = BottomTabScreenProps<
  MainTabParamList,
  'Trades'
>;

type MarketDirection =
  | 'BULLISH'
  | 'BEARISH'
  | 'NEUTRAL'
  | 'NONE';

type Market = {
  symbol: string;
  price: string;
  change: string;
  direction: MarketDirection;
  decision: TradingDecision;
  confidence: number;
  reason: string;
  points: number[];
  dataReady: boolean;
  analysisAvailable: boolean;
  latestTime: number | string | null;
};

type UserAction =
  | 'BUY'
  | 'SELL'
  | 'NO_TRADE'
  | null;

const POLL_INTERVAL = 10000;

function toNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === 'string') {
    const parsed = Number(value);

    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return null;
}

function formatPrice(value: number | null): string {
  if (value === null) {
    return '�';
  }

  if (Math.abs(value) >= 1000) {
    return value.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }

  if (Math.abs(value) >= 100) {
    return value.toFixed(2);
  }

  if (Math.abs(value) >= 10) {
    return value.toFixed(3);
  }

  return value.toFixed(5);
}

function formatPercent(value: number | null): string {
  if (value === null || !Number.isFinite(value)) {
    return '�';
  }

  const prefix = value > 0 ? '+' : '';

  return `${prefix}${value.toFixed(2)}%`;
}

function getTimeframe(
  scan: MarketScanItem | undefined,
  timeframe: string,
) {
  if (!scan?.timeframes) {
    return undefined;
  }

  return scan.timeframes[timeframe];
}

function getLatestClose(
  scan: MarketScanItem | undefined,
): number | null {
  const m15 = getTimeframe(scan, 'M15');

  const latestClosed = m15?.latest_closed_candle;

  const latestClosedPrice = toNumber(latestClosed?.close);

  if (latestClosedPrice !== null) {
    return latestClosedPrice;
  }

  const candles = m15?.candles ?? [];

  if (candles.length === 0) {
    return null;
  }

  return toNumber(candles[candles.length - 1]?.close);
}

function getPreviousClose(
  scan: MarketScanItem | undefined,
): number | null {
  const m15 = getTimeframe(scan, 'M15');

  const candles = m15?.candles ?? [];

  if (candles.length < 2) {
    return null;
  }

  return toNumber(candles[candles.length - 2]?.close);
}

function getChartPoints(
  scan: MarketScanItem | undefined,
): number[] {
  const candles = getTimeframe(scan, 'M15')?.candles ?? [];

  return candles
    .slice(-20)
    .map(candle => toNumber(candle.close))
    .filter(
      (value): value is number =>
        value !== null && Number.isFinite(value),
    );
}

function getDecision(
  analysis: MarketAnalysisItem | undefined,
): TradingDecision {
  const directDecision = analysis?.signal ?? analysis?.decision;

  if (
    typeof directDecision === 'string' &&
    ['BUY', 'SELL', 'NO_TRADE'].includes(
      directDecision.toUpperCase(),
    )
  ) {
    return directDecision.toUpperCase() as TradingDecision;
  }

  if (
    directDecision &&
    typeof directDecision === 'object' &&
    'decision' in directDecision
  ) {
    const nested = directDecision.decision;

    if (
      typeof nested === 'string' &&
      ['BUY', 'SELL', 'NO_TRADE'].includes(
        nested.toUpperCase(),
      )
    ) {
      return nested.toUpperCase() as TradingDecision;
    }
  }

  return 'NO_TRADE';
}

function getConfidence(
  analysis: MarketAnalysisItem | undefined,
): number {
  const direct = toNumber(analysis?.confidence);

  if (direct !== null) {
    return Math.max(0, Math.min(100, direct));
  }

  if (
    analysis?.ai_confidence &&
    typeof analysis.ai_confidence === 'object'
  ) {
    const nested =
      toNumber(analysis.ai_confidence.confidence) ??
      toNumber(analysis.ai_confidence.score);

    if (nested !== null) {
      return Math.max(0, Math.min(100, nested));
    }
  }

  if (typeof analysis?.ai_confidence === 'number') {
    return Math.max(
      0,
      Math.min(100, analysis.ai_confidence),
    );
  }

  return 0;
}

function getDirection(
  analysis: MarketAnalysisItem | undefined,
): MarketDirection {
  const raw =
    analysis?.dominant_direction ??
    analysis?.technical_analysis;

  if (typeof raw === 'string') {
    const value = raw.toUpperCase();

    if (
      value === 'BULLISH' ||
      value === 'BEARISH' ||
      value === 'NEUTRAL' ||
      value === 'NONE'
    ) {
      return value;
    }
  }

  const decision = getDecision(analysis);

  if (decision === 'BUY') {
    return 'BULLISH';
  }

  if (decision === 'SELL') {
    return 'BEARISH';
  }

  return 'NEUTRAL';
}

function getReason(
  analysis: MarketAnalysisItem | undefined,
): string {
  if (typeof analysis?.reason === 'string') {
    return analysis.reason;
  }

  if (
    Array.isArray(analysis?.reasons) &&
    analysis.reasons.length > 0
  ) {
    return analysis.reasons.join(' � ');
  }

  return 'Awaiting complete market analysis.';
}

function buildMarket(
  symbol: string,
  scan: MarketScanItem | undefined,
  analysis: MarketAnalysisItem | undefined,
): Market {
  const price = getLatestClose(scan);
  const previousPrice = getPreviousClose(scan);

  let change: number | null = null;

  if (
    price !== null &&
    previousPrice !== null &&
    previousPrice !== 0
  ) {
    change =
      ((price - previousPrice) / previousPrice) * 100;
  }

  const m15 = getTimeframe(scan, 'M15');

  return {
    symbol,
    price: formatPrice(price),
    change: formatPercent(change),
    direction: getDirection(analysis),
    decision: getDecision(analysis),
    confidence: getConfidence(analysis),
    reason: getReason(analysis),
    points: getChartPoints(scan),
    dataReady: Boolean(
      scan?.data_ready &&
        (scan?.ready_timeframe_count ?? 0) >= 3,
    ),
    analysisAvailable: Boolean(analysis),
    latestTime:
      m15?.latest_closed_candle_time ??
      m15?.latest_candle_time ??
      null,
  };
}

function Sparkline({
  points,
}: {
  points: number[];
}) {
  if (points.length < 2) {
    return (
      <View style={styles.sparklineEmpty}>
        <Text style={styles.sparklineEmptyText}>
          NO CHART DATA
        </Text>
      </View>
    );
  }

  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;

  return (
    <View style={styles.sparkline}>
      {points.map((point, index) => {
        const height =
          8 + ((point - min) / range) * 34;

        return (
          <View
            key={`${point}-${index}`}
            style={[
              styles.sparkBar,
              {
                height,
              },
            ]}
          />
        );
      })}
    </View>
  );
}

function DecisionBadge({
  decision,
}: {
  decision: TradingDecision;
}) {
  return (
    <View
      style={[
        styles.decisionBadge,
        decision === 'BUY' && styles.buyBadge,
        decision === 'SELL' && styles.sellBadge,
        decision === 'NO_TRADE' && styles.noTradeBadge,
      ]}>
      <Text
        style={[
          styles.decisionText,
          decision === 'BUY' && styles.buyText,
          decision === 'SELL' && styles.sellText,
          decision === 'NO_TRADE' && styles.noTradeText,
        ]}>
        {decision}
      </Text>
    </View>
  );
}

export default function TradesScreen({}: TradesScreenProps) {
  const insets = useSafeAreaInsets();

  const [mode, setMode] =
    useState<TradingMode>('technical');

  const [marketSymbols, setMarketSymbols] =
    useState<string[]>([]);

  const [marketData, setMarketData] = useState<
    Record<string, MarketScanItem>
  >({});

  const [analysisData, setAnalysisData] = useState<
    Record<string, MarketAnalysisItem>
  >({});

  const [positions, setPositions] = useState<
    OpenPosition[]
  >([]);

  const [selectedSymbol, setSelectedSymbol] =
    useState('');

  const [userAction, setUserAction] =
    useState<UserAction>(null);

  const [loading, setLoading] = useState(true);

  const [refreshing, setRefreshing] =
    useState(false);

  const [error, setError] = useState<string | null>(
    null,
  );

  const [lastUpdated, setLastUpdated] =
    useState<Date | null>(null);

  const selectedMarket = useMemo(
    () =>
      buildMarket(
        selectedSymbol,
        marketData[selectedSymbol],
        analysisData[selectedSymbol],
      ),
    [
      selectedSymbol,
      marketData,
      analysisData,
    ],
  );

  
    const loadData = useCallback(
    async (showLoader = false) => {
      if (showLoader) {
        setRefreshing(true);
      }

      setError(null);

      const errors: string[] = [];

      try {
        /*
         * Each backend source is loaded independently.
         *
         * This is intentional:
         * a failure in positions must not prevent
         * market data or market analysis from reaching
         * the screen.
         */

        const [
          appModeResult,
          marketsResult,
          scanResult,
          analysisResult,
          positionsResult,
        ] = await Promise.allSettled([
          getApplicationMode(),
          getMarkets(),
          scanAllMarkets(),
          getMarketAnalysis('technical'),
          getOpenPositions(),
        ]);

        /*
         * APPLICATION MODE
         */
        if (
          appModeResult.status === 'fulfilled' &&
          appModeResult.value?.mode
        ) {
          setMode(appModeResult.value.mode);
        } else if (
          appModeResult.status === 'rejected'
        ) {
          errors.push('Application mode unavailable.');
        }

        /*
         * MARKET UNIVERSE
         */
        let symbols: string[] = [];

        if (marketsResult.status === 'fulfilled') {
          const backendMarkets =
            Array.isArray(
              marketsResult.value?.markets,
            )
              ? marketsResult.value.markets
              : [];

          symbols = backendMarkets
            .map(symbol =>
              String(symbol).toUpperCase(),
            )
            .filter(symbol =>
              [
                'XAUUSD',
                'EURUSD',
                'GBPUSD',
                'USDJPY',
                'XAGUSD',
                'NASDAQ',
              ].includes(symbol),
            );

          setMarketSymbols(symbols);
        } else {
          errors.push('Market universe unavailable.');
        }

        /*
         * MARKET DATA SCAN
         */
        if (scanResult.status === 'fulfilled') {
          const scanMap: Record<
            string,
            MarketScanItem
          > = {};

          const scannedMarkets =
            scanResult.value?.scan?.markets ?? [];

          scannedMarkets.forEach(
            (item: MarketScanItem) => {
              const logicalSymbol =
                item.market ??
                item.symbol ??
                item.broker_symbol;

              if (!logicalSymbol) {
                return;
              }

              scanMap[
                String(logicalSymbol).toUpperCase()
              ] = item;
            },
          );

          setMarketData(scanMap);
        } else {
          errors.push('Market scan unavailable.');
        }

        /*
         * AUTHORITATIVE MARKET ANALYSIS
         *
         * Technical mode is explicitly requested.
         * This prevents the screen from accidentally
         * depending on an unspecified API default.
         */
        if (analysisResult.status === 'fulfilled') {
          const analysisMap: Record<
            string,
            MarketAnalysisItem
          > = {};

          const analysedMarkets =
            analysisResult.value?.analysis ?? {};

          Object.entries(
            analysedMarkets,
          ).forEach(([symbol, item]) => {
            if (
              item &&
              typeof item === 'object'
            ) {
              analysisMap[
                String(symbol).toUpperCase()
              ] = item as MarketAnalysisItem;
            }
          });

          setAnalysisData(analysisMap);
        } else {
          errors.push('Market analysis unavailable.');
        }

        /*
         * OPEN MT5 POSITIONS
         */
        if (positionsResult.status === 'fulfilled') {
          setPositions(
            positionsResult.value?.positions ?? [],
          );
        } else {
          errors.push('Open positions unavailable.');
        }

        /*
         * SELECT FIRST BACKEND MARKET ONLY WHEN
         * THE CURRENT SELECTION IS NO LONGER VALID.
         */
        if (
          symbols.length > 0 &&
          !symbols.includes(
            selectedSymbol.toUpperCase(),
          )
        ) {
          setSelectedSymbol(symbols[0]);
          setUserAction(null);
        }

        setLastUpdated(new Date());

        if (errors.length > 0) {
          setError(errors.join(' '));
        }
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : 'Unable to load BALLY FLOW backend data.';

        setError(message);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [selectedSymbol],
  );

    useEffect(() => {
    loadData(true);

    const interval = setInterval(() => {
      loadData(false);
    }, POLL_INTERVAL);

    return () => clearInterval(interval);
  }, [loadData]);

  const markets = useMemo(
    () =>
      marketSymbols.map(
        (symbol: string) =>
          buildMarket(
            symbol,
            marketData[symbol],
            analysisData[symbol],
          ),
      ),
    [marketSymbols, marketData, analysisData],
  );

  const connectionReady = useMemo(
    () =>
      markets.some(
        market =>
          market.dataReady &&
          market.price !== '�',
      ),
    [markets],
  );

  const totalConfidence = selectedMarket.analysisAvailable
    ? selectedMarket.confidence
    : null;

  const selectedPositions = useMemo(
    () => {
      if (!selectedSymbol) {
        return [];
      }

      return positions.filter(
        position =>
          position.symbol?.toUpperCase() ===
          selectedSymbol.toUpperCase(),
      );
    },
    [positions, selectedSymbol],
  );

  const totalOpenProfit = useMemo(
    () =>
      selectedPositions.reduce(
        (sum, position) =>
          sum + Number(position.profit ?? 0),
        0,
      ),
    [selectedPositions],
  );

  const handleAction = (action: UserAction) => {
    if (!selectedMarket.analysisAvailable) {
      setUserAction(null);
      return;
    }

    setUserAction(action);
  };
  return (
    <View
      style={[
        styles.container,
        {
          paddingTop: insets.top,
        },
      ]}>
      <StatusBar barStyle="light-content" />

      <ScrollView
        contentContainerStyle={[
          styles.content,
          {
            paddingBottom: insets.bottom + 32,
          },
        ]}
        showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <View>
            <Text style={styles.eyebrow}>
              TRADING INTELLIGENCE
            </Text>

            <Text style={styles.title}>
              {BRANDING?.appName ?? 'BALLY FLOW'}
            </Text>

            <Text style={styles.subtitle}>
              Live market decision interface
            </Text>
          </View>

          <Pressable
            style={styles.refreshButton}
            onPress={() => loadData(true)}
            disabled={refreshing}>
            {refreshing ? (
              <ActivityIndicator
                size="small"
                color="#FFFFFF"
              />
            ) : (
              <Text style={styles.refreshText}>
                REFRESH
              </Text>
            )}
          </Pressable>
        </View>

        <View style={styles.statusRow}>
          <View style={styles.statusItem}>
            <View
              style={[
                styles.statusDot,
                connectionReady
                  ? styles.statusOnline
                  : styles.statusOffline,
              ]}
            />

            <Text style={styles.statusLabel}>
              {connectionReady
                ? 'DATA READY'
                : 'DATA UNAVAILABLE'}
            </Text>
          </View>

          <View style={styles.modePill}>
            <Text style={styles.modeText}>
              {mode.toUpperCase()} MODE
            </Text>
          </View>
        </View>

        {error ? (
          <View style={styles.errorCard}>
            <Text style={styles.errorTitle}>
              DATA CONNECTION WARNING
            </Text>

            <Text style={styles.errorText}>
              {error}
            </Text>

            <Text style={styles.errorHint}>
              The interface remains read-only until
              live backend data is available.
            </Text>
          </View>
        ) : null}

        <View style={styles.marketSection}>
          <View style={styles.sectionHeader}>
            <View>
              <Text style={styles.sectionEyebrow}>
                MARKET UNIVERSE
              </Text>

              <Text style={styles.sectionTitle}>
                Six supported markets
              </Text>
            </View>

            <Text style={styles.marketCount}>
              {marketSymbols.length}
            </Text>
          </View>

          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={
              styles.marketSelector
            }>
            {markets.map((market: Market) => {
              const selected =
                market.symbol === selectedSymbol;

              return (
                <Pressable
                  key={market.symbol}
                  onPress={() => {
                    setSelectedSymbol(
                      market.symbol,
                    );
                    setUserAction(null);
                  }}
                  style={[
                    styles.marketChip,
                    selected &&
                      styles.marketChipSelected,
                  ]}>
                  <Text
                    style={[
                      styles.marketChipText,
                      selected &&
                        styles.marketChipTextSelected,
                    ]}>
                    {market.symbol}
                  </Text>

                  <Text
                    style={[
                      styles.marketChipPrice,
                      selected &&
                        styles.marketChipPriceSelected,
                    ]}>
                    {market.price}
                  </Text>
                </Pressable>
              );
            })}
          </ScrollView>
        </View>

        {loading && markets.length === 0 ? (
          <View style={styles.loadingCard}>
            <ActivityIndicator
              size="large"
              color="#FFFFFF"
            />

            <Text style={styles.loadingText}>
              ACQUIRING LIVE MARKET DATA...
            </Text>
          </View>
        ) : (
          <>
            <View style={styles.heroCard}>
              <View style={styles.heroTop}>
                <View>
                  <Text style={styles.heroSymbol}>
                    {selectedMarket.symbol}
                  </Text>

                  <Text style={styles.heroPrice}>
                    {selectedMarket.price}
                  </Text>

                  <Text style={styles.heroChange}>
                    {selectedMarket.change} M15 MOVE
                  </Text>
                </View>

                <View style={styles.heroDecision}>
                  <Text style={styles.miniLabel}>
                    DECISION
                  </Text>

                  <>{selectedMarket.analysisAvailable ? (
                    <DecisionBadge
                      decision={selectedMarket.decision}
                    />
                  ) : (
                    <Text style={styles.metricValue}>
                      ANALYSIS UNAVAILABLE
                    </Text>
                  )}</>
                </View>
              </View>

              <Sparkline
                points={selectedMarket.points}
              />

              <View style={styles.metricsRow}>
                <View style={styles.metricBox}>
                  <Text style={styles.miniLabel}>
                    DIRECTION
                  </Text>

                  <Text
                    style={[
                      styles.metricValue,
                      selectedMarket.direction ===
                        'BULLISH' &&
                        styles.buyText,
                      selectedMarket.direction ===
                        'BEARISH' &&
                        styles.sellText,
                    ]}>
                    {selectedMarket.direction}
                  </Text>
                </View>

                <View style={styles.metricBox}>
                  <Text style={styles.miniLabel}>
                    CONFIDENCE
                  </Text>

                  <Text style={styles.metricValue}>
                    {totalConfidence !== null ? `${totalConfidence.toFixed(1)}%` : '�'}
                  </Text>
                </View>

                <View style={styles.metricBox}>
                  <Text style={styles.miniLabel}>
                    DATA
                  </Text>

                  <Text
                    style={[
                      styles.metricValue,
                      selectedMarket.dataReady
                        ? styles.buyText
                        : styles.sellText,
                    ]}>
                    {selectedMarket.dataReady
                      ? 'READY'
                      : 'WAIT'}
                  </Text>
                </View>
              </View>
            </View>

            <View style={styles.analysisCard}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>
                  MARKET ANALYSIS
                </Text>

                <Text style={styles.cardStage}>
                  H4 ? H1 ? M15
                </Text>
              </View>

              <View style={styles.analysisLine}>
                <Text style={styles.analysisLabel}>
                  MARKET
                </Text>

                <Text style={styles.analysisValue}>
                  {selectedMarket.symbol}
                </Text>
              </View>

              <View style={styles.analysisLine}>
  <Text style={styles.analysisLabel}>
    DIRECTION
  </Text>

  <Text style={styles.analysisValue}>
    {selectedMarket.analysisAvailable
      ? selectedMarket.direction
      : 'ANALYSIS UNAVAILABLE'}
  </Text>
</View>

              <View style={styles.analysisLine}>
                <Text style={styles.analysisLabel}>
                  CONFIDENCE
                </Text>

                <Text style={styles.analysisValue}>
  {selectedMarket.analysisAvailable
    ? `${selectedMarket.confidence.toFixed(1)}%`
    : '�'}
</Text>
              </View>

              <View style={styles.reasonBox}>
                <Text style={styles.reasonLabel}>
                  ENGINE REASON
                </Text>
              <Text style={styles.reasonText}>
  {selectedMarket.analysisAvailable
    ? selectedMarket.reason
    : 'Backend analysis has not returned for this market.'}
</Text>
              </View>
            </View>

            <View style={styles.positionsCard}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>
                  OPEN POSITIONS
                </Text>

                <Text style={styles.cardStage}>
                  {positions.length} TOTAL
                </Text>
              </View>

              <View style={styles.positionSummary}>
                <View>
                  <Text style={styles.summaryLabel}>
                    OPEN P&L
                  </Text>

                  <Text
                    style={[
                      styles.summaryValue,
                      totalOpenProfit >= 0
                        ? styles.buyText
                        : styles.sellText,
                    ]}>
                    {totalOpenProfit >= 0
                      ? '+'
                      : ''}
                    {totalOpenProfit.toFixed(2)}
                  </Text>
                </View>

                <View>
                  <Text style={styles.summaryLabel}>
                    {selectedSymbol}
                  </Text>

                  <Text style={styles.summaryValue}>
                    {selectedPositions.length}
                  </Text>
                </View>
              </View>

              {selectedPositions.length === 0 ? (
                <View style={styles.emptyPosition}>
                  <Text
                    style={styles.emptyPositionText}>
                    NO OPEN POSITION FOR{' '}
                    {selectedSymbol}
                  </Text>
                </View>
              ) : (
                selectedPositions.map(
                  (position: OpenPosition) => (
                    <View
                      key={String(position.ticket)}
                      style={styles.positionRow}>
                      <View>
                        <Text
                          style={
                            styles.positionSymbol
                          }>
                          {position.symbol}
                        </Text>

                        <Text
                          style={
                            styles.positionMeta
                          }>
                          {position.type} �{' '}
                          {position.volume}
                        </Text>
                      </View>

                      <View
                        style={
                          styles.positionRight
                        }>
                        <Text
                          style={[
                            styles.positionProfit,
                            position.profit >= 0
                              ? styles.buyText
                              : styles.sellText,
                          ]}>
                          {position.profit >= 0
                            ? '+'
                            : ''}
                          {position.profit.toFixed(
                            2,
                          )}
                        </Text>

                        <Text
                          style={
                            styles.positionPrice
                          }>
                          {formatPrice(
                            Number(
                              position.current_price,
                            ),
                          )}
                        </Text>
                      </View>
                    </View>
                  ),
                )
              )}
            </View>

            <View style={styles.actionCard}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>
                  TRADE DECISION
                </Text>

                <Text style={styles.cardStage}>
                  READ ONLY
                </Text>
              </View>

              <Text style={styles.actionDescription}>
                These controls represent the selected
                decision only. They do not bypass
                backend risk management, validation,
                execution permissions, or MT5 safety
                controls.
              </Text>

              <View style={styles.actionRow}>
                <Pressable
                  style={[
                    styles.actionButton,
                    styles.buyButton,
                    userAction === 'BUY' &&
                      styles.actionSelected,
                  ]}
                  onPress={() =>
                    handleAction('BUY')
                  }>
                  <Text style={styles.actionText}>
                    BUY
                  </Text>
                </Pressable>

                <Pressable
                  style={[
                    styles.actionButton,
                    styles.sellButton,
                    userAction === 'SELL' &&
                      styles.actionSelected,
                  ]}
                  onPress={() =>
                    handleAction('SELL')
                  }>
                  <Text style={styles.actionText}>
                    SELL
                  </Text>
                </Pressable>

                <Pressable
                  style={[
                    styles.actionButton,
                    styles.noTradeButton,
                    userAction === 'NO_TRADE' &&
                      styles.actionSelected,
                  ]}
                  onPress={() =>
                    handleAction('NO_TRADE')
                  }>
                  <Text style={styles.actionText}>
                    NO TRADE
                  </Text>
                </Pressable>
              </View>

              {userAction ? (
                <View style={styles.actionFeedback}>
                  <Text
                    style={
                      styles.actionFeedbackText
                    }>
                    SELECTED: {userAction}
                  </Text>

                  <Text
                    style={
                      styles.actionFeedbackSubtext
                    }>
                    Backend execution remains
                    authoritative.
                  </Text>
                </View>
              ) : null}
            </View>

            <View style={styles.safetyCard}>
              <Text style={styles.safetyTitle}>
                EXECUTION SAFETY
              </Text>

              <Text style={styles.safetyText}>
                Final trade execution must pass
                backend validation, risk management,
                broker constraints, and MT5 execution
                permissions. This screen never sends an
                order directly to the broker.
              </Text>
            </View>

            <View style={styles.footer}>
              <Text style={styles.footerText}>
                {lastUpdated
                  ? `UPDATED ${lastUpdated.toLocaleTimeString()}`
                  : 'WAITING FOR LIVE DATA'}
              </Text>

              <Text style={styles.footerText}>
                {mode.toUpperCase()} � H4/H1/M15
              </Text>
            </View>
          </>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#05070B',
  },

  content: {
    paddingHorizontal: 18,
    paddingTop: 18,
  },

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 18,
  },

  eyebrow: {
    color: '#7C8798',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 2,
  },

  title: {
    color: '#FFFFFF',
    fontSize: 25,
    fontWeight: '900',
    marginTop: 4,
  },

  subtitle: {
    color: '#707B8C',
    fontSize: 12,
    marginTop: 4,
  },

  refreshButton: {
    minWidth: 76,
    height: 34,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#26303E',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 10,
  },

  refreshText: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1,
  },

  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 18,
  },

  statusItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  statusDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    marginRight: 7,
  },

  statusOnline: {
    backgroundColor: '#32D583',
  },

  statusOffline: {
    backgroundColor: '#F04438',
  },

  statusLabel: {
    color: '#8D98A8',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
  },

  modePill: {
    borderWidth: 1,
    borderColor: '#293443',
    borderRadius: 20,
    paddingHorizontal: 11,
    paddingVertical: 6,
  },

  modeText: {
    color: '#AEB8C7',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1,
  },

  errorCard: {
    borderWidth: 1,
    borderColor: '#5A2929',
    backgroundColor: '#180D0F',
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
  },

  errorTitle: {
    color: '#F97066',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 1,
  },

  errorText: {
    color: '#E5B8B8',
    fontSize: 12,
    marginTop: 7,
    lineHeight: 18,
  },

  errorHint: {
    color: '#8F6E70',
    fontSize: 10,
    marginTop: 7,
    lineHeight: 15,
  },

  marketSection: {
    marginBottom: 16,
  },

  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    marginBottom: 10,
  },

  sectionEyebrow: {
    color: '#6F7A8A',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1.5,
  },

  sectionTitle: {
    color: '#DCE2EA',
    fontSize: 15,
    fontWeight: '800',
    marginTop: 3,
  },

  marketCount: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: '900',
  },

  marketSelector: {
    gap: 8,
  },

  marketChip: {
    minWidth: 88,
    borderWidth: 1,
    borderColor: '#202A37',
    backgroundColor: '#0A0E14',
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 9,
  },

  marketChipSelected: {
    borderColor: '#687587',
    backgroundColor: '#111823',
  },

  marketChipText: {
    color: '#778292',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1,
  },

  marketChipTextSelected: {
    color: '#FFFFFF',
  },

  marketChipPrice: {
    color: '#A2ACBA',
    fontSize: 11,
    fontWeight: '700',
    marginTop: 4,
  },

  marketChipPriceSelected: {
    color: '#FFFFFF',
  },

  loadingCard: {
    minHeight: 180,
    borderRadius: 14,
    backgroundColor: '#0A0E14',
    borderWidth: 1,
    borderColor: '#1C2531',
    alignItems: 'center',
    justifyContent: 'center',
  },

  loadingText: {
    color: '#7E8999',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
    marginTop: 12,
  },

  heroCard: {
    backgroundColor: '#0A0E14',
    borderWidth: 1,
    borderColor: '#202A36',
    borderRadius: 16,
    padding: 16,
    marginBottom: 14,
  },

  heroTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },

  heroSymbol: {
    color: '#8894A4',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 1.5,
  },

  heroPrice: {
    color: '#FFFFFF',
    fontSize: 31,
    fontWeight: '900',
    marginTop: 4,
  },

  heroChange: {
    color: '#718092',
    fontSize: 10,
    fontWeight: '700',
    marginTop: 3,
  },

  heroDecision: {
    alignItems: 'flex-end',
  },

  miniLabel: {
    color: '#687486',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1.2,
  },

  decisionBadge: {
    borderRadius: 7,
    paddingHorizontal: 10,
    paddingVertical: 7,
    marginTop: 6,
    borderWidth: 1,
  },

  decisionText: {
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 1,
  },

  buyBadge: {
    borderColor: '#1D6F4B',
    backgroundColor: '#0C2119',
  },

  sellBadge: {
    borderColor: '#713530',
    backgroundColor: '#21100F',
  },

  noTradeBadge: {
    borderColor: '#414B59',
    backgroundColor: '#141921',
  },

  buyText: {
    color: '#32D583',
  },

  sellText: {
    color: '#F97066',
  },

  noTradeText: {
    color: '#AAB4C1',
  },

  sparkline: {
    height: 48,
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 3,
    marginTop: 18,
    overflow: 'hidden',
  },

  sparkBar: {
    flex: 1,
    minWidth: 3,
    backgroundColor: '#657285',
    borderRadius: 2,
  },

  sparklineEmpty: {
    height: 48,
    borderWidth: 1,
    borderColor: '#1B2430',
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 18,
    borderRadius: 7,
  },

  sparklineEmptyText: {
    color: '#566273',
    fontSize: 8,
    fontWeight: '800',
    letterSpacing: 1,
  },

  metricsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 16,
  },

  metricBox: {
    flex: 1,
    backgroundColor: '#070A0F',
    borderRadius: 8,
    padding: 10,
  },

  metricValue: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '900',
    marginTop: 5,
  },

  analysisCard: {
    backgroundColor: '#0A0E14',
    borderWidth: 1,
    borderColor: '#202A36',
    borderRadius: 14,
    padding: 15,
    marginBottom: 14,
  },

  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 13,
  },

  cardTitle: {
    color: '#DCE2EA',
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1,
  },

  cardStage: {
    color: '#697586',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1,
  },

  analysisLine: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderBottomWidth: 1,
    borderBottomColor: '#141B24',
    paddingVertical: 10,
  },

  analysisLabel: {
    color: '#667284',
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 1,
  },

  analysisValue: {
    color: '#D9E0E8',
    fontSize: 10,
    fontWeight: '800',
  },

  reasonBox: {
    marginTop: 12,
    padding: 11,
    borderRadius: 8,
    backgroundColor: '#070A0F',
  },

  reasonLabel: {
    color: '#667284',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1,
  },

  reasonText: {
    color: '#AAB4C1',
    fontSize: 11,
    lineHeight: 17,
    marginTop: 6,
  },

  positionsCard: {
    backgroundColor: '#0A0E14',
    borderWidth: 1,
    borderColor: '#202A36',
    borderRadius: 14,
    padding: 15,
    marginBottom: 14,
  },

  positionSummary: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: '#070A0F',
    borderRadius: 9,
    padding: 12,
    marginBottom: 10,
  },

  summaryLabel: {
    color: '#657183',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1,
  },

  summaryValue: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '900',
    marginTop: 4,
  },

  emptyPosition: {
    borderWidth: 1,
    borderColor: '#1B2430',
    borderStyle: 'dashed',
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
  },

  emptyPositionText: {
    color: '#5E6979',
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.7,
  },

  positionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 11,
    borderBottomWidth: 1,
    borderBottomColor: '#141B24',
  },

  positionSymbol: {
    color: '#DCE2EA',
    fontSize: 11,
    fontWeight: '900',
  },

  positionMeta: {
    color: '#667284',
    fontSize: 9,
    marginTop: 4,
  },

  positionRight: {
    alignItems: 'flex-end',
  },

  positionProfit: {
    fontSize: 11,
    fontWeight: '900',
  },

  positionPrice: {
    color: '#697586',
    fontSize: 9,
    marginTop: 3,
  },

  actionCard: {
    backgroundColor: '#0A0E14',
    borderWidth: 1,
    borderColor: '#202A36',
    borderRadius: 14,
    padding: 15,
    marginBottom: 14,
  },

  actionDescription: {
    color: '#697586',
    fontSize: 10,
    lineHeight: 16,
    marginBottom: 13,
  },

  actionRow: {
    flexDirection: 'row',
    gap: 7,
  },

  actionButton: {
    flex: 1,
    height: 42,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
  },

  buyButton: {
    borderColor: '#1D6F4B',
    backgroundColor: '#0C2119',
  },

  sellButton: {
    borderColor: '#713530',
    backgroundColor: '#21100F',
  },

  noTradeButton: {
    borderColor: '#414B59',
    backgroundColor: '#141921',
  },

  actionSelected: {
    borderColor: '#FFFFFF',
  },

  actionText: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  actionFeedback: {
    marginTop: 11,
    borderRadius: 8,
    backgroundColor: '#070A0F',
    padding: 10,
  },

  actionFeedbackText: {
    color: '#DCE2EA',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1,
  },

  actionFeedbackSubtext: {
    color: '#626E7E',
    fontSize: 9,
    marginTop: 4,
  },

  safetyCard: {
    borderWidth: 1,
    borderColor: '#283342',
    backgroundColor: '#080C12',
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
  },

  safetyTitle: {
    color: '#9AA6B6',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1.2,
  },

  safetyText: {
    color: '#626E7E',
    fontSize: 10,
    lineHeight: 16,
    marginTop: 7,
  },

  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },

  footerText: {
    color: '#4D5867',
    fontSize: 8,
    fontWeight: '800',
    letterSpacing: 0.6,
  },
});










