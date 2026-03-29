import { Link, router } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { useCallback, useRef } from "react";
import { useFocusEffect } from "@react-navigation/native";
import {
  NativeScrollEvent,
  NativeSyntheticEvent,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  useWindowDimensions,
  View
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useI18n } from "@/i18n";
import { WelcomeBackground } from "@/components/welcome-background";
import { ProductImage, editorialSerif, editorialTheme } from "@/components/ui";
import { api } from "@/services/api";
import type { ProductCard } from "@/services/api/types";

function BrandMarker({ compact }: { compact?: boolean }) {
  return (
    <View style={[styles.brandMarker, compact ? styles.brandMarkerCompact : null]}>
      <Text style={styles.brandMarkerText}>AVISHU</Text>
    </View>
  );
}

export default function HomeScreen() {
  const { t } = useI18n();
  const { width, height } = useWindowDimensions();
  const hasNavigatedRef = useRef(false);
  const { data: productsData } = useQuery({ queryKey: ["products"], queryFn: api.products });

  const pageWidth = Math.max(width, 320);
  const heroHeight = Math.max(height * 0.88, pageWidth * 1.25);
  const spotlightHeight = Math.max(pageWidth * 1.18, 360);
  const bottomSpaceHeight = Math.max(height * 0.72, 460);
  const spotlightProducts = (productsData ?? []).slice(0, 2) as ProductCard[];

  useFocusEffect(
    useCallback(() => {
      hasNavigatedRef.current = false;
    }, [])
  );

  const handleScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    if (hasNavigatedRef.current) {
      return;
    }

    const {
      contentOffset,
      contentSize,
      layoutMeasurement
    } = event.nativeEvent;
    const distanceToBottom = contentSize.height - (contentOffset.y + layoutMeasurement.height);

    if (distanceToBottom <= 72) {
      hasNavigatedRef.current = true;
      router.replace("/(tabs)/collections?mode=editorial");
    }
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={["top"]}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.screenContent}
        onScroll={handleScroll}
        scrollEventThrottle={16}
        showsVerticalScrollIndicator={false}
      >
        <View style={[styles.heroSection, { height: heroHeight }]}>
          <WelcomeBackground />
          <View style={styles.heroOverlay} />
          <View style={styles.heroBrandWrap}>
            <Text style={styles.heroBrandText}>AVISHU</Text>
          </View>
        </View>

        <BrandMarker compact />

        <ProductSpotlight product={spotlightProducts[0]} height={spotlightHeight} emptyTitle={t("home.newProductSoon", "New Product Coming Soon")} emptyCopy={t("home.addCatalogItems", "Add more catalog items in admin and they will appear here automatically.")} />

        <BrandMarker />

        <ProductSpotlight product={spotlightProducts[1]} height={spotlightHeight} emptyTitle={t("home.newProductSoon", "New Product Coming Soon")} emptyCopy={t("home.addCatalogItems", "Add more catalog items in admin and they will appear here automatically.")} />

        <View style={[styles.bottomSpace, { height: bottomSpaceHeight }]}>
          <BrandMarker />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function ProductSpotlight({ product, height, emptyTitle, emptyCopy }: { product?: ProductCard; height: number; emptyTitle: string; emptyCopy: string }) {
  if (!product) {
    return (
      <View style={[styles.mediaShell, styles.imageSection, styles.centeredMediaShell, { height }]}>
        <View style={styles.emptySpotlight}>
          <Text style={styles.emptySpotlightTitle}>{emptyTitle}</Text>
          <Text style={styles.emptySpotlightCopy}>{emptyCopy}</Text>
        </View>
      </View>
    );
  }

  const imageUri = product.hero_image_url || product.reference_image_url;

  return (
    <Link href={`/product/${product.slug}`} asChild>
      <Pressable style={({ pressed }) => [styles.spotlightCard, pressed ? styles.cardPressed : null]}>
        <View style={[styles.mediaShell, styles.imageSection, { height }]}>
          {imageUri ? <ProductImage uri={imageUri} height={height} style={styles.spotlightImage} /> : <View style={[styles.mediaFill, styles.imageFallback]} />}
          <View style={styles.spotlightOverlay} />
          <View style={styles.spotlightMeta}>
            <Text style={styles.spotlightCategory}>{product.display_category}</Text>
            <Text style={styles.spotlightTitle}>{product.name}</Text>
            <Text style={styles.spotlightSubtitle}>{product.subtitle || `${product.color} / ${product.normalized_category}`}</Text>
          </View>
        </View>
      </Pressable>
    </Link>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: editorialTheme.background
  },
  scrollView: {
    flex: 1,
    backgroundColor: editorialTheme.background
  },
  screenContent: {
    paddingHorizontal: 0,
    paddingTop: 0,
    paddingBottom: 140
  },
  mediaShell: {
    position: "relative",
    width: "100%",
    overflow: "hidden",
    backgroundColor: editorialTheme.empty
  },
  heroSection: {
    position: "relative",
    width: "100%",
    overflow: "hidden",
    backgroundColor: "#000000"
  },
  heroOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(0, 0, 0, 0.2)"
  },
  heroBrandWrap: {
    ...StyleSheet.absoluteFillObject,
    alignItems: "center",
    justifyContent: "center",
    pointerEvents: "none"
  },
  heroBrandText: {
    fontFamily: editorialSerif,
    fontSize: 40,
    lineHeight: 48,
    letterSpacing: 8,
    textTransform: "uppercase",
    color: "#FFFFFF",
    textShadowColor: "rgba(0, 0, 0, 0.45)",
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 12
  },
  imageSection: {
    backgroundColor: editorialTheme.surface
  },
  centeredMediaShell: {
    alignItems: "center",
    justifyContent: "center"
  },
  spotlightCard: {
    width: "100%"
  },
  spotlightImage: {
    borderRadius: 0
  },
  imageFallback: {
    backgroundColor: editorialTheme.empty
  },
  spotlightOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(0, 0, 0, 0.2)"
  },
  spotlightMeta: {
    position: "absolute",
    left: 18,
    right: 18,
    bottom: 20,
    gap: 8
  },
  spotlightCategory: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 2.4,
    textTransform: "uppercase",
    color: "rgba(255, 255, 255, 0.78)"
  },
  spotlightTitle: {
    fontFamily: editorialSerif,
    fontSize: 28,
    lineHeight: 32,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: "#FFFFFF"
  },
  spotlightSubtitle: {
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 14,
    lineHeight: 20,
    color: "rgba(255, 255, 255, 0.88)"
  },
  emptySpotlight: {
    paddingHorizontal: 28,
    alignItems: "center",
    justifyContent: "center",
    gap: 12
  },
  emptySpotlightTitle: {
    fontFamily: editorialSerif,
    fontSize: 28,
    lineHeight: 34,
    letterSpacing: 2,
    textTransform: "uppercase",
    color: editorialTheme.text,
    textAlign: "center"
  },
  emptySpotlightCopy: {
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 14,
    lineHeight: 24,
    color: editorialTheme.textMuted,
    textAlign: "center"
  },
  mediaFill: {
    ...StyleSheet.absoluteFillObject
  },
  brandMarker: {
    paddingTop: 18,
    paddingBottom: 28,
    alignItems: "center",
    justifyContent: "center"
  },
  brandMarkerCompact: {
    paddingTop: 14,
    paddingBottom: 18
  },
  brandMarkerText: {
    fontFamily: editorialSerif,
    fontSize: 32,
    lineHeight: 40,
    letterSpacing: 5.8,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  cardPressed: {
    opacity: 0.88
  },
  bottomSpace: {
    justifyContent: "flex-start",
    backgroundColor: editorialTheme.background
  }
});
