
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

import type {
  NativeStackScreenProps,
} from '@react-navigation/native-stack';

import {
  RootStackParamList,
  FlowSymbol,
} from '../navigation/navigationTypes';

type Props = NativeStackScreenProps<
  RootStackParamList,
  'MainTabs'
>;

type StageStatus =
  | 'READY'
  | 'AVAILABLE'
  | 'WAITING';

type FlowStage = {
  number: string;
  title: string;
  description: string;
  status: StageStatus;
  route:
    | 'FlowMarketSelection'
    | 'FlowAnalysis'
    | 'FlowConfluence'
    | 'FlowConfidence'
    | 'FlowDecision'
    | 'FlowValidation'
    | 'FlowExecution';
};

const DEFAULT_SYMBOL: FlowSymbol = 'XAUUSD';

const pipeline: FlowStage[] = [
  {
    number: '01',
    title: 'MARKET',
    description:
      'Select the market that will drive the complete intelligence flow.',
    status: 'READY',
    route: 'FlowMarketSelection',
  },
  {
    number: '02',
    title: 'ANALYSIS',
    description:
      'H4 → H1 → M15 top-down analysis with candlestick data.',
    status: 'AVAILABLE',
    route: 'FlowAnalysis',
  },
  {
    number: '03',
    title: 'CONFLUENCE',
    description:
      'SMC, supply & demand, volume profile, volatility and market session.',
    status: 'AVAILABLE',
    route: 'FlowConfluence',
  },
  {
    number: '04',
    title: 'CONFIDENCE',
    description:
      'AI confidence derived from technical intelligence and market conditions.',
    status: 'AVAILABLE',
    route: 'FlowConfidence',
  },
  {
    number: '05',
    title: 'DECISION',
    description:
      'Final trading decision: BUY, SELL or NO TRADE.',
    status: 'WAITING',
    route: 'FlowDecision',
  },
  {
    number: '06',
    title: 'VALIDATION',
    description:
      'Risk, intelligent lot sizing, margin and broker safety validation.',
    status: 'WAITING',
    route: 'FlowValidation',
  },
  {
    number: '07',
    title: 'EXECUTION',
    description:
      'MT5 execution status controlled by the backend execution layer.',
    status: 'WAITING',
    route: 'FlowExecution',
  },
];

function getStatusStyle(status: StageStatus) {
  if (status === 'READY') {
    return {
      text: '#35E68A',
      background: '#0A1713',
      border: '#203A32',
    };
  }

  if (status === 'AVAILABLE') {
    return {
      text: '#7083FF',
      background: '#10183D',
      border: '#263A91',
    };
  }

  return {
    text: '#68748D',
    background: '#111722',
    border: '#263043',
  };
}

export default function FlowScreen({
  navigation,
  route,
}: Props) {
  const insets = useSafeAreaInsets();

  const user = route.params;

  const selectedSymbol: FlowSymbol = DEFAULT_SYMBOL;

  const handleStagePress = (stage: FlowStage) => {
    if (stage.route === 'FlowMarketSelection') {
      navigation.getParent()?.navigate('FlowMarketSelection', {
        user,
      });

      return;
    }

    navigation.getParent()?.navigate(stage.route, {
      user,
      symbol: selectedSymbol,
    } as never);
  };

  const handleMarketPress = () => {
    navigation.getParent()?.navigate('FlowMarketSelection', {
      user,
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
            paddingTop: Math.max(insets.top, 24),
            paddingBottom: Math.max(insets.bottom, 30),
          },
        ]}
      >
        {/* HEADER */}

        <View style={styles.header}>
          <View style={styles.headerText}>
            <Text style={styles.eyebrow}>
              BALLY FLOW
            </Text>

            <Text style={styles.title}>
              Trading Intelligence
            </Text>

            <Text style={styles.subtitle}>
              Market to execution decision pipeline
            </Text>
          </View>

          <View style={styles.liveBadge}>
            <View style={styles.liveDot} />

            <Text style={styles.liveText}>
              LIVE
            </Text>
          </View>
        </View>

        {/* ACTIVE MARKET */}

        <Pressable
          onPress={handleMarketPress}
          style={({pressed}) => [
            styles.marketCard,
            pressed && styles.pressed,
          ]}
        >
          <View style={styles.marketHeader}>
            <Text style={styles.cardLabel}>
              ACTIVE MARKET
            </Text>

            <Text style={styles.changeText}>
              CHANGE
            </Text>
          </View>

          <View style={styles.marketRow}>
            <View>
              <Text style={styles.marketSymbol}>
                {selectedSymbol}
              </Text>

              <Text style={styles.marketDescription}>
                Gold / US Dollar
              </Text>
            </View>

            <View style={styles.marketBadge}>
              <Text style={styles.marketBadgeText}>
                SELECTED
              </Text>
            </View>
          </View>
        </Pressable>

        {/* PIPELINE HEADER */}

        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>
              TRADING INTELLIGENCE
            </Text>

            <Text style={styles.sectionSubtitle}>
              Seven-stage analysis pipeline
            </Text>
          </View>

          <Text style={styles.sectionCount}>
            07 STAGES
          </Text>
        </View>

        {/* PIPELINE */}

        <View style={styles.pipeline}>
          {pipeline.map((stage, index) => {
            const statusStyle =
              getStatusStyle(stage.status);

            const isActive =
              stage.number === '01';

            return (
              <View
                key={stage.number}
                style={styles.stageWrapper}
              >
                <Pressable
                  onPress={() =>
                    handleStagePress(stage)
                  }
                  style={({pressed}) => [
                    styles.stageCard,
                    isActive && styles.stageActive,
                    pressed && styles.pressed,
                  ]}
                >
                  <View
                    style={[
                      styles.numberCircle,
                      isActive &&
                        styles.numberCircleActive,
                    ]}
                  >
                    <Text
                      style={[
                        styles.numberText,
                        isActive &&
                          styles.numberTextActive,
                      ]}
                    >
                      {stage.number}
                    </Text>
                  </View>

                  <View style={styles.stageContent}>
                    <View style={styles.stageTitleRow}>
                      <Text style={styles.stageTitle}>
                        {stage.title}
                      </Text>

                      <View
                        style={[
                          styles.statusBadge,
                          {
                            backgroundColor:
                              statusStyle.background,
                            borderColor:
                              statusStyle.border,
                          },
                        ]}
                      >
                        <Text
                          style={[
                            styles.stageStatus,
                            {
                              color:
                                statusStyle.text,
                            },
                          ]}
                        >
                          {stage.status}
                        </Text>
                      </View>
                    </View>

                    <Text style={styles.stageDescription}>
                      {stage.description}
                    </Text>
                  </View>

                  <Text style={styles.chevron}>
                    ›
                  </Text>
                </Pressable>

                {index <
                  pipeline.length - 1 && (
                  <View style={styles.connector}>
                    <View style={styles.connectorLine} />

                    <View style={styles.connectorDot} />
                  </View>
                )}
              </View>
            );
          })}
        </View>

        {/* FLOW ENGINE */}

        <View style={styles.infoCard}>
          <View style={styles.infoHeader}>
            <View style={styles.infoIndicator} />

            <Text style={styles.infoTitle}>
              FLOW ENGINE
            </Text>
          </View>

          <Text style={styles.infoText}>
            BALLY FLOW presents intelligence produced by the
            trading backend. Market analysis, SMC confluence,
            supply and demand, volume profile, volatility,
            confidence, validation and execution remain
            controlled by their respective backend layers.
          </Text>
        </View>

        {/* ARCHITECTURE */}

        <View style={styles.architectureCard}>
          <Text style={styles.architectureTitle}>
            INTELLIGENCE PATH
          </Text>

          <View style={styles.pathRow}>
            <Text style={styles.pathText}>
              MARKET
            </Text>

            <Text style={styles.pathArrow}>
              →
            </Text>

            <Text style={styles.pathText}>
              ANALYSIS
            </Text>

            <Text style={styles.pathArrow}>
              →
            </Text>

            <Text style={styles.pathText}>
              CONFLUENCE
            </Text>
          </View>

          <View style={styles.pathRow}>
            <Text style={styles.pathText}>
              CONFIDENCE
            </Text>

            <Text style={styles.pathArrow}>
              →
            </Text>

            <Text style={styles.pathText}>
              DECISION
            </Text>

            <Text style={styles.pathArrow}>
              →
            </Text>

            <Text style={styles.pathText}>
              VALIDATION
            </Text>
          </View>

          <View style={styles.finalPath}>
            <Text style={styles.pathText}>
              EXECUTION
            </Text>
          </View>
        </View>
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
    justifyContent: 'space-between',
    marginBottom: 24,
  },

  headerText: {
    flex: 1,
    paddingRight: 10,
  },

  eyebrow: {
    color: '#7083FF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 2,
  },

  title: {
    color: '#FFFFFF',
    fontSize: 26,
    fontWeight: '900',
    marginTop: 5,
  },

  subtitle: {
    color: '#77839D',
    fontSize: 11,
    lineHeight: 16,
    marginTop: 5,
  },

  liveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#203A32',
    backgroundColor: '#0A1713',
    borderRadius: 20,
    paddingHorizontal: 11,
    paddingVertical: 7,
  },

  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 6,
  },

  liveText: {
    color: '#35E68A',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1.2,
  },

  marketCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 18,
    padding: 18,
    marginBottom: 26,
  },

  marketHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  cardLabel: {
    color: '#68748D',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1.5,
  },

  changeText: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1,
  },

  marketRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 11,
  },

  marketSymbol: {
    color: '#FFFFFF',
    fontSize: 24,
    fontWeight: '900',
    letterSpacing: 1,
  },

  marketDescription: {
    color: '#69758D',
    fontSize: 10,
    marginTop: 4,
  },

  marketBadge: {
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#334BFF',
    borderRadius: 9,
    paddingHorizontal: 9,
    paddingVertical: 7,
  },

  marketBadgeText: {
    color: '#7083FF',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    marginBottom: 14,
  },

  sectionTitle: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1.5,
  },

  sectionSubtitle: {
    color: '#56627A',
    fontSize: 9,
    marginTop: 4,
  },

  sectionCount: {
    color: '#56627A',
    fontSize: 8,
    fontWeight: '800',
    letterSpacing: 1,
  },

  pipeline: {
    marginBottom: 24,
  },

  stageWrapper: {
    alignItems: 'stretch',
  },

  stageCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 16,
    padding: 14,
  },

  stageActive: {
    borderColor: '#334BFF',
  },

  numberCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#111722',
    borderWidth: 1,
    borderColor: '#263043',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },

  numberCircleActive: {
    backgroundColor: '#10183D',
    borderColor: '#334BFF',
  },

  numberText: {
    color: '#8995B1',
    fontSize: 9,
    fontWeight: '900',
  },

  numberTextActive: {
    color: '#7083FF',
  },

  stageContent: {
    flex: 1,
    paddingRight: 6,
  },

  stageTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  stageTitle: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1,
    flex: 1,
  },

  statusBadge: {
    borderWidth: 1,
    borderRadius: 7,
    paddingHorizontal: 6,
    paddingVertical: 4,
    marginLeft: 7,
  },

  stageStatus: {
    fontSize: 5.5,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  stageDescription: {
    color: '#69758D',
    fontSize: 9,
    lineHeight: 14,
    marginTop: 5,
  },

  chevron: {
    color: '#53617A',
    fontSize: 23,
    fontWeight: '300',
    marginLeft: 3,
  },

  connector: {
    height: 17,
    alignItems: 'center',
    justifyContent: 'center',
  },

  connectorLine: {
    position: 'absolute',
    width: 1,
    height: '100%',
    backgroundColor: '#263043',
  },

  connectorDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: '#33405A',
  },

  infoCard: {
    backgroundColor: '#080C15',
    borderWidth: 1,
    borderColor: '#151D2C',
    borderRadius: 16,
    padding: 17,
    marginBottom: 16,
  },

  infoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 9,
  },

  infoIndicator: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#7083FF',
    marginRight: 7,
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
    lineHeight: 16,
  },

  architectureCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 16,
    padding: 16,
  },

  architectureTitle: {
    color: '#56627A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.3,
    marginBottom: 13,
  },

  pathRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 9,
    flexWrap: 'wrap',
  },

  pathText: {
    color: '#8B96AD',
    fontSize: 6.5,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  pathArrow: {
    color: '#334BFF',
    fontSize: 10,
    marginHorizontal: 7,
  },

  finalPath: {
    alignItems: 'center',
    paddingTop: 2,
  },

  pressed: {
    opacity: 0.72,
  },
});