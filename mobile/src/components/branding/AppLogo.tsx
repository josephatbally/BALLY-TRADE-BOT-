import React from 'react';
import {
  Image,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {BRANDING} from '../../config/branding';

type AppLogoProps = {
  size?: number;
};

export default function AppLogo({size = 74}: AppLogoProps) {
  if (BRANDING.logo) {
    return (
      <View
        style={[
          styles.outer,
          {
            width: size,
            height: size,
            borderRadius: size / 2,
          },
        ]}>
        <Image
          source={BRANDING.logo}
          style={[
            styles.logo,
            {
              width: size * 0.76,
              height: size * 0.76,
            },
          ]}
          resizeMode="contain"
          accessibilityLabel={`${BRANDING.appName} logo`}
        />
      </View>
    );
  }

  return (
    <View
      style={[
        styles.outer,
        {
          width: size,
          height: size,
          borderRadius: size / 2,
        },
      ]}>
      <View
        style={[
          styles.placeholder,
          {
            width: size * 0.76,
            height: size * 0.76,
            borderRadius: (size * 0.76) / 2,
          },
        ]}>
        <Text
          style={[
            styles.placeholderText,
            {
              fontSize: size * 0.38,
            },
          ]}>
          B
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  outer: {
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#334BFF',
    backgroundColor: '#0A0F24',
  },

  logo: {
    borderRadius: 999,
  },

  placeholder: {
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#111A45',
  },

  placeholderText: {
    color: '#FFFFFF',
    fontWeight: '900',
    letterSpacing: 1,
  },
});
