import { Redirect, Tabs } from "expo-router";

import { FranchiseTabBar } from "@/components/franchise-tab-bar";
import { routeForRole } from "@/navigation/role-routes";
import { useAuthStore } from "@/state/auth-store";

export default function FranchiseLayout() {
  const { accessToken, hydrated, user } = useAuthStore();

  if (!hydrated) {
    return null;
  }

  if (!accessToken) {
    return <Redirect href="/login" />;
  }

  if (user?.role && user.role !== "franchisee") {
    return <Redirect href={routeForRole(user.role)} />;
  }

  return (
    <Tabs
      tabBar={(props) => <FranchiseTabBar {...props} />}
      screenOptions={{
        headerShown: false,
        sceneStyle: { backgroundColor: "#FFFFFF" }
      }}
    >
      <Tabs.Screen name="index" options={{ title: "Dashboard" }} />
      <Tabs.Screen name="sales" options={{ title: "Sales" }} />
      <Tabs.Screen name="settings" options={{ title: "Settings" }} />
    </Tabs>
  );
}
