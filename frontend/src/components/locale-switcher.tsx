import { Pressable, StyleSheet, Text, View } from "react-native";

import { useI18n } from "@/i18n";
import type { LocaleCode } from "@/services/api/types";
import { useAuthStore } from "@/state/auth-store";

const localeOptions: LocaleCode[] = ["en", "ru", "kk"];

export function LocaleSwitcher({ dark }: { dark?: boolean }) {
  const activeLocale = useAuthStore((state) => state.locale);
  const { t } = useI18n();

  return (
    <View style={styles.row}>
      {localeOptions.map((locale) => {
        const selected = activeLocale === locale;
        return (
          <Pressable
            key={locale}
            style={({ pressed }) => [
              styles.pill,
              dark ? styles.pillDark : styles.pillLight,
              selected ? (dark ? styles.pillDarkSelected : styles.pillLightSelected) : null,
              pressed ? styles.pillPressed : null
            ]}
            onPress={() => useAuthStore.getState().setLocale(locale)}
          >
            <Text
              style={[
                styles.pillText,
                dark ? styles.pillTextDark : styles.pillTextLight,
                selected ? styles.pillTextSelected : null
              ]}
            >
              {t(`lang.${locale}`, locale.toUpperCase())}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    justifyContent: "center",
    gap: 8
  },
  pill: {
    minHeight: 34,
    paddingHorizontal: 14,
    borderRadius: 999,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center"
  },
  pillLight: {
    borderColor: "rgba(255, 255, 255, 0.22)",
    backgroundColor: "rgba(255, 255, 255, 0.08)"
  },
  pillDark: {
    borderColor: "#D6D6D6",
    backgroundColor: "#FFFFFF"
  },
  pillLightSelected: {
    borderColor: "#D7C39A",
    backgroundColor: "#D7C39A"
  },
  pillDarkSelected: {
    borderColor: "#000000",
    backgroundColor: "#000000"
  },
  pillPressed: {
    opacity: 0.84
  },
  pillText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 10,
    lineHeight: 12,
    letterSpacing: 1.2,
    textTransform: "uppercase"
  },
  pillTextLight: {
    color: "#FFFFFF"
  },
  pillTextDark: {
    color: "#17120B"
  },
  pillTextSelected: {
    color: "#FFFFFF"
  }
});
