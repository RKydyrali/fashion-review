import { Feather } from "@expo/vector-icons";
import type { BottomTabBarProps } from "@react-navigation/bottom-tabs";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { editorialTheme } from "@/components/ui";

export function FranchiseTabBar({ state, descriptors, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();

  const tabs = {
    index: { label: "Dashboard", compactLabel: "DASHBOARD", icon: "home" },
    sales: { label: "Sales", compactLabel: "SALES", icon: "bar-chart-2" },
    settings: { label: "Settings", compactLabel: "SETTINGS", icon: "settings" }
  } as const;

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
