import { Link, router } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useI18n } from "@/i18n";
import {
  BodyText,
  CardFrame,
  EditorialButton,
  EditorialPill,
  EditorialTitle,
  MetricTile,
  ProductImage,
  Screen,
  SectionLabel,
  SoftPanel,
  editorialSerif,
  editorialTheme
} from "@/components/ui";
import { api } from "@/services/api";
import { useAuthStore } from "@/state/auth-store";

function initialsFor(name?: string | null) {
  if (!name) {
    return "A";
  }

  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

function formatMeasure(value?: number | null) {
  return value ? `${value}` : "--";
}

export default function ProfileScreen() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const accessToken = useAuthStore((state) => state.accessToken);
  const queryEnabled = Boolean(accessToken);
  const { data: me } = useQuery({ queryKey: ["me"], queryFn: api.me, enabled: queryEnabled });
  const { data: favorites } = useQuery({ queryKey: ["favorites"], queryFn: api.favorites, enabled: queryEnabled });
  const updateProfile = useMutation({
    mutationFn: api.updateProfile,
    onSuccess: async (user) => {
      useAuthStore.setState({ user, locale: user.preferred_language });
      await queryClient.invalidateQueries({ queryKey: ["me"] });
    }
  });

  const activeLanguage = me?.preferred_language ?? useAuthStore.getState().locale ?? "en";
  const languages = [
    { id: "en", label: t("lang.en", "English") },
    { id: "ru", label: t("lang.ru", "Russian") },
    { id: "kk", label: t("lang.kk", "Kazakh") }
  ] as const;

  return (
    <Screen>
      <SectionLabel>{t("profile.section", "Profile")}</SectionLabel>
      <CardFrame style={styles.heroCard}>
        <View style={styles.heroTop}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{initialsFor(me?.full_name)}</Text>
          </View>
          <View style={styles.heroCopy}>
            <SectionLabel style={styles.heroEyebrow}>{t("profile.privateClient", "Private Client")}</SectionLabel>
            <EditorialTitle style={styles.heroTitle}>{me?.full_name || t("profile.clientProfile", "Client Profile")}</EditorialTitle>
            <BodyText style={styles.heroEmail}>{me?.email || "client@avishu.com"}</BodyText>
          </View>
        </View>
        <View style={styles.heroPills}>
          <EditorialPill label={me?.preferred_language || "en"} strong />
          <EditorialPill label={me?.body_profile?.preferred_fit || t("profile.regularFit", "regular fit")} />
        </View>
      </CardFrame>

      <SoftPanel style={styles.measurePanel}>
        <SectionLabel>{t("profile.fitProfile", "Fit Profile")}</SectionLabel>
        <BodyText style={styles.measureText}>
          {t("profile.alphaPreferred", "Size: {alpha} / Fit: {fit}", {
            alpha: me?.body_profile?.alpha_size || "--",
            fit: me?.body_profile?.preferred_fit || "regular"
          })}
        </BodyText>
      </SoftPanel>

      <CardFrame style={styles.languageCard}>
        <SectionLabel style={styles.languageEyebrow}>{t("profile.language", "Language")}</SectionLabel>
        <Text style={styles.languageTitle}>{t("profile.interfaceVoice", "Interface voice")}</Text>
        <View style={styles.languageRow}>
          {languages.map((language) => {
            const selected = activeLanguage === language.id;
            return (
              <Pressable
                key={language.id}
                style={({ pressed }) => [
                  styles.languageButton,
                  selected ? styles.languageButtonSelected : null,
                  pressed ? styles.cardPressed : null
                ]}
                onPress={() => updateProfile.mutate({ preferred_language: language.id })}
              >
                <Text style={[styles.languageButtonText, selected ? styles.languageButtonTextSelected : null]}>{language.label}</Text>
              </Pressable>
            );
          })}
        </View>
      </CardFrame>

      <CardFrame style={styles.savedCard}>
        <SectionLabel style={styles.languageEyebrow}>{t("profile.savedEdit", "Saved Edit")}</SectionLabel>
        <Text style={styles.savedTitle}>{t("profile.favorites", "Favorites")}</Text>
        <View style={styles.savedList}>
          {favorites?.length ? (
            favorites.map((favorite) => (
              <Link key={favorite.id} href={`/product/${favorite.product.slug}`} asChild>
                <Pressable style={({ pressed }) => [styles.favoriteCard, pressed ? styles.cardPressed : null]}>
                  <ProductImage
                    uri={favorite.product.hero_image_url || favorite.product.reference_image_url}
                    height={180}
                    style={styles.favoriteImage}
                  />
                  <Text style={styles.favoriteName}>{favorite.product.name}</Text>
                  <Text style={styles.favoriteMeta}>{favorite.product.display_category}</Text>
                </Pressable>
              </Link>
            ))
          ) : (
            <BodyText style={styles.emptyFavorites}>{t("profile.noSavedItems", "No saved items yet. Favorite a few pieces to build your capsule faster.")}</BodyText>
          )}
        </View>
      </CardFrame>

      <CardFrame style={styles.wardrobeCard}>
        <Pressable
          style={({ pressed }) => [styles.wardrobeButton, pressed ? styles.cardPressed : null]}
          onPress={() => router.push("/wardrobe")}
        >
          <View style={styles.wardrobeContent}>
            <Text style={styles.wardrobeTitle}>My Wardrobe</Text>
            <Text style={styles.wardrobeSubtitle}>Your personal collection & outfits</Text>
          </View>
          <Text style={styles.wardrobeArrow}>→</Text>
        </Pressable>
      </CardFrame>

      <CardFrame style={styles.actionCard}>
        <EditorialButton
          label={t("profile.signOut", "Sign Out")}
          onPress={async () => {
            const refreshToken = useAuthStore.getState().refreshToken;
            if (refreshToken) {
              try {
                await api.logout(refreshToken);
              } catch {
                // Clear the local session even if the API is offline.
              }
            }
            await useAuthStore.getState().clearSession();
            router.replace("/login");
          }}
          style={styles.signOutButton}
        />
      </CardFrame>
    </Screen>
  );
}

const styles = StyleSheet.create({
  heroCard: {
    marginBottom: 16,
    padding: 18
  },
  heroTop: {
    flexDirection: "row",
    gap: 16
  },
  avatar: {
    width: 74,
    height: 74,
    borderRadius: 2,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surfaceMuted,
    alignItems: "center",
    justifyContent: "center"
  },
  avatarText: {
    fontFamily: editorialSerif,
    fontSize: 28,
    lineHeight: 34,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  heroCopy: {
    flex: 1
  },
  heroEyebrow: {
    marginBottom: 2
  },
  heroTitle: {
    fontSize: 36,
    lineHeight: 42,
    textTransform: "uppercase"
  },
  heroEmail: {
    marginTop: 4
  },
  heroPills: {
    flexDirection: "row",
    gap: 10,
    marginTop: 18
  },
  measurePanel: {
    marginBottom: 16
  },
  measureTitle: {
    fontFamily: editorialSerif,
    fontSize: 28,
    lineHeight: 34,
    letterSpacing: 1.3,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  metricsRow: {
    flexDirection: "row",
    gap: 10,
    marginTop: 14
  },
  measureText: {
    marginTop: 14
  },
  profileAction: {
    marginTop: 18
  },
  languageCard: {
    marginBottom: 16
  },
  languageEyebrow: {
    marginBottom: 4
  },
  languageTitle: {
    fontFamily: editorialSerif,
    fontSize: 28,
    lineHeight: 34,
    letterSpacing: 1.3,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  languageRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 16
  },
  languageButton: {
    minHeight: 42,
    borderRadius: 2,
    paddingHorizontal: 18,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surface
  },
  languageButtonSelected: {
    backgroundColor: editorialTheme.surfaceStrong,
    borderColor: editorialTheme.borderStrong
  },
  languageButtonText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 1.2,
    color: editorialTheme.textMuted
  },
  languageButtonTextSelected: {
    color: editorialTheme.text
  },
  savedCard: {
    marginBottom: 16
  },
  savedTitle: {
    fontFamily: editorialSerif,
    fontSize: 28,
    lineHeight: 34,
    letterSpacing: 1.3,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  savedList: {
    marginTop: 16,
    gap: 14
  },
  favoriteCard: {
    borderRadius: 28
  },
  favoriteImage: {
    marginBottom: 12,
    borderRadius: 2
  },
  favoriteName: {
    fontFamily: editorialSerif,
    fontSize: 22,
    lineHeight: 28,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  favoriteMeta: {
    marginTop: 6,
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 1.6,
    textTransform: "uppercase",
    color: editorialTheme.textSoft
  },
  emptyFavorites: {
    marginTop: 4
  },
  wardrobeCard: {
    marginBottom: 16
  },
  wardrobeButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 20,
    backgroundColor: "#000",
    borderRadius: 2
  },
  wardrobeContent: {
    flex: 1
  },
  wardrobeTitle: {
    fontFamily: editorialSerif,
    fontSize: 24,
    textTransform: "uppercase",
    color: "#FFF"
  },
  wardrobeSubtitle: {
    fontSize: 12,
    color: "#999",
    marginTop: 4
  },
  wardrobeArrow: {
    fontSize: 20,
    color: "#FFF"
  },
  actionCard: {
    gap: 12
  },
  signOutButton: {
    marginTop: 12
  },
  cardPressed: {
    opacity: 0.84
  }
});
