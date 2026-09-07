
import React, {useMemo, useState} from 'react';
import {
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {useSafeAreaInsets} from 'react-native-safe-area-context';

type Timeframe = 'H4' | 'H1' | 'M15';

type Candle = {
  open: number;
  close: number;
  high: number;
  low: number;
};

const TIMEFRAMES: Timeframe[] = ['H4', 'H1', 'M15'];

/*
 * Temporary visualization data.
 *
 * This is intentionally only used to render the chart structure.
 * Real OHLC candles should eventually come from the BALLY TRADES BOT
 * market-data/API layer.
 */
const CHART_DATA: Record<Timeframe, Candle[]> = {
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

export default function FlowAnalysisScreen({
  navigation,
  route,
}: any) {
  const insets = useSafeAreaInsets();

  const symbol = route?.params?.symbol || 'XAUUSD';

  const [timeframe, setTimeframe] =
    useState<Timeframe>('H4');

  const candles = useMemo(
    () => CHART_DATA[timeframe],
    [timeframe],
  );

  const handleConfluence = () => {
    navigation.navigate('FlowConfluence', {
      symbol,
    });
  };

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
            <Text style={styles.backIcon}>‹</Text>
          </Pressable>

          <View style={styles.headerText}>
            <Text style={styles.eyebrow}>
              BALLY FLOW
            </Text>

            <Text style={styles.title}>
              Market Analysis
            </Text>

            <Text style={styles.subtitle}>
              H4 → H1 → M15 top-down analysis
            </Text>
          </View>

          <View style={styles.stageBadge}>
            <Text style={styles.stageNumber}>
              02
            </Text>

            <Text style={styles.stageLabel}>
              ANALYSIS
            </Text>
          </View>
        </View>

        {/* MARKET */}
        <View style={styles.marketCard}>
          <View style={styles.marketTopRow}>
            <Text style={styles.marketLabel}>
              ANALYSIS MARKET
            </Text>

            <View style={styles.marketStatus}>
              <View style={styles.statusDot} />

              <Text style={styles.statusText}>
                SELECTED
              </Text>
            </View>
          </View>

          <View style={styles.marketMainRow}>
            <View>
              <Text style={styles.symbol}>
                {symbol}
              </Text>

              <Text style={styles.marketName}>
                {symbol === 'XAUUSD'
                  ? 'Gold / US Dollar'
                  : 'Selected Trading Intelligence market'}
              </Text>
            </View>

            <View style={styles.topDownBadge}>
              <Text style={styles.topDownText}>
                TOP-DOWN
              </Text>
            </View>
          </View>
        </View>

        {/* TIMEFRAME SELECTOR */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              TIMEFRAME ANALYSIS
            </Text>

            <Text style={styles.sectionSubtitle}>
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
              <Text style={styles.chartSymbol}>
                {symbol}
              </Text>

              <Text style={styles.chartTimeframe}>
                {timeframe} CANDLESTICKS
              </Text>
            </View>

            <View style={styles.chartLiveBadge}>
              <View style={styles.chartLiveDot} />

              <Text style={styles.chartLiveText}>
                MARKET DATA
              </Text>
            </View>
          </View>

          <View style={styles.chart}>
            <View style={styles.gridLineOne} />
            <View style={styles.gridLineTwo} />
            <View style={styles.gridLineThree} />
            <View style={styles.gridLineFour} />

            <View style={styles.candleContainer}>
              {candles.map((candle, index) => {
                const bullish =
                  candle.close >= candle.open;

                const bodyTop =
                  100 - Math.max(
                    candle.open,
                    candle.close,
                  );

                const bodyHeight = Math.max(
                  Math.abs(
                    candle.close - candle.open,
                  ),
                  5,
                );

                const wickTop =
                  100 - candle.high;

                const wickHeight =
                  Math.max(
                    candle.high - candle.low,
                    10,
                  );

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
              <Text style={styles.priceLabelText}>
                HIGH
              </Text>
            </View>

            <View style={styles.priceLabelBottom}>
              <Text style={styles.priceLabelText}>
                LOW
              </Text>
            </View>
          </View>

          <View style={styles.chartFooter}>
            <Text style={styles.chartFooterText}>
              OHLC
            </Text>

            <Text style={styles.chartFooterText}>
              {timeframe}
            </Text>

            <Text style={styles.chartFooterText}>
              {candles.length} BARS
            </Text>
          </View>
        </View>

        {/* ANALYSIS COMPONENTS */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              ANALYSIS COMPONENTS
            </Text>

            <Text style={styles.sectionSubtitle}>
              Intelligence prepared for Confluence
            </Text>
          </View>
        </View>

        <View style={styles.analysisList}>
          <AnalysisRow
            title="Market Structure"
            description="Higher-timeframe directional structure"
            status="ANALYZING"
          />

          <AnalysisRow
            title="Price Action"
            description="Candle behavior and structural movement"
            status="ANALYZING"
          />

          <AnalysisRow
            title="H4 → H1 Alignment"
            description="Higher and intermediate timeframe relationship"
            status="ANALYZING"
          />

          <AnalysisRow
            title="M15 Entry Context"
            description="Lower-timeframe market context"
            status="ANALYZING"
          />
        </View>

        {/* TOP-DOWN FLOW */}
        <View style={styles.topDownCard}>
          <View style={styles.topDownHeader}>
            <View>
              <Text style={styles.topDownEyebrow}>
                ANALYSIS SEQUENCE
              </Text>

              <Text style={styles.topDownTitle}>
                Top-Down Market Model
              </Text>
            </View>

            <Text style={styles.topDownNumber}>
              02
            </Text>
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

        {/* ENGINE NOTE */}
        <View style={styles.infoCard}>
          <View style={styles.infoHeader}>
            <View style={styles.infoIcon}>
              <Text style={styles.infoIconText}>
                i
              </Text>
            </View>

            <Text style={styles.infoTitle}>
              ANALYSIS ENGINE
            </Text>
          </View>

          <Text style={styles.infoText}>
            This stage establishes the top-down market context.
            SMC confluence, Supply & Demand, Volume Profile,
            volatility and market-session analysis are evaluated
            in Stage 03.
          </Text>
        </View>
      </ScrollView>

      {/* CONTINUE */}
      <View
        style={[
          styles.bottomBar,
          {
            paddingBottom: Math.max(
              insets.bottom,
              16,
            ),
          },
        ]}
      >
        <Pressable
          onPress={handleConfluence}
          style={({pressed}) => [
            styles.continueButton,
            pressed && styles.continuePressed,
          ]}
        >
          <View>
            <Text style={styles.continueLabel}>
              NEXT STAGE
            </Text>

            <Text style={styles.continueTitle}>
              CONFLUENCE
            </Text>
          </View>

          <View style={styles.continueArrow}>
            <Text style={styles.continueArrowText}>
              →
            </Text>
          </View>
        </Pressable>
      </View>
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
  return (
    <View style={styles.analysisRow}>
      <View style={styles.analysisIndicator}>
        <View style={styles.analysisIndicatorInner} />
      </View>

      <View style={styles.analysisContent}>
        <View style={styles.analysisTitleRow}>
          <Text style={styles.analysisTitle}>
            {title}
          </Text>

          <Text style={styles.analysisStatus}>
            {status}
          </Text>
        </View>

        <Text style={styles.analysisDescription}>
          {description}
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
  timeframe: Timeframe;
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
          styles.sequenceCircle,
          active && styles.sequenceCircleActive,
        ]}
      >
        <Text
          style={[
            styles.sequenceTimeframe,
            active && styles.sequenceTimeframeActive,
          ]}
        >
          {timeframe}
        </Text>
      </View>

      <View style={styles.sequenceContent}>
        <Text style={styles.sequenceTitle}>
          {title}
        </Text>

        <Text style={styles.sequenceDescription}>
          {description}
        </Text>
      </View>

      <Text style={styles.sequenceArrow}>
        ›
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#05070D',
  },

  content: {
    paddingHorizontal: 20,
  },

  glowTop: {
    position: 'absolute',
    width: 280,
    height: 280,
    borderRadius: 140,
    backgroundColor: '#101B5C',
    opacity: 0.18,
    top: -170,
    right: -100,
  },

  glowBottom: {
    position: 'absolute',
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: '#17204A',
    opacity: 0.16,
    bottom: -150,
    left: -110,
  },

  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 24,
  },

  backButton: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },

  backIcon: {
    color: '#A0ABC0',
    fontSize: 28,
    fontWeight: '300',
    marginTop: -2,
  },

  pressed: {
    opacity: 0.7,
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
    fontSize: 25,
    fontWeight: '900',
    marginTop: 4,
  },

  subtitle: {
    color: '#77839D',
    fontSize: 10,
    lineHeight: 15,
    marginTop: 5,
  },

  stageBadge: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    marginLeft: 8,
  },

  stageNumber: {
    color: '#7083FF',
    fontSize: 12,
    fontWeight: '900',
  },

  stageLabel: {
    color: '#53617A',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.8,
    marginTop: 2,
  },

  marketCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 18,
    padding: 18,
    marginBottom: 25,
  },

  marketTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  marketLabel: {
    color: '#68748D',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1.5,
  },

  marketStatus: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  statusDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 5,
  },

  statusText: {
    color: '#35E68A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1,
  },

  marketMainRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 13,
  },

  symbol: {
    color: '#FFFFFF',
    fontSize: 26,
    fontWeight: '900',
    letterSpacing: 1,
  },

  marketName: {
    color: '#69758D',
    fontSize: 11,
    marginTop: 4,
  },

  topDownBadge: {
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 9,
    paddingHorizontal: 9,
    paddingVertical: 6,
  },

  topDownText: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1,
  },

  sectionHeader: {
    marginBottom: 13,
  },

  sectionTitle: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1.4,
  },

  sectionSubtitle: {
    color: '#56627A',
    fontSize: 9,
    marginTop: 4,
  },

  timeframeSelector: {
    flexDirection: 'row',
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 13,
    padding: 4,
    marginBottom: 17,
  },

  timeframeButton: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 9,
  },

  timeframeButtonActive: {
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#334BFF',
  },

  timeframeText: {
    color: '#56627A',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1,
  },

  timeframeTextActive: {
    color: '#8A98FF',
  },

  chartCard: {
    backgroundColor: '#080C15',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 18,
    padding: 14,
    marginBottom: 25,
  },

  chartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 13,
  },

  chartSymbol: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  chartTimeframe: {
    color: '#56627A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1,
    marginTop: 3,
  },

  chartLiveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#202A3D',
    backgroundColor: '#0D121D',
    borderRadius: 8,
    paddingHorizontal: 7,
    paddingVertical: 5,
  },

  chartLiveDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 5,
  },

  chartLiveText: {
    color: '#68758E',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  chart: {
    height: 245,
    backgroundColor: '#060911',
    borderRadius: 11,
    borderWidth: 1,
    borderColor: '#111827',
    overflow: 'hidden',
    position: 'relative',
  },

  gridLineOne: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: '20%',
    height: 1,
    backgroundColor: '#111827',
  },

  gridLineTwo: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: '40%',
    height: 1,
    backgroundColor: '#111827',
  },

  gridLineThree: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: '60%',
    height: 1,
    backgroundColor: '#111827',
  },

  gridLineFour: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: '80%',
    height: 1,
    backgroundColor: '#111827',
  },

  candleContainer: {
    position: 'absolute',
    left: 17,
    right: 30,
    top: 18,
    bottom: 18,
    flexDirection: 'row',
    alignItems: 'stretch',
    justifyContent: 'space-between',
  },

  candleColumn: {
    width: 10,
    height: '100%',
    position: 'relative',
  },

  wick: {
    position: 'absolute',
    width: 1,
    left: 4.5,
    backgroundColor: '#6C7891',
  },

  candleBody: {
    position: 'absolute',
    width: 9,
    left: 0.5,
    borderRadius: 1,
  },

  bullishCandle: {
    backgroundColor: '#35E68A',
  },

  bearishCandle: {
    backgroundColor: '#69758D',
  },

  priceLabelTop: {
    position: 'absolute',
    top: 8,
    right: 7,
  },

  priceLabelBottom: {
    position: 'absolute',
    bottom: 8,
    right: 7,
  },

  priceLabelText: {
    color: '#39455B',
    fontSize: 6,
    fontWeight: '900',
  },

  chartFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 9,
  },

  chartFooterText: {
    color: '#4E5A72',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  analysisList: {
    marginBottom: 24,
  },

  analysisRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 14,
    padding: 13,
    marginBottom: 8,
  },

  analysisIndicator: {
    width: 30,
    height: 30,
    borderRadius: 10,
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
  },

  analysisIndicatorInner: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: '#7083FF',
  },

  analysisContent: {
    flex: 1,
  },

  analysisTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  analysisTitle: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '900',
  },

  analysisStatus: {
    color: '#56627A',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  analysisDescription: {
    color: '#68758E',
    fontSize: 9,
    lineHeight: 14,
    marginTop: 3,
  },

  topDownCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 18,
    padding: 16,
    marginBottom: 20,
  },

  topDownHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },

  topDownEyebrow: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.5,
  },

  topDownTitle: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '900',
    marginTop: 3,
  },

  topDownNumber: {
    color: '#53617A',
    fontSize: 18,
    fontWeight: '900',
  },

  sequence: {
    marginTop: 15,
  },

  sequenceItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    borderRadius: 11,
  },

  sequenceItemActive: {
    backgroundColor: '#0D1324',
  },

  sequenceCircle: {
    width: 39,
    height: 39,
    borderRadius: 20,
    backgroundColor: '#111722',
    borderWidth: 1,
    borderColor: '#263043',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
  },

  sequenceCircleActive: {
    backgroundColor: '#10183D',
    borderColor: '#334BFF',
  },

  sequenceTimeframe: {
    color: '#68758E',
    fontSize: 8,
    fontWeight: '900',
  },

  sequenceTimeframeActive: {
    color: '#8A98FF',
  },

  sequenceContent: {
    flex: 1,
  },

  sequenceTitle: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '900',
  },

  sequenceDescription: {
    color: '#68758E',
    fontSize: 8,
    lineHeight: 13,
    marginTop: 3,
  },

  sequenceArrow: {
    color: '#53617A',
    fontSize: 23,
    marginLeft: 7,
  },

  sequenceLine: {
    width: 1,
    height: 13,
    backgroundColor: '#263043',
    marginLeft: 19,
  },

  infoCard: {
    backgroundColor: '#080C15',
    borderWidth: 1,
    borderColor: '#151D2C',
    borderRadius: 16,
    padding: 17,
  },

  infoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 9,
  },

  infoIcon: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 1,
    borderColor: '#334BFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },

  infoIconText: {
    color: '#7083FF',
    fontSize: 10,
    fontWeight: '900',
  },

  infoTitle: {
    color: '#7083FF',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1.5,
  },

  infoText: {
    color: '#68758E',
    fontSize: 10,
    lineHeight: 17,
  },

  bottomBar: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    paddingHorizontal: 20,
    paddingTop: 12,
    backgroundColor: '#05070D',
    borderTopWidth: 1,
    borderTopColor: '#111827',
  },

  continueButton: {
    minHeight: 60,
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#334BFF',
    borderRadius: 16,
    paddingHorizontal: 17,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  continuePressed: {
    opacity: 0.78,
    transform: [{scale: 0.995}],
  },

  continueLabel: {
    color: '#68758E',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.2,
  },

  continueTitle: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '900',
    letterSpacing: 0.8,
    marginTop: 3,
  },

  continueArrow: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#263A91',
    alignItems: 'center',
    justifyContent: 'center',
  },

  continueArrowText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
});
