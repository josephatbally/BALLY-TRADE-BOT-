import { loadUserProfilePhoto } from '../utils/userPhoto';
import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
  TextInput,
  Image,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { getMarketQuotes, MarketQuote } from '../api/marketsApi';
import { getAccountInfo, AccountResponse } from '../api/accountApi';
import { getOpenPositions, OpenPosition } from '../api/positionsApi';
import { executeOrder, closePosition, closeAllPositions } from '../api/ordersApi';

const MARKETS = ['XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'XAGUSD', 'NASDAQ'];
const LOT_PRESETS = [0.01, 0.02, 0.05, 0.10];

export default function TradesScreen() {
  const navigation = useNavigation<any>();

  // State
  const [account, setAccount] = useState<AccountResponse | null>(null);
  const [positions, setPositions] = useState<OpenPosition[]>([]);
  const [quotes, setQuotes] = useState<Record<string, MarketQuote>>({});
  const [selectedSymbol, setSelectedSymbol] = useState<string>('XAUUSD');
  const [lotSize, setLotSize] = useState<string>('0.01');
  const [orderType, setOrderType] = useState<'BUY' | 'SELL'>('BUY');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [avatarUri, setAvatarUri] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const loadPhoto = () => {
      loadUserProfilePhoto()
        .then(photo => {
          if (active) setAvatarUri(photo);
        })
        .catch(() => {});
    };
    loadPhoto();
    const interval = setInterval(loadPhoto, 4000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  // Fetch telemetry & quotes
  const fetchAllData = useCallback(async () => {
    try {
      const [accRes, posRes, quoteRes] = await Promise.allSettled([
        getAccountInfo(),
        getOpenPositions(),
        getMarketQuotes(),
      ]);

      if (accRes.status === 'fulfilled' && accRes.value) {
        setAccount(accRes.value);
      }

      if (posRes.status === 'fulfilled' && posRes.value?.positions) {
        setPositions(posRes.value.positions);
      }

      if (quoteRes.status === 'fulfilled' && quoteRes.value?.quotes) {
        const map: Record<string, MarketQuote> = {};
        quoteRes.value.quotes.forEach((q: MarketQuote) => {
          map[q.symbol] = q;
        });
        setQuotes(map);
      }
    } catch {
      // Quiet recovery for smooth polling
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 3500);
    return () => clearInterval(interval);
  }, [fetchAllData]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchAllData();
  };

  // Selected market live quote
  const activeQuote = quotes[selectedSymbol] || null;
  const rawPrice = activeQuote?.raw_price ?? 0;
  const displayPrice = activeQuote?.price ?? (rawPrice > 0 ? rawPrice.toFixed(2) : '---');

  // Floating summary
  const totalFloatingPnl = useMemo(() => {
    return positions.reduce((acc, p) => acc + (p.profit || 0), 0);
  }, [positions]);

  const totalLots = useMemo(() => {
    return positions.reduce((acc, p) => acc + (p.volume || 0), 0);
  }, [positions]);

  // Order execution handler (accepts direct action to avoid state lag)
    // Instant execution on click — zero confirmation dialog delay
  const handleExecuteOrder = async (action: 'BUY' | 'SELL') => {
    setOrderType(action);
    const lot = parseFloat(lotSize);
    if (isNaN(lot) || lot <= 0) {
      Alert.alert('Invalid Lot', 'Please specify a valid trade volume.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await executeOrder({
        symbol: selectedSymbol,
        action: action,
        lot_size: lot,
      });

      if (res && (res.status === 'EXECUTED' || res.order_sent)) {
        Alert.alert('Order Dispatched', res.reason || 'Order submitted to execution pipeline.');
        fetchAllData();
      } else {
        Alert.alert('Execution Gate', res?.reason || 'Order blocked by safety checks.');
      }
    } catch (err: any) {
      Alert.alert('Order Failed', err?.message || 'Network request failed.');
    } finally {
      setSubmitting(false);
    }
  };

  // Close single position handler
  const handleClosePosition = async (ticket: number, sym: string) => {
    Alert.alert(
      'Close Position',
      `Close position #${ticket} on ${sym}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Close Trade',
          style: 'destructive',
          onPress: async () => {
            setSubmitting(true);
            try {
              const res = await closePosition(ticket);
              if (res && (res.status === 'SUCCESS' || res.closed)) {
                Alert.alert('Trade Closed', `Position #${ticket} has been closed.`);
                fetchAllData();
              } else {
                Alert.alert('Close Error', res?.reason || 'Could not close position.');
              }
            } catch (err: any) {
              Alert.alert('Close Failed', err?.message || 'Network error closing position.');
            } finally {
              setSubmitting(false);
            }
          },
        },
      ]
    );
  };

  // Close all positions handler
  const handleCloseAllPositions = async () => {
    Alert.alert(
      'Close All Positions',
      `Are you sure you want to close ALL ${positions.length} active positions?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Close All Now',
          style: 'destructive',
          onPress: async () => {
            setSubmitting(true);
            try {
              const res = await closeAllPositions();
              if (res && (res.status === 'SUCCESS' || (res.closed_count ?? 0) > 0)) {
                Alert.alert('All Positions Closed', `Successfully closed ${res.closed_count ?? 0} positions.`);
                fetchAllData();
              } else {
                Alert.alert('Close All', res?.reason || 'No positions closed.');
              }
            } catch (err: any) {
              Alert.alert('Close Failed', err?.message || 'Network error closing positions.');
            } finally {
              setSubmitting(false);
            }
          },
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
      {/* Background glow accents */}
      <View style={styles.ambientOrbBlue} pointerEvents="none" />
      <View style={styles.ambientOrbGreen} pointerEvents="none" />

      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle} allowFontScaling={false}>
            EXECUTION COCKPIT
          </Text>
          <Text style={styles.headerSubtitle} allowFontScaling={false}>
            DIRECT MT5 RISK & ORDER DESK
          </Text>
        </View>
        <View style={styles.headerRightGroup}>
          <View style={styles.statusBadge}>
            <View style={styles.statusDotLive} />
            <Text style={styles.statusBadgeText} allowFontScaling={false}>
              DESK ACTIVE
            </Text>
          </View>
          <TouchableOpacity
            style={styles.headerAvatarBtn}
            onPress={() => navigation.navigate('Profile')}
            accessibilityLabel="Open profile">
            {avatarUri ? (
              <Image source={{ uri: avatarUri }} style={styles.headerAvatarImg} />
            ) : (
              <Text style={styles.headerAvatarFallback}>⚡</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#7083FF" />}
        showsVerticalScrollIndicator={false}
      >
        {/* Floating Telemetry Hero Card */}
        <View style={styles.heroCard}>
          <View style={styles.heroRow}>
            <View>
              <Text style={styles.telemetryLabel} allowFontScaling={false}>
                NET FLOATING P&L
              </Text>
              <Text
                style={[
                  styles.telemetryValueLarge,
                  { color: totalFloatingPnl >= 0 ? '#35E68A' : '#EF4444' },
                ]}
                allowFontScaling={false}
              >
                {totalFloatingPnl >= 0 ? '+' : ''}${totalFloatingPnl.toFixed(2)}
              </Text>
            </View>
            <View style={styles.alignRight}>
              <Text style={styles.telemetryLabel} allowFontScaling={false}>
                ACTIVE EXPOSURE
              </Text>
              <Text style={styles.telemetryValueWhite} allowFontScaling={false}>
                {positions.length} POS ({totalLots.toFixed(2)} LOTS)
              </Text>
            </View>
          </View>

          <View style={styles.heroDivider} />

          <View style={styles.metricGrid}>
            <View style={styles.metricBox}>
              <Text style={styles.metricLabel} allowFontScaling={false}>BALANCE</Text>
              <Text style={styles.metricVal} allowFontScaling={false}>
                ${(account?.balance ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Text>
            </View>
            <View style={styles.metricBox}>
              <Text style={styles.metricLabel} allowFontScaling={false}>EQUITY</Text>
              <Text style={styles.metricVal} allowFontScaling={false}>
                ${(account?.equity ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Text>
            </View>
            <View style={styles.metricBox}>
              <Text style={styles.metricLabel} allowFontScaling={false}>FREE MARGIN</Text>
              <Text style={styles.metricVal} allowFontScaling={false}>
                ${(account?.free_margin ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Text>
            </View>
          </View>
        </View>

        {/* Order Execution Terminal */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle} allowFontScaling={false}>DIRECT EXECUTION STATION</Text>
          <TouchableOpacity
            onPress={() => navigation.navigate('FlowAnalysis', { symbol: selectedSymbol })}
          >
            <Text style={styles.sectionActionText} allowFontScaling={false}>ANALYZE IN FLOW →</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.terminalCard}>
          {/* Symbol Selector Pills */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.symbolScroll}>
            {MARKETS.map((sym) => {
              const isSelected = sym === selectedSymbol;
              return (
                <TouchableOpacity
                  key={sym}
                  style={[styles.symbolPill, isSelected && styles.symbolPillActive]}
                  onPress={() => setSelectedSymbol(sym)}
                >
                  <Text
                    style={[styles.symbolPillText, isSelected && styles.symbolPillTextActive]}
                    allowFontScaling={false}
                  >
                    {sym}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>

          {/* Pricing Row */}
          <View style={styles.pricingRow}>
            <View style={styles.priceColumn}>
              <Text style={styles.priceTypeLabel} allowFontScaling={false}>SELECTED ASSET</Text>
              <Text style={styles.selectedSymbolTitle} allowFontScaling={false}>{selectedSymbol}</Text>
            </View>
            <View style={styles.priceBadge}>
              <Text style={styles.priceVal} allowFontScaling={false}>
                {displayPrice}
              </Text>
            </View>
            <View style={[styles.priceColumn, styles.alignRight]}>
              <Text style={styles.priceTypeLabel} allowFontScaling={false}>DIRECTION</Text>
              <Text
                style={[
                  styles.directionVal,
                  { color: activeQuote?.direction === 'BULLISH' ? '#35E68A' : '#EF4444' },
                ]}
                allowFontScaling={false}
              >
                {activeQuote?.direction || 'NEUTRAL'}
              </Text>
            </View>
          </View>

          {/* Lot Size Selector */}
          <View style={styles.lotContainer}>
            <Text style={styles.lotLabel} allowFontScaling={false}>VOLUME (LOTS)</Text>
            <View style={styles.lotRow}>
              {LOT_PRESETS.map((preset) => {
                const isSelected = parseFloat(lotSize) === preset;
                return (
                  <TouchableOpacity
                    key={preset}
                    style={[styles.presetButton, isSelected && styles.presetButtonActive]}
                    onPress={() => setLotSize(preset.toString())}
                  >
                    <Text
                      style={[styles.presetText, isSelected && styles.presetTextActive]}
                      allowFontScaling={false}
                    >
                      {preset.toFixed(2)}
                    </Text>
                  </TouchableOpacity>
                );
              })}
              <TextInput
                style={styles.lotInput}
                value={lotSize}
                onChangeText={setLotSize}
                keyboardType="decimal-pad"
                placeholder="Custom"
                placeholderTextColor="#64748B"
                allowFontScaling={false}
              />
            </View>
          </View>

          {/* Order Action Buttons */}
          <View style={styles.actionButtonRow}>
            <TouchableOpacity
              style={[
                styles.executeBtn,
                styles.buyBtn,
                submitting && styles.btnDisabled,
              ]}
              disabled={submitting}
              onPress={() => handleExecuteOrder('BUY')}
            >
              <Text style={styles.executeBtnTitle} allowFontScaling={false}>BUY / LONG</Text>
              <Text style={styles.executeBtnSub} allowFontScaling={false}>
                 {displayPrice}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.executeBtn,
                styles.sellBtn,
                submitting && styles.btnDisabled,
              ]}
              disabled={submitting}
              onPress={() => handleExecuteOrder('SELL')}
            >
              <Text style={styles.executeBtnTitle} allowFontScaling={false}>SELL / SHORT</Text>
              <Text style={styles.executeBtnSub} allowFontScaling={false}>
                 {displayPrice}
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Live Active Positions */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle} allowFontScaling={false}>
            ACTIVE POSITIONS ({positions.length})
          </Text>
          {positions.length > 0 && (
            <TouchableOpacity
              style={styles.closeAllBtn}
              onPress={handleCloseAllPositions}
              disabled={submitting}
            >
              <Text style={styles.closeAllBtnText} allowFontScaling={false}>
                CLOSE ALL ({positions.length})
              </Text>
            </TouchableOpacity>
          )}
        </View>

        {positions.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyTitle} allowFontScaling={false}>NO OPEN POSITIONS</Text>
            <Text style={styles.emptySub} allowFontScaling={false}>
              Execute a manual order or monitor automated Flow signals.
            </Text>
          </View>
        ) : (
          positions.map((pos) => {
            const isProfit = (pos.profit || 0) >= 0;
            const side = (pos.type || 'BUY').toString().toUpperCase();

            return (
              <View key={pos.ticket} style={styles.ticketCard}>
                <View style={styles.ticketTopRow}>
                  <View style={styles.ticketTagRow}>
                    <View
                      style={[
                        styles.sideTag,
                        { backgroundColor: side.includes('BUY') ? '#10B98125' : '#EF444425' },
                      ]}
                    >
                      <Text
                        style={[
                          styles.sideTagText,
                          { color: side.includes('BUY') ? '#35E68A' : '#EF4444' },
                        ]}
                        allowFontScaling={false}
                      >
                        {side}
                      </Text>
                    </View>
                    <Text style={styles.ticketSymbol} allowFontScaling={false}>{pos.symbol}</Text>
                    <Text style={styles.ticketVolume} allowFontScaling={false}>{pos.volume.toFixed(2)} lots</Text>
                  </View>
                  <View style={styles.profitAndCloseCol}>
                    <Text
                      style={[styles.ticketProfit, { color: isProfit ? '#35E68A' : '#EF4444' }]}
                      allowFontScaling={false}
                    >
                      {isProfit ? '+' : ''}${(pos.profit || 0).toFixed(2)}
                    </Text>
                    <TouchableOpacity
                      style={styles.ticketCloseBtn}
                      onPress={() => handleClosePosition(pos.ticket, pos.symbol)}
                      disabled={submitting}
                    >
                      <Text style={styles.ticketCloseBtnText} allowFontScaling={false}>CLOSE</Text>
                    </TouchableOpacity>
                  </View>
                </View>

                <View style={styles.ticketDetailsRow}>
                  <Text style={styles.ticketDetailText} allowFontScaling={false}>
                    Open: {pos.open_price?.toFixed(pos.symbol.includes('JPY') ? 3 : 2)}
                  </Text>
                  <Text style={styles.ticketDetailText} allowFontScaling={false}>
                    Cur: {pos.current_price?.toFixed(pos.symbol.includes('JPY') ? 3 : 2)}
                  </Text>
                  <Text style={styles.ticketDetailText} allowFontScaling={false}>
                    SL: {pos.stop_loss ? pos.stop_loss.toFixed(2) : '---'}
                  </Text>
                  <Text style={styles.ticketDetailText} allowFontScaling={false}>
                    TP: {pos.take_profit ? pos.take_profit.toFixed(2) : '---'}
                  </Text>
                  <Text style={styles.ticketDetailText} allowFontScaling={false}>
                    #{pos.ticket}
                  </Text>
                </View>
              </View>
            );
          })
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#05070D',
  },
  ambientOrbBlue: {
    position: 'absolute',
    top: -60,
    left: -40,
    width: 220,
    height: 220,
    borderRadius: 110,
    backgroundColor: '#7083FF12',
  },
  ambientOrbGreen: {
    position: 'absolute',
    top: 150,
    right: -50,
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: '#35E68A0A',
  },
  headerRightGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  headerAvatarBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#0F1626',
    borderWidth: 1.5,
    borderColor: '#7083FF40',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  headerAvatarImg: {
    width: '100%',
    height: '100%',
    borderRadius: 18,
  },
  headerAvatarFallback: {
    color: '#7083FF',
    fontSize: 14,
    fontWeight: '700',
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 54,
    paddingBottom: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#131D31',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: 1.5,
  },
  headerSubtitle: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 2,
    letterSpacing: 1,
    fontWeight: '600',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#10B98115',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#10B98135',
  },
  statusDotLive: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#10B981',
    marginRight: 6,
  },
  statusBadgeText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#10B981',
    letterSpacing: 0.8,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  heroCard: {
    backgroundColor: '#0A0E18',
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: '#1E293B',
    marginBottom: 20,
  },
  heroRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  telemetryLabel: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  telemetryValueLarge: {
    fontSize: 26,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  telemetryValueWhite: {
    fontSize: 14,
    fontWeight: '700',
    color: '#E2E8F0',
    marginTop: 6,
  },
  alignRight: {
    alignItems: 'flex-end',
  },
  heroDivider: {
    height: 1,
    backgroundColor: '#1E293B',
    marginVertical: 14,
  },
  metricGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metricBox: {
    flex: 1,
  },
  metricLabel: {
    fontSize: 10,
    color: '#64748B',
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  metricVal: {
    fontSize: 13,
    color: '#FFFFFF',
    fontWeight: '700',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: '#94A3B8',
    letterSpacing: 1.2,
  },
  sectionActionText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#7083FF',
    letterSpacing: 0.5,
  },
  terminalCard: {
    backgroundColor: '#0A0E18',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1E293B',
    marginBottom: 24,
  },
  symbolScroll: {
    marginBottom: 16,
  },
  symbolPill: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 8,
    backgroundColor: '#131D31',
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#1E293B',
  },
  symbolPillActive: {
    backgroundColor: '#7083FF22',
    borderColor: '#7083FF',
  },
  symbolPillText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#94A3B8',
  },
  symbolPillTextActive: {
    color: '#7083FF',
  },
  pricingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#05070D',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#131D31',
    marginBottom: 16,
  },
  priceColumn: {
    flex: 1,
  },
  priceTypeLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: '#64748B',
    marginBottom: 2,
  },
  selectedSymbolTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  priceBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
    backgroundColor: '#131D31',
  },
  priceVal: {
    fontSize: 16,
    fontWeight: '800',
    color: '#35E68A',
  },
  directionVal: {
    fontSize: 13,
    fontWeight: '800',
  },
  lotContainer: {
    marginBottom: 16,
  },
  lotLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#64748B',
    marginBottom: 8,
    letterSpacing: 0.5,
  },
  lotRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  presetButton: {
    flex: 1,
    paddingVertical: 9,
    borderRadius: 8,
    backgroundColor: '#131D31',
    alignItems: 'center',
    marginRight: 6,
    borderWidth: 1,
    borderColor: '#1E293B',
  },
  presetButtonActive: {
    backgroundColor: '#7083FF20',
    borderColor: '#7083FF',
  },
  presetText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#94A3B8',
  },
  presetTextActive: {
    color: '#7083FF',
  },
  lotInput: {
    width: 68,
    height: 38,
    backgroundColor: '#05070D',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#1E293B',
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
    textAlign: 'center',
    paddingHorizontal: 6,
  },
  actionButtonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  executeBtn: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buyBtn: {
    backgroundColor: '#10B981',
    marginRight: 6,
  },
  sellBtn: {
    backgroundColor: '#EF4444',
    marginLeft: 6,
  },
  btnDisabled: {
    opacity: 0.5,
  },
  executeBtnTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: 1,
  },
  executeBtnSub: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFFCC',
    marginTop: 2,
  },
  emptyContainer: {
    backgroundColor: '#0A0E18',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#1E293B',
  },
  emptyTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#64748B',
    letterSpacing: 1,
    marginBottom: 4,
  },
  emptySub: {
    fontSize: 11,
    color: '#475569',
    textAlign: 'center',
  },
  ticketCard: {
    backgroundColor: '#0A0E18',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: '#1E293B',
    marginBottom: 10,
  },
  ticketTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  ticketTagRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  sideTag: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginRight: 8,
  },
  sideTagText: {
    fontSize: 10,
    fontWeight: '800',
  },
  ticketSymbol: {
    fontSize: 14,
    fontWeight: '800',
    color: '#FFFFFF',
    marginRight: 8,
  },
  ticketVolume: {
    fontSize: 12,
    fontWeight: '600',
    color: '#94A3B8',
  },
  ticketProfit: {
    fontSize: 16,
    fontWeight: '800',
  },
  ticketDetailsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderTopWidth: 1,
    borderColor: '#131D31',
  },
  ticketDetailText: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '600',
  },

  closeAllBtn: {
    backgroundColor: '#EF44441F',
    borderWidth: 1,
    borderColor: '#EF444460',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  closeAllBtnText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#EF4444',
    letterSpacing: 0.8,
  },
  profitAndCloseCol: {
    alignItems: 'flex-end',
    gap: 4,
  },
  ticketCloseBtn: {
    backgroundColor: '#EF444422',
    borderWidth: 1,
    borderColor: '#EF444455',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  ticketCloseBtnText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#EF4444',
    letterSpacing: 0.5,
  },
});
