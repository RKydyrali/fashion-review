import * as ImagePicker from "expo-image-picker";
import { router } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { AdminEmptyState, AdminField, AdminFormTitle, AdminHero, AdminOptionGroup, AdminSection, AdminStatCard, AdminStatGrid, AdminToggle } from "@/components/admin-ui";
import { BodyText, EditorialButton, EditorialPill, ProductImage, Screen, SectionLabel, editorialTheme } from "@/components/ui";
import { api } from "@/services/api";
import type {
  AdminProductCreate,
  AdminProductRead,
  AdminProductUpdate,
  LocalizedProductContent,
  LocalizedProductContentMap,
  UploadableFile
} from "@/services/api/types";

type ProductDraft = {
  sku: string;
  slug: string;
  normalized_category: string;
  season_tags: string;
  color: string;
  base_price_minor: string;
  currency: string;
  collection_slug: string | null;
  hero_image_url: string;
  reference_image_url: string;
  gallery_image_urls: string[];
  available_sizes: string;
  size_chart_id: string;
  editorial_rank: string;
  is_featured: boolean;
  is_available: boolean;
  is_active: boolean;
  translations: LocalizedProductContentMap;
};

function emptyContent(): LocalizedProductContent {
  return {
    name: "",
    description: "",
    subtitle: "",
    long_description: "",
    fabric_notes: "",
    care_notes: "",
    preorder_note: "",
    display_category: ""
  };
}

function emptyProductDraft(): ProductDraft {
  return {
    sku: "",
    slug: "",
    normalized_category: "",
    season_tags: "",
    color: "",
    base_price_minor: "0",
    currency: "USD",
    collection_slug: null,
    hero_image_url: "",
    reference_image_url: "",
    gallery_image_urls: [],
    available_sizes: "",
    size_chart_id: "1",
    editorial_rank: "1",
    is_featured: false,
    is_available: true,
    is_active: true,
    translations: {
      en: emptyContent(),
      ru: emptyContent(),
      kk: emptyContent()
    }
  };
}

function draftFromProduct(product: AdminProductRead): ProductDraft {
  return {
    sku: product.sku,
    slug: product.slug,
    normalized_category: product.normalized_category,
    season_tags: product.season_tags.join(", "),
    color: product.color,
    base_price_minor: String(product.base_price_minor),
    currency: product.currency,
    collection_slug: product.collection_slug ?? null,
    hero_image_url: product.hero_image_url ?? "",
    reference_image_url: product.reference_image_url ?? "",
    gallery_image_urls: product.gallery_image_urls,
    available_sizes: product.available_sizes.join(", "),
    size_chart_id: product.size_chart_id ? String(product.size_chart_id) : "",
    editorial_rank: String(product.editorial_rank),
    is_featured: product.is_featured,
    is_available: product.is_available,
    is_active: product.is_active,
    translations: product.translations
  };
}

function parseCsv(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function hasRequiredProductCopy(value: LocalizedProductContent) {
  return value.name.trim().length > 0 && value.display_category.trim().length > 0;
}

function needsAiTranslations(draft: ProductDraft) {
  return !hasRequiredProductCopy(draft.translations.ru) || !hasRequiredProductCopy(draft.translations.kk);
}

function applyGeneratedTranslations(
  draft: ProductDraft,
  translations: Pick<LocalizedProductContentMap, "ru" | "kk">
): ProductDraft {
  return {
    ...draft,
    translations: {
      ...draft.translations,
      ru: translations.ru,
      kk: translations.kk
    }
  };
}

function createPayload(draft: ProductDraft): AdminProductCreate {
  return {
    sku: draft.sku,
    slug: draft.slug,
    normalized_category: draft.normalized_category,
    season_tags: parseCsv(draft.season_tags),
    color: draft.color,
    base_price_minor: Number(draft.base_price_minor || 0),
    currency: draft.currency.toUpperCase(),
    collection_slug: draft.collection_slug || null,
    hero_image_url: draft.hero_image_url || null,
    reference_image_url: draft.reference_image_url || null,
    gallery_image_urls: draft.gallery_image_urls,
    available_sizes: parseCsv(draft.available_sizes),
    size_chart_id: draft.size_chart_id ? Number(draft.size_chart_id) : null,
    editorial_rank: Number(draft.editorial_rank || 1),
    is_featured: draft.is_featured,
    is_available: draft.is_available,
    is_active: draft.is_active,
    translations: draft.translations
  };
}

async function pickUploadableFile(): Promise<UploadableFile | null> {
  const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ["images"], quality: 0.8 });
  if (result.canceled || !result.assets[0]) {
    return null;
  }
  const asset = result.assets[0];
  return {
    uri: asset.uri,
    name: asset.fileName ?? `upload-${Date.now()}.jpg`,
    type: asset.mimeType ?? "image/jpeg"
  };
}

function TranslationEditor({
  language,
  value,
  onChange
}: {
  language: keyof LocalizedProductContentMap;
  value: LocalizedProductContent;
  onChange: (nextValue: LocalizedProductContent) => void;
}) {
  return (
    <AdminSection title={`${language.toUpperCase()} Copy`}>
      <AdminField label="Name" value={value.name} onChangeText={(next) => onChange({ ...value, name: next })} />
      <AdminField label="Display Category" value={value.display_category} onChangeText={(next) => onChange({ ...value, display_category: next })} />
      <AdminField label="Description" value={value.description ?? ""} onChangeText={(next) => onChange({ ...value, description: next })} multiline />
      <AdminField label="Subtitle" value={value.subtitle ?? ""} onChangeText={(next) => onChange({ ...value, subtitle: next })} />
      <AdminField label="Long Description" value={value.long_description ?? ""} onChangeText={(next) => onChange({ ...value, long_description: next })} multiline />
      <AdminField label="Fabric Notes" value={value.fabric_notes ?? ""} onChangeText={(next) => onChange({ ...value, fabric_notes: next })} multiline />
      <AdminField label="Care Notes" value={value.care_notes ?? ""} onChangeText={(next) => onChange({ ...value, care_notes: next })} multiline />
      <AdminField label="Preorder Note" value={value.preorder_note ?? ""} onChangeText={(next) => onChange({ ...value, preorder_note: next })} multiline />
    </AdminSection>
  );
}

export default function AdminProductsScreen() {
  const queryClient = useQueryClient();
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  const [draft, setDraft] = useState<ProductDraft>(emptyProductDraft());
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { data: products } = useQuery({ queryKey: ["admin-products"], queryFn: api.adminProducts });
  const { data: collections } = useQuery({ queryKey: ["admin-collections"], queryFn: api.adminCollections });
  const activeProducts = (products ?? []).filter((product) => product.is_active).length;
  const featuredProducts = (products ?? []).filter((product) => product.is_featured && product.is_active).length;
  const archivedProducts = (products ?? []).filter((product) => !product.is_active).length;

  const translateMutation = useMutation({
    mutationFn: async (workingDraft: ProductDraft) => {
      if (!hasRequiredProductCopy(workingDraft.translations.en)) {
        throw new Error("Fill the English name and display category before using AI translation.");
      }
      const response = await api.adminTranslateProductFromEnglish({
        english: workingDraft.translations.en,
        normalized_category: workingDraft.normalized_category || null,
        color: workingDraft.color || null,
        season_tags: parseCsv(workingDraft.season_tags)
      });
      if (response.ai_status !== "completed" || !response.translations) {
        throw new Error(response.error_message || "AI translation is unavailable right now.");
      }
      return response.translations;
    },
    onSuccess: (translations) => {
      setDraft((current) => applyGeneratedTranslations(current, translations));
      setErrorMessage(null);
    },
    onError: (error) => {
      setErrorMessage(error instanceof Error ? error.message : "Unable to translate product copy.");
    }
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      setErrorMessage(null);
      let workingDraft = draft;
      if (needsAiTranslations(workingDraft)) {
        const translations = await translateMutation.mutateAsync(workingDraft);
        workingDraft = applyGeneratedTranslations(workingDraft, translations);
      }
      const payload = createPayload(workingDraft);
      if (selectedProductId == null) {
        return api.adminCreateProduct(payload);
      }
      const updatePayload: AdminProductUpdate = payload;
      return api.adminUpdateProduct(selectedProductId, updatePayload);
    },
    onSuccess: async (savedProduct) => {
      setSelectedProductId(savedProduct.id);
      setDraft(draftFromProduct(savedProduct));
      await queryClient.invalidateQueries({ queryKey: ["admin-products"] });
      await queryClient.invalidateQueries({ queryKey: ["collections"] });
      await queryClient.invalidateQueries({ queryKey: ["products"] });
    },
    onError: (error) => {
      setErrorMessage(error instanceof Error ? error.message : "Unable to save product.");
    }
  });

  const archiveMutation = useMutation({
    mutationFn: async () => {
      if (selectedProductId == null) {
        return null;
      }
      return draft.is_active ? api.adminArchiveProduct(selectedProductId) : api.adminRestoreProduct(selectedProductId);
    },
    onSuccess: async (savedProduct) => {
      if (!savedProduct) {
        return;
      }
      setDraft(draftFromProduct(savedProduct));
      await queryClient.invalidateQueries({ queryKey: ["admin-products"] });
      await queryClient.invalidateQueries({ queryKey: ["products"] });
      await queryClient.invalidateQueries({ queryKey: ["collections"] });
    }
  });

  const permanentDeleteMutation = useMutation({
    mutationFn: async () => {
      if (selectedProductId == null) {
        return;
      }
      await api.adminDeleteProductPermanently(selectedProductId);
    },
    onSuccess: async () => {
      setSelectedProductId(null);
      setDraft(emptyProductDraft());
      setErrorMessage(null);
      await queryClient.invalidateQueries({ queryKey: ["admin-products"] });
      await queryClient.invalidateQueries({ queryKey: ["products"] });
      await queryClient.invalidateQueries({ queryKey: ["collections"] });
    },
    onError: (error) => {
      setErrorMessage(error instanceof Error ? error.message : "Unable to delete product permanently.");
    }
  });

  async function uploadSingle(
    uploader: (file: UploadableFile) => Promise<{ url: string }>,
    onUploaded: (url: string) => void
  ) {
    try {
      const file = await pickUploadableFile();
      if (!file) {
        return;
      }
      const upload = await uploader(file);
      onUploaded(upload.url);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to upload image.");
    }
  }

  return (
    <Screen contentContainerStyle={styles.content}>
      <SectionLabel>Admin / Products</SectionLabel>
      <AdminHero
        eyebrow="Catalog Editor"
        title="Edit products with cleaner flow, clearer status, and image-ready publishing."
        description="The product editor now separates browsing from form work, making it easier to move between copy, pricing, collection assignment, and image slots without losing context."
      >
        <AdminStatGrid>
          <AdminStatCard label="All Products" value={String(products?.length ?? 0)} note={`${activeProducts} active in the public catalog.`} tone="accent" />
          <AdminStatCard label="Featured" value={String(featuredProducts)} note="Highlighted products that are also active." />
          <AdminStatCard label="Archived" value={String(archivedProducts)} note="Soft-deleted products can be restored at any time." tone={archivedProducts > 0 ? "danger" : "success"} />
        </AdminStatGrid>
      </AdminHero>

      <View style={styles.topActions}>
        <EditorialButton label="Back To Admin" inverse onPress={() => router.push("/(admin)/dashboard")} />
        <EditorialButton
          label="Start New Product Draft"
          inverse
          onPress={() => {
            setSelectedProductId(null);
            setDraft(emptyProductDraft());
            setErrorMessage(null);
          }}
        />
      </View>

      <AdminSection
        title="Catalog List"
        description="Select an item to load it into the editor, or start a fresh draft for a new product."
        style={styles.sectionGap}
      >
        {(products ?? []).length === 0 ? (
          <AdminEmptyState
            title="No products yet"
            description="Create the first catalog product to start populating the storefront and collection assignments."
          />
        ) : null}
        {(products ?? []).map((product) => (
          <Pressable
            key={product.id}
            style={[styles.listCard, selectedProductId === product.id ? styles.listCardActive : null]}
            onPress={() => {
              setSelectedProductId(product.id);
              setDraft(draftFromProduct(product));
              setErrorMessage(null);
            }}
          >
            <View style={styles.listRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.listTitle}>{product.translations.en.name}</Text>
                <Text style={styles.listMeta}>{product.slug} / {product.sku}</Text>
                <Text style={styles.listHint}>
                  {product.collection_slug ? `Linked to ${product.collection_slug}` : "No collection linked"} / {product.available_sizes.length} sizes / {product.base_price_minor} {product.currency}
                </Text>
              </View>
              <View style={styles.listPills}>
                <EditorialPill label={product.is_active ? "active" : "archived"} strong={product.is_active} />
                {product.is_featured ? <EditorialPill label="featured" /> : null}
                <EditorialPill label={product.currency} />
              </View>
            </View>
          </Pressable>
        ))}
      </AdminSection>

      <AdminSection
        title={selectedProductId == null ? "Create Product" : "Edit Product"}
        description="Start with product identity and pricing, then tune collection placement, visibility, and localized content."
        style={styles.sectionGap}
      >
        <View style={styles.row}>
          <AdminField label="SKU" value={draft.sku} onChangeText={(value) => setDraft((current) => ({ ...current, sku: value }))} style={styles.flexField} />
          <AdminField label="Slug" value={draft.slug} onChangeText={(value) => setDraft((current) => ({ ...current, slug: value }))} style={styles.flexField} />
        </View>

        <View style={styles.row}>
          <AdminField label="Normalized Category" value={draft.normalized_category} onChangeText={(value) => setDraft((current) => ({ ...current, normalized_category: value }))} style={styles.flexField} />
          <AdminField label="Color" value={draft.color} onChangeText={(value) => setDraft((current) => ({ ...current, color: value }))} style={styles.flexField} />
        </View>

        <View style={styles.row}>
          <AdminField label="Base Price Minor" value={draft.base_price_minor} onChangeText={(value) => setDraft((current) => ({ ...current, base_price_minor: value }))} keyboardType="numeric" style={styles.flexField} />
          <AdminField label="Currency" value={draft.currency} onChangeText={(value) => setDraft((current) => ({ ...current, currency: value }))} style={styles.flexField} />
        </View>

        <View style={styles.row}>
          <AdminField label="Season Tags (comma)" value={draft.season_tags} onChangeText={(value) => setDraft((current) => ({ ...current, season_tags: value }))} style={styles.flexField} />
          <AdminField label="Sizes (comma)" value={draft.available_sizes} onChangeText={(value) => setDraft((current) => ({ ...current, available_sizes: value }))} style={styles.flexField} />
        </View>

        <View style={styles.row}>
          <AdminField label="Size Chart Id" value={draft.size_chart_id} onChangeText={(value) => setDraft((current) => ({ ...current, size_chart_id: value }))} keyboardType="numeric" style={styles.flexField} />
          <AdminField label="Editorial Rank" value={draft.editorial_rank} onChangeText={(value) => setDraft((current) => ({ ...current, editorial_rank: value }))} keyboardType="numeric" style={styles.flexField} />
        </View>

        <AdminOptionGroup
          label="Collection"
          activeValue={draft.collection_slug ?? "none"}
          onChange={(value) => setDraft((current) => ({ ...current, collection_slug: value === "none" ? null : value }))}
          options={[
            { label: "No collection", value: "none" },
            ...((collections ?? []).map((collection) => ({
              label: collection.translations.en.title,
              value: collection.slug
            })) as Array<{ label: string; value: string }>)
          ]}
        />

        <View style={styles.row}>
          <AdminToggle label="Featured" value={draft.is_featured} onToggle={() => setDraft((current) => ({ ...current, is_featured: !current.is_featured }))} style={styles.flexField} />
          <AdminToggle label="Available" value={draft.is_available} onToggle={() => setDraft((current) => ({ ...current, is_available: !current.is_available }))} style={styles.flexField} />
        </View>
        <AdminToggle label="Active in catalog" value={draft.is_active} onToggle={() => setDraft((current) => ({ ...current, is_active: !current.is_active }))} />

        <AdminSection title="Images" description="Hero and reference stay fixed, while gallery images can be added and removed as needed.">
          <View style={styles.imagePreviewRow}>
            <View style={styles.imageTile}>
              <Text style={styles.imageLabel}>Hero</Text>
              <ProductImage uri={draft.hero_image_url || null} height={180} />
              <EditorialButton
                label="Upload Hero"
                inverse
                style={styles.imageButton}
                onPress={() => uploadSingle(api.adminUploadProductHeroImage, (url) => setDraft((current) => ({ ...current, hero_image_url: url })))}
              />
            </View>
            <View style={styles.imageTile}>
              <Text style={styles.imageLabel}>Reference</Text>
              <ProductImage uri={draft.reference_image_url || null} height={180} />
              <EditorialButton
                label="Upload Reference"
                inverse
                style={styles.imageButton}
                onPress={() => uploadSingle(api.adminUploadProductReferenceImage, (url) => setDraft((current) => ({ ...current, reference_image_url: url })))}
              />
            </View>
          </View>

          <EditorialButton
            label="Add Gallery Image"
            inverse
            onPress={() =>
              uploadSingle(api.adminUploadProductGalleryImage, (url) =>
                setDraft((current) => ({ ...current, gallery_image_urls: [...current.gallery_image_urls, url] }))
              )
            }
          />

          {draft.gallery_image_urls.map((url, index) => (
            <View key={`${url}-${index}`} style={styles.galleryRow}>
              <View style={styles.galleryPreview}>
                <ProductImage uri={url} height={96} />
                <Text style={styles.galleryText}>Gallery {index + 1}</Text>
              </View>
              <EditorialButton
                label="Remove"
                inverse
                style={styles.removeButton}
                onPress={() =>
                  setDraft((current) => ({
                    ...current,
                    gallery_image_urls: current.gallery_image_urls.filter((_, itemIndex) => itemIndex !== index)
                  }))
                }
              />
            </View>
          ))}
        </AdminSection>
      </AdminSection>

      <TranslationEditor
        language="en"
        value={draft.translations.en}
        onChange={(value) => setDraft((current) => ({ ...current, translations: { ...current.translations, en: value } }))}
      />
      <AdminSection
        title="AI Translation"
        description="Fill English once, then generate Russian and Kazakh product copy for the remaining language sections. Save will also do this automatically when those sections are still empty."
      >
        <EditorialButton
          label={translateMutation.isPending ? "Translating" : "Generate Russian + Kazakh"}
          inverse
          onPress={() => translateMutation.mutate(draft)}
        />
        <BodyText style={styles.translationHint}>
          AI fills name, display category, description, subtitle, long description, fabric notes, care notes, and preorder note from the English source.
        </BodyText>
      </AdminSection>
      <TranslationEditor
        language="ru"
        value={draft.translations.ru}
        onChange={(value) => setDraft((current) => ({ ...current, translations: { ...current.translations, ru: value } }))}
      />
      <TranslationEditor
        language="kk"
        value={draft.translations.kk}
        onChange={(value) => setDraft((current) => ({ ...current, translations: { ...current.translations, kk: value } }))}
      />

      {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}

      <View style={styles.actionColumn}>
        <EditorialButton label={saveMutation.isPending ? "Saving" : selectedProductId == null ? "Create Product" : "Save Product"} onPress={() => saveMutation.mutate()} />
        {selectedProductId != null ? (
          <EditorialButton
            label={archiveMutation.isPending ? "Working" : draft.is_active ? "Archive Product" : "Restore Product"}
            inverse
            onPress={() => archiveMutation.mutate()}
          />
        ) : null}
        {selectedProductId != null ? (
          <AdminSection
            title="Permanent Delete"
            description="This removes the product entirely when it has no order history. Products tied to orders stay protected and cannot be fully deleted."
          >
            <EditorialButton
              label={permanentDeleteMutation.isPending ? "Deleting Permanently" : "Delete Product Permanently"}
              inverse
              style={styles.dangerButton}
              textStyle={styles.dangerButtonText}
              onPress={() => permanentDeleteMutation.mutate()}
            />
          </AdminSection>
        ) : null}
        <EditorialButton
          label="Reset Form"
          inverse
          onPress={() => {
            setSelectedProductId(null);
            setDraft(emptyProductDraft());
            setErrorMessage(null);
          }}
        />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: {
    gap: 16
  },
  pageCopy: {
    marginTop: 8
  },
  topActions: {
    gap: 10
  },
  sectionGap: {
    marginTop: 8
  },
  listCard: {
    borderWidth: 1,
    borderColor: editorialTheme.border,
    padding: 16,
    backgroundColor: editorialTheme.surfaceMuted,
    borderRadius: 2
  },
  listCardActive: {
    borderColor: editorialTheme.text,
    backgroundColor: "#F0ECE4"
  },
  listRow: {
    gap: 10,
    alignItems: "flex-start"
  },
  listTitle: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 13,
    lineHeight: 18,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  listMeta: {
    marginTop: 4,
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 13,
    lineHeight: 18,
    color: editorialTheme.textMuted
  },
  listHint: {
    marginTop: 8,
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 12,
    lineHeight: 18,
    color: editorialTheme.textSoft
  },
  listPills: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  row: {
    gap: 14
  },
  flexField: {
    flex: 1
  },
  imagePreviewRow: {
    gap: 14
  },
  imageTile: {
    gap: 10
  },
  imageLabel: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 1.8,
    textTransform: "uppercase",
    color: editorialTheme.textSoft
  },
  imageButton: {
    marginTop: 0
  },
  galleryRow: {
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surfaceMuted,
    padding: 12,
    gap: 12
  },
  galleryPreview: {
    gap: 10
  },
  galleryText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  removeButton: {
    minHeight: 32,
    paddingHorizontal: 12
  },
  translationHint: {
    fontSize: 14,
    lineHeight: 24
  },
  errorText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 13,
    lineHeight: 18,
    color: "#8E1F1F"
  },
  dangerButton: {
    borderColor: "#B14A3D",
    backgroundColor: "#FFF3F1"
  },
  dangerButtonText: {
    color: "#8E1F1F"
  },
  actionColumn: {
    gap: 10
  }
});
