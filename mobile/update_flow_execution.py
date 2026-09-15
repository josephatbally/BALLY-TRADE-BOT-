import os

target = os.path.join("src", "screens", "flow", "FlowExecutionScreen.tsx")
if not os.path.exists(target):
    target = os.path.join("mobile", "src", "screens", "flow", "FlowExecutionScreen.tsx")

if not os.path.exists(target):
    print(f"[ERROR] Could not find {target}")
    exit(1)

content = """import React, {useEffect, useState, useCallback} from 'react';
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

type ExecutionStatus =
  | 'READY'
  | 'EXECUTED'
  | 'REJECTED'
  | 'BLOCKED'
  | 'STANDBY';

function getStatusColor(status: string) {
  switch (status) {
    case 'EXECUTED':
    case 'READY':
      return '#35E68A';
    case 'REJECTED':
    case 'BLOCKED':
      return '#FF6675';
    default:
      return '#7083FF';
  }
}

function getStatusBackground(status: string) {
  switch (status) {
    case 'EXECUTED':
    case 'READY':
      return '#0A1713';
    case 'REJECTED':
    case 'BLOCKED':
      return '#180A0D';
    default:
      return 'rgba(112, 131, 255, 0.12)';
  }
}

export default function FlowExecutionScreen({
  navigation,
  route,
}: any) {
  const insets = useSafeAreaInsets();

  const symbol = route?.params?.symbol || 'XAUUSD';
  const decision = route?.params?.decision || 'NO TRADE';
  const validation = route?.params?.validationStatus || 'VALID';

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

  const isExecutable = decision === 'BUY' || decision === 'SELL';
  const executionStatus: ExecutionStatus = isExecutable ? 'READY' : 'STANDBY';

  const executionSteps = [
    {
      number: '01',
      title: 'VALIDATION RECEIVED',
      description: 'Risk management and lot allocation verified by backend.',
      status: 'READY',
    },
    {
      number: '02',
      title: 'MT5 CONNECTION',
      description: 'MetaTrader 5 live terminal bridge online and responsive.',
      status: 'READY',
    },
    {
      number: '03',
      title: 'EXECUTION CHECKS',
      description: 'Symbol spread, tick latency and broker trading rules cleared.',
      status: 'READY',
    },
    {
      number: '04',
      title: 'ORDER PIPELINE',
      description: isExecutable
        ? `Armed for ${decision} dispatch with 0.01 lot size.`
        : 'Standby: awaiting qualified directional decision.',
      status: isExecutable ? 'READY' : 'STANDBY',
    },
    {
      number: '05',
      title: 'MT5 RESULT',
      description: isExecutable
        ? `Pending trigger @ ${quote?.price ?? 'market price'}.`
        : 'Execution gate closed in non-directional mode.',
      status: isExecutable ? 'READY' : 'STANDBY',
    },
  ];

  const handleBackToFlow = () => {
    navigation.popToTop();
  };

  const handlePrevious = () => {
    navigation.goBack();
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
            onPress={handlePrevious}
            style={({pressed}) => [
              styles.backButton,
              pressed && styles.pressed,
            ]}
          >
            <Text style={styles.backIcon}>‹</Text>
          </Pressable>

          <View style={styles.headerText}>
            <Text style={styles.eyebrow}>BALLY FLOW</Text>
            <Text style={styles.title}>Execution</Text>
            <Text style={styles.subtitle}>
              MT5 execution and broker response
            </Text>
          </View>

          <View style={styles.stageBadge}>
            <Text style={styles.stageNumber}>07</Text>
            <Text style={styles.stageLabel}>EXECUTION</Text>
          </View>
        </View>

        {/* TRADE CONTEXT */}
        <View style={styles.marketCard}>
          <View style={styles.marketHeader}>
            <Text style={styles.marketLabel}>EXECUTION CONTEXT</Text>
            <View style={styles.backendBadge}>
              <View style={styles.backendDot} />
              <Text style={styles.backendText}>
                {loading ? 'CONNECTING...' : 'BACKEND CONTROLLED'}
              </Text>
            </View>
          </View>

          <View style={styles.marketRow}>
            <View>
              <Text style={styles.marketSymbol}>{symbol}</Text>
              <Text style={styles.marketDescription}>
                Decision: {decision} {quote ? `(${quote.price})` : ''}
              </Text>
            </View>

            <View style={styles.stageReference}>
              <Text style={styles.stageReferenceNumber}>07</Text>
              <Text style={styles.stageReferenceText}>FINAL</Text>
            </View>
          </View>
        </View>

        {/* EXECUTION STATUS */}
        <View
          style={[
            styles.executionCard,
            {borderColor: getStatusColor(executionStatus)},
          ]}
        >
          <View style={styles.executionHeader}>
            <View>
              <Text style={styles.executionEyebrow}>MT5 EXECUTION STATUS</Text>
              <Text style={styles.executionTitle}>{executionStatus}</Text>
            </View>

            <View
              style={[
                styles.statusIndicator,
                {
                  backgroundColor: getStatusBackground(executionStatus),
                  borderColor: getStatusColor(executionStatus),
                },
              ]}
            >
              <View
                style={[
                  styles.statusIndicatorDot,
                  {backgroundColor: getStatusColor(executionStatus)},
                ]}
              />
            </View>
          </View>

          <Text style={styles.executionDescription}>
            {isExecutable
              ? `Terminal armed. The backend execution engine is authorized to dispatch ${decision} orders for ${symbol}.`
              : 'Standby mode: execution gate is safely held until high-confluence directional decision is qualified.'}
          </Text>
        </View>

        {/* EXECUTION PIPELINE */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>EXECUTION PIPELINE</Text>
            <Text style={styles.sectionSubtitle}>
              Backend → MT5 → broker response
            </Text>
          </View>
          <Text style={styles.sectionCount}>05 STEPS</Text>
        </View>

        <View style={styles.stepsCard}>
          {executionSteps.map((step, index) => {
            const color = getStatusColor(step.status);

            return (
              <View
                key={step.number}
                style={[
                  styles.stepRow,
                  index < executionSteps.length - 1 && styles.stepDivider,
                ]}
              >
                <View
                  style={[
                    styles.stepNumber,
                    {borderColor: color},
                  ]}
                >
                  <Text style={[styles.stepNumberText, {color}]}>
                    {step.number}
                  </Text>
                </View>

                <View style={styles.stepContent}>
                  <Text style={styles.stepTitle}>{step.title}</Text>
                  <Text style={styles.stepDescription}>
                    {step.description}
                  </Text>
                </View>

                <View
                  style={[
                    styles.stepStatus,
                    {
                      backgroundColor: getStatusBackground(step.status),
                      borderColor: color,
                    },
                  ]}
                >
                  <Text style={[styles.stepStatusText, {color}]}>
                    {step.status}
                  </Text>
                </View>
              </View>
            );
          })}
        </View>

        {/* MT5 CONNECTION */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>MT5 CONNECTION</Text>
            <Text style={styles.sectionSubtitle}>
              Terminal execution environment
            </Text>
          </View>
          <Text style={styles.sectionCount}>LIVE</Text>
        </View>

        <View style={styles.connectionCard}>
          <View style={styles.connectionRow}>
            <View style={styles.connectionIcon}>
              <Text style={styles.connectionIconText}>MT5</Text>
            </View>

            <View style={styles.connectionContent}>
              <Text style={styles.connectionTitle}>METATRADER 5</Text>
              <Text style={styles.connectionDescription}>
                Bridge active • Latency optimal
              </Text>
            </View>

            <View style={styles.connectionStatus}>
              <View style={styles.connectionStatusDot} />
              <Text style={styles.connectionStatusText}>ONLINE</Text>
            </View>
          </View>
        </View>

        {/* ORDER INFORMATION */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>ORDER INFORMATION</Text>
            <Text style={styles.sectionSubtitle}>
              Authoritative execution parameters
            </Text>
          </View>
          <Text style={styles.sectionCount}>MT5</Text>
        </View>

        <View style={styles.orderCard}>
          <View style={styles.orderRow}>
            <Text style={styles.orderLabel}>SYMBOL</Text>
            <Text style={styles.orderValue}>{symbol}</Text>
          </View>

          <View style={styles.orderRow}>
            <Text style={styles.orderLabel}>DECISION</Text>
            <Text style={[styles.orderValue, {color: isExecutable ? '#35E68A' : '#F8FAFC'}]}>
              {decision}
            </Text>
          </View>

          <View style={styles.orderRow}>
            <Text style={styles.orderLabel}>VALIDATION</Text>
            <Text style={[styles.orderValue, {color: '#35E68A'}]}>
              {validation}
            </Text>
          </View>

          <View style={styles.orderRow}>
            <Text style={styles.orderLabel}>DEFAULT LOT</Text>
            <Text style={styles.orderValue}>0.01</Text>
          </View>

          <View style={styles.orderRow}>
            <Text style={styles.orderLabel}>EXECUTION PRICE</Text>
            <Text style={quote ? styles.orderValue : styles.orderValueMuted}>
              {quote ? quote.price : '—'}
            </Text>
          </View>

          <View style={styles.orderRow}>
            <Text style={styles.orderLabel}>GATE STATUS</Text>
            <Text style={[styles.orderValue, {color: isExecutable ? '#35E68A' : '#7083FF'}]}>
              {isExecutable ? 'ARMED' : 'STANDBY'}
            </Text>
          </View>
        </View>

        {/* SAFETY NOTICE */}
        <View style={styles.safetyCard}>
          <View style={styles.safetyIcon}>
            <Text style={styles.safetyIconText}>!</Text>
          </View>

          <View style={styles.safetyContent}>
            <Text style={styles.safetyTitle}>EXECUTION SAFETY</Text>
            <Text style={styles.safetyText}>
              The mobile application does not directly submit MT5 orders. Execution
              remains backend-governed through strict risk management and algo controls.
            </Text>
          </View>
        </View>
      </ScrollView>

      {/* FOOTER CTA */}
      <View
        style={[
          styles.footer,
          {paddingBottom: Math.max(insets.bottom, 16)},
        ]}
      >
        <Pressable
          onPress={handleBackToFlow}
          style={({pressed}) => [
            styles.continueButton,
            pressed && styles.continuePressed,
          ]}
        >
          <View>
            <Text style={styles.continueLabel}>COMPLETE FLOW</Text>
            <Text style={styles.continueTitle}>RETURN TO FLOW HOME</Text>
          </View>

          <View style={styles.continueArrow}>
            <Text style={styles.arrowIcon}>↺</Text>
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
  pressed: {
    opacity: 0.7,
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
  backendBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(112, 131, 255, 0.12)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(112, 131, 255, 0.25)',
  },
  backendDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#7083FF',
    marginRight: 6,
  },
  backendText: {
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
    alignItems: 'flex-end',
  },
  stageReferenceNumber: {
    color: '#7083FF',
    fontSize: 14,
    fontWeight: '800',
  },
  stageReferenceText: {
    color: '#64748B',
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  executionCard: {
    backgroundColor: '#0B101E',
    borderRadius: 18,
    padding: 20,
    borderWidth: 1,
    marginBottom: 20,
  },
  executionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  executionEyebrow: {
    color: '#7083FF',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
  },
  executionTitle: {
    color: '#F8FAFC',
    fontSize: 24,
    fontWeight: '900',
    marginTop: 2,
  },
  statusIndicator: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  statusIndicatorDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  executionDescription: {
    color: '#94A3B8',
    fontSize: 12,
    lineHeight: 18,
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
  sectionCount: {
    color: '#334155',
    fontSize: 12,
    fontWeight: '800',
  },
  stepsCard: {
    backgroundColor: '#0B101E',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#172238',
    marginBottom: 20,
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
  },
  stepDivider: {
    borderBottomWidth: 1,
    borderBottomColor: '#172238',
  },
  stepNumber: {
    width: 28,
    height: 28,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  stepNumberText: {
    fontSize: 11,
    fontWeight: '800',
  },
  stepContent: {
    flex: 1,
    marginRight: 10,
  },
  stepTitle: {
    color: '#F8FAFC',
    fontSize: 12,
    fontWeight: '700',
  },
  stepDescription: {
    color: '#64748B',
    fontSize: 11,
    marginTop: 2,
    lineHeight: 15,
  },
  stepStatus: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
  },
  stepStatusText: {
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  connectionCard: {
    backgroundColor: '#0B101E',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#172238',
    marginBottom: 20,
  },
  connectionRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  connectionIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: '#121B2D',
    borderWidth: 1,
    borderColor: '#1B2438',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  connectionIconText: {
    color: '#7083FF',
    fontSize: 11,
    fontWeight: '900',
  },
  connectionContent: {
    flex: 1,
  },
  connectionTitle: {
    color: '#F8FAFC',
    fontSize: 13,
    fontWeight: '800',
  },
  connectionDescription: {
    color: '#64748B',
    fontSize: 11,
    marginTop: 2,
  },
  connectionStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(53, 230, 138, 0.12)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(53, 230, 138, 0.25)',
  },
  connectionStatusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 6,
  },
  connectionStatusText: {
    color: '#35E68A',
    fontSize: 9,
    fontWeight: '800',
  },
  orderCard: {
    backgroundColor: '#0B101E',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#172238',
    marginBottom: 20,
  },
  orderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 7,
  },
  orderLabel: {
    color: '#64748B',
    fontSize: 12,
    fontWeight: '700',
  },
  orderValue: {
    color: '#F8FAFC',
    fontSize: 12,
    fontWeight: '800',
  },
  orderValueMuted: {
    color: '#475569',
    fontSize: 12,
    fontWeight: '700',
  },
  safetyCard: {
    flexDirection: 'row',
    backgroundColor: 'rgba(112, 131, 255, 0.05)',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(112, 131, 255, 0.15)',
    marginBottom: 20,
  },
  safetyIcon: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: 'rgba(112, 131, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
    marginTop: 2,
  },
  safetyIconText: {
    color: '#7083FF',
    fontSize: 11,
    fontWeight: '900',
  },
  safetyContent: {
    flex: 1,
  },
  safetyTitle: {
    color: '#7083FF',
    fontSize: 11,
    fontWeight: '800',
    marginBottom: 3,
  },
  safetyText: {
    color: '#94A3B8',
    fontSize: 11,
    lineHeight: 16,
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
});
"""

with open(target, "w", encoding="utf-8") as f:
    f.write(content)

print(f"[OK] Successfully updated {target}")
