import { Link, router, useLocalSearchParams } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View, useWindowDimensions } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useI18n } from "@/i18n";
import {
  EditorialPill,
  ProductImage,
  SectionLabel,
  SkeletonBlock,
  editorialSerif,
  editorialTheme
} from "@/components/ui";
import { api } from "@/services/api";
import type { ProductCard } from "@/services/api/types";

const ALL_FILTER_VALUE = "__all__";
const CATALOG_ROW_GAP = 14;

function normalizeDisplayPrice(value: number) {
  if (value > 0 && value < 1000) {
    return value * 100;
  }
  return value;
}

function formatFilterPrice(value: number, localeTag: string) {
  return new Intl.NumberFormat(localeTag, { maximumFractionDigits: 0 }).format(value);
}

function formatPrice(basePrice: number | null | undefined, currency: string | null | undefined, localeTag: string, fallback: string) {
  if (!basePrice) {
    return fallback;
  }

  return `${currency ?? "USD"} ${new Intl.NumberFormat(localeTag, { maximumFractionDigits: 0 }).format(normalizeDisplayPrice(basePrice))}`;
}

function shuffleProducts(products: ProductCard[]) {
  const next = [...products];
  for (let index = next.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [next[index], next[swapIndex]] = [next[swapIndex], next[index]];
  }
  return next;
}

export default function CollectionsScreen() {
  const { t, localeTag } = useI18n();
  const { mode } = useLocalSearchParams<{ mode?: string }>();
  const { width: screenWidth } = useWindowDimensions();
  const lowPriceLabel = formatFilterPrice(30_000, localeTag);
  const highPriceLabel = formatFilterPrice(50_000, localeTag);
  const priceBuckets = [
    { id: "ALL", label: t("collections.allPrices", "All prices") },
    { id: "LOW", label: `${lowPriceLabel}-ге дейін` },
    { id: "MID", label: `${lowPriceLabel} - ${highPriceLabel}` },
    { id: "HIGH", label: `${highPriceLabel}+` }
  ] as const;
  const [query, setQuery] = useState("");
  const allLabel = t("collections.all", "All");
  const [activeCategory, setActiveCategory] = useState(ALL_FILTER_VALUE);
  const [activeColor, setActiveColor] = useState(ALL_FILTER_VALUE);
  const [activePrice, setActivePrice] = useState<(typeof priceBuckets)[number]["id"]>("ALL");
  const { data: collectionsData, isLoading: collectionsLoading } = useQuery({ queryKey: ["collections"], queryFn: api.collections });
  const { data: productsData, isLoading: productsLoading } = useQuery({ queryKey: ["products"], queryFn: api.products });

  const isLoading = collectionsLoading || productsLoading;

  if (isLoading) {
    return (
      <SafeAreaView style={styles.safeArea} edges={["top"]}>
        <ScrollView style={styles.screen} contentContainerStyle={styles.screenContent} showsVerticalScrollIndicator={false}>
          <SkeletonBlock height={14} style={styles.loadingLabel} />
          <SkeletonBlock height={60} />
          <SkeletonBlock height={180} />
          <SkeletonBlock height={200} />
          <SkeletonBlock height={200} />
        </ScrollView>
      </SafeAreaView>
    );
  }

  const collections = collectionsData ?? [];
  const catalogProducts = (productsData as ProductCard[] | undefined) ?? [];
  const productMap = new Map<number, ProductCard>(catalogProducts.map((product) => [product.id, product]));

  for (const collection of collections) {
    for (const product of collection.products) {
      if (!productMap.has(product.id)) {
        productMap.set(product.id, product);
      }
    }
  }

  const mergedCatalogProducts = Array.from(productMap.values());
  const categories = [{ id: ALL_FILTER_VALUE, label: allLabel }, ...Array.from(new Set(mergedCatalogProducts.map((product) => product.display_category).filter(Boolean))).map((category) => ({ id: category, label: category }))];
  const colors = [{ id: ALL_FILTER_VALUE, label: allLabel }, ...Array.from(new Set(mergedCatalogProducts.map((product) => product.color).filter(Boolean))).map((color) => ({ id: color, label: color }))];
  const normalizedQuery = query.trim().toLowerCase();

  const filteredProducts = mergedCatalogProducts.filter((product) => {
    const matchesCategory = activeCategory === ALL_FILTER_VALUE || product.display_category === activeCategory;
    const matchesColor = activeColor === ALL_FILTER_VALUE || product.color === activeColor;
    const matchesQuery =
      !normalizedQuery ||
      product.name.toLowerCase().includes(normalizedQuery) ||
      product.display_category.toLowerCase().includes(normalizedQuery);

    const price = normalizeDisplayPrice(product.base_price ?? 0);
    const matchesPrice =
      activePrice === "ALL" ||
      (activePrice === "LOW" && price < 30_000) ||
      (activePrice === "MID" && price >= 30_000 && price <= 50_000) ||
      (activePrice === "HIGH" && price > 50_000);

    return matchesCategory && matchesColor && matchesQuery && matchesPrice;
  });

  const sampledProducts = shuffleProducts(filteredProducts).slice(0, 6);
  const featuredCatalogSlots = [...sampledProducts, ...Array.from({ length: Math.max(0, 6 - sampledProducts.length) }, () => null)];
  const editorialProducts = shuffleProducts(mergedCatalogProducts).slice(0, 2);
  const catalogColumnWidth = (screenWidth - 40 - CATALOG_ROW_GAP) / 2;
  const catalogImageHeight = Math.round(Math.min(Math.max(catalogColumnWidth * 1.58, 248), 328));
  const editorialPrimaryWidth = Math.min(Math.max(screenWidth * 0.66, 228), 292);
  const editorialSecondaryWidth = Math.min(Math.max(screenWidth * 0.56, 204), 248);
  const editorialPrimaryHeight = Math.round(editorialPrimaryWidth * 1.38);
  const editorialSecondaryHeight = Math.round(editorialSecondaryWidth * 1.34);

  const rows: Array<Array<ProductCard | null>> = [];
  for (let index = 0; index < featuredCatalogSlots.length; index += 2) {
    rows.push(featuredCatalogSlots.slice(index, index + 2));
  }

  if (mode === "editorial") {
    return (
      <SafeAreaView style={styles.editorialSafeArea} edges={["top", "bottom"]}>
        <View style={styles.editorialFrame}>
          <ScrollView style={styles.editorialScreen} contentContainerStyle={styles.editorialContent} showsVerticalScrollIndicator={false}>
            <SectionLabel style={styles.editorialSectionLabel}>{t("collections.fullCatalog", "Full Catalog")}</SectionLabel>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.editorialRail}
              decelerationRate="fast"
            >
              {editorialProducts.map((product, index) => {
                const imageUri = product.hero_image_url || product.reference_image_url;
                const canRenderRemoteImage = Boolean(imageUri && !imageUri.includes("example.test"));
                const imageHeight = index === 0 ? editorialPrimaryHeight : editorialSecondaryHeight;

                return (
                  <Link key={product.id} href={`/product/${product.slug}`} asChild>
                    <Pressable
                      style={({ pressed }) => [
                        styles.editorialCard,
                        index === 0
                          ? { width: editorialPrimaryWidth }
                          : [styles.editorialCardShifted, { width: editorialSecondaryWidth }],
                        pressed ? styles.cardPressed : null
                      ]}
                    >
                      {canRenderRemoteImage ? (
                        <ProductImage uri={imageUri} height={imageHeight} style={styles.editorialImage} />
                      ) : (
                        <View style={[styles.editorialImage, styles.editorialFallback, { height: imageHeight }]}>
                          <Text style={styles.editorialFallbackText}>AVISHU</Text>
                        </View>
                      )}
                      <View style={styles.editorialMeta}>
                        <Text style={styles.editorialProductName}>{product.name}</Text>
                        <Text style={styles.editorialProductDetails}>
                          {product.color}  /  {formatPrice(product.base_price, product.currency, localeTag, t("collections.priceOnRequest", "Price on request"))}
                        </Text>
                      </View>
                    </Pressable>
                  </Link>
                );
              })}
              {!editorialProducts.length ? (
                <View style={styles.editorialEmptyState}>
                  <Text style={styles.editorialFallbackText}>AVISHU</Text>
                  <Text style={styles.editorialEmptyText}>{t("home.addCatalogItems", "Add more catalog items in admin and they will appear here automatically.")}</Text>
                </View>
              ) : null}
            </ScrollView>
          </ScrollView>

          <View style={styles.editorialFooter}>
            <Pressable onPress={() => router.replace("/(tabs)/collections")} style={({ pressed }) => [styles.backButton, pressed ? styles.cardPressed : null]}>
              <Text style={styles.backButtonText}>{t("common.backToCatalog", "Back To Catalog")}</Text>
            </Pressable>
          </View>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={["top"]}>
      <ScrollView style={styles.screen} contentContainerStyle={styles.screenContent} showsVerticalScrollIndicator={false}>
        <SectionLabel>{t("collections.search", "Catalog Search")}</SectionLabel>
        <View style={styles.searchShell}>
          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder={t("collections.searchPlaceholder", "Search catalog")}
            placeholderTextColor={editorialTheme.textSoft}
            style={styles.searchInput}
          />
          <Text style={styles.searchCount}>{filteredProducts.length}</Text>
        </View>

        <SectionLabel style={styles.catalogLabel}>{t("collections.categories", "Catalog Categories")}</SectionLabel>
        <View style={styles.categoryList}>
          {categories.map((category) => (
            <Pressable key={category.id} onPress={() => setActiveCategory(category.id)} style={styles.categoryButton}>
              <Text style={[styles.categoryText, activeCategory === category.id ? styles.categoryTextActive : null]}>{category.label}</Text>
            </Pressable>
          ))}
        </View>

        <View style={styles.filterSection}>
          <View style={styles.filterHeader}>
            <Text style={styles.filterTitle}>{t("common.size", "Size")}</Text>
            <Text style={styles.filterValue}>XS - 6XL</Text>
          </View>
        </View>

        <View style={styles.filterSection}>
          <Text style={styles.filterTitle}>{t("common.color", "Color")}</Text>
          <View style={styles.filterRow}>
            {colors.map((color) => (
              <Pressable key={color.id} onPress={() => setActiveColor(color.id)}>
                <EditorialPill label={color.label} strong={activeColor === color.id} style={styles.filterPill} />
              </Pressable>
            ))}
          </View>
        </View>

        <View style={styles.filterSection}>
          <Text style={styles.filterTitle}>{t("common.price", "Price")}</Text>
          <View style={styles.filterRow}>
            {priceBuckets.map((bucket) => (
              <Pressable key={bucket.id} onPress={() => setActivePrice(bucket.id)}>
                <EditorialPill label={bucket.label} strong={activePrice === bucket.id} style={styles.filterPill} />
              </Pressable>
            ))}
          </View>
        </View>

        <SectionLabel style={styles.catalogLabel}>{t("collections.fullCatalog", "Full Catalog")}</SectionLabel>

        {rows.map((row, rowIndex) => (
          <View key={`row-${rowIndex}`} style={styles.catalogRow}>
            {row.map((product, itemIndex) => {
              if (!product) {
                return <View key={`empty-${rowIndex}-${itemIndex}`} style={styles.catalogCardPlaceholder} />;
              }

              const imageUri = product.hero_image_url || product.reference_image_url;
              const canRenderRemoteImage = Boolean(imageUri && !imageUri.includes("example.test"));

              return (
                <Link key={product.id} href={`/product/${product.slug}`} asChild>
                  <Pressable
                    style={({ pressed }) => [
                      styles.catalogCard,
                      pressed ? styles.cardPressed : null
                    ]}
                  >
                    <View style={styles.catalogImageShell}>
                      {canRenderRemoteImage ? (
                        <ProductImage uri={imageUri} height={catalogImageHeight} style={styles.catalogImage} />
                      ) : (
                        <View style={[styles.catalogImage, styles.catalogFallback, { height: catalogImageHeight }]}>
                          <Text style={styles.catalogFallbackText}>AVISHU</Text>
                        </View>
                      )}
                    </View>
                    <View style={styles.catalogMeta}>
                      <Text numberOfLines={2} style={styles.catalogName}>
                        {product.name}
                      </Text>
                      <View style={styles.catalogTagRow}>
                        <View style={styles.catalogTag}>
                          <Text style={styles.catalogTagText}>{product.color}</Text>
                        </View>
                        <View style={styles.catalogTag}>
                          <Text style={styles.catalogTagText}>XS - 6XL</Text>
                        </View>
                      </View>
                      <Text style={styles.catalogCategory}>{product.display_category}</Text>
                    </View>
                    <View style={styles.catalogFooter}>
                      <Text style={styles.catalogPrice}>{formatPrice(product.base_price, product.currency, localeTag, t("collections.priceOnRequest", "Price on request"))}</Text>
                    </View>
                  </Pressable>
                </Link>
              );
            })}
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: editorialTheme.background
  },
  editorialSafeArea: {
    flex: 1,
    backgroundColor: "#000000"
  },
  screen: {
    flex: 1,
    backgroundColor: editorialTheme.background
  },
  editorialScreen: {
    flex: 1,
    backgroundColor: "#000000"
  },
  editorialFrame: {
    flex: 1
  },
  screenContent: {
    width: "100%",
    paddingHorizontal: 20,
    paddingTop: 18,
    paddingBottom: 170
  },
  editorialContent: {
    paddingTop: 18,
    paddingBottom: 132
  },
  editorialSectionLabel: {
    marginBottom: 18,
    paddingHorizontal: 18,
    color: "rgba(255,255,255,0.68)"
  },
  editorialRail: {
    paddingLeft: 18,
    paddingRight: 28,
    paddingBottom: 12,
    alignItems: "flex-start",
    gap: 18
  },
  loadingLabel: {
    width: 138,
    borderRadius: 8
  },
  backButton: {
    alignSelf: "flex-start",
    minHeight: 34,
    paddingHorizontal: 12,
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.35)",
    backgroundColor: "rgba(0,0,0,0.55)",
    width: "100%"
  },
  backButtonText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: "#FFFFFF"
  },
  editorialCard: {
    alignSelf: "flex-start"
  },
  editorialCardShifted: {
    marginTop: 44
  },
  editorialImage: {
    width: "100%",
    borderRadius: 2
  },
  editorialMeta: {
    marginTop: 12,
    gap: 6
  },
  editorialProductName: {
    fontFamily: editorialSerif,
    fontSize: 22,
    lineHeight: 26,
    textTransform: "uppercase",
    color: "#FFFFFF"
  },
  editorialProductDetails: {
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 12,
    lineHeight: 18,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: "rgba(255,255,255,0.72)"
  },
  editorialFallback: {
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.18)",
    backgroundColor: "#111111",
    alignItems: "center",
    justifyContent: "center"
  },
  editorialFallbackText: {
    fontFamily: editorialSerif,
    fontSize: 28,
    lineHeight: 34,
    letterSpacing: 4,
    textTransform: "uppercase",
    color: "#FFFFFF"
  },
  editorialEmptyState: {
    width: 240,
    minHeight: 360,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.18)",
    backgroundColor: "#111111",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 24,
    gap: 14
  },
  editorialEmptyText: {
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 13,
    lineHeight: 20,
    color: "rgba(255,255,255,0.72)",
    textAlign: "center"
  },
  editorialFooter: {
    position: "absolute",
    left: 18,
    right: 18,
    bottom: 18
  },
  searchShell: {
    minHeight: 54,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surface,
    paddingHorizontal: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between"
  },
  searchInput: {
    flex: 1,
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 15,
    lineHeight: 20,
    color: editorialTheme.text
  },
  searchCount: {
    marginLeft: 12,
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: editorialTheme.textSoft
  },
  catalogLabel: {
    marginTop: 24,
    marginBottom: 12
  },
  categoryList: {
    gap: 10
  },
  categoryButton: {
    paddingVertical: 2
  },
  categoryText: {
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 16,
    lineHeight: 22,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  categoryTextActive: {
    fontFamily: "SpaceGrotesk_700Bold"
  },
  filterSection: {
    marginTop: 22,
    paddingTop: 18,
    borderTopWidth: 1,
    borderTopColor: editorialTheme.border
  },
  filterHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between"
  },
  filterTitle: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 13,
    lineHeight: 16,
    letterSpacing: 1.6,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  filterValue: {
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 13,
    lineHeight: 16,
    color: editorialTheme.textMuted
  },
  filterRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 12
  },
  filterPill: {
    minHeight: 30,
    paddingHorizontal: 12
  },
  catalogRow: {
    width: "100%",
    flexDirection: "row",
    gap: CATALOG_ROW_GAP,
    marginBottom: 14,
    alignItems: "stretch"
  },
  catalogCard: {
    flex: 1,
    minWidth: 0,
    flexShrink: 1,
    backgroundColor: "transparent"
  },
  catalogCardPlaceholder: {
    flex: 1,
    minWidth: 0,
    minHeight: 372,
    opacity: 0
  },
  catalogImageShell: {
    overflow: "hidden",
    borderRadius: 18,
    backgroundColor: "#F0E9DD"
  },
  catalogImage: {
    width: "100%",
    borderRadius: 18
  },
  catalogFallback: {
    height: 188,
    borderWidth: 1,
    borderColor: "rgba(23, 18, 11, 0.08)",
    backgroundColor: "#F0E9DD",
    alignItems: "center",
    justifyContent: "center"
  },
  catalogFallbackText: {
    fontFamily: editorialSerif,
    fontSize: 22,
    lineHeight: 28,
    letterSpacing: 3,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  catalogMeta: {
    marginTop: 12,
    gap: 8,
    paddingHorizontal: 2
  },
  catalogName: {
    minHeight: 40,
    fontFamily: editorialSerif,
    fontSize: 18,
    lineHeight: 20,
    letterSpacing: 0.3,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  catalogTagRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  catalogTag: {
    minHeight: 26,
    paddingHorizontal: 10,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "rgba(23, 18, 11, 0.08)",
    backgroundColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "center"
  },
  catalogTagText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 10,
    lineHeight: 12,
    letterSpacing: 1.1,
    textTransform: "uppercase",
    color: editorialTheme.textSoft
  },
  catalogCategory: {
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 11,
    lineHeight: 15,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: "#8E7F6A"
  },
  catalogFooter: {
    marginTop: 12,
    paddingTop: 10,
    paddingHorizontal: 2
  },
  catalogPrice: {
    fontFamily: editorialSerif,
    fontSize: 20,
    lineHeight: 24,
    letterSpacing: 0.6,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  cardPressed: {
    opacity: 0.84
  }
});
