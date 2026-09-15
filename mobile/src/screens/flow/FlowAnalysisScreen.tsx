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
import {useSafeAreaInsets} from 'react-native-safe-area-context';
import {getMarketQuotes, MarketQuote} from '../../api/marketsApi';

type Timeframe = 'H4' | 'H1' | 'M15';

type Candle = {
  open: number;
  close: number;
  high: number;
  low: number;
  rawHigh?: number;
  rawLow?: number;
};

const TIMEFRAMES: Timeframe[] = ['H4', 'H1', 'M15'];

const DEFAULT_CANDLE_DATA: Record<Timeframe, Candle[]> = {
  H4: [
    {open: 62, close: 70, high: 76, low: 54},
    {open: 71, close: 65, high: 78, low: 60},
    {open: 66, close: 74, high: 80, low: 62},
    {open: 75, close: 82, high: 88, low: 70},
    {open: 83, close: 78, high: 90, low: 73},
    {open: 77, close: 86, high: 92, low: 75},
    {open: 87, close: 81, high: 94, low: 77},
    {open: 82, close: 89, high: 96, low: 79},
    {open: 90, close: 84, high: 95, low: 80},
    {open: 85, close: 92, high: 98, low: 82},
    {open: 91, close: 87, high: 97, low: 84},
    {open: 88, close: 94, high: 100, low: 86},
  ],
  H1: [
    {open: 58, close: 67, high: 73, low: 52},
    {open: 68, close: 63, high: 75, low: 58},
    {open: 64, close: 72, high: 78, low: 61},
    {open: 73, close: 79, high: 84, low: 69},
    {open: 80, close: 75, high: 86, low: 71},
    {open: 76, close: 84, high: 89, low: 73},
    {open: 85, close: 80, high: 91, low: 76},
    {open: 81, close: 88, high: 94, low: 78},
    {open: 89, close: 85, high: 93, low: 81},
    {open: 86, close: 92, high: 97, low: 83},
    {open: 93, close: 89, high: 98, low: 86},
    {open: 90, close: 96, high: 100, low: 88},
  ],
  M15: [
    {open: 51, close: 58, high: 63, low: 48},
    {open: 59, close: 54, high: 65, low: 51},
    {open: 55, close: 62, high: 67, low: 53},
    {open: 63, close: 69, high: 74, low: 59},
    {open: 70, close: 66, high: 76, low: 63},
    {open: 67, close: 75, high: 80, low: 65},
    {open: 76, close: 71, high: 82, low: 68},
    {open: 72, close: 81, high: 85, low: 69},
    {open: 82, close: 77, high: 87, low: 73},
    {open: 78, close: 86, high: 91, low: 75},
    {open: 87, close: 83, high: 93, low: 80},
    {open: 84, close: 91, high: 96, low: 81},
  ],
};

function normalizeClosesToCandles(closes: number[]): Candle[] {
  if (!closes || closes.length < 2) return DEFAULT_CANDLE_DATA.M15;
  const minVal = Math.min(...closes);
  const maxVal = Math.max(...closes);
  const range = maxVal - minVal || 1;

  const result: Candle[] = [];
  for (let i = 0; i < closes.length; i++) {
    const prev = i > 0 ? closes[i - 1] : closes[i];
    const curr = closes[i];
    const openPct = ((prev - minVal) / range) * 80 + 10;
    const closePct = ((curr - minVal) / range) * 80 + 10;
    const highPct = Math.min(100, Math.max(openPct, closePct) + 5);
    const lowPct = Math.max(0, Math.min(openPct, closePct) - 5);

    result.push({
      open: Math.round(openPct),
      close: Math.round(closePct),
      high: Math.round(highPct),
      low: Math.round(lowPct),
      rawHigh: maxVal,
      rawLow: minVal,
    });
  }
  return result;
}

export default function FlowAnalysisScreen({navigation, route}: any) {
  const insets = useSafeAreaInsets();
  const symbol = route?.params?.symbol || 'XAUUSD';

  const [timeframe, setTimeframe] = useState<Timeframe>('H4');
  const [quote, setQuote] = useState<MarketQuote | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchQuote = useCallback(async () => {
    try {
      const res = await getMarketQuotes();
      if (res && res.quotes) {
        const found = res.quotes.find(
          q => q.symbol.toUpperCase() === symbol.toUpperCase()
        );
        if (found) {
          setQuote(found);
        }
      }
    } catch {
      // Keep existing state on transient network blips
    }
  }, [symbol]);

  useEffect(() => {
    fetchQuote();
    const interval = setInterval(fetchQuote, 5000);
    return () => clearInterval(interval);
  }, [fetchQuote]);

    const candles = useMemo(() => {
    if (quote && quote.points && quote.points.length >= 4) {
      return normalizeClosesToCandles(quote.points);
    }
    return DEFAULT_CANDLE_DATA[timeframe];
  }, [quote, timeframe]);


  const highLabel = quote ? `${quote.price}` : 'HIGH';
  const lowLabel = quote ? `${(quote.raw_price * 0.998).toFixed(2)}` : 'LOW';

  const handleConfluence = () => {
    navigation.navigate('FlowConfluence', {
      symbol,
    });
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
            paddingTop: Math.max(insets.top, 18),
            paddingBottom: Math.max(insets.bottom, 110),
          },
        ]}
      >
        {/* HEADER */}
        <View style={styles.header}>
          <Pressable
            onPress={() => navigation.goBack()}
            style={({pressed}) => [
              styles.backButton,
              pressed && styles.pressed,
            ]}
          >
            <Text style={styles.backIcon} allowFontScaling={false}>‹</Text>
          </Pressable>

          <View style={styles.headerText}>
            <Text style={styles.eyebrow} allowFontScaling={false}>BALLY FLOW</Text>
            <Text style={styles.title} allowFontScaling={false}>Market Analysis</Text>
            <Text style={styles.subtitle} allowFontScaling={false}>H4 → H1 → M15 top-down analysis</Text>
          </View>

          <View style={styles.stageBadge}>
            <Text style={styles.stageNumber} allowFontScaling={false}>02</Text>
            <Text style={styles.stageLabel} allowFontScaling={false}>ANALYSIS</Text>
          </View>
        </View>

        {/* MARKET */}
        <View style={styles.marketCard}>
          <View style={styles.marketTopRow}>
            <Text style={styles.marketLabel} allowFontScaling={false}>ANALYSIS MARKET</Text>
            <View style={styles.marketStatus}>
              <View style={styles.statusDot} />
              <Text style={styles.statusText} allowFontScaling={false}>SELECTED</Text>
            </View>
          </View>

          <View style={styles.marketMainRow}>
            <View>
              <Text style={styles.symbol} allowFontScaling={false}>{symbol}</Text>
              <Text style={styles.marketName} allowFontScaling={false}>
                {quote ? `Live Price: ${quote.price}` : 'Loading market quote...'}
              </Text>
            </View>

            <View style={styles.topDownBadge}>
              <Text style={styles.topDownText} allowFontScaling={false}>TOP-DOWN</Text>
            </View>
          </View>
        </View>

        {/* TIMEFRAME SELECTOR */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle} allowFontScaling={false}>TIMEFRAME ANALYSIS</Text>
            <Text style={styles.sectionSubtitle} allowFontScaling={false}>
              Analyze structure from higher to lower timeframe
            </Text>
          </View>
        </View>

        <View style={styles.timeframeSelector}>
          {TIMEFRAMES.map(frame => {
            const active = timeframe === frame;

            return (
              <Pressable
                key={frame}
                onPress={() => setTimeframe(frame)}
                style={({pressed}) => [
                  styles.timeframeButton,
                  active && styles.timeframeButtonActive,
                  pressed && styles.pressed,
                ]}
              >
                <Text
                  allowFontScaling={false}
                  style={[
                    styles.timeframeText,
                    active && styles.timeframeTextActive,
                  ]}
                >
                  {frame}
                </Text>
              </Pressable>
            );
          })}
        </View>

        {/* CHART */}
        <View style={styles.chartCard}>
          <View style={styles.chartHeader}>
            <View>
              <Text style={styles.chartSymbol} allowFontScaling={false}>{symbol}</Text>
              <Text style={styles.chartTimeframe} allowFontScaling={false}>{timeframe} CANDLESTICKS</Text>
            </View>

            <View style={styles.chartLiveBadge}>
              <View style={styles.chartLiveDot} />
              <Text style={styles.chartLiveText} allowFontScaling={false}>MARKET DATA</Text>
            </View>
          </View>

          <View style={styles.chart}>
            <View style={styles.gridLineOne} />
            <View style={styles.gridLineTwo} />
            <View style={styles.gridLineThree} />
            <View style={styles.gridLineFour} />

            <View style={styles.candleContainer}>
              {candles.map((candle, index) => {
                const bullish = candle.close >= candle.open;
                const bodyTop = 100 - Math.max(candle.open, candle.close);
                const bodyHeight = Math.max(
                  Math.abs(candle.close - candle.open),
                  5,
                );
                const wickTop = 100 - candle.high;
                const wickHeight = Math.max(candle.high - candle.low, 10);

                return (
                  <View
                    key={`${timeframe}-${index}`}
                    style={styles.candleColumn}
                  >
                    <View
                      style={[
                        styles.wick,
                        {
                          top: `${wickTop}%`,
                          height: `${wickHeight}%`,
                        },
                      ]}
                    />

                    <View
                      style={[
                        styles.candleBody,
                        bullish
                          ? styles.bullishCandle
                          : styles.bearishCandle,
                        {
                          top: `${bodyTop}%`,
                          height: `${bodyHeight}%`,
                        },
                      ]}
                    />
                  </View>
                );
              })}
            </View>

            <View style={styles.priceLabelTop}>
              <Text style={styles.priceLabelText} allowFontScaling={false}>{highLabel}</Text>
            </View>

            <View style={styles.priceLabelBottom}>
              <Text style={styles.priceLabelText} allowFontScaling={false}>{lowLabel}</Text>
            </View>
          </View>

          <View style={styles.chartFooter}>
            <Text style={styles.chartFooterText} allowFontScaling={false}>OHLC</Text>
            <Text style={styles.chartFooterText} allowFontScaling={false}>{timeframe}</Text>
            <Text style={styles.chartFooterText} allowFontScaling={false}>{candles.length} BARS</Text>
          </View>
        </View>

        {/* ANALYSIS COMPONENTS */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle} allowFontScaling={false}>ANALYSIS COMPONENTS</Text>
            <Text style={styles.sectionSubtitle} allowFontScaling={false}>Intelligence prepared for Confluence</Text>
          </View>
        </View>

        <View style={styles.analysisList}>
                    <AnalysisRow
            title="Market Structure"
            description="Higher-timeframe directional structure"
            status={quote?.direction || 'NEUTRAL'}
          />

          <AnalysisRow
            title="Price Action"
            description="Candle behavior and structural movement"
            status="CONFIRMED"
          />

          <AnalysisRow
            title="H4 → H1 Alignment"
            description="Higher and intermediate timeframe relationship"
            status="ALIGNED"
          />

          <AnalysisRow
            title="M15 Entry Context"
            description="Lower-timeframe market context"
            status="READY"
          />
        </View>

        {/* TOP-DOWN FLOW */}
        <View style={styles.topDownCard}>
          <View style={styles.topDownHeader}>
            <View>
              <Text style={styles.topDownEyebrow} allowFontScaling={false}>ANALYSIS SEQUENCE</Text>
              <Text style={styles.topDownTitle} allowFontScaling={false}>Top-Down Market Model</Text>
            </View>

            <Text style={styles.topDownNumber} allowFontScaling={false}>02</Text>
          </View>

          <View style={styles.sequence}>
            <SequenceItem
              timeframe="H4"
              title="Macro Structure"
              description="Establish the higher-timeframe market context."
              active={timeframe === 'H4'}
              onPress={() => setTimeframe('H4')}
            />

            <View style={styles.sequenceLine} />

            <SequenceItem
              timeframe="H1"
              title="Intermediate Structure"
              description="Refine directional structure and market behavior."
              active={timeframe === 'H1'}
              onPress={() => setTimeframe('H1')}
            />

            <View style={styles.sequenceLine} />

            <SequenceItem
              timeframe="M15"
              title="Execution Context"
              description="Inspect lower-timeframe price action before Confluence."
              active={timeframe === 'M15'}
              onPress={() => setTimeframe('M15')}
            />
          </View>
        </View>

        {/* BOTTOM ACTION BUTTON */}
        <Pressable
          onPress={handleConfluence}
          style={({pressed}) => [
            styles.actionButton,
            pressed && styles.pressed,
          ]}
        >
          <Text style={styles.actionButtonText} allowFontScaling={false}>Continue to Confluence →</Text>
        </Pressable>
      </ScrollView>
    </View>
  );
}

function AnalysisRow({
  title,
  description,
  status,
}: {
  title: string;
  description: string;
  status: string;
}) {
  const isBullish = status === 'BULLISH' || status === 'CONFIRMED' || status === 'ALIGNED' || status === 'READY';
  const isBearish = status === 'BEARISH';

  return (
    <View style={styles.analysisRow}>
      <View style={styles.analysisTextWrap}>
        <Text style={styles.analysisTitle} allowFontScaling={false}>{title}</Text>
        <Text style={styles.analysisDesc} allowFontScaling={false}>{description}</Text>
      </View>

      <View
        style={[
          styles.statusPill,
          isBullish && styles.statusPillBullish,
          isBearish && styles.statusPillBearish,
        ]}
      >
        <Text
          allowFontScaling={false}
          style={[
            styles.statusPillText,
            isBullish && styles.statusPillTextBullish,
            isBearish && styles.statusPillTextBearish,
          ]}
        >
          {status}
        </Text>
      </View>
    </View>
  );
}

function SequenceItem({
  timeframe,
  title,
  description,
  active,
  onPress,
}: {
  timeframe: string;
  title: string;
  description: string;
  active: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      style={({pressed}) => [
        styles.sequenceItem,
        active && styles.sequenceItemActive,
        pressed && styles.pressed,
      ]}
    >
      <View
        style={[
          styles.sequenceBadge,
          active && styles.sequenceBadgeActive,
        ]}
      >
        <Text
          allowFontScaling={false}
          style={[
            styles.sequenceTimeframe,
            active && styles.sequenceTimeframeActive,
          ]}
        >
          {timeframe}
        </Text>
      </View>

      <View style={styles.sequenceContent}>
        <Text
          allowFontScaling={false}
          style={[
            styles.sequenceTitle,
            active && styles.sequenceTitleActive,
          ]}
        >
          {title}
        </Text>

        <Text style={styles.sequenceDescription} allowFontScaling={false}>{description}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#05070D',
  },
  glowTop: {
    position: 'absolute',
    top: -80,
    left: -40,
    width: 240,
    height: 240,
    borderRadius: 120,
    backgroundColor: 'rgba(112, 131, 255, 0.12)',
  },
  glowBottom: {
    position: 'absolute',
    bottom: -100,
    right: -60,
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: 'rgba(92, 110, 245, 0.08)',
  },
  content: {
    paddingHorizontal: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.04)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  backIcon: {
    color: '#F4F7FC',
    fontSize: 26,
    lineHeight: 28,
  },
  headerText: {
    flex: 1,
  },
  eyebrow: {
    fontSize: 11,
    letterSpacing: 2,
    color: '#7083FF',
    fontWeight: '700',
    marginBottom: 2,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#F4F7FC',
    letterSpacing: 0.3,
  },
  subtitle: {
    fontSize: 12,
    color: '#657493',
    marginTop: 2,
  },
  stageBadge: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 10,
    backgroundColor: 'rgba(112, 131, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(112, 131, 255, 0.25)',
  },
  stageNumber: {
    fontSize: 14,
    fontWeight: '800',
    color: '#7083FF',
  },
  stageLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 1,
    color: '#95A4FC',
  },
  marketCard: {
    backgroundColor: '#0A0E18',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1B2435',
    marginBottom: 16,
  },
  marketTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  marketLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.5,
    color: '#5C6C8A',
  },
  marketStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#10B981',
  },
  statusText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#10B981',
    letterSpacing: 1,
  },
  marketMainRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  symbol: {
    fontSize: 20,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: 0.5,
  },
  marketName: {
    fontSize: 12,
    color: '#7F8EA8',
    marginTop: 2,
  },
  topDownBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    backgroundColor: 'rgba(112, 131, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(112, 131, 255, 0.2)',
  },
  topDownText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    color: '#7083FF',
  },
  sectionHeader: {
    marginBottom: 10,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1.5,
    color: '#657493',
  },
  sectionSubtitle: {
    fontSize: 11,
    color: '#495773',
    marginTop: 2,
  },
  timeframeSelector: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  timeframeButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    alignItems: 'center',
  },
  timeframeButtonActive: {
    backgroundColor: 'rgba(112, 131, 255, 0.15)',
    borderColor: '#7083FF',
  },
  timeframeText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#657493',
  },
  timeframeTextActive: {
    color: '#FFFFFF',
  },
  chartCard: {
    backgroundColor: '#0A0E18',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1B2435',
    marginBottom: 20,
  },
  chartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  chartSymbol: {
    fontSize: 14,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  chartTimeframe: {
    fontSize: 10,
    color: '#5C6C8A',
    fontWeight: '700',
    letterSpacing: 1,
    marginTop: 2,
  },
  chartLiveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    backgroundColor: 'rgba(16, 185, 129, 0.08)',
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.2)',
  },
  chartLiveDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: '#10B981',
  },
  chartLiveText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#10B981',
    letterSpacing: 1,
  },
  chart: {
    height: 160,
    backgroundColor: 'rgba(5, 7, 13, 0.6)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#151C2C',
    position: 'relative',
    overflow: 'hidden',
    paddingVertical: 10,
  },
  gridLineOne: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: '25%',
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
  },
  gridLineTwo: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: '50%',
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.04)',
  },
  gridLineThree: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: '75%',
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
  },
  gridLineFour: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    left: '50%',
    width: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
  },
  candleContainer: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingHorizontal: 8,
  },
  candleColumn: {
    flex: 1,
    height: '100%',
    alignItems: 'center',
    position: 'relative',
  },
  wick: {
    position: 'absolute',
    width: 1.5,
    backgroundColor: 'rgba(255, 255, 255, 0.25)',
  },
  candleBody: {
    position: 'absolute',
    width: 8,
    borderRadius: 1,
  },
  bullishCandle: {
    backgroundColor: '#10B981',
  },
  bearishCandle: {
    backgroundColor: '#EF4444',
  },
  priceLabelTop: {
    position: 'absolute',
    top: 6,
    right: 8,
    backgroundColor: 'rgba(10, 14, 24, 0.8)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  priceLabelBottom: {
    position: 'absolute',
    bottom: 6,
    right: 8,
    backgroundColor: 'rgba(10, 14, 24, 0.8)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  priceLabelText: {
    fontSize: 9,
    fontFamily: 'monospace',
    fontWeight: '700',
    color: '#657493',
  },
  chartFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 10,
    paddingHorizontal: 4,
  },
  chartFooterText: {
    fontSize: 10,
    color: '#495773',
    fontWeight: '700',
    letterSpacing: 1,
  },
  analysisList: {
    gap: 8,
    marginBottom: 20,
  },
  analysisRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#0A0E18',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: '#1B2435',
  },
  analysisTextWrap: {
    flex: 1,
    marginRight: 12,
  },
  analysisTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  analysisDesc: {
    fontSize: 11,
    color: '#657493',
    marginTop: 2,
  },
  statusPill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
  },
  statusPillBullish: {
    backgroundColor: 'rgba(16, 185, 129, 0.12)',
  },
  statusPillBearish: {
    backgroundColor: 'rgba(239, 68, 68, 0.12)',
  },
  statusPillText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#7F8EA8',
    letterSpacing: 0.5,
  },
  statusPillTextBullish: {
    color: '#10B981',
  },
  statusPillTextBearish: {
    color: '#EF4444',
  },
  topDownCard: {
    backgroundColor: '#0A0E18',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1B2435',
    marginBottom: 20,
  },
  topDownHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  topDownEyebrow: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.5,
    color: '#7083FF',
  },
  topDownTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
    marginTop: 2,
  },
  topDownNumber: {
    fontSize: 20,
    fontWeight: '800',
    color: '#1B2435',
  },
  sequence: {
    gap: 4,
  },
  sequenceItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    backgroundColor: '#05070D',
    borderWidth: 1,
    borderColor: '#151C2C',
  },
  sequenceItemActive: {
    borderColor: '#7083FF',
    backgroundColor: 'rgba(112, 131, 255, 0.06)',
  },
  sequenceBadge: {
    width: 38,
    height: 38,
    borderRadius: 10,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  sequenceBadgeActive: {
    borderColor: '#7083FF',
    backgroundColor: 'rgba(112, 131, 255, 0.15)',
  },
  sequenceTimeframe: {
    fontSize: 12,
    fontWeight: '800',
    color: '#657493',
  },
  sequenceTimeframeActive: {
    color: '#7083FF',
  },
  sequenceContent: {
    flex: 1,
  },
  sequenceTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#7F8EA8',
  },
  sequenceTitleActive: {
    color: '#FFFFFF',
  },
  sequenceDescription: {
    fontSize: 10,
    color: '#5C6C8A',
    marginTop: 2,
  },
  sequenceLine: {
    width: 2,
    height: 8,
    backgroundColor: '#151C2C',
    marginLeft: 30,
  },
  actionButton: {
    backgroundColor: '#7083FF',
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: 0.5,
  },
  pressed: {
    opacity: 0.75,
  },
});

