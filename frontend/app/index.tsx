import { Redirect } from "expo-router";
import { useEffect } from "react";

import { routeForRole } from "@/navigation/role-routes";
import { useAuthStore } from "@/state/auth-store";

export default function Index() {
  const { accessToken, hydrated, hasSeenOnboarding, user } = useAuthStore();

  useEffect(() => {
    if (!hydrated) {
      useAuthStore.getState().bootstrap();
    }
  }, [hydrated]);

  if (!hydrated) {
    return null;
  }

  if (!hasSeenOnboarding) {
    return <Redirect href="/welcome" />;
  }

  if (!accessToken) {
    return <Redirect href="/login" />;
  }

  return <Redirect href={routeForRole(user?.role)} />;
}
