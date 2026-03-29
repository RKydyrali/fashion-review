import { router } from "expo-router";
import { useEffect, useRef } from "react";
import { Animated, Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useI18n } from "@/i18n";
import { WelcomeBackground } from "@/components/welcome-background";
import { useAuthStore } from "@/state/auth-store";

export default function WelcomeScreen() {
  const { t } = useI18n();
  const headlineOpacity = useRef(new Animated.Value(0)).current;
  const headlineTranslateY = useRef(new Animated.Value(72)).current;
  const headlineScale = useRef(new Animated.Value(0.94)).current;
  const ctaOpacity = useRef(new Animated.Value(0)).current;
  const ctaTranslateY = useRef(new Animated.Value(28)).current;
  const screenOpacity = useRef(new Animated.Value(1)).current;
  const screenScale = useRef(new Animated.Value(1)).current;
  const loginButtonScale = useRef(new Animated.Value(1)).current;
  const signupButtonScale = useRef(new Animated.Value(1)).current;
  const isNavigating = useRef(false);

  useEffect(() => {
    const headlineAnimation = Animated.parallel([
      Animated.timing(headlineOpacity, {
        toValue: 1,
        duration: 520,
        delay: 160,
        useNativeDriver: true
      }),
      Animated.spring(headlineTranslateY, {
        toValue: 0,
        tension: 32,
        friction: 9,
        useNativeDriver: true
      }),
      Animated.spring(headlineScale, {
        toValue: 1,
        tension: 34,
        friction: 10,
        useNativeDriver: true
      })
    ]);

    const ctaAnimation = Animated.parallel([
      Animated.timing(ctaOpacity, {
        toValue: 1,
        duration: 360,
        delay: 460,
        useNativeDriver: true
      }),
      Animated.timing(ctaTranslateY, {
        toValue: 0,
        duration: 360,
        delay: 460,
        useNativeDriver: true
      })
    ]);

    headlineAnimation.start();
    ctaAnimation.start();
  }, [ctaOpacity, ctaTranslateY, headlineOpacity, headlineScale, headlineTranslateY]);

  const animateButtonScale = (value: Animated.Value, toValue: number) => {
    Animated.spring(value, {
      toValue,
      tension: 260,
      friction: 18,
      useNativeDriver: true
    }).start();
  };

  const goToRoute = (route: "/login" | "/signup") => {
    if (isNavigating.current) {
      return;
    }

    isNavigating.current = true;
    useAuthStore.getState().completeOnboarding();
    Animated.parallel([
      Animated.timing(screenOpacity, {
        toValue: 0,
        duration: 220,
        useNativeDriver: true
      }),
      Animated.timing(screenScale, {
        toValue: 0.98,
        duration: 220,
        useNativeDriver: true
      }),
      Animated.timing(headlineOpacity, {
        toValue: 0,
        duration: 170,
        useNativeDriver: true
      }),
      Animated.timing(ctaOpacity, {
        toValue: 0,
        duration: 150,
        useNativeDriver: true
      }),
      Animated.timing(headlineTranslateY, {
        toValue: -18,
        duration: 220,
        useNativeDriver: true
      }),
      Animated.timing(ctaTranslateY, {
        toValue: 18,
        duration: 220,
        useNativeDriver: true
      })
    ]).start(() => {
      router.replace(route);
    });
  };

  return (
    <View style={styles.root}>
      <WelcomeBackground />
      <View pointerEvents="none" style={styles.videoTint} />
      <View pointerEvents="none" style={styles.topShade} />
      <View pointerEvents="none" style={styles.bottomShade} />

      <Animated.View
        style={[
          styles.foreground,
          {
            opacity: screenOpacity,
            transform: [{ scale: screenScale }]
          }
        ]}
      >
        <SafeAreaView style={styles.safeArea} edges={["top", "bottom"]}>
          <View style={styles.header} />

          <View style={styles.centerStage}>
            <Animated.View
              style={[
                styles.copyBlock,
                {
                  opacity: headlineOpacity,
                  transform: [{ translateY: headlineTranslateY }, { scale: headlineScale }]
                }
              ]}
            >
              <Text style={styles.headline}>AVISHU</Text>
              <Text style={styles.supportingCopy}>{t("welcome.tagline", "Curated fashion in motion.")}</Text>
            </Animated.View>
          </View>

          <Animated.View
            style={[
              styles.buttonStack,
              {
                opacity: ctaOpacity,
                transform: [{ translateY: ctaTranslateY }]
              }
            ]}
          >
            <Animated.View style={{ transform: [{ scale: loginButtonScale }] }}>
              <Pressable
                style={[styles.buttonBase, styles.primaryButton]}
                onPress={() => goToRoute("/login")}
                onPressIn={() => animateButtonScale(loginButtonScale, 0.97)}
                onPressOut={() => animateButtonScale(loginButtonScale, 1)}
              >
                <Text style={styles.primaryButtonText}>{t("common.login", "Login")}</Text>
              </Pressable>
            </Animated.View>
            <Animated.View style={{ transform: [{ scale: signupButtonScale }] }}>
              <Pressable
                style={[styles.buttonBase, styles.secondaryButton]}
                onPress={() => goToRoute("/signup")}
                onPressIn={() => animateButtonScale(signupButtonScale, 0.97)}
                onPressOut={() => animateButtonScale(signupButtonScale, 1)}
              >
                <Text style={styles.secondaryButtonText}>{t("common.signUp", "Sign Up")}</Text>
              </Pressable>
            </Animated.View>
          </Animated.View>
        </SafeAreaView>
      </Animated.View>
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
    zIndex: 1,
    backgroundColor: "rgba(9, 9, 11, 0.48)"
  },
  topShade: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: "28%",
    zIndex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.18)"
  },
  bottomShade: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    height: "34%",
    zIndex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.34)"
  },
  foreground: {
    ...StyleSheet.absoluteFillObject,
    zIndex: 2
  },
  safeArea: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 8,
    paddingBottom: 20
  },
  header: {
    minHeight: 24
  },
  centerStage: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center"
  },
  copyBlock: {
    width: "100%",
    maxWidth: 360,
    alignItems: "center"
  },
  headline: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 52,
    lineHeight: 56,
    letterSpacing: -1.2,
    color: "#FFFFFF",
    textShadowColor: "rgba(0, 0, 0, 0.65)",
    textShadowOffset: { width: 0, height: 3 },
    textShadowRadius: 18
  },
  supportingCopy: {
    marginTop: 12,
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 14,
    letterSpacing: 1.6,
    textTransform: "uppercase",
    color: "rgba(255, 255, 255, 0.86)",
    textShadowColor: "rgba(0, 0, 0, 0.42)",
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 8
  },
  buttonStack: {
    gap: 12
  },
  buttonBase: {
    minHeight: 56,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#000000",
    shadowOpacity: 0.18,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 8 },
    elevation: 6
  },
  primaryButton: {
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.88)",
    backgroundColor: "rgba(255, 255, 255, 0.96)"
  },
  secondaryButton: {
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.42)",
    backgroundColor: "rgba(10, 10, 10, 0.42)"
  },
  primaryButtonText: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 12,
    letterSpacing: 3,
    textTransform: "uppercase",
    color: "#0A0A0A"
  },
  secondaryButtonText: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 12,
    letterSpacing: 3,
    textTransform: "uppercase",
    color: "#FFFFFF"
  }
});
