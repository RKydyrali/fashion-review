import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

const memoryStore = new Map<string, string>();

function canUseLocalStorage() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

export async function getItem(key: string) {
  if (Platform.OS === "web") {
    if (canUseLocalStorage()) {
      const value = window.localStorage.getItem(key);
      if (value !== null) {
        return value;
      }
    }
    return memoryStore.get(key) ?? null;
  }

  return SecureStore.getItemAsync(key);
}

export async function setItem(key: string, value: string) {
  if (Platform.OS === "web") {
    if (canUseLocalStorage()) {
      window.localStorage.setItem(key, value);
      return;
    }
    memoryStore.set(key, value);
    return;
  }

  await SecureStore.setItemAsync(key, value);
}

export async function deleteItem(key: string) {
  if (Platform.OS === "web") {
    if (canUseLocalStorage()) {
      window.localStorage.removeItem(key);
    }
    memoryStore.delete(key);
    return;
  }

  await SecureStore.deleteItemAsync(key);
}
