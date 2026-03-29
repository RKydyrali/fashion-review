import { useState } from "react";
import { router } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Modal, Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import {
  BodyText,
  CardFrame,
  MetricTile,
  Screen,
  SectionLabel,
  editorialSerif,
  editorialTheme
} from "@/components/ui";
import { api } from "@/services/api";
import { useAuthStore } from "@/state/auth-store";

type ShiftType = "morning" | "afternoon";

function getCurrentShiftType(): ShiftType {
  const hour = new Date().getHours();
  if (hour >= 8 && hour < 14) return "morning";
  return "afternoon";
}

function getShiftLabel(type: ShiftType): string {
  return type === "morning" ? "Morning Shift" : "Afternoon Shift";
}

function getShiftTimeRange(type: ShiftType): string {
  return type === "morning" ? "08:00 - 14:00" : "14:00 - 20:00";
}

function formatTime(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours > 0) {
    return `${hours}h ${mins}m`;
  }
  return `${mins}m`;
}

function formatDateTime(isoString?: string | null): string {
  if (!isoString) return "—";
  const date = new Date(isoString);
  return date.toLocaleTimeString("en", { hour: "2-digit", minute: "2-digit" });
}

export default function ProductionShift() {
  const queryClient = useQueryClient();
  const { accessToken, user } = useAuthStore();
  const queryEnabled = Boolean(accessToken) && user?.role === "production";

  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const { data: shiftStatus, isLoading } = useQuery({
    queryKey: ["production-shift-status"],
    queryFn: api.productionShiftStatus,
    enabled: queryEnabled,
    refetchInterval: 30000
  });

  const startShift = useMutation({
    mutationFn: (shiftType: string) => api.productionStartShift(shiftType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["production-shift-status"] });
    },
    onError: () => {
      Alert.alert("Error", "Failed to start shift");
    }
  });

  const endShift = useMutation({
    mutationFn: api.productionEndShift,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["production-shift-status"] });
      showShiftReport(data);
    },
    onError: () => {
      Alert.alert("Error", "Failed to end shift");
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
      setShowPasswordModal(false);
      Alert.alert("Success", "Password changed successfully");
    },
    onError: (error: Error) => {
      Alert.alert("Error", error.message || "Failed to change password");
    }
  });

  const [showReport, setShowReport] = useState(false);
  const [reportData, setReportData] = useState<any>(null);

  const showShiftReport = (data: any) => {
    setReportData(data);
    setShowReport(true);
  };

  const currentShiftType = shiftStatus?.shift_type as ShiftType | undefined;
  const isShiftActive = shiftStatus?.is_open ?? false;

  const handleStartShift = (shiftType: ShiftType) => {
    startShift.mutate(shiftType);
  };

  const handleEndShift = () => {
    endShift.mutate();
  };

  const suggestedShift = getCurrentShiftType();

  return (
    <Screen contentContainerStyle={styles.screenContent}>
      <View style={styles.header}>
        <SectionLabel>Production</SectionLabel>
        <Pressable
          style={({ pressed }) => [styles.passwordButton, pressed && styles.buttonPressed]}
          onPress={() => setShowPasswordModal(true)}
        >
          <Text style={styles.passwordButtonText}>Password</Text>
        </Pressable>
      </View>

      <CardFrame style={styles.mainCard}>
        <Text style={styles.mainTitle}>Select Your Shift</Text>

        {!isShiftActive ? (
          <>
            <Text style={styles.subtitle}>Choose your working hours:</Text>

            <Pressable
              style={({ pressed }) => [
                styles.shiftOption,
                suggestedShift === "morning" ? styles.shiftOptionSuggested : null,
                pressed && styles.buttonPressed
              ]}
              onPress={() => handleStartShift("morning")}
              disabled={startShift.isPending}
            >
              <View style={styles.shiftOptionContent}>
                <Text style={styles.shiftOptionTitle}>Morning</Text>
                <Text style={styles.shiftOptionTime}>08:00 - 14:00</Text>
              </View>
              {suggestedShift === "morning" && (
                <Text style={styles.suggestedBadge}>Suggested</Text>
              )}
            </Pressable>

            <Pressable
              style={({ pressed }) => [
                styles.shiftOption,
                suggestedShift === "afternoon" ? styles.shiftOptionSuggested : null,
                pressed && styles.buttonPressed
              ]}
              onPress={() => handleStartShift("afternoon")}
              disabled={startShift.isPending}
            >
              <View style={styles.shiftOptionContent}>
                <Text style={styles.shiftOptionTitle}>Afternoon</Text>
                <Text style={styles.shiftOptionTime}>14:00 - 20:00</Text>
              </View>
              {suggestedShift === "afternoon" && (
                <Text style={styles.suggestedBadge}>Suggested</Text>
              )}
            </Pressable>
          </>
        ) : (
          <>
            <View style={[styles.shiftStatus, styles.shiftActive]}>
              <View style={styles.shiftIndicator}>
                <View style={[styles.indicatorDot, styles.dotGreen]} />
                <Text style={styles.shiftStatusText}>
                  {getShiftLabel(currentShiftType!)} Active
                </Text>
              </View>
              {shiftStatus?.shift_started_at && (
                <Text style={styles.shiftStarted}>
                  Started at {formatDateTime(shiftStatus.shift_started_at)}
                </Text>
              )}
            </View>

            <View style={styles.timerSection}>
              <Text style={styles.timerLabel}>Duration</Text>
              <Text style={styles.timerValue}>{formatTime(shiftStatus?.shift_duration_minutes ?? 0)}</Text>
            </View>

            <View style={styles.statsGrid}>
              <MetricTile
                label="Started"
                value={String(shiftStatus?.orders_started_today ?? 0)}
              />
              <MetricTile
                label="Completed"
                value={String(shiftStatus?.orders_completed_today ?? 0)}
              />
              <MetricTile
                label="In Progress"
                value={String(shiftStatus?.orders_in_progress ?? 0)}
              />
            </View>

            <Pressable
              style={({ pressed }) => [
                styles.mainButton,
                styles.endButton,
                pressed && styles.buttonPressed
              ]}
              onPress={handleEndShift}
              disabled={endShift.isPending}
            >
              <Text style={styles.mainButtonText}>
                {endShift.isPending ? "Ending..." : "End Shift"}
              </Text>
            </Pressable>
          </>
        )}
      </CardFrame>

      <Modal visible={showPasswordModal} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Change Password</Text>

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

            <View style={styles.modalButtons}>
              <Pressable
                style={({ pressed }) => [styles.modalButton, styles.cancelButton, pressed && styles.buttonPressed]}
                onPress={() => setShowPasswordModal(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </Pressable>
              <Pressable
                style={({ pressed }) => [styles.modalButton, styles.submitButton, pressed && styles.buttonPressed]}
                onPress={() => changePassword.mutate()}
                disabled={changePassword.isPending}
              >
                <Text style={styles.submitButtonText}>
                  {changePassword.isPending ? "Changing..." : "Change"}
                </Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>

      <Modal visible={showReport} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Shift Report</Text>

            {reportData && (
              <View style={styles.reportContent}>
                <View style={styles.reportRow}>
                  <Text style={styles.reportLabel}>Date</Text>
                  <Text style={styles.reportValue}>{reportData.shift_date}</Text>
                </View>
                <View style={styles.reportRow}>
                  <Text style={styles.reportLabel}>Shift</Text>
                  <Text style={styles.reportValue}>{getShiftLabel(reportData.shift_type)}</Text>
                </View>
                <View style={styles.reportRow}>
                  <Text style={styles.reportLabel}>Started</Text>
                  <Text style={styles.reportValue}>{formatDateTime(reportData.shift_started_at)}</Text>
                </View>
                <View style={styles.reportRow}>
                  <Text style={styles.reportLabel}>Ended</Text>
                  <Text style={styles.reportValue}>{formatDateTime(reportData.shift_ended_at)}</Text>
                </View>
                <View style={styles.reportRow}>
                  <Text style={styles.reportLabel}>Duration</Text>
                  <Text style={styles.reportValue}>{formatTime(reportData.duration_minutes)}</Text>
                </View>
                <View style={styles.reportDivider} />
                <View style={styles.reportRow}>
                  <Text style={styles.reportLabel}>Orders Started</Text>
                  <Text style={styles.reportValue}>{reportData.orders_started}</Text>
                </View>
                <View style={styles.reportRow}>
                  <Text style={styles.reportLabel}>Orders Completed</Text>
                  <Text style={styles.reportValue}>{reportData.orders_completed}</Text>
                </View>
              </View>
            )}

            <Pressable
              style={({ pressed }) => [styles.reportButton, pressed && styles.buttonPressed]}
              onPress={() => setShowReport(false)}
            >
              <Text style={styles.reportButtonText}>Close</Text>
            </Pressable>
          </View>
        </View>
      </Modal>

      <Pressable
        style={({ pressed }) => [styles.logoutButton, pressed && styles.buttonPressed]}
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
      >
        <Text style={styles.logoutButtonText}>Sign Out</Text>
      </Pressable>
    </Screen>
  );
}

const styles = StyleSheet.create({
  screenContent: {
    paddingBottom: 100
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16
  },
  passwordButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 2,
    borderWidth: 1,
    borderColor: editorialTheme.border
  },
  passwordButtonText: {
    fontSize: 11,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: editorialTheme.textMuted
  },
  mainCard: {
    marginBottom: 16
  },
  mainTitle: {
    fontFamily: editorialSerif,
    fontSize: 24,
    textTransform: "uppercase",
    marginBottom: 12,
    textAlign: "center"
  },
  subtitle: {
    fontSize: 14,
    color: editorialTheme.textMuted,
    textAlign: "center",
    marginBottom: 20
  },
  shiftOption: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 20,
    borderRadius: 2,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    marginBottom: 12,
    backgroundColor: editorialTheme.surface
  },
  shiftOptionSuggested: {
    borderColor: "#4CAF50",
    backgroundColor: "#F1F8E9"
  },
  shiftOptionContent: {
    flex: 1
  },
  shiftOptionTitle: {
    fontFamily: editorialSerif,
    fontSize: 20,
    textTransform: "uppercase",
    marginBottom: 4
  },
  shiftOptionTime: {
    fontSize: 14,
    color: editorialTheme.textMuted
  },
  suggestedBadge: {
    fontSize: 10,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: "#4CAF50",
    fontWeight: "600"
  },
  shiftStatus: {
    padding: 20,
    borderRadius: 2,
    alignItems: "center",
    marginBottom: 20
  },
  shiftActive: {
    backgroundColor: "#E8F5E9"
  },
  shiftIndicator: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8
  },
  indicatorDot: {
    width: 12,
    height: 12,
    borderRadius: 6
  },
  dotGreen: {
    backgroundColor: "#4CAF50"
  },
  shiftStatusText: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 16,
    letterSpacing: 1.5
  },
  shiftStarted: {
    marginTop: 8,
    fontSize: 14,
    color: editorialTheme.textMuted
  },
  timerSection: {
    alignItems: "center",
    marginBottom: 16
  },
  timerLabel: {
    fontSize: 11,
    letterSpacing: 1.5,
    textTransform: "uppercase",
    color: editorialTheme.textMuted,
    marginBottom: 4
  },
  timerValue: {
    fontFamily: editorialSerif,
    fontSize: 36,
    color: "#000"
  },
  statsGrid: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 20
  },
  mainButton: {
    minHeight: 56,
    borderRadius: 2,
    alignItems: "center",
    justifyContent: "center"
  },
  endButton: {
    backgroundColor: "#F44336"
  },
  buttonPressed: {
    opacity: 0.7
  },
  mainButtonText: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 16,
    letterSpacing: 1.5,
    textTransform: "uppercase",
    color: "#FFF"
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    alignItems: "center",
    padding: 20
  },
  modalContent: {
    width: "100%",
    maxWidth: 360,
    backgroundColor: editorialTheme.surface,
    borderRadius: 2,
    padding: 24
  },
  modalTitle: {
    fontFamily: editorialSerif,
    fontSize: 22,
    textTransform: "uppercase",
    marginBottom: 20,
    textAlign: "center"
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
  modalButtons: {
    flexDirection: "row",
    gap: 12,
    marginTop: 10
  },
  modalButton: {
    flex: 1,
    minHeight: 48,
    borderRadius: 2,
    alignItems: "center",
    justifyContent: "center"
  },
  cancelButton: {
    borderWidth: 1,
    borderColor: editorialTheme.border
  },
  cancelButtonText: {
    fontSize: 13,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: editorialTheme.textMuted
  },
  submitButton: {
    backgroundColor: editorialTheme.text
  },
  submitButtonText: {
    fontSize: 13,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: editorialTheme.surface
  },
  reportContent: {
    marginBottom: 20
  },
  reportRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: editorialTheme.border
  },
  reportLabel: {
    fontSize: 14,
    color: editorialTheme.textMuted
  },
  reportValue: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 14,
    color: editorialTheme.text
  },
  reportDivider: {
    height: 1,
    backgroundColor: editorialTheme.border,
    marginVertical: 12
  },
  reportButton: {
    minHeight: 48,
    borderRadius: 2,
    backgroundColor: editorialTheme.text,
    alignItems: "center",
    justifyContent: "center"
  },
  reportButtonText: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 13,
    letterSpacing: 1.5,
    textTransform: "uppercase",
    color: editorialTheme.surface
  },
  logoutButton: {
    marginTop: 24,
    minHeight: 48,
    borderRadius: 2,
    borderWidth: 1,
    borderColor: editorialTheme.borderStrong,
    backgroundColor: editorialTheme.surface,
    alignItems: "center",
    justifyContent: "center"
  },
  logoutButtonText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 13,
    letterSpacing: 1.5,
    textTransform: "uppercase",
    color: editorialTheme.textMuted
  }
});
