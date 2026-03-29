import { router } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Pressable, StyleSheet, Text, View, Image } from "react-native";

import { useI18n } from "@/i18n";
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
  SoftPanel,
  editorialSerif,
  editorialTheme
} from "@/components/ui";
import { api } from "@/services/api";
import type { Order, PreorderBatch } from "@/services/api/types";
import { useAuthStore } from "@/state/auth-store";

function formatDate(value: string | null | undefined, localeTag: string, nowLabel: string) {
  if (!value) {
    return nowLabel;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleDateString(localeTag, { month: "short", day: "numeric" });
}

function humanizeStatus(status: string) {
  return status.replace(/_/g, " ");
}

function toneLabel(status: string, readyLabel: string, inMotionLabel: string) {
  return /complete|delivered|ready/.test(status.toLowerCase()) ? readyLabel : inMotionLabel;
}

function latestEvent(order: Order) {
  return order.events[order.events.length - 1];
}

function BatchCard({ batch, t, localeTag }: { batch: PreorderBatch; t: ReturnType<typeof useI18n>["t"]; localeTag: string }) {
  const isReady = batch.status === "ready";
  
  return (
    <CardFrame style={styles.batchCard}>
      <View style={styles.cardTopRow}>
        <SectionLabel style={styles.batchEyebrow}>{t("orders.batchHeading", "Batch #{id}", { id: batch.id })}</SectionLabel>
        <EditorialPill label={toneLabel(batch.status, t("orders.ready", "Ready"), t("orders.inMotion", "In motion"))} strong />
      </View>
      <Text style={styles.batchTitle}>{batch.total_price.formatted}</Text>
      <BodyText style={styles.batchText}>
        {t("orders.looksHeaded", "{count} looks headed to Karaganda.", {
          count: batch.item_count
        })}
      </BodyText>
      <View style={styles.batchMetaRow}>
        <Text style={styles.metaLine}>{t("orders.created", "Created {date}", { date: formatDate(batch.created_at, localeTag, t("common.now", "Now")) })}</Text>
        <Text style={styles.metaLine}>{humanizeStatus(batch.status)}</Text>
      </View>
      {isReady && (
        <Pressable style={styles.pickupButton}>
          <Text style={styles.pickupButtonText}>{t("orders.getOrder", "Get My Order")}</Text>
        </Pressable>
      )}
    </CardFrame>
  );
}

function OrderCard({ order, t, onPickup }: { order: Order; t: ReturnType<typeof useI18n>["t"]; onPickup: (orderId: number) => void }) {
  const event = latestEvent(order);
  const isReady = order.status === "ready";

  return (
    <CardFrame style={styles.orderCard}>
      <View style={styles.cardTopRow}>
        <SectionLabel style={styles.batchEyebrow}>{t("orders.orderHeading", "Order #{id}", { id: order.id })}</SectionLabel>
        <EditorialPill label={toneLabel(order.status, t("orders.ready", "Ready"), t("orders.inMotion", "In motion"))} />
      </View>
      {order.product?.hero_image_url && (
        <Image source={{ uri: order.product.hero_image_url }} style={styles.productImage} />
      )}
      <Text style={styles.orderTitle}>{order.line_total?.formatted || t("orders.awaitingPricing", "Awaiting pricing")}</Text>
      <BodyText style={styles.orderText}>
        {order.product?.name && `${order.product.name} / `}
        {t("common.size", "Size")} {order.size_label || t("orders.pending", "Pending")} / {t("common.quantity", "Quantity")} {order.quantity} / {humanizeStatus(order.status)}
      </BodyText>
      {isReady && (
        <Pressable style={styles.pickupButton} onPress={() => onPickup(order.id)}>
          <Text style={styles.pickupButtonText}>{t("orders.getOrder", "Get My Order")}</Text>
        </Pressable>
      )}
      <View style={styles.timelineBlock}>
        <Text style={styles.timelineLabel}>{t("orders.currentStage", "Current Stage")}</Text>
        <Text style={styles.timelineText}>{order.current_deadline_stage || t("orders.preparingTimeline", "Preparing production timeline.")}</Text>
      </View>
      {event ? (
        <View style={styles.timelineBlock}>
          <Text style={styles.timelineLabel}>{t("orders.latestNote", "Latest Note")}</Text>
          <Text style={styles.timelineText}>{event.note || t("orders.historyRegistered", "{status} registered in the order history.", { status: humanizeStatus(event.to_status) })}</Text>
        </View>
      ) : null}
    </CardFrame>
  );
}

export default function OrdersScreen() {
  const { t, localeTag } = useI18n();
  const accessToken = useAuthStore((state) => state.accessToken);
  const queryEnabled = Boolean(accessToken);
  const queryClient = useQueryClient();
  const { data: orders, isLoading } = useQuery({ queryKey: ["orders"], queryFn: api.orders, enabled: queryEnabled });
  const { data: preorders } = useQuery({ queryKey: ["preorders"], queryFn: api.preorders, enabled: queryEnabled });

  const pickupOrder = useMutation({
    mutationFn: (orderId: number) => api.pickupOrder(orderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["preorders"] });
    }
  });

  if (isLoading) {
    return (
      <Screen>
        <SkeletonBlock height={14} style={styles.loadingLabel} />
        <SkeletonBlock height={90} />
        <SkeletonBlock height={220} />
        <SkeletonBlock height={220} />
      </Screen>
    );
  }

  const preorderList = preorders ?? [];
  const orderList = orders ?? [];

  const activeOrders = orderList.filter((o) => o.status !== "ready" && o.status !== "cancelled" && o.status !== "picked_up");
  const completedOrders = orderList.filter((o) => o.status === "ready" || o.status === "cancelled" || o.status === "picked_up");

  return (
    <Screen>
      <SectionLabel>{t("orders.section", "Orders")}</SectionLabel>
      <EditorialTitle style={styles.pageTitle}>{t("orders.title", "Track every preorder in one journal.")}</EditorialTitle>
      <BodyText style={styles.pageIntro}>
        {t("orders.intro", "Production status, branch movement, and final delivery notes are all staged here in a calmer, editorial view.")}
      </BodyText>

      <SoftPanel style={styles.summaryPanel}>
        <View style={styles.metricsRow}>
          <MetricTile label={t("orders.batches", "Batches")} value={String(preorderList.length)} />
          <MetricTile label={t("orders.active", "Active")} value={String(activeOrders.length)} />
          <MetricTile label={t("orders.history", "History")} value={String(completedOrders.length)} />
        </View>
      </SoftPanel>

      {preorderList.length ? preorderList.map((batch) => <BatchCard key={batch.id} batch={batch} t={t} localeTag={localeTag} />) : null}

      {activeOrders.length ? (
        activeOrders.map((order) => <OrderCard key={order.id} order={order} t={t} onPickup={(id) => pickupOrder.mutate(id)} />)
      ) : (
        <CardFrame style={styles.emptyCard}>
          <Text style={styles.emptyTitle}>{t("orders.noLiveOrders", "No live orders yet")}</Text>
          <BodyText style={styles.emptyText}>
            {t("orders.noLiveOrdersBody", "Once you submit a preorder, this page will hold its full progress from confirmation to final handoff.")}
          </BodyText>
          <EditorialButton label={t("orders.buildEdit", "Build an Edit")} onPress={() => router.push("/(tabs)/collections")} style={styles.emptyAction} />
        </CardFrame>
      )}

      {completedOrders.length > 0 && (
        <>
          <View style={styles.historySection}>
            <SectionLabel>{t("orders.history", "Order History")}</SectionLabel>
          </View>
          {completedOrders.map((order) => <OrderCard key={order.id} order={order} t={t} onPickup={(id) => pickupOrder.mutate(id)} />)}
        </>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  loadingLabel: {
    width: 86,
    borderRadius: 8
  },
  pageTitle: {
    fontSize: 40,
    lineHeight: 48,
    textTransform: "uppercase"
  },
  pageIntro: {
    marginTop: 10,
    marginBottom: 18
  },
  summaryPanel: {
    marginBottom: 16
  },
  metricsRow: {
    flexDirection: "row",
    gap: 10
  },
  batchCard: {
    marginBottom: 16
  },
  orderCard: {
    marginBottom: 16
  },
  cardTopRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 12,
    marginBottom: 8
  },
  batchEyebrow: {
    marginBottom: 0
  },
  batchTitle: {
    fontFamily: editorialSerif,
    fontSize: 30,
    lineHeight: 36,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  batchText: {
    marginTop: 6
  },
  batchMetaRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 10,
    marginTop: 18
  },
  metaLine: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: editorialTheme.textSoft
  },
  orderTitle: {
    fontFamily: editorialSerif,
    fontSize: 28,
    lineHeight: 34,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  orderText: {
    marginTop: 6
  },
  timelineBlock: {
    marginTop: 16,
    borderTopWidth: 1,
    borderTopColor: editorialTheme.border,
    paddingTop: 16
  },
  timelineLabel: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 1.6,
    textTransform: "uppercase",
    color: editorialTheme.textSoft
  },
  timelineText: {
    marginTop: 8,
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 15,
    lineHeight: 24,
    color: editorialTheme.textMuted
  },
  emptyCard: {
    marginTop: 2
  },
  emptyTitle: {
    fontFamily: editorialSerif,
    fontSize: 30,
    lineHeight: 36,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  emptyText: {
    marginTop: 8
  },
  emptyAction: {
    marginTop: 18
  },
  historySection: {
    marginTop: 32,
    marginBottom: 8,
    borderTopWidth: 1,
    borderTopColor: editorialTheme.border,
    paddingTop: 16
  },
  pickupButton: {
    backgroundColor: "#000",
    padding: 16,
    borderRadius: 2,
    alignItems: "center",
    marginTop: 16
  },
  productImage: {
    width: "100%",
    height: 120,
    borderRadius: 2,
    marginBottom: 12,
    resizeMode: "cover"
  },
  pickupButtonText: {
    color: "#FFF",
    fontSize: 13,
    letterSpacing: 1,
    textTransform: "uppercase",
    fontWeight: "600"
  }
});
