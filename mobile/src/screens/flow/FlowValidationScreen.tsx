
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

type ValidationState =
  | 'READY'
  | 'VALID'
  | 'BLOCKED'
  | 'PENDING';

const validationState: ValidationState = 'PENDING';

const validationChecks = [
  {
    number: '01',
    title: 'RISK VALIDATION',
    description:
      'Risk percentage and maximum risk limits checked by the backend.',
    status: 'PENDING',
  },
  {
    number: '02',
    title: 'LOT SIZE',
    description:
      'Position size calculated against broker symbol specifications.',
    status: 'PENDING',
  },
  {
    number: '03',
    title: 'MARGIN CHECK',
    description:
      'Required margin and available account margin verified.',
    status: 'PENDING',
  },
  {
    number: '04',
    title: 'BROKER CONSTRAINTS',
    description:
      'Volume, stop distance, spread and symbol trading rules checked.',
    status: 'PENDING',
  },
  {
    number: '05',
    title: 'FINAL VALIDATION',
    description:
      'Trade plan must pass all safety requirements before execution.',
    status: 'PENDING',
  },
];

function getStatusColor(status: string) {
  switch (status) {
    case 'VALID':
    case 'READY':
      return '#35E68A';

    case 'BLOCKED':
      return '#FF6675';

    default:
      return '#68758E';
  }
}

function getStatusBackground(status: string) {
  switch (status) {
    case 'VALID':
    case 'READY':
      return '#0A1713';

    case 'BLOCKED':
      return '#180A0D';

    default:
      return '#111722';
  }
}

export default function FlowValidationScreen({
  navigation,
  route,
}: any) {
  const insets = useSafeAreaInsets();

  const symbol = route?.params?.symbol || 'XAUUSD';
  const decision = route?.params?.decision || 'NO TRADE';
  const confidence = route?.params?.confidence;

  const handleBack = () => {
    navigation.goBack();
  };

  const handleExecution = () => {
    navigation.navigate('FlowExecution', {
      user: route?.params?.user,
      symbol,
      decision,
      confidence,
      validationStatus: validationState,
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
            paddingBottom: Math.max(insets.bottom, 40),
          },
        ]}
      >
        {/* HEADER */}

        <View style={styles.header}>
          <Pressable
            onPress={handleBack}
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
              Validation
            </Text>

            <Text style={styles.subtitle}>
              Risk, position sizing and final safety checks
            </Text>
          </View>

          <View style={styles.stageBadge}>
            <Text style={styles.stageNumber}>06</Text>

            <Text style={styles.stageLabel}>
              VALIDATION
            </Text>
          </View>
        </View>

        {/* MARKET CONTEXT */}

        <View style={styles.marketCard}>
          <Text style={styles.cardLabel}>
            VALIDATION CONTEXT
          </Text>

          <View style={styles.marketRow}>
            <View>
              <Text style={styles.marketSymbol}>
                {symbol}
              </Text>

              <Text style={styles.marketDescription}>
                Decision: {decision}
              </Text>
            </View>

            <View style={styles.contextBadge}>
              <Text style={styles.contextBadgeText}>
                STAGE 06
              </Text>
            </View>
          </View>

          {confidence !== undefined && (
            <View style={styles.confidenceRow}>
              <Text style={styles.confidenceLabel}>
                AI CONFIDENCE
              </Text>

              <Text style={styles.confidenceValue}>
                {confidence}%
              </Text>
            </View>
          )}
        </View>

        {/* VALIDATION STATUS */}

        <View
          style={[
            styles.statusCard,
            {
              borderColor:
                getStatusColor(validationState),
            },
          ]}
        >
          <View style={styles.statusHeader}>
            <View>
              <Text style={styles.statusEyebrow}>
                FINAL VALIDATION
              </Text>

              <Text style={styles.statusTitle}>
                {validationState}
              </Text>
            </View>

            <View
              style={[
                styles.statusCircle,
                {
                  backgroundColor:
                    getStatusBackground(validationState),
                  borderColor:
                    getStatusColor(validationState),
                },
              ]}
            >
              <View
                style={[
                  styles.statusDot,
                  {
                    backgroundColor:
                      getStatusColor(validationState),
                  },
                ]}
              />
            </View>
          </View>

          <Text style={styles.statusDescription}>
            {validationState === 'VALID'
              ? 'All required validation checks have passed.'
              : validationState === 'BLOCKED'
              ? 'Execution is blocked until the validation requirements are satisfied.'
              : 'Waiting for authoritative validation data from the backend.'}
          </Text>
        </View>

        {/* VALIDATION PIPELINE */}

        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              VALIDATION PIPELINE
            </Text>

            <Text style={styles.sectionSubtitle}>
              Backend risk and execution safety
            </Text>
          </View>

          <Text style={styles.sectionCount}>
            05 CHECKS
          </Text>
        </View>

        <View style={styles.checksCard}>
          {validationChecks.map((check, index) => {
            const color = getStatusColor(check.status);

            return (
              <View
                key={check.number}
                style={[
                  styles.checkRow,
                  index < validationChecks.length - 1 &&
                    styles.checkDivider,
                ]}
              >
                <View
                  style={[
                    styles.checkNumber,
                    {
                      borderColor: color,
                    },
                  ]}
                >
                  <Text
                    style={[
                      styles.checkNumberText,
                      {
                        color,
                      },
                    ]}
                  >
                    {check.number}
                  </Text>
                </View>

                <View style={styles.checkContent}>
                  <Text style={styles.checkTitle}>
                    {check.title}
                  </Text>

                  <Text style={styles.checkDescription}>
                    {check.description}
                  </Text>
                </View>

                <View
                  style={[
                    styles.checkStatus,
                    {
                      backgroundColor:
                        getStatusBackground(check.status),
                      borderColor: color,
                    },
                  ]}
                >
                  <Text
                    style={[
                      styles.checkStatusText,
                      {
                        color,
                      },
                    ]}
                  >
                    {check.status}
                  </Text>
                </View>
              </View>
            );
          })}
        </View>

        {/* RISK SUMMARY */}

        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              RISK SUMMARY
            </Text>

            <Text style={styles.sectionSubtitle}>
              Backend-calculated trade parameters
            </Text>
          </View>

          <Text style={styles.sectionCount}>
            RISK
          </Text>
        </View>

        <View style={styles.metricsCard}>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>
              RISK %
            </Text>

            <Text style={styles.metricValue}>
              —
            </Text>
          </View>

          <View style={styles.metric}>
            <Text style={styles.metricLabel}>
              LOT SIZE
            </Text>

            <Text style={styles.metricValue}>
              —
            </Text>
          </View>

          <View style={styles.metric}>
            <Text style={styles.metricLabel}>
              MARGIN
            </Text>

            <Text style={styles.metricValue}>
              —
            </Text>
          </View>

          <View style={styles.metric}>
            <Text style={styles.metricLabel}>
              R:R
            </Text>

            <Text style={styles.metricValue}>
              —
            </Text>
          </View>
        </View>

        {/* BROKER SAFETY */}

        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              BROKER SAFETY
            </Text>

            <Text style={styles.sectionSubtitle}>
              Symbol and execution constraints
            </Text>
          </View>
        </View>

        <View style={styles.safetyCard}>
          <View style={styles.safetyRow}>
            <Text style={styles.safetyLabel}>
              SYMBOL
            </Text>

            <Text style={styles.safetyValue}>
              {symbol}
            </Text>
          </View>

          <View style={styles.safetyRow}>
            <Text style={styles.safetyLabel}>
              SPREAD
            </Text>

            <Text style={styles.safetyPending}>
              BACKEND
            </Text>
          </View>

          <View style={styles.safetyRow}>
            <Text style={styles.safetyLabel}>
              STOP DISTANCE
            </Text>

            <Text style={styles.safetyPending}>
              BACKEND
            </Text>
          </View>

          <View style={styles.safetyRow}>
            <Text style={styles.safetyLabel}>
              VOLUME RULES
            </Text>

            <Text style={styles.safetyPending}>
              BACKEND
            </Text>
          </View>

          <View style={styles.safetyRow}>
            <Text style={styles.safetyLabel}>
              MARGIN
            </Text>

            <Text style={styles.safetyPending}>
              BACKEND
            </Text>
          </View>
        </View>

        {/* SAFETY NOTICE */}

        <View style={styles.noticeCard}>
          <View style={styles.noticeIcon}>
            <Text style={styles.noticeIconText}>
              !
            </Text>
          </View>

          <View style={styles.noticeContent}>
            <Text style={styles.noticeTitle}>
              EXECUTION GATE
            </Text>

            <Text style={styles.noticeText}>
              A trade must pass the complete backend validation
              pipeline before it can proceed to MT5 execution.
              The mobile interface does not override validation
              failures.
            </Text>
          </View>
        </View>

        {/* CONTINUE */}

        <Pressable
          onPress={handleExecution}
          disabled={validationState === 'BLOCKED'}
          style={({pressed}) => [
            styles.continueButton,
            validationState === 'BLOCKED' &&
              styles.continueButtonDisabled,
            pressed &&
              validationState !== 'BLOCKED' &&
              styles.pressed,
          ]}
        >
          <Text style={styles.continueButtonText}>
            CONTINUE TO EXECUTION
          </Text>

          <Text style={styles.continueArrow}>
            →
          </Text>
        </Pressable>

        <Text style={styles.footerText}>
          Execution remains controlled by the backend execution
          and MT5 safety layer.
        </Text>
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
    width: 50,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    alignItems: 'center',
    justifyContent: 'center',
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
    letterSpacing: 0.5,
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

  cardLabel: {
    color: '#68748D',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1.5,
    marginBottom: 12,
  },

  marketRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
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

  contextBadge: {
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 9,
    paddingHorizontal: 9,
    paddingVertical: 6,
  },

  contextBadgeText: {
    color: '#7083FF',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  confidenceRow: {
    marginTop: 16,
    paddingTop: 13,
    borderTopWidth: 1,
    borderTopColor: '#182131',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },

  confidenceLabel: {
    color: '#56627A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  confidenceValue: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '900',
  },

  statusCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderRadius: 20,
    padding: 18,
    marginBottom: 26,
  },

  statusHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  statusEyebrow: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.4,
  },

  statusTitle: {
    color: '#FFFFFF',
    fontSize: 27,
    fontWeight: '900',
    marginTop: 4,
  },

  statusCircle: {
    width: 42,
    height: 42,
    borderRadius: 21,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },

  statusDot: {
    width: 9,
    height: 9,
    borderRadius: 5,
  },

  statusDescription: {
    color: '#68758E',
    fontSize: 9,
    lineHeight: 15,
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

  sectionCount: {
    color: '#53617A',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  checksCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 17,
    paddingHorizontal: 14,
    marginBottom: 26,
  },

  checkRow: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 79,
    paddingVertical: 9,
  },

  checkDivider: {
    borderBottomWidth: 1,
    borderBottomColor: '#111827',
  },

  checkNumber: {
    width: 31,
    height: 31,
    borderRadius: 9,
    backgroundColor: '#111722',
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },

  checkNumberText: {
    fontSize: 7,
    fontWeight: '900',
  },

  checkContent: {
    flex: 1,
    paddingRight: 8,
  },

  checkTitle: {
    color: '#FFFFFF',
    fontSize: 8.5,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  checkDescription: {
    color: '#68758E',
    fontSize: 7.5,
    lineHeight: 12,
    marginTop: 3,
  },

  checkStatus: {
    borderWidth: 1,
    borderRadius: 7,
    paddingHorizontal: 7,
    paddingVertical: 5,
  },

  checkStatusText: {
    fontSize: 5.5,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  metricsCard: {
    flexDirection: 'row',
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 17,
    padding: 14,
    marginBottom: 26,
  },

  metric: {
    flex: 1,
    alignItems: 'center',
    borderRightWidth: 1,
    borderRightColor: '#182131',
  },

  metricLabel: {
    color: '#56627A',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  metricValue: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '900',
    marginTop: 6,
  },

  safetyCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 17,
    paddingHorizontal: 16,
    marginBottom: 25,
  },

  safetyRow: {
    minHeight: 48,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: 1,
    borderBottomColor: '#111827',
  },

  safetyLabel: {
    color: '#56627A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  safetyValue: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '900',
  },

  safetyPending: {
    color: '#68758E',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.6,
  },

  noticeCard: {
    flexDirection: 'row',
    backgroundColor: '#0B1020',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 17,
    padding: 15,
    marginBottom: 18,
  },

  noticeIcon: {
    width: 30,
    height: 30,
    borderRadius: 10,
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#334BFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
  },

  noticeIconText: {
    color: '#7083FF',
    fontSize: 13,
    fontWeight: '900',
  },

  noticeContent: {
    flex: 1,
  },

  noticeTitle: {
    color: '#FFFFFF',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  noticeText: {
    color: '#68758E',
    fontSize: 8.5,
    lineHeight: 14,
    marginTop: 4,
  },

  continueButton: {
    minHeight: 56,
    borderRadius: 15,
    borderWidth: 1,
    borderColor: '#263A91',
    backgroundColor: '#10183D',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 17,
  },

  continueButtonDisabled: {
    opacity: 0.4,
  },

  continueButtonText: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  continueArrow: {
    color: '#7083FF',
    fontSize: 19,
    fontWeight: '700',
  },

  footerText: {
    color: '#4F5B72',
    fontSize: 7.5,
    lineHeight: 13,
    textAlign: 'center',
    marginTop: 12,
    paddingHorizontal: 15,
  },
});
