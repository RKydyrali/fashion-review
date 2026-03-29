import * as ImagePicker from "expo-image-picker";
import { router } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { AdminEmptyState, AdminField, AdminFormTitle, AdminHero, AdminSection, AdminStatCard, AdminStatGrid, AdminToggle } from "@/components/admin-ui";
import { BodyText, EditorialButton, EditorialPill, ProductImage, Screen, SectionLabel, editorialTheme } from "@/components/ui";
import { api } from "@/services/api";
import type {
  AdminCollectionCreate,
  AdminCollectionRead,
  AdminCollectionUpdate,
  LocalizedCollectionContent,
  LocalizedCollectionContentMap,
  UploadableFile
} from "@/services/api/types";

type CollectionDraft = {
  slug: string;
  hero_image_url: string;
  cover_image_url: string;
  sort_order: string;
  is_featured: boolean;
  is_active: boolean;
  translations: LocalizedCollectionContentMap;
};

function emptyCollectionContent(): LocalizedCollectionContent {
  return {
    title: "",
    summary: "",
    eyebrow: ""
  };
}

function emptyCollectionDraft(): CollectionDraft {
  return {
    slug: "",
    hero_image_url: "",
    cover_image_url: "",
    sort_order: "1",
    is_featured: true,
    is_active: true,
    translations: {
      en: emptyCollectionContent(),
      ru: emptyCollectionContent(),
      kk: emptyCollectionContent()
    }
  };
}

function draftFromCollection(collection: AdminCollectionRead): CollectionDraft {
  return {
    slug: collection.slug,
    hero_image_url: collection.hero_image_url,
    cover_image_url: collection.cover_image_url,
    sort_order: String(collection.sort_order),
    is_featured: collection.is_featured,
    is_active: collection.is_active,
    translations: collection.translations
  };
}

function createPayload(draft: CollectionDraft): AdminCollectionCreate {
  return {
    slug: draft.slug,
    hero_image_url: draft.hero_image_url,
    cover_image_url: draft.cover_image_url,
    sort_order: Number(draft.sort_order || 1),
    is_featured: draft.is_featured,
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
    name: asset.fileName ?? `collection-${Date.now()}.jpg`,
    type: asset.mimeType ?? "image/jpeg"
  };
}

function CollectionTranslationEditor({
  language,
  value,
  onChange
}: {
  language: keyof LocalizedCollectionContentMap;
  value: LocalizedCollectionContent;
  onChange: (nextValue: LocalizedCollectionContent) => void;
}) {
  return (
    <AdminSection title={`${language.toUpperCase()} Collection Copy`}>
      <AdminField label="Title" value={value.title} onChangeText={(next) => onChange({ ...value, title: next })} />
      <AdminField label="Eyebrow" value={value.eyebrow} onChangeText={(next) => onChange({ ...value, eyebrow: next })} />
      <AdminField label="Summary" value={value.summary} onChangeText={(next) => onChange({ ...value, summary: next })} multiline />
    </AdminSection>
  );
}

export default function AdminCollectionsScreen() {
  const queryClient = useQueryClient();
  const [selectedCollectionId, setSelectedCollectionId] = useState<number | null>(null);
  const [draft, setDraft] = useState<CollectionDraft>(emptyCollectionDraft());
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { data: collections } = useQuery({ queryKey: ["admin-collections"], queryFn: api.adminCollections });
  const activeCollections = (collections ?? []).filter((collection) => collection.is_active).length;
  const featuredCollections = (collections ?? []).filter((collection) => collection.is_active && collection.is_featured).length;
  const archivedCollections = (collections ?? []).filter((collection) => !collection.is_active).length;

  const saveMutation = useMutation({
    mutationFn: async () => {
      setErrorMessage(null);
      const payload = createPayload(draft);
      if (selectedCollectionId == null) {
        return api.adminCreateCollection(payload);
      }
      const updatePayload: AdminCollectionUpdate = payload;
      return api.adminUpdateCollection(selectedCollectionId, updatePayload);
    },
    onSuccess: async (savedCollection) => {
      setSelectedCollectionId(savedCollection.id);
      setDraft(draftFromCollection(savedCollection));
      await queryClient.invalidateQueries({ queryKey: ["admin-collections"] });
      await queryClient.invalidateQueries({ queryKey: ["collections"] });
    },
    onError: (error) => {
      setErrorMessage(error instanceof Error ? error.message : "Unable to save collection.");
    }
  });

  const archiveMutation = useMutation({
    mutationFn: async () => {
      if (selectedCollectionId == null) {
        return null;
      }
      return draft.is_active ? api.adminArchiveCollection(selectedCollectionId) : api.adminRestoreCollection(selectedCollectionId);
    },
    onSuccess: async (savedCollection) => {
      if (!savedCollection) {
        return;
      }
      setDraft(draftFromCollection(savedCollection));
      await queryClient.invalidateQueries({ queryKey: ["admin-collections"] });
      await queryClient.invalidateQueries({ queryKey: ["collections"] });
      await queryClient.invalidateQueries({ queryKey: ["admin-products"] });
      await queryClient.invalidateQueries({ queryKey: ["products"] });
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
      <SectionLabel>Admin / Collections</SectionLabel>
      <AdminHero
        eyebrow="Collection Studio"
        title="Build collection stories with clearer editorial status and media flow."
        description="Collections often carry the strongest merchandising narrative, so this screen now foregrounds active state, feature status, and artwork updates more gracefully."
      >
        <AdminStatGrid>
          <AdminStatCard label="All Collections" value={String(collections?.length ?? 0)} note={`${activeCollections} active across the catalog.`} tone="accent" />
          <AdminStatCard label="Featured" value={String(featuredCollections)} note="Active collections marked for stronger placement." />
          <AdminStatCard label="Archived" value={String(archivedCollections)} note="Archiving unassigns linked products instead of hiding them." tone={archivedCollections > 0 ? "danger" : "success"} />
        </AdminStatGrid>
      </AdminHero>

      <View style={styles.topActions}>
        <EditorialButton label="Back To Admin" inverse onPress={() => router.push("/(admin)/dashboard")} />
        <EditorialButton
          label="Start New Collection Draft"
          inverse
          onPress={() => {
            setSelectedCollectionId(null);
            setDraft(emptyCollectionDraft());
            setErrorMessage(null);
          }}
        />
      </View>

      <AdminSection
        title="Collection List"
        description="Choose an existing collection to refine it, or create a fresh story from a clean draft."
        style={styles.sectionGap}
      >
        {(collections ?? []).length === 0 ? (
          <AdminEmptyState
            title="No collections yet"
            description="Create the first collection to group products under a shared editorial story and imagery."
          />
        ) : null}
        {(collections ?? []).map((collection) => (
          <Pressable
            key={collection.id}
            style={[styles.listCard, selectedCollectionId === collection.id ? styles.listCardActive : null]}
            onPress={() => {
              setSelectedCollectionId(collection.id);
              setDraft(draftFromCollection(collection));
              setErrorMessage(null);
            }}
          >
            <View style={styles.listRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.listTitle}>{collection.translations.en.title}</Text>
                <Text style={styles.listMeta}>{collection.slug}</Text>
                <Text style={styles.listHint}>{collection.translations.en.eyebrow || "No eyebrow yet"} / sort order {collection.sort_order}</Text>
              </View>
              <View style={styles.listPills}>
                <EditorialPill label={collection.is_active ? "active" : "archived"} strong={collection.is_active} />
                {collection.is_featured ? <EditorialPill label="featured" /> : null}
              </View>
            </View>
          </Pressable>
        ))}
      </AdminSection>

      <AdminSection
        title={selectedCollectionId == null ? "Create Collection" : "Edit Collection"}
        description="Set identity and visibility first, then upload the art direction and localized collection copy."
        style={styles.sectionGap}
      >
        <AdminField label="Slug" value={draft.slug} onChangeText={(value) => setDraft((current) => ({ ...current, slug: value }))} />
        <AdminField label="Sort Order" value={draft.sort_order} onChangeText={(value) => setDraft((current) => ({ ...current, sort_order: value }))} keyboardType="numeric" />

        <AdminToggle label="Featured collection" value={draft.is_featured} onToggle={() => setDraft((current) => ({ ...current, is_featured: !current.is_featured }))} />
        <AdminToggle label="Active in catalog" value={draft.is_active} onToggle={() => setDraft((current) => ({ ...current, is_active: !current.is_active }))} />

        <AdminSection title="Images" description="Hero and cover images shape the first impression for collection landing content.">
          <View style={styles.imageTile}>
            <Text style={styles.imageLabel}>Hero Image</Text>
            <ProductImage uri={draft.hero_image_url || null} height={180} />
            <EditorialButton
              label="Upload Hero"
              inverse
              onPress={() => uploadSingle(api.adminUploadCollectionHeroImage, (url) => setDraft((current) => ({ ...current, hero_image_url: url })))}
            />
          </View>
          <View style={styles.imageTile}>
            <Text style={styles.imageLabel}>Cover Image</Text>
            <ProductImage uri={draft.cover_image_url || null} height={180} />
            <EditorialButton
              label="Upload Cover"
              inverse
              onPress={() => uploadSingle(api.adminUploadCollectionCoverImage, (url) => setDraft((current) => ({ ...current, cover_image_url: url })))}
            />
          </View>
        </AdminSection>
      </AdminSection>

      <CollectionTranslationEditor
        language="en"
        value={draft.translations.en}
        onChange={(value) => setDraft((current) => ({ ...current, translations: { ...current.translations, en: value } }))}
      />
      <CollectionTranslationEditor
        language="ru"
        value={draft.translations.ru}
        onChange={(value) => setDraft((current) => ({ ...current, translations: { ...current.translations, ru: value } }))}
      />
      <CollectionTranslationEditor
        language="kk"
        value={draft.translations.kk}
        onChange={(value) => setDraft((current) => ({ ...current, translations: { ...current.translations, kk: value } }))}
      />

      {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}

      <View style={styles.actionColumn}>
        <EditorialButton
          label={saveMutation.isPending ? "Saving" : selectedCollectionId == null ? "Create Collection" : "Save Collection"}
          onPress={() => saveMutation.mutate()}
        />
        {selectedCollectionId != null ? (
          <EditorialButton
            label={archiveMutation.isPending ? "Working" : draft.is_active ? "Archive Collection" : "Restore Collection"}
            inverse
            onPress={() => archiveMutation.mutate()}
          />
        ) : null}
        <EditorialButton
          label="Reset Form"
          inverse
          onPress={() => {
            setSelectedCollectionId(null);
            setDraft(emptyCollectionDraft());
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
  errorText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 13,
    lineHeight: 18,
    color: "#8E1F1F"
  },
  actionColumn: {
    gap: 10
  }
});
