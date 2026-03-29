import { router } from "expo-router";
import { Controller, useForm } from "react-hook-form";
import { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { AuthScreenShell } from "@/components/auth-screen-shell";
import { useI18n } from "@/i18n";
import { routeForRole } from "@/navigation/role-routes";
import { api } from "@/services/api";
import { useAuthStore } from "@/state/auth-store";

type FormValues = { full_name: string; email: string; password: string };

export default function SignupScreen() {
  const { t, locale } = useI18n();
  const [signupError, setSignupError] = useState<string | null>(null);
  const { control, handleSubmit, formState } = useForm<FormValues>({
    defaultValues: { full_name: "", email: "", password: "" }
  });
  const { errors, isSubmitting } = formState;

  return (
    <AuthScreenShell
      title={t("auth.createAccount", "Create Account")}
      subtitle={t("auth.startProfile", "Start your profile.")}
      primaryLabel={t("auth.alreadyRegistered", "Already registered?")}
      secondaryLabel={t("common.login", "Login")}
      onSecondaryPress={() => router.push("/login")}
    >
      <Controller
        control={control}
        name="full_name"
        rules={{ required: t("auth.nameRequired", "Name is required.") }}
        render={({ field: { onChange, value } }) => (
          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>{t("common.name", "Name")}</Text>
            <TextInput
              style={[styles.input, signupError ? styles.inputError : null]}
              value={value}
              onChangeText={(nextValue) => {
                if (signupError) {
                  setSignupError(null);
                }
                onChange(nextValue);
              }}
              autoCapitalize="words"
              autoComplete="off"
              autoCorrect={false}
              spellCheck={false}
              importantForAutofill="no"
              placeholder={t("auth.namePlaceholder", "Your name")}
              placeholderTextColor="rgba(255,255,255,0.38)"
            />
            {errors.full_name ? <Text style={styles.fieldErrorText}>{errors.full_name.message}</Text> : null}
          </View>
        )}
      />
      <Controller
        control={control}
        name="email"
        rules={{
          required: t("auth.emailRequired", "Email is required."),
          pattern: {
            value: /\S+@\S+\.\S+/,
            message: t("auth.validEmail", "Enter a valid email address.")
          }
        }}
        render={({ field: { onChange, value } }) => (
          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>{t("common.email", "Email")}</Text>
            <TextInput
              style={[styles.input, signupError ? styles.inputError : null]}
              value={value}
              onChangeText={(nextValue) => {
                if (signupError) {
                  setSignupError(null);
                }
                onChange(nextValue);
              }}
              autoCapitalize="none"
              autoComplete="off"
              autoCorrect={false}
              spellCheck={false}
              importantForAutofill="no"
              keyboardType="email-address"
              placeholder={t("auth.newClientEmailPlaceholder", "newclient@example.com")}
              placeholderTextColor="rgba(255,255,255,0.38)"
            />
            {errors.email ? <Text style={styles.fieldErrorText}>{errors.email.message}</Text> : null}
          </View>
        )}
      />
      <Controller
        control={control}
        name="password"
        rules={{
          required: t("auth.passwordRequired", "Password is required."),
          minLength: { value: 8, message: t("auth.passwordLength", "Password must be at least 8 characters.") }
        }}
        render={({ field: { onChange, value } }) => (
          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>{t("common.password", "Password")}</Text>
            <TextInput
              style={[styles.input, signupError ? styles.inputError : null]}
              value={value}
              onChangeText={(nextValue) => {
                if (signupError) {
                  setSignupError(null);
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
            {errors.password ? <Text style={styles.fieldErrorText}>{errors.password.message}</Text> : null}
          </View>
        )}
      />

      {signupError ? <Text style={styles.errorText}>{signupError}</Text> : null}

      <Pressable
        style={[styles.buttonBase, styles.primaryButton, isSubmitting ? styles.primaryButtonDisabled : null]}
        disabled={isSubmitting}
        onPress={handleSubmit(async (values) => {
          setSignupError(null);
          try {
            const session = await api.signup({ ...values, preferred_language: locale });
            await useAuthStore.getState().setSession(session);
            router.replace(routeForRole(session.user.role));
          } catch (error) {
            const fallbackError = t("auth.unableSignUp", "Unable to sign up right now.");
            const message = error instanceof Error ? error.message : fallbackError;
            setSignupError(message || fallbackError);
          }
        })}
      >
        <Text style={styles.primaryButtonText}>
          {isSubmitting ? t("auth.creating", "Creating...") : t("common.signUp", "Sign Up")}
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
  fieldErrorText: {
    marginTop: 2,
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 12,
    lineHeight: 16,
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
