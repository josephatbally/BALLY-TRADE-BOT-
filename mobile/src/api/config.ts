/**
 * BALLY FLOW API CONFIGURATION
 */

// Local development IP (your PC's current LAN IP)
const DEV_API_URL = 'http://192.168.1.136:8000';

// For local release APK testing, use the same LAN IP:
const PROD_API_URL = 'http://192.168.1.136:8000';

export const API_BASE_URL = __DEV__ ? DEV_API_URL : PROD_API_URL;

// 35 seconds gives the 6-market H4/H1/M15 scans enough time to complete
export const API_TIMEOUT_MS = 35000;
