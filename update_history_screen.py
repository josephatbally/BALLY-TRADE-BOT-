import os
import sys

def find_paths():
    if os.path.exists("src/screens/HistoryScreen.tsx"):
        return "src/api/historyApi.ts", "src/screens/HistoryScreen.tsx"
    elif os.path.exists("mobile/src/screens/HistoryScreen.tsx"):
        return "mobile/src/api/historyApi.ts", "mobile/src/screens/HistoryScreen.tsx"
    else:
        print("[ERROR] Could not locate HistoryScreen.tsx. Run from 'mobile' or repository root.")
        sys.exit(1)

api_path, screen_path = find_paths()

API_CONTENT = """import { apiRequest } from './client';

export interface HistorySummaryResponse {
  status: string;
  connected: boolean;
  days: number;
  win_rate: number;
  total_trades: number;
  wins: number;
  losses: number;
  profit_factor: number;
  net_profit: number;
}

export interface HistoryDeal {
  ticket: number;
  order: number;
  position_id: number;
  symbol: string;
  type: number; // 0 = BUY, 1 = SELL
  entry: number; // 0 = IN, 1 = OUT
  volume: number;
  price: number;
  profit: number;
  swap: number;
  commission: number;
  fee: number;
  comment?: string | null;
  time?: string | null;
  time_msc?: number;
}

export interface HistoryDealsResponse {
  status: string;
  connected: boolean;
  days: number;
  symbol?: string | null;
  count: number;
  deals: HistoryDeal[];
}

export async function getHistorySummary(days: number = 7): Promise<HistorySummaryResponse> {
  return apiRequest<HistorySummaryResponse>(`/api/v1/history/summary?days=${days}`);
}

export async function getHistoryDeals(days: number = 30, symbol?: string): Promise<HistoryDealsResponse> {
  const query = symbol ? `?days=${days}&symbol=${encodeURIComponent(symbol)}` : `?days=${days}`;
  return apiRequest<HistoryDealsResponse>(`/api/v1/history${query}`);
}
"""

SCREEN_CONTENT = """import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { RootStackParamList } from '../navigation/navigationTypes';
import {
  getHistoryDeals,
  getHistorySummary,
  HistoryDeal,
  HistorySummaryResponse,
} from '../api/historyApi';

type HistoryScreenProps = NativeStackScreenProps<
  RootStackParamList,
  'History'
>;

type FilterPeriod = 1 | 7 | 30 | 90;
type FilterOutcome = 'ALL' | 'PROFIT' | 'LOSS';

export const HistoryScreen: React.FC<HistoryScreenProps> = ({
  route,
  navigation,
}) => {
  const insets = useSafeAreaInsets();
  const user = route.params;

  const [period, setPeriod] = useState<FilterPeriod>(7);
  const [outcomeFilter, setOutcomeFilter] = useState<FilterOutcome>('ALL');

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [summary, setSummary] = useState<HistorySummaryResponse | null>(null);
  const [deals, setDeals] = useState<HistoryDeal[]>([]);

  const loadHistoryData = useCallback(async (selectedDays: FilterPeriod) => {
    try {
      setError(null);
      const [summaryRes, dealsRes] = await Promise.allSettled([
        getHistorySummary(selectedDays),
        getHistoryDeals(selectedDays),
      ]);

      if (summaryRes.status === 'fulfilled') {
        setSummary(summaryRes.value);
      }
      if (dealsRes.status === 'fulfilled') {
        setDeals(dealsRes.value?.deals || []);
      }
    } catch (err: any) {
      setError(err?.message || 'Unable to sync history with MT5');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    loadHistoryData(period);
  }, [period, loadHistoryData]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadHistoryData(period);
  }, [period, loadHistoryData]);

  // Filter deals based on outcome toggle
  const filteredDeals = useMemo(() => {
    if (!deals) return [];
    return deals.filter((deal) => {
      if (outcomeFilter === 'PROFIT') return deal.profit > 0;
      if (outcomeFilter === 'LOSS') return deal.profit < 0;
      return true;
    });
  }, [deals, outcomeFilter]);

  const formatCurrency = (val: number | undefined) => {
    if (val === undefined || isNaN(val)) return '$0.00';
    const prefix = val > 0 ? '+' : '';
    return `${prefix}$${val.toFixed(2)}`;
  };

  const formatTimestamp = (isoString?: string | null) => {
    if (!isoString) return '--:--';
    try {
      const d = new Date(isoString);
      return `${d.getMonth() + 1}/${d.getDate()} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } catch {
      return isoString;
    }
  };

  const netProfit = summary?.net_profit ?? 0;
  const isProfitPositive = netProfit >= 0;

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#05070D" />

      {/* Top Header Bar */}
      <View style={[styles.header, { paddingTop: Math.max(insets.top, 16) }]}>
        <Pressable
          style={styles.backButton}
          onPress={() => navigation.goBack()}
          hitSlop={12}
        >
          <Text style={styles.backButtonText} allowFontScaling={false}>
            ‹
          </Text>
        </Pressable>
        <View style={styles.headerTitleWrap}>
          <Text style={styles.headerTitle} allowFontScaling={false}>
            Trade History
          </Text>
          <Text style={styles.headerSubtitle} allowFontScaling={false}>
            {user?.firstName ? `${user.firstName}'s Audit Ledger` : 'MT5 Closed Deals Ledger'}
          </Text>
        </View>
        <View style={styles.connectionPill}>
          <View
            style={[
              styles.connectionDot,
              { backgroundColor: summary?.connected !== false ? '#35E68A' : '#EF4444' },
            ]}
          />
          <Text style={styles.connectionText} allowFontScaling={false}>
            {summary?.connected !== false ? 'MT5 SYNC' : 'OFFLINE'}
          </Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={[
          styles.scrollContent,
          { paddingBottom: Math.max(insets.bottom, 24) + 20 },
        ]}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#7083FF"
            colors={['#7083FF']}
          />
        }
      >
        {/* Performance Cockpit Card */}
        <View style={styles.summaryCard}>
          <View style={styles.summaryTopRow}>
            <View>
              <Text style={styles.summaryLabel} allowFontScaling={false}>
                NET REALIZED P&L ({period}D)
              </Text>
              <Text
                style={[
                  styles.summaryProfitValue,
                  { color: isProfitPositive ? '#35E68A' : '#EF4444' },
                ]}
                allowFontScaling={false}
              >
                {formatCurrency(netProfit)}
              </Text>
            </View>
            <View style={styles.winRateBadge}>
              <Text style={styles.winRateLabel} allowFontScaling={false}>
                WIN RATE
              </Text>
              <Text style={styles.winRateValue} allowFontScaling={false}>
                {summary?.win_rate !== undefined ? `${summary.win_rate.toFixed(1)}%` : '--%'}
              </Text>
            </View>
          </View>

          <View style={styles.summaryDivider} />

          <View style={styles.metricsGrid}>
            <View style={styles.metricItem}>
              <Text style={styles.metricTitle} allowFontScaling={false}>
                TOTAL DEALS
              </Text>
              <Text style={styles.metricVal} allowFontScaling={false}>
                {summary?.total_trades ?? deals.length}
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricTitle} allowFontScaling={false}>
                WINS / LOSSES
              </Text>
              <Text style={styles.metricVal} allowFontScaling={false}>
                <Text style={{ color: '#35E68A' }}>{summary?.wins ?? '--'}</Text>
                {' / '}
                <Text style={{ color: '#EF4444' }}>{summary?.losses ?? '--'}</Text>
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricTitle} allowFontScaling={false}>
                PROFIT FACTOR
              </Text>
              <Text style={styles.metricVal} allowFontScaling={false}>
                {summary?.profit_factor !== undefined ? summary.profit_factor.toFixed(2) : '--'}
              </Text>
            </View>
          </View>
        </View>

        {/* Lookback Period Filters */}
        <View style={styles.periodFilterRow}>
          {[
            { label: '1D', val: 1 as FilterPeriod },
            { label: '7D', val: 7 as FilterPeriod },
            { label: '30D', val: 30 as FilterPeriod },
            { label: '90D', val: 90 as FilterPeriod },
          ].map((item) => (
            <Pressable
              key={item.label}
              style={[
                styles.periodButton,
                period === item.val && styles.periodButtonActive,
              ]}
              onPress={() => setPeriod(item.val)}
            >
              <Text
                style={[
                  styles.periodButtonText,
                  period === item.val && styles.periodButtonTextActive,
                ]}
                allowFontScaling={false}
              >
                {item.label}
              </Text>
            </Pressable>
          ))}
        </View>

        {/* Outcome Filter Tabs */}
        <View style={styles.filterSection}>
          <Text style={styles.filterSectionTitle} allowFontScaling={false}>
            CLOSED ORDERS ({filteredDeals.length})
          </Text>
          <View style={styles.outcomeToggleWrap}>
            {(['ALL', 'PROFIT', 'LOSS'] as FilterOutcome[]).map((tab) => (
              <Pressable
                key={tab}
                style={[
                  styles.outcomeTab,
                  outcomeFilter === tab && styles.outcomeTabActive,
                ]}
                onPress={() => setOutcomeFilter(tab)}
              >
                <Text
                  style={[
                    styles.outcomeTabText,
                    outcomeFilter === tab && styles.outcomeTabTextActive,
                  ]}
                  allowFontScaling={false}
                >
                  {tab}
                </Text>
              </Pressable>
            ))}
          </View>
        </View>

        {/* Error Notice */}
        {error ? (
          <View style={styles.errorNotice}>
            <Text style={styles.errorNoticeText} allowFontScaling={false}>
              {error}
            </Text>
          </View>
        ) : null}

        {/* Loading Indicator */}
        {loading && !refreshing ? (
          <View style={styles.loadingWrap}>
            <ActivityIndicator size="small" color="#7083FF" />
            <Text style={styles.loadingText} allowFontScaling={false}>
              Retrieving MT5 historical records...
            </Text>
          </View>
        ) : null}

        {/* Deals List */}
        {!loading && filteredDeals.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateTitle} allowFontScaling={false}>
              No Closed Deals Found
            </Text>
            <Text style={styles.emptyStateSubtitle} allowFontScaling={false}>
              No completed trades match the selected lookback range.
            </Text>
          </View>
        ) : (
          filteredDeals.map((deal, idx) => {
            const isBuy = deal.type === 0;
            const dealProfit = deal.profit ?? 0;
            const isDealPositive = dealProfit >= 0;

            return (
              <View key={`${deal.ticket}-${idx}`} style={styles.dealCard}>
                <View style={styles.dealHeaderRow}>
                  <View style={styles.dealSymbolWrap}>
                    <Text style={styles.dealSymbol} allowFontScaling={false}>
                      {deal.symbol || 'SYMBOL'}
                    </Text>
                    <View
                      style={[
                        styles.sidePill,
                        {
                          backgroundColor: isBuy
                            ? 'rgba(53, 230, 138, 0.12)'
                            : 'rgba(239, 68, 68, 0.12)',
                          borderColor: isBuy ? '#35E68A' : '#EF4444',
                        },
                      ]}
                    >
                      <Text
                        style={[
                          styles.sidePillText,
                          { color: isBuy ? '#35E68A' : '#EF4444' },
                        ]}
                        allowFontScaling={false}
                      >
                        {isBuy ? 'BUY' : 'SELL'}
                      </Text>
                    </View>
                    <Text style={styles.volumeText} allowFontScaling={false}>
                      {deal.volume?.toFixed(2)} Lots
                    </Text>
                  </View>

                  <Text
                    style={[
                      styles.dealProfitText,
                      { color: isDealPositive ? '#35E68A' : '#EF4444' },
                    ]}
                    allowFontScaling={false}
                  >
                    {formatCurrency(dealProfit)}
                  </Text>
                </View>

                <View style={styles.dealDetailsRow}>
                  <View style={styles.detailCol}>
                    <Text style={styles.detailLabel} allowFontScaling={false}>
                      PRICE
                    </Text>
                    <Text style={styles.detailVal} allowFontScaling={false}>
                      {deal.price ? deal.price.toFixed(5).replace(/0+$/, '').replace(/\\.$/, '') : '--'}
                    </Text>
                  </View>
                  <View style={styles.detailCol}>
                    <Text style={styles.detailLabel} allowFontScaling={false}>
                      TICKET / ORDER
                    </Text>
                    <Text style={styles.detailVal} allowFontScaling={false}>
                      #{deal.ticket}
                    </Text>
                  </View>
                  <View style={[styles.detailCol, { alignItems: 'flex-end' }]}>
                    <Text style={styles.detailLabel} allowFontScaling={false}>
                      TIME (UTC)
                    </Text>
                    <Text style={styles.detailVal} allowFontScaling={false}>
                      {formatTimestamp(deal.time)}
                    </Text>
                  </View>
                </View>

                {(deal.swap !== 0 || deal.commission !== 0) && (
                  <View style={styles.dealFooterRow}>
                    <Text style={styles.feeText} allowFontScaling={false}>
                      Swap: {formatCurrency(deal.swap)} | Comm: {formatCurrency(deal.commission)}
                    </Text>
                  </View>
                )}
              </View>
            );
          })
        )}
      </ScrollView>
    </View>
  );
};

export default HistoryScreen;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#05070D',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#121726',
    backgroundColor: '#05070D',
  },
  backButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182033',
    alignItems: 'center',
    justifyContent: 'center',
  },
  backButtonText: {
    color: '#F8FAFC',
    fontSize: 24,
    lineHeight: 26,
    marginTop: -2,
    fontWeight: '300',
  },
  headerTitleWrap: {
    flex: 1,
    marginLeft: 12,
  },
  headerTitle: {
    color: '#F8FAFC',
    fontSize: 17,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  headerSubtitle: {
    color: '#7083FF',
    fontSize: 11,
    fontWeight: '500',
    marginTop: 2,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  connectionPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0A0E18',
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#182033',
  },
  connectionDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 6,
  },
  connectionText: {
    color: '#94A3B8',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.4,
  },
  scrollContent: {
    padding: 16,
  },
  summaryCard: {
    backgroundColor: '#0A0E18',
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: '#182033',
    marginBottom: 16,
  },
  summaryTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  summaryLabel: {
    color: '#94A3B8',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.6,
  },
  summaryProfitValue: {
    fontSize: 26,
    fontWeight: '800',
    marginTop: 4,
    letterSpacing: 0.5,
  },
  winRateBadge: {
    backgroundColor: 'rgba(112, 131, 255, 0.12)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: 'rgba(112, 131, 255, 0.3)',
    alignItems: 'center',
  },
  winRateLabel: {
    color: '#7083FF',
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  winRateValue: {
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: '800',
    marginTop: 2,
  },
  summaryDivider: {
    height: 1,
    backgroundColor: '#121726',
    marginVertical: 14,
  },
  metricsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metricItem: {
    flex: 1,
  },
  metricTitle: {
    color: '#64748B',
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  metricVal: {
    color: '#F8FAFC',
    fontSize: 13,
    fontWeight: '700',
    marginTop: 3,
  },
  periodFilterRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
    gap: 8,
  },
  periodButton: {
    flex: 1,
    backgroundColor: '#0A0E18',
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#182033',
    alignItems: 'center',
  },
  periodButtonActive: {
    backgroundColor: 'rgba(112, 131, 255, 0.16)',
    borderColor: '#7083FF',
  },
  periodButtonText: {
    color: '#64748B',
    fontSize: 12,
    fontWeight: '700',
  },
  periodButtonTextActive: {
    color: '#7083FF',
  },
  filterSection: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  filterSectionTitle: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  outcomeToggleWrap: {
    flexDirection: 'row',
    backgroundColor: '#0A0E18',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#182033',
    padding: 2,
  },
  outcomeTab: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  outcomeTabActive: {
    backgroundColor: '#182033',
  },
  outcomeTabText: {
    color: '#64748B',
    fontSize: 10,
    fontWeight: '700',
  },
  outcomeTabTextActive: {
    color: '#F8FAFC',
  },
  errorNotice: {
    backgroundColor: 'rgba(239, 68, 68, 0.12)',
    borderColor: '#EF4444',
    borderWidth: 1,
    padding: 10,
    borderRadius: 8,
    marginBottom: 12,
  },
  errorNoticeText: {
    color: '#EF4444',
    fontSize: 12,
    fontWeight: '500',
  },
  loadingWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
    gap: 10,
  },
  loadingText: {
    color: '#94A3B8',
    fontSize: 12,
  },
  emptyState: {
    backgroundColor: '#0A0E18',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#182033',
    padding: 24,
    alignItems: 'center',
    marginTop: 10,
  },
  emptyStateTitle: {
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: '700',
  },
  emptyStateSubtitle: {
    color: '#64748B',
    fontSize: 12,
    textAlign: 'center',
    marginTop: 4,
  },
  dealCard: {
    backgroundColor: '#0A0E18',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#182033',
    padding: 14,
    marginBottom: 10,
  },
  dealHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  dealSymbolWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  dealSymbol: {
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: '800',
    letterSpacing: 0.3,
  },
  sidePill: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    borderWidth: 1,
  },
  sidePillText: {
    fontSize: 9,
    fontWeight: '800',
  },
  volumeText: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '600',
  },
  dealProfitText: {
    fontSize: 15,
    fontWeight: '800',
  },
  dealDetailsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#121726',
  },
  detailCol: {
    flex: 1,
  },
  detailLabel: {
    color: '#64748B',
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.4,
  },
  detailVal: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '600',
    marginTop: 2,
  },
  dealFooterRow: {
    marginTop: 8,
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: '#121726',
  },
  feeText: {
    color: '#64748B',
    fontSize: 10,
  },
});
"""

with open(api_path, "w", encoding="utf-8") as f:
    f.write(API_CONTENT)
print(f"[OK] Successfully updated {api_path}")

with open(screen_path, "w", encoding="utf-8") as f:
    f.write(SCREEN_CONTENT)
print(f"[OK] Successfully updated {screen_path}")
