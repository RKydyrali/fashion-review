import { apiFetch } from "./client";
import { Platform } from "react-native";
import type {
  AdminBranchSummary,
  AdminCollectionCreate,
  AdminCollectionRead,
  AdminCollectionUpdate,
  AdminMediaUpload,
  AdminProductCreate,
  AdminProductTranslationGenerateRequest,
  AdminProductTranslationGenerateResponse,
  AdminProductRead,
  AdminProductUpdate,
  AdminUserCreate,
  AdminUserRead,
  AdminUserUpdate,
  AuthSession,
  BagSummary,
  CollectionSummary,
  FavoriteItem,
  Feed,
  FranchiseSales,
  FranchiseSettings,
  FranchiseSettingsUpdate,
  Order,
  PreorderBatch,
  ProductCard,
  ProductDetail,
  ProductionShiftReport,
  ProductionShiftStatus,
  SelectedPreorderSubmitRequest,
  SizeChart,
  SizeRecommendation,
  TryOnJob,
  TryOnSession,
  UploadableFile,
  User,
  WardrobeItemRead,
  WardrobeOutfitRead,
  WardrobeSummary
} from "./types";

async function buildUploadForm(file: UploadableFile) {
  const formData = new FormData();

  if (Platform.OS === "web") {
    const response = await fetch(file.uri);
    const blob = await response.blob();
    formData.append("file", blob, file.name);
    return formData;
  }

  formData.append(
    "file",
    {
      uri: file.uri,
      name: file.name,
      type: file.type
    } as never
  );
  return formData;
}

export const api = {
  signup: (payload: { email: string; full_name: string; password: string; preferred_language: string }) =>
    apiFetch<AuthSession>("/api/v1/auth/signup", { method: "POST", auth: false, body: JSON.stringify(payload) }),
  login: async (email: string, password: string) => {
    const body = new URLSearchParams();
    body.append("username", email);
    body.append("password", password);
    return apiFetch<AuthSession>("/api/v1/auth/login", {
      method: "POST",
      auth: false,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString()
    });
  },
  logout: (refreshToken: string) =>
    apiFetch<void>("/api/v1/auth/logout", { method: "POST", body: JSON.stringify({ refresh_token: refreshToken }) }),
  me: () => apiFetch<User>("/api/v1/auth/me"),
  updateProfile: (payload: Record<string, unknown>) => apiFetch<User>("/api/v1/auth/me", { method: "PATCH", body: JSON.stringify(payload) }),
  feed: () => apiFetch<Feed>("/api/v1/feed", { auth: false }),
  products: () => apiFetch<ProductCard[]>("/api/v1/products", { auth: false }),
  collections: () => apiFetch<CollectionSummary[]>("/api/v1/collections", { auth: false }),
  product: (slug: string) => apiFetch<ProductDetail>(`/api/v1/products/${slug}`, { auth: false }),
  sizeChart: (chartId: number) => apiFetch<SizeChart>(`/api/v1/size-charts/${chartId}`, { auth: false }),
  sizeRecommend: (payload: Record<string, unknown>) => apiFetch<SizeRecommendation>("/api/v1/sizes/recommend", { method: "POST", body: JSON.stringify(payload) }),
  favorites: () => apiFetch<FavoriteItem[]>("/api/v1/client/favorites"),
  addFavorite: (productId: number) => apiFetch<FavoriteItem>("/api/v1/client/favorites", { method: "POST", body: JSON.stringify({ product_id: productId }) }),
  removeFavorite: (productId: number) => apiFetch<void>(`/api/v1/client/favorites/${productId}`, { method: "DELETE" }),
  bag: () => apiFetch<BagSummary>("/api/v1/client/bag/items"),
  addBagItem: (payload: { product_id: number; size_label: string; quantity: number }) =>
    apiFetch("/api/v1/client/bag/items", { method: "POST", body: JSON.stringify(payload) }),
  updateBagItem: (itemId: number, payload: { size_label?: string; quantity?: number }) =>
    apiFetch(`/api/v1/client/bag/items/${itemId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteBagItem: (itemId: number) => apiFetch<void>(`/api/v1/client/bag/items/${itemId}`, { method: "DELETE" }),
  submitPreorder: (delivery_city?: string) =>
    apiFetch<PreorderBatch>("/api/v1/client/preorders/submit", { method: "POST", body: JSON.stringify({ delivery_city }) }),
  submitSelectedPreorder: (payload: SelectedPreorderSubmitRequest) =>
    apiFetch<PreorderBatch>("/api/v1/client/preorders/submit-selected", { method: "POST", body: JSON.stringify(payload) }),
  preorders: () => apiFetch<PreorderBatch[]>("/api/v1/client/preorders"),
  orders: () => apiFetch<Order[]>("/api/v1/client/orders"),
  pickupOrder: (orderId: number) => apiFetch<Order>(`/api/v1/client/orders/${orderId}/pickup`, { method: "POST" }),
  franchiseOrders: () => apiFetch<Order[]>("/api/v1/franchise/orders"),
  franchiseApproveOrder: (orderId: number) =>
    apiFetch<Order>(`/api/v1/franchise/orders/${orderId}/approve`, { method: "POST" }),
  franchiseRejectOrder: (orderId: number, reason: string) =>
    apiFetch<Order>(`/api/v1/franchise/orders/${orderId}/reject`, { method: "POST", body: JSON.stringify({ reason }) }),
  franchiseSettings: () => apiFetch<FranchiseSettings>("/api/v1/franchise/settings"),
  updateFranchiseSettings: (payload: FranchiseSettingsUpdate) =>
    apiFetch<FranchiseSettings>("/api/v1/franchise/settings", { method: "PATCH", body: JSON.stringify(payload) }),
  franchiseSales: (period: string) => apiFetch<FranchiseSales>(`/api/v1/franchise/sales?period=${period}`),
  productionQueue: () => apiFetch<Order[]>("/api/v1/production/queue"),
  productionShiftStatus: () => apiFetch<ProductionShiftStatus>("/api/v1/production/shift-status"),
  productionStartShift: (shiftType: string) => 
    apiFetch<ProductionShiftStatus>("/api/v1/production/shift/start", { method: "POST", body: JSON.stringify({ shift_type: shiftType }) }),
  productionEndShift: () => apiFetch<ProductionShiftReport>("/api/v1/production/shift/end", { method: "POST" }),
  productionUpdateOrderStatus: (orderId: number, status: string) =>
    apiFetch<Order>(`/api/v1/production/orders/${orderId}/status`, { method: "POST", body: JSON.stringify({ status }) }),
  adminUsers: (query?: string) => apiFetch<AdminUserRead[]>(`/api/v1/admin/users${query ? `?query=${encodeURIComponent(query)}` : ""}`),
  adminCreateUser: (payload: AdminUserCreate) => apiFetch<AdminUserRead>("/api/v1/admin/users", { method: "POST", body: JSON.stringify(payload) }),
  adminUpdateUser: (userId: number, payload: AdminUserUpdate) =>
    apiFetch<AdminUserRead>(`/api/v1/admin/users/${userId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  adminBranches: () => apiFetch<AdminBranchSummary[]>("/api/v1/admin/branches"),
  adminProducts: () => apiFetch<AdminProductRead[]>("/api/v1/admin/products"),
  adminTranslateProductFromEnglish: (payload: AdminProductTranslationGenerateRequest) =>
    apiFetch<AdminProductTranslationGenerateResponse>("/api/v1/admin/products/translate", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  adminCreateProduct: (payload: AdminProductCreate) =>
    apiFetch<AdminProductRead>("/api/v1/admin/products", { method: "POST", body: JSON.stringify(payload) }),
  adminUpdateProduct: (productId: number, payload: AdminProductUpdate) =>
    apiFetch<AdminProductRead>(`/api/v1/admin/products/${productId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  adminArchiveProduct: (productId: number) => apiFetch<AdminProductRead>(`/api/v1/admin/products/${productId}`, { method: "DELETE" }),
  adminRestoreProduct: (productId: number) => apiFetch<AdminProductRead>(`/api/v1/admin/products/${productId}/restore`, { method: "POST" }),
  adminDeleteProductPermanently: (productId: number) => apiFetch<void>(`/api/v1/admin/products/${productId}/permanent`, { method: "DELETE" }),
  adminCollections: () => apiFetch<AdminCollectionRead[]>("/api/v1/admin/collections"),
  adminCreateCollection: (payload: AdminCollectionCreate) =>
    apiFetch<AdminCollectionRead>("/api/v1/admin/collections", { method: "POST", body: JSON.stringify(payload) }),
  adminUpdateCollection: (collectionId: number, payload: AdminCollectionUpdate) =>
    apiFetch<AdminCollectionRead>(`/api/v1/admin/collections/${collectionId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  adminArchiveCollection: (collectionId: number) =>
    apiFetch<AdminCollectionRead>(`/api/v1/admin/collections/${collectionId}`, { method: "DELETE" }),
  adminRestoreCollection: (collectionId: number) =>
    apiFetch<AdminCollectionRead>(`/api/v1/admin/collections/${collectionId}/restore`, { method: "POST" }),
  adminUploadProductHeroImage: async (file: UploadableFile) =>
    apiFetch<AdminMediaUpload>("/api/v1/admin/uploads/products/hero-image", { method: "POST", body: await buildUploadForm(file), headers: {} }),
  adminUploadProductReferenceImage: async (file: UploadableFile) =>
    apiFetch<AdminMediaUpload>("/api/v1/admin/uploads/products/reference-image", { method: "POST", body: await buildUploadForm(file), headers: {} }),
  adminUploadProductGalleryImage: async (file: UploadableFile) =>
    apiFetch<AdminMediaUpload>("/api/v1/admin/uploads/products/gallery-image", { method: "POST", body: await buildUploadForm(file), headers: {} }),
  adminUploadCollectionHeroImage: async (file: UploadableFile) =>
    apiFetch<AdminMediaUpload>("/api/v1/admin/uploads/collections/hero-image", { method: "POST", body: await buildUploadForm(file), headers: {} }),
  adminUploadCollectionCoverImage: async (file: UploadableFile) =>
    apiFetch<AdminMediaUpload>("/api/v1/admin/uploads/collections/cover-image", { method: "POST", body: await buildUploadForm(file), headers: {} }),
  createTryOn: (formData: FormData) =>
    apiFetch<TryOnJob>("/api/v1/ai/try-on/jobs", {
      method: "POST",
      body: formData,
      headers: {}
    }),
  getTryOn: (jobId: number) => apiFetch<TryOnJob>(`/api/v1/ai/try-on/jobs/${jobId}`),
  createTryOnSession: (formData: FormData) =>
    apiFetch<TryOnSession>("/api/v1/try-on/sessions", {
      method: "POST",
      body: formData,
      headers: {}
    }),
  getTryOnSession: (sessionId: number) => apiFetch<TryOnSession>(`/api/v1/try-on/sessions/${sessionId}`),
  wardrobeItems: () => apiFetch<WardrobeItemRead[]>("/api/v1/client/wardrobe/items"),
  addWardrobeItem: (payload: { product_id: number; size_label: string; color?: string; fit_notes?: string }) =>
    apiFetch<WardrobeItemRead>("/api/v1/client/wardrobe/items", { method: "POST", body: JSON.stringify(payload) }),
  updateWardrobeItem: (itemId: number, payload: { size_label?: string; color?: string; fit_notes?: string }) =>
    apiFetch<WardrobeItemRead>(`/api/v1/client/wardrobe/items/${itemId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteWardrobeItem: (itemId: number) => apiFetch<void>(`/api/v1/client/wardrobe/items/${itemId}`, { method: "DELETE" }),
  wardrobeOutfits: () => apiFetch<WardrobeOutfitRead[]>("/api/v1/client/wardrobe/outfits"),
  createWardrobeOutfit: (payload: { name: string; wardrobe_item_ids: number[] }) =>
    apiFetch<WardrobeOutfitRead>("/api/v1/client/wardrobe/outfits", { method: "POST", body: JSON.stringify(payload) }),
  deleteWardrobeOutfit: (outfitId: number) => apiFetch<void>(`/api/v1/client/wardrobe/outfits/${outfitId}`, { method: "DELETE" }),
  wardrobeSummary: () => apiFetch<WardrobeSummary>("/api/v1/client/wardrobe/summary")
};
