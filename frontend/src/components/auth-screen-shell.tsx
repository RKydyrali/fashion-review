import { PropsWithChildren } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { LocaleSwitcher } from "@/components/locale-switcher";
import { WelcomeBackground } from "@/components/welcome-background";

type AuthScreenShellProps = PropsWithChildren<{
  title: string;
  subtitle: string;
  primaryLabel: string;
  secondaryLabel: string;
  onSecondaryPress: () => void;
}>;

export function AuthScreenShell({
  title,
  subtitle,
  primaryLabel,
  secondaryLabel,
  onSecondaryPress,
  children
}: AuthScreenShellProps) {
  return (
    <View style={styles.root}>
      <WelcomeBackground />
      <View style={styles.videoTint} />
      <View style={styles.topShade} />
      <View style={styles.bottomShade} />

      <SafeAreaView style={styles.safeArea} edges={["top", "bottom"]}>
        <View style={styles.centerColumn}>
          <LocaleSwitcher dark />

          <View style={styles.hero}>
            <Text style={styles.title}>{title}</Text>
            <Text style={styles.subtitle}>{subtitle}</Text>
          </View>

          <View style={styles.panel}>
            <View style={styles.formArea}>{children}</View>
            <View style={styles.footer}>
              <Text style={styles.footerLabel}>{primaryLabel}</Text>
              <Pressable onPress={onSecondaryPress} style={styles.secondaryLink}>
                <Text style={styles.secondaryLinkText}>{secondaryLabel}</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    width: "100%",
    height: "100%",
    overflow: "hidden",
    backgroundColor: "#09090B"
  },
  videoTint: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(9, 9, 11, 0.5)"
  },
  topShade: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: "28%",
    backgroundColor: "rgba(0, 0, 0, 0.14)"
  },
  bottomShade: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    height: "42%",
    backgroundColor: "rgba(0, 0, 0, 0.38)"
  },
  safeArea: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 8,
    paddingBottom: 20
  },
  centerColumn: {
    flex: 1,
    width: "100%",
    maxWidth: 420,
    alignSelf: "center",
    justifyContent: "center",
    gap: 24
  },
  hero: {
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 16
  },
  title: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 48,
    lineHeight: 52,
    letterSpacing: -1,
    color: "#FFFFFF",
    textAlign: "center",
    textShadowColor: "rgba(0, 0, 0, 0.64)",
    textShadowOffset: { width: 0, height: 3 },
    textShadowRadius: 18
  },
  subtitle: {
    marginTop: 12,
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 13,
    lineHeight: 18,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: "rgba(255, 255, 255, 0.84)",
    textAlign: "center",
    textShadowColor: "rgba(0, 0, 0, 0.42)",
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 8
  },
  panel: {
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.16)",
    borderRadius: 28,
    backgroundColor: "rgba(10, 10, 10, 0.44)",
    paddingHorizontal: 18,
    paddingTop: 18,
    paddingBottom: 20
  },
  formArea: {
    gap: 12
  },
  footer: {
    marginTop: 18,
    alignItems: "center",
    gap: 10
  },
  footerLabel: {
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 12,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: "rgba(255, 255, 255, 0.62)"
  },
  secondaryLink: {
    paddingVertical: 4,
    paddingHorizontal: 8
  },
  secondaryLinkText: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 12,
    letterSpacing: 2.4,
    textTransform: "uppercase",
    color: "#FFFFFF"
  }
});
