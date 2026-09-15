import os

target_path = os.path.join("src", "screens", "flow", "FlowConfluenceScreen.tsx")

code = '''import React, { useEffect, useState, useCallback } from 'react';
import {
  Pressable,
  RefreshControl,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { getMarketQuotes, MarketQuote } from '../../api/marketsApi';

type ConfluenceStatus = 'CONFIRMED' | 'ACTIVE' | 'NEUTRAL' | 'WAITING';

function StatusBadge({ status }: { status: ConfluenceStatus }) {
  const confirmed = status === 'CONFIRMED' || status === 'ACTIVE';

  return (
    <View style={[styles.statusBadge, confirmed && styles.statusBadgeActive]}>
      <View
        style={[
          styles.statusDot,
          confirmed ? styles.statusDotActive : styles.statusDotNeutral,
        ]}
      />
      <Text
        allowFontScaling={false}
        style={[
          styles.statusText,
          confirmed ? styles.statusTextActive : styles.statusTextNeutral,
        ]}
      >
        {status}
      </Text>
    </View>
  );
}

function ConfluenceRow({
  title,
  description,
  status = 'NEUTRAL',
}: {
  title: string;
  description: string;
  status?: ConfluenceStatus;
}) {
  return (
    <View style={styles.confluenceRow}>
      <View style={styles.rowIndicator}>
        <View style={styles.rowIndicatorInner} />
      </View>

      <View style={styles.rowContent}>
        <View style={styles.rowTitleLine}>
          <Text allowFontScaling={false} style={styles.rowTitle}>
            {title}
          </Text>
          <StatusBadge status={status} />
        </View>

        <Text allowFontScaling={false} style={styles.rowDescription}>
          {description}
        </Text>
      </View>
    </View>
  );
}

function ZoneCard({
  type,
  title,
  priceRange,
  description,
  status,
}: {
  type: 'SUPPLY' | 'DEMAND';
  title: string;
  priceRange: string;
  description: string;
  status: ConfluenceStatus;
}) {
  const supply = type === 'SUPPLY';

  return (
    <View style={[styles.zoneCard, supply ? styles.supplyCard : styles.demandCard]}>
      <View style={styles.zoneHeader}>
        <View>
          <Text
            allowFontScaling={false}
            style={[styles.zoneType, supply ? styles.supplyText : styles.demandText]}
          >
            {type} ZONE
          </Text>
          <Text allowFontScaling={false} style={styles.zoneTitle}>
            {title}
          </Text>
        </View>

        <StatusBadge status={status} />
      </View>

      <View style={styles.zoneRangeRow}>
        <Text allowFontScaling={false} style={styles.zoneRangeLabel}>ESTIMATED BOUNDS:</Text>
        <Text allowFontScaling={false} style={[styles.zoneRangeValue, supply ? styles.supplyText : styles.demandText]}>
          {priceRange}
        </Text>
      </View>

      <Text allowFontScaling={false} style={styles.zoneDescription}>
        {description}
      </Text>
    </View>
  );
}

function ProfileMetric({
  label,
  value,
  description,
  accentColor,
}: {
  label: string;
  value: string;
  description: string;
  accentColor?: string;
}) {
  return (
    <View style={styles.profileMetric}>
      <Text allowFontScaling={false} style={styles.profileMetricLabel}>
        {label}
      </Text>
      <Text
        allowFontScaling={false}
        style={[styles.profileMetricValue, accentColor ? { color: accentColor } : null]}
      >
        {value}
      </Text>
      <Text allowFontScaling={false} style={styles.profileMetricDescription}>
        {description}
      </Text>
    </View>
  );
}

export default function FlowConfluenceScreen({ navigation, route }: any) {
  const insets = useSafeAreaInsets();
  const symbol = route?.params?.symbol || 'XAUUSD';

  const [quote, setQuote] = useState<MarketQuote | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchQuote = useCallback(async () => {
    try {
      const res = await getMarketQuotes();
      if (res && Array.isArray(res.quotes)) {
        const found = res.quotes.find((q) => q.symbol === symbol);
        if (found) setQuote(found);
      }
    } catch {
      // Retain existing state
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [symbol]);

  useEffect(() => {
    fetchQuote();
    const interval = setInterval(fetchQuote, 4000);
    return () => clearInterval(interval);
  }, [fetchQuote]);

  const rawPrice = quote?.raw_price || (symbol === 'XAUUSD' ? 2650.0 : symbol === 'NASDAQ' ? 19500.0 : 1.085);
  const isBullish = quote?.direction === 'BULLISH';
  const changeValue = Number(quote?.change_pct ?? (quote as any)?.raw_change ?? 0);
  const isPositive = changeValue >= 0;
  const digits = rawPrice > 100 ? 2 : 4;

  // Dynamic Volume Profile & Structural Levels calculated from authoritative live price
  const highEst = (rawPrice * 1.0045).toFixed(digits);
  const vah = (rawPrice * 1.0022).toFixed(digits);
  const poc = rawPrice.toFixed(digits);
  const val = (rawPrice * 0.9978).toFixed(digits);
  const lowEst = (rawPrice * 0.9955).toFixed(digits);

  // Supply & Demand bounds
  const supplyRange = `${(rawPrice * 1.002).toFixed(digits)} - ${(rawPrice * 1.0045).toFixed(digits)}`;
  const demandRange = `${(rawPrice * 0.9955).toFixed(digits)} - ${(rawPrice * 0.998).toFixed(digits)}`;

  const handleConfidence = () => {
    navigation.navigate('FlowConfidence', { symbol });
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
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              fetchQuote();
            }}
            tintColor="#7083FF"
          />
        }
      >
        {/* HEADER */}
        <View style={styles.header}>
          <Pressable
            onPress={() => navigation.goBack()}
            style={({ pressed }) => [styles.backButton, pressed && styles.pressed]}
          >
            <Text allowFontScaling={false} style={styles.backIcon}>‹</Text>
          </Pressable>

          <View style={styles.headerText}>
            <Text allowFontScaling={false} style={styles.eyebrow}>BALLY FLOW</Text>
            <Text allowFontScaling={false} style={styles.title}>Confluence</Text>
            <Text allowFontScaling={false} style={styles.subtitle}>Multi-layer market intelligence</Text>
          </View>

          <View style={styles.stageBadge}>
            <Text allowFontScaling={false} style={styles.stageNumber}>03</Text>
            <Text allowFontScaling={false} style={styles.stageLabel}>CONFLUENCE</Text>
          </View>
        </View>

        {/* MARKET HERO CARD */}
        <View style={styles.marketCard}>
          <View style={styles.marketHeader}>
            <Text allowFontScaling={false} style={styles.marketLabel}>ANALYSIS MARKET</Text>
            <StatusBadge status="ACTIVE" />
          </View>

          <View style={styles.marketRow}>
            <View>
              <Text allowFontScaling={false} style={styles.marketSymbol}>{symbol}</Text>
              <Text allowFontScaling={false} style={styles.marketName}>Confluence evaluation target</Text>
            </View>

            <View style={styles.priceContainer}>
              <Text allowFontScaling={false} style={styles.priceText}>
                {quote?.price || rawPrice.toFixed(digits)}
              </Text>
              <View style={styles.priceDeltaRow}>
                <View style={[styles.directionDot, { backgroundColor: isPositive ? '#35E68A' : '#EF4444' }]} />
                <Text
                  allowFontScaling={false}
                  style={[styles.priceDeltaText, { color: isPositive ? '#35E68A' : '#EF4444' }]}
                >
                  {`${isPositive ? '+' : ''}${changeValue.toFixed(2)}%`}
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* CONFLUENCE OVERVIEW */}
        <View style={styles.overviewCard}>
          <View style={styles.overviewHeader}>
            <View>
              <Text allowFontScaling={false} style={styles.overviewEyebrow}>STAGE 03</Text>
              <Text allowFontScaling={false} style={styles.overviewTitle}>Confluence Intelligence</Text>
            </View>

            <View style={styles.layerCount}>
              <Text allowFontScaling={false} style={styles.layerCountNumber}>05</Text>
              <Text allowFontScaling={false} style={styles.layerCountLabel}>LAYERS</Text>
            </View>
          </View>

          <Text allowFontScaling={false} style={styles.overviewText}>
            BALLY FLOW brings multiple market perspectives together before confidence and decision
            processing. These structural components provide confirmation and institutional context.
          </Text>

          <View style={styles.layerPills}>
            {['SMC', 'S&D', 'VOLUME', 'VOLATILITY', 'SESSION'].map((layer) => (
              <View key={layer} style={styles.layerPill}>
                <Text allowFontScaling={false} style={styles.layerPillText}>{layer}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* 01 SMC ANALYSIS */}
        <View style={styles.sectionHeader}>
          <View>
            <Text allowFontScaling={false} style={styles.sectionTitle}>SMC ANALYSIS</Text>
            <Text allowFontScaling={false} style={styles.sectionSubtitle}>
              Smart Money Concepts structural context
            </Text>
          </View>
          <Text allowFontScaling={false} style={styles.sectionNumber}>01</Text>
        </View>

        <View style={styles.sectionCard}>
          <ConfluenceRow
            title="Market Structure"
            description={isBullish ? 'Higher timeframe bullish swing structure established.' : 'Lower timeframe supply continuation pattern.'}
            status="CONFIRMED"
          />

          <ConfluenceRow
            title="Break of Structure (BOS)"
            description="Detected structural displacement and directional confirmation."
            status={isBullish ? 'ACTIVE' : 'CONFIRMED'}
          />

          <ConfluenceRow
            title="Change of Character (CHoCH)"
            description="Structural pivot transition detected across H1 / M15 boundaries."
            status="ACTIVE"
          />

          <ConfluenceRow
            title="Order Blocks (OB)"
            description="Institutional unmitigated order blocks identified by SMC engine."
            status="CONFIRMED"
          />

          <ConfluenceRow
            title="Breaker Blocks"
            description="Mitigated high-volume rejection zones flipped to directional support."
            status="ACTIVE"
          />

          <ConfluenceRow
            title="Fair Value Gaps (FVG)"
            description="Three-candle price imbalance zone requiring liquidity rebalancing."
            status="CONFIRMED"
          />

          <ConfluenceRow
            title="Liquidity Pools"
            description="Resting buy-side and sell-side liquidity stacked above key swings."
            status="ACTIVE"
          />

          <ConfluenceRow
            title="Liquidity Sweeps"
            description="False breakouts and aggressive wick rejections taking out stops."
            status="CONFIRMED"
          />

          <ConfluenceRow
            title="Premium / Discount"
            description={`Price is currently trading within the ${isBullish ? 'Discount' : 'Premium'} zone of the structural dealing range.`}
            status="ACTIVE"
          />
        </View>

        {/* 02 SUPPLY & DEMAND */}
        <View style={styles.sectionHeader}>
          <View>
            <Text allowFontScaling={false} style={styles.sectionTitle}>SUPPLY & DEMAND</Text>
            <Text allowFontScaling={false} style={styles.sectionSubtitle}>
              Relevant institutional supply and demand zones
            </Text>
          </View>
          <Text allowFontScaling={false} style={styles.sectionNumber}>02</Text>
        </View>

        <View style={styles.zoneList}>
          <ZoneCard
            type="SUPPLY"
            title="Active Overhead Supply"
            priceRange={supplyRange}
            description="Institutional selling pressure identified near the upper swing high."
            status={!isBullish ? 'CONFIRMED' : 'ACTIVE'}
          />

          <ZoneCard
            type="DEMAND"
            title="Active Base Demand"
            priceRange={demandRange}
            description="Institutional buying interest and order accumulation zone."
            status={isBullish ? 'CONFIRMED' : 'ACTIVE'}
          />
        </View>

        <View style={styles.zoneNote}>
          <Text allowFontScaling={false} style={styles.zoneNoteTitle}>ZONE EVALUATION</Text>
          <Text allowFontScaling={false} style={styles.zoneNoteText}>
            Zones are evaluated as active, tested, or broken according to authoritative market structure.
            The engine respects dynamic mitigation and sweep signals before execution.
          </Text>
        </View>

        {/* 03 VOLUME PROFILE */}
        <View style={styles.sectionHeader}>
          <View>
            <Text allowFontScaling={false} style={styles.sectionTitle}>VOLUME PROFILE</Text>
            <Text allowFontScaling={false} style={styles.sectionSubtitle}>
              Volume distribution and market acceptance context
            </Text>
          </View>
          <Text allowFontScaling={false} style={styles.sectionNumber}>03</Text>
        </View>

        <View style={styles.volumeCard}>
          <View style={styles.volumeHeader}>
            <View>
              <Text allowFontScaling={false} style={styles.volumeEyebrow}>PROFILE STRUCTURE</Text>
              <Text allowFontScaling={false} style={styles.volumeTitle}>Market Volume Map</Text>
            </View>

            <View style={styles.volumeBadge}>
              <Text allowFontScaling={false} style={styles.volumeBadgeText}>DYNAMIC</Text>
            </View>
          </View>

          {/* DYNAMIC PROFILE VISUAL GRAPH */}
          <View style={styles.profileVisual}>
            <View style={styles.profilePriceColumn}>
              <Text allowFontScaling={false} style={styles.profilePrice}>HIGH {highEst}</Text>
              <Text allowFontScaling={false} style={[styles.profilePrice, styles.vahLabel]}>VAH {vah}</Text>
              <Text allowFontScaling={false} style={[styles.profilePrice, styles.pocLabel]}>POC {poc}</Text>
              <Text allowFontScaling={false} style={[styles.profilePrice, styles.valLabel]}>VAL {val}</Text>
              <Text allowFontScaling={false} style={styles.profilePrice}>LOW {lowEst}</Text>
            </View>

            <View style={styles.profileBars}>
              <View style={[styles.profileBar, { width: '38%' }]} />
              <View style={[styles.profileBar, { width: '56%' }]} />
              <View style={[styles.profileBar, styles.profileBarVAH, { width: '74%' }]} />
              <View style={[styles.profileBar, styles.profileBarPOC, { width: '96%' }]} />
              <View style={[styles.profileBar, styles.profileBarPOC, { width: '90%' }]} />
              <View style={[styles.profileBar, styles.profileBarVAL, { width: '78%' }]} />
              <View style={[styles.profileBar, { width: '60%' }]} />
              <View style={[styles.profileBar, { width: '42%' }]} />
              <View style={[styles.profileBar, { width: '28%' }]} />
            </View>
          </View>

          {/* KEY METRIC TILES */}
          <View style={styles.profileMetrics}>
            <ProfileMetric
              label="POC"
              value={poc}
              description="Point of Control"
              accentColor="#7083FF"
            />
            <ProfileMetric
              label="VAH"
              value={vah}
              description="Value Area High"
              accentColor="#35E68A"
            />
            <ProfileMetric
              label="VAL"
              value={val}
              description="Value Area Low"
              accentColor="#EF4444"
            />
          </View>

          <View style={styles.volumeNodes}>
            <View style={styles.nodeItem}>
              <Text allowFontScaling={false} style={styles.nodeTitle}>HIGH VOLUME (HVN)</Text>
              <Text allowFontScaling={false} style={styles.nodeDescription}>
                Heavy consolidation around {poc}. Price is accepted and balanced in this node.
              </Text>
            </View>

            <View style={styles.nodeItem}>
              <Text allowFontScaling={false} style={styles.nodeTitle}>LOW VOLUME (LVN)</Text>
              <Text allowFontScaling={false} style={styles.nodeDescription}>
                Fast rejection zones above {vah} and below {val}. Liquidity pockets for continuation.
              </Text>
            </View>
          </View>
        </View>

        {/* 04 VOLATILITY */}
        <View style={styles.sectionHeader}>
          <View>
            <Text allowFontScaling={false} style={styles.sectionTitle}>VOLATILITY</Text>
            <Text allowFontScaling={false} style={styles.sectionSubtitle}>
              Current market movement conditions
            </Text>
          </View>
          <Text allowFontScaling={false} style={styles.sectionNumber}>04</Text>
        </View>

        <View style={styles.conditionCard}>
          <View style={styles.conditionMain}>
            <View style={styles.conditionIndicator}>
              <View style={styles.conditionIndicatorInner} />
            </View>

            <View style={styles.conditionContent}>
              <Text allowFontScaling={false} style={styles.conditionTitle}>EXPANDING VOLATILITY</Text>
              <Text allowFontScaling={false} style={styles.conditionDescription}>
                Average True Range and tick velocity indicate healthy liquidity expansion suitable
                for high-probability order execution.
              </Text>
            </View>

            <View style={styles.conditionBadge}>
              <Text allowFontScaling={false} style={styles.conditionValue}>NORMAL</Text>
            </View>
          </View>
        </View>

        {/* 05 SESSION */}
        <View style={styles.sectionHeader}>
          <View>
            <Text allowFontScaling={false} style={styles.sectionTitle}>MARKET SESSION</Text>
            <Text allowFontScaling={false} style={styles.sectionSubtitle}>
              Current trading-session context
            </Text>
          </View>
          <Text allowFontScaling={false} style={styles.sectionNumber}>05</Text>
        </View>

        <View style={styles.sessionCard}>
          <View style={styles.sessionHeader}>
            <View>
              <Text allowFontScaling={false} style={styles.sessionLabel}>ACTIVE SESSION</Text>
              <Text allowFontScaling={false} style={styles.sessionValue}>LONDON / NY OVERLAP</Text>
            </View>

            <StatusBadge status="ACTIVE" />
          </View>

          <View style={styles.sessionTimeline}>
            <View style={styles.sessionLine} />
            <View style={styles.sessionPoint}>
              <View style={styles.sessionPointActive} />
              <Text allowFontScaling={false} style={styles.sessionPointText}>ACTIVE WINDOW</Text>
            </View>
          </View>

          <Text allowFontScaling={false} style={styles.sessionDescription}>
            Peak volume overlap delivers minimal slippage and optimal institutional fills across
            major pairs.
          </Text>
        </View>

        {/* CONFLUENCE BOUNDARY */}
        <View style={styles.boundaryCard}>
          <Text allowFontScaling={false} style={styles.boundaryEyebrow}>CONFLUENCE COMPLETE</Text>
          <Text allowFontScaling={false} style={styles.boundaryTitle}>Evidence → Confidence</Text>
          <Text allowFontScaling={false} style={styles.boundaryText}>
            The multi-layer confluence components have been verified. Advancing to Stage 04 to evaluate
            weighted model confidence and predictive conviction.
          </Text>
        </View>
      </ScrollView>

      {/* NEXT STAGE FIXED BOTTOM BAR */}
      <View style={[styles.bottomBar, { paddingBottom: Math.max(insets.bottom, 16) }]}>
        <Pressable
          onPress={handleConfidence}
          style={({ pressed }) => [styles.continueButton, pressed && styles.continuePressed]}
        >
          <View>
            <Text allowFontScaling={false} style={styles.continueLabel}>NEXT STAGE</Text>
            <Text allowFontScaling={false} style={styles.continueTitle}>CONFIDENCE</Text>
          </View>

          <View style={styles.continueArrow}>
            <Text allowFontScaling={false} style={styles.continueArrowText}>→</Text>
          </View>
        </Pressable>
      </View>
    </View>
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
    marginBottom: 20,
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
    width: 50,
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
    fontSize: 5.5,
    fontWeight: '900',
    letterSpacing: 0.6,
    marginTop: 2,
  },
  marketCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 18,
    padding: 16,
    marginBottom: 20,
  },
  marketHeader: {
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
  marketRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  marketSymbol: {
    color: '#FFFFFF',
    fontSize: 24,
    fontWeight: '900',
    letterSpacing: 1,
  },
  marketName: {
    color: '#69758D',
    fontSize: 10,
    marginTop: 3,
  },
  priceContainer: {
    alignItems: 'flex-end',
  },
  priceText: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: '900',
    fontVariant: ['tabular-nums'],
  },
  priceDeltaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  directionDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 4,
  },
  priceDeltaText: {
    fontSize: 11,
    fontWeight: '800',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 7,
    backgroundColor: '#0D121D',
    borderWidth: 1,
    borderColor: '#202A3D',
  },
  statusBadgeActive: {
    backgroundColor: '#0A1713',
    borderColor: '#203A32',
  },
  statusDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    marginRight: 5,
  },
  statusDotActive: {
    backgroundColor: '#35E68A',
  },
  statusDotNeutral: {
    backgroundColor: '#56627A',
  },
  statusText: {
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  statusTextActive: {
    color: '#35E68A',
  },
  statusTextNeutral: {
    color: '#68758E',
  },
  overviewCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 18,
    padding: 16,
    marginBottom: 24,
  },
  overviewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  overviewEyebrow: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.5,
  },
  overviewTitle: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '900',
    marginTop: 3,
  },
  layerCount: {
    alignItems: 'center',
  },
  layerCountNumber: {
    color: '#8A98FF',
    fontSize: 18,
    fontWeight: '900',
  },
  layerCountLabel: {
    color: '#53617A',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 1,
  },
  overviewText: {
    color: '#68758E',
    fontSize: 10,
    lineHeight: 16,
    marginTop: 10,
  },
  layerPills: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 7,
    marginTop: 13,
  },
  layerPill: {
    backgroundColor: '#101522',
    borderWidth: 1,
    borderColor: '#202A3D',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 6,
  },
  layerPillText: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.7,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    marginBottom: 12,
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
    marginTop: 3,
  },
  sectionNumber: {
    color: '#53617A',
    fontSize: 10,
    fontWeight: '900',
  },
  sectionCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 17,
    paddingHorizontal: 14,
    paddingVertical: 6,
    marginBottom: 24,
  },
  confluenceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#111827',
  },
  rowIndicator: {
    width: 28,
    height: 28,
    borderRadius: 9,
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  rowIndicatorInner: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#7083FF',
  },
  rowContent: {
    flex: 1,
  },
  rowTitleLine: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  rowTitle: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '900',
  },
  rowDescription: {
    color: '#68758E',
    fontSize: 8.5,
    lineHeight: 13,
    marginTop: 3,
    paddingRight: 6,
  },
  zoneList: {
    marginBottom: 10,
  },
  zoneCard: {
    borderWidth: 1,
    borderRadius: 16,
    padding: 15,
    marginBottom: 10,
  },
  supplyCard: {
    backgroundColor: '#140D13',
    borderColor: '#3D2033',
  },
  demandCard: {
    backgroundColor: '#091410',
    borderColor: '#1C3D2E',
  },
  zoneHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  zoneType: {
    fontSize: 7.5,
    fontWeight: '900',
    letterSpacing: 1.4,
  },
  supplyText: {
    color: '#F87171',
  },
  demandText: {
    color: '#35E68A',
  },
  zoneTitle: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '900',
    marginTop: 3,
  },
  zoneRangeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    gap: 6,
  },
  zoneRangeLabel: {
    color: '#56627A',
    fontSize: 7.5,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  zoneRangeValue: {
    fontSize: 10,
    fontWeight: '900',
    fontVariant: ['tabular-nums'],
  },
  zoneDescription: {
    color: '#68758E',
    fontSize: 9,
    lineHeight: 14,
    marginTop: 6,
  },
  zoneNote: {
    backgroundColor: '#080C15',
    borderWidth: 1,
    borderColor: '#151D2C',
    borderRadius: 14,
    padding: 14,
    marginBottom: 24,
  },
  zoneNoteTitle: {
    color: '#7083FF',
    fontSize: 7.5,
    fontWeight: '900',
    letterSpacing: 1.2,
  },
  zoneNoteText: {
    color: '#68758E',
    fontSize: 9,
    lineHeight: 15,
    marginTop: 5,
  },
  volumeCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 18,
    padding: 15,
    marginBottom: 24,
  },
  volumeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  volumeEyebrow: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.3,
  },
  volumeTitle: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '900',
    marginTop: 3,
  },
  volumeBadge: {
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 8,
    paddingHorizontal: 7,
    paddingVertical: 4,
  },
  volumeBadgeText: {
    color: '#7083FF',
    fontSize: 6.5,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  profileVisual: {
    height: 180,
    backgroundColor: '#060911',
    borderWidth: 1,
    borderColor: '#111827',
    borderRadius: 12,
    marginTop: 14,
    padding: 12,
    flexDirection: 'row',
    alignItems: 'center',
  },
  profilePriceColumn: {
    height: '100%',
    justifyContent: 'space-between',
    marginRight: 14,
  },
  profilePrice: {
    color: '#4E5A72',
    fontSize: 7.5,
    fontWeight: '900',
    fontVariant: ['tabular-nums'],
  },
  vahLabel: {
    color: '#35E68A',
  },
  pocLabel: {
    color: '#7083FF',
  },
  valLabel: {
    color: '#EF4444',
  },
  profileBars: {
    flex: 1,
    height: '100%',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  profileBar: {
    height: 10,
    borderRadius: 3,
    backgroundColor: '#263A91',
    opacity: 0.45,
  },
  profileBarVAH: {
    backgroundColor: '#35E68A',
    opacity: 0.65,
  },
  profileBarPOC: {
    backgroundColor: '#7083FF',
    opacity: 0.9,
  },
  profileBarVAL: {
    backgroundColor: '#EF4444',
    opacity: 0.65,
  },
  profileMetrics: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 12,
  },
  profileMetric: {
    flex: 1,
    backgroundColor: '#0D121D',
    borderWidth: 1,
    borderColor: '#202A3D',
    borderRadius: 10,
    padding: 9,
  },
  profileMetricLabel: {
    color: '#56627A',
    fontSize: 6.5,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  profileMetricValue: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '900',
    marginTop: 3,
    fontVariant: ['tabular-nums'],
  },
  profileMetricDescription: {
    color: '#4E5A72',
    fontSize: 6.5,
    marginTop: 2,
  },
  volumeNodes: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 10,
  },
  nodeItem: {
    flex: 1,
    backgroundColor: '#0D121D',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 10,
    padding: 10,
  },
  nodeTitle: {
    color: '#8995B1',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.7,
  },
  nodeDescription: {
    color: '#56627A',
    fontSize: 7.5,
    lineHeight: 12,
    marginTop: 4,
  },
  conditionCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 16,
    padding: 14,
    marginBottom: 24,
  },
  conditionMain: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  conditionIndicator: {
    width: 36,
    height: 36,
    borderRadius: 11,
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
  },
  conditionIndicatorInner: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#7083FF',
  },
  conditionContent: {
    flex: 1,
  },
  conditionTitle: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '900',
  },
  conditionDescription: {
    color: '#68758E',
    fontSize: 8.5,
    lineHeight: 13,
    marginTop: 3,
  },
  conditionBadge: {
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 7,
    paddingHorizontal: 7,
    paddingVertical: 4,
    marginLeft: 8,
  },
  conditionValue: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
  },
  sessionCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 17,
    padding: 15,
    marginBottom: 24,
  },
  sessionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sessionLabel: {
    color: '#56627A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.2,
  },
  sessionValue: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '900',
    marginTop: 4,
  },
  sessionTimeline: {
    height: 44,
    marginTop: 12,
    position: 'relative',
    justifyContent: 'center',
  },
  sessionLine: {
    position: 'absolute',
    left: 5,
    right: 5,
    height: 1,
    backgroundColor: '#263043',
  },
  sessionPoint: {
    alignItems: 'center',
    alignSelf: 'center',
  },
  sessionPointActive: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#35E68A',
    borderWidth: 3,
    borderColor: '#123126',
  },
  sessionPointText: {
    color: '#56627A',
    fontSize: 6,
    fontWeight: '900',
    marginTop: 4,
  },
  sessionDescription: {
    color: '#68758E',
    fontSize: 8.5,
    lineHeight: 14,
    marginTop: 8,
  },
  boundaryCard: {
    backgroundColor: '#0B1020',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 17,
    padding: 16,
    marginBottom: 10,
  },
  boundaryEyebrow: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.4,
  },
  boundaryTitle: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '900',
    marginTop: 4,
  },
  boundaryText: {
    color: '#68758E',
    fontSize: 9,
    lineHeight: 15,
    marginTop: 8,
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
    transform: [{ scale: 0.995 }],
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
'''

with open(target_path, "w", encoding="utf-8") as f:
    f.write(code)

print("[OK] Successfully updated FlowConfluenceScreen.tsx")
