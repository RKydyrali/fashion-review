import { SpaceGrotesk_400Regular, SpaceGrotesk_500Medium, SpaceGrotesk_700Bold, useFonts } from "@expo-google-fonts/space-grotesk";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as SplashScreen from "expo-splash-screen";
import { PropsWithChildren, useEffect } from "react";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { useAuthStore } from "@/state/auth-store";
import { useStyleStore } from "@/state/style-store";

SplashScreen.preventAutoHideAsync().catch(() => undefined);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: (failureCount, error) => {
        if (error instanceof Error && error.message.includes("Cannot connect to AVISHU API")) {
          return false;
        }
        return failureCount < 1;
      }
    }
  }
});

export function AppProviders({ children }: PropsWithChildren) {
  const [fontsLoaded] = useFonts({
    SpaceGrotesk_400Regular,
    SpaceGrotesk_500Medium,
    SpaceGrotesk_700Bold
  });
  const hydrated = useAuthStore((state) => state.hydrated);
  const styleHydrated = useStyleStore((state) => state.hydrated);
  const userId = useAuthStore((state) => state.user?.id);

  useEffect(() => {
    if (fontsLoaded) {
      SplashScreen.hideAsync().catch(() => undefined);
    }
  }, [fontsLoaded]);

  useEffect(() => {
    if (!hydrated) {
      void useAuthStore.getState().bootstrap();
    }
  }, [hydrated]);

  useEffect(() => {
    if (hydrated && !styleHydrated) {
      void useStyleStore.getState().bootstrap(userId ?? null);
    }
  }, [hydrated, styleHydrated, userId]);

  useEffect(() => {
    if (hydrated && styleHydrated) {
      void useStyleStore.getState().bootstrap(userId ?? null);
    }
  }, [hydrated, styleHydrated, userId]);

  if (!fontsLoaded) {
    return null;
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
