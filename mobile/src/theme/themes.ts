import {ColorSchemeName} from 'react-native';

export type ThemeMode = 'DARK' | 'LIGHT' | 'SYSTEM';

export type AppTheme = {
  mode: ThemeMode;
  isDark: boolean;

  colors: {
    background: string;
    surface: string;
    surfaceSecondary: string;
    border: string;

    primary: string;
    primaryStrong: string;

    text: string;
    textSecondary: string;
    textMuted: string;

    success: string;
    warning: string;
    danger: string;

    inputBackground: string;
    divider: string;
  };
};

const darkColors = {
  background: '#05070D',
  surface: '#0A0E18',
  surfaceSecondary: '#0B1020',
  border: '#1B2435',

  primary: '#7083FF',
  primaryStrong: '#5067E5',

  text: '#FFFFFF',
  textSecondary: '#A8B2C7',
  textMuted: '#69758E',

  success: '#58D7A0',
  warning: '#FFBE63',
  danger: '#FF7185',

  inputBackground: '#11182A',
  divider: '#172032',
};

const lightColors = {
  background: '#F4F6FB',
  surface: '#FFFFFF',
  surfaceSecondary: '#EEF1F8',
  border: '#D9DEEA',

  primary: '#5368E8',
  primaryStrong: '#3F54CF',

  text: '#101522',
  textSecondary: '#4E5970',
  textMuted: '#737D92',

  success: '#159A68',
  warning: '#C77A08',
  danger: '#D9485F',

  inputBackground: '#F0F3F9',
  divider: '#E1E5EE',
};

export const createTheme = (
  mode: ThemeMode,
  systemScheme: ColorSchemeName,
): AppTheme => {
  const isDark =
    mode === 'DARK' ||
    (mode === 'SYSTEM' && systemScheme !== 'light');

  return {
    mode,
    isDark,
    colors: isDark ? darkColors : lightColors,
  };
};
