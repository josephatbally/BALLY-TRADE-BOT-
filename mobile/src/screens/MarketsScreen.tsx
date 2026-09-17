import React, { useState, useEffect, useCallback } from 'react';
import PairLogo from '../components/broker/PairLogo';
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  getMarketQuotes,
  getScannerStatus,
  MarketQuote,
  MarketSymbol,
  ScannerStatusResponse,
} from '../api/marketsApi';

type CategoryFilter = 'ALL' | 'METALS' | 'FOREX' | 'INDEX' | 'HOT';

interface MarketDef {
  symbol: MarketSymbol;
  name: string;
  category: 'METALS' | 'FOREX' | 'INDEX';
  spreadPts: string;
  h4Bias: string;
  h1Bias: string;
  m15Bias: string;
  confluencePct: number;
}

const MARKETS: MarketDef[] = [
  {
    symbol: 'XAUUSD',
    name: 'Gold / US Dollar',
    category: 'METALS',
    spreadPts: '1.8 pts',
    h4Bias: 'BULLISH BOS',
    h1Bias: 'OB RETEST',
    m15Bias: 'FVG REBALANCE',
    confluencePct: 88,
  },
  {
    symbol: 'EURUSD',
    name: 'Euro / US Dollar',
    category: 'FOREX',
    spreadPts: '0.6 pips',
    h4Bias: 'BEARISH CONT',
    h1Bias: 'CHoCH PIVOT',
    m15Bias: 'SWEEP RETEST',
    confluencePct: 54,
  },
  {
    symbol: 'GBPUSD',
    name: 'British Pound / US Dollar',
    category: 'FOREX',
    spreadPts: '0.8 pips',
    h4Bias: 'EXPANSION',
    h1Bias: 'LIQUIDITY RUN',
    m15Bias: 'BOS CONFIRMED',
    confluencePct: 76,
  },
  {
    symbol: 'USDJPY',
    name: 'US Dollar / Yen',
    category: 'FOREX',
    spreadPts: '0.9 pips',
    h4Bias: 'BULLISH ACCUM',
    h1Bias: 'ORDER BLOCK',
    m15Bias: 'RANGE EXPAND',
    confluencePct: 62,
  },
  {
    symbol: 'XAGUSD',
    name: 'Silver / US Dollar',
    category: 'METALS',
    spreadPts: '2.1 pts',
    h4Bias: 'BULLISH SWEEP',
    h1Bias: 'VALUE RE-ENTRY',
    m15Bias: 'DEMAND TEST',
    confluencePct: 82,
  },
  {
    symbol: 'NASDAQ',
    name: 'US Tech 100 Index',
    category: 'INDEX',
    spreadPts: '1.2 pts',
    h4Bias: 'BULLISH EXP',
    h1Bias: 'BOS BREAKOUT',
    m15Bias: 'PREMIUM FILL',
    confluencePct: 84,
  },
];

export default function MarketsScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const [activeFilter, setActiveFilter] = useState<CategoryFilter>('ALL');
  const [quotes, setQuotes] = useState<Record<string, MarketQuote>>({});
  const [scannerStatus, setScannerStatus] = useState<ScannerStatusResponse | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [quotesRes, scanRes] = await Promise.allSettled([
        getMarketQuotes(),
        getScannerStatus(),
      ]);

      if (quotesRes.status === 'fulfilled' && quotesRes.value?.quotes) {
        const map: Record<string, MarketQuote> = {};
        for (const q of quotesRes.value.quotes) {
          map[q.symbol] = q;
        }
        setQuotes(map);
      }

      if (scanRes.status === 'fulfilled' && scanRes.value) {
        setScannerStatus(scanRes.value);
      }
    } catch {
      // Retain existing telemetry
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3500);
    return () => clearInterval(interval);
  }, [fetchData]);

  const filteredMarkets = MARKETS.filter((m) => {
    if (activeFilter === 'ALL') return true;
    if (activeFilter === 'HOT') return m.confluencePct >= 80;
    return m.category === activeFilter;
  });

  const highConfluenceCount = MARKETS.filter((m) => m.confluencePct >= 80).length;

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      {/* Futuristic ambient background glows */}
      <View style={styles.glowTop} />
      <View style={styles.glowBottom} />

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[
          styles.content,
          {
            paddingTop: Math.max(insets.top + 8, 20),
            paddingBottom: Math.max(insets.bottom + 24, 40),
          },
        ]}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              fetchData();
            }}
            tintColor="#7083FF"
          />
        }
      >
        {/* HEADER */}
        <View style={styles.header}>
          <View style={styles.headerText}>
            <Text allowFontScaling={false} style={styles.eyebrow}>BALLY FLOW</Text>
            <Text allowFontScaling={false} style={styles.title}>Market Radar</Text>
            <Text allowFontScaling={false} style={styles.subtitle}>
              Autonomous scanner & multi-asset structural sweep
            </Text>
          </View>

          <View style={styles.liveBadge}>
            <View style={styles.livePulse} />
            <Text allowFontScaling={false} style={styles.liveBadgeText}>06/06 LIVE</Text>
          </View>
        </View>

        {/* SCANNER TELEMETRY HUD */}
        <View style={styles.hudCard}>
          <View style={styles.hudHeader}>
            <View style={styles.hudTitleRow}>
              <View style={styles.hudDot} />
              <Text allowFontScaling={false} style={styles.hudTitle}>AUTONOMOUS SCANNER ENGINE</Text>
            </View>
            <View style={styles.hudStateBadge}>
              <Text allowFontScaling={false} style={styles.hudStateText}>
                {scannerStatus?.status || 'ACTIVE SCAN'}
              </Text>
            </View>
          </View>

          <View style={styles.hudMetricsRow}>
            <View style={styles.hudMetric}>
              <Text allowFontScaling={false} style={styles.hudMetricLabel}>COVERAGE</Text>
              <Text allowFontScaling={false} style={styles.hudMetricValue}>6 PAIRS</Text>
            </View>
            <View style={styles.hudDivider} />
            <View style={styles.hudMetric}>
              <Text allowFontScaling={false} style={styles.hudMetricLabel}>HIGH CONVICTION</Text>
              <Text allowFontScaling={false} style={[styles.hudMetricValue, { color: '#35E68A' }]}>
                {highConfluenceCount} SETUPS
              </Text>
            </View>
            <View style={styles.hudDivider} />
            <View style={styles.hudMetric}>
              <Text allowFontScaling={false} style={styles.hudMetricLabel}>ATR VELOCITY</Text>
              <Text allowFontScaling={false} style={[styles.hudMetricValue, { color: '#7083FF' }]}>
                EXPANDING
              </Text>
            </View>
          </View>
        </View>

        {/* CATEGORY FILTER PILLS */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filterBar}
        >
          {(['ALL', 'METALS', 'FOREX', 'INDEX', 'HOT'] as CategoryFilter[]).map((filter) => {
            const active = activeFilter === filter;
            return (
              <Pressable
                key={filter}
                onPress={() => setActiveFilter(filter)}
                style={[styles.filterPill, active && styles.filterPillActive]}
              >
                <Text
                  allowFontScaling={false}
                  style={[styles.filterPillText, active && styles.filterPillTextActive]}
                >
                  {filter === 'HOT' ? 'âš¡ HOT SETUPS' : filter}
                </Text>
              </Pressable>
            );
          })}
        </ScrollView>

        {/* RADAR ASSET CARDS */}
        {loading && !refreshing ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color="#7083FF" />
            <Text allowFontScaling={false} style={styles.loadingText}>Syncing Market Telemetry...</Text>
          </View>
        ) : (
          filteredMarkets.map((market) => {
            const quote = quotes[market.symbol];
            const changeVal = Number(quote?.change_pct ?? (quote as any)?.raw_change ?? 0);
            const isPositive = changeVal >= 0;
            const isHighConviction = market.confluencePct >= 80;

            return (
              <View key={market.symbol} style={styles.marketCard}>
                {/* CARD TOP ROW: Symbol, Category, Live Price & Change */}
                <View style={styles.cardHeader}>
                  <View>
                    <View style={styles.symbolBadgeRow}>
                      <PairLogo symbol={market.symbol} size={30} style={{ marginRight: 8 }} />
                      <Text allowFontScaling={false} style={styles.cardSymbol}>
                        {market.symbol}
                      </Text>
                      <View style={styles.categoryBadge}>
                        <Text allowFontScaling={false} style={styles.categoryBadgeText}>
                          {market.category}
                        </Text>
                      </View>
                    </View>
                    <Text allowFontScaling={false} style={styles.cardName}>
                      {market.name}
                    </Text>
                  </View>

                  <View style={styles.cardPriceColumn}>
                    <Text allowFontScaling={false} style={styles.cardPrice}>
                      {quote?.price || (market.symbol === 'XAUUSD' ? '2,654.80' : market.symbol === 'NASDAQ' ? '19,480.50' : '1.0842')}
                    </Text>
                    <View style={styles.changeRow}>
                      <View
                        style={[
                          styles.changeDot,
                          { backgroundColor: isPositive ? '#35E68A' : '#EF4444' },
                        ]}
                      />
                      <Text
                        allowFontScaling={false}
                        style={[
                          styles.changeText,
                          { color: isPositive ? '#35E68A' : '#EF4444' },
                        ]}
                      >
                        {`${isPositive ? '+' : ''}${changeVal.toFixed(2)}%`}
                      </Text>
                    </View>
                  </View>
                </View>

                {/* SPREAD & LIQUIDITY TELEMETRY */}
                <View style={styles.telemetryStrip}>
                  <Text allowFontScaling={false} style={styles.telemetryText}>
                    SPREAD: <Text style={styles.telemetryHighlight}>{market.spreadPts}</Text>
                  </Text>
                  <View style={styles.telemetryDot} />
                  <Text allowFontScaling={false} style={styles.telemetryText}>
                    LIQUIDITY: <Text style={styles.telemetryHighlight}>HIGH DENSITY</Text>
                  </Text>
                  <View style={styles.telemetryDot} />
                  <Text allowFontScaling={false} style={styles.telemetryText}>
                    TICK SYNC: <Text style={styles.telemetryHighlight}>REAL-TIME</Text>
                  </Text>
                </View>

                {/* TIMEFRAME STRUCTURAL MATRIX */}
                <View style={styles.matrixContainer}>
                  <View style={styles.matrixCol}>
                    <Text allowFontScaling={false} style={styles.matrixLabel}>H4 TREND</Text>
                    <View style={styles.matrixPill}>
                      <Text allowFontScaling={false} style={styles.matrixValue}>{market.h4Bias}</Text>
                    </View>
                  </View>

                  <View style={styles.matrixCol}>
                    <Text allowFontScaling={false} style={styles.matrixLabel}>H1 STRUCTURE</Text>
                    <View style={styles.matrixPill}>
                      <Text allowFontScaling={false} style={styles.matrixValue}>{market.h1Bias}</Text>
                    </View>
                  </View>

                  <View style={styles.matrixCol}>
                    <Text allowFontScaling={false} style={styles.matrixLabel}>M15 ENTRY</Text>
                    <View style={styles.matrixPill}>
                      <Text allowFontScaling={false} style={styles.matrixValue}>{market.m15Bias}</Text>
                    </View>
                  </View>
                </View>

                {/* PREDICTIVE CONVICTION BAR */}
                <View style={styles.convictionRow}>
                  <View style={styles.convictionLeft}>
                    <Text allowFontScaling={false} style={styles.convictionLabel}>
                      ENGINE CONVICTION
                    </Text>
                    <Text
                      allowFontScaling={false}
                      style={[
                        styles.convictionScore,
                        { color: isHighConviction ? '#35E68A' : '#7083FF' },
                      ]}
                    >
                      {market.confluencePct}% {isHighConviction ? '· HIGH CONFIRMATION' : '· NEUTRAL'}
                    </Text>
                  </View>

                  <View style={styles.convictionTrack}>
                    <View
                      style={[
                        styles.convictionFill,
                        {
                          width: `${market.confluencePct}%`,
                          backgroundColor: isHighConviction ? '#35E68A' : '#7083FF',
                        },
                      ]}
                    />
                  </View>
                </View>

                {/* ACTION BUTTONS */}
                <View style={styles.cardActions}>
                  <Pressable
                    onPress={() => navigation.navigate('Trades')}
                    style={({ pressed }) => [styles.actionBtnSecondary, pressed && styles.pressed]}
                  >
                    <Text allowFontScaling={false} style={styles.actionBtnSecondaryText}>
                       EXECUTE
                    </Text>
                  </Pressable>

                  <Pressable
                    onPress={() => navigation.navigate('FlowAnalysis', { symbol: market.symbol })}
                    style={({ pressed }) => [styles.actionBtnPrimary, pressed && styles.pressed]}
                  >
                    <Text allowFontScaling={false} style={styles.actionBtnPrimaryText}>
                      OPEN IN FLOW 
                    </Text>
                  </Pressable>
                </View>
              </View>
            );
          })
        )}
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
    width: 280,
    height: 280,
    borderRadius: 140,
    backgroundColor: '#101B5C',
    opacity: 0.18,
    top: -160,
    right: -90,
  },
  glowBottom: {
    position: 'absolute',
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: '#17204A',
    opacity: 0.16,
    bottom: -140,
    left: -100,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  headerText: {
    flex: 1,
  },
  eyebrow: {
    color: '#7083FF',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 2,
  },
  title: {
    color: '#FFFFFF',
    fontSize: 24,
    fontWeight: '900',
    marginTop: 3,
  },
  subtitle: {
    color: '#77839D',
    fontSize: 10,
    lineHeight: 14,
    marginTop: 4,
  },
  liveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 5,
    marginLeft: 10,
  },
  livePulse: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 5,
  },
  liveBadgeText: {
    color: '#7083FF',
    fontSize: 7.5,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  hudCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 16,
    padding: 14,
    marginBottom: 16,
  },
  hudHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  hudTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  hudDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#7083FF',
    marginRight: 7,
  },
  hudTitle: {
    color: '#FFFFFF',
    fontSize: 8.5,
    fontWeight: '900',
    letterSpacing: 1.2,
  },
  hudStateBadge: {
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 3,
  },
  hudStateText: {
    color: '#35E68A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  hudMetricsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#0D121D',
    borderWidth: 1,
    borderColor: '#1A2333',
    borderRadius: 10,
    paddingVertical: 9,
    paddingHorizontal: 12,
  },
  hudMetric: {
    alignItems: 'center',
    flex: 1,
  },
  hudMetricLabel: {
    color: '#56627A',
    fontSize: 6.5,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  hudMetricValue: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '900',
    marginTop: 3,
  },
  hudDivider: {
    width: 1,
    height: 20,
    backgroundColor: '#1E293B',
  },
  filterBar: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
    paddingVertical: 2,
  },
  filterPill: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1E293B',
    borderRadius: 9,
    paddingHorizontal: 11,
    paddingVertical: 7,
  },
  filterPillActive: {
    backgroundColor: '#10183D',
    borderColor: '#334BFF',
  },
  filterPillText: {
    color: '#68758E',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  filterPillTextActive: {
    color: '#7083FF',
  },
  loadingContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    color: '#68758E',
    fontSize: 10,
    marginTop: 10,
  },
  marketCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 18,
    padding: 15,
    marginBottom: 16,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  symbolBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  cardSymbol: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  categoryBadge: {
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  categoryBadgeText: {
    color: '#7083FF',
    fontSize: 6.5,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  cardName: {
    color: '#68758E',
    fontSize: 9.5,
    marginTop: 3,
  },
  cardPriceColumn: {
    alignItems: 'flex-end',
  },
  cardPrice: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '900',
    fontVariant: ['tabular-nums'],
  },
  changeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 3,
  },
  changeDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    marginRight: 4,
  },
  changeText: {
    fontSize: 10,
    fontWeight: '800',
    fontVariant: ['tabular-nums'],
  },
  telemetryStrip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#070B14',
    borderWidth: 1,
    borderColor: '#121927',
    borderRadius: 8,
    paddingHorizontal: 9,
    paddingVertical: 6,
    marginTop: 12,
    gap: 7,
  },
  telemetryText: {
    color: '#56627A',
    fontSize: 7,
    fontWeight: '800',
    letterSpacing: 0.6,
  },
  telemetryHighlight: {
    color: '#A0ABC0',
    fontWeight: '900',
  },
  telemetryDot: {
    width: 3,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: '#263043',
  },
  matrixContainer: {
    flexDirection: 'row',
    gap: 6,
    marginTop: 11,
  },
  matrixCol: {
    flex: 1,
  },
  matrixLabel: {
    color: '#56627A',
    fontSize: 6.5,
    fontWeight: '900',
    letterSpacing: 0.6,
    marginBottom: 4,
  },
  matrixPill: {
    backgroundColor: '#0D121D',
    borderWidth: 1,
    borderColor: '#1D273A',
    borderRadius: 7,
    paddingVertical: 5,
    paddingHorizontal: 6,
    alignItems: 'center',
  },
  matrixValue: {
    color: '#8A98FF',
    fontSize: 6.5,
    fontWeight: '900',
    letterSpacing: 0.4,
  },
  convictionRow: {
    marginTop: 12,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#121A28',
  },
  convictionLeft: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  convictionLabel: {
    color: '#56627A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  convictionScore: {
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 0.6,
  },
  convictionTrack: {
    height: 4,
    borderRadius: 2,
    backgroundColor: '#121926',
    overflow: 'hidden',
  },
  convictionFill: {
    height: '100%',
    borderRadius: 2,
  },
  cardActions: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 13,
  },
  actionBtnSecondary: {
    flex: 1,
    minHeight: 40,
    backgroundColor: '#0D121D',
    borderWidth: 1,
    borderColor: '#1D273A',
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionBtnSecondaryText: {
    color: '#8A98FF',
    fontSize: 8.5,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  actionBtnPrimary: {
    flex: 1.4,
    minHeight: 40,
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#334BFF',
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionBtnPrimaryText: {
    color: '#FFFFFF',
    fontSize: 8.5,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  pressed: {
    opacity: 0.75,
    transform: [{ scale: 0.99 }],
  },
});
