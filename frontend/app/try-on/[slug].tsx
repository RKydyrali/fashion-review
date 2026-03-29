import * as ImagePicker from "expo-image-picker";
import { router, useLocalSearchParams } from "expo-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { Platform, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import {
  BodyText,
  CardFrame,
  EditorialButton,
  EditorialPill,
  EditorialTitle,
  InlineNotice,
  ProductImage,
  Screen,
  SectionLabel,
  editorialSerif,
  editorialTheme
} from "@/components/ui";
import { api } from "@/services/api";
import type { TryOnJob } from "@/services/api/types";
import { useAuthStore } from "@/state/auth-store";
import {
  BUILDER_SLOTS,
  getBuilderSlotItems,
  getSelectedBuilderItems,
  toTryOnPortrait,
  useStyleStore,
  type BuilderSlot,
  type TryOnPortrait
} from "@/state/style-store";

function slotLabel(slot: BuilderSlot) {
  switch (slot) {
    case "outerwear":
      return "Outerwear";
    case "tops":
      return "Tops";
    default:
      return "Bottoms";
  }
}

function normalizeSlug(value?: string | string[]) {
  if (typeof value === "string") {
    return value;
  }
  return value?.[0] ?? "";
}

async function buildTryOnJobFormData({
  portrait,
  productIds,
  singleProductId
}: {
  portrait: TryOnPortrait;
  productIds: number[];
  singleProductId?: number;
}) {
  const formData = new FormData();

  if (singleProductId != null) {
    formData.append("product_id", String(singleProductId));
  } else {
    for (const productId of productIds) {
      formData.append("product_ids", String(productId));
    }
  }

  if (Platform.OS === "web") {
    const response = await fetch(portrait.uri);
    const blob = await response.blob();
    formData.append("user_image", blob, portrait.fileName || "try-on.png");
    return formData;
  }

  formData.append("user_image", {
    uri: portrait.uri,
    name: portrait.fileName || "try-on.jpg",
    type: portrait.mimeType || "image/jpeg"
  } as never);
  return formData;
}

export default function TryOnScreen() {
  const { slug, mode } = useLocalSearchParams<{ slug: string; mode?: string }>();
  const currentUser = useAuthStore((state) => state.user);
  const builderMode = mode === "builder";
  const normalizedSlug = normalizeSlug(slug);
  const styleHydrated = useStyleStore((state) => state.hydrated);
  const bootstrapStyleStore = useStyleStore((state) => state.bootstrap);
  const builderSession = useStyleStore((state) => state.session);
  const updatePortrait = useStyleStore((state) => state.updatePortrait);
  const selectSlotItem = useStyleStore((state) => state.selectSlotItem);
  const [standalonePortrait, setStandalonePortrait] = useState<TryOnPortrait | null>(null);
  const [submittedJob, setSubmittedJob] = useState<TryOnJob | null>(null);

  useEffect(() => {
    if (!styleHydrated) {
      void bootstrapStyleStore(currentUser?.id ?? null);
    }
  }, [bootstrapStyleStore, currentUser?.id, styleHydrated]);

  const { data: product, isLoading: productLoading } = useQuery({
    queryKey: ["product", normalizedSlug],
    queryFn: () => api.product(normalizedSlug),
    enabled: !builderMode && Boolean(normalizedSlug)
  });

  const selectedBuilderItems = useMemo(() => getSelectedBuilderItems(builderSession), [builderSession]);
  const chosenProductIds = selectedBuilderItems.map((item) => item.product.id);

  const jobQuery = useQuery({
    queryKey: ["try-on-job", submittedJob?.id],
    queryFn: () => api.getTryOn(submittedJob!.id),
    enabled: Boolean(submittedJob?.id),
    initialData: submittedJob ?? undefined,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "queued" || status === "processing" ? 2500 : false;
    }
  });

  const createJob = useMutation({
    mutationFn: async ({
      portrait,
      productIds,
      singleProductId
    }: {
      portrait: TryOnPortrait;
      productIds: number[];
      singleProductId?: number;
    }) => {
      const formData = await buildTryOnJobFormData({ portrait, productIds, singleProductId });
      return api.createTryOn(formData);
    },
    onSuccess: (job) => {
      setSubmittedJob(job);
    }
  });

  const currentJob = jobQuery.data ?? submittedJob;
  const isGenerating =
    createJob.isPending ||
    currentJob?.status === "queued" ||
    currentJob?.status === "processing" ||
    jobQuery.isFetching;

  async function pickPortrait(forBuilder: boolean) {
    const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ["images"], quality: 0.85 });
    if (result.canceled) {
      return null;
    }

    const portrait = toTryOnPortrait(result.assets[0]);
    if (forBuilder) {
      await updatePortrait(portrait);
    } else {
      setStandalonePortrait(portrait);
    }
    return portrait;
  }

  async function handleBuilderGenerate() {
    if (!builderSession.portrait || !chosenProductIds.length) {
      return;
    }

    createJob.mutate({
      portrait: builderSession.portrait,
      productIds: chosenProductIds
    });
  }

  async function handleSingleProductGenerate() {
    if (!product) {
      return;
    }

    const portrait = standalonePortrait ?? (await pickPortrait(false));
    if (!portrait) {
      return;
    }

    createJob.mutate({
      portrait,
      productIds: [product.id],
      singleProductId: product.id
    });
  }

  if (builderMode && !styleHydrated) {
    return (
      <Screen>
        <CardFrame>
          <Text style={styles.loadingTitle}>Preparing try-on builder...</Text>
        </CardFrame>
      </Screen>
    );
  }

  if (!builderMode && (productLoading || !product)) {
    return (
      <Screen>
        <CardFrame>
          <Text style={styles.loadingTitle}>Loading product try-on...</Text>
        </CardFrame>
      </Screen>
    );
  }

  const standaloneProduct = product!;

  if (builderMode) {
    return (
      <Screen>
        <EditorialButton label="Back To Bag" inverse onPress={() => router.push("/(tabs)/bag")} style={styles.backButton} />

        <SectionLabel>Try-On Builder</SectionLabel>
        <EditorialTitle style={styles.pageTitle}>Build the look before you generate it.</EditorialTitle>
        <BodyText style={styles.pageIntro}>
          Your uploaded portrait stays at the top while you choose one outerwear piece, one top, and one bottom from the selected bag items plus favorites.
        </BodyText>

        {builderSession.portrait ? (
          <CardFrame style={styles.previewCard}>
            <ProductImage uri={builderSession.portrait.uri} height={420} style={styles.previewImage} />
            <View style={styles.previewOverlay}>
              <Text style={styles.previewOverlayTitle}>Chosen outfit</Text>
              <View style={styles.previewSelectionRow}>
                {selectedBuilderItems.length ? (
                  selectedBuilderItems.map((item) => (
                    <EditorialPill key={item.id} label={`${slotLabel(item.slot)}: ${item.product.name}`} strong style={styles.selectionPill} />
                  ))
                ) : (
                  <EditorialPill label="Pick at least one lane item" />
                )}
              </View>
            </View>
          </CardFrame>
        ) : (
          <InlineNotice
            title="Upload portrait"
            description="The bag flow normally attaches a portrait before opening this builder. If you arrived without one, upload it now and keep building."
            style={styles.notice}
          />
        )}

        <EditorialButton
          label={builderSession.portrait ? "Replace Portrait" : "Upload Portrait"}
          inverse
          onPress={() => void pickPortrait(true)}
          style={styles.portraitButton}
        />

        {BUILDER_SLOTS.map((slot) => {
          const slotItems = getBuilderSlotItems(builderSession, slot);
          const selectedId = builderSession.activeSelections[slot];

          return (
            <CardFrame key={slot} style={styles.laneCard}>
              <View style={styles.laneHeader}>
                <View style={styles.laneHeaderCopy}>
                  <Text style={styles.laneTitle}>{slotLabel(slot)}</Text>
                  <BodyText style={styles.laneSubtitle}>
                    {slotItems.length
                      ? `Choose one ${slotLabel(slot).toLowerCase()} item for the final look.`
                      : `No ${slotLabel(slot).toLowerCase()} pieces available yet.`}
                  </BodyText>
                </View>
                <EditorialPill label={`${slotItems.length} item${slotItems.length === 1 ? "" : "s"}`} strong={Boolean(slotItems.length)} />
              </View>

              {slotItems.length ? (
                <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.laneScrollContent}>
                  {slotItems.map((item) => {
                    const selected = selectedId === item.id;
                    return (
                      <Pressable
                        key={item.id}
                        style={({ pressed }) => [styles.laneItem, selected ? styles.laneItemSelected : null, pressed ? styles.pressed : null]}
                        onPress={() => void selectSlotItem(slot, item.id)}
                      >
                        <ProductImage uri={item.product.hero_image_url || item.product.reference_image_url} height={170} style={styles.laneImage} />
                        <Text style={styles.laneItemName}>{item.product.name}</Text>
                        <Text style={styles.laneItemMeta}>{item.product.color}</Text>
                        <Text style={styles.laneItemMeta}>
                          {item.selectedSize ? `Size ${item.selectedSize}` : item.source === "favorite" ? "Favorite piece" : "Bag piece"}
                        </Text>
                      </Pressable>
                    );
                  })}
                </ScrollView>
              ) : (
                <InlineNotice
                  title={`${slotLabel(slot)} empty`}
                  description="Add or favorite more items in this category if you want this lane to participate in the outfit."
                  style={styles.emptyLaneNotice}
                />
              )}
            </CardFrame>
          );
        })}

        {currentJob ? (
          <CardFrame style={styles.resultCard}>
            <Text style={styles.resultStatus}>Status: {currentJob.status}</Text>
            {currentJob.error_message ? (
              <InlineNotice title="Try-on failed" description={currentJob.error_message} style={styles.notice} />
            ) : null}
            {currentJob.result_image_url ? (
              <>
                <SectionLabel style={styles.resultLabel}>Generated Look</SectionLabel>
                <ProductImage uri={currentJob.result_image_url} height={420} style={styles.resultImage} />
              </>
            ) : (
              <BodyText style={styles.pendingCopy}>
                We’re processing the selected outfit. This screen refreshes automatically until the rendered look is ready.
              </BodyText>
            )}
          </CardFrame>
        ) : null}

        <EditorialButton
          label={isGenerating ? "Generating Look..." : "Generate Look"}
          onPress={() => void handleBuilderGenerate()}
          disabled={!builderSession.portrait || !chosenProductIds.length || isGenerating}
          style={styles.primaryAction}
        />
        <EditorialButton label="Return To Bag" inverse onPress={() => router.push("/(tabs)/bag")} style={styles.secondaryAction} />
      </Screen>
    );
  }

  return (
    <Screen>
      <EditorialButton label="Back To Catalog" inverse onPress={() => router.push("/(tabs)/collections")} style={styles.backButton} />

      <SectionLabel>AI Try-On</SectionLabel>
      <EditorialTitle style={styles.pageTitle}>{standaloneProduct.name}</EditorialTitle>
      <BodyText style={styles.pageIntro}>
        Upload a portrait to generate a single-product try-on. For multi-piece styling, start from Bag and open the full try-on builder.
      </BodyText>

      <ProductImage uri={standaloneProduct.hero_image_url || standaloneProduct.reference_image_url} height={420} style={styles.previewImage} />
      <CardFrame style={styles.singleCard}>
        <Text style={styles.singleTitle}>Single garment mode</Text>
        <BodyText style={styles.singleBody}>
          This screen can generate one product directly. If you want outerwear, tops, and bottoms together, choose pieces in Bag and launch Try On from there.
        </BodyText>
        {standalonePortrait ? <ProductImage uri={standalonePortrait.uri} height={250} style={styles.singlePortrait} /> : null}
        <EditorialButton
          label={standalonePortrait ? "Replace Portrait" : "Upload Portrait"}
          inverse
          onPress={() => void pickPortrait(false)}
          style={styles.secondaryAction}
        />
        <EditorialButton
          label={isGenerating ? "Generating Look..." : "Generate Look"}
          onPress={() => void handleSingleProductGenerate()}
          disabled={isGenerating}
          style={styles.primaryAction}
        />
      </CardFrame>

      {currentJob ? (
        <CardFrame style={styles.resultCard}>
          <Text style={styles.resultStatus}>Status: {currentJob.status}</Text>
          {currentJob.error_message ? (
            <InlineNotice title="Try-on failed" description={currentJob.error_message} style={styles.notice} />
          ) : null}
          {currentJob.result_image_url ? (
            <>
              <SectionLabel style={styles.resultLabel}>Generated Look</SectionLabel>
              <ProductImage uri={currentJob.result_image_url} height={420} style={styles.resultImage} />
            </>
          ) : (
            <BodyText style={styles.pendingCopy}>
              We’re processing the portrait with the selected product now. This screen refreshes automatically until the result is ready.
            </BodyText>
          )}
        </CardFrame>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  backButton: {
    alignSelf: "flex-start",
    marginBottom: 18
  },
  loadingTitle: {
    fontFamily: editorialSerif,
    fontSize: 26,
    lineHeight: 32,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  pageTitle: {
    fontSize: 38,
    lineHeight: 44,
    textTransform: "uppercase"
  },
  pageIntro: {
    marginTop: 8,
    marginBottom: 18
  },
  previewCard: {
    padding: 12
  },
  previewImage: {
    borderRadius: 24
  },
  previewOverlay: {
    marginTop: 14,
    paddingHorizontal: 6
  },
  previewOverlayTitle: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 2,
    textTransform: "uppercase",
    color: editorialTheme.textSoft
  },
  previewSelectionRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 10
  },
  selectionPill: {
    marginRight: 0
  },
  portraitButton: {
    marginTop: 14
  },
  laneCard: {
    marginTop: 18,
    padding: 16
  },
  laneHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 12
  },
  laneHeaderCopy: {
    flex: 1
  },
  laneTitle: {
    fontFamily: editorialSerif,
    fontSize: 24,
    lineHeight: 30,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  laneSubtitle: {
    marginTop: 6,
    lineHeight: 24
  },
  laneScrollContent: {
    gap: 12,
    paddingTop: 16,
    paddingRight: 8
  },
  laneItem: {
    width: 156,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surface,
    padding: 10
  },
  laneItemSelected: {
    borderColor: editorialTheme.text,
    backgroundColor: "#F6F3ED"
  },
  laneImage: {
    borderRadius: 16
  },
  laneItemName: {
    marginTop: 10,
    fontFamily: editorialSerif,
    fontSize: 18,
    lineHeight: 22,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  laneItemMeta: {
    marginTop: 4,
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.textSoft
  },
  emptyLaneNotice: {
    marginTop: 16
  },
  resultCard: {
    marginTop: 20
  },
  resultStatus: {
    fontFamily: editorialSerif,
    fontSize: 24,
    lineHeight: 30,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  resultLabel: {
    marginTop: 18
  },
  resultImage: {
    borderRadius: 24
  },
  pendingCopy: {
    marginTop: 10
  },
  primaryAction: {
    marginTop: 20
  },
  secondaryAction: {
    marginTop: 12
  },
  notice: {
    marginTop: 14
  },
  singleCard: {
    marginTop: 18
  },
  singleTitle: {
    fontFamily: editorialSerif,
    fontSize: 26,
    lineHeight: 32,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  singleBody: {
    marginTop: 8
  },
  singlePortrait: {
    marginTop: 16,
    borderRadius: 24
  },
  pressed: {
    opacity: 0.82
  }
});
