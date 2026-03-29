import { create } from "zustand";

import * as storage from "@/services/storage/kv";
import type { AuthSession, LocaleCode, User } from "@/services/api/types";

const ACCESS_TOKEN_KEY = "avishu_access_token";
const REFRESH_TOKEN_KEY = "avishu_refresh_token";
const ONBOARDING_KEY = "avishu_has_seen_onboarding";
const USER_KEY = "avishu_user";
const LOCALE_KEY = "avishu_locale";

function detectSystemLocale(): LocaleCode {
  const fallback: LocaleCode = "en";

  try {
    const locale = Intl.DateTimeFormat().resolvedOptions().locale?.toLowerCase();
    if (!locale) {
      return fallback;
    }
    if (locale.startsWith("ru")) {
      return "ru";
    }
    if (locale.startsWith("kk")) {
      return "kk";
    }
    return "en";
  } catch {
    return fallback;
  }
}

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  locale: LocaleCode;
  hasSeenOnboarding: boolean;
  hydrated: boolean;
  bootstrap: () => Promise<void>;
  setSession: (session: AuthSession) => Promise<void>;
  clearSession: () => Promise<void>;
  setLocale: (locale: LocaleCode) => void;
  completeOnboarding: () => void;
};

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  locale: "en",
  hasSeenOnboarding: false,
  hydrated: false,
  bootstrap: async () => {
    const accessToken = await storage.getItem(ACCESS_TOKEN_KEY);
    const refreshToken = await storage.getItem(REFRESH_TOKEN_KEY);
    const hasSeenOnboarding = (await storage.getItem(ONBOARDING_KEY)) === "true";
    const storedUser = await storage.getItem(USER_KEY);
    const storedLocale = await storage.getItem(LOCALE_KEY);
    let user: User | null = null;
    if (storedUser) {
      try {
        user = JSON.parse(storedUser) as User;
      } catch {
        user = null;
      }
    }
    set({
      accessToken,
      refreshToken,
      user,
      locale: user?.preferred_language ?? (storedLocale as LocaleCode | null) ?? detectSystemLocale(),
      hasSeenOnboarding,
      hydrated: true
    });
  },
  setSession: async (session) => {
    await storage.setItem(ACCESS_TOKEN_KEY, session.access_token);
    await storage.setItem(REFRESH_TOKEN_KEY, session.refresh_token);
    await storage.setItem(USER_KEY, JSON.stringify(session.user));
    await storage.setItem(LOCALE_KEY, session.user.preferred_language);
    set({
      accessToken: session.access_token,
      refreshToken: session.refresh_token,
      user: session.user,
      locale: session.user.preferred_language
    });
  },
  clearSession: async () => {
    await storage.deleteItem(ACCESS_TOKEN_KEY);
    await storage.deleteItem(REFRESH_TOKEN_KEY);
    await storage.deleteItem(USER_KEY);
    set({
      accessToken: null,
      refreshToken: null,
      user: null
    });
  },
  setLocale: (locale) => {
    void storage.setItem(LOCALE_KEY, locale);
    set({ locale });
  },
  completeOnboarding: () => {
    void storage.setItem(ONBOARDING_KEY, "true");
    set({ hasSeenOnboarding: true });
  }
}));
