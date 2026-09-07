
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

type ExecutionStatus =
  | 'READY'
  | 'EXECUTED'
  | 'REJECTED'
  | 'BLOCKED'
  | 'PENDING';

const executionStatus: ExecutionStatus = 'PENDING';

const executionSteps = [
  {
    number: '01',
    title: 'VALIDATION RECEIVED',
    description: 'Final validation result received from the backend',
    status: 'PENDING',
  },
  {
    number: '02',
    title: 'MT5 CONNECTION',
    description: 'MetaTrader 5 terminal connectivity verification',
    status: 'PENDING',
  },
  {
    number: '03',
    title: 'EXECUTION CHECKS',
    description: 'Symbol, spread, price, volume and safety checks',
    status: 'PENDING',
  },
  {
    number: '04',
    title: 'ORDER PIPELINE',
    description: 'Authorized trade passed to the execution layer',
    status: 'PENDING',
  },
  {
    number: '05',
    title: 'MT5 RESULT',
    description: 'Broker response and execution result',
    status: 'PENDING',
  },
];

function getStatusColor(status: string) {
  switch (status) {
    case 'EXECUTED':
    case 'READY':
      return '#35E68A';

    case 'REJECTED':
    case 'BLOCKED':
      return '#FF6675';

    default:
      return '#68758E';
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
      return '#111722';
  }
}

export default function FlowExecutionScreen({
  navigation,
  route,
}: any) {
  const insets = useSafeAreaInsets();

  const symbol = route?.params?.symbol || 'XAUUSD';
  const decision = route?.params?.decision || 'NO TRADE';
  const validation =
    route?.params?.validationStatus || 'PENDING';

  const handleBackToFlow = () => {
    navigation.popToTop();
  };

  const handlePrevious = () => {
    navigation.goBack();
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

            <Text style={styles.stageLabel}>
              EXECUTION
            </Text>
          </View>
        </View>

        {/* TRADE CONTEXT */}
        <View style={styles.marketCard}>
          <View style={styles.marketHeader}>
            <Text style={styles.marketLabel}>
              EXECUTION CONTEXT
            </Text>

            <View style={styles.backendBadge}>
              <View style={styles.backendDot} />

              <Text style={styles.backendText}>
                BACKEND CONTROLLED
              </Text>
            </View>
          </View>

          <View style={styles.marketRow}>
            <View>
              <Text style={styles.marketSymbol}>
                {symbol}
              </Text>

              <Text style={styles.marketDescription}>
                Decision: {decision}
              </Text>
            </View>

            <View style={styles.stageReference}>
              <Text style={styles.stageReferenceNumber}>
                07
              </Text>

              <Text style={styles.stageReferenceText}>
                FINAL
              </Text>
            </View>
          </View>
        </View>

        {/* EXECUTION STATUS */}
        <View
          style={[
            styles.executionCard,
            {
              borderColor: getStatusColor(executionStatus),
            },
          ]}
        >
          <View style={styles.executionHeader}>
            <View>
              <Text style={styles.executionEyebrow}>
                MT5 EXECUTION STATUS
              </Text>

              <Text style={styles.executionTitle}>
                {executionStatus}
              </Text>
            </View>

            <View
              style={[
                styles.statusIndicator,
                {
                  backgroundColor:
                    getStatusBackground(executionStatus),
                  borderColor:
                    getStatusColor(executionStatus),
                },
              ]}
            >
              <View
                style={[
                  styles.statusIndicatorDot,
                  {
                    backgroundColor:
                      getStatusColor(executionStatus),
                  },
                ]}
              />
            </View>
          </View>

          <Text style={styles.executionDescription}>
            {executionStatus === 'EXECUTED'
              ? 'The backend has confirmed the MT5 execution result.'
              : executionStatus === 'BLOCKED'
              ? 'Execution has been blocked by the backend safety layer.'
              : executionStatus === 'REJECTED'
              ? 'The execution request was rejected by the execution layer or broker.'
              : 'Waiting for authoritative execution status from the backend.'}
          </Text>
        </View>

        {/* EXECUTION PIPELINE */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              EXECUTION PIPELINE
            </Text>

            <Text style={styles.sectionSubtitle}>
              Backend → MT5 → broker response
            </Text>
          </View>

          <Text style={styles.sectionCount}>
            05 STEPS
          </Text>
        </View>

        <View style={styles.stepsCard}>
          {executionSteps.map((step, index) => {
            const color = getStatusColor(step.status);

            return (
              <View
                key={step.number}
                style={[
                  styles.stepRow,
                  index < executionSteps.length - 1 &&
                    styles.stepDivider,
                ]}
              >
                <View
                  style={[
                    styles.stepNumber,
                    {
                      borderColor: color,
                    },
                  ]}
                >
                  <Text
                    style={[
                      styles.stepNumberText,
                      {
                        color,
                      },
                    ]}
                  >
                    {step.number}
                  </Text>
                </View>

                <View style={styles.stepContent}>
                  <Text style={styles.stepTitle}>
                    {step.title}
                  </Text>

                  <Text style={styles.stepDescription}>
                    {step.description}
                  </Text>
                </View>

                <View
                  style={[
                    styles.stepStatus,
                    {
                      backgroundColor:
                        getStatusBackground(step.status),
                      borderColor: color,
                    },
                  ]}
                >
                  <Text
                    style={[
                      styles.stepStatusText,
                      {
                        color,
                      },
                    ]}
                  >
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
            <Text style={styles.sectionTitle}>
              MT5 CONNECTION
            </Text>

            <Text style={styles.sectionSubtitle}>
              Terminal execution environment
            </Text>
          </View>

          <Text style={styles.sectionCount}>
            LIVE
          </Text>
        </View>

        <View style={styles.connectionCard}>
          <View style={styles.connectionRow}>
            <View style={styles.connectionIcon}>
              <Text style={styles.connectionIconText}>
                MT5
              </Text>
            </View>

            <View style={styles.connectionContent}>
              <Text style={styles.connectionTitle}>
                METATRADER 5
              </Text>

              <Text style={styles.connectionDescription}>
                Connection state is supplied by the backend.
              </Text>
            </View>

            <View style={styles.connectionStatus}>
              <View style={styles.connectionStatusDot} />

              <Text style={styles.connectionStatusText}>
                PENDING
              </Text>
            </View>
          </View>
        </View>

        {/* ORDER INFORMATION */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              ORDER INFORMATION
            </Text>

            <Text style={styles.sectionSubtitle}>
              Authoritative execution response
            </Text>
          </View>

          <Text style={styles.sectionCount}>
            MT5
          </Text>
        </View>

        <View style={styles.orderCard}>
          <View style={styles.orderRow}>
            <Text style={styles.orderLabel}>
              SYMBOL
            </Text>

            <Text style={styles.orderValue}>
              {symbol}
            </Text>
          </View>

          <View style={styles.orderRow}>
            <Text style={styles.orderLabel}>
              DECISION
            </Text>

            <Text style={styles.orderValue}>
              {decision}
            </Text>
          </View>

          <View style={styles.orderRow}>
            <Text style={styles.orderLabel}>
              VALIDATION
            </Text>

            <Text style={styles.orderValue}>
              {validation}
            </Text>
          </View>

          <View style={styles.orderRow}>
            <Text style={styles.orderLabel}>
              TICKET
            </Text>

            <Text style={styles.orderValueMuted}>
              —
            </Text>
          </View>

          <View style={styles.orderRow}>
            <Text style={styles.orderLabel}>
              EXECUTION PRICE
            </Text>

            <Text style={styles.orderValueMuted}>
              —
            </Text>
          </View>

          <View style={styles.orderRow}>
            <Text style={styles.orderLabel}>
              BROKER RESULT
            </Text>

            <Text style={styles.orderValueMuted}>
              —
            </Text>
          </View>
        </View>

        {/* SAFETY NOTICE */}
        <View style={styles.safetyCard}>
          <View style={styles.safetyIcon}>
            <Text style={styles.safetyIconText}>
              !
            </Text>
          </View>

          <View style={styles.safetyContent}>
            <Text style={styles.safetyTitle}>
              EXECUTION SAFETY
            </Text>

            <Text style={styles.safetyText}>
              The mobile application does not directly submit
              MT5 orders. Execution remains controlled by the
              backend execution layer and its safety controls.
            </Text>
          </View>
        </View>

        {/* COMPLETE PIPELINE */}
        <View style={styles.completeCard}>
          <Text style={styles.completeEyebrow}>
            TRADING INTELLIGENCE
          </Text>

          <Text style={styles.completeTitle}>
            07 STAGES
          </Text>

          <Text style={styles.completeText}>
            Market → Analysis → Confluence → Confidence →
            Decision → Validation → Execution
          </Text>
        </View>

        <Pressable
          onPress={handleBackToFlow}
          style={({pressed}) => [
            styles.returnButton,
            pressed && styles.pressed,
          ]}
        >
          <Text style={styles.returnButtonText}>
            RETURN TO TRADING FLOW
          </Text>

          <Text style={styles.returnArrow}>
            ↗
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

  backendBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#111722',
    borderWidth: 1,
    borderColor: '#263043',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 5,
  },

  backendDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#68758E',
    marginRight: 5,
  },

  backendText: {
    color: '#68758E',
    fontSize: 5.5,
    fontWeight: '900',
    letterSpacing: 0.5,
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
    alignItems: 'center',
  },

  stageReferenceNumber: {
    color: '#7083FF',
    fontSize: 13,
    fontWeight: '900',
  },

  stageReferenceText: {
    color: '#53617A',
    fontSize: 5.5,
    fontWeight: '900',
    letterSpacing: 0.8,
    marginTop: 1,
  },

  executionCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderRadius: 20,
    padding: 18,
    marginBottom: 26,
  },

  executionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  executionEyebrow: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.4,
  },

  executionTitle: {
    color: '#FFFFFF',
    fontSize: 27,
    fontWeight: '900',
    marginTop: 4,
    letterSpacing: 0.5,
  },

  statusIndicator: {
    width: 42,
    height: 42,
    borderRadius: 21,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },

  statusIndicatorDot: {
    width: 9,
    height: 9,
    borderRadius: 5,
  },

  executionDescription: {
    color: '#68758E',
    fontSize: 9,
    lineHeight: 15,
    marginTop: 16,
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

  stepsCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 17,
    paddingHorizontal: 14,
    marginBottom: 26,
  },

  stepRow: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 78,
    paddingVertical: 9,
  },

  stepDivider: {
    borderBottomWidth: 1,
    borderBottomColor: '#111827',
  },

  stepNumber: {
    width: 31,
    height: 31,
    borderRadius: 9,
    backgroundColor: '#111722',
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },

  stepNumberText: {
    fontSize: 7,
    fontWeight: '900',
  },

  stepContent: {
    flex: 1,
    paddingRight: 8,
  },

  stepTitle: {
    color: '#FFFFFF',
    fontSize: 8.5,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  stepDescription: {
    color: '#68758E',
    fontSize: 7.5,
    lineHeight: 12,
    marginTop: 3,
  },

  stepStatus: {
    borderWidth: 1,
    borderRadius: 7,
    paddingHorizontal: 7,
    paddingVertical: 5,
  },

  stepStatusText: {
    fontSize: 5.5,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  connectionCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 17,
    padding: 15,
    marginBottom: 26,
  },

  connectionRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  connectionIcon: {
    width: 43,
    height: 43,
    borderRadius: 12,
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
  },

  connectionIconText: {
    color: '#7083FF',
    fontSize: 8,
    fontWeight: '900',
  },

  connectionContent: {
    flex: 1,
  },

  connectionTitle: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  connectionDescription: {
    color: '#68758E',
    fontSize: 7.5,
    lineHeight: 12,
    marginTop: 3,
  },

  connectionStatus: {
    alignItems: 'flex-end',
  },

  connectionStatusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#68758E',
    marginBottom: 4,
  },

  connectionStatusText: {
    color: '#68758E',
    fontSize: 5.5,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  orderCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 17,
    paddingHorizontal: 16,
    marginBottom: 25,
  },

  orderRow: {
    minHeight: 48,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: 1,
    borderBottomColor: '#111827',
  },

  orderLabel: {
    color: '#56627A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  orderValue: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '800',
  },

  orderValueMuted: {
    color: '#53617A',
    fontSize: 9,
    fontWeight: '800',
  },

  safetyCard: {
    flexDirection: 'row',
    backgroundColor: '#0B1020',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 17,
    padding: 15,
    marginBottom: 25,
  },

  safetyIcon: {
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

  safetyIconText: {
    color: '#7083FF',
    fontSize: 13,
    fontWeight: '900',
  },

  safetyContent: {
    flex: 1,
  },

  safetyTitle: {
    color: '#FFFFFF',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  safetyText: {
    color: '#68758E',
    fontSize: 8.5,
    lineHeight: 14,
    marginTop: 4,
  },

  completeCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#263043',
    borderRadius: 17,
    padding: 17,
    marginBottom: 16,
  },

  completeEyebrow: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.5,
  },

  completeTitle: {
    color: '#FFFFFF',
    fontSize: 22,
    fontWeight: '900',
    marginTop: 4,
  },

  completeText: {
    color: '#68758E',
    fontSize: 8.5,
    lineHeight: 15,
    marginTop: 7,
  },

  returnButton: {
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

  returnButtonText: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  returnArrow: {
    color: '#7083FF',
    fontSize: 19,
    fontWeight: '700',
  },
});
