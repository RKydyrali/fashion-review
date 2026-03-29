import { Redirect, Tabs } from "expo-router";

import { ProductionTabBar } from "@/components/production-tab-bar";
import { routeForRole } from "@/navigation/role-routes";
import { useAuthStore } from "@/state/auth-store";

export default function ProductionLayout() {
  const { accessToken, hydrated, user } = useAuthStore();

  if (!hydrated) {
    return null;
  }

  if (!accessToken) {
    return <Redirect href="/login" />;
  }

  if (user?.role && user.role !== "production") {
    return <Redirect href={routeForRole(user.role)} />;
  }

  return (
    <Tabs
      tabBar={(props) => <ProductionTabBar {...props} />}
      screenOptions={{
        headerShown: false,
        sceneStyle: { backgroundColor: "#FFFFFF" }
      }}
    >
      <Tabs.Screen name="index" options={{ title: "Queue" }} />
      <Tabs.Screen name="shift" options={{ title: "Shift" }} />
    </Tabs>
  );
}
