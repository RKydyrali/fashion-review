import { Redirect, Tabs } from "expo-router";

import { EditorialTabBar } from "@/components/editorial-tab-bar";
import { useRealtimeSync } from "@/hooks/useRealtimeSync";
import { routeForRole } from "@/navigation/role-routes";
import { useAuthStore } from "@/state/auth-store";

export default function TabsLayout() {
  const { accessToken, hydrated, user } = useAuthStore();

  useRealtimeSync();

  if (!hydrated) {
    return null;
  }

  if (!accessToken) {
    return <Redirect href="/login" />;
  }

  if (user?.role && user.role !== "client") {
    return <Redirect href={routeForRole(user.role)} />;
  }

  return (
    <Tabs
      tabBar={(props) => <EditorialTabBar {...props} />}
      screenOptions={{
        headerShown: false,
        sceneStyle: { backgroundColor: "#F6F1EA" }
      }}
    >
      <Tabs.Screen name="home" options={{ title: "Home" }} />
      <Tabs.Screen name="collections" options={{ title: "Collect" }} />
      <Tabs.Screen name="bag" options={{ title: "Bag" }} />
      <Tabs.Screen name="orders" options={{ title: "Orders" }} />
      <Tabs.Screen name="profile" options={{ title: "Profile" }} />
    </Tabs>
  );
}
