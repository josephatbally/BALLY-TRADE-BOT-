
import React from 'react';
import {
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {useSafeAreaInsets} from 'react-native-safe-area-context';

type ConfluenceStatus = 'CONFIRMED' | 'ACTIVE' | 'NEUTRAL' | 'WAITING';

function StatusBadge({
  status,
}: {
  status: ConfluenceStatus;
}) {
  const confirmed =
    status === 'CONFIRMED' || status === 'ACTIVE';

  return (
    <View
      style={[
        styles.statusBadge,
        confirmed && styles.statusBadgeActive,
      ]}
    >
      <View
        style={[
          styles.statusDot,
          confirmed
            ? styles.statusDotActive
            : styles.statusDotNeutral,
        ]}
      />

      <Text
        style={[
          styles.statusText,
          confirmed
            ? styles.statusTextActive
            : styles.statusTextNeutral,
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
          <Text style={styles.rowTitle}>{title}</Text>

          <StatusBadge status={status} />
        </View>

        <Text style={styles.rowDescription}>
          {description}
        </Text>
      </View>
    </View>
  );
}

function ZoneCard({
  type,
  title,
  description,
  status,
}: {
  type: 'SUPPLY' | 'DEMAND';
  title: string;
  description: string;
  status: ConfluenceStatus;
}) {
  const supply = type === 'SUPPLY';

  return (
    <View
      style={[
        styles.zoneCard,
        supply
          ? styles.supplyCard
          : styles.demandCard,
      ]}
    >
      <View style={styles.zoneHeader}>
        <View>
          <Text
            style={[
              styles.zoneType,
              supply
                ? styles.supplyText
                : styles.demandText,
            ]}
          >
            {type} ZONE
          </Text>

          <Text style={styles.zoneTitle}>
            {title}
          </Text>
        </View>

        <StatusBadge status={status} />
      </View>

      <Text style={styles.zoneDescription}>
        {description}
      </Text>
    </View>
  );
}

function ProfileMetric({
  label,
  value,
  description,
}: {
  label: string;
  value: string;
  description: string;
}) {
  return (
    <View style={styles.profileMetric}>
      <Text style={styles.profileMetricLabel}>
        {label}
      </Text>

      <Text style={styles.profileMetricValue}>
        {value}
      </Text>

      <Text style={styles.profileMetricDescription}>
        {description}
      </Text>
    </View>
  );
}

export default function FlowConfluenceScreen({
  navigation,
  route,
}: any) {
  const insets = useSafeAreaInsets();

  const symbol = route?.params?.symbol || 'XAUUSD';

  const handleConfidence = () => {
    navigation.navigate('FlowConfidence', {
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
              Confluence
            </Text>

            <Text style={styles.subtitle}>
              Multi-layer market intelligence
            </Text>
          </View>

          <View style={styles.stageBadge}>
            <Text style={styles.stageNumber}>
              03
            </Text>

            <Text style={styles.stageLabel}>
              CONFLUENCE
            </Text>
          </View>
        </View>

        {/* MARKET */}
        <View style={styles.marketCard}>
          <View style={styles.marketHeader}>
            <Text style={styles.marketLabel}>
              ANALYSIS MARKET
            </Text>

            <StatusBadge status="ACTIVE" />
          </View>

          <View style={styles.marketRow}>
            <View>
              <Text style={styles.marketSymbol}>
                {symbol}
              </Text>

              <Text style={styles.marketName}>
                Confluence evaluation target
              </Text>
            </View>

            <View style={styles.multiLayerBadge}>
              <Text style={styles.multiLayerText}>
                MULTI-LAYER
              </Text>
            </View>
          </View>
        </View>

        {/* CONFLUENCE OVERVIEW */}
        <View style={styles.overviewCard}>
          <View style={styles.overviewHeader}>
            <View>
              <Text style={styles.overviewEyebrow}>
                STAGE 03
              </Text>

              <Text style={styles.overviewTitle}>
                Confluence Intelligence
              </Text>
            </View>

            <View style={styles.layerCount}>
              <Text style={styles.layerCountNumber}>
                05
              </Text>

              <Text style={styles.layerCountLabel}>
                LAYERS
              </Text>
            </View>
          </View>

          <Text style={styles.overviewText}>
            BALLY FLOW brings multiple market perspectives
            together before confidence and decision processing.
            These components provide evidence and context;
            they do not independently create a trade decision.
          </Text>

          <View style={styles.layerPills}>
            <View style={styles.layerPill}>
              <Text style={styles.layerPillText}>
                SMC
              </Text>
            </View>

            <View style={styles.layerPill}>
              <Text style={styles.layerPillText}>
                S&D
              </Text>
            </View>

            <View style={styles.layerPill}>
              <Text style={styles.layerPillText}>
                VOLUME
              </Text>
            </View>

            <View style={styles.layerPill}>
              <Text style={styles.layerPillText}>
                VOLATILITY
              </Text>
            </View>

            <View style={styles.layerPill}>
              <Text style={styles.layerPillText}>
                SESSION
              </Text>
            </View>
          </View>
        </View>

        {/* SMC */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              SMC ANALYSIS
            </Text>

            <Text style={styles.sectionSubtitle}>
              Smart Money Concepts structural context
            </Text>
          </View>

          <Text style={styles.sectionNumber}>
            01
          </Text>
        </View>

        <View style={styles.sectionCard}>
          <ConfluenceRow
            title="Market Structure"
            description="Higher and lower timeframe structural relationship."
            status="CONFIRMED"
          />

          <ConfluenceRow
            title="Break of Structure"
            description="Detected structural displacement and directional context."
            status="ACTIVE"
          />

          <ConfluenceRow
            title="CHoCH"
            description="Potential change in market structure context."
            status="NEUTRAL"
          />

          <ConfluenceRow
            title="Liquidity Pools"
            description="Relevant areas where resting liquidity may exist."
            status="ACTIVE"
          />

          <ConfluenceRow
            title="Liquidity Sweeps"
            description="Liquidity interaction identified by the backend."
            status="NEUTRAL"
          />

          <ConfluenceRow
            title="Order Blocks"
            description="Institutional price areas identified by the SMC engine."
            status="ACTIVE"
          />

          <ConfluenceRow
            title="Fair Value Gaps"
            description="Price imbalance areas relevant to current structure."
            status="NEUTRAL"
          />

          <ConfluenceRow
            title="Premium / Discount"
            description="Current price position within the analyzed range."
            status="ACTIVE"
          />
        </View>

        {/* SUPPLY & DEMAND */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              SUPPLY & DEMAND
            </Text>

            <Text style={styles.sectionSubtitle}>
              Relevant institutional supply and demand zones
            </Text>
          </View>

          <Text style={styles.sectionNumber}>
            02
          </Text>
        </View>

        <View style={styles.zoneList}>
          <ZoneCard
            type="SUPPLY"
            title="Active Supply Area"
            description="Supply-zone state supplied by the market-analysis backend."
            status="ACTIVE"
          />

          <ZoneCard
            type="DEMAND"
            title="Active Demand Area"
            description="Demand-zone state supplied by the market-analysis backend."
            status="ACTIVE"
          />
        </View>

        <View style={styles.zoneNote}>
          <Text style={styles.zoneNoteTitle}>
            ZONE STATUS
          </Text>

          <Text style={styles.zoneNoteText}>
            Zones can be evaluated as active, tested or broken
            according to authoritative backend analysis. The
            mobile interface does not independently classify
            supply or demand.
          </Text>
        </View>

        {/* VOLUME PROFILE */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              VOLUME PROFILE
            </Text>

            <Text style={styles.sectionSubtitle}>
              Volume distribution and market acceptance context
            </Text>
          </View>

          <Text style={styles.sectionNumber}>
            03
          </Text>
        </View>

        <View style={styles.volumeCard}>
          <View style={styles.volumeHeader}>
            <View>
              <Text style={styles.volumeEyebrow}>
                PROFILE STRUCTURE
              </Text>

              <Text style={styles.volumeTitle}>
                Market Volume Map
              </Text>
            </View>

            <View style={styles.volumeBadge}>
              <Text style={styles.volumeBadgeText}>
                ANALYSIS
              </Text>
            </View>
          </View>

          {/* PROFILE VISUAL */}
          <View style={styles.profileVisual}>
            <View style={styles.profilePriceColumn}>
              <Text style={styles.profilePrice}>
                HIGH
              </Text>

              <Text style={styles.profilePrice}>
                VAH
              </Text>

              <Text style={styles.profilePrice}>
                POC
              </Text>

              <Text style={styles.profilePrice}>
                VAL
              </Text>

              <Text style={styles.profilePrice}>
                LOW
              </Text>
            </View>

            <View style={styles.profileBars}>
              <View style={[styles.profileBar, {width: '42%'}]} />
              <View style={[styles.profileBar, {width: '58%'}]} />
              <View style={[styles.profileBar, {width: '76%'}]} />
              <View style={[styles.profileBar, {width: '92%'}]} />
              <View style={[styles.profileBar, {width: '68%'}]} />
              <View style={[styles.profileBar, {width: '82%'}]} />
              <View style={[styles.profileBar, {width: '54%'}]} />
              <View style={[styles.profileBar, {width: '34%'}]} />
              <View style={[styles.profileBar, {width: '48%'}]} />
              <View style={[styles.profileBar, {width: '27%'}]} />
            </View>
          </View>

          <View style={styles.profileMetrics}>
            <ProfileMetric
              label="POC"
              value="—"
              description="Point of Control"
            />

            <ProfileMetric
              label="VAH"
              value="—"
              description="Value Area High"
            />

            <ProfileMetric
              label="VAL"
              value="—"
              description="Value Area Low"
            />
          </View>

          <View style={styles.volumeNodes}>
            <View style={styles.nodeItem}>
              <Text style={styles.nodeTitle}>
                HIGH VOLUME
              </Text>

              <Text style={styles.nodeDescription}>
                Areas of stronger traded-volume concentration.
              </Text>
            </View>

            <View style={styles.nodeItem}>
              <Text style={styles.nodeTitle}>
                LOW VOLUME
              </Text>

              <Text style={styles.nodeDescription}>
                Areas of lighter volume and weaker acceptance.
              </Text>
            </View>
          </View>
        </View>

        {/* VOLATILITY */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              VOLATILITY
            </Text>

            <Text style={styles.sectionSubtitle}>
              Current market movement conditions
            </Text>
          </View>

          <Text style={styles.sectionNumber}>
            04
          </Text>
        </View>

        <View style={styles.conditionCard}>
          <View style={styles.conditionMain}>
            <View style={styles.conditionIndicator}>
              <View style={styles.conditionIndicatorInner} />
            </View>

            <View style={styles.conditionContent}>
              <Text style={styles.conditionTitle}>
                MARKET VOLATILITY
              </Text>

              <Text style={styles.conditionDescription}>
                Volatility is supplied as market-condition
                intelligence and contributes to the overall
                confidence assessment.
              </Text>
            </View>

            <Text style={styles.conditionValue}>
              LIVE
            </Text>
          </View>
        </View>

        {/* SESSION */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              MARKET SESSION
            </Text>

            <Text style={styles.sectionSubtitle}>
              Current trading-session context
            </Text>
          </View>

          <Text style={styles.sectionNumber}>
            05
          </Text>
        </View>

        <View style={styles.sessionCard}>
          <View style={styles.sessionHeader}>
            <View>
              <Text style={styles.sessionLabel}>
                CURRENT SESSION
              </Text>

              <Text style={styles.sessionValue}>
                LIVE MARKET CONTEXT
              </Text>
            </View>

            <StatusBadge status="ACTIVE" />
          </View>

          <View style={styles.sessionTimeline}>
            <View style={styles.sessionLine} />

            <View style={styles.sessionPoint}>
              <View style={styles.sessionPointActive} />

              <Text style={styles.sessionPointText}>
                SESSION
              </Text>
            </View>
          </View>

          <Text style={styles.sessionDescription}>
            Session information is used as contextual market
            intelligence and is passed into the confidence
            stage rather than creating a standalone trade signal.
          </Text>
        </View>

        {/* CONFLUENCE BOUNDARY */}
        <View style={styles.boundaryCard}>
          <Text style={styles.boundaryEyebrow}>
            CONFLUENCE COMPLETE
          </Text>

          <Text style={styles.boundaryTitle}>
            Evidence → Confidence
          </Text>

          <Text style={styles.boundaryText}>
            The combined confluence information now moves into
            Stage 04, where the confidence engine evaluates
            technical intelligence together with market
            conditions.
          </Text>
        </View>
      </ScrollView>

      {/* NEXT STAGE */}
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
          onPress={handleConfidence}
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
              CONFIDENCE
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
    padding: 18,
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
    marginTop: 13,
  },

  marketSymbol: {
    color: '#FFFFFF',
    fontSize: 26,
    fontWeight: '900',
    letterSpacing: 1,
  },

  marketName: {
    color: '#69758D',
    fontSize: 10,
    marginTop: 4,
  },

  multiLayerBadge: {
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 9,
    paddingHorizontal: 9,
    paddingVertical: 6,
  },

  multiLayerText: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 7,
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
    fontSize: 6,
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
    padding: 17,
    marginBottom: 26,
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
    color: '#68758E',
    fontSize: 6.5,
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
    marginTop: 4,
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
    padding: 12,
    marginBottom: 25,
  },

  confluenceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 11,
    borderBottomWidth: 1,
    borderBottomColor: '#111827',
  },

  rowIndicator: {
    width: 30,
    height: 30,
    borderRadius: 10,
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
    fontSize: 9.5,
    fontWeight: '900',
  },

  rowDescription: {
    color: '#68758E',
    fontSize: 8.5,
    lineHeight: 13,
    marginTop: 3,
    paddingRight: 5,
  },

  zoneList: {
    marginBottom: 10,
  },

  zoneCard: {
    borderWidth: 1,
    borderRadius: 16,
    padding: 15,
    marginBottom: 9,
  },

  supplyCard: {
    backgroundColor: '#120D14',
    borderColor: '#332031',
  },

  demandCard: {
    backgroundColor: '#09130F',
    borderColor: '#1C3429',
  },

  zoneHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  zoneType: {
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.4,
  },

  supplyText: {
    color: '#B97B91',
  },

  demandText: {
    color: '#58B88A',
  },

  zoneTitle: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '900',
    marginTop: 4,
  },

  zoneDescription: {
    color: '#68758E',
    fontSize: 9,
    lineHeight: 14,
    marginTop: 8,
  },

  zoneNote: {
    backgroundColor: '#080C15',
    borderWidth: 1,
    borderColor: '#151D2C',
    borderRadius: 14,
    padding: 14,
    marginBottom: 25,
  },

  zoneNoteTitle: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.2,
  },

  zoneNoteText: {
    color: '#68758E',
    fontSize: 9,
    lineHeight: 15,
    marginTop: 6,
  },

  volumeCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 18,
    padding: 15,
    marginBottom: 25,
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
    paddingVertical: 5,
  },

  volumeBadgeText: {
    color: '#7083FF',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  profileVisual: {
    height: 190,
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
    marginRight: 12,
  },

  profilePrice: {
    color: '#4E5A72',
    fontSize: 6.5,
    fontWeight: '900',
  },

  profileBars: {
    flex: 1,
    height: '100%',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
  },

  profileBar: {
    height: 10,
    borderRadius: 3,
    backgroundColor: '#334BFF',
    opacity: 0.45,
  },

  profileMetrics: {
    flexDirection: 'row',
    gap: 7,
    marginTop: 10,
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
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  profileMetricValue: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '900',
    marginTop: 4,
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
    marginBottom: 25,
  },

  conditionMain: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  conditionIndicator: {
    width: 37,
    height: 37,
    borderRadius: 12,
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
    marginTop: 4,
  },

  conditionValue: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
    marginLeft: 8,
  },

  sessionCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 17,
    padding: 15,
    marginBottom: 25,
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
    height: 50,
    marginTop: 15,
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
    marginTop: 5,
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
