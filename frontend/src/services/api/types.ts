export type LocaleCode = "en" | "ru" | "kk";
export type UserRole = "admin" | "client" | "franchisee" | "production";

export type Money = {
  amount_minor: number;
  currency: string;
  formatted: string;
};

export type PriceBreakdown = {
  base_price: Money;
  tailoring_adjustment: Money;
  total_price: Money;
  adjustment_label?: string | null;
};

export type UserBodyProfile = {
  height_cm?: number | null;
  weight_kg?: number | null;
  chest_cm?: number | null;
  waist_cm?: number | null;
  hips_cm?: number | null;
  preferred_fit?: "regular" | "oversized" | "slim" | null;
  alpha_size?: string | null;
  top_size?: string | null;
  bottom_size?: string | null;
  dress_size?: string | null;
};

export type User = {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  preferred_language: LocaleCode;
  is_active: boolean;
  branch_id?: number | null;
  body_profile?: UserBodyProfile | null;
};

export type AuthSession = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
};

export type ProductCard = {
  id: number;
  sku: string;
  slug: string;
  name: string;
  description?: string | null;
  subtitle?: string | null;
  display_category: string;
  normalized_category: string;
  season_tags: string[];
  color: string;
  base_price?: number | null;
  currency?: string | null;
  hero_image_url?: string | null;
  reference_image_url?: string | null;
  is_available: boolean;
  is_active: boolean;
  available_sizes?: string[];
  price_breakdown?: {
    base_price: Money;
    tailoring_adjustment: Money;
    total_price: Money;
  };
};

export type ProductSizeOption = {
  size_label: string;
  is_available: boolean;
  price_breakdown: PriceBreakdown;
};

export type ProductDetail = ProductCard & {
  long_description?: string | null;
  fabric_notes?: string | null;
  care_notes?: string | null;
  preorder_note?: string | null;
  collection_slug?: string | null;
  gallery_image_urls: string[];
  size_chart_id?: number | null;
  price_breakdown: PriceBreakdown;
  size_options: ProductSizeOption[];
};

export type CollectionSummary = {
  id: number;
  slug: string;
  eyebrow: string;
  title: string;
  summary: string;
  hero_image_url: string;
  cover_image_url: string;
  is_featured: boolean;
  products: ProductCard[];
};

export type FeedSection = {
  slug: string;
  title: string;
  eyebrow: string;
  products: ProductCard[];
};

export type Feed = {
  hero: {
    title: string;
    subtitle: string;
    image_url: string;
    collection_slug?: string | null;
  };
  collections: CollectionSummary[];
  sections: FeedSection[];
};

export type SizeChart = {
  id?: number | null;
  name: string;
  sizes: {
    size_label: string;
    chest_min_cm: number;
    chest_max_cm: number;
    waist_min_cm: number;
    waist_max_cm: number;
    hips_min_cm: number;
    hips_max_cm: number;
  }[];
};

export type SizeRecommendation = {
  recommended_size: string;
  base_size: string;
  confidence: "high" | "medium" | "low";
  confidence_score: number;
  match_method: string;
  fit_type: "regular" | "oversized" | "slim";
  warnings: string[];
  matched_sizes_by_measurement: Record<string, string | null>;
};

export type FavoriteItem = {
  id: number;
  product: ProductCard;
};

export type BagItem = {
  id: number;
  product: ProductCard;
  size_label: string;
  quantity: number;
  price_breakdown: PriceBreakdown;
  line_total: Money;
};

export type BagSummary = {
  items: BagItem[];
  subtotal: Money;
  total_adjustments: Money;
  grand_total: Money;
};

export type Order = {
  id: number;
  client_id: number;
  product_id: number;
  branch_id: number;
  preorder_batch_id?: number | null;
  delivery_city?: string | null;
  size_label?: string | null;
  quantity: number;
  unit_price?: Money | null;
  price_breakdown?: PriceBreakdown | null;
  line_total?: Money | null;
  branch_attempt_count: number;
  current_deadline_at?: string | null;
  current_deadline_stage?: string | null;
  cancellation_reason?: string | null;
  escalation_reason?: string | null;
  status: string;
  events: Array<{
    id: number;
    order_id: number;
    actor_user_id?: number | null;
    event_type: string;
    from_status?: string | null;
    to_status: string;
    note?: string | null;
  }>;
  product?: {
    id: number;
    name: string;
    hero_image_url?: string | null;
    color: string;
  };
};

export type PreorderBatch = {
  id: number;
  client_id: number;
  delivery_city?: string | null;
  item_count: number;
  total_price: Money;
  currency: string;
  status: string;
  created_at: string;
  orders: Order[];
};

export type SelectedPreorderSubmitRequest = {
  bag_item_ids: number[];
  delivery_city?: string | null;
};

export type TryOnJob = {
  id: number;
  status: string;
  product_id: number;
  fit_class: string;
  fit_reason: string;
  source_image_url: string;
  result_image_url?: string | null;
  error_message?: string | null;
};

export type TryOnSession = {
  id: number;
  status: string;
  source_image_url: string;
  rendered_image_url?: string | null;
  product_ids: number[];
  attempt_count: number;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
};

export type LocalizedProductContent = {
  name: string;
  description?: string | null;
  subtitle?: string | null;
  long_description?: string | null;
  fabric_notes?: string | null;
  care_notes?: string | null;
  preorder_note?: string | null;
  display_category: string;
};

export type LocalizedCollectionContent = {
  title: string;
  summary: string;
  eyebrow: string;
};

export type LocalizedProductContentMap = {
  en: LocalizedProductContent;
  ru: LocalizedProductContent;
  kk: LocalizedProductContent;
};

export type LocalizedCollectionContentMap = {
  en: LocalizedCollectionContent;
  ru: LocalizedCollectionContent;
  kk: LocalizedCollectionContent;
};

export type AdminBranchSummary = {
  id: number;
  name: string;
  code: string;
  city: string;
  manager_user_id?: number | null;
};

export type AdminUserRead = {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  preferred_language: LocaleCode;
  is_active: boolean;
  branch_id?: number | null;
};

export type AdminUserCreate = {
  email: string;
  full_name: string;
  password: string;
  role: Exclude<UserRole, "admin">;
  preferred_language?: LocaleCode;
  branch_id?: number | null;
};

export type AdminUserUpdate = {
  full_name?: string;
  password?: string;
  role?: Exclude<UserRole, "admin">;
  preferred_language?: LocaleCode;
  is_active?: boolean;
  branch_id?: number | null;
};

export type AdminProductRead = {
  id: number;
  sku: string;
  slug: string;
  normalized_category: string;
  season_tags: string[];
  color: string;
  base_price_minor: number;
  currency: string;
  collection_slug?: string | null;
  hero_image_url?: string | null;
  reference_image_url?: string | null;
  gallery_image_urls: string[];
  available_sizes: string[];
  size_chart_id?: number | null;
  editorial_rank: number;
  is_featured: boolean;
  is_available: boolean;
  is_active: boolean;
  translations: LocalizedProductContentMap;
};

export type AdminProductCreate = {
  sku: string;
  slug: string;
  normalized_category: string;
  season_tags: string[];
  color: string;
  base_price_minor: number;
  currency: string;
  collection_slug?: string | null;
  hero_image_url?: string | null;
  reference_image_url?: string | null;
  gallery_image_urls: string[];
  available_sizes: string[];
  size_chart_id?: number | null;
  editorial_rank: number;
  is_featured: boolean;
  is_available: boolean;
  is_active: boolean;
  translations: LocalizedProductContentMap;
};

export type AdminProductUpdate = Partial<AdminProductCreate>;

export type AdminProductTranslationGenerateRequest = {
  english: LocalizedProductContent;
  normalized_category?: string | null;
  color?: string | null;
  season_tags: string[];
};

export type AdminProductTranslationGenerateResponse = {
  ai_status: "completed" | "fallback" | "disabled";
  provider_name?: string | null;
  model_name?: string | null;
  prompt_template_version: string;
  used_fallback: boolean;
  error_message?: string | null;
  translations?: {
    ru: LocalizedProductContent;
    kk: LocalizedProductContent;
  } | null;
};

export type AdminCollectionRead = {
  id: number;
  slug: string;
  hero_image_url: string;
  cover_image_url: string;
  sort_order: number;
  is_featured: boolean;
  is_active: boolean;
  translations: LocalizedCollectionContentMap;
};

export type AdminCollectionCreate = {
  slug: string;
  hero_image_url: string;
  cover_image_url: string;
  sort_order: number;
  is_featured: boolean;
  is_active: boolean;
  translations: LocalizedCollectionContentMap;
};

export type AdminCollectionUpdate = Partial<AdminCollectionCreate>;

export type AdminMediaUpload = {
  url: string;
  relative_path: string;
};

export type UploadableFile = {
  uri: string;
  name: string;
  type: string;
};

export type FranchiseSettings = {
  branch_id: number;
  branch_name: string;
  approval_mode: "auto" | "manual";
  auto_approve_until?: string | null;
  preferred_language: LocaleCode;
};

export type FranchiseSettingsUpdate = {
  approval_mode?: "auto" | "manual";
  preferred_language?: LocaleCode;
};

export type FranchiseSales = {
  period: string;
  start_date: string;
  end_date: string;
  total_revenue: Money;
  order_count: number;
  avg_order_value: Money;
  daily_breakdown: Array<{
    date: string;
    revenue: number;
    orders: number;
  }>;
  top_products: Array<{
    product_name: string;
    quantity_sold: number;
    revenue: number;
  }>;
};

export type ProductionShiftStatus = {
  is_open: boolean;
  shift_type?: "morning" | "afternoon" | null;
  shift_started_at?: string | null;
  shift_duration_minutes: number;
  orders_started_today: number;
  orders_completed_today: number;
  orders_in_progress: number;
};

export type ProductionShiftReport = {
  shift_date: string;
  shift_type: string;
  shift_started_at: string;
  shift_ended_at: string;
  duration_minutes: number;
  orders_started: number;
  orders_completed: number;
  orders_incomplete: number;
};

export type WardrobeItemRead = {
  id: number;
  product_id: number;
  size_label: string;
  color: string | null;
  fit_notes: string | null;
  is_from_order: boolean;
  order_id: number | null;
  product_name: string;
  product_image: string | null;
  product_category: string;
  product_color: string;
  product_price_minor: number;
};

export type WardrobeOutfitRead = {
  id: number;
  name: string;
  wardrobe_item_ids: number[];
  items: WardrobeItemRead[];
};

export type WardrobeSummary = {
  items: WardrobeItemRead[];
  outfits: WardrobeOutfitRead[];
  total_items: number;
  total_outfits: number;
};
