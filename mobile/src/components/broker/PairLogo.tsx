import React from 'react';
import { View, StyleSheet, StyleProp, ViewStyle } from 'react-native';
import Svg, { Circle, Rect, Path, Defs, LinearGradient, Stop, G, Text as SvgText } from 'react-native-svg';

export interface PairMeta {
  rawSymbol: string;
  base: string;
  quote: string;
  type: 'FOREX' | 'COMMODITY' | 'CRYPTO' | 'INDEX';
  displayName: string;
  baseColor: string;
  baseColorEnd: string;
  quoteColor: string;
  quoteColorEnd: string;
  baseSymbolText: string;
  quoteSymbolText: string;
}

export function detectPairMeta(symbol: string): PairMeta {
  const clean = (symbol || '').toUpperCase().replace(/[^A-Z0-9]/g, '');

  // 1. Precious Metals & Commodities
  if (clean.includes('XAU') || clean.includes('GOLD')) {
    return {
      rawSymbol: clean,
      base: 'XAU',
      quote: 'USD',
      type: 'COMMODITY',
      displayName: 'Gold / USD',
      baseColor: '#FFE066',
      baseColorEnd: '#FFB800',
      quoteColor: '#1B5E20',
      quoteColorEnd: '#00C853',
      baseSymbolText: 'Au',
      quoteSymbolText: '$',
    };
  }

  if (clean.includes('XAG') || clean.includes('SILVER')) {
    return {
      rawSymbol: clean,
      base: 'XAG',
      quote: 'USD',
      type: 'COMMODITY',
      displayName: 'Silver / USD',
      baseColor: '#FFFFFF',
      baseColorEnd: '#B0BEC5',
      quoteColor: '#1B5E20',
      quoteColorEnd: '#00C853',
      baseSymbolText: 'Ag',
      quoteSymbolText: '$',
    };
  }

  if (clean.includes('OIL') || clean.includes('WTI') || clean.includes('BRENT')) {
    return {
      rawSymbol: clean,
      base: 'OIL',
      quote: 'USD',
      type: 'COMMODITY',
      displayName: 'Crude Oil',
      baseColor: '#FF6D00',
      baseColorEnd: '#DD2C00',
      quoteColor: '#1B5E20',
      quoteColorEnd: '#00C853',
      baseSymbolText: 'OIL',
      quoteSymbolText: '$',
    };
  }

  // 2. Cryptocurrencies
  if (clean.includes('BTC')) {
    return {
      rawSymbol: clean,
      base: 'BTC',
      quote: 'USD',
      type: 'CRYPTO',
      displayName: 'Bitcoin',
      baseColor: '#FF9900',
      baseColorEnd: '#F7931A',
      quoteColor: '#1B5E20',
      quoteColorEnd: '#00C853',
      baseSymbolText: '₿',
      quoteSymbolText: '$',
    };
  }

  if (clean.includes('ETH')) {
    return {
      rawSymbol: clean,
      base: 'ETH',
      quote: 'USD',
      type: 'CRYPTO',
      displayName: 'Ethereum',
      baseColor: '#7B8AFF',
      baseColorEnd: '#627EEA',
      quoteColor: '#1B5E20',
      quoteColorEnd: '#00C853',
      baseSymbolText: 'Ξ',
      quoteSymbolText: '$',
    };
  }

  // 3. Stock Indices
  if (clean.includes('US30') || clean.includes('DJ30') || clean.includes('DOW')) {
    return {
      rawSymbol: clean,
      base: 'US30',
      quote: 'USD',
      type: 'INDEX',
      displayName: 'Dow Jones 30',
      baseColor: '#1E88E5',
      baseColorEnd: '#0D47A1',
      quoteColor: '#1B5E20',
      quoteColorEnd: '#00C853',
      baseSymbolText: '30',
      quoteSymbolText: '$',
    };
  }

  if (clean.includes('NAS') || clean.includes('100') || clean.includes('TECH') || clean.includes('USTEC')) {
    return {
      rawSymbol: clean,
      base: 'NAS',
      quote: 'USD',
      type: 'INDEX',
      displayName: 'Nasdaq 100',
      baseColor: '#00E5FF',
      baseColorEnd: '#0097A7',
      quoteColor: '#1B5E20',
      quoteColorEnd: '#00C853',
      baseSymbolText: 'NDX',
      quoteSymbolText: '$',
    };
  }

  if (clean.includes('US500') || clean.includes('SPX') || clean.includes('SP500')) {
    return {
      rawSymbol: clean,
      base: 'SPX',
      quote: 'USD',
      type: 'INDEX',
      displayName: 'S&P 500',
      baseColor: '#7C4DFF',
      baseColorEnd: '#4A148C',
      quoteColor: '#1B5E20',
      quoteColorEnd: '#00C853',
      baseSymbolText: '500',
      quoteSymbolText: '$',
    };
  }

  // 4. Standard 6-character FX Pairs (e.g. EURUSD, GBPUSD, USDJPY)
  const base = clean.length >= 6 ? clean.substring(0, 3) : clean;
  const quote = clean.length >= 6 ? clean.substring(3, 6) : 'USD';

  const currencyStyles: Record<string, { color: string; colorEnd: string; text: string }> = {
    EUR: { color: '#0052B4', colorEnd: '#002B7F', text: '€' },
    USD: { color: '#2E7D32', colorEnd: '#1B5E20', text: '$' },
    GBP: { color: '#C62828', colorEnd: '#8E0000', text: '£' },
    JPY: { color: '#D32F2F', colorEnd: '#B71C1C', text: '¥' },
    AUD: { color: '#0277BD', colorEnd: '#01579B', text: 'A$' },
    NZD: { color: '#00838F', colorEnd: '#006064', text: 'NZ$' },
    CAD: { color: '#E53935', colorEnd: '#C62828', text: 'C$' },
    CHF: { color: '#D50000', colorEnd: '#9B0000', text: '₣' },
    ZAR: { color: '#2E7D32', colorEnd: '#00796B', text: 'R' },
  };

  const baseStyle = currencyStyles[base] || { color: '#37474F', colorEnd: '#263238', text: base.substring(0, 2) };
  const quoteStyle = currencyStyles[quote] || { color: '#1B5E20', colorEnd: '#00C853', text: quote.substring(0, 2) };

  return {
    rawSymbol: clean,
    base,
    quote,
    type: 'FOREX',
    displayName: `${base}/${quote}`,
    baseColor: baseStyle.color,
    baseColorEnd: baseStyle.colorEnd,
    quoteColor: quoteStyle.color,
    quoteColorEnd: quoteStyle.colorEnd,
    baseSymbolText: baseStyle.text,
    quoteSymbolText: quoteStyle.text,
  };
}

interface PairLogoProps {
  symbol: string;
  size?: number;
  style?: StyleProp<ViewStyle>;
}

/**
 * Authentic Global Market Pair Presentation Badge
 * Dual overlapping circular discs (institutional market standard)
 */
export default function PairLogo({ symbol, size = 32, style }: PairLogoProps) {
  const meta = detectPairMeta(symbol);

  const discRadius = size * 0.32;
  const strokeWidth = Math.max(1, size * 0.04);

  // Center positions for overlapping discs
  const baseCx = size * 0.36;
  const baseCy = size * 0.50;
  const quoteCx = size * 0.64;
  const quoteCy = size * 0.50;

  const baseGradId = `baseGrad_${meta.rawSymbol}_${size}`;
  const quoteGradId = `quoteGrad_${meta.rawSymbol}_${size}`;

  return (
    <View style={[{ width: size, height: size }, styles.container, style]}>
      <Svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <Defs>
          <LinearGradient id={baseGradId} x1="0%" y1="0%" x2="100%" y2="100%">
            <Stop offset="0%" stopColor={meta.baseColor} />
            <Stop offset="100%" stopColor={meta.baseColorEnd} />
          </LinearGradient>
          <LinearGradient id={quoteGradId} x1="0%" y1="0%" x2="100%" y2="100%">
            <Stop offset="0%" stopColor={meta.quoteColor} />
            <Stop offset="100%" stopColor={meta.quoteColorEnd} />
          </LinearGradient>
        </Defs>

        {/* 1. Quote Disc (Background layer, right side) */}
        <Circle
          cx={quoteCx}
          cy={quoteCy}
          r={discRadius}
          fill={`url(#${quoteGradId})`}
          stroke="#0A0E1A"
          strokeWidth={strokeWidth}
        />
        <SvgText
          x={quoteCx + size * 0.04}
          y={quoteCy + size * 0.10}
          textAnchor="middle"
          fill="#FFFFFF"
          fontSize={size * 0.22}
          fontWeight="900">
          {meta.quoteSymbolText}
        </SvgText>

        {/* 2. Base Disc (Foreground layer, left side, slightly overlapping) */}
        <Circle
          cx={baseCx}
          cy={baseCy}
          r={discRadius}
          fill={`url(#${baseGradId})`}
          stroke="#0A0E1A"
          strokeWidth={strokeWidth}
        />
        <SvgText
          x={baseCx}
          y={baseCy + size * 0.10}
          textAnchor="middle"
          fill={meta.base === 'XAU' || meta.base === 'XAG' ? '#121212' : '#FFFFFF'}
          fontSize={meta.baseSymbolText.length > 1 ? size * 0.20 : size * 0.24}
          fontWeight="900">
          {meta.baseSymbolText}
        </SvgText>
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});
