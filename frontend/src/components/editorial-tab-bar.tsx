import { Feather } from "@expo/vector-icons";
import type { BottomTabBarProps } from "@react-navigation/bottom-tabs";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useI18n } from "@/i18n";
import { editorialTheme } from "@/components/ui";

export function EditorialTabBar({ state, descriptors, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();
  const { t } = useI18n();
  const focusedRoute = state.routes[state.index];
  const focusedRouteParams = focusedRoute?.params as { mode?: string } | undefined;
  const tabs = {
    home: { label: t("tab.home", "Home"), compactLabel: t("tab.homeCompact", "HOME"), icon: "home" },
    collections: { label: t("tab.collect", "Collect"), compactLabel: t("tab.collectCompact", "COLLECT"), icon: "grid" },
    bag: { label: t("tab.bag", "Bag"), compactLabel: t("tab.bagCompact", "BAG"), icon: "shopping-bag" },
    orders: { label: t("tab.orders", "Orders"), compactLabel: t("tab.ordersCompact", "ORDERS"), icon: "package" },
    profile: { label: t("tab.profile", "Profile"), compactLabel: t("tab.profileCompact", "PROFILE"), icon: "user" }
  } as const;

  if (focusedRoute?.name === "collections" && focusedRouteParams?.mode === "editorial") {
    return null;
  }

  return (
    <View pointerEvents="box-none" style={[styles.outer, { paddingBottom: Math.max(insets.bottom, 12) }]}>
      <View style={styles.shell}>
        {state.routes.map((route, index) => {
          const config = tabs[route.name as keyof typeof tabs];
          if (!config) {
            return null;
          }

          const isFocused = state.index === index;

          return (
            <Pressable
              key={route.key}
              accessibilityRole="button"
              accessibilityState={isFocused ? { selected: true } : {}}
              onPress={() => {
                const event = navigation.emit({ type: "tabPress", target: route.key, canPreventDefault: true });
                if (!isFocused && !event.defaultPrevented) {
                  navigation.navigate(route.name, route.params);
                }
              }}
              onLongPress={() => navigation.emit({ type: "tabLongPress", target: route.key })}
              style={({ pressed }) => [styles.item, pressed ? styles.itemPressed : null]}
            >
              <View style={[styles.iconCapsule, isFocused ? styles.iconCapsuleActive : null]}>
                <Feather
                  name={config.icon}
                  size={20}
                  color={isFocused ? editorialTheme.surface : editorialTheme.textMuted}
                />
                {isFocused ? <Text style={styles.activeCapsuleText}>{config.compactLabel}</Text> : null}
              </View>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  outer: {
    position: "absolute",
    left: 20,
    right: 20,
    bottom: 0
  },
  shell: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 6,
    paddingTop: 8,
    paddingBottom: 8,
    borderRadius: 2,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surface,
    shadowColor: editorialTheme.shadow,
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.04,
    shadowRadius: 12,
    elevation: 6
  },
  item: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center"
  },
  itemPressed: {
    opacity: 0.82
  },
  iconCapsule: {
    minHeight: 44,
    minWidth: 44,
    borderRadius: 2,
    paddingHorizontal: 10,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8
  },
  iconCapsuleActive: {
    backgroundColor: editorialTheme.text
  },
  activeCapsuleText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 10,
    lineHeight: 12,
    letterSpacing: 1.4,
    color: editorialTheme.surface
  },
});
