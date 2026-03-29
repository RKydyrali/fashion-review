import { router, useLocalSearchParams } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import {
  BodyText,
  CardFrame,
  Divider,
  EditorialButton,
  EditorialTitle,
  InlineNotice,
  ProductImage,
  QuantityStepper,
  Screen,
  SectionLabel,
  SkeletonBlock,
  editorialSerif,
  editorialTheme
} from "@/components/ui";
import { useI18n } from "@/i18n";
import { api } from "@/services/api";
import type { ProductSizeOption } from "@/services/api/types";
import { useAuthStore } from "@/state/auth-store";

type NoticeTone = "neutral" | "success" | "error";

function productSections(data: NonNullable<ReturnType<typeof useProductCopy>>) {
  return data;
}

function useProductCopy(
  data:
    | {
        subtitle?: string | null;
        description?: string | null;
        long_description?: string | null;
        fabric_notes?: string | null;
        care_notes?: string | null;
        preorder_note?: string | null;
      }
    | undefined
) {
  return useMemo(
    () =>
      [
        { title: "Product Story", value: data?.subtitle || data?.description || data?.long_description || null },
        { title: "Details", value: data?.long_description && data?.long_description !== data?.subtitle ? data.long_description : null },
        { title: "Fabric", value: data?.fabric_notes || null },
        { title: "Care", value: data?.care_notes || null }
      ].filter((section) => Boolean(section.value)),
    [data?.care_notes, data?.description, data?.fabric_notes, data?.long_description, data?.subtitle]
  );
}

export default function ProductDetailScreen() {
  const { t } = useI18n();
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const queryClient = useQueryClient();
  const accessToken = useAuthStore((state) => state.accessToken);
  const { data, isLoading } = useQuery({ queryKey: ["product", slug], queryFn: () => api.product(slug) });
  const { data: me } = useQuery({ queryKey: ["me"], queryFn: api.me, enabled: Boolean(accessToken) });
  const { data: favorites } = useQuery({ queryKey: ["favorites"], queryFn: api.favorites, enabled: Boolean(accessToken) });
  const { data: sizeChart } = useQuery({
    queryKey: ["size-chart", data?.size_chart_id],
    queryFn: () => api.sizeChart(data?.size_chart_id ?? 1),
    enabled: Boolean(data?.size_chart_id)
  });
  const sizeRecommend = useQuery({
    queryKey: ["size-recommend", data?.size_chart_id, me?.body_profile],
    queryFn: () =>
      api.sizeRecommend({
        chart_id: data?.size_chart_id,
        fit_type: me?.body_profile?.preferred_fit || "regular"
      }),
    enabled: Boolean(data?.size_chart_id && me?.body_profile?.chest_cm && me?.body_profile?.waist_cm && me?.body_profile?.hips_cm)
  });
  const [selectedSize, setSelectedSize] = useState<string>("");
  const [quantity, setQuantity] = useState(1);
  const [sizeGuideOpen, setSizeGuideOpen] = useState(false);
  const [feedback, setFeedback] = useState<{ title: string; description: string; tone: NoticeTone } | null>(null);

  useEffect(() => {
    if (!data) {
      return;
    }

    const recommendedSize = sizeRecommend.data?.recommended_size;
    const fallbackSize = recommendedSize && data.size_options.some((option) => option.size_label === recommendedSize)
      ? recommendedSize
      : data.size_options[0]?.size_label ?? "";
    setSelectedSize((current) => {
      if (current && data.size_options.some((option) => option.size_label === current)) {
        return current;
      }
      return fallbackSize;
    });
  }, [data, sizeRecommend.data?.recommended_size]);

  const selectedOption =
    data?.size_options.find((option) => option.size_label === selectedSize) ??
    data?.size_options[0];

  const addBag = useMutation({
    mutationFn: () => api.addBagItem({ product_id: data!.id, size_label: selectedSize, quantity }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["bag"] });
      setFeedback({
        title: t("product.addedToBag", "Added to bag"),
        description: t("product.addedToBagBody", "{name} is ready in your bag with size {size} and quantity {quantity}.", {
          name: data?.name || "",
          size: selectedSize,
          quantity
        }),
        tone: "success"
      });
    },
    onError: (error) => {
      setFeedback({
        title: t("product.bagFailed", "Bag update failed"),
        description: error instanceof Error ? error.message : "We could not add this item to your bag.",
        tone: "error"
      });
    }
  });
  const addFavorite = useMutation({
    mutationFn: () => api.addFavorite(data!.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["favorites"] });
      setFeedback({
        title: t("product.savedTitle", "Saved"),
        description: t("product.savedBody", "{name} has been added to your saved edit.", { name: data?.name || "" }),
        tone: "success"
      });
    },
    onError: (error) => {
      setFeedback({
        title: t("product.saveFailed", "Save failed"),
        description: error instanceof Error ? error.message : "We could not save this item right now.",
        tone: "error"
      });
    }
  });

  const copySections = productSections(useProductCopy(data));
  const preorderNote = data?.preorder_note || "Submitted looks become grouped preorders with live status tracking.";
  const recommendedSize = sizeRecommend.data?.recommended_size;
  const isSaved = Boolean(favorites?.some((favorite) => favorite.product.id === data?.id));

  function openTryOn() {
    if (!data) {
      return;
    }

    router.push({
      pathname: "/try-on/[slug]",
      params: { slug: data.slug }
    });
  }

  if (isLoading || !data) {
    return (
      <Screen>
        <SkeletonBlock height={40} style={styles.loadingButton} />
        <SkeletonBlock height={320} />
        <SkeletonBlock height={40} />
      </Screen>
    );
  }

  return (
    <Screen>
      <EditorialButton label={t("common.backToCatalog", "Back To Catalog")} inverse onPress={() => router.push("/(tabs)/collections")} style={styles.backButton} />

      <ProductImage uri={data.hero_image_url || data.reference_image_url} />
      <SectionLabel style={styles.sectionTop}>{data.display_category}</SectionLabel>
      <EditorialTitle>{data.name}</EditorialTitle>
      <BodyText style={styles.productMeta}>{data.color}</BodyText>

      {copySections.map((section) => (
        <View key={section.title} style={styles.copySection}>
          <SectionLabel>
            {section.title === "Product Story"
              ? t("product.productStory", "Product Story")
              : section.title === "Details"
                ? t("product.details", "Details")
                : section.title === "Fabric"
                  ? t("product.fabric", "Fabric")
                  : t("product.care", "Care")}
          </SectionLabel>
          <BodyText>{section.value}</BodyText>
        </View>
      ))}

      <Divider />

      <View style={styles.priceRow}>
        <View style={styles.priceBlock}>
          <Text style={styles.priceLabel}>{t("product.selectedPrice", "Selected Price")}</Text>
          <Text style={styles.priceValue}>{selectedOption?.price_breakdown.total_price.formatted ?? data.price_breakdown.total_price.formatted}</Text>
        </View>
        {selectedOption?.price_breakdown.adjustment_label ? (
          <View style={styles.priceBlockRight}>
            <Text style={styles.priceLabel}>{t("product.adjustment", "Adjustment")}</Text>
            <Text style={styles.priceSecondary}>
              {selectedOption.price_breakdown.adjustment_label}: {selectedOption.price_breakdown.tailoring_adjustment.formatted}
            </Text>
          </View>
        ) : null}
      </View>

      <CardFrame style={styles.selectionCard}>
        <Text style={styles.cardTitle}>{t("product.sizeSelection", "Size Selection")}</Text>
        <View style={styles.sizeGrid}>
          {data.size_options.map((option: ProductSizeOption) => {
            const selected = option.size_label === selectedSize;
            return (
              <Pressable
                key={option.size_label}
                style={({ pressed }) => [styles.sizeButton, selected ? styles.sizeButtonSelected : null, pressed ? styles.buttonPressed : null]}
                onPress={() => setSelectedSize(option.size_label)}
              >
                <Text style={[styles.sizeButtonText, selected ? styles.sizeButtonTextSelected : null]}>{option.size_label}</Text>
              </Pressable>
            );
          })}
        </View>
        {recommendedSize ? (
          <InlineNotice
            title={t("product.recommended", "Recommended")}
            description={t("product.recommendedBody", "Based on your saved measurements, {size} is the current best match.", { size: recommendedSize })}
            style={styles.inlineNotice}
          />
        ) : null}

        <View style={styles.quantitySection}>
          <Text style={styles.cardTitle}>{t("common.quantity", "Quantity")}</Text>
          <QuantityStepper value={quantity} onChange={setQuantity} />
        </View>
      </CardFrame>

      {sizeChart ? (
        <CardFrame style={styles.guideCard}>
          <Pressable style={({ pressed }) => [styles.guideHeader, pressed ? styles.buttonPressed : null]} onPress={() => setSizeGuideOpen((current) => !current)}>
            <View style={styles.guideHeaderCopy}>
              <Text style={styles.cardTitle}>{t("product.sizeGuide", "Size Guide")}</Text>
              <BodyText style={styles.guideSubtitle}>{sizeGuideOpen ? t("product.hideMeasurements", "Hide measurements") : t("product.openMeasurements", "Open measurements")}</BodyText>
            </View>
            <Text style={styles.guideToggle}>{sizeGuideOpen ? t("common.close", "Close") : t("common.open", "Open")}</Text>
          </Pressable>
          {sizeGuideOpen ? (
            <View style={styles.guideRows}>
              {sizeChart.sizes.map((size) => (
                <View key={size.size_label} style={styles.guideRow}>
                  <Text style={styles.guideSizeLabel}>{size.size_label}</Text>
                  <BodyText style={styles.guideText}>
                    Chest {size.chest_min_cm}-{size.chest_max_cm} / Waist {size.waist_min_cm}-{size.waist_max_cm} / Hips {size.hips_min_cm}-{size.hips_max_cm}
                  </BodyText>
                </View>
              ))}
            </View>
          ) : null}
        </CardFrame>
      ) : null}

      <InlineNotice title={t("product.preorder", "Preorder")} description={preorderNote} />

      {feedback ? (
        <InlineNotice
          title={feedback.title}
          description={feedback.description}
          style={[styles.feedbackNotice, feedback.tone === "error" ? styles.feedbackError : styles.feedbackSuccess]}
        />
      ) : null}

      <EditorialButton
        label={addBag.isPending ? t("product.addingToBag", "Adding To Bag...") : t("product.addToBag", "Add To Bag")}
        onPress={() => addBag.mutate()}
        disabled={addBag.isPending || !selectedSize}
      />
      <EditorialButton
        label={isSaved ? t("common.saved", "Saved") : addFavorite.isPending ? t("common.saving", "Saving...") : t("product.saveItem", "Save Item")}
        inverse
        onPress={() => addFavorite.mutate()}
        disabled={isSaved || addFavorite.isPending}
        style={styles.secondaryAction}
      />
      <EditorialButton label="Open Bag Builder" inverse onPress={() => router.push("/(tabs)/bag")} style={styles.secondaryAction} />
      <EditorialButton label={t("product.aiTryOn", "AI Try-On")} inverse onPress={openTryOn} style={styles.secondaryAction} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  loadingButton: {
    width: 170,
    borderRadius: 8
  },
  backButton: {
    alignSelf: "flex-start",
    marginBottom: 16
  },
  sectionTop: {
    marginTop: 18
  },
  productMeta: {
    marginTop: 8
  },
  copySection: {
    marginTop: 18
  },
  priceRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 16
  },
  priceBlock: {
    flex: 1
  },
  priceBlockRight: {
    flex: 1,
    alignItems: "flex-end"
  },
  priceLabel: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 1.8,
    textTransform: "uppercase",
    color: editorialTheme.textSoft
  },
  priceValue: {
    marginTop: 8,
    fontFamily: editorialSerif,
    fontSize: 30,
    lineHeight: 34,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  priceSecondary: {
    marginTop: 8,
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 14,
    lineHeight: 22,
    textAlign: "right",
    color: editorialTheme.textMuted
  },
  selectionCard: {
    marginTop: 24
  },
  cardTitle: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  sizeGrid: {
    marginTop: 16,
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10
  },
  sizeButton: {
    minWidth: 70,
    minHeight: 46,
    paddingHorizontal: 14,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surface
  },
  sizeButtonSelected: {
    backgroundColor: editorialTheme.text,
    borderColor: editorialTheme.text
  },
  sizeButtonText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 1.6,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  sizeButtonTextSelected: {
    color: editorialTheme.surface
  },
  inlineNotice: {
    marginTop: 16
  },
  quantitySection: {
    marginTop: 18,
    gap: 12
  },
  guideCard: {
    marginTop: 16
  },
  guideHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 16
  },
  guideHeaderCopy: {
    flex: 1
  },
  guideSubtitle: {
    marginTop: 8,
    lineHeight: 24
  },
  guideToggle: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 1.8,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  guideRows: {
    marginTop: 18,
    gap: 14
  },
  guideRow: {
    paddingTop: 14,
    borderTopWidth: 1,
    borderTopColor: editorialTheme.border
  },
  guideSizeLabel: {
    fontFamily: editorialSerif,
    fontSize: 22,
    lineHeight: 26,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  guideText: {
    marginTop: 6,
    lineHeight: 24
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
  secondaryAction: {
    marginTop: 12
  },
  buttonPressed: {
    opacity: 0.84
  }
});
