export type BrokerCredentials = {
  brokerName?: string;
  server: string;
  accountNumber: string;
  currency?: string;
  leverage?: number;
  connected?: boolean;
};

export type AuthenticatedUser = {
  id: string;
  email: string;
  firstName: string;
  displayName: string;
  phone?: string;
  countryCode?: string;
  token?: string; // Add this line
  broker?: BrokerCredentials;
};


export type FlowSymbol =
  | "XAUUSD"
  | "EURUSD"
  | "GBPUSD"
  | "USDJPY"
  | "XAGUSD"
  | "NASDAQ";

export type FlowDecision =
  | "BUY"
  | "SELL"
  | "NO TRADE";

export type RootStackParamList = {
  Splash: undefined;
  Login: undefined;
  BrokerSetup: AuthenticatedUser;

  MainTabs: AuthenticatedUser;

  History: AuthenticatedUser;
  Notifications: AuthenticatedUser;
  Settings: AuthenticatedUser;
  ThemeSelection: AuthenticatedUser;
  BotControl: AuthenticatedUser;
  TradingPreferences: AuthenticatedUser;
  RiskConfiguration: AuthenticatedUser;
  Security: AuthenticatedUser;
  AccountInformation: AuthenticatedUser;

  FlowMarketSelection: {
    user: AuthenticatedUser;
  };
  FlowAnalysis: {
    user: AuthenticatedUser;
    symbol: FlowSymbol;
  };
  FlowConfluence: {
    user: AuthenticatedUser;
    symbol: FlowSymbol;
  };
  FlowConfidence: {
    user: AuthenticatedUser;
    symbol: FlowSymbol;
  };
  FlowDecision: {
    user: AuthenticatedUser;
    symbol: FlowSymbol;
    confidence?: number;
  };
  FlowValidation: {
    user: AuthenticatedUser;
    symbol: FlowSymbol;
    decision?: FlowDecision;
    confidence?: number;
  };
  FlowExecution: {
    user: AuthenticatedUser;
    symbol: FlowSymbol;
    decision?: FlowDecision;
    confidence?: number;
    validationStatus?: string;
  };
};
