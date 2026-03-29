import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Pressable, StyleSheet, Text, View } from "react-native";

import {
  BodyText,
  CardFrame,
  EditorialPill,
  MetricTile,
  Screen,
  SectionLabel,
  SkeletonBlock,
  editorialSerif,
  editorialTheme
} from "@/components/ui";
import { api } from "@/services/api";
import { useAuthStore } from "@/state/auth-store";

type OrderStatus = "pending" | "in_progress" | "ready";

function getDisplayStatus(status: string): OrderStatus {
  if (status === "created" || status === "accepted") return "pending";
  if (status === "in_production") return "in_progress";
  if (status === "ready") return "ready";
  return "pending";
}

function formatTime(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours > 0) {
    return `${hours}h ${mins}m`;
  }
  return `${mins}m`;
}

export default function ProductionQueue() {
  const queryClient = useQueryClient();
  const { accessToken, user } = useAuthStore();
  const queryEnabled = Boolean(accessToken) && user?.role === "production";

  const { data: orders, isLoading } = useQuery({
    queryKey: ["production-queue"],
    queryFn: api.productionQueue,
    enabled: queryEnabled
  });

  const { data: shiftStatus } = useQuery({
    queryKey: ["production-shift-status"],
    queryFn: api.productionShiftStatus,
    enabled: queryEnabled
  });

  const updateOrderStatus = useMutation({
    mutationFn: ({ orderId, status }: { orderId: number; status: string }) =>
      api.productionUpdateOrderStatus(orderId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["production-queue"] });
      queryClient.invalidateQueries({ queryKey: ["production-shift-status"] });
    }
  });

  const orderList = orders ?? [];
  const pendingOrders = orderList.filter((o) => getDisplayStatus(o.status) === "pending");
  const inProgressOrders = orderList.filter((o) => getDisplayStatus(o.status) === "in_progress");
  const readyOrders = orderList.filter((o) => getDisplayStatus(o.status) === "ready");

  const isShiftOpen = shiftStatus?.is_open ?? false;
  const shiftMinutes = shiftStatus?.shift_duration_minutes ?? 0;

  const handleStatusChange = (orderId: number, currentStatus: string, newStatus: string) => {
    updateOrderStatus.mutate({ orderId, status: newStatus });
  };

  if (isLoading) {
    return (
      <Screen contentContainerStyle={styles.screenContent}>
        <SkeletonBlock height={16} style={{ width: 100 }} />
        <SkeletonBlock height={80} />
      </Screen>
    );
  }

  return (
    <Screen contentContainerStyle={styles.screenContent}>
      <SectionLabel>Production</SectionLabel>

      <View style={[styles.shiftBanner, isShiftOpen ? styles.shiftOpen : styles.shiftClosed]}>
        <View style={styles.shiftInfo}>
          <Text style={styles.shiftLabel}>{isShiftOpen ? "SHIFT OPEN" : "SHIFT CLOSED"}</Text>
          {isShiftOpen && (
            <Text style={styles.shiftTime}>{formatTime(shiftMinutes)}</Text>
          )}
        </View>
        <View style={styles.shiftStats}>
          <View style={styles.shiftStat}>
            <Text style={styles.shiftStatValue}>{pendingOrders.length}</Text>
            <Text style={styles.shiftStatLabel}>Pending</Text>
          </View>
          <View style={styles.shiftStat}>
            <Text style={styles.shiftStatValue}>{inProgressOrders.length}</Text>
            <Text style={styles.shiftStatLabel}>Working</Text>
          </View>
          <View style={styles.shiftStat}>
            <Text style={styles.shiftStatValue}>{readyOrders.length}</Text>
            <Text style={styles.shiftStatLabel}>Ready</Text>
          </View>
        </View>
      </View>

      {orderList.length === 0 ? (
        <CardFrame style={styles.emptyCard}>
          <Text style={styles.emptyText}>No orders in queue</Text>
        </CardFrame>
      ) : (
        orderList.map((order) => {
          const displayStatus = getDisplayStatus(order.status);
          const isEscalated = order.status === "escalated";

          return (
            <CardFrame key={order.id} style={[styles.orderCard, isEscalated && styles.orderEscalated]}>
              <View style={styles.orderHeader}>
                <View>
                  <Text style={styles.orderId}>Order #{order.id}</Text>
                  <Text style={styles.orderBranch}>Branch #{order.branch_id}</Text>
                </View>
                <EditorialPill
                  label={displayStatus.replace(/_/g, " ")}
                  strong={isEscalated || displayStatus === "pending"}
                  style={isEscalated ? styles.pillEscalated : undefined}
                />
              </View>

              <View style={styles.orderDetails}>
                <Text style={styles.orderQty}>Qty: {order.quantity}</Text>
                <Text style={styles.orderStage}>{order.current_deadline_stage || "—"}</Text>
              </View>

              <View style={styles.actionButtons}>
                {displayStatus === "pending" && (
                  <Pressable
                    style={({ pressed }) => [styles.actionButton, styles.startButton, pressed && styles.buttonPressed]}
                    onPress={() => handleStatusChange(order.id, order.status, "in_production")}
                    disabled={updateOrderStatus.isPending}
                  >
                    <Text style={styles.actionButtonText}>START</Text>
                  </Pressable>
                )}
                {displayStatus === "in_progress" && (
                  <Pressable
                    style={({ pressed }) => [styles.actionButton, styles.readyButton, pressed && styles.buttonPressed]}
                    onPress={() => handleStatusChange(order.id, order.status, "ready")}
                    disabled={updateOrderStatus.isPending}
                  >
                    <Text style={[styles.actionButtonText, styles.readyButtonText]}>READY</Text>
                  </Pressable>
                )}
                {displayStatus === "ready" && (
                  <View style={styles.completedBadge}>
                    <Text style={styles.completedText}>READY - DONE</Text>
                  </View>
                )}
              </View>
            </CardFrame>
          );
        })
      )}
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
  shiftBanner: {
    padding: 16,
    borderRadius: 2,
    marginBottom: 16
  },
  shiftOpen: {
    backgroundColor: "#E8F5E9",
    borderWidth: 1,
    borderColor: "#4CAF50"
  },
  shiftClosed: {
    backgroundColor: "#FFEBEE",
    borderWidth: 1,
    borderColor: "#F44336"
  },
  shiftInfo: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12
  },
  shiftLabel: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 14,
    letterSpacing: 1.5,
    textTransform: "uppercase"
  },
  shiftTime: {
    fontFamily: editorialSerif,
    fontSize: 20,
    color: "#2E7D32"
  },
  shiftStats: {
    flexDirection: "row",
    gap: 16
  },
  shiftStat: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 8,
    backgroundColor: "rgba(255,255,255,0.7)",
    borderRadius: 2
  },
  shiftStatValue: {
    fontFamily: editorialSerif,
    fontSize: 24,
    color: "#000"
  },
  shiftStatLabel: {
    fontSize: 10,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: editorialTheme.textMuted,
    marginTop: 2
  },
  emptyCard: {
    alignItems: "center",
    paddingVertical: 40
  },
  emptyText: {
    fontSize: 16,
    color: editorialTheme.textMuted
  },
  orderCard: {
    marginBottom: 12,
    padding: 14
  },
  orderEscalated: {
    borderWidth: 2,
    borderColor: "#F44336",
    backgroundColor: "#FFF5F5"
  },
  orderHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 10
  },
  orderId: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 16,
    letterSpacing: 1,
    textTransform: "uppercase"
  },
  orderBranch: {
    fontSize: 12,
    color: editorialTheme.textMuted,
    marginTop: 2
  },
  pillEscalated: {
    backgroundColor: "#F44336",
    borderColor: "#F44336"
  },
  orderDetails: {
    marginBottom: 12
  },
  orderQty: {
    fontSize: 14,
    color: editorialTheme.text
  },
  orderStage: {
    fontSize: 12,
    color: editorialTheme.textMuted,
    marginTop: 4
  },
  actionButtons: {
    flexDirection: "row",
    gap: 10
  },
  actionButton: {
    flex: 1,
    minHeight: 48,
    borderRadius: 2,
    alignItems: "center",
    justifyContent: "center"
  },
  startButton: {
    backgroundColor: "#2196F3"
  },
  readyButton: {
    backgroundColor: "#FF9800"
  },
  doneButton: {
    backgroundColor: "#4CAF50"
  },
  buttonPressed: {
    opacity: 0.7
  },
  actionButtonText: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 13,
    letterSpacing: 1.5,
    textTransform: "uppercase",
    color: "#FFF"
  },
  readyButtonText: {
    color: "#FFF"
  },
  completedBadge: {
    flex: 1,
    minHeight: 48,
    borderRadius: 2,
    backgroundColor: editorialTheme.surfaceMuted,
    alignItems: "center",
    justifyContent: "center"
  },
  completedText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    letterSpacing: 1.5,
    textTransform: "uppercase",
    color: editorialTheme.textSoft
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
  }
});
