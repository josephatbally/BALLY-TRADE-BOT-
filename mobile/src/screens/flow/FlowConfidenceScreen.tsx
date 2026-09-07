
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

type ConfidenceLevel = 'HIGH' | 'MODERATE' | 'LOW';

function ConfidenceBadge({
  level,
}: {
  level: ConfidenceLevel;
}) {
  const isHigh = level === 'HIGH';
  const isModerate = level === 'MODERATE';

  return (
    <View
      style={[
        styles.badge,
        isHigh && styles.badgeHigh,
        isModerate && styles.badgeModerate,
      ]}
    >
      <View
        style={[
          styles.badgeDot,
          isHigh && styles.badgeDotHigh,
          isModerate && styles.badgeDotModerate,
        ]}
      />

      <Text
        style={[
          styles.badgeText,
          isHigh && styles.badgeTextHigh,
          isModerate && styles.badgeTextModerate,
        ]}
      >
        {level}
      </Text>
    </View>
  );
}

function ComponentBar({
  title,
  description,
  value,
}: {
  title: string;
  description: string;
  value: string;
}) {
  return (
    <View style={styles.componentRow}>
      <View style={styles.componentHeader}>
        <View style={styles.componentText}>
          <Text style={styles.componentTitle}>{title}</Text>

          <Text style={styles.componentDescription}>
            {description}
          </Text>
        </View>

        <Text style={styles.componentValue}>{value}</Text>
      </View>

      <View style={styles.progressTrack}>
        <View
          style={[
            styles.progressFill,
            {
              width:
                value === '—'
                  ? '0%'
                  : `${Math.min(
                      100,
                      Math.max(
                        0,
                        Number(value.replace('%', '')),
                      ),
                    )}%`,
            },
          ]}
        />
      </View>
    </View>
  );
}

export default function FlowConfidenceScreen({
  navigation,
  route,
}: any) {
  const insets = useSafeAreaInsets();

  const symbol = route?.params?.symbol || 'XAUUSD';

  const handleDecision = () => {
    navigation.navigate('FlowDecision', {
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
            <Text style={styles.eyebrow}>BALLY FLOW</Text>

            <Text style={styles.title}>Confidence</Text>

            <Text style={styles.subtitle}>
              AI assessment of confluence quality
            </Text>
          </View>

          <View style={styles.stageBadge}>
            <Text style={styles.stageNumber}>04</Text>

            <Text style={styles.stageLabel}>
              CONFIDENCE
            </Text>
          </View>
        </View>

        {/* MARKET */}
        <View style={styles.marketCard}>
          <View style={styles.marketHeader}>
            <Text style={styles.marketLabel}>
              ACTIVE MARKET
            </Text>

            <ConfidenceBadge level="MODERATE" />
          </View>

          <View style={styles.marketRow}>
            <View>
              <Text style={styles.marketSymbol}>
                {symbol}
              </Text>

              <Text style={styles.marketDescription}>
                Confidence assessment target
              </Text>
            </View>

            <View style={styles.assessmentBadge}>
              <Text style={styles.assessmentText}>
                AI ASSESSMENT
              </Text>
            </View>
          </View>
        </View>

        {/* MAIN CONFIDENCE */}
        <View style={styles.confidenceCard}>
          <View style={styles.confidenceHeader}>
            <View>
              <Text style={styles.confidenceEyebrow}>
                AI CONFIDENCE
              </Text>

              <Text style={styles.confidenceTitle}>
                Overall Assessment
              </Text>
            </View>

            <View style={styles.stageIndicator}>
              <Text style={styles.stageIndicatorNumber}>
                04
              </Text>
            </View>
          </View>

          <View style={styles.confidenceCenter}>
            <View style={styles.confidenceRing}>
              <Text style={styles.confidenceValue}>
                —
              </Text>

              <Text style={styles.confidencePercent}>
                / 100
              </Text>
            </View>

            <ConfidenceBadge level="MODERATE" />

            <Text style={styles.confidenceState}>
              AWAITING LIVE ENGINE DATA
            </Text>
          </View>

          <Text style={styles.confidenceExplanation}>
            Confidence is calculated from technical intelligence
            and market-condition context. It is an assessment
            of signal quality, not a standalone trade instruction.
          </Text>
        </View>

        {/* MODEL ARCHITECTURE */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              CONFIDENCE MODEL
            </Text>

            <Text style={styles.sectionSubtitle}>
              Authoritative backend weighting
            </Text>
          </View>

          <Text style={styles.sectionNumber}>01</Text>
        </View>

        <View style={styles.modelCard}>
          <View style={styles.modelHeader}>
            <View>
              <Text style={styles.modelTitle}>
                Technical Intelligence
              </Text>

              <Text style={styles.modelDescription}>
                SMC and confluence evidence
              </Text>
            </View>

            <Text style={styles.modelWeight}>70%</Text>
          </View>

          <View style={styles.weightTrack}>
            <View
              style={[
                styles.weightFill,
                {width: '70%'},
              ]}
            />
          </View>

          <View style={styles.modelHeader}>
            <View>
              <Text style={styles.modelTitle}>
                Market Conditions
              </Text>

              <Text style={styles.modelDescription}>
                Volatility and contextual conditions
              </Text>
            </View>

            <Text style={styles.modelWeight}>30%</Text>
          </View>

          <View style={styles.weightTrack}>
            <View
              style={[
                styles.weightFillSecondary,
                {width: '30%'},
              ]}
            />
          </View>

          <View style={styles.modelFormula}>
            <Text style={styles.formulaText}>
              TECHNICAL × 70% + CONDITIONS × 30%
            </Text>
          </View>
        </View>

        {/* COMPONENTS */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              ASSESSMENT COMPONENTS
            </Text>

            <Text style={styles.sectionSubtitle}>
              Inputs contributing to confidence
            </Text>
          </View>

          <Text style={styles.sectionNumber}>02</Text>
        </View>

        <View style={styles.componentsCard}>
          <ComponentBar
            title="SMC Confluence"
            description="Structure, liquidity and SMC evidence"
            value="—"
          />

          <ComponentBar
            title="Supply & Demand"
            description="Relevant institutional zones"
            value="—"
          />

          <ComponentBar
            title="Volume Profile"
            description="Volume acceptance and distribution"
            value="—"
          />

          <ComponentBar
            title="Volatility"
            description="Current movement conditions"
            value="—"
          />

          <ComponentBar
            title="Market Session"
            description="Current trading-session context"
            value="—"
          />
        </View>

        {/* INTERPRETATION */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              CONFIDENCE INTERPRETATION
            </Text>

            <Text style={styles.sectionSubtitle}>
              How the assessment should be understood
            </Text>
          </View>

          <Text style={styles.sectionNumber}>03</Text>
        </View>

        <View style={styles.interpretationCard}>
          <View style={styles.interpretationRow}>
            <View
              style={[
                styles.interpretationIndicator,
                styles.highIndicator,
              ]}
            />

            <View style={styles.interpretationContent}>
              <Text style={styles.interpretationTitle}>
                HIGH
              </Text>

              <Text style={styles.interpretationText}>
                Strong alignment across the evaluated intelligence
                layers.
              </Text>
            </View>
          </View>

          <View style={styles.interpretationRow}>
            <View
              style={[
                styles.interpretationIndicator,
                styles.moderateIndicator,
              ]}
            />

            <View style={styles.interpretationContent}>
              <Text style={styles.interpretationTitle}>
                MODERATE
              </Text>

              <Text style={styles.interpretationText}>
                Some evidence is aligned while other conditions
                remain mixed or incomplete.
              </Text>
            </View>
          </View>

          <View style={styles.interpretationRow}>
            <View
              style={[
                styles.interpretationIndicator,
                styles.lowIndicator,
              ]}
            />

            <View style={styles.interpretationContent}>
              <Text style={styles.interpretationTitle}>
                LOW
              </Text>

              <Text style={styles.interpretationText}>
                Insufficient alignment for a strong confidence
                assessment.
              </Text>
            </View>
          </View>
        </View>

        {/* DECISION BOUNDARY */}
        <View style={styles.boundaryCard}>
          <Text style={styles.boundaryEyebrow}>
            STAGE 04 COMPLETE
          </Text>

          <Text style={styles.boundaryTitle}>
            Confidence → Decision
          </Text>

          <Text style={styles.boundaryText}>
            The confidence assessment is passed to Stage 05.
            BUY, SELL or NO TRADE must be determined by the
            decision engine rather than by this screen.
          </Text>
        </View>
      </ScrollView>

      {/* NEXT */}
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
          onPress={handleDecision}
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
              DECISION
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

  marketDescription: {
    color: '#69758D',
    fontSize: 10,
    marginTop: 4,
  },

  assessmentBadge: {
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 9,
    paddingHorizontal: 9,
    paddingVertical: 6,
  },

  assessmentText: {
    color: '#7083FF',
    fontSize: 6.5,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 8,
    backgroundColor: '#0D121D',
    borderWidth: 1,
    borderColor: '#202A3D',
  },

  badgeHigh: {
    backgroundColor: '#0A1713',
    borderColor: '#203A32',
  },

  badgeModerate: {
    backgroundColor: '#15120A',
    borderColor: '#3B321B',
  },

  badgeDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    marginRight: 5,
    backgroundColor: '#56627A',
  },

  badgeDotHigh: {
    backgroundColor: '#35E68A',
  },

  badgeDotModerate: {
    backgroundColor: '#D9B95C',
  },

  badgeText: {
    color: '#68758E',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  badgeTextHigh: {
    color: '#35E68A',
  },

  badgeTextModerate: {
    color: '#D9B95C',
  },

  confidenceCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 20,
    padding: 18,
    marginBottom: 26,
  },

  confidenceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },

  confidenceEyebrow: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.5,
  },

  confidenceTitle: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '900',
    marginTop: 3,
  },

  stageIndicator: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    alignItems: 'center',
    justifyContent: 'center',
  },

  stageIndicatorNumber: {
    color: '#7083FF',
    fontSize: 8,
    fontWeight: '900',
  },

  confidenceCenter: {
    alignItems: 'center',
    marginTop: 20,
  },

  confidenceRing: {
    width: 148,
    height: 148,
    borderRadius: 74,
    borderWidth: 9,
    borderColor: '#1C285E',
    backgroundColor: '#080C15',
    alignItems: 'center',
    justifyContent: 'center',
  },

  confidenceValue: {
    color: '#FFFFFF',
    fontSize: 40,
    fontWeight: '900',
  },

  confidencePercent: {
    color: '#56627A',
    fontSize: 8,
    fontWeight: '800',
    marginTop: -3,
  },

  confidenceState: {
    color: '#56627A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.1,
    marginTop: 9,
  },

  confidenceExplanation: {
    color: '#68758E',
    fontSize: 9.5,
    lineHeight: 15,
    textAlign: 'center',
    marginTop: 17,
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

  modelCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 17,
    padding: 15,
    marginBottom: 25,
  },

  modelHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  modelTitle: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '900',
  },

  modelDescription: {
    color: '#68758E',
    fontSize: 8,
    marginTop: 3,
  },

  modelWeight: {
    color: '#7083FF',
    fontSize: 15,
    fontWeight: '900',
  },

  weightTrack: {
    height: 6,
    borderRadius: 3,
    backgroundColor: '#141B2A',
    overflow: 'hidden',
    marginTop: 9,
    marginBottom: 16,
  },

  weightFill: {
    height: '100%',
    borderRadius: 3,
    backgroundColor: '#334BFF',
  },

  weightFillSecondary: {
    height: '100%',
    borderRadius: 3,
    backgroundColor: '#59678B',
  },

  modelFormula: {
    backgroundColor: '#080C15',
    borderWidth: 1,
    borderColor: '#151D2C',
    borderRadius: 9,
    padding: 10,
    alignItems: 'center',
  },

  formulaText: {
    color: '#68758E',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  componentsCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 17,
    padding: 14,
    marginBottom: 25,
  },

  componentRow: {
    marginBottom: 17,
  },

  componentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  componentText: {
    flex: 1,
    paddingRight: 10,
  },

  componentTitle: {
    color: '#FFFFFF',
    fontSize: 9.5,
    fontWeight: '900',
  },

  componentDescription: {
    color: '#68758E',
    fontSize: 7.5,
    marginTop: 3,
  },

  componentValue: {
    color: '#68758E',
    fontSize: 10,
    fontWeight: '900',
  },

  progressTrack: {
    height: 5,
    borderRadius: 3,
    backgroundColor: '#141B2A',
    overflow: 'hidden',
    marginTop: 8,
  },

  progressFill: {
    height: '100%',
    borderRadius: 3,
    backgroundColor: '#334BFF',
  },

  interpretationCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 17,
    padding: 14,
    marginBottom: 25,
  },

  interpretationRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#111827',
  },

  interpretationIndicator: {
    width: 9,
    height: 9,
    borderRadius: 5,
    marginTop: 3,
    marginRight: 10,
  },

  highIndicator: {
    backgroundColor: '#35E68A',
  },

  moderateIndicator: {
    backgroundColor: '#D9B95C',
  },

  lowIndicator: {
    backgroundColor: '#56627A',
  },

  interpretationContent: {
    flex: 1,
  },

  interpretationTitle: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '900',
  },

  interpretationText: {
    color: '#68758E',
    fontSize: 8.5,
    lineHeight: 13,
    marginTop: 3,
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
