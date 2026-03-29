import * as ImagePicker from "expo-image-picker";
import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import {
  BodyText,
  CardFrame,
  EditorialButton,
  EditorialTitle,
  InlineNotice,
  MetricTile,
  ProductImage,
  QuantityStepper,
  Screen,
  SectionLabel,
  SkeletonBlock,
  SoftPanel,
  editorialSerif,
  editorialTheme
} from "@/components/ui";
import { useI18n } from "@/i18n";
import { api } from "@/services/api";
import type { BagItem } from "@/services/api/types";
import { useAuthStore } from "@/state/auth-store";
import { buildBuilderInventory, toTryOnPortrait, useStyleStore } from "@/state/style-store";

function normalizeDisplayPrice(value: number) {
  if (value > 0 && value < 1000) {
    return value * 100;
  }
  return value;
}

function formatMoney(amountMinor: number, currency: string, localeTag: string) {
  return `${currency} ${new Intl.NumberFormat(localeTag, {
    maximumFractionDigits: 0
  }).format(normalizeDisplayPrice(amountMinor))}`;
}

function SelectionChip({
  label,
  active,
  onPress
}: {
  label: string;
  active?: boolean;
  onPress?: () => void;
}) {
  if (!onPress) {
    return (
      <View style={[styles.selectionChip, active ? styles.selectionChipActive : null]}>
        <Text style={[styles.selectionChipText, active ? styles.selectionChipTextActive : null]}>{label}</Text>
      </View>
    );
  }

  return (
    <Pressable style={({ pressed }) => [styles.selectionChip, active ? styles.selectionChipActive : null, pressed ? styles.pressed : null]} onPress={onPress}>
      <Text style={[styles.selectionChipText, active ? styles.selectionChipTextActive : null]}>{label}</Text>
    </Pressable>
  );
}

export default function BagScreen() {
  const { t, localeTag } = useI18n();
  const queryClient = useQueryClient();
  const accessToken = useAuthStore((state) => state.accessToken);
  const currentUser = useAuthStore((state) => state.user);
  const queryEnabled = Boolean(accessToken);
  const styleHydrated = useStyleStore((state) => state.hydrated);
  const bootstrapStyleStore = useStyleStore((state) => state.bootstrap);
  const startWardrobeSession = useStyleStore((state) => state.startWardrobeSession);
  const [busyBagItemId, setBusyBagItemId] = useState<number | null>(null);
  const [selectedMap, setSelectedMap] = useState<Record<number, boolean>>({});
  const [selectionInitialized, setSelectionInitialized] = useState(false);
  const [isPreparingTryOn, setIsPreparingTryOn] = useState(false);
  const [feedback, setFeedback] = useState<{ title: string; description: string; tone: "success" | "error" } | null>(null);

  useEffect(() => {
    if (!styleHydrated) {
      void bootstrapStyleStore(currentUser?.id ?? null);
    }
  }, [bootstrapStyleStore, currentUser?.id, styleHydrated]);

  const { data, isLoading } = useQuery({ queryKey: ["bag"], queryFn: api.bag, enabled: queryEnabled });
  const { data: favorites } = useQuery({ queryKey: ["favorites"], queryFn: api.favorites, enabled: queryEnabled });

  const items = data?.items ?? [];

  useEffect(() => {
    setSelectedMap((current) => {
      const next: Record<number, boolean> = {};
      for (const item of items) {
        next[item.id] = current[item.id] ?? true;
      }
      return next;
    });

    if (items.length && !selectionInitialized) {
      setSelectionInitialized(true);
    }
    if (!items.length && selectionInitialized) {
      setSelectionInitialized(false);
    }
  }, [items, selectionInitialized]);

  const selectedItems = useMemo(() => items.filter((item) => selectedMap[item.id]), [items, selectedMap]);
  const selectedUnits = selectedItems.reduce((sum, item) => sum + item.quantity, 0);
  const selectedTotalMinor = selectedItems.reduce((sum, item) => sum + item.line_total.amount_minor, 0);
  const selectedCurrency = selectedItems[0]?.line_total.currency ?? data?.grand_total.currency ?? "KZT";
  const builderInventory = useMemo(
    () => buildBuilderInventory({ bagItems: selectedItems, favorites: favorites ?? [] }),
    [favorites, selectedItems]
  );

  const removeItem = useMutation({
    mutationFn: api.deleteBagItem,
    onMutate: (itemId) => {
      setBusyBagItemId(itemId);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["bag"] });
      setFeedback({
        title: t("bag.remove", "Remove"),
        description: "The item has been removed from your bag.",
        tone: "success"
      });
    },
    onError: (error) => {
      setFeedback({
        title: "Bag update failed",
        description: error instanceof Error ? error.message : "We could not remove this item right now.",
        tone: "error"
      });
    },
    onSettled: () => {
      setBusyBagItemId(null);
    }
  });

  const updateItem = useMutation({
    mutationFn: ({ itemId, quantity }: { itemId: number; quantity: number }) => api.updateBagItem(itemId, { quantity }),
    onMutate: ({ itemId }) => {
      setBusyBagItemId(itemId);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["bag"] });
    },
    onError: (error) => {
      setFeedback({
        title: "Quantity update failed",
        description: error instanceof Error ? error.message : "We could not change the quantity right now.",
        tone: "error"
      });
    },
    onSettled: () => {
      setBusyBagItemId(null);
    }
  });

  const submitSelected = useMutation({
    mutationFn: (bagItemIds: number[]) =>
      api.submitSelectedPreorder({
        bag_item_ids: bagItemIds,
        delivery_city: "Karaganda"
      }),
    onSuccess: async (batch) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["bag"] }),
        queryClient.invalidateQueries({ queryKey: ["orders"] }),
        queryClient.invalidateQueries({ queryKey: ["preorders"] })
      ]);
      setFeedback({
        title: "Order Confirmed",
        description: `Your order is being prepared for pickup in Karaganda.`,
        tone: "success"
      });
    },
    onError: (error) => {
      setFeedback({
        title: "Checkout failed",
        description: error instanceof Error ? error.message : "We could not process your order right now.",
        tone: "error"
      });
    }
  });

  function toggleSelected(itemId: number) {
    setSelectedMap((current) => ({
      ...current,
      [itemId]: !current[itemId]
    }));
  }

  async function handleTryOn() {
    if (!builderInventory.length) {
      setFeedback({
        title: "Try-on unavailable",
        description: "Select at least one eligible outerwear, top, or bottom from the bag. Favorites will be added automatically.",
        tone: "error"
      });
      return;
    }

    setIsPreparingTryOn(true);
    try {
      const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ["images"], quality: 0.85 });
      if (result.canceled) {
        return;
      }

      const portrait = toTryOnPortrait(result.assets[0]);
      const session = await startWardrobeSession({
        portrait,
        bagItems: selectedItems,
        favorites: favorites ?? []
      });
      const firstItem = session.inventory[0];

      if (!firstItem) {
        setFeedback({
          title: "Try-on unavailable",
          description: "We could not find any try-on-ready items in the selected bag and favorites mix.",
          tone: "error"
        });
        return;
      }

      router.push({
        pathname: "/try-on/[slug]",
        params: {
          slug: firstItem.product.slug,
          mode: "builder"
        }
      });
    } finally {
      setIsPreparingTryOn(false);
    }
  }

  if (isLoading || !styleHydrated) {
    return (
      <Screen>
        <SkeletonBlock height={14} style={styles.loadingLabel} />
        <SkeletonBlock height={120} />
        <SkeletonBlock height={250} />
        <SkeletonBlock height={250} />
      </Screen>
    );
  }

  return (
    <Screen>
      <SectionLabel>{t("bag.section", "Bag")}</SectionLabel>
      <EditorialTitle style={styles.pageTitle}>Your Bag</EditorialTitle>

      {items.length ? (
        <>
          <SoftPanel style={styles.summaryPanel}>
            <View style={styles.metricsRow}>
              <MetricTile label="Items" value={String(selectedItems.length)} style={styles.metricTileHalf} />
              <MetricTile label="Total" value={formatMoney(selectedTotalMinor, selectedCurrency, localeTag)} style={styles.metricTileHalf} />
            </View>
          </SoftPanel>

          {items.map((item) => {
            const itemBusy = busyBagItemId === item.id;
            const selected = Boolean(selectedMap[item.id]);

            return (
              <CardFrame key={item.id} style={styles.itemCard}>
                <View style={styles.itemHeaderRow}>
                  <SelectionChip
                    label={selected ? "Selected" : "Not selected"}
                    active={selected}
                    onPress={() => toggleSelected(item.id)}
                  />
                  <Pressable style={({ pressed }) => [styles.iconButton, pressed ? styles.pressed : null]} onPress={() => removeItem.mutate(item.id)} disabled={itemBusy}>
                    <Feather name="trash-2" size={18} color={editorialTheme.text} />
                  </Pressable>
                </View>

                <ProductImage uri={item.product.hero_image_url || item.product.reference_image_url} height={220} style={styles.itemImage} />

                <View style={styles.itemCopyBlock}>
                  <Text style={styles.itemCategory}>{item.product.display_category}</Text>
                  <Text style={styles.itemName}>{item.product.name}</Text>
                  <Text style={styles.itemColor}>{item.product.color}</Text>
                </View>

                <View style={styles.metaRow}>
                  <SelectionChip label={`Color ${item.product.color}`} />
                  <SelectionChip label={`Size ${item.size_label}`} />
                  <SelectionChip label={`Qty ${item.quantity}`} />
                </View>

                <View style={styles.controlRow}>
                  <View style={styles.controlBlock}>
                    <Text style={styles.controlLabel}>{t("common.quantity", "Quantity")}</Text>
                    <QuantityStepper value={item.quantity} onChange={(value) => updateItem.mutate({ itemId: item.id, quantity: value })} style={styles.stepper} />
                  </View>
                  <View style={styles.priceBlock}>
                    <Text style={styles.controlLabel}>{t("common.price", "Price")}</Text>
                    <Text style={styles.linePrice}>{formatMoney(item.line_total.amount_minor, item.line_total.currency, localeTag)}</Text>
                    <Text style={styles.priceNote}>
                      {item.price_breakdown.adjustment_label
                        ? `${item.price_breakdown.adjustment_label}: ${formatMoney(
                            item.price_breakdown.tailoring_adjustment.amount_minor,
                            item.price_breakdown.tailoring_adjustment.currency,
                            localeTag
                          )}`
                        : "Standard tailoring profile"}
                    </Text>
                  </View>
                </View>
              </CardFrame>
            );
          })}

          <SoftPanel style={styles.actionPanel}>
            {feedback ? (
              <InlineNotice
                title={feedback.title}
                description={feedback.description}
                style={[styles.feedbackNotice, feedback.tone === "error" ? styles.feedbackError : styles.feedbackSuccess]}
              />
            ) : null}

            <EditorialButton
              label={submitSelected.isPending ? "Processing..." : "Place Order"}
              onPress={() => submitSelected.mutate(selectedItems.map((item) => item.id))}
              disabled={!selectedItems.length || submitSelected.isPending}
              style={styles.primaryButton}
            />
            <EditorialButton
              label={isPreparingTryOn ? "Preparing..." : "Virtual Try-On"}
              inverse
              onPress={() => void handleTryOn()}
              disabled={!builderInventory.length || isPreparingTryOn}
              style={styles.secondaryButton}
            />
            <EditorialButton
              label={t("common.continueShopping", "Add More Items")}
              inverse
              onPress={() => router.push("/(tabs)/collections")}
              style={styles.secondaryButton}
            />
          </SoftPanel>
        </>
      ) : (
        <SoftPanel style={styles.emptyPanel}>
          <Text style={styles.emptyTitle}>Your bag is empty.</Text>
          <BodyText style={styles.emptyBody}>
            Browse the catalog and add items to your bag.
          </BodyText>
          <EditorialButton
            label="Browse Catalog"
            onPress={() => router.push("/(tabs)/collections")}
            style={styles.emptyButton}
          />
        </SoftPanel>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  loadingLabel: {
    width: 78,
    borderRadius: 8
  },
  pageTitle: {
    fontSize: 40,
    lineHeight: 46,
    textTransform: "uppercase"
  },
  pageIntro: {
    marginTop: 10,
    marginBottom: 18
  },
  summaryPanel: {
    marginBottom: 18
  },
  metricsRow: {
    flexDirection: "row",
    gap: 10
  },
  metricTileHalf: {
    flex: 1
  },
  metricTileFull: {
    marginTop: 10
  },
  itemCard: {
    marginBottom: 16,
    padding: 16
  },
  itemHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12
  },
  itemImage: {
    marginTop: 16,
    borderRadius: 18
  },
  itemCopyBlock: {
    marginTop: 16
  },
  itemCategory: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 2,
    textTransform: "uppercase",
    color: editorialTheme.textSoft
  },
  itemName: {
    marginTop: 6,
    fontFamily: editorialSerif,
    fontSize: 26,
    lineHeight: 32,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  itemColor: {
    marginTop: 6,
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 15,
    lineHeight: 20,
    color: editorialTheme.textMuted
  },
  metaRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 16
  },
  selectionChip: {
    minHeight: 36,
    borderRadius: 18,
    paddingHorizontal: 14,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surface
  },
  selectionChipActive: {
    borderColor: editorialTheme.text,
    backgroundColor: editorialTheme.text
  },
  selectionChipText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 10,
    lineHeight: 12,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  selectionChipTextActive: {
    color: editorialTheme.surface
  },
  iconButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: editorialTheme.surface
  },
  controlRow: {
    flexDirection: "row",
    gap: 16,
    marginTop: 18
  },
  controlBlock: {
    flex: 1
  },
  controlLabel: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 1.8,
    textTransform: "uppercase",
    color: editorialTheme.textSoft
  },
  stepper: {
    marginTop: 10,
    alignSelf: "flex-start"
  },
  priceBlock: {
    flex: 1,
    alignItems: "flex-end"
  },
  linePrice: {
    marginTop: 8,
    fontFamily: editorialSerif,
    fontSize: 26,
    lineHeight: 30,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  priceNote: {
    marginTop: 6,
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 13,
    lineHeight: 20,
    color: editorialTheme.textMuted,
    textAlign: "right"
  },
  actionPanel: {
    marginTop: 6
  },
  actionTitle: {
    fontFamily: editorialSerif,
    fontSize: 30,
    lineHeight: 36,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  actionBody: {
    marginTop: 8
  },
  feedbackNotice: {
    marginTop: 16
  },
  feedbackSuccess: {
    backgroundColor: "#F2F0EA"
  },
  feedbackError: {
    borderColor: "#B8A7A1",
    backgroundColor: "#F6EFEC"
  },
  primaryButton: {
    marginTop: 18
  },
  secondaryButton: {
    marginTop: 12
  },
  emptyPanel: {
    marginTop: 10
  },
  emptyTitle: {
    fontFamily: editorialSerif,
    fontSize: 32,
    lineHeight: 38,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  emptyBody: {
    marginTop: 8
  },
  emptyButton: {
    marginTop: 18
  },
  pressed: {
    opacity: 0.82
  }
});
