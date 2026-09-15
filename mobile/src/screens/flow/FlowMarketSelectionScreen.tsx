import React, { useEffect, useState, useCallback } from 'react';
import {
  Pressable,
  RefreshControl,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { getMarketQuotes, MarketQuote } from '../../api/marketsApi';

type Market = {
  symbol: string;
  name: string;
  category: string;
};

const MARKETS: Market[] = [
  { symbol: 'XAUUSD', name: 'Gold / US Dollar', category: 'METAL' },
  { symbol: 'EURUSD', name: 'Euro / US Dollar', category: 'FOREX' },
  { symbol: 'GBPUSD', name: 'British Pound / US Dollar', category: 'FOREX' },
  { symbol: 'USDJPY', name: 'US Dollar / Japanese Yen', category: 'FOREX' },
  { symbol: 'XAGUSD', name: 'Silver / US Dollar', category: 'METAL' },
  { symbol: 'NASDAQ', name: 'Nasdaq Index', category: 'INDEX' },
];

export default function FlowMarketSelectionScreen({
  navigation,
  route,
}: any) {
  const insets = useSafeAreaInsets();
  const initialSymbol = route?.params?.symbol || 'XAUUSD';

  const [selectedSymbol, setSelectedSymbol] = useState<string>(initialSymbol);
  const [quotes, setQuotes] = useState<Record<string, MarketQuote>>({});
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const fetchQuotes = useCallback(async () => {
    try {
      const res = await getMarketQuotes();
      if (res && Array.isArray(res.quotes)) {
        const map: Record<string, MarketQuote> = {};
        res.quotes.forEach(q => {
          map[q.symbol] = q;
        });
        setQuotes(map);
      }
    } catch {
      // Retain existing quotes on network blip
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchQuotes();
    const interval = setInterval(fetchQuotes, 5000);
    return () => clearInterval(interval);
  }, [fetchQuotes]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchQuotes();
  };

  const selectedMarket =
    MARKETS.find(market => market.symbol === selectedSymbol) || MARKETS[0];
  const activeQuote = quotes[selectedSymbol];

  const handleContinue = () => {
    navigation.navigate('FlowAnalysis', {
      user: route?.params?.user,
      symbol: selectedSymbol,
    });
  };

  const handleBack = () => {
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
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#7083FF"
          />
        }
      >
        {/* HEADER */}
        <View style={styles.header}>
          <Pressable
            onPress={handleBack}
            style={({ pressed }) => [
              styles.backButton,
              pressed && styles.pressed,
            ]}
          >
            <Text allowFontScaling={false} style={styles.backIcon}>‹</Text>
          </Pressable>

          <View style={styles.headerText}>
            <Text allowFontScaling={false} style={styles.eyebrow}>
              BALLY FLOW
            </Text>

            <Text allowFontScaling={false} style={styles.title}>
              Select Market
            </Text>

            <Text allowFontScaling={false} style={styles.subtitle}>
              Choose the market for Trading Intelligence
            </Text>
          </View>

          <View style={styles.stageBadge}>
            <Text allowFontScaling={false} style={styles.stageNumber}>
              01
            </Text>

            <Text allowFontScaling={false} style={styles.stageLabel}>
              MARKET
            </Text>
          </View>
        </View>

        {/* CURRENT SELECTION */}
        <View style={styles.selectionCard}>
          <View style={styles.selectionHeader}>
            <Text allowFontScaling={false} style={styles.selectionLabel}>
              SELECTED MARKET
            </Text>

            <View style={styles.readyBadge}>
              <View style={styles.readyDot} />

              <Text allowFontScaling={false} style={styles.readyText}>
                {activeQuote?.price ? 'LIVE' : 'READY'}
              </Text>
            </View>
          </View>

          <View style={styles.selectedMarketRow}>
            <View>
              <Text allowFontScaling={false} style={styles.selectedSymbol}>
                {selectedMarket?.symbol}
              </Text>

              <Text allowFontScaling={false} style={styles.selectedName}>
                {selectedMarket?.name}
              </Text>
            </View>

            <View style={styles.selectedPriceCol}>
              <Text allowFontScaling={false} style={styles.selectedPriceText}>
                {activeQuote?.price ? activeQuote.price : '---'}
              </Text>
              <Text
                allowFontScaling={false}
                style={[
                  styles.selectedChangeText,
                  { color: (activeQuote?.change_pct || 0) >= 0 ? '#35E68A' : '#EF4444' },
                ]}
              >
                {activeQuote?.change_pct != null
                  ? `${activeQuote.change_pct >= 0 ? '+' : ''}${activeQuote.change_pct.toFixed(2)}%`
                  : '0.00%'}
              </Text>
            </View>

            <View style={styles.selectedCategory}>
              <Text allowFontScaling={false} style={styles.selectedCategoryText}>
                {selectedMarket?.category}
              </Text>
            </View>
          </View>
        </View>

        {/* MARKET LIST */}
        <View style={styles.sectionHeader}>
          <View>
            <Text allowFontScaling={false} style={styles.sectionTitle}>
              AVAILABLE MARKETS
            </Text>

            <Text allowFontScaling={false} style={styles.sectionSubtitle}>
              Exactly six supported Trading Intelligence markets
            </Text>
          </View>

          <Text allowFontScaling={false} style={styles.marketCount}>
            06
          </Text>
        </View>

        <View style={styles.marketList}>
          {MARKETS.map((market, index) => {
            const isSelected = market.symbol === selectedSymbol;
            const q = quotes[market.symbol];
            const isUp = (q?.change_pct || 0) >= 0;

            return (
              <Pressable
                key={market.symbol}
                onPress={() => setSelectedSymbol(market.symbol)}
                style={({ pressed }) => [
                  styles.marketItem,
                  isSelected && styles.marketItemSelected,
                  pressed && styles.marketItemPressed,
                ]}
              >
                <View
                  style={[
                    styles.marketIcon,
                    isSelected && styles.marketIconSelected,
                  ]}
                >
                  <Text
                    allowFontScaling={false}
                    style={[
                      styles.marketIconText,
                      isSelected && styles.marketIconTextSelected,
                    ]}
                  >
                    {String(index + 1).padStart(2, '0')}
                  </Text>
                </View>

                <View style={styles.marketInfo}>
                  <View style={styles.marketTitleRow}>
                    <Text allowFontScaling={false} style={styles.marketItemSymbol}>
                      {market.symbol}
                    </Text>

                    <View style={styles.categoryBadge}>
                      <Text allowFontScaling={false} style={styles.categoryText}>
                        {market.category}
                      </Text>
                    </View>
                  </View>

                  <Text allowFontScaling={false} style={styles.marketItemName}>
                    {market.name}
                  </Text>
                </View>

                <View style={styles.itemPriceCol}>
                  <Text allowFontScaling={false} style={styles.itemPriceText}>
                    {q?.price ? q.price : '---'}
                  </Text>
                  <Text
                    allowFontScaling={false}
                    style={[
                      styles.itemChangeText,
                      { color: isUp ? '#35E68A' : '#EF4444' },
                    ]}
                  >
                    {q?.change_pct != null ? `${isUp ? '+' : ''}${q.change_pct.toFixed(2)}%` : '0.00%'}
                  </Text>
                </View>

                <View
                  style={[
                    styles.radio,
                    isSelected && styles.radioSelected,
                  ]}
                >
                  {isSelected && <View style={styles.radioInner} />}
                </View>
              </Pressable>
            );
          })}
        </View>

        {/* ANALYSIS PIPELINE PREVIEW */}
        <View style={styles.pipelineCard}>
          <View style={styles.pipelineHeader}>
            <View>
              <Text allowFontScaling={false} style={styles.pipelineEyebrow}>
                NEXT STAGE
              </Text>

              <Text allowFontScaling={false} style={styles.pipelineTitle}>
                Top-Down Analysis
              </Text>
            </View>

            <Text allowFontScaling={false} style={styles.pipelineNumber}>
              02
            </Text>
          </View>

          <Text allowFontScaling={false} style={styles.pipelineText}>
            The selected market will continue through H4 → H1 → M15 analysis before entering the Confluence stage.
          </Text>

          <View style={styles.timeframeRow}>
            <View style={styles.timeframe}>
              <Text allowFontScaling={false} style={styles.timeframeText}>H4</Text>
            </View>
            <Text allowFontScaling={false} style={styles.timeframeArrow}>→</Text>
            <View style={styles.timeframe}>
              <Text allowFontScaling={false} style={styles.timeframeText}>H1</Text>
            </View>
            <Text allowFontScaling={false} style={styles.timeframeArrow}>→</Text>
            <View style={styles.timeframe}>
              <Text allowFontScaling={false} style={styles.timeframeText}>M15</Text>
            </View>
          </View>
        </View>
      </ScrollView>

      {/* CONTINUE ACTION */}
      <View
        style={[
          styles.bottomBar,
          {
            paddingBottom: Math.max(insets.bottom, 16),
          },
        ]}
      >
        <Pressable
          onPress={handleContinue}
          style={({ pressed }) => [
            styles.continueButton,
            pressed && styles.continuePressed,
          ]}
        >
          <View>
            <Text allowFontScaling={false} style={styles.continueLabel}>
              CONTINUE WITH
            </Text>

            <Text allowFontScaling={false} style={styles.continueSymbol}>
              {selectedSymbol}
            </Text>
          </View>

          <View style={styles.continueArrow}>
            <Text allowFontScaling={false} style={styles.continueArrowText}>
              →
            </Text>
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
    opacity: 0.65,
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
    alignItems: 'center',
    justifyContent: 'center',
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    marginLeft: 8,
  },
  stageNumber: {
    color: '#7083FF',
    fontSize: 12,
    fontWeight: '900',
  },
  stageLabel: {
    color: '#53617A',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.8,
    marginTop: 2,
  },
  selectionCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 18,
    padding: 18,
    marginBottom: 26,
  },
  selectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  selectionLabel: {
    color: '#68748D',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1.5,
  },
  readyBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0A1713',
    borderWidth: 1,
    borderColor: '#203A32',
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 5,
  },
  readyDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 5,
  },
  readyText: {
    color: '#35E68A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1,
  },
  selectedMarketRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 14,
  },
  selectedSymbol: {
    color: '#FFFFFF',
    fontSize: 26,
    fontWeight: '900',
    letterSpacing: 1,
  },
  selectedName: {
    color: '#69758D',
    fontSize: 11,
    marginTop: 4,
  },
  selectedPriceCol: {
    alignItems: 'center',
  },
  selectedPriceText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '800',
  },
  selectedChangeText: {
    fontSize: 10,
    fontWeight: '800',
    marginTop: 2,
  },
  selectedCategory: {
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#263A91',
    borderRadius: 9,
    paddingHorizontal: 9,
    paddingVertical: 6,
  },
  selectedCategoryText: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    marginBottom: 13,
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
  marketCount: {
    color: '#56627A',
    fontSize: 10,
    fontWeight: '900',
  },
  marketList: {
    marginBottom: 24,
  },
  marketItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#182131',
    borderRadius: 15,
    padding: 13,
    marginBottom: 9,
  },
  marketItemSelected: {
    borderColor: '#334BFF',
    backgroundColor: '#0B101E',
  },
  marketItemPressed: {
    opacity: 0.75,
  },
  marketIcon: {
    width: 39,
    height: 39,
    borderRadius: 12,
    backgroundColor: '#111722',
    borderWidth: 1,
    borderColor: '#263043',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  marketIconSelected: {
    backgroundColor: '#10183D',
    borderColor: '#334BFF',
  },
  marketIconText: {
    color: '#68758E',
    fontSize: 8,
    fontWeight: '900',
  },
  marketIconTextSelected: {
    color: '#8A98FF',
  },
  marketInfo: {
    flex: 1,
  },
  marketTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  marketItemSymbol: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 0.7,
  },
  categoryBadge: {
    marginLeft: 7,
    borderWidth: 1,
    borderColor: '#202A3D',
    borderRadius: 6,
    paddingHorizontal: 5,
    paddingVertical: 3,
  },
  categoryText: {
    color: '#56627A',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.7,
  },
  marketItemName: {
    color: '#68758E',
    fontSize: 9,
    marginTop: 4,
  },
  itemPriceCol: {
    alignItems: 'flex-end',
    marginRight: 8,
  },
  itemPriceText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '800',
  },
  itemChangeText: {
    fontSize: 9,
    fontWeight: '800',
    marginTop: 2,
  },
  radio: {
    width: 19,
    height: 19,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#344056',
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 6,
  },
  radioSelected: {
    borderColor: '#7083FF',
  },
  radioInner: {
    width: 9,
    height: 9,
    borderRadius: 5,
    backgroundColor: '#7083FF',
  },
  pipelineCard: {
    backgroundColor: '#080C15',
    borderWidth: 1,
    borderColor: '#151D2C',
    borderRadius: 17,
    padding: 16,
    marginBottom: 10,
  },
  pipelineHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  pipelineEyebrow: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.5,
  },
  pipelineTitle: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '900',
    marginTop: 3,
  },
  pipelineNumber: {
    color: '#53617A',
    fontSize: 18,
    fontWeight: '900',
  },
  pipelineText: {
    color: '#68758E',
    fontSize: 10,
    lineHeight: 15,
    marginTop: 9,
  },
  timeframeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 13,
  },
  timeframe: {
    backgroundColor: '#0D121D',
    borderWidth: 1,
    borderColor: '#202A3D',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 7,
  },
  timeframeText: {
    color: '#8995B1',
    fontSize: 8,
    fontWeight: '900',
  },
  timeframeArrow: {
    color: '#53617A',
    fontSize: 13,
    marginHorizontal: 8,
  },
  bottomBar: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    paddingHorizontal: 20,
    paddingTop: 12,
    backgroundColor: '#05070D',
    borderTopWidth: 1,
    borderTopColor: '#111827',
  },
  continueButton: {
    minHeight: 60,
    backgroundColor: '#10183D',
    borderWidth: 1,
    borderColor: '#334BFF',
    borderRadius: 16,
    paddingHorizontal: 17,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  continuePressed: {
    opacity: 0.78,
    transform: [{ scale: 0.995 }],
  },
  continueLabel: {
    color: '#68758E',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1.2,
  },
  continueSymbol: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '900',
    letterSpacing: 0.8,
    marginTop: 3,
  },
  continueArrow: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#263A91',
    alignItems: 'center',
    justifyContent: 'center',
  },
  continueArrowText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
});
