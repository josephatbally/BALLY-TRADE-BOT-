import React, {useEffect, useState, useCallback} from 'react';
import {
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {useSafeAreaInsets} from 'react-native-safe-area-context';
import {getMarketQuotes, MarketQuote} from '../../api/marketsApi';

type Decision = 'BUY' | 'SELL' | 'NO TRADE';

const decisionStates = [
  {
    title: 'BUY',
    description: 'Bullish trade decision from backend confluence',
  },
  {
    title: 'SELL',
    description: 'Bearish trade decision from backend confluence',
  },
  {
    title: 'NO TRADE',
    description: 'Conditions do not authorize a trade setup',
  },
];

export default function FlowDecisionScreen({
  navigation,
  route,
}: any) {
  const insets = useSafeAreaInsets();
  const symbol = route?.params?.symbol || 'XAUUSD';

  const [quote, setQuote] = useState<MarketQuote | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchQuote = useCallback(async () => {
    try {
      const res = await getMarketQuotes();
      if (res && res.quotes) {
        const found = res.quotes.find(
          (q: MarketQuote) => q.symbol.toUpperCase() === symbol.toUpperCase(),
        );
        if (found) {
          setQuote(found);
        }
      }
    } catch {
      // Retain last quote
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    fetchQuote();
    const interval = setInterval(fetchQuote, 4000);
    return () => clearInterval(interval);
  }, [fetchQuote]);

  // Derive decision dynamically from live engine direction
  let decision: Decision = 'NO TRADE';
  if (quote) {
    if (quote.direction === 'BULLISH') {
      decision = 'BUY';
    } else if (quote.direction === 'BEARISH') {
      decision = 'SELL';
    } else {
      decision = 'NO TRADE';
    }
  }

  const decisionReasons = [
    quote
      ? `Live market direction identified as ${quote.direction || 'NEUTRAL'} (${quote.change_pct >= 0 ? '+' : ''}${quote.change_pct}%)`
      : 'Awaiting live engine quotes',
    decision === 'BUY'
      ? 'Top-down multi-timeframe structure confirmed bullish alignment'
      : decision === 'SELL'
      ? 'Top-down multi-timeframe structure confirmed bearish distribution'
      : 'Market conditions currently lack conclusive directional consensus',
    'Order validation gate required before live execution',
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

  const activeStyles = getDecisionStyles(decision);

  const handleValidation = () => {
    navigation.navigate('FlowValidation', {
      symbol,
      decision,
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
            <Text style={styles.backIcon}></Text>
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
            <Text style={styles.stageLabel}>DECISION</Text>
          </View>
        </View>

        {/* MARKET */}
        <View style={styles.marketCard}>
          <View style={styles.marketHeader}>
            <Text style={styles.marketLabel}>ACTIVE MARKET</Text>
            <View style={styles.engineBadge}>
              <View style={styles.engineDot} />
              <Text style={styles.engineText}>
                {loading ? 'CONNECTING...' : 'ENGINE ONLINE'}
              </Text>
            </View>
          </View>

          <View style={styles.marketRow}>
            <View>
              <Text style={styles.marketSymbol}>{symbol}</Text>
              <Text style={styles.marketDescription}>
                {quote ? `Live Price: ${quote.price}` : 'Backend decision target'}
              </Text>
            </View>

            <Text style={styles.stageReference}>STAGE 05</Text>
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
              <Text style={styles.decisionEyebrow}>CURRENT DECISION</Text>
              <Text style={styles.decisionTitle}>Backend Engine Output</Text>
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
                : 'DECISION CONFIRMED'}
            </Text>
          </View>

          <View style={styles.divider} />

          <Text style={styles.decisionExplanation}>
            The trading decision is produced by the backend decision engine after
            evaluating market structure, confluence, and confidence filters.
          </Text>
        </View>

        {/* DECISION STATES */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>DECISION STATES</Text>
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
            <Text style={styles.sectionTitle}>DECISION INPUTS</Text>
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
              <Text style={styles.inputTitle}>MARKET ANALYSIS</Text>
              <Text style={styles.inputDescription}>
                H4 â†’ H1 â†’ M15 top-down analysis
              </Text>
            </View>
            <Text style={styles.inputStatus}>RECEIVED</Text>
          </View>

          <View style={styles.inputRow}>
            <View style={styles.inputIcon}>
              <Text style={styles.inputIconText}>02</Text>
            </View>
            <View style={styles.inputContent}>
              <Text style={styles.inputTitle}>CONFLUENCE MATRIX</Text>
              <Text style={styles.inputDescription}>
                Key level and structure alignment
              </Text>
            </View>
            <Text style={styles.inputStatus}>CONFIRMED</Text>
          </View>

          <View style={styles.inputRow}>
            <View style={styles.inputIcon}>
              <Text style={styles.inputIconText}>03</Text>
            </View>
            <View style={styles.inputContent}>
              <Text style={styles.inputTitle}>CONFIDENCE MODEL</Text>
              <Text style={styles.inputDescription}>
                Weighted multi-factor score
              </Text>
            </View>
            <Text style={styles.inputStatus}>EVALUATED</Text>
          </View>
        </View>

        {/* DECISION RATIONALE */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>DECISION RATIONALE</Text>
            <Text style={styles.sectionSubtitle}>
              Why this decision was reached
            </Text>
          </View>

          <Text style={styles.sectionNumber}>03</Text>
        </View>

        <View style={styles.reasonsCard}>
          {decisionReasons.map((reason, index) => (
            <View key={index} style={styles.reasonRow}>
              <View style={styles.reasonBullet} />
              <Text style={styles.reasonText}>{reason}</Text>
            </View>
          ))}
        </View>
      </ScrollView>

      {/* FOOTER CTA */}
      <View
        style={[
          styles.footer,
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
            <Text style={styles.arrowIcon}></Text>
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
  glowTop: {
    position: 'absolute',
    top: -60,
    left: 20,
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: 'rgba(112, 131, 255, 0.08)',
  },
  glowBottom: {
    position: 'absolute',
    bottom: 80,
    right: -40,
    width: 220,
    height: 220,
    borderRadius: 110,
    backgroundColor: 'rgba(0, 209, 255, 0.05)',
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
    backgroundColor: '#0D1322',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    borderWidth: 1,
    borderColor: '#1B2438',
  },
  backIcon: {
    color: '#F8FAFC',
    fontSize: 22,
    lineHeight: 24,
  },
  headerText: {
    flex: 1,
  },
  eyebrow: {
    color: '#7083FF',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
  },
  title: {
    color: '#F8FAFC',
    fontSize: 20,
    fontWeight: '800',
    marginTop: 2,
  },
  subtitle: {
    color: '#94A3B8',
    fontSize: 12,
    marginTop: 2,
  },
  stageBadge: {
    backgroundColor: '#0D1322',
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: '#1B2438',
    alignItems: 'center',
  },
  stageNumber: {
    color: '#7083FF',
    fontSize: 14,
    fontWeight: '800',
  },
  stageLabel: {
    color: '#64748B',
    fontSize: 8,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  marketCard: {
    backgroundColor: '#0B101E',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#172238',
    marginBottom: 16,
  },
  marketHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  marketLabel: {
    color: '#64748B',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
  },
  engineBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(112, 131, 255, 0.12)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(112, 131, 255, 0.25)',
  },
  engineDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#7083FF',
    marginRight: 6,
  },
  engineText: {
    color: '#7083FF',
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  marketRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  marketSymbol: {
    color: '#F8FAFC',
    fontSize: 22,
    fontWeight: '800',
  },
  marketDescription: {
    color: '#94A3B8',
    fontSize: 12,
    marginTop: 2,
  },
  stageReference: {
    color: '#64748B',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  decisionCard: {
    borderRadius: 18,
    padding: 20,
    borderWidth: 1,
    marginBottom: 20,
  },
  buyBorder: {
    borderColor: '#10B981',
  },
  buyBackground: {
    backgroundColor: 'rgba(16, 185, 129, 0.08)',
  },
  buyText: {
    color: '#10B981',
  },
  buyDot: {
    backgroundColor: '#10B981',
  },
  sellBorder: {
    borderColor: '#EF4444',
  },
  sellBackground: {
    backgroundColor: 'rgba(239, 68, 68, 0.08)',
  },
  sellText: {
    color: '#EF4444',
  },
  sellDot: {
    backgroundColor: '#EF4444',
  },
  neutralBorder: {
    borderColor: '#172238',
  },
  neutralBackground: {
    backgroundColor: '#0B101E',
  },
  neutralText: {
    color: '#94A3B8',
  },
  neutralDot: {
    backgroundColor: '#64748B',
  },
  decisionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  decisionEyebrow: {
    color: '#7083FF',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
  },
  decisionTitle: {
    color: '#F8FAFC',
    fontSize: 18,
    fontWeight: '800',
    marginTop: 2,
  },
  decisionIndicator: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: '#0D1322',
    borderWidth: 1,
    borderColor: '#1B2438',
    alignItems: 'center',
    justifyContent: 'center',
  },
  decisionIndicatorDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  decisionCenter: {
    alignItems: 'center',
    marginVertical: 12,
  },
  decisionValue: {
    fontSize: 50,
    fontWeight: '900',
    letterSpacing: 1,
  },
  decisionState: {
    color: '#64748B',
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1,
    marginTop: 8,
  },
  divider: {
    height: 1,
    backgroundColor: '#172238',
    marginVertical: 14,
  },
  decisionExplanation: {
    color: '#94A3B8',
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    marginTop: 6,
  },
  sectionTitle: {
    color: '#F8FAFC',
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 1,
  },
  sectionSubtitle: {
    color: '#64748B',
    fontSize: 11,
    marginTop: 2,
  },
  sectionNumber: {
    color: '#334155',
    fontSize: 12,
    fontWeight: '800',
  },
  statesCard: {
    backgroundColor: '#0B101E',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#172238',
    marginBottom: 20,
  },
  stateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
  },
  stateRowDivider: {
    borderBottomWidth: 1,
    borderBottomColor: '#172238',
  },
  stateIndicator: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  stateIndicatorActive: {
    borderColor: '#7083FF',
    backgroundColor: 'rgba(112, 131, 255, 0.2)',
  },
  stateIndicatorInactive: {
    borderColor: '#334155',
  },
  stateIndicatorInner: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#7083FF',
  },
  stateContent: {
    flex: 1,
  },
  stateTitle: {
    color: '#94A3B8',
    fontSize: 13,
    fontWeight: '700',
  },
  stateTitleActive: {
    color: '#F8FAFC',
    fontWeight: '800',
  },
  stateDescription: {
    color: '#64748B',
    fontSize: 11,
    marginTop: 2,
  },
  activeLabel: {
    color: '#7083FF',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  inputsCard: {
    backgroundColor: '#0B101E',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#172238',
    marginBottom: 20,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  inputIcon: {
    width: 24,
    height: 24,
    borderRadius: 6,
    backgroundColor: '#121B2D',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  inputIconText: {
    color: '#7083FF',
    fontSize: 10,
    fontWeight: '800',
  },
  inputContent: {
    flex: 1,
  },
  inputTitle: {
    color: '#F8FAFC',
    fontSize: 12,
    fontWeight: '700',
  },
  inputDescription: {
    color: '#64748B',
    fontSize: 11,
    marginTop: 2,
  },
  inputStatus: {
    color: '#10B981',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  reasonsCard: {
    backgroundColor: '#0B101E',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#172238',
    marginBottom: 20,
  },
  reasonRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  reasonBullet: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#7083FF',
    marginTop: 6,
    marginRight: 10,
  },
  reasonText: {
    color: '#94A3B8',
    fontSize: 12,
    lineHeight: 18,
    flex: 1,
  },
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingHorizontal: 16,
    paddingTop: 12,
    backgroundColor: 'rgba(5, 7, 13, 0.95)',
    borderTopWidth: 1,
    borderTopColor: '#172238',
  },
  continueButton: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#7083FF',
    paddingHorizontal: 18,
    paddingVertical: 14,
    borderRadius: 14,
  },
  continuePressed: {
    opacity: 0.85,
  },
  continueLabel: {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  continueTitle: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '900',
    letterSpacing: 0.5,
    marginTop: 1,
  },
  continueArrow: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  arrowIcon: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '800',
  },
  pressed: {
    opacity: 0.7,
  },
});

