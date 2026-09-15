import React from 'react';
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import {
  getMarkets,
  getScannerStatus,
  scanAllMarkets,
  getMarketAnalysis,
  SUPPORTED_MARKETS,
  ANALYSIS_TIMEFRAMES,
  MarketSymbol,
  ScannerStatusResponse,
  ScanAllMarketsPayload,
  AllMarketAnalysisResponse,
  MarketAnalysisItem,
  MarketQuote,
  getMarketQuotes,
} from '../api/marketsApi';

type MarketStatus = 'READY' | 'PARTIAL' | 'WAITING' | 'FAILED';

type Market = {
  symbol: MarketSymbol;
  name: string;
  category: string;
};

const MARKET_META: Record<
  MarketSymbol,
  {name: string; category: string}
> = {
  XAUUSD: {
    name: 'Gold / US Dollar',
    category: 'METALS',
  },
  EURUSD: {
    name: 'Euro / US Dollar',
    category: 'FOREX',
  },
  GBPUSD: {
    name: 'British Pound / US Dollar',
    category: 'FOREX',
  },
  USDJPY: {
    name: 'US Dollar / Japanese Yen',
    category: 'FOREX',
  },
  XAGUSD: {
    name: 'Silver / US Dollar',
    category: 'METALS',
  },
  NASDAQ: {
    name: 'Nasdaq Index',
    category: 'INDEX',
  },
};

function normaliseStatus(value: unknown): MarketStatus {
  const status = String(value ?? '').toUpperCase();

  if (status === 'READY') {
    return 'READY';
  }

  if (status === 'PARTIAL') {
    return 'PARTIAL';
  }

  if (
    status === 'FAILED' ||
    status === 'ERROR' ||
    status === 'UNAVAILABLE'
  ) {
    return 'FAILED';
  }

  return 'WAITING';
}

function getScanMarket(
  scan: ScanAllMarketsPayload | null,
  symbol: MarketSymbol,
) {
  return scan?.scan?.markets?.find(
    item =>
      String(item.market ?? item.symbol ?? '').toUpperCase() === symbol,
  );
}

function getMarketStatus(
  scan: ScanAllMarketsPayload | null,
  symbol: MarketSymbol,
): MarketStatus {
  const item = getScanMarket(scan, symbol);

  if (!item) {
    return 'WAITING';
  }

  if (item.data_ready === true) {
    return 'READY';
  }

  if (
    typeof item.ready_timeframe_count === 'number' &&
    item.ready_timeframe_count > 0
  ) {
    return 'PARTIAL';
  }

  return normaliseStatus(item.status);
}

function isTimeframeReady(
  scan: ScanAllMarketsPayload | null,
  symbol: MarketSymbol,
  timeframe: string,
): boolean {
  const item = getScanMarket(scan, symbol);
  const timeframeData = item?.timeframes?.[timeframe];

  if (!timeframeData) {
    return false;
  }

  if (timeframeData.status) {
    return normaliseStatus(timeframeData.status) === 'READY';
  }

  return Boolean(
    timeframeData.candles &&
      timeframeData.candles.length > 0 &&
      timeframeData.latest_closed_candle_time != null,
  );
}

function getQuoteFor(
  quotes: MarketQuote[],
  symbol: MarketSymbol,
): MarketQuote | null {
  const match = quotes.find(
    item => String(item.symbol ?? '').toUpperCase() === symbol,
  );
  return match ?? null;
}

function getAnalysisMarket(
  analysis: AllMarketAnalysisResponse | null,
  symbol: MarketSymbol,
): MarketAnalysisItem | null {
  if (!analysis?.analysis) {
    return null;
  }

  const markets = analysis.analysis as Record<
    string,
    MarketAnalysisItem
  >;

  const direct = markets[symbol];

  if (direct) {
    return direct;
  }

  const match = Object.entries(markets).find(
    ([key, item]) =>
      key.toUpperCase() === symbol ||
      String(item?.market ?? item?.symbol ?? '').toUpperCase() ===
        symbol,
  );

  return match?.[1] ?? null;
}

function getAnalysisDecision(
  item: MarketAnalysisItem | null,
): string | null {
  if (!item) {
    return null;
  }

  if (typeof item.decision === 'string') {
    return item.decision.toUpperCase();
  }

  if (
    item.decision &&
    typeof item.decision === 'object'
  ) {
    const decision = item.decision as {
      decision?: unknown;
      signal?: unknown;
    };

    const value =
      decision.decision ?? decision.signal;

    return value
      ? String(value).toUpperCase()
      : null;
  }

  if (item.signal) {
    return String(item.signal).toUpperCase();
  }

  return null;
}

function getAnalysisConfidence(
  item: MarketAnalysisItem | null,
): number | null {
  if (!item) {
    return null;
  }

  if (typeof item.confidence === 'number') {
    return item.confidence;
  }

  if (
    item.ai_confidence &&
    typeof item.ai_confidence === 'object'
  ) {
    const confidence =
      item.ai_confidence.confidence ??
      item.ai_confidence.score;

    return typeof confidence === 'number'
      ? confidence
      : null;
  }

  if (typeof item.ai_confidence === 'number') {
    return item.ai_confidence;
  }

  return null;
}

function getAnalysisDirection(
  item: MarketAnalysisItem | null,
): string | null {
  if (!item) {
    return null;
  }

  if (item.dominant_direction) {
    return String(
      item.dominant_direction,
    ).toUpperCase();
  }

  if (
    item.decision &&
    typeof item.decision === 'object'
  ) {
    const decision = item.decision as {
      dominant_direction?: unknown;
    };

    if (decision.dominant_direction) {
      return String(
        decision.dominant_direction,
      ).toUpperCase();
    }
  }

  return null;
}

function StatusPill({
  status,
}: {
  status: MarketStatus;
}) {
  const label =
    status === 'READY'
      ? 'READY'
      : status === 'PARTIAL'
        ? 'PARTIAL'
        : status === 'FAILED'
          ? 'FAILED'
          : 'WAITING';

  return (
    <View style={styles.statusPill}>
      <View style={styles.statusDot} />
      <Text allowFontScaling={false} style={styles.statusText}>{label}</Text>
    </View>
  );
}

function TimeframeStatus({
  timeframe,
  ready,
}: {
  timeframe: string;
  ready: boolean;
}) {
  return (
    <View style={styles.timeframeItem}>
      <View
        style={[
          styles.timeframeDot,
          ready && styles.timeframeDotReady,
        ]}
      />
      <Text allowFontScaling={false} style={styles.timeframeText}>{timeframe}</Text>
    </View>
  );
}

export default function MarketsScreen() {
  const [markets, setMarkets] = React.useState<Market[]>([]);
  const [scanner, setScanner] =
    React.useState<ScannerStatusResponse | null>(null);
  const [scan, setScan] =
    React.useState<ScanAllMarketsPayload | null>(null);
  const [quotes, setQuotes] = React.useState<MarketQuote[]>([]);
  const [analysis, setAnalysis] =
    React.useState<AllMarketAnalysisResponse | null>(null);

  const [loading, setLoading] = React.useState(true);
  const [refreshing, setRefreshing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const mountedRef = React.useRef(true);

  React.useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const loadMarkets = React.useCallback(
    async (isRefresh = false) => {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError(null);

      // Fast non-blocking live quotes
      getMarketQuotes()
        .then(res => {
          if (mountedRef.current && Array.isArray(res?.quotes)) {
            setQuotes(res.quotes);
          }
        })
        .catch(() => {});


      try {
               const [
          marketsResult,
          scannerResult,
          scanResult,
          analysisResult,
        ] = await Promise.allSettled([
          getMarkets(),
          getScannerStatus(),
          scanAllMarkets(),
          getMarketAnalysis('technical'),
        ]);

        if (!mountedRef.current) {
          return;
        }

        // 1. Markets list
        let resolvedMarkets: Market[] = [];
        if (marketsResult.status === 'fulfilled') {
          const backendMarkets = Array.isArray(marketsResult.value.markets)
            ? marketsResult.value.markets
            : [];

          resolvedMarkets = backendMarkets
            .map(symbol => String(symbol).toUpperCase() as MarketSymbol)
            .filter(symbol => SUPPORTED_MARKETS.includes(symbol))
            .map(symbol => ({
              symbol,
              name: MARKET_META[symbol]?.name || symbol,
              category: MARKET_META[symbol]?.category || 'FOREX',
            }));
        } else {
          resolvedMarkets = SUPPORTED_MARKETS.map(symbol => ({
            symbol,
            name: MARKET_META[symbol].name,
            category: MARKET_META[symbol].category,
          }));
        }
        setMarkets(resolvedMarkets);

        // 2. Scanner status
        if (scannerResult.status === 'fulfilled') {
          setScanner(scannerResult.value);
        }

        // 3. Scan payload (candles)
        if (scanResult.status === 'fulfilled') {
          setScan(scanResult.value);
        }

        // 4. Analysis
        if (analysisResult.status === 'fulfilled') {
          setAnalysis(analysisResult.value);
        }
      } catch (requestError) {
        if (!mountedRef.current) {
          return;
        }

        const message =
          requestError instanceof Error
            ? requestError.message
            : 'Unable to load market data from BALLY FLOW API.';

        setError(message);
      } finally {
        if (mountedRef.current) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    },
    [],
  );

  React.useEffect(() => {
    loadMarkets(false);
  }, [loadMarkets]);

  const handleRefresh = React.useCallback(() => {
    loadMarkets(true);
  }, [loadMarkets]);

  const scannerReady =
    String(scanner?.status ?? '').toUpperCase() === 'READY';

  const marketCount =
    scan?.scan?.market_count ??
    scanner?.market_count ??
    markets.length;

  const expectedMarketCount =
    scan?.scan?.expected_market_count ??
    scanner?.market_count ??
    markets.length;

  const readyMarketCount =
    scan?.scan?.ready_market_count ?? 0;

  const partialMarketCount =
    scan?.scan?.partial_market_count ?? 0;

  const failedMarketCount =
    scan?.scan?.failed_market_count ?? 0;

  const readyTimeframeCount =
    scan?.scan?.ready_timeframe_count ?? 0;

  const requiredTimeframeCount =
    scan?.scan?.required_timeframe_count ??
    scanner?.expected_stream_count ??
    expectedMarketCount *
      (scanner?.timeframe_count ?? ANALYSIS_TIMEFRAMES.length);

  const marketDataReady =
    scan?.scan?.data_ready === true;

  const analysisMarkets =
  analysis?.analysis &&
  typeof analysis.analysis === 'object'
    ? Object.values(analysis.analysis)
    : [];

const analyzedMarketCount =
  analysisMarkets.filter(item => {
    const analysisItem =
      item as MarketAnalysisItem;

    return (
      analysisItem.analysis_ready === true ||
      getAnalysisDecision(analysisItem) !== null
    );
  }).length;

const decisionMarketCount =
  analysisMarkets.filter(item =>
    getAnalysisDecision(
      item as MarketAnalysisItem,
    ) !== null,
  ).length;

const analysisReady =
  analyzedMarketCount > 0;

const tradingDecisionReady =
  decisionMarketCount > 0;

const executionReady =
  scanner?.execution === true;

  const handleMarketPress = (symbol: MarketSymbol) => {
    console.log(
      `[BALLY FLOW] Selected market: ${symbol}`,
    );
  };

  return (
    <View style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
          />
        }
      >
        <View style={styles.header}>
          <Text allowFontScaling={false} style={styles.title}>Markets</Text>
          <Text allowFontScaling={false} style={styles.subtitle}>
            Authoritative BALLY FLOW market data
          </Text>
        </View>

        {error ? (
          <View style={styles.errorCard}>
            <Text allowFontScaling={false} style={styles.errorTitle}>
              Market data unavailable
            </Text>
            <Text allowFontScaling={false} style={styles.errorText}>
              {error}
            </Text>

            <TouchableOpacity
              style={styles.retryButton}
              onPress={() => loadMarkets(false)}
            >
              <Text allowFontScaling={false} style={styles.retryText}>
                Retry
              </Text>
            </TouchableOpacity>
          </View>
        ) : null}

        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <View>
              <Text allowFontScaling={false} style={styles.cardTitle}>
                Market Universe
              </Text>
              <Text allowFontScaling={false} style={styles.cardSubtitle}>
                Backend-defined markets
              </Text>
            </View>

            {loading ? (
              <ActivityIndicator size="small" />
            ) : (
              <View style={styles.universeBadge}>
                <Text allowFontScaling={false} style={styles.universeBadgeText}>
                  {marketCount}/{expectedMarketCount}
                </Text>
              </View>
            )}
          </View>

          <View style={styles.universeStats}>
            <View style={styles.statBox}>
              <Text allowFontScaling={false} style={styles.statValue}>
                {marketCount}
              </Text>
              <Text allowFontScaling={false} style={styles.statLabel}>
                Markets
              </Text>
            </View>

            <View style={styles.statBox}>
              <Text allowFontScaling={false} style={styles.statValue}>
                {scanner?.timeframe_count ?? ANALYSIS_TIMEFRAMES.length}
              </Text>
              <Text allowFontScaling={false} style={styles.statLabel}>
                Timeframes
              </Text>
            </View>

            <View style={styles.statBox}>
              <Text allowFontScaling={false} style={styles.statValue}>
                {scanner?.expected_stream_count ??
                  requiredTimeframeCount}
              </Text>
              <Text allowFontScaling={false} style={styles.statLabel}>
                Streams
              </Text>
            </View>
          </View>
        </View>

        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <View>
              <Text allowFontScaling={false} style={styles.cardTitle}>
                Market Data Readiness
              </Text>
              <Text allowFontScaling={false} style={styles.cardSubtitle}>
                H4 ? H1 ? M15
              </Text>
            </View>

            <View
              style={[
                styles.readinessBadge,
                marketDataReady
                  ? styles.readinessBadgeReady
                  : styles.readinessBadgeWaiting,
              ]}
            >
              <Text allowFontScaling={false} style={styles.readinessBadgeText}>
                {marketDataReady
                  ? 'READY'
                  : 'NOT READY'}
              </Text>
            </View>
          </View>

          <View style={styles.readinessRow}>
            <Text allowFontScaling={false} style={styles.readinessLabel}>
              Scanner
            </Text>
            <Text allowFontScaling={false} style={styles.readinessValue}>
              {scannerReady ? 'READY' : 'NOT READY'}
            </Text>
          </View>

          <View style={styles.readinessRow}>
            <Text allowFontScaling={false} style={styles.readinessLabel}>
              Markets
            </Text>
            <Text allowFontScaling={false} style={styles.readinessValue}>
              {readyMarketCount}/{expectedMarketCount}
            </Text>
          </View>

          <View style={styles.readinessRow}>
            <Text allowFontScaling={false} style={styles.readinessLabel}>
              Timeframe streams
            </Text>
            <Text allowFontScaling={false} style={styles.readinessValue}>
              {readyTimeframeCount}/{requiredTimeframeCount}
            </Text>
          </View>

          <View style={styles.readinessRow}>
            <Text allowFontScaling={false} style={styles.readinessLabel}>
              Partial
            </Text>
            <Text allowFontScaling={false} style={styles.readinessValue}>
              {partialMarketCount}
            </Text>
          </View>

          <View style={styles.readinessRow}>
            <Text allowFontScaling={false} style={styles.readinessLabel}>
              Failed
            </Text>
            <Text allowFontScaling={false} style={styles.readinessValue}>
              {failedMarketCount}
            </Text>
          </View>

          <View style={styles.divider} />

          <View style={styles.readinessRow}>
            <Text allowFontScaling={false} style={styles.readinessLabel}>
              Technical analysis
            </Text>
            <Text allowFontScaling={false} style={styles.readinessValue}>
              {analysisReady ? 'READY' : 'NOT READY'}
            </Text>
          </View>

          <View style={styles.readinessRow}>
            <Text allowFontScaling={false} style={styles.readinessLabel}>
              Trading decision
            </Text>
            <Text allowFontScaling={false} style={styles.readinessValue}>
              {tradingDecisionReady
                ? 'READY'
                : 'NOT READY'}
            </Text>
          </View>

          <View style={styles.readinessRow}>
            <Text allowFontScaling={false} style={styles.readinessLabel}>
              Execution
            </Text>
            <Text allowFontScaling={false} style={styles.readinessValue}>
              {executionReady
                ? 'READY'
                : 'NOT READY'}
            </Text>
          </View>
        </View>

        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <View>
              <Text allowFontScaling={false} style={styles.cardTitle}>
                Tracked Markets
              </Text>
              <Text allowFontScaling={false} style={styles.cardSubtitle}>
                Live backend market-data state
              </Text>
            </View>
          </View>

          {loading && markets.length === 0 ? (
            <View style={styles.loadingBox}>
              <ActivityIndicator />
              <Text allowFontScaling={false} style={styles.loadingText}>
                Loading markets...
              </Text>
            </View>
          ) : markets.length === 0 ? (
            <View style={styles.loadingBox}>
              <Text allowFontScaling={false} style={styles.loadingText}>
                No markets returned by backend.
              </Text>
            </View>
          ) : (
            markets.map(market => {
              const status = getMarketStatus(
                scan,
                market.symbol,
              );

             const marketAnalysis =
  getAnalysisMarket(
    analysis,
    market.symbol,
  );

const decision =
  getAnalysisDecision(marketAnalysis);

const confidence =
  getAnalysisConfidence(marketAnalysis);

const direction =
  getAnalysisDirection(marketAnalysis);
const quote = getQuoteFor(quotes, market.symbol);

              return (
                <TouchableOpacity
                  key={market.symbol}
                  style={styles.marketRow}
                  onPress={() =>
                    handleMarketPress(market.symbol)
                  }
                  activeOpacity={0.75}
                >
                  <View style={styles.marketIdentity}>
                    <Text allowFontScaling={false} style={styles.marketSymbol}>
                      {market.symbol}
                    </Text>
                    <Text allowFontScaling={false} style={styles.marketName}>
                      {market.name}
                    </Text>
                    <Text allowFontScaling={false} style={styles.marketCategory}>
                      {market.category}
                    </Text>
                  </View>

                  <View style={styles.marketRight}>
  <StatusPill status={status} />

  <View style={styles.analysisSummary}>
    <Text allowFontScaling={false} style={styles.analysisDecision}>
      {decision ?? (quote?.price ? String(quote.price) : 'ANALYZING')}
    </Text>

    <Text allowFontScaling={false} style={styles.analysisDetail}>
      {direction ?? '—'}
      {'  '}
      {confidence !== null
        ? `${confidence.toFixed(1)}%`
        : '—'}
    </Text>
  </View>

  <View style={styles.timeframes}>
                      {ANALYSIS_TIMEFRAMES.map(
                        timeframe => (
                          <TimeframeStatus
                            key={timeframe}
                            timeframe={timeframe}
                            ready={isTimeframeReady(
                              scan,
                              market.symbol,
                              timeframe,
                            )}
                          />
                        ),
                      )}
                    </View>
                  </View>
                </TouchableOpacity>
              );
            })
          )}
        </View>

        <View style={styles.noteCard}>
          <Text allowFontScaling={false} style={styles.noteTitle}>
            Top-down analysis
          </Text>
          <Text allowFontScaling={false} style={styles.noteText}>
            BALLY FLOW receives market data from the
            backend in the authoritative order H4 ?
            H1 ? M15. Trading intelligence remains
            on the backend.
          </Text>
        </View>

        <View style={styles.dataStatus}>
          <View
            style={[
              styles.dataStatusDot,
              marketDataReady
                ? styles.dataStatusDotReady
                : styles.dataStatusDotWaiting,
            ]}
          />

          <Text allowFontScaling={false} style={styles.dataStatusText}>
            {marketDataReady
              ? 'Backend market data synchronized'
              : 'Waiting for backend market data'}
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0B111D',
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  header: {
    marginBottom: 18,
  },
  title: {
    color: '#F8FAFC',
    fontSize: 28,
    fontWeight: '700',
  },
  subtitle: {
    color: '#94A3B8',
    fontSize: 13,
    marginTop: 4,
  },
  card: {
    backgroundColor: '#131D31',
    borderWidth: 1,
    borderColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    marginBottom: 14,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  cardTitle: {
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: '700',
  },
  cardSubtitle: {
    color: '#64748B',
    fontSize: 12,
    marginTop: 3,
  },
  universeBadge: {
    borderWidth: 1,
    borderColor: '#1E293B',
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  universeBadgeText: {
    color: '#F8FAFC',
    fontSize: 12,
    fontWeight: '700',
  },
  universeStats: {
    flexDirection: 'row',
    gap: 10,
  },
  statBox: {
    flex: 1,
    backgroundColor: '#0F1421',
    borderRadius: 12,
    padding: 12,
  },
  statValue: {
    color: '#F8FAFC',
    fontSize: 20,
    fontWeight: '700',
  },
  statLabel: {
    color: '#64748B',
    fontSize: 11,
    marginTop: 4,
  },
  readinessBadge: {
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  readinessBadgeReady: {
    backgroundColor: '#10251B',
  },
  readinessBadgeWaiting: {
    backgroundColor: '#211A0E',
  },
  readinessBadgeText: {
    color: '#F8FAFC',
    fontSize: 11,
    fontWeight: '700',
  },
  readinessRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 7,
  },
  readinessLabel: {
    color: '#94A3B8',
    fontSize: 13,
  },
  readinessValue: {
    color: '#F8FAFC',
    fontSize: 13,
    fontWeight: '600',
  },
  divider: {
    height: 1,
    backgroundColor: '#1B2435',
    marginVertical: 8,
  },
  marketRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#131D31',
    borderWidth: 1,
    borderColor: '#1E293B',
    borderRadius: 14,
    paddingVertical: 14,
    paddingHorizontal: 16,
    marginBottom: 10,
  },
  marketIdentity: {
    flex: 1,
  },
  marketSymbol: {
    color: '#F8FAFC',
    fontSize: 15,
    fontWeight: '700',
  },
  marketName: {
    color: '#94A3B8',
    fontSize: 12,
    marginTop: 3,
  },
  marketCategory: {
    color: '#64748B',
    fontSize: 10,
    marginTop: 3,
  },
  marketRight: {
    alignItems: 'flex-end',
  },
  analysisSummary: {
    alignItems: 'flex-end',
    marginBottom: 8,
  },
  analysisDecision: {
    color: '#F8FAFC',
    fontSize: 12,
    fontWeight: '700',
  },
  analysisDetail: {
    color: '#10B981',
    fontSize: 10,
    marginTop: 2,
  },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#1E293B',
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 5,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#38BDF8',
    marginRight: 5,
  },
  statusText: {
    color: '#10B981',
    fontSize: 9,
    fontWeight: '700',
  },

  timeframes: {
    flexDirection: 'row',
    marginTop: 8,
    gap: 7,
  },
  timeframeItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  timeframeDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#56627A',
    marginRight: 3,
  },
  timeframeDotReady: {
    backgroundColor: '#7083FF',
  },
  timeframeText: {
    color: '#041841',
    fontSize: 9,
  },
  noteCard: {
    backgroundColor: '#020b22',
    borderWidth: 1,
    borderColor: '#02201d',
    borderRadius: 16,
    padding: 16,
    marginBottom: 14,
  },
  noteTitle: {
    color: '#063126b5',
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 6,
  },
  noteText: {
    color: '#94A3B8',
    fontSize: 12,
    lineHeight: 18,
  },
  dataStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
  },
  dataStatusDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    marginRight: 7,
  },
  dataStatusDotReady: {
    backgroundColor: '#7083FF',
  },
  dataStatusDotWaiting: {
    backgroundColor: '#56627A',
  },
  dataStatusText: {
    color: '#64748B',
    fontSize: 11,
  },
  errorCard: {
    backgroundColor: '#1E1420',
    borderWidth: 1,
    borderColor: '#EF4444',
    borderRadius: 16,
    padding: 16,
    marginBottom: 14,
  },
  errorTitle: {
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: '700',
  },
  errorText: {
    color: '#FCA5A5',
    fontSize: 12,
    lineHeight: 18,
    marginTop: 5,
  },
  retryButton: {
    alignSelf: 'flex-start',
    marginTop: 12,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 9,
    backgroundColor: '#1E293B',
    borderWidth: 1,
    borderColor: '#334155',
  },
  retryText: {
    color: '#F8FAFC',
    fontSize: 12,
    fontWeight: '700',
  },
  loadingBox: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  loadingText: {
    color: '#64748B',
    fontSize: 12,
    marginTop: 8,
  },
});
