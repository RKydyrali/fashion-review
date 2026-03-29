import { router } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { StyleSheet, Text, View } from "react-native";

import { AdminHero, AdminSection, AdminStatCard, AdminStatGrid } from "@/components/admin-ui";
import { BodyText, CardFrame, EditorialButton, EditorialPill, Screen, SectionLabel, SkeletonBlock, editorialTheme } from "@/components/ui";
import { api } from "@/services/api";
import { useAuthStore } from "@/state/auth-store";

export default function AdminHomeScreen() {
  const { data: users, isLoading: usersLoading } = useQuery({ queryKey: ["admin-users"], queryFn: () => api.adminUsers() });
  const { data: products, isLoading: productsLoading } = useQuery({ queryKey: ["admin-products"], queryFn: api.adminProducts });
  const { data: collections, isLoading: collectionsLoading } = useQuery({ queryKey: ["admin-collections"], queryFn: api.adminCollections });

  if (usersLoading || productsLoading || collectionsLoading) {
    return (
      <Screen>
        <SkeletonBlock height={16} style={{ width: 92 }} />
        <SkeletonBlock height={110} />
        <SkeletonBlock height={96} />
      </Screen>
    );
  }

  const activeStaffCount = (users ?? []).filter((user) => user.role !== "client").length;
  const franchiseCount = (users ?? []).filter((user) => user.role === "franchisee" && user.is_active).length;
  const productionCount = (users ?? []).filter((user) => user.role === "production" && user.is_active).length;
  const activeProducts = (products ?? []).filter((product) => product.is_active).length;
  const featuredCollections = (collections ?? []).filter((collection) => collection.is_featured && collection.is_active).length;

  return (
    <Screen contentContainerStyle={styles.content}>
      <SectionLabel>Admin</SectionLabel>
      <AdminHero
        eyebrow="Control Room"
        title="One place to manage staff, catalog, and publishing rhythm."
        description="The admin workspace now reads like an operations desk instead of a utility page, so role assignment and catalog work stay easier to scan on mobile."
      >
        <View style={styles.heroPills}>
          <EditorialPill label={`${franchiseCount} franchise`} strong />
          <EditorialPill label={`${productionCount} production`} />
          <EditorialPill label={`${activeProducts} live products`} />
        </View>
      </AdminHero>

      <AdminStatGrid>
        <AdminStatCard label="Active Staff" value={String(activeStaffCount)} note="Only franchisee and production roles count here." tone="accent" />
        <AdminStatCard label="Products" value={String(products?.length ?? 0)} note={`${activeProducts} currently visible in catalog.`} />
        <AdminStatCard label="Collections" value={String(collections?.length ?? 0)} note={`${featuredCollections} featured and active right now.`} tone="success" />
      </AdminStatGrid>

      <AdminSection
        title="Workspace"
        description="Each lane keeps a different kind of admin work focused, so you can jump straight into people, product data, or collection storytelling."
      >
        <CardFrame style={styles.routeCard}>
          <View style={styles.routeHeader}>
            <Text style={styles.routeTitle}>Staff Console</Text>
            <EditorialPill label="Roles" strong />
          </View>
          <BodyText style={styles.routeCopy}>Create accounts, assign franchise branches, manage passwords, and deactivate staff when needed.</BodyText>
          <EditorialButton label="Open Staff Console" onPress={() => router.push("/(admin)/staff")} style={styles.routeButton} />
        </CardFrame>

        <CardFrame style={styles.routeCard}>
          <View style={styles.routeHeader}>
            <Text style={styles.routeTitle}>Product Editor</Text>
            <EditorialPill label="Catalog" strong />
          </View>
          <BodyText style={styles.routeCopy}>Update multilingual copy, pricing, image slots, and product visibility without leaving the app.</BodyText>
          <EditorialButton label="Open Product Editor" inverse onPress={() => router.push("/(admin)/products")} style={styles.routeButton} />
        </CardFrame>

        <CardFrame style={styles.routeCard}>
          <View style={styles.routeHeader}>
            <Text style={styles.routeTitle}>Collection Studio</Text>
            <EditorialPill label="Stories" strong />
          </View>
          <BodyText style={styles.routeCopy}>Shape editorial collection pages, upload hero media, and archive collections without breaking linked products.</BodyText>
          <EditorialButton label="Open Collection Studio" inverse onPress={() => router.push("/(admin)/collections")} style={styles.routeButton} />
        </CardFrame>
      </AdminSection>

      <AdminSection title="Session" description="The seeded admin account uses the shared login screen and routes here after authentication.">
        <BodyText style={styles.sessionCopy}>Demo credentials: `admin@gmail.com` / `admin`</BodyText>
        <EditorialButton
          label="Sign Out"
          inverse
          onPress={async () => {
            const refreshToken = useAuthStore.getState().refreshToken;
            if (refreshToken) {
              try {
                await api.logout(refreshToken);
              } catch {
                // Clear locally even if the API is unavailable.
              }
            }
            await useAuthStore.getState().clearSession();
            router.replace("/login");
          }}
        />
      </AdminSection>
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: {
    gap: 16
  },
  heroPills: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  routeCard: {
    backgroundColor: editorialTheme.surfaceMuted,
    padding: 18
  },
  routeHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12
  },
  routeTitle: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  routeCopy: {
    marginTop: 10
  },
  routeButton: {
    marginTop: 14
  },
  sessionCopy: {
    marginBottom: 6
  }
});
