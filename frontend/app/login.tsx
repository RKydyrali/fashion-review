import { router } from "expo-router";
import { Controller, useForm } from "react-hook-form";
import { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { AuthScreenShell } from "@/components/auth-screen-shell";
import { useI18n } from "@/i18n";
import { routeForRole } from "@/navigation/role-routes";
import { api } from "@/services/api";
import { useAuthStore } from "@/state/auth-store";

type FormValues = { email: string; password: string };

export default function LoginScreen() {
  const { t } = useI18n();
  const [authError, setAuthError] = useState<string | null>(null);
  const { control, handleSubmit, formState } = useForm<FormValues>({
    defaultValues: { email: "", password: "" }
  });

  return (
    <AuthScreenShell
      title={t("auth.welcomeBack", "Welcome Back")}
      subtitle={t("auth.signInContinue", "Sign in to continue.")}
      primaryLabel={t("auth.needAccount", "Need an account?")}
      secondaryLabel={t("common.signUp", "Sign Up")}
      onSecondaryPress={() => router.push("/signup")}
    >
      <Controller
        control={control}
        name="email"
        render={({ field: { onChange, value } }) => (
          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>{t("common.email", "Email")}</Text>
            <TextInput
              style={[styles.input, authError ? styles.inputError : null]}
              value={value}
              onChangeText={(nextValue) => {
                if (authError) {
                  setAuthError(null);
                }
                onChange(nextValue);
              }}
              autoCapitalize="none"
              autoComplete="off"
              autoCorrect={false}
              spellCheck={false}
              importantForAutofill="no"
              keyboardType="email-address"
              placeholder={t("auth.clientEmailPlaceholder", "client@example.com")}
              placeholderTextColor="rgba(255,255,255,0.38)"
            />
          </View>
        )}
      />
      <Controller
        control={control}
        name="password"
        render={({ field: { onChange, value } }) => (
          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>{t("common.password", "Password")}</Text>
            <TextInput
              style={[styles.input, authError ? styles.inputError : null]}
              value={value}
              onChangeText={(nextValue) => {
                if (authError) {
                  setAuthError(null);
                }
                onChange(nextValue);
              }}
              secureTextEntry
              autoComplete="off"
              autoCorrect={false}
              spellCheck={false}
              importantForAutofill="no"
              placeholder={t("auth.passwordPlaceholder", "Password")}
              placeholderTextColor="rgba(255,255,255,0.38)"
            />
          </View>
        )}
      />

      {authError ? <Text style={styles.errorText}>{authError}</Text> : null}

      <Pressable
        style={[styles.buttonBase, styles.primaryButton, formState.isSubmitting ? styles.primaryButtonDisabled : null]}
        disabled={formState.isSubmitting}
        onPress={handleSubmit(async (values) => {
          setAuthError(null);
          try {
            const session = await api.login(values.email, values.password);
            await useAuthStore.getState().setSession(session);
            router.replace(routeForRole(session.user.role));
          } catch (error) {
            const fallbackError = t("auth.unableSignIn", "Unable to sign in right now.");
            const message = error instanceof Error ? error.message : fallbackError;
            setAuthError(message || fallbackError);
          }
        })}
      >
        <Text style={styles.primaryButtonText}>
          {formState.isSubmitting ? t("auth.checking", "Checking...") : t("common.login", "Login")}
        </Text>
      </Pressable>
    </AuthScreenShell>
  );
}

const styles = StyleSheet.create({
  fieldGroup: {
    gap: 8
  },
  fieldLabel: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 11,
    letterSpacing: 2.6,
    textTransform: "uppercase",
    color: "rgba(255, 255, 255, 0.76)"
  },
  input: {
    minHeight: 56,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.18)",
    borderRadius: 18,
    backgroundColor: "rgba(255, 255, 255, 0.1)",
    paddingHorizontal: 16,
    color: "#FFFFFF",
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 16
  },
  inputError: {
    borderColor: "#E8A4A4",
    backgroundColor: "rgba(120, 25, 25, 0.22)"
  },
  errorText: {
    marginTop: -2,
    marginBottom: 2,
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 13,
    lineHeight: 18,
    color: "#F3C1C1"
  },
  buttonBase: {
    minHeight: 56,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 6
  },
  primaryButton: {
    borderWidth: 1,
    borderColor: "#D7C39A",
    backgroundColor: "#D7C39A"
  },
  primaryButtonDisabled: {
    opacity: 0.72
  },
  primaryButtonText: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 12,
    letterSpacing: 3,
    textTransform: "uppercase",
    color: "#17120B"
  }
});
