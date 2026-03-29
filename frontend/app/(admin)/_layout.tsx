import { Redirect, Stack } from "expo-router";

import { routeForRole } from "@/navigation/role-routes";
import { useAuthStore } from "@/state/auth-store";

export default function AdminLayout() {
  const { accessToken, hydrated, user } = useAuthStore();

  if (!hydrated) {
    return null;
  }

  if (!accessToken) {
    return <Redirect href="/login" />;
  }

  if (user?.role && user.role !== "admin") {
    return <Redirect href={routeForRole(user.role)} />;
  }

  return <Stack screenOptions={{ headerShown: false }} />;
}
