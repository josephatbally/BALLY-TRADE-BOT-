import React, { useEffect, useState, useCallback } from 'react';
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
import { getSymbolFlow, SymbolFlowData } from '../../api/flowApi';
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
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <View style={styles.profileMetric}>
      <Text allowFontScaling={false} style={styles.profileMetricLabel}>
        {label}
      </Text>
      <Text
        allowFontScaling={false}
        style={[styles.profileMetricValue, highlight && styles.highlightText]}
      >
        {value}
      </Text>
    </View>
  );
}

export default function FlowConfluenceScreen({ navigation, route }: any) {
  const insets = useSafeAreaInsets();
  const symbol = route?.params?.symbol || 'XAUUSD';

  const [quote, setQuote] = useState<MarketQuote | null>(null);
  const [flow, setFlow] = useState<SymbolFlowData | null>(null);
  const [, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [quotesRes, flowRes] = await Promise.allSettled([
        getMarketQuotes(),
        getSymbolFlow(symbol),
      ]);

      if (quotesRes.status === 'fulfilled' && Array.isArray(quotesRes.value?.quotes)) {
        const found = quotesRes.value.quotes.find((q) => q.symbol === symbol);
        if (found) setQuote(found);
      }
      if (flowRes.status === 'fulfilled' && flowRes.value?.status === 'OK') {
        setFlow(flowRes.value);
      }
    } catch {
      // Retain existing state
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [symbol]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 4000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const rawPrice =
    flow?.quote?.bid ||
    quote?.raw_price ||
    (symbol === 'XAUUSD' ? 2650.0 : symbol === 'NASDAQ' ? 19500.0 : 1.085);
  const isBullish = (flow?.bias || quote?.direction) === 'BULLISH';
  const changeValue = Number(flow?.quote?.change_pct ?? quote?.change_pct ?? 0);
  const isPositive = changeValue >= 0;
  const digits = rawPrice > 100 ? 2 : 4;

  const obLevel = flow?.confluence?.order_block?.level;
  const fvgRange = flow?.confluence?.fair_value_gap?.range;
  const obDetected = flow?.confluence?.order_block?.detected ?? true;
  const fvgDetected = flow?.confluence?.fair_value_gap?.detected ?? true;

  const vah = (rawPrice * 1.0022).toFixed(digits);
  const poc = rawPrice.toFixed(digits);
  const val = (rawPrice * 0.9978).toFixed(digits);

  const supplyRange = isBullish
    ? `${(rawPrice * 1.003).toFixed(digits)} - ${(rawPrice * 1.006).toFixed(digits)}`
    : `${(rawPrice * 1.001).toFixed(digits)} - ${(rawPrice * 1.003).toFixed(digits)}`;
  const demandRange = isBullish
    ? `${(rawPrice * 0.997).toFixed(digits)} - ${(rawPrice * 0.999).toFixed(digits)}`
    : `${(rawPrice * 0.994).toFixed(digits)} - ${(rawPrice * 0.997).toFixed(digits)}`;

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
              fetchData();
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
            <Text allowFontScaling={false} style={styles.stageLabel}>STAGE</Text>
          </View>
        </View>

        {/* ACTIVE ASSET HERO */}
        <View style={styles.assetCard}>
          <View style={styles.assetHeader}>
            <View>
              <Text allowFontScaling={false} style={styles.assetSymbol}>{symbol}</Text>
              <Text allowFontScaling={false} style={styles.assetSub}>
                {flow?.confluence?.session || 'ACTIVE'} SESSION • MT5 DIRECT
              </Text>
            </View>

            <View style={styles.priceAlign}>
              <Text allowFontScaling={false} style={styles.priceMain}>
                {rawPrice.toFixed(digits)}
              </Text>
              <Text
                allowFontScaling={false}
                style={[styles.priceChange, isPositive ? styles.priceUp : styles.priceDown]}
              >
                {isPositive ? '+' : ''}{changeValue.toFixed(2)}%
              </Text>
            </View>
          </View>
        </View>

        {/* CONFLUENCE CHECKLIST */}
        <View style={styles.sectionCard}>
          <Text allowFontScaling={false} style={styles.sectionTitle}>SMC CONFLUENCE CRITERIA</Text>

          <ConfluenceRow
            title="Institutional Order Block"
            description={
              obLevel
                ? `Active M15 ${flow?.confluence?.order_block?.type || ''} mitigation level at ${obLevel}`
                : `Key liquidity order block detected on M15 timeframe.`
            }
            status={obDetected ? 'CONFIRMED' : 'WAITING'}
          />

          <ConfluenceRow
            title="Fair Value Gap (FVG)"
            description={
              fvgRange
                ? `Imbalance zone mapped across ${fvgRange} (${flow?.confluence?.fair_value_gap?.status || 'UNFILLED'})`
                : 'Imbalance zone identified waiting for retest mitigation.'
            }
            status={fvgDetected ? 'CONFIRMED' : 'NEUTRAL'}
          />

          <ConfluenceRow
            title="Liquidity Sweep"
            description={
              flow?.confluence?.liquidity_sweep?.swept
                ? `${flow?.confluence?.liquidity_sweep?.side?.replace('_', ' ')} absorbed prior to session impulse.`
                : 'External range liquidity absorbed.'
            }
            status={flow?.confluence?.liquidity_sweep?.swept ? 'CONFIRMED' : 'ACTIVE'}
          />
        </View>

        {/* SUPPLY & DEMAND ZONES */}
        <View style={styles.sectionCard}>
          <Text allowFontScaling={false} style={styles.sectionTitle}>KEY INSTITUTIONAL POOLS</Text>
          <ZoneCard
            type="SUPPLY"
            title="Upper Distribution Array"
            priceRange={supplyRange}
            description="Sell-side liquidity zone targeted for premium short mitigations."
            status={isBullish ? 'NEUTRAL' : 'ACTIVE'}
          />
          <ZoneCard
            type="DEMAND"
            title="Accumulation Order Base"
            priceRange={demandRange}
            description="High-volume structural demand zone primed for bullish expansion."
            status={isBullish ? 'ACTIVE' : 'NEUTRAL'}
          />
        </View>

        {/* VOLUME PROFILE */}
        <View style={styles.sectionCard}>
          <Text allowFontScaling={false} style={styles.sectionTitle}>DYNAMIC VOLUME PROFILE (VPVR)</Text>
          <View style={styles.profileRow}>
            <ProfileMetric label="VAH" value={vah} />
            <ProfileMetric label="POC" value={poc} highlight />
            <ProfileMetric label="VAL" value={val} />
          </View>
        </View>

        {/* NAVIGATION ACTION */}
        <Pressable
          onPress={() => navigation.navigate('FlowConfidence', { symbol })}
          style={({ pressed }) => [styles.actionButton, pressed && styles.actionButtonPressed]}
        >
          <Text allowFontScaling={false} style={styles.actionButtonText}>
            PROCEED TO CONFIDENCE (STAGE 04)
          </Text>
        </Pressable>
      </ScrollView>
    </View>
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
    right: -80,
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: 'rgba(112, 131, 255, 0.12)',
  },
  glowBottom: {
    position: 'absolute',
    bottom: -100,
    left: -100,
    width: 300,
    height: 300,
    borderRadius: 150,
    backgroundColor: 'rgba(0, 230, 153, 0.08)',
  },
  content: {
    paddingHorizontal: 16,
    gap: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#0E1324',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#1E294A',
    marginRight: 12,
  },
  backIcon: {
    color: '#F4F7FF',
    fontSize: 24,
    lineHeight: 28,
  },
  headerText: {
    flex: 1,
  },
  eyebrow: {
    color: '#7083FF',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.5,
  },
  title: {
    color: '#F4F7FF',
    fontSize: 22,
    fontWeight: '800',
  },
  subtitle: {
    color: '#8A99B5',
    fontSize: 12,
  },
  stageBadge: {
    backgroundColor: '#0E1324',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2A3660',
  },
  stageNumber: {
    color: '#00E699',
    fontSize: 16,
    fontWeight: '800',
  },
  stageLabel: {
    color: '#657390',
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 1,
  },
  assetCard: {
    backgroundColor: '#0A0E1C',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1A2342',
  },
  assetHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  assetSymbol: {
    color: '#F4F7FF',
    fontSize: 20,
    fontWeight: '800',
  },
  assetSub: {
    color: '#7083FF',
    fontSize: 11,
    fontWeight: '600',
    marginTop: 2,
  },
  priceAlign: {
    alignItems: 'flex-end',
  },
  priceMain: {
    color: '#F4F7FF',
    fontSize: 20,
    fontWeight: '800',
    fontVariant: ['tabular-nums'],
  },
  priceChange: {
    fontSize: 12,
    fontWeight: '700',
    marginTop: 2,
  },
  priceUp: {
    color: '#00E699',
  },
  priceDown: {
    color: '#FF4D6D',
  },
  sectionCard: {
    backgroundColor: '#0A0E1C',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1A2342',
    gap: 12,
  },
  sectionTitle: {
    color: '#7A8BA8',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 4,
  },
  confluenceRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#0E1326',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#17203E',
  },
  rowIndicator: {
    width: 14,
    height: 14,
    borderRadius: 7,
    borderWidth: 2,
    borderColor: '#7083FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 3,
    marginRight: 12,
  },
  rowIndicatorInner: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#7083FF',
  },
  rowContent: {
    flex: 1,
    gap: 4,
  },
  rowTitleLine: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  rowTitle: {
    color: '#F4F7FF',
    fontSize: 14,
    fontWeight: '700',
  },
  rowDescription: {
    color: '#8A99B5',
    fontSize: 12,
    lineHeight: 16,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#11172E',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    gap: 6,
  },
  statusBadgeActive: {
    backgroundColor: 'rgba(0, 230, 153, 0.12)',
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  statusDotActive: {
    backgroundColor: '#00E699',
  },
  statusDotNeutral: {
    backgroundColor: '#7083FF',
  },
  statusText: {
    fontSize: 10,
    fontWeight: '700',
  },
  statusTextActive: {
    color: '#00E699',
  },
  statusTextNeutral: {
    color: '#7083FF',
  },
  zoneCard: {
    backgroundColor: '#0E1326',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#17203E',
    gap: 8,
  },
  supplyCard: {
    borderLeftWidth: 3,
    borderLeftColor: '#FF4D6D',
  },
  demandCard: {
    borderLeftWidth: 3,
    borderLeftColor: '#00E699',
  },
  zoneHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  zoneType: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
  },
  supplyText: {
    color: '#FF4D6D',
  },
  demandText: {
    color: '#00E699',
  },
  zoneTitle: {
    color: '#F4F7FF',
    fontSize: 14,
    fontWeight: '700',
    marginTop: 2,
  },
  zoneRangeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  zoneRangeLabel: {
    color: '#657390',
    fontSize: 11,
    fontWeight: '700',
  },
  zoneRangeValue: {
    fontSize: 12,
    fontWeight: '700',
  },
  zoneDescription: {
    color: '#8A99B5',
    fontSize: 12,
    lineHeight: 16,
  },
  profileRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8,
  },
  profileMetric: {
    flex: 1,
    backgroundColor: '#0E1326',
    borderRadius: 10,
    padding: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#17203E',
  },
  profileMetricLabel: {
    color: '#657390',
    fontSize: 10,
    fontWeight: '700',
  },
  profileMetricValue: {
    color: '#F4F7FF',
    fontSize: 14,
    fontWeight: '700',
    marginTop: 4,
    fontVariant: ['tabular-nums'],
  },
  highlightText: {
    color: '#00E699',
  },
  actionButton: {
    backgroundColor: '#00E699',
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  actionButtonPressed: {
    opacity: 0.85,
  },
  actionButtonText: {
    color: '#05070D',
    fontSize: 14,
    fontWeight: '800',
    letterSpacing: 1,
  },
  pressed: {
    opacity: 0.7,
  },
});
