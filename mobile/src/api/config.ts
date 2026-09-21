/**
 * BALLY FLOW API CONFIGURATION
 */

// Local development IP (your PC's LAN IP)
const LOCAL_LAN_URL = 'http://192.168.1.136:8000';

export const API_BASE_URL = LOCAL_LAN_URL;

// 35 seconds gives the 6-market H4/H1/M15 scans enough time to complete
export const API_TIMEOUT_MS = 35000;
