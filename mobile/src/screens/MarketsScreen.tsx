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

type Market = {
  symbol: string;
  name: string;
  category: string;
  price: string;
  change: string;
  direction: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  status: 'ACTIVE' | 'WAITING';
};

const MARKETS: Market[] = [
  {
    symbol: 'XAUUSD',
    name: 'Gold / US Dollar',
    category: 'METALS',
    price: '—',
    change: '—',
    direction: 'NEUTRAL',
    status: 'ACTIVE',
  },
  {
    symbol: 'EURUSD',
    name: 'Euro / US Dollar',
    category: 'FOREX',
    price: '—',
    change: '—',
    direction: 'NEUTRAL',
    status: 'ACTIVE',
  },
  {
    symbol: 'GBPUSD',
    name: 'British Pound / US Dollar',
    category: 'FOREX',
    price: '—',
    change: '—',
    direction: 'NEUTRAL',
    status: 'ACTIVE',
  },
  {
    symbol: 'USDJPY',
    name: 'US Dollar / Japanese Yen',
    category: 'FOREX',
    price: '—',
    change: '—',
    direction: 'NEUTRAL',
    status: 'ACTIVE',
  },
  {
    symbol: 'XAGUSD',
    name: 'Silver / US Dollar',
    category: 'METALS',
    price: '—',
    change: '—',
    direction: 'NEUTRAL',
    status: 'ACTIVE',
  },
  {
    symbol: 'NASDAQ',
    name: 'Nasdaq Index',
    category: 'INDEX',
    price: '—',
    change: '—',
    direction: 'NEUTRAL',
    status: 'ACTIVE',
  },
];

export default function MarketsScreen() {
  const insets = useSafeAreaInsets();

  const handleMarketPress = (market: Market) => {
    // Reserved for market-analysis navigation.
    console.log('Selected market:', market.symbol);
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
            paddingTop: Math.max(insets.top, 24),
            paddingBottom: Math.max(insets.bottom, 30),
          },
        ]}>

        {/* HEADER */}
        <View style={styles.header}>
          <View>
            <Text style={styles.eyebrow}>BALLY FLOW</Text>

            <Text style={styles.title}>
              Markets
            </Text>

            <Text style={styles.subtitle}>
              Monitor the markets connected to your trading engine.
            </Text>
          </View>

          <View style={styles.connectionBadge}>
            <View style={styles.connectionDot} />

            <Text style={styles.connectionText}>
              LIVE
            </Text>
          </View>
        </View>

        {/* MARKET OVERVIEW */}
        <View style={styles.overviewCard}>
          <View style={styles.overviewTop}>
            <View>
              <Text style={styles.overviewLabel}>
                MARKET UNIVERSE
              </Text>

              <Text style={styles.overviewTitle}>
                6 Markets
              </Text>
            </View>

            <View style={styles.statusPill}>
              <Text style={styles.statusPillText}>
                MONITORING
              </Text>
            </View>
          </View>

          <View style={styles.overviewDivider} />

          <View style={styles.overviewStats}>
            <View style={styles.overviewStat}>
              <Text style={styles.statValue}>06</Text>
              <Text style={styles.statLabel}>MARKETS</Text>
            </View>

            <View style={styles.statSeparator} />

            <View style={styles.overviewStat}>
              <Text style={styles.statValue}>03</Text>
              <Text style={styles.statLabel}>FOREX</Text>
            </View>

            <View style={styles.statSeparator} />

            <View style={styles.overviewStat}>
              <Text style={styles.statValue}>02</Text>
              <Text style={styles.statLabel}>METALS</Text>
            </View>

            <View style={styles.statSeparator} />

            <View style={styles.overviewStat}>
              <Text style={styles.statValue}>01</Text>
              <Text style={styles.statLabel}>INDEX</Text>
            </View>
          </View>
        </View>

        {/* SECTION HEADER */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            TRACKED MARKETS
          </Text>

          <Text style={styles.sectionMeta}>
            H4 • H1 • M15
          </Text>
        </View>

        {/* MARKET LIST */}
        <View style={styles.marketList}>
          {MARKETS.map((market) => (
            <Pressable
              key={market.symbol}
              onPress={() => handleMarketPress(market)}
              accessibilityRole="button"
              accessibilityLabel={`Open ${market.symbol}`}
              style={({pressed}) => [
                styles.marketCard,
                pressed && styles.marketCardPressed,
              ]}>

              <View style={styles.marketLeft}>
                <View style={styles.symbolBadge}>
                  <Text style={styles.symbolBadgeText}>
                    {market.symbol.slice(0, 2)}
                  </Text>
                </View>

                <View style={styles.marketInfo}>
                  <View style={styles.symbolRow}>
                    <Text style={styles.symbol}>
                      {market.symbol}
                    </Text>

                    <View style={styles.activeDot} />
                  </View>

                  <Text style={styles.marketName}>
                    {market.name}
                  </Text>

                  <Text style={styles.category}>
                    {market.category}
                  </Text>
                </View>
              </View>

              <View style={styles.marketRight}>
                <Text style={styles.price}>
                  {market.price}
                </Text>

                <Text style={styles.change}>
                  {market.change}
                </Text>

                <View style={styles.directionPill}>
                  <Text style={styles.directionText}>
                    {market.direction}
                  </Text>
                </View>
              </View>
            </Pressable>
          ))}
        </View>

        {/* ANALYSIS NOTE */}
        <View style={styles.noteCard}>
          <View style={styles.noteIndicator} />

          <View style={styles.noteContent}>
            <Text style={styles.noteTitle}>
              TOP-DOWN ANALYSIS
            </Text>

            <Text style={styles.noteText}>
              Market analysis will follow the authoritative
              H4 → H1 → M15 structure before a trading decision
              can be produced.
            </Text>
          </View>
        </View>

        {/* DATA STATUS */}
        <View style={styles.dataStatus}>
          <View style={styles.dataStatusDot} />

          <Text style={styles.dataStatusText}>
            LIVE MARKET DATA CONNECTION READY
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

  content: {
    paddingHorizontal: 20,
  },

  glowTop: {
    position: 'absolute',
    width: 300,
    height: 300,
    borderRadius: 150,
    backgroundColor: '#101B5C',
    opacity: 0.18,
    top: -170,
    right: -110,
  },

  glowBottom: {
    position: 'absolute',
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: '#17204A',
    opacity: 0.14,
    bottom: -150,
    left: -110,
  },

  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 24,
  },

  eyebrow: {
    color: '#7083FF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 2,
  },

  title: {
    color: '#FFFFFF',
    fontSize: 30,
    fontWeight: '900',
    marginTop: 5,
  },

  subtitle: {
    color: '#77839D',
    fontSize: 12,
    lineHeight: 18,
    marginTop: 5,
    maxWidth: 270,
  },

  connectionBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#203A32',
    backgroundColor: '#0A1713',
    borderRadius: 20,
    paddingHorizontal: 11,
    paddingVertical: 7,
  },

  connectionDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 6,
  },

  connectionText: {
    color: '#35E68A',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1.2,
  },

  overviewCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 19,
    padding: 18,
    marginBottom: 26,
  },

  overviewTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },

  overviewLabel: {
    color: '#68748D',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1.5,
  },

  overviewTitle: {
    color: '#FFFFFF',
    fontSize: 22,
    fontWeight: '900',
    marginTop: 5,
  },

  statusPill: {
    borderWidth: 1,
    borderColor: '#263A91',
    backgroundColor: '#10183D',
    borderRadius: 9,
    paddingHorizontal: 9,
    paddingVertical: 6,
  },

  statusPillText: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1,
  },

  overviewDivider: {
    height: 1,
    backgroundColor: '#182131',
    marginVertical: 17,
  },

  overviewStats: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  overviewStat: {
    alignItems: 'center',
    flex: 1,
  },

  statValue: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '900',
  },

  statLabel: {
    color: '#5D6981',
    fontSize: 7,
    fontWeight: '800',
    letterSpacing: 0.8,
    marginTop: 4,
  },

  statSeparator: {
    width: 1,
    height: 25,
    backgroundColor: '#1C2535',
  },

  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 13,
  },

  sectionTitle: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1.4,
  },

  sectionMeta: {
    color: '#56627A',
    fontSize: 8,
    fontWeight: '800',
    letterSpacing: 0.8,
  },

  marketList: {
    gap: 10,
  },

  marketCard: {
    minHeight: 91,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 16,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  marketCardPressed: {
    opacity: 0.75,
    transform: [{scale: 0.99}],
  },

  marketLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },

  symbolBadge: {
    width: 42,
    height: 42,
    borderRadius: 13,
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },

  symbolBadgeText: {
    color: '#7083FF',
    fontSize: 10,
    fontWeight: '900',
  },

  marketInfo: {
    flex: 1,
  },

  symbolRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  symbol: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  activeDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginLeft: 7,
  },

  marketName: {
    color: '#737F98',
    fontSize: 9,
    marginTop: 3,
  },

  category: {
    color: '#4F5A70',
    fontSize: 7,
    fontWeight: '800',
    letterSpacing: 1,
    marginTop: 4,
  },

  marketRight: {
    alignItems: 'flex-end',
    marginLeft: 8,
  },

  price: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '800',
  },

  change: {
    color: '#58647B',
    fontSize: 8,
    marginTop: 2,
  },

  directionPill: {
    borderWidth: 1,
    borderColor: '#263043',
    backgroundColor: '#0D121C',
    borderRadius: 7,
    paddingHorizontal: 6,
    paddingVertical: 4,
    marginTop: 5,
  },

  directionText: {
    color: '#68748D',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  noteCard: {
    flexDirection: 'row',
    backgroundColor: '#080C15',
    borderWidth: 1,
    borderColor: '#151D2C',
    borderRadius: 16,
    padding: 16,
    marginTop: 24,
  },

  noteIndicator: {
    width: 3,
    borderRadius: 2,
    backgroundColor: '#334BFF',
    marginRight: 12,
  },

  noteContent: {
    flex: 1,
  },

  noteTitle: {
    color: '#7083FF',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1.3,
    marginBottom: 7,
  },

  noteText: {
    color: '#69758E',
    fontSize: 10,
    lineHeight: 16,
  },

  dataStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 18,
  },

  dataStatusDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 6,
  },

  dataStatusText: {
    color: '#4E5A72',
    fontSize: 7,
    fontWeight: '800',
    letterSpacing: 0.9,
  },
});
