import os

# -------------------------------------------------------------
# 1. Wire mobile/src/api/appApi.ts
# -------------------------------------------------------------
app_api_candidates = [
    os.path.join("mobile", "src", "api", "appApi.ts"),
    os.path.join("src", "api", "appApi.ts"),
]
app_api_path = next((p for p in app_api_candidates if os.path.exists(p)), None)

if not app_api_path:
    print("[ERROR] Could not locate appApi.ts")
    exit(1)

with open(app_api_path, "r", encoding="utf-8") as f:
    api_content = f.read()

bot_telemetry_snippet = """
export type BotLogEntry = {
  timestamp: string;
  level: string;
  message: string;
  details?: Record<string, any>;
};

export type BotTelemetryResponse = {
  enabled: boolean;
  running: boolean;
  mt5_connected: boolean;
  scan_interval: number;
  min_confidence: number;
  max_positions: number;
  current_positions_count: number;
  risk_pct: number;
  default_lot: number;
  last_scan_time: string | null;
  balance: number;
  equity: number;
  recent_logs: BotLogEntry[];
  last_analysis_summary?: Record<string, any>;
};

export function getBotTelemetry() {
  return apiRequest<BotTelemetryResponse>('/api/v1/app/bot/telemetry');
}

export function toggleBotAutoTrade(enabled: boolean) {
  return apiRequest<{status: string; auto_trading_enabled: boolean}>('/api/v1/app/bot/toggle', {
    method: 'POST',
    body: JSON.stringify({enabled}),
  });
}
"""

if "getBotTelemetry" not in api_content:
    with open(app_api_path, "a", encoding="utf-8") as f:
        f.write("\n" + bot_telemetry_snippet.strip() + "\n")
    print(f"[OK] Appended bot telemetry methods to {app_api_path}")
else:
    print(f"[OK] {app_api_path} already has bot telemetry methods")

# -------------------------------------------------------------
# 2. Wire mobile/src/screens/BotControlScreen.tsx
# -------------------------------------------------------------
bot_screen_candidates = [
    os.path.join("mobile", "src", "screens", "BotControlScreen.tsx"),
    os.path.join("src", "screens", "BotControlScreen.tsx"),
]
bot_screen_path = next((p for p in bot_screen_candidates if os.path.exists(p)), None)

if not bot_screen_path:
    print("[ERROR] Could not locate BotControlScreen.tsx")
    exit(1)

bot_screen_content = """import React, {useCallback, useEffect, useState} from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  RefreshControl,
  ScrollView,
  StatusBar,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import {useSafeAreaInsets} from 'react-native-safe-area-context';

import {RootStackParamList} from '../navigation/navigationTypes';
import {
  BotTelemetryResponse,
  getBotTelemetry,
  toggleBotAutoTrade,
} from '../api/appApi';

type Props = NativeStackScreenProps<RootStackParamList, 'BotControl'>;

export default function BotControlScreen({navigation}: Props) {
  const insets = useSafeAreaInsets();
  const [telemetry, setTelemetry] = useState<BotTelemetryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [toggling, setToggling] = useState(false);

  const fetchTelemetry = useCallback(async () => {
    try {
      const data = await getBotTelemetry();
      setTelemetry(data);
    } catch (e) {
      // Keep previous telemetry during transient network blips
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 3500);
    return () => clearInterval(interval);
  }, [fetchTelemetry]);

  const handleToggle = (value: boolean) => {
    if (value) {
      Alert.alert(
        'Enable Live Auto-Trading?',
        'The bot will scan 6 markets continuously and execute trades via MT5 whenever high-confidence setups appear.',
        [
          {text: 'Cancel', style: 'cancel'},
          {
            text: 'Enable Auto-Trading',
            style: 'default',
            onPress: async () => {
              setToggling(true);
              try {
                await toggleBotAutoTrade(true);
                await fetchTelemetry();
              } catch (e) {
                Alert.alert('Error', 'Failed to enable auto-trading.');
              } finally {
                setToggling(false);
              }
            },
          },
        ],
      );
    } else {
      setToggling(true);
      toggleBotAutoTrade(false)
        .then(() => fetchTelemetry())
        .catch(() => Alert.alert('Error', 'Failed to pause auto-trading.'))
        .finally(() => setToggling(false));
    }
  };

  const isEnabled = telemetry?.enabled ?? false;
  const isConnected = telemetry?.mt5_connected ?? false;

  return (
    <View style={[styles.container, {paddingTop: insets.top}]}>
      <StatusBar barStyle="light-content" />

      {/* Header */}
      <View style={styles.header}>
        <Pressable
          style={styles.backButton}
          onPress={() => navigation.goBack()}
          hitSlop={12}>
          <Text style={styles.backButtonText} allowFontScaling={false}>
            ←
          </Text>
        </Pressable>
        <View style={styles.headerTitleWrap}>
          <Text style={styles.headerTitle} allowFontScaling={false}>
            BOT CONTROL COCKPIT
          </Text>
          <Text style={styles.headerSubtitle} allowFontScaling={false}>
            AUTONOMOUS EXECUTION ENGINE
          </Text>
        </View>
        <View
          style={[
            styles.statusPill,
            isEnabled ? styles.statusPillActive : styles.statusPillStandby,
          ]}>
          <View
            style={[
              styles.statusDot,
              isEnabled ? styles.statusDotActive : styles.statusDotStandby,
            ]}
          />
          <Text
            style={[
              styles.statusPillText,
              isEnabled ? styles.statusTextActive : styles.statusTextStandby,
            ]}
            allowFontScaling={false}>
            {isEnabled ? 'LIVE' : 'STANDBY'}
          </Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={[
          styles.scrollContent,
          {paddingBottom: insets.bottom + 24},
        ]}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              fetchTelemetry();
            }}
            tintColor="#7083FF"
          />
        }>
        {/* Master Switch Card */}
        <View style={styles.masterCard}>
          <View style={styles.masterHeader}>
            <View>
              <Text style={styles.masterTitle} allowFontScaling={false}>
                Auto-Trading Master Switch
              </Text>
              <Text style={styles.masterSubtitle} allowFontScaling={false}>
                {isEnabled
                  ? 'Daemon actively scanning & executing on MT5'
                  : 'Execution engine paused — observation only'}
              </Text>
            </View>
            {toggling ? (
              <ActivityIndicator color="#7083FF" />
            ) : (
              <Switch
                value={isEnabled}
                onValueChange={handleToggle}
                trackColor={{false: '#1D2538', true: '#264491'}}
                thumbColor={isEnabled ? '#35E68A' : '#71809A'}
              />
            )}
          </View>
        </View>

        {/* Engine Telemetry Grid */}
        <Text style={styles.sectionTitle} allowFontScaling={false}>
          ENGINE TELEMETRY
        </Text>
        <View style={styles.grid}>
          <View style={styles.gridCard}>
            <Text style={styles.gridLabel} allowFontScaling={false}>
              MT5 LINK
            </Text>
            <Text
              style={[
                styles.gridValue,
                {color: isConnected ? '#35E68A' : '#EF4444'},
              ]}
              allowFontScaling={false}>
              {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
            </Text>
            <Text style={styles.gridSub} allowFontScaling={false}>
              Broker Terminal
            </Text>
          </View>

          <View style={styles.gridCard}>
            <Text style={styles.gridLabel} allowFontScaling={false}>
              SCAN INTERVAL
            </Text>
            <Text style={styles.gridValue} allowFontScaling={false}>
              {telemetry?.scan_interval ?? 15}s
            </Text>
            <Text style={styles.gridSub} allowFontScaling={false}>
              Continuous Cycle
            </Text>
          </View>

          <View style={styles.gridCard}>
            <Text style={styles.gridLabel} allowFontScaling={false}>
              CONFIDENCE GATE
            </Text>
            <Text style={styles.gridValue} allowFontScaling={false}>
              ≥{telemetry?.min_confidence ?? 75}%
            </Text>
            <Text style={styles.gridSub} allowFontScaling={false}>
              SMC Confluence
            </Text>
          </View>

          <View style={styles.gridCard}>
            <Text style={styles.gridLabel} allowFontScaling={false}>
              POSITION CAP
            </Text>
            <Text style={styles.gridValue} allowFontScaling={false}>
              {telemetry?.current_positions_count ?? 0} /{' '}
              {telemetry?.max_positions ?? 3}
            </Text>
            <Text style={styles.gridSub} allowFontScaling={false}>
              Max Open Trades
            </Text>
          </View>

          <View style={styles.gridCard}>
            <Text style={styles.gridLabel} allowFontScaling={false}>
              RISK PER TRADE
            </Text>
            <Text style={styles.gridValue} allowFontScaling={false}>
              {telemetry?.risk_pct ?? 1.0}%
            </Text>
            <Text style={styles.gridSub} allowFontScaling={false}>
              Lot: {telemetry?.default_lot ?? 0.01}
            </Text>
          </View>

          <View style={styles.gridCard}>
            <Text style={styles.gridLabel} allowFontScaling={false}>
              BALANCE / EQUITY
            </Text>
            <Text
              style={[styles.gridValue, {color: '#35E68A'}]}
              allowFontScaling={false}>
              ${Number(telemetry?.equity ?? 0).toFixed(2)}
            </Text>
            <Text style={styles.gridSub} allowFontScaling={false}>
              Bal: ${Number(telemetry?.balance ?? 0).toFixed(2)}
            </Text>
          </View>
        </View>

        {/* Live Activity Feed */}
        <View style={styles.logsHeader}>
          <Text style={styles.sectionTitle} allowFontScaling={false}>
            DAEMON ACTIVITY FEED
          </Text>
          <Text style={styles.logsTime} allowFontScaling={false}>
            {telemetry?.last_scan_time ? `Last: ${telemetry.last_scan_time.slice(11)}` : 'Scanning...'}
          </Text>
        </View>

        <View style={styles.logsContainer}>
          {loading && !telemetry ? (
            <ActivityIndicator color="#7083FF" style={{marginVertical: 20}} />
          ) : telemetry?.recent_logs && telemetry.recent_logs.length > 0 ? (
            telemetry.recent_logs.map((log, index) => {
              const isError = log.level === 'ERROR' || log.level === 'EXECUTION_REJECTED';
              const isSuccess = log.level === 'EXECUTION_SUCCESS' || log.level === 'OPPORTUNITY';
              return (
                <View key={index} style={styles.logRow}>
                  <View
                    style={[
                      styles.logDot,
                      isError
                        ? styles.logDotRed
                        : isSuccess
                        ? styles.logDotGreen
                        : styles.logDotBlue,
                    ]}
                  />
                  <View style={styles.logBody}>
                    <View style={styles.logTop}>
                      <Text
                        style={[
                          styles.logLevel,
                          isError
                            ? {color: '#EF4444'}
                            : isSuccess
                            ? {color: '#35E68A'}
                            : {color: '#7083FF'},
                        ]}
                        allowFontScaling={false}>
                        {log.level}
                      </Text>
                      <Text style={styles.logTime} allowFontScaling={false}>
                        {log.timestamp.slice(11)}
                      </Text>
                    </View>
                    <Text style={styles.logMessage} allowFontScaling={false}>
                      {log.message}
                    </Text>
                  </View>
                </View>
              );
            })
          ) : (
            <Text style={styles.emptyLogs} allowFontScaling={false}>
              No events recorded yet. Engine idle.
            </Text>
          )}
        </View>
      </ScrollView>
    </View>
  );
}

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
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#121828',
  },
  backButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#0E1526',
    borderWidth: 1,
    borderColor: '#1D2740',
    alignItems: 'center',
    justifyContent: 'center',
  },
  backButtonText: {
    color: '#8995B1',
    fontSize: 16,
    fontWeight: '700',
  },
  headerTitleWrap: {
    flex: 1,
    marginLeft: 12,
  },
  headerTitle: {
    color: '#F0F3FA',
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 1.2,
  },
  headerSubtitle: {
    color: '#657493',
    fontSize: 8,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginTop: 2,
  },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
  },
  statusPillActive: {
    backgroundColor: 'rgba(53, 230, 138, 0.1)',
    borderColor: '#35E68A',
  },
  statusPillStandby: {
    backgroundColor: 'rgba(112, 131, 255, 0.1)',
    borderColor: '#7083FF',
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 5,
  },
  statusDotActive: {
    backgroundColor: '#35E68A',
  },
  statusDotStandby: {
    backgroundColor: '#7083FF',
  },
  statusPillText: {
    fontSize: 8,
    fontWeight: '800',
    letterSpacing: 0.6,
  },
  statusTextActive: {
    color: '#35E68A',
  },
  statusTextStandby: {
    color: '#7083FF',
  },
  scrollContent: {
    padding: 16,
  },
  masterCard: {
    backgroundColor: '#0A0E1A',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#182238',
    padding: 16,
    marginBottom: 20,
  },
  masterHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  masterTitle: {
    color: '#F0F3FA',
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  masterSubtitle: {
    color: '#7A8AA5',
    fontSize: 9,
    marginTop: 4,
    maxWidth: 240,
    lineHeight: 14,
  },
  sectionTitle: {
    color: '#7083FF',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.2,
    marginBottom: 10,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 22,
  },
  gridCard: {
    width: '48.8%',
    backgroundColor: '#0A0E1A',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#151E32',
    padding: 12,
  },
  gridLabel: {
    color: '#657493',
    fontSize: 8,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  gridValue: {
    color: '#F0F3FA',
    fontSize: 14,
    fontWeight: '900',
    marginTop: 6,
    letterSpacing: 0.5,
  },
  gridSub: {
    color: '#556481',
    fontSize: 8,
    marginTop: 4,
  },
  logsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  logsTime: {
    color: '#556481',
    fontSize: 9,
  },
  logsContainer: {
    backgroundColor: '#0A0E1A',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#151E32',
    padding: 12,
  },
  logRow: {
    flexDirection: 'row',
    paddingVertical: 9,
    borderBottomWidth: 1,
    borderBottomColor: '#121828',
  },
  logDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 5,
    marginRight: 10,
  },
  logDotBlue: {
    backgroundColor: '#7083FF',
  },
  logDotGreen: {
    backgroundColor: '#35E68A',
  },
  logDotRed: {
    backgroundColor: '#EF4444',
  },
  logBody: {
    flex: 1,
  },
  logTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  logLevel: {
    fontSize: 8,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  logTime: {
    color: '#4B5872',
    fontSize: 8,
  },
  logMessage: {
    color: '#C0C8DA',
    fontSize: 9,
    marginTop: 3,
    lineHeight: 14,
  },
  emptyLogs: {
    color: '#556481',
    fontSize: 9,
    textAlign: 'center',
    paddingVertical: 18,
  },
});
"""

with open(bot_screen_path, "w", encoding="utf-8") as f:
    f.write(bot_screen_content)
print(f"[OK] Successfully wrote {bot_screen_path}")
