import React from 'react';
import {
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import {useSafeAreaInsets} from 'react-native-safe-area-context';

import {RootStackParamList} from '../navigation/navigationTypes';
import {BRANDING} from '../config/branding';

type HistoryScreenProps = NativeStackScreenProps<
  RootStackParamList,
  'History'
>;

type TradeDirection = 'BUY' | 'SELL';

type TradeStatus = 'OPEN' | 'CLOSED' | 'CANCELLED';

type TradeRecord = {
  id: string;
  symbol: string;
  direction: TradeDirection;
  entry: string;
  exit: string;
  stopLoss: string;
  takeProfit: string;
  profit: string;
  status: TradeStatus;
  date: string;
};

const HISTORY: TradeRecord[] = [];

function StatusBadge({
  status,
}: {
  status: TradeStatus;
}) {
  const statusStyle =
    status === 'CLOSED'
      ? styles.closedBadge
      : status === 'OPEN'
      ? styles.openBadge
      : styles.cancelledBadge;

  const textStyle =
    status === 'CLOSED'
      ? styles.closedText
      : status === 'OPEN'
      ? styles.openText
      : styles.cancelledText;

  return (
    <View style={[styles.statusBadge, statusStyle]}>
      <Text style={[styles.statusText, textStyle]}>
        {status}
      </Text>
    </View>
  );
}

function TradeCard({
  trade,
}: {
  trade: TradeRecord;
}) {
  const isBuy = trade.direction === 'BUY';

  return (
    <View style={styles.tradeCard}>
      <View style={styles.tradeHeader}>
        <View>
          <Text style={styles.symbol}>
            {trade.symbol}
          </Text>

          <Text
            style={[
              styles.direction,
              isBuy
                ? styles.buyText
                : styles.sellText,
            ]}>
            {isBuy ? '▲ BUY' : '▼ SELL'}
          </Text>
        </View>

        <View style={styles.tradeHeaderRight}>
          <StatusBadge status={trade.status} />

          <Text style={styles.date}>
            {trade.date}
          </Text>
        </View>
      </View>

      <View style={styles.priceGrid}>
        <View style={styles.priceItem}>
          <Text style={styles.priceLabel}>
            ENTRY
          </Text>
          <Text style={styles.priceValue}>
            {trade.entry}
          </Text>
        </View>

        <View style={styles.priceItem}>
          <Text style={styles.priceLabel}>
            EXIT
          </Text>
          <Text style={styles.priceValue}>
            {trade.exit}
          </Text>
        </View>

        <View style={styles.priceItem}>
          <Text style={styles.priceLabel}>
            STOP LOSS
          </Text>
          <Text style={styles.priceValue}>
            {trade.stopLoss}
          </Text>
        </View>

        <View style={styles.priceItem}>
          <Text style={styles.priceLabel}>
            TAKE PROFIT
          </Text>
          <Text style={styles.priceValue}>
            {trade.takeProfit}
          </Text>
        </View>
      </View>

      <View style={styles.tradeFooter}>
        <Text style={styles.profitLabel}>
          RESULT
        </Text>

        <Text
          style={[
            styles.profit,
            trade.profit.startsWith('+')
              ? styles.profitPositive
              : styles.profitNegative,
          ]}>
          {trade.profit}
        </Text>
      </View>
    </View>
  );
}

export default function HistoryScreen({
  route,
  navigation,
}: HistoryScreenProps) {
  const insets = useSafeAreaInsets();

  const user = route.params;

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[
          styles.scrollContent,
          {
            paddingTop: Math.max(
              insets.top,
              20,
            ),
            paddingBottom: Math.max(
              insets.bottom + 40,
              30,
            ),
          },
        ]}>

        <View style={styles.header}>
          <Pressable
            onPress={() => navigation.goBack()}
            style={styles.backButton}>
            <Text style={styles.backText}>
              ‹
            </Text>
          </Pressable>

          <View style={styles.headerText}>
            <Text style={styles.appName}>
              {BRANDING.appName}
            </Text>

            <Text style={styles.title}>
              TRADE HISTORY
            </Text>

            <Text style={styles.subtitle}>
              {user.firstName} • Historical trading activity
            </Text>
          </View>
        </View>

        <View style={styles.summaryCard}>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryValue}>
              —
            </Text>

            <Text style={styles.summaryLabel}>
              TOTAL TRADES
            </Text>
          </View>

          <View style={styles.summaryDivider} />

          <View style={styles.summaryItem}>
            <Text style={styles.summaryValue}>
              —
            </Text>

            <Text style={styles.summaryLabel}>
              WIN RATE
            </Text>
          </View>

          <View style={styles.summaryDivider} />

          <View style={styles.summaryItem}>
            <Text style={styles.summaryValue}>
              —
            </Text>

            <Text style={styles.summaryLabel}>
              NET RESULT
            </Text>
          </View>
        </View>

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            TRADING ACTIVITY
          </Text>

          <Text style={styles.sectionMeta}>
            BACKEND DATA
          </Text>
        </View>

        {HISTORY.length === 0 ? (
          <View style={styles.emptyCard}>
            <View style={styles.emptyIcon}>
              <Text style={styles.emptyIconText}>
                ↗
              </Text>
            </View>

            <Text style={styles.emptyTitle}>
              NO TRADING HISTORY
            </Text>

            <Text style={styles.emptyText}>
              Completed and active trades will appear
              here once trading history is provided by
              the BALLY TRADES BOT backend.
            </Text>
          </View>
        ) : (
          HISTORY.map(trade => (
            <TradeCard
              key={trade.id}
              trade={trade}
            />
          ))
        )}

        <View style={styles.notice}>
          <View style={styles.noticeDot} />

          <Text style={styles.noticeText}>
            Trade history is read-only. Records displayed
            here must come from the authenticated backend
            account and MT5 trading history.
          </Text>
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

  scrollContent: {
    paddingHorizontal: 18,
  },

  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 25,
  },

  backButton: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    marginTop: 5,
  },

  backText: {
    color: '#FFFFFF',
    fontSize: 28,
    lineHeight: 30,
    fontWeight: '300',
  },

  headerText: {
    flex: 1,
  },

  appName: {
    color: '#7083FF',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 2,
    marginBottom: 6,
  },

  title: {
    color: '#FFFFFF',
    fontSize: 25,
    fontWeight: '900',
    letterSpacing: 0.3,
  },

  subtitle: {
    color: '#69758E',
    fontSize: 10,
    marginTop: 6,
  },

  summaryCard: {
    minHeight: 92,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 17,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    marginBottom: 27,
  },

  summaryItem: {
    flex: 1,
    alignItems: 'center',
  },

  summaryValue: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '900',
  },

  summaryLabel: {
    color: '#69758E',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
    marginTop: 5,
  },

  summaryDivider: {
    width: 1,
    height: 35,
    backgroundColor: '#1B2435',
  },

  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 11,
  },

  sectionTitle: {
    color: '#A8B2C7',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 1.5,
  },

  sectionMeta: {
    color: '#56627A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  emptyCard: {
    minHeight: 210,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 30,
  },

  emptyIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#11182A',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 13,
  },

  emptyIconText: {
    color: '#7083FF',
    fontSize: 21,
    fontWeight: '800',
  },

  emptyTitle: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  emptyText: {
    color: '#647087',
    fontSize: 9,
    lineHeight: 16,
    textAlign: 'center',
    marginTop: 8,
  },

  tradeCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 17,
    padding: 15,
    marginBottom: 11,
  },

  tradeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },

  symbol: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '900',
  },

  direction: {
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 0.7,
    marginTop: 5,
  },

  buyText: {
    color: '#35E68A',
  },

  sellText: {
    color: '#FF7185',
  },

  tradeHeaderRight: {
    alignItems: 'flex-end',
  },

  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },

  closedBadge: {
    backgroundColor: '#0D211A',
  },

  openBadge: {
    backgroundColor: '#11182A',
  },

  cancelledBadge: {
    backgroundColor: '#281419',
  },

  statusText: {
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.6,
  },

  closedText: {
    color: '#35E68A',
  },

  openText: {
    color: '#7083FF',
  },

  cancelledText: {
    color: '#FF7185',
  },

  date: {
    color: '#59657C',
    fontSize: 7,
    marginTop: 6,
  },

  priceGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 17,
    paddingTop: 13,
    borderTopWidth: 1,
    borderTopColor: '#172032',
  },

  priceItem: {
    width: '50%',
    marginBottom: 12,
  },

  priceLabel: {
    color: '#59657C',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  priceValue: {
    color: '#A8B2C7',
    fontSize: 10,
    fontWeight: '800',
    marginTop: 4,
  },

  tradeFooter: {
    borderTopWidth: 1,
    borderTopColor: '#172032',
    paddingTop: 11,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },

  profitLabel: {
    color: '#59657C',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  profit: {
    fontSize: 13,
    fontWeight: '900',
  },

  profitPositive: {
    color: '#35E68A',
  },

  profitNegative: {
    color: '#FF7185',
  },

  notice: {
    marginTop: 15,
    backgroundColor: '#0B1020',
    borderRadius: 11,
    padding: 12,
    flexDirection: 'row',
    alignItems: 'flex-start',
  },

  noticeDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#7083FF',
    marginTop: 4,
    marginRight: 8,
  },

  noticeText: {
    flex: 1,
    color: '#66738C',
    fontSize: 8,
    lineHeight: 14,
  },
});

