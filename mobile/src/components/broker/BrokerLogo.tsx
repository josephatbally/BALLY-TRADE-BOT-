import React, { useState } from 'react';
import { View, StyleSheet, Text, Image, StyleProp, ViewStyle } from 'react-native';
import Svg, { Path, Rect, Circle, Polygon, Defs, LinearGradient, Stop, G, Text as SvgText } from 'react-native-svg';

export interface BrokerBrand {
  key: string;
  name: string;
  shortName: string;
  primaryColor: string;
  secondaryColor: string;
  badgeBg: string;
  borderColor: string;
  remoteLogoUrl?: string;
}

export function detectBrokerBrand(company?: string | null, server?: string | null): BrokerBrand {
  const query = `${company || ''} ${server || ''}`.toLowerCase().trim();

  if (query.includes('exness')) {
    return {
      key: 'exness',
      name: 'Exness',
      shortName: 'EX',
      primaryColor: '#FFD700',
      secondaryColor: '#FFA500',
      badgeBg: '#181816',
      borderColor: 'rgba(255, 215, 0, 0.4)',
      remoteLogoUrl: 'https://img.icons8.com/color/120/exness.png',
    };
  }

  if (query.includes('ic markets') || query.includes('icmarkets') || query.includes('icm')) {
    return {
      key: 'icmarkets',
      name: 'IC Markets',
      shortName: 'ICM',
      primaryColor: '#00D084',
      secondaryColor: '#00A86B',
      badgeBg: '#091F17',
      borderColor: 'rgba(0, 208, 132, 0.4)',
    };
  }

  if (query.includes('deriv')) {
    return {
      key: 'deriv',
      name: 'Deriv',
      shortName: 'DRV',
      primaryColor: '#FF444F',
      secondaryColor: '#CC202A',
      badgeBg: '#210B0E',
      borderColor: 'rgba(255, 68, 79, 0.4)',
    };
  }

  if (query.includes('xm global') || query.includes('xmglobal') || query.includes('xm.') || query.includes('xm-')) {
    return {
      key: 'xm',
      name: 'XM Global',
      shortName: 'XM',
      primaryColor: '#E53935',
      secondaryColor: '#B71C1C',
      badgeBg: '#210B0F',
      borderColor: 'rgba(229, 57, 53, 0.4)',
    };
  }

  if (query.includes('pepperstone')) {
    return {
      key: 'pepperstone',
      name: 'Pepperstone',
      shortName: 'PEP',
      primaryColor: '#FF5722',
      secondaryColor: '#E64A19',
      badgeBg: '#23120A',
      borderColor: 'rgba(255, 87, 34, 0.4)',
    };
  }

  if (query.includes('ftmo')) {
    return {
      key: 'ftmo',
      name: 'FTMO',
      shortName: 'FTMO',
      primaryColor: '#00E5FF',
      secondaryColor: '#00B0FF',
      badgeBg: '#081D29',
      borderColor: 'rgba(0, 229, 255, 0.4)',
    };
  }

  if (query.includes('fbs')) {
    return {
      key: 'fbs',
      name: 'FBS',
      shortName: 'FBS',
      primaryColor: '#2ECC71',
      secondaryColor: '#27AE60',
      badgeBg: '#0B2416',
      borderColor: 'rgba(46, 204, 113, 0.4)',
    };
  }

  if (query.includes('hfm') || query.includes('hotforex')) {
    return {
      key: 'hfm',
      name: 'HFM Markets',
      shortName: 'HFM',
      primaryColor: '#D32F2F',
      secondaryColor: '#9A0007',
      badgeBg: '#240B0E',
      borderColor: 'rgba(211, 47, 47, 0.4)',
    };
  }

  if (query.includes('octa') || query.includes('octafx')) {
    return {
      key: 'octafx',
      name: 'OctaFX',
      shortName: 'OCTA',
      primaryColor: '#1E88E5',
      secondaryColor: '#1565C0',
      badgeBg: '#0B1A38',
      borderColor: 'rgba(30, 136, 229, 0.4)',
    };
  }

  if (query.includes('justmarkets') || query.includes('justforex')) {
    return {
      key: 'justmarkets',
      name: 'JustMarkets',
      shortName: 'JM',
      primaryColor: '#00BCD4',
      secondaryColor: '#00838F',
      badgeBg: '#0A202A',
      borderColor: 'rgba(0, 188, 212, 0.4)',
    };
  }

  if (query.includes('roboforex')) {
    return {
      key: 'roboforex',
      name: 'RoboForex',
      shortName: 'RF',
      primaryColor: '#1976D2',
      secondaryColor: '#0D47A1',
      badgeBg: '#091A33',
      borderColor: 'rgba(25, 118, 210, 0.4)',
    };
  }

  if (query.includes('avatrade')) {
    return {
      key: 'avatrade',
      name: 'AvaTrade',
      shortName: 'AVA',
      primaryColor: '#FF9800',
      secondaryColor: '#F57C00',
      badgeBg: '#2A1809',
      borderColor: 'rgba(255, 152, 0, 0.4)',
    };
  }

  if (query.includes('vantage')) {
    return {
      key: 'vantage',
      name: 'Vantage',
      shortName: 'VTG',
      primaryColor: '#E63946',
      secondaryColor: '#D90429',
      badgeBg: '#230B10',
      borderColor: 'rgba(230, 57, 70, 0.4)',
    };
  }

  // Default MetaQuotes / MT5 Terminal
  return {
    key: 'metaquotes',
    name: company || 'MetaQuotes / MT5',
    shortName: company ? company.substring(0, 2).toUpperCase() : 'MT',
    primaryColor: '#334BFF',
    secondaryColor: '#00D2FF',
    badgeBg: '#0A122E',
    borderColor: 'rgba(51, 75, 255, 0.4)',
  };
}

interface BrokerLogoProps {
  company?: string | null;
  server?: string | null;
  size?: number;
  style?: StyleProp<ViewStyle>;
}

export default function BrokerLogo({
  company,
  server,
  size = 44,
  style,
}: BrokerLogoProps) {
  const brand = detectBrokerBrand(company, server);
  const [imageError, setImageError] = useState(false);

  const radius = Math.round(size * 0.24);

  // If a reliable remote logo is specified and hasn't errored, render it with fallback
  if (brand.remoteLogoUrl && !imageError) {
    return (
      <View
        style={[
          styles.container,
          {
            width: size,
            height: size,
            borderRadius: radius,
            backgroundColor: brand.badgeBg,
            borderColor: brand.borderColor,
          },
          style,
        ]}>
        <Image
          source={{ uri: brand.remoteLogoUrl }}
          style={{ width: size * 0.72, height: size * 0.72 }}
          resizeMode="contain"
          onError={() => setImageError(true)}
        />
      </View>
    );
  }

  // Native Vector Geometric Broker Emblem
  return (
    <View
      style={[
        styles.container,
        {
          width: size,
          height: size,
          borderRadius: radius,
          backgroundColor: brand.badgeBg,
          borderColor: brand.borderColor,
        },
        style,
      ]}>
      {renderVectorBrokerEmblem(brand, size)}
    </View>
  );
}

function renderVectorBrokerEmblem(brand: BrokerBrand, size: number) {
  const s = size;
  const cx = s / 2;
  const cy = s / 2;

  switch (brand.key) {
    case 'exness': {
      // Exness geometric interlocking emblem in brand gold
      return (
        <Svg width={s} height={s} viewBox={`0 0 ${s} ${s}`}>
          <Defs>
            <LinearGradient id="exnessGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <Stop offset="0%" stopColor="#FFE066" />
              <Stop offset="100%" stopColor="#FFB800" />
            </LinearGradient>
          </Defs>
          <G transform={`translate(${cx}, ${cy})`}>
            {/* Top-left rounded wing */}
            <Path
              d={`M -${s * 0.3} -${s * 0.05} C -${s * 0.3} -${s * 0.28}, -${s * 0.12} -${s * 0.32}, 0 -${s * 0.32} C -${s * 0.05} -${s * 0.18}, -${s * 0.15} -${s * 0.05}, -${s * 0.3} -${s * 0.05} Z`}
              fill="url(#exnessGrad)"
            />
            {/* Bottom-right rounded wing */}
            <Path
              d={`M ${s * 0.3} ${s * 0.05} C ${s * 0.3} ${s * 0.28}, ${s * 0.12} ${s * 0.32}, 0 ${s * 0.32} C ${s * 0.05} ${s * 0.18}, ${s * 0.15} ${s * 0.05}, ${s * 0.3} ${s * 0.05} Z`}
              fill="url(#exnessGrad)"
            />
            {/* Center diamond link */}
            <Polygon
              points={`0,-${s * 0.16} ${s * 0.18},0 0,${s * 0.16} -${s * 0.18},0`}
              fill="#FFE066"
            />
          </G>
        </Svg>
      );
    }

    case 'icmarkets': {
      // IC Markets green dual chevron / signal
      return (
        <Svg width={s} height={s} viewBox={`0 0 ${s} ${s}`}>
          <Defs>
            <LinearGradient id="icmGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <Stop offset="0%" stopColor="#00E676" />
              <Stop offset="100%" stopColor="#00B0FF" />
            </LinearGradient>
          </Defs>
          <G transform={`translate(${cx}, ${cy})`}>
            <Polygon
              points={`-${s * 0.28},${s * 0.22} -${s * 0.08},-${s * 0.22} ${s * 0.04},-${s * 0.22} -${s * 0.16},${s * 0.22}`}
              fill="url(#icmGrad)"
            />
            <Polygon
              points={`-${s * 0.04},${s * 0.22} ${s * 0.16},-${s * 0.22} ${s * 0.28},-${s * 0.22} ${s * 0.08},${s * 0.22}`}
              fill="url(#icmGrad)"
            />
            <Circle cx={s * 0.18} cy={-s * 0.18} r={s * 0.05} fill="#00E676" />
          </G>
        </Svg>
      );
    }

    case 'deriv': {
      // Deriv coral red angled chevron
      return (
        <Svg width={s} height={s} viewBox={`0 0 ${s} ${s}`}>
          <Defs>
            <LinearGradient id="derivGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <Stop offset="0%" stopColor="#FF444F" />
              <Stop offset="100%" stopColor="#D92D37" />
            </LinearGradient>
          </Defs>
          <G transform={`translate(${cx}, ${cy})`}>
            <Path
              d={`M -${s * 0.22} -${s * 0.25} L ${s * 0.12} -${s * 0.25} C ${s * 0.26} -${s * 0.25}, ${s * 0.26} ${s * 0.25}, ${s * 0.12} ${s * 0.25} L -${s * 0.22} ${s * 0.25} L -${s * 0.1} 0 Z`}
              fill="url(#derivGrad)"
            />
          </G>
        </Svg>
      );
    }

    case 'xm': {
      // XM bold white monogram on red banner
      return (
        <Svg width={s} height={s} viewBox={`0 0 ${s} ${s}`}>
          <Defs>
            <LinearGradient id="xmGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <Stop offset="0%" stopColor="#EF5350" />
              <Stop offset="100%" stopColor="#C62828" />
            </LinearGradient>
          </Defs>
          <G transform={`translate(${cx}, ${cy})`}>
            {/* Shield backing */}
            <Polygon
              points={`-${s * 0.32},-${s * 0.26} ${s * 0.32},-${s * 0.26} ${s * 0.24},${s * 0.26} -${s * 0.24},${s * 0.26}`}
              fill="url(#xmGrad)"
            />
            <SvgText
              x="0"
              y={s * 0.09}
              textAnchor="middle"
              fill="#FFFFFF"
              fontSize={s * 0.34}
              fontWeight="900"
              letterSpacing="1">
              XM
            </SvgText>
          </G>
        </Svg>
      );
    }

    case 'ftmo': {
      // FTMO cyan geometric shield
      return (
        <Svg width={s} height={s} viewBox={`0 0 ${s} ${s}`}>
          <Defs>
            <LinearGradient id="ftmoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <Stop offset="0%" stopColor="#00E5FF" />
              <Stop offset="100%" stopColor="#0077B6" />
            </LinearGradient>
          </Defs>
          <G transform={`translate(${cx}, ${cy})`}>
            <Polygon
              points={`0,-${s * 0.3} ${s * 0.26},-${s * 0.1} ${s * 0.16},${s * 0.26} -${s * 0.16},${s * 0.26} -${s * 0.26},-${s * 0.1}`}
              fill="url(#ftmoGrad)"
            />
            <Circle cx="0" cy="0" r={s * 0.08} fill="#081D29" />
          </G>
        </Svg>
      );
    }

    case 'pepperstone': {
      // Pepperstone flame / double chevron
      return (
        <Svg width={s} height={s} viewBox={`0 0 ${s} ${s}`}>
          <Defs>
            <LinearGradient id="pepGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <Stop offset="0%" stopColor="#FF6E40" />
              <Stop offset="100%" stopColor="#D84315" />
            </LinearGradient>
          </Defs>
          <G transform={`translate(${cx}, ${cy})`}>
            <Polygon
              points={`-${s * 0.2},-${s * 0.26} ${s * 0.2},0 -${s * 0.2},${s * 0.26} -${s * 0.08},0`}
              fill="url(#pepGrad)"
            />
            <Polygon
              points={`-${s * 0.02},-${s * 0.26} ${s * 0.28},0 -${s * 0.02},${s * 0.26} ${s * 0.1},0`}
              fill="#FFAB91"
            />
          </G>
        </Svg>
      );
    }

    default: {
      // MetaQuotes / MT5 / Clean Modern Broker Badge
      return (
        <Svg width={s} height={s} viewBox={`0 0 ${s} ${s}`}>
          <Defs>
            <LinearGradient id="metaGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <Stop offset="0%" stopColor={brand.secondaryColor} />
              <Stop offset="100%" stopColor={brand.primaryColor} />
            </LinearGradient>
          </Defs>
          <G transform={`translate(${cx}, ${cy})`}>
            {/* Triangular network nodes (MT5 style) */}
            <Circle cx="0" cy={-s * 0.18} r={s * 0.06} fill="url(#metaGrad)" />
            <Circle cx={-s * 0.18} cy={s * 0.15} r={s * 0.06} fill="url(#metaGrad)" />
            <Circle cx={s * 0.18} cy={s * 0.15} r={s * 0.06} fill="url(#metaGrad)" />
            <Path
              d={`M 0 -${s * 0.14} L -${s * 0.14} ${s * 0.12} L ${s * 0.14} ${s * 0.12} Z`}
              stroke="url(#metaGrad)"
              strokeWidth={Math.max(1.5, s * 0.04)}
              fill="none"
            />
            <SvgText
              x="0"
              y={s * 0.06}
              textAnchor="middle"
              fill="#FFFFFF"
              fontSize={s * 0.2}
              fontWeight="800">
              {brand.shortName}
            </SvgText>
          </G>
        </Svg>
      );
    }
  }
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    overflow: 'hidden',
  },
});
