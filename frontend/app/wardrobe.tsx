import { useState, useEffect } from "react";
import * as ImagePicker from "expo-image-picker";
import { router } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View, Alert, Image } from "react-native";

import {
  BodyText,
  CardFrame,
  EditorialPill,
  ProductImage,
  Screen,
  SectionLabel,
  editorialSerif,
  editorialTheme
} from "@/components/ui";
import { api } from "@/services/api";
import { useAuthStore } from "@/state/auth-store";
import { useStyleStore, toTryOnPortrait } from "@/state/style-store";
import type { WardrobeItemRead, WardrobeOutfitRead, ProductCard } from "@/services/api/types";

type TabType = "wardrobe" | "catalog" | "outfits" | "insights";

export default function WardrobeScreen() {
  const { accessToken, user } = useAuthStore();
  const queryClient = useQueryClient();
  const queryEnabled = Boolean(accessToken);
  const startWardrobeSession = useStyleStore((state) => state.startWardrobeSession);
  
  const [activeTab, setActiveTab] = useState<TabType>("wardrobe");
  const [outfitName, setOutfitName] = useState("");
  const [showCreateOutfit, setShowCreateOutfit] = useState(false);
  const [selectedItems, setSelectedItems] = useState<number[]>([]);
  const [isPreparingTryOn, setIsPreparingTryOn] = useState(false);

  const { data: items = [], isLoading: itemsLoading } = useQuery({
    queryKey: ["wardrobeItems"],
    queryFn: () => api.wardrobeItems(),
    enabled: queryEnabled,
  });

  const { data: outfits = [], isLoading: outfitsLoading } = useQuery({
    queryKey: ["wardrobeOutfits"],
    queryFn: () => api.wardrobeOutfits(),
    enabled: queryEnabled,
  });

  const { data: catalog = [], isLoading: catalogLoading } = useQuery({
    queryKey: ["products"],
    queryFn: () => api.products(),
    enabled: queryEnabled,
  });

  const { data: favorites = [], isLoading: favoritesLoading } = useQuery({
    queryKey: ["favorites"],
    queryFn: () => api.favorites(),
    enabled: queryEnabled,
  });

  const [showSizePicker, setShowSizePicker] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<ProductCard | null>(null);

  const addItemMutation = useMutation({
    mutationFn: api.addWardrobeItem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wardrobeItems"] });
      Alert.alert("Added to Wardrobe", "Item has been added to your wardrobe.");
    },
  });

  const deleteItemMutation = useMutation({
    mutationFn: api.deleteWardrobeItem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wardrobeItems"] });
    },
  });

  const createOutfitMutation = useMutation({
    mutationFn: api.createWardrobeOutfit,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wardrobeOutfits"] });
    },
  });

  const handleTryOnOutfit = async (outfit: typeof outfits[0]) => {
    if (outfit.items.length === 0) {
      Alert.alert("No Items", "This outfit has no items to try on.");
      return;
    }

    setIsPreparingTryOn(true);
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ["images"],
        quality: 0.85,
      });
      if (result.canceled) {
        setIsPreparingTryOn(false);
        return;
      }

      const portrait = toTryOnPortrait(result.assets[0]);
      const session = await startWardrobeSession({
        portrait,
        bagItems: outfit.items.map(item => ({
          id: item.id,
          product: {
            id: item.product_id,
            name: item.product_name,
            slug: `product-${item.product_id}`,
            sku: `SKU-${item.product_id}`,
            display_category: item.product_category,
            normalized_category: item.product_category.toLowerCase(),
            color: item.product_color,
            hero_image_url: item.product_image || undefined,
            reference_image_url: undefined,
            is_available: true,
            is_active: true,
            season_tags: [],
            base_price: item.product_price_minor,
            currency: "KZT",
            available_sizes: [item.size_label],
          },
          size_label: item.size_label,
          quantity: 1,
          price_breakdown: {
            base_price: { amount_minor: item.product_price_minor, currency: "KZT", formatted: `${item.product_price_minor / 100} ₸` },
            tailoring_adjustment: { amount_minor: 0, currency: "KZT", formatted: "0 ₸" },
            total_price: { amount_minor: item.product_price_minor, currency: "KZT", formatted: `${item.product_price_minor / 100} ₸` },
          },
          line_total: { amount_minor: item.product_price_minor, currency: "KZT", formatted: `${item.product_price_minor / 100} ₸` },
        })),
        favorites: [],
      });

      const firstItem = session.inventory[0];
      if (!firstItem) {
        Alert.alert("Try-on Unavailable", "Could not find try-on ready items.");
        setIsPreparingTryOn(false);
        return;
      }

      router.push({
        pathname: "/try-on/[slug]",
        params: { slug: firstItem.product.slug, mode: "builder" },
      });
    } catch (error) {
      Alert.alert("Error", "Failed to start try-on.");
    } finally {
      setIsPreparingTryOn(false);
    }
  };

  const tabs: { key: TabType; label: string }[] = [
    { key: "wardrobe", label: "My Wardrobe" },
    { key: "catalog", label: "Catalog" },
    { key: "outfits", label: "Outfits" },
    { key: "insights", label: "Insights" }
  ];

  const toggleItemSelection = (itemId: number) => {
    setSelectedItems(prev => 
      prev.includes(itemId) 
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const favoriteIds = favorites.map(f => f.id);
  const isFavoriteSelection = selectedItems.length > 0 && items.length === 0 && selectedItems.some(id => favoriteIds.includes(id));

  const createOutfit = async () => {
    if (!outfitName || selectedItems.length === 0) return;

    let wardrobeItemIds = selectedItems.filter(id => items.some(i => i.id === id));

    if (isFavoriteSelection) {
      const favItems = favorites.filter(f => selectedItems.includes(f.id));
      for (const fav of favItems) {
        await api.addWardrobeItem({
          product_id: fav.product.id,
          size_label: fav.product.available_sizes?.[0] || "M",
          color: fav.product.color,
        });
      }
      await queryClient.invalidateQueries({ queryKey: ["wardrobeItems"] });
      const updatedItems = await api.wardrobeItems();
      wardrobeItemIds = updatedItems.slice(0, favItems.length).map(i => i.id);
    }
    
    createOutfitMutation.mutate({
      name: outfitName,
      wardrobe_item_ids: wardrobeItemIds,
    });
    
    setOutfitName("");
    setSelectedItems([]);
    setShowCreateOutfit(false);
  };

  const removeItem = (itemId: number) => {
    Alert.alert(
      "Remove Item",
      "Are you sure you want to remove this item from your wardrobe?",
      [
        { text: "Cancel", style: "cancel" },
        { text: "Remove", style: "destructive", onPress: () => deleteItemMutation.mutate(itemId) },
      ]
    );
  };

  return (
    <Screen contentContainerStyle={styles.screenContent}>
      <Pressable style={styles.backButton} onPress={() => router.back()}>
        <Text style={styles.backButtonText}>← Back</Text>
      </Pressable>

      <SectionLabel>Personal Stylist</SectionLabel>
      <Text style={styles.pageTitle}>My Wardrobe</Text>
      <BodyText style={styles.pageSubtitle}>
        Build your personal style. Add items from the catalog and create your own outfits - no purchase required.
      </BodyText>

      <View style={styles.tabRow}>
        {tabs.map(tab => (
          <Pressable
            key={tab.key}
            style={[styles.tab, activeTab === tab.key && styles.tabActive]}
            onPress={() => setActiveTab(tab.key)}
          >
            <Text style={[styles.tabText, activeTab === tab.key && styles.tabTextActive]}>
              {tab.label}
            </Text>
          </Pressable>
        ))}
      </View>

      {activeTab === "wardrobe" && (
        <ScrollView style={styles.contentScroll} showsVerticalScrollIndicator={false}>
          {itemsLoading ? (
            <Text style={styles.loadingText}>Loading...</Text>
          ) : (
            <>
              <View style={styles.wardrobeGrid}>
                {items.map(item => (
                  <Pressable
                    key={item.id}
                    style={styles.wardrobeItem}
                    onPress={() => toggleItemSelection(item.id)}
                    onLongPress={() => removeItem(item.id)}
                  >
                    <View style={styles.wardrobeItemImage}>
                      {selectedItems.includes(item.id) && (
                        <View style={styles.selectedBadge}>
                          <Text style={styles.selectedBadgeText}>✓</Text>
                        </View>
                      )}
                      {item.product_image ? (
                        <Image source={{ uri: item.product_image }} style={styles.productImage} />
                      ) : (
                        <Text style={styles.wardrobeItemPlaceholder}>👔</Text>
                      )}
                    </View>
                    <Text style={styles.wardrobeItemName} numberOfLines={1}>{item.product_name}</Text>
                    <Text style={styles.wardrobeItemDetails}>
                      {item.product_color} / {item.size_label}
                    </Text>
                  </Pressable>
                ))}
              </View>

              {selectedItems.length > 0 && (
                <Pressable
                  style={styles.createOutfitButton}
                  onPress={() => setShowCreateOutfit(true)}
                >
                  <Text style={styles.createOutfitButtonText}>
                    Create Outfit ({selectedItems.length} items)
                  </Text>
                </Pressable>
              )}

              {items.length === 0 && favorites.length > 0 && (
                <>
                  <Text style={styles.sectionTitle}>Your Favorites</Text>
                  <Text style={styles.sectionSubtitle}>Select items to create an outfit</Text>
                  <View style={styles.wardrobeGrid}>
                    {favorites.map(fav => (
                      <Pressable
                        key={fav.id}
                        style={styles.wardrobeItem}
                        onPress={() => toggleItemSelection(fav.id)}
                      >
                        <View style={styles.wardrobeItemImage}>
                          {selectedItems.includes(fav.id) && (
                            <View style={styles.selectedBadge}>
                              <Text style={styles.selectedBadgeText}>✓</Text>
                            </View>
                          )}
                          {fav.product.hero_image_url ? (
                            <Image source={{ uri: fav.product.hero_image_url }} style={styles.productImage} />
                          ) : (
                            <Text style={styles.wardrobeItemPlaceholder}>👔</Text>
                          )}
                        </View>
                        <Text style={styles.wardrobeItemName} numberOfLines={1}>{fav.product.name}</Text>
                        <Text style={styles.wardrobeItemDetails}>
                          {fav.product.color}
                        </Text>
                      </Pressable>
                    ))}
                  </View>
                </>
              )}

              {items.length === 0 && favorites.length === 0 && (
                <CardFrame style={styles.emptyCard}>
                  <Text style={styles.emptyText}>No items yet</Text>
                  <BodyText style={styles.emptySubtext}>
                    Browse the catalog and add favorites or add items to your wardrobe
                  </BodyText>
                </CardFrame>
              )}
            </>
          )}
        </ScrollView>
      )}

      {activeTab === "catalog" && (
        <ScrollView style={styles.contentScroll} showsVerticalScrollIndicator={false}>
          {catalogLoading ? (
            <Text style={styles.loadingText}>Loading...</Text>
          ) : (
            <>
              <BodyText style={styles.catalogDescription}>
                Browse the catalog and add items to your wardrobe to create outfits.
              </BodyText>
              <View style={styles.wardrobeGrid}>
                {catalog.map(product => (
                  <Pressable
                    key={product.id}
                    style={styles.wardrobeItem}
                    onPress={() => {
                      setSelectedProduct(product);
                      setShowSizePicker(true);
                    }}
                  >
                    <View style={styles.wardrobeItemImage}>
                      {product.hero_image_url ? (
                        <Image source={{ uri: product.hero_image_url }} style={styles.productImage} />
                      ) : (
                        <Text style={styles.wardrobeItemPlaceholder}>👔</Text>
                      )}
                    </View>
                    <Text style={styles.wardrobeItemName} numberOfLines={1}>{product.name}</Text>
                    <Text style={styles.wardrobeItemDetails}>
                      {product.color} {product.base_price ? `/ $${(product.base_price / 100).toFixed(0)}` : ""}
                    </Text>
                  </Pressable>
                ))}
              </View>
            </>
          )}
        </ScrollView>
      )}

      {activeTab === "outfits" && (
        <ScrollView style={styles.contentScroll} showsVerticalScrollIndicator={false}>
          {outfitsLoading ? (
            <Text style={styles.loadingText}>Loading...</Text>
          ) : (
            <>
              {outfits.map(outfit => (
                <CardFrame key={outfit.id} style={styles.outfitCard}>
                  <Text style={styles.outfitName}>{outfit.name}</Text>
                  <Text style={styles.outfitItems}>{outfit.items.length} items</Text>
                  <View style={styles.outfitPreview}>
                    {outfit.items.slice(0, 3).map((item, idx) => (
                      <View key={idx} style={styles.outfitPreviewItem}>
                        {item.product_image ? (
                          <Image source={{ uri: item.product_image }} style={styles.outfitPreviewImage} />
                        ) : (
                          <Text style={styles.outfitPreviewEmoji}>👔</Text>
                        )}
                      </View>
                    ))}
                  </View>
                  <Pressable 
                    style={styles.tryOnButton}
                    onPress={() => handleTryOnOutfit(outfit)}
                    disabled={isPreparingTryOn}
                  >
                    <Text style={styles.tryOnButtonText}>
                      {isPreparingTryOn ? "Opening..." : "Virtual Try-On"}
                    </Text>
                  </Pressable>
                </CardFrame>
              ))}

              {outfits.length === 0 && (
                <CardFrame style={styles.emptyCard}>
                  <Text style={styles.emptyText}>No outfits yet</Text>
                  <BodyText style={styles.emptySubtext}>
                    Select items from your wardrobe and create your first outfit
                  </BodyText>
                </CardFrame>
              )}
            </>
          )}
        </ScrollView>
      )}

      {activeTab === "insights" && (
        <ScrollView style={styles.contentScroll} showsVerticalScrollIndicator={false}>
          <CardFrame style={styles.insightCard}>
            <View style={styles.insightHeader}>
              <EditorialPill label="get started" strong />
            </View>
            <Text style={styles.insightTitle}>Build Your Wardrobe</Text>
            <Text style={styles.insightDescription}>
              Start by adding items from the catalog to your personal wardrobe.
            </Text>
            <Text style={styles.insightReason}>
              Items you purchase will automatically appear here.
            </Text>
          </CardFrame>

          {items.length > 0 && (
            <CardFrame style={styles.insightCard}>
              <View style={styles.insightHeader}>
                <EditorialPill label="collection" />
              </View>
              <Text style={styles.insightTitle}>Your Collection</Text>
              <Text style={styles.insightDescription}>
                You have {items.length} item{items.length !== 1 ? "s" : ""} in your wardrobe.
              </Text>
            </CardFrame>
          )}

          {outfits.length > 0 && (
            <CardFrame style={styles.insightCard}>
              <View style={styles.insightHeader}>
                <EditorialPill label="style" />
              </View>
              <Text style={styles.insightTitle}>Your Outfits</Text>
              <Text style={styles.insightDescription}>
                You have created {outfits.length} outfit{outfits.length !== 1 ? "s" : ""}.
              </Text>
            </CardFrame>
          )}
        </ScrollView>
      )}

      {showCreateOutfit && (
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Create Outfit</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="Outfit name (e.g. Business Meeting)"
              placeholderTextColor={editorialTheme.textSoft}
              value={outfitName}
              onChangeText={setOutfitName}
            />
            <Text style={styles.modalSubtext}>{selectedItems.length} items selected</Text>
            <View style={styles.modalButtons}>
              <Pressable
                style={styles.modalCancelButton}
                onPress={() => setShowCreateOutfit(false)}
              >
                <Text style={styles.modalCancelText}>Cancel</Text>
              </Pressable>
              <Pressable
                style={styles.modalCreateButton}
                onPress={createOutfit}
                disabled={!outfitName}
              >
                <Text style={styles.modalCreateText}>Create</Text>
              </Pressable>
            </View>
          </View>
        </View>
      )}

      {showSizePicker && selectedProduct && (
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Select Size</Text>
            <Text style={styles.modalSubtext}>{selectedProduct.name}</Text>
            <View style={styles.sizeGrid}>
              {selectedProduct.available_sizes?.map((size) => (
                <Pressable
                  key={size}
                  style={styles.sizeButton}
                  onPress={() => {
                    addItemMutation.mutate({
                      product_id: selectedProduct.id,
                      size_label: size,
                      color: selectedProduct.color,
                    });
                    setShowSizePicker(false);
                    setSelectedProduct(null);
                  }}
                >
                  <Text style={styles.sizeButtonText}>{size}</Text>
                </Pressable>
              ))}
            </View>
            <Pressable
              style={styles.modalCancelButton}
              onPress={() => {
                setShowSizePicker(false);
                setSelectedProduct(null);
              }}
            >
              <Text style={styles.modalCancelText}>Cancel</Text>
            </Pressable>
          </View>
        </View>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  screenContent: {
    paddingBottom: 100
  },
  backButton: {
    marginBottom: 16
  },
  backButtonText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 14,
    color: editorialTheme.textMuted
  },
  pageTitle: {
    fontFamily: editorialSerif,
    fontSize: 32,
    textTransform: "uppercase",
    marginBottom: 8
  },
  pageSubtitle: {
    marginBottom: 20,
    fontSize: 14,
    color: editorialTheme.textMuted
  },
  tabRow: {
    flexDirection: "row",
    marginBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: editorialTheme.border
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: "center"
  },
  tabActive: {
    borderBottomWidth: 2,
    borderBottomColor: "#000"
  },
  tabText: {
    fontSize: 12,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: editorialTheme.textMuted
  },
  tabTextActive: {
    color: "#000",
    fontWeight: "600"
  },
  contentScroll: {
    flex: 1
  },
  loadingText: {
    textAlign: "center",
    marginTop: 40,
    color: editorialTheme.textMuted
  },
  wardrobeGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12
  },
  wardrobeItem: {
    width: "47%",
    marginBottom: 16
  },
  wardrobeItemImage: {
    height: 160,
    backgroundColor: editorialTheme.surfaceMuted,
    borderRadius: 2,
    marginBottom: 10,
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden"
  },
  productImage: {
    width: "100%",
    height: "100%",
    resizeMode: "cover"
  },
  selectedBadge: {
    position: "absolute",
    top: 8,
    right: 8,
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: "#000",
    alignItems: "center",
    justifyContent: "center"
  },
  selectedBadgeText: {
    color: "#FFF",
    fontSize: 12
  },
  wardrobeItemPlaceholder: {
    fontSize: 40
  },
  wardrobeItemName: {
    fontFamily: editorialSerif,
    fontSize: 14,
    textTransform: "uppercase",
    marginBottom: 4
  },
  wardrobeItemDetails: {
    fontSize: 11,
    color: editorialTheme.textMuted
  },
  createOutfitButton: {
    backgroundColor: "#000",
    padding: 16,
    borderRadius: 2,
    alignItems: "center",
    marginTop: 16
  },
  createOutfitButtonText: {
    color: "#FFF",
    fontSize: 13,
    letterSpacing: 1,
    textTransform: "uppercase"
  },
  outfitCard: {
    marginBottom: 12,
    padding: 16
  },
  outfitName: {
    fontFamily: editorialSerif,
    fontSize: 18,
    textTransform: "uppercase",
    marginBottom: 4
  },
  outfitItems: {
    fontSize: 12,
    color: editorialTheme.textMuted,
    marginBottom: 12
  },
  outfitPreview: {
    flexDirection: "row",
    gap: 8
  },
  outfitPreviewItem: {
    width: 50,
    height: 50,
    backgroundColor: editorialTheme.surfaceMuted,
    borderRadius: 2,
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden"
  },
  outfitPreviewImage: {
    width: "100%",
    height: "100%",
    resizeMode: "cover"
  },
  outfitPreviewEmoji: {
    fontSize: 24
  },
  insightCard: {
    marginBottom: 12,
    padding: 16
  },
  insightHeader: {
    marginBottom: 12
  },
  insightTitle: {
    fontFamily: editorialSerif,
    fontSize: 18,
    textTransform: "uppercase",
    marginBottom: 8
  },
  insightDescription: {
    fontSize: 14,
    marginBottom: 8
  },
  insightReason: {
    fontSize: 12,
    color: editorialTheme.textMuted,
    fontStyle: "italic"
  },
  emptyCard: {
    alignItems: "center",
    paddingVertical: 40
  },
  emptyText: {
    fontFamily: editorialSerif,
    fontSize: 18,
    textTransform: "uppercase",
    marginBottom: 8
  },
  emptySubtext: {
    textAlign: "center",
    fontSize: 14,
    color: editorialTheme.textMuted
  },
  modalOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    alignItems: "center",
    padding: 20
  },
  modalContent: {
    width: "100%",
    maxWidth: 320,
    backgroundColor: editorialTheme.surface,
    borderRadius: 2,
    padding: 24
  },
  modalTitle: {
    fontFamily: editorialSerif,
    fontSize: 20,
    textTransform: "uppercase",
    marginBottom: 16,
    textAlign: "center"
  },
  modalInput: {
    height: 48,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    borderRadius: 2,
    paddingHorizontal: 14,
    fontSize: 16,
    marginBottom: 12
  },
  modalSubtext: {
    fontSize: 12,
    color: editorialTheme.textMuted,
    marginBottom: 16
  },
  modalButtons: {
    flexDirection: "row",
    gap: 12
  },
  modalCancelButton: {
    flex: 1,
    height: 44,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    borderRadius: 2,
    alignItems: "center",
    justifyContent: "center"
  },
  modalCancelText: {
    fontSize: 12,
    letterSpacing: 1,
    textTransform: "uppercase"
  },
  modalCreateButton: {
    flex: 1,
    height: 44,
    backgroundColor: "#000",
    borderRadius: 2,
    alignItems: "center",
    justifyContent: "center"
  },
  modalCreateText: {
    color: "#FFF",
    fontSize: 12,
    letterSpacing: 1,
    textTransform: "uppercase"
  },
  catalogDescription: {
    marginBottom: 16,
    fontSize: 14,
    color: editorialTheme.textMuted
  },
  sectionTitle: {
    fontFamily: editorialSerif,
    fontSize: 20,
    textTransform: "uppercase",
    marginBottom: 4,
    marginTop: 8
  },
  sectionSubtitle: {
    fontSize: 13,
    color: editorialTheme.textMuted,
    marginBottom: 16
  },
  sizeGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 16
  },
  sizeButton: {
    width: 50,
    height: 50,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    borderRadius: 2,
    alignItems: "center",
    justifyContent: "center"
  },
  sizeButtonText: {
    fontSize: 14,
    fontWeight: "600"
  },
  tryOnButton: {
    backgroundColor: "#000",
    padding: 12,
    borderRadius: 2,
    alignItems: "center",
    marginTop: 12
  },
  tryOnButtonText: {
    color: "#FFF",
    fontSize: 12,
    letterSpacing: 1,
    textTransform: "uppercase",
    fontWeight: "600"
  }
});
