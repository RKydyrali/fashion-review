import Constants from "expo-constants";
import { Platform } from "react-native";

const configured = process.env.EXPO_PUBLIC_API_URL ?? Constants.expoConfig?.extra?.apiUrl;

function extractDevelopmentHost() {
  const candidates = [
    Constants.expoConfig?.hostUri,
    Constants.platform?.hostUri,
    Constants.linkingUri
  ];

  for (const candidate of candidates) {
    if (typeof candidate !== "string" || !candidate.trim()) {
      continue;
    }

    const normalized = candidate.includes("://") ? candidate : `http://${candidate}`;

    try {
      const { hostname } = new URL(normalized);
      if (hostname) {
        return hostname;
      }
    } catch {
      continue;
    }
  }

  return null;
}

function defaultBaseUrl() {
  if (configured) {
    return configured;
  }
  const developmentHost = extractDevelopmentHost();
  if (developmentHost) {
    return `http://${developmentHost}:8000`;
  }
  if (Platform.OS === "android") {
    return "http://10.0.2.2:8000";
  }
  return "http://127.0.0.1:8000";
}

export const API_BASE_URL = defaultBaseUrl();
export const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");
