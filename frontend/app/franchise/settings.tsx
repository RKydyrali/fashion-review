import { useState } from "react";
import { router } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import {
  BodyText,
  CardFrame,
  EditorialButton,
  EditorialPill,
  EditorialTitle,
  Screen,
  SectionLabel,
  editorialSerif,
  editorialTheme
} from "@/components/ui";
import { api } from "@/services/api";
import { useAuthStore } from "@/state/auth-store";
import type { LocaleCode } from "@/services/api/types";

type ApprovalMode = "auto" | "manual";

function getTimeRemaining(isoDate?: string | null): string | null {
  if (!isoDate) return null;
  const now = new Date();
  const until = new Date(isoDate);
  const diff = until.getTime() - now.getTime();
  
  if (diff <= 0) return "Expired";
  
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  
  if (hours >= 24) {
    const days = Math.floor(hours / 24);
    return `${days} day${days > 1 ? "s" : ""} left`;
  }
  
  return `${hours}h ${minutes}m left`;
}

export default function FranchiseSettings() {
  const queryClient = useQueryClient();
  const { accessToken, user, setLocale } = useAuthStore();
  const queryEnabled = Boolean(accessToken) && user?.role === "franchisee";

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const { data: settings, isLoading } = useQuery({
    queryKey: ["franchise-settings"],
    queryFn: api.franchiseSettings,
    enabled: queryEnabled
  });

  const updateSettings = useMutation({
    mutationFn: api.updateFranchiseSettings,
    onSuccess: (data) => {
      if (data.preferred_language) {
        setLocale(data.preferred_language);
      }
      queryClient.invalidateQueries({ queryKey: ["franchise-settings"] });
      Alert.alert("Success", "Settings updated successfully");
    },
    onError: () => {
      Alert.alert("Error", "Failed to update settings");
    }
  });

  const changePassword = useMutation({
    mutationFn: async () => {
      if (newPassword !== confirmPassword) {
        throw new Error("Passwords do not match");
      }
      if (newPassword.length < 6) {
        throw new Error("Password must be at least 6 characters");
      }
      return api.updateProfile({ current_password: currentPassword, new_password: newPassword });
    },
    onSuccess: () => {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      Alert.alert("Success", "Password changed successfully");
    },
    onError: (error: Error) => {
      Alert.alert("Error", error.message || "Failed to change password");
    }
  });

  const languages: { id: LocaleCode; label: string }[] = [
    { id: "en", label: "English" },
    { id: "ru", label: "Русский" },
    { id: "kk", label: "Қазақша" }
  ];

  const activeLanguage = settings?.preferred_language ?? user?.preferred_language ?? "en";

  const handleApprovalModeChange = (mode: ApprovalMode) => {
    if (mode === "auto") {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      updateSettings.mutate({
        approval_mode: "auto",
        preferred_language: activeLanguage
      });
      Alert.alert(
        "Auto-Approve Enabled",
        "Orders will be automatically approved for 24 hours, then switch to manual mode."
      );
    } else {
      updateSettings.mutate({
        approval_mode: "manual",
        preferred_language: activeLanguage
      });
    }
  };

  const timeRemaining = getTimeRemaining(settings?.auto_approve_until);

  return (
    <Screen contentContainerStyle={styles.screenContent}>
      <SectionLabel>Franchise</SectionLabel>
      <EditorialTitle style={styles.pageTitle}>Settings</EditorialTitle>
      <BodyText style={styles.pageCopy}>
        Manage your branch preferences and account
      </BodyText>

      <CardFrame style={styles.sectionCard}>
        <SectionLabel style={styles.sectionEyebrow}>Branch Info</SectionLabel>
        <Text style={styles.sectionTitle}>Your Branch</Text>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Branch ID</Text>
          <Text style={styles.infoValue}>#{settings?.branch_id ?? user?.branch_id ?? "—"}</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Branch Name</Text>
          <Text style={styles.infoValue}>{settings?.branch_name ?? "Branch"}</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Manager</Text>
          <Text style={styles.infoValue}>{user?.full_name ?? "—"}</Text>
        </View>
      </CardFrame>

      <CardFrame style={styles.sectionCard}>
        <SectionLabel style={styles.sectionEyebrow}>Language</SectionLabel>
        <Text style={styles.sectionTitle}>Interface Language</Text>
        <View style={styles.languageRow}>
          {languages.map((lang) => {
            const selected = activeLanguage === lang.id;
            return (
              <Pressable
                key={lang.id}
                style={({ pressed }) => [
                  styles.languageButton,
                  selected ? styles.languageButtonSelected : null,
                  pressed ? styles.buttonPressed : null
                ]}
                onPress={() => {
                  setLocale(lang.id);
                  updateSettings.mutate({ preferred_language: lang.id });
                }}
              >
                <Text style={[styles.languageButtonText, selected ? styles.languageButtonTextSelected : null]}>
                  {lang.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </CardFrame>

      <CardFrame style={styles.sectionCard}>
        <SectionLabel style={styles.sectionEyebrow}>Order Approval</SectionLabel>
        <Text style={styles.sectionTitle}>Approval Mode</Text>
        <BodyText style={styles.sectionDescription}>
          Choose how orders from your branch are processed
        </BodyText>

        <View style={styles.modeRow}>
          <Pressable
            style={({ pressed }) => [
              styles.modeButton,
              settings?.approval_mode === "manual" ? styles.modeButtonActive : null,
              pressed ? styles.buttonPressed : null
            ]}
            onPress={() => handleApprovalModeChange("manual")}
          >
            <Text style={[styles.modeButtonText, settings?.approval_mode === "manual" ? styles.modeButtonTextActive : null]}>
              Manual
            </Text>
            <Text style={styles.modeButtonDesc}>Approve each order individually</Text>
          </Pressable>

          <Pressable
            style={({ pressed }) => [
              styles.modeButton,
              settings?.approval_mode === "auto" ? styles.modeButtonActive : null,
              pressed ? styles.buttonPressed : null
            ]}
            onPress={() => handleApprovalModeChange("auto")}
          >
            <Text style={[styles.modeButtonText, settings?.approval_mode === "auto" ? styles.modeButtonTextActive : null]}>
              Auto
            </Text>
            <Text style={styles.modeButtonDesc}>Auto-approve for 24h</Text>
          </Pressable>
        </View>

        {settings?.approval_mode === "auto" && timeRemaining && (
          <View style={styles.timerRow}>
            <EditorialPill label={timeRemaining} strong />
          </View>
        )}
      </CardFrame>

      <CardFrame style={styles.sectionCard}>
        <SectionLabel style={styles.sectionEyebrow}>Security</SectionLabel>
        <Text style={styles.sectionTitle}>Change Password</Text>

        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Current Password</Text>
          <TextInput
            style={styles.input}
            value={currentPassword}
            onChangeText={setCurrentPassword}
            placeholder="Enter current password"
            placeholderTextColor={editorialTheme.textSoft}
            secureTextEntry
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>New Password</Text>
          <TextInput
            style={styles.input}
            value={newPassword}
            onChangeText={setNewPassword}
            placeholder="Enter new password"
            placeholderTextColor={editorialTheme.textSoft}
            secureTextEntry
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Confirm Password</Text>
          <TextInput
            style={styles.input}
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            placeholder="Confirm new password"
            placeholderTextColor={editorialTheme.textSoft}
            secureTextEntry
          />
        </View>

        <EditorialButton
          label={changePassword.isPending ? "Changing..." : "Change Password"}
          onPress={() => changePassword.mutate()}
          disabled={!currentPassword || !newPassword || !confirmPassword || changePassword.isPending}
          style={styles.passwordButton}
        />
      </CardFrame>

      <EditorialButton
        label="Sign Out"
        inverse
        onPress={async () => {
          const refreshToken = useAuthStore.getState().refreshToken;
          if (refreshToken) {
            try {
              await api.logout(refreshToken);
            } catch {
              // Clear locally even if the API is unavailable.
            }
          }
          await useAuthStore.getState().clearSession();
          router.replace("/login");
        }}
        style={styles.signOutButton}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  screenContent: {
    paddingBottom: 100
  },
  backButton: {
    marginBottom: 16
  },
  backButtonText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 14,
    color: editorialTheme.textMuted
  },
  pageTitle: {
    fontSize: 32,
    lineHeight: 38
  },
  pageCopy: {
    marginTop: 10,
    marginBottom: 24
  },
  sectionCard: {
    marginBottom: 16
  },
  sectionEyebrow: {
    marginBottom: 4
  },
  sectionTitle: {
    fontFamily: editorialSerif,
    fontSize: 22,
    lineHeight: 28,
    textTransform: "uppercase",
    color: editorialTheme.text,
    marginBottom: 12
  },
  sectionDescription: {
    marginBottom: 16,
    fontSize: 14
  },
  infoRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: editorialTheme.border
  },
  infoLabel: {
    fontSize: 14,
    color: editorialTheme.textMuted
  },
  infoValue: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 14,
    color: editorialTheme.text
  },
  languageRow: {
    flexDirection: "row",
    gap: 10
  },
  languageButton: {
    flex: 1,
    minHeight: 44,
    borderRadius: 2,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surface,
    alignItems: "center",
    justifyContent: "center"
  },
  languageButtonSelected: {
    backgroundColor: editorialTheme.surfaceStrong,
    borderColor: editorialTheme.borderStrong
  },
  buttonPressed: {
    opacity: 0.7
  },
  languageButtonText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    letterSpacing: 0.8,
    textTransform: "uppercase",
    color: editorialTheme.textMuted
  },
  languageButtonTextSelected: {
    color: editorialTheme.text
  },
  modeRow: {
    flexDirection: "row",
    gap: 10
  },
  modeButton: {
    flex: 1,
    padding: 16,
    borderRadius: 2,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surface
  },
  modeButtonActive: {
    backgroundColor: editorialTheme.text,
    borderColor: editorialTheme.text
  },
  modeButtonText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 14,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: editorialTheme.text,
    marginBottom: 4
  },
  modeButtonTextActive: {
    color: editorialTheme.surface
  },
  modeButtonDesc: {
    fontSize: 12,
    color: editorialTheme.textSoft
  },
  timerRow: {
    marginTop: 16,
    alignItems: "center"
  },
  inputGroup: {
    marginBottom: 14
  },
  inputLabel: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.textMuted,
    marginBottom: 8
  },
  input: {
    height: 48,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    borderRadius: 2,
    paddingHorizontal: 14,
    fontSize: 16,
    color: editorialTheme.text,
    backgroundColor: editorialTheme.surface
  },
  passwordButton: {
    marginTop: 8
  },
  signOutButton: {
    marginTop: 8
  }
});
