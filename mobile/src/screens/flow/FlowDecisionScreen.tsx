
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

type Decision = 'BUY' | 'SELL' | 'NO TRADE';

const decision: Decision = 'NO TRADE';

const decisionReasons = [
  'Awaiting authoritative decision-engine output',
  'Technical and market-condition inputs must be evaluated by the backend',
  'No frontend-generated trading decision is permitted',
];

const decisionStates = [
  {
    title: 'BUY',
    description: 'Bullish trade decision from the backend',
  },
  {
    title: 'SELL',
    description: 'Bearish trade decision from the backend',
  },
  {
    title: 'NO TRADE',
    description: 'Conditions do not authorize a trade',
  },
];

function getDecisionStyles(value: Decision) {
  switch (value) {
    case 'BUY':
      return {
        border: styles.buyBorder,
        background: styles.buyBackground,
        text: styles.buyText,
        dot: styles.buyDot,
      };

    case 'SELL':
      return {
        border: styles.sellBorder,
        background: styles.sellBackground,
        text: styles.sellText,
        dot: styles.sellDot,
      };

    default:
      return {
        border: styles.neutralBorder,
        background: styles.neutralBackground,
        text: styles.neutralText,
        dot: styles.neutralDot,
      };
  }
}

export default function FlowDecisionScreen({
  navigation,
  route,
}: any) {
  const insets = useSafeAreaInsets();

  const symbol = route?.params?.symbol || 'XAUUSD';

  const activeStyles = getDecisionStyles(decision);

  const handleValidation = () => {
    navigation.navigate('FlowValidation', {
      symbol,
      decision,
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

            <Text style={styles.title}>Decision</Text>

            <Text style={styles.subtitle}>
              Authoritative trading decision
            </Text>
          </View>

          <View style={styles.stageBadge}>
            <Text style={styles.stageNumber}>05</Text>

            <Text style={styles.stageLabel}>
              DECISION
            </Text>
          </View>
        </View>

        {/* MARKET */}
        <View style={styles.marketCard}>
          <View style={styles.marketHeader}>
            <Text style={styles.marketLabel}>
              ACTIVE MARKET
            </Text>

            <View style={styles.engineBadge}>
              <View style={styles.engineDot} />

              <Text style={styles.engineText}>
                DECISION ENGINE
              </Text>
            </View>
          </View>

          <View style={styles.marketRow}>
            <View>
              <Text style={styles.marketSymbol}>
                {symbol}
              </Text>

              <Text style={styles.marketDescription}>
                Backend decision target
              </Text>
            </View>

            <Text style={styles.stageReference}>
              STAGE 05
            </Text>
          </View>
        </View>

        {/* DECISION CARD */}
        <View
          style={[
            styles.decisionCard,
            activeStyles.border,
            activeStyles.background,
          ]}
        >
          <View style={styles.decisionHeader}>
            <View>
              <Text style={styles.decisionEyebrow}>
                CURRENT DECISION
              </Text>

              <Text style={styles.decisionTitle}>
                Backend Output
              </Text>
            </View>

            <View style={styles.decisionIndicator}>
              <View
                style={[
                  styles.decisionIndicatorDot,
                  activeStyles.dot,
                ]}
              />
            </View>
          </View>

          <View style={styles.decisionCenter}>
            <Text
              style={[
                styles.decisionValue,
                activeStyles.text,
              ]}
            >
              {decision}
            </Text>

            <Text style={styles.decisionState}>
              {decision === 'NO TRADE'
                ? 'NO AUTHORIZED TRADE'
                : 'DECISION RECEIVED'}
            </Text>
          </View>

          <View style={styles.divider} />

          <Text style={styles.decisionExplanation}>
            The trading decision is produced by the backend
            decision engine after the preceding intelligence
            stages. This screen only displays that result.
          </Text>
        </View>

        {/* DECISION STATES */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              DECISION STATES
            </Text>

            <Text style={styles.sectionSubtitle}>
              Possible backend outcomes
            </Text>
          </View>

          <Text style={styles.sectionNumber}>01</Text>
        </View>

        <View style={styles.statesCard}>
          {decisionStates.map((item, index) => {
            const isActive = item.title === decision;

            return (
              <View
                key={item.title}
                style={[
                  styles.stateRow,
                  index < decisionStates.length - 1 &&
                    styles.stateRowDivider,
                ]}
              >
                <View
                  style={[
                    styles.stateIndicator,
                    isActive
                      ? styles.stateIndicatorActive
                      : styles.stateIndicatorInactive,
                  ]}
                >
                  {isActive && (
                    <View style={styles.stateIndicatorInner} />
                  )}
                </View>

                <View style={styles.stateContent}>
                  <Text
                    style={[
                      styles.stateTitle,
                      isActive && styles.stateTitleActive,
                    ]}
                  >
                    {item.title}
                  </Text>

                  <Text style={styles.stateDescription}>
                    {item.description}
                  </Text>
                </View>

                {isActive && (
                  <Text style={styles.activeLabel}>
                    ACTIVE
                  </Text>
                )}
              </View>
            );
          })}
        </View>

        {/* ENGINE INPUTS */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              DECISION INPUTS
            </Text>

            <Text style={styles.sectionSubtitle}>
              Evidence supplied by previous stages
            </Text>
          </View>

          <Text style={styles.sectionNumber}>02</Text>
        </View>

        <View style={styles.inputsCard}>
          <View style={styles.inputRow}>
            <View style={styles.inputIcon}>
              <Text style={styles.inputIconText}>01</Text>
            </View>

            <View style={styles.inputContent}>
              <Text style={styles.inputTitle}>
                MARKET ANALYSIS
              </Text>

              <Text style={styles.inputDescription}>
                H4 → H1 → M15 top-down analysis
              </Text>
            </View>

            <Text style={styles.inputStatus}>
              RECEIVED
            </Text>
          </View>

          <View style={styles.inputRow}>
            <View style={styles.inputIcon}>
              <Text style={styles.inputIconText}>02</Text>
            </View>

            <View style={styles.inputContent}>
              <Text style={styles.inputTitle}>
                CONFLUENCE
              </Text>

              <Text style={styles.inputDescription}>
                SMC, supply/demand, volume profile,
                volatility and session context
              </Text>
            </View>

            <Text style={styles.inputStatus}>
              RECEIVED
            </Text>
          </View>

          <View style={styles.inputRow}>
            <View style={styles.inputIcon}>
              <Text style={styles.inputIconText}>03</Text>
            </View>

            <View style={styles.inputContent}>
              <Text style={styles.inputTitle}>
                AI CONFIDENCE
              </Text>

              <Text style={styles.inputDescription}>
                Technical intelligence and market conditions
              </Text>
            </View>

            <Text style={styles.inputStatus}>
              RECEIVED
            </Text>
          </View>
        </View>

        {/* REASONS */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              DECISION REASONS
            </Text>

            <Text style={styles.sectionSubtitle}>
              Backend explanation
            </Text>
          </View>

          <Text style={styles.sectionNumber}>03</Text>
        </View>

        <View style={styles.reasonsCard}>
          {decisionReasons.map((reason, index) => (
            <View
              key={reason}
              style={styles.reasonRow}
            >
              <View style={styles.reasonNumber}>
                <Text style={styles.reasonNumberText}>
                  {String(index + 1).padStart(2, '0')}
                </Text>
              </View>

              <Text style={styles.reasonText}>
                {reason}
              </Text>
            </View>
          ))}
        </View>

        {/* PIPELINE BOUNDARY */}
        <View style={styles.boundaryCard}>
          <Text style={styles.boundaryEyebrow}>
            STAGE 05 COMPLETE
          </Text>

          <Text style={styles.boundaryTitle}>
            Decision → Validation
          </Text>

          <Text style={styles.boundaryText}>
            A BUY or SELL decision is not an execution command.
            The next stage must independently validate risk,
            lot size, margin, broker constraints and trade safety.
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
          onPress={handleValidation}
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
              VALIDATION
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
    borderColor: '#1B2435',
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

  engineBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0D121D',
    borderWidth: 1,
    borderColor: '#202A3D',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 5,
  },

  engineDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#56627A',
    marginRight: 5,
  },

  engineText: {
    color: '#68758E',
    fontSize: 5.5,
    fontWeight: '900',
    letterSpacing: 0.6,
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

  stageReference: {
    color: '#53617A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1,
  },

  decisionCard: {
    borderWidth: 1,
    borderRadius: 20,
    padding: 18,
    marginBottom: 26,
  },

  neutralBorder: {
    borderColor: '#263043',
  },

  neutralBackground: {
    backgroundColor: '#0A0E18',
  },

  buyBorder: {
    borderColor: '#205A45',
  },

  buyBackground: {
    backgroundColor: '#091712',
  },

  sellBorder: {
    borderColor: '#5A2830',
  },

  sellBackground: {
    backgroundColor: '#180A0D',
  },

  neutralText: {
    color: '#A7B1C4',
  },

  buyText: {
    color: '#35E68A',
  },

  sellText: {
    color: '#FF6675',
  },

  neutralDot: {
    backgroundColor: '#68758E',
  },

  buyDot: {
    backgroundColor: '#35E68A',
  },

  sellDot: {
    backgroundColor: '#FF6675',
  },

  decisionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  decisionEyebrow: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.5,
  },

  decisionTitle: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '900',
    marginTop: 3,
  },

  decisionIndicator: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#080C15',
    borderWidth: 1,
    borderColor: '#202A3D',
    alignItems: 'center',
    justifyContent: 'center',
  },

  decisionIndicatorDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },

  decisionCenter: {
    alignItems: 'center',
    paddingVertical: 27,
  },

  decisionValue: {
    fontSize: 38,
    fontWeight: '900',
    letterSpacing: 1,
  },

  decisionState: {
    color: '#56627A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.1,
    marginTop: 8,
  },

  divider: {
    height: 1,
    backgroundColor: '#182131',
  },

  decisionExplanation: {
    color: '#68758E',
    fontSize: 9,
    lineHeight: 15,
    textAlign: 'center',
    marginTop: 15,
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

  statesCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 17,
    paddingHorizontal: 14,
    marginBottom: 25,
  },

  stateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 70,
  },

  stateRowDivider: {
    borderBottomWidth: 1,
    borderBottomColor: '#111827',
  },

  stateIndicator: {
    width: 18,
    height: 18,
    borderRadius: 9,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
  },

  stateIndicatorActive: {
    borderWidth: 1,
    borderColor: '#334BFF',
    backgroundColor: '#10183D',
  },

  stateIndicatorInactive: {
    borderWidth: 1,
    borderColor: '#263043',
    backgroundColor: '#111722',
  },

  stateIndicatorInner: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#7083FF',
  },

  stateContent: {
    flex: 1,
  },

  stateTitle: {
    color: '#8995B1',
    fontSize: 10,
    fontWeight: '900',
  },

  stateTitleActive: {
    color: '#FFFFFF',
  },

  stateDescription: {
    color: '#68758E',
    fontSize: 8,
    lineHeight: 13,
    marginTop: 3,
  },

  activeLabel: {
    color: '#7083FF',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.8,
    marginLeft: 7,
  },

  inputsCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 17,
    paddingHorizontal: 14,
    marginBottom: 25,
  },

  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 74,
    borderBottomWidth: 1,
    borderBottomColor: '#111827',
  },

  inputIcon: {
    width: 30,
    height: 30,
    borderRadius: 9,
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },

  inputIconText: {
    color: '#7083FF',
    fontSize: 6.5,
    fontWeight: '900',
  },

  inputContent: {
    flex: 1,
    paddingRight: 8,
  },

  inputTitle: {
    color: '#FFFFFF',
    fontSize: 8.5,
    fontWeight: '900',
    letterSpacing: 0.6,
  },

  inputDescription: {
    color: '#68758E',
    fontSize: 7.5,
    lineHeight: 12,
    marginTop: 3,
  },

  inputStatus: {
    color: '#35E68A',
    fontSize: 5.5,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  reasonsCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 17,
    padding: 14,
    marginBottom: 25,
  },

  reasonRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 13,
  },

  reasonNumber: {
    width: 26,
    height: 26,
    borderRadius: 8,
    backgroundColor: '#111722',
    borderWidth: 1,
    borderColor: '#263043',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 9,
  },

  reasonNumberText: {
    color: '#68758E',
    fontSize: 6,
    fontWeight: '900',
  },

  reasonText: {
    flex: 1,
    color: '#8995B1',
    fontSize: 8.5,
    lineHeight: 14,
    paddingTop: 4,
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
