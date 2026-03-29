import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pressable, StyleSheet, Text, View } from "react-native";

import {
  BodyText,
  CardFrame,
  EditorialButton,
  EditorialPill,
  EditorialTitle,
  MetricTile,
  Screen,
  SectionLabel,
  SkeletonBlock,
  editorialSerif,
  editorialTheme
} from "@/components/ui";
import { api } from "@/services/api";
import { useAuthStore } from "@/state/auth-store";
import type { Order } from "@/services/api/types";

type FilterType = "all" | "pending" | "approved" | "rejected";

function getStatusFilter(status: string): FilterType {
  if (status === "created" || status === "pending") return "pending";
  if (status === "accepted" || status === "approved") return "approved";
  if (status === "rejected" || status === "cancelled") return "rejected";
  return "all";
}

function formatCurrency(amount?: number | null, currency: string = "KZT"): string {
  if (!amount) return "0 ₸";
  return `${(amount / 100).toLocaleString()} ${currency}`;
}

export default function FranchiseDashboard() {
  const queryClient = useQueryClient();
  const { hydrated, accessToken, user } = useAuthStore();
  const queryEnabled = Boolean(accessToken) && user?.role === "franchisee";

  const [activeFilter, setActiveFilter] = React.useState<FilterType>("all");

  const { data: orders, isLoading } = useQuery({
    queryKey: ["franchise-orders"],
    queryFn: api.franchiseOrders,
    enabled: queryEnabled
  });

  const approveOrder = useMutation({
    mutationFn: (orderId: number) => api.franchiseApproveOrder(orderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["franchise-orders"] });
    }
  });

  const rejectOrder = useMutation({
    mutationFn: ({ orderId, reason }: { orderId: number; reason: string }) =>
      api.franchiseRejectOrder(orderId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["franchise-orders"] });
    }
  });

  if (!hydrated) {
    return null;
  }

  if (!accessToken) {
    return null;
  }

  const orderList = orders ?? [];
  const filteredOrders =
    activeFilter === "all"
      ? orderList
      : orderList.filter((order) => getStatusFilter(order.status) === activeFilter);

  const pendingCount = orderList.filter((o) => getStatusFilter(o.status) === "pending").length;
  const approvedCount = orderList.filter((o) => getStatusFilter(o.status) === "approved").length;
  const rejectedCount = orderList.filter((o) => getStatusFilter(o.status) === "rejected").length;
  const totalRevenue = orderList.reduce((sum, o) => sum + (o.line_total?.amount_minor ?? 0), 0);

  const filters: { key: FilterType; label: string }[] = [
    { key: "all", label: "All" },
    { key: "pending", label: "Pending" },
    { key: "approved", label: "Approved" },
    { key: "rejected", label: "Rejected" }
  ];

  if (isLoading) {
    return (
      <Screen>
        <SkeletonBlock height={16} style={{ width: 86 }} />
        <SkeletonBlock height={120} />
      </Screen>
    );
  }

  return (
    <Screen contentContainerStyle={styles.screenContent}>
      <SectionLabel>Franchise</SectionLabel>
      <EditorialTitle style={styles.pageTitle}>Dashboard</EditorialTitle>
      <BodyText style={styles.pageCopy}>
        Manage your branch orders and track performance
      </BodyText>

      <CardFrame style={styles.heroCard}>
        <View style={styles.heroTop}>
          <Text style={styles.branchTitle}>Branch #{user?.branch_id ?? "—"}</Text>
          <EditorialPill label={pendingCount > 0 ? `${pendingCount} Pending` : "All Clear"} strong={pendingCount > 0} />
        </View>
        <BodyText>{user?.full_name || "Franchise Manager"}</BodyText>
        <BodyText style={styles.emailText}>{user?.email || "franchise@example.com"}</BodyText>
      </CardFrame>

      <CardFrame style={styles.metricsCard}>
        <View style={styles.metricsRow}>
          <MetricTile label="Total Orders" value={String(orderList.length)} />
          <MetricTile label="Pending" value={String(pendingCount)} />
          <MetricTile label="Approved" value={String(approvedCount)} />
        </View>
        <View style={styles.revenueRow}>
          <MetricTile label="Total Revenue" value={formatCurrency(totalRevenue)} style={styles.revenueTile} />
        </View>
      </CardFrame>

      <View style={styles.filterRow}>
        {filters.map((filter) => {
          const isActive = activeFilter === filter.key;
          return (
            <Pressable
              key={filter.key}
              style={({ pressed }) => [
                styles.filterPill,
                isActive ? styles.filterPillActive : null,
                pressed ? styles.filterPillPressed : null
              ]}
              onPress={() => setActiveFilter(filter.key)}
            >
              <Text style={[styles.filterPillText, isActive ? styles.filterPillTextActive : null]}>
                {filter.label}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {filteredOrders.length === 0 ? (
        <CardFrame style={styles.emptyCard}>
          <BodyText style={styles.emptyText}>
            {activeFilter === "all"
              ? "No orders yet"
              : `No ${activeFilter} orders`}
          </BodyText>
        </CardFrame>
      ) : (
        filteredOrders.map((order) => (
          <CardFrame key={order.id} style={styles.orderCard}>
            <View style={styles.orderHeader}>
              <Text style={styles.orderHeading}>Order #{order.id}</Text>
              <EditorialPill
                label={order.status.replace(/_/g, " ")}
                strong={getStatusFilter(order.status) === "pending"}
              />
            </View>
            <BodyText>
              Qty: {order.quantity} • {order.size_label || "No size"} • Branch #{order.branch_id}
            </BodyText>
            <BodyText style={styles.orderPrice}>
              {order.line_total?.formatted || formatCurrency(order.line_total?.amount_minor)}
            </BodyText>
            <BodyText style={styles.noteText}>
              {order.current_deadline_stage || "Processing..."}
            </BodyText>

            {getStatusFilter(order.status) === "pending" && (
              <View style={styles.actionRow}>
                <Pressable
                  style={({ pressed }) => [
                    styles.approveButton,
                    pressed && styles.buttonPressed
                  ]}
                  onPress={() => approveOrder.mutate(order.id)}
                  disabled={approveOrder.isPending}
                >
                  <Text style={styles.approveButtonText}>
                    {approveOrder.isPending ? "Approving..." : "Approve"}
                  </Text>
                </Pressable>
                <Pressable
                  style={({ pressed }) => [
                    styles.rejectButton,
                    pressed && styles.buttonPressed
                  ]}
                  onPress={() => rejectOrder.mutate({ orderId: order.id, reason: "Rejected by franchise" })}
                  disabled={rejectOrder.isPending}
                >
                  <Text style={styles.rejectButtonText}>
                    {rejectOrder.isPending ? "Rejecting..." : "Reject"}
                  </Text>
                </Pressable>
              </View>
            )}
          </CardFrame>
        ))
      )}
    </Screen>
  );
}

import React from "react";

const styles = StyleSheet.create({
  screenContent: {
    paddingBottom: 100
  },
  pageTitle: {
    fontSize: 32,
    lineHeight: 38
  },
  pageCopy: {
    marginTop: 10,
    marginBottom: 16
  },
  navRow: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 16
  },
  navButton: {
    flex: 1,
    minHeight: 48,
    borderRadius: 2,
    borderWidth: 1,
    borderColor: editorialTheme.borderStrong,
    backgroundColor: editorialTheme.surface,
    alignItems: "center",
    justifyContent: "center"
  },
  navButtonPressed: {
    opacity: 0.7
  },
  navButtonText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 12,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  heroCard: {
    marginBottom: 16
  },
  heroTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 10,
    marginBottom: 10
  },
  branchTitle: {
    fontFamily: editorialSerif,
    fontSize: 26,
    lineHeight: 30,
    textTransform: "uppercase",
    color: "#000000"
  },
  emailText: {
    marginTop: 4,
    fontSize: 14
  },
  metricsCard: {
    marginBottom: 16
  },
  metricsRow: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 10
  },
  revenueRow: {
    marginTop: 0
  },
  revenueTile: {
    flex: 1
  },
  filterRow: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 16
  },
  filterPill: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 2,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surface
  },
  filterPillActive: {
    backgroundColor: editorialTheme.text,
    borderColor: editorialTheme.text
  },
  filterPillPressed: {
    opacity: 0.7
  },
  filterPillText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: editorialTheme.textMuted
  },
  filterPillTextActive: {
    color: editorialTheme.surface
  },
  emptyCard: {
    alignItems: "center",
    paddingVertical: 40
  },
  emptyText: {
    textAlign: "center"
  },
  orderCard: {
    marginBottom: 14
  },
  orderHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8
  },
  orderHeading: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 1.8,
    textTransform: "uppercase",
    color: "#000000"
  },
  orderPrice: {
    marginTop: 6,
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 16,
    color: editorialTheme.text
  },
  noteText: {
    marginTop: 10,
    fontSize: 14
  },
  actionRow: {
    flexDirection: "row",
    gap: 10,
    marginTop: 14,
    paddingTop: 14,
    borderTopWidth: 1,
    borderTopColor: editorialTheme.border
  },
  approveButton: {
    flex: 1,
    minHeight: 42,
    borderRadius: 2,
    backgroundColor: editorialTheme.text,
    alignItems: "center",
    justifyContent: "center"
  },
  rejectButton: {
    flex: 1,
    minHeight: 42,
    borderRadius: 2,
    borderWidth: 1,
    borderColor: editorialTheme.borderStrong,
    backgroundColor: editorialTheme.surface,
    alignItems: "center",
    justifyContent: "center"
  },
  buttonPressed: {
    opacity: 0.7
  },
  approveButtonText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.surface
  },
  rejectButtonText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.textMuted
  }
});
