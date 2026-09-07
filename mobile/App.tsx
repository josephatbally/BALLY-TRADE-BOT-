import React from 'react';
import {StatusBar} from 'react-native';
import {SafeAreaProvider} from 'react-native-safe-area-context';

import AppNavigator from './src/navigation/AppNavigator';
import {ThemeProvider, useTheme} from './src/theme/ThemeContext';

function AppContent() {
  const {theme} = useTheme();

  return (
    <>
      <StatusBar
        barStyle={
          theme.isDark
            ? 'light-content'
            : 'dark-content'
        }
      />

      <AppNavigator />
    </>
  );
}

function App() {
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <AppContent />
      </ThemeProvider>
    </SafeAreaProvider>
  );
}

export default App;