import React from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  Appearance,
  ColorSchemeName,
} from 'react-native';

import {
  AppTheme,
  ThemeMode,
  createTheme,
} from './themes';

const THEME_STORAGE_KEY = '@bally_flow_theme';

type ThemeContextValue = {
  theme: AppTheme;
  themeMode: ThemeMode;
  setThemeMode: (mode: ThemeMode) => Promise<void>;
  isLoading: boolean;
};

const ThemeContext =
  React.createContext<ThemeContextValue | undefined>(
    undefined,
  );

export function ThemeProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const initialSystemScheme =
    Appearance.getColorScheme() ?? 'dark';

  const [currentSystemScheme, setCurrentSystemScheme] =
    React.useState<ColorSchemeName>(
      initialSystemScheme,
    );

  const [themeMode, setThemeModeState] =
    React.useState<ThemeMode>('DARK');

  const [isLoading, setIsLoading] =
    React.useState(true);

  React.useEffect(() => {
    const loadTheme = async () => {
      try {
        const stored =
          await AsyncStorage.getItem(
            THEME_STORAGE_KEY,
          );

        if (
          stored === 'DARK' ||
          stored === 'LIGHT' ||
          stored === 'SYSTEM'
        ) {
          setThemeModeState(stored);
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadTheme();
  }, []);

  React.useEffect(() => {
    const subscription =
      Appearance.addChangeListener(({colorScheme}) => {
        setCurrentSystemScheme(
          colorScheme ?? 'dark',
        );
      });

    return () => subscription.remove();
  }, []);

  const setThemeMode = async (
    mode: ThemeMode,
  ) => {
    setThemeModeState(mode);

    await AsyncStorage.setItem(
      THEME_STORAGE_KEY,
      mode,
    );
  };

  const theme = React.useMemo(
    () =>
      createTheme(
        themeMode,
        currentSystemScheme,
      ),
    [themeMode, currentSystemScheme],
  );

  return (
    <ThemeContext.Provider
      value={{
        theme,
        themeMode,
        setThemeMode,
        isLoading,
      }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const context = React.useContext(ThemeContext);

  if (!context) {
    throw new Error(
      'useTheme must be used inside ThemeProvider',
    );
  }

  return context;
}