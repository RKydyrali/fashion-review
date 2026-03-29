import { create } from "zustand";

import type { BagItem, FavoriteItem, ProductCard } from "@/services/api/types";
import * as storage from "@/services/storage/kv";

const STYLE_STORE_KEY = "avishu_style_store";

export const BUILDER_SLOTS = ["outerwear", "tops", "bottoms"] as const;

export type BuilderSlot = (typeof BUILDER_SLOTS)[number];
type BuilderSource = "bag" | "favorite";

type BuilderProductSnapshot = Pick<
  ProductCard,
  "id" | "slug" | "name" | "display_category" | "normalized_category" | "color" | "hero_image_url" | "reference_image_url"
>;

export type TryOnPortrait = {
  uri: string;
  fileName?: string | null;
  mimeType?: string | null;
  width?: number;
  height?: number;
  fileSize?: number | null;
};

export type BuilderInventoryItem = {
  id: string;
  source: BuilderSource;
  bagItemId?: number | null;
  favoriteItemId?: number | null;
  slot: BuilderSlot;
  product: BuilderProductSnapshot;
  quantity: number;
  selectedSize?: string | null;
};

export type BuilderSession = {
  portrait: TryOnPortrait | null;
  inventory: BuilderInventoryItem[];
  activeSelections: Partial<Record<BuilderSlot, string>>;
  updatedAt?: string | null;
};

type PersistedStyleState = {
  ownerUserId: number | null;
  session: BuilderSession;
};

type StyleState = PersistedStyleState & {
  hydrated: boolean;
  bootstrap: (userId?: number | null) => Promise<void>;
  startWardrobeSession: (payload: {
    portrait: TryOnPortrait;
    bagItems: BagItem[];
    favorites: FavoriteItem[];
  }) => Promise<BuilderSession>;
  updatePortrait: (portrait: TryOnPortrait | null) => Promise<void>;
  selectSlotItem: (slot: BuilderSlot, itemId: string) => Promise<void>;
  clearSession: () => Promise<void>;
};

const SLOT_KEYWORDS: Record<BuilderSlot, string[]> = {
  outerwear: ["coat", "jacket", "blazer", "cardigan", "hoodie", "sweatshirt", "outerwear"],
  tops: ["top", "shirt", "blouse", "tee", "t-shirt", "knit", "sweater", "topwear"],
  bottoms: ["pants", "trousers", "skirt", "jeans", "shorts", "bottoms"]
};

function emptySession(): BuilderSession {
  return {
    portrait: null,
    inventory: [],
    activeSelections: {},
    updatedAt: null
  };
}

function normalizeText(value?: string | null) {
  return value?.toLowerCase().trim() ?? "";
}

function toSnapshot(product: ProductCard): BuilderProductSnapshot {
  return {
    id: product.id,
    slug: product.slug,
    name: product.name,
    display_category: product.display_category,
    normalized_category: product.normalized_category,
    color: product.color,
    hero_image_url: product.hero_image_url,
    reference_image_url: product.reference_image_url
  };
}

export function toTryOnPortrait(asset: {
  uri: string;
  fileName?: string | null;
  mimeType?: string | null;
  width?: number;
  height?: number;
  fileSize?: number | null;
}): TryOnPortrait {
  return {
    uri: asset.uri,
    fileName: asset.fileName,
    mimeType: asset.mimeType,
    width: asset.width,
    height: asset.height,
    fileSize: asset.fileSize
  };
}

export function classifyBuilderSlot(product: Pick<ProductCard, "normalized_category" | "display_category">): BuilderSlot | null {
  const candidates = [normalizeText(product.normalized_category), normalizeText(product.display_category)];

  for (const candidate of candidates) {
    for (const slot of BUILDER_SLOTS) {
      if (SLOT_KEYWORDS[slot].some((keyword) => candidate.includes(keyword))) {
        return slot;
      }
    }
  }

  return null;
}

export function buildBuilderInventory({
  bagItems,
  favorites
}: {
  bagItems: BagItem[];
  favorites: FavoriteItem[];
}): BuilderInventoryItem[] {
  const inventory: BuilderInventoryItem[] = [];
  const favoriteSeenProductIds = new Set<number>();

  for (const item of bagItems) {
    const slot = classifyBuilderSlot(item.product);
    if (!slot) {
      continue;
    }

    inventory.push({
      id: `bag-${item.id}`,
      source: "bag",
      bagItemId: item.id,
      favoriteItemId: null,
      slot,
      product: toSnapshot(item.product),
      quantity: item.quantity,
      selectedSize: item.size_label
    });
    favoriteSeenProductIds.add(item.product.id);
  }

  for (const favorite of favorites) {
    if (favoriteSeenProductIds.has(favorite.product.id)) {
      continue;
    }

    const slot = classifyBuilderSlot(favorite.product);
    if (!slot) {
      continue;
    }

    inventory.push({
      id: `favorite-${favorite.id}`,
      source: "favorite",
      bagItemId: null,
      favoriteItemId: favorite.id,
      slot,
      product: toSnapshot(favorite.product),
      quantity: 1,
      selectedSize: null
    });
  }

  return inventory;
}

function buildSelections(inventory: BuilderInventoryItem[]): BuilderSession["activeSelections"] {
  return BUILDER_SLOTS.reduce<BuilderSession["activeSelections"]>((selections, slot) => {
    const firstItem = inventory.find((item) => item.slot === slot);
    if (firstItem) {
      selections[slot] = firstItem.id;
    }
    return selections;
  }, {});
}

export function getBuilderSlotItems(session: BuilderSession, slot: BuilderSlot) {
  return session.inventory.filter((item) => item.slot === slot);
}

export function getSelectedBuilderItems(session: BuilderSession) {
  return BUILDER_SLOTS.flatMap((slot) => {
    const selectedId = session.activeSelections[slot];
    const selectedItem = selectedId ? session.inventory.find((item) => item.id === selectedId) : null;
    return selectedItem ? [selectedItem] : [];
  });
}

async function persist(state: PersistedStyleState) {
  await storage.setItem(STYLE_STORE_KEY, JSON.stringify(state));
}

export const useStyleStore = create<StyleState>((set, get) => ({
  ownerUserId: null,
  session: emptySession(),
  hydrated: false,
  bootstrap: async (userId) => {
    const stored = await storage.getItem(STYLE_STORE_KEY);
    const normalizedUserId = userId ?? null;

    if (!stored) {
      const nextState = {
        ownerUserId: normalizedUserId,
        session: emptySession()
      };
      await persist(nextState);
      set({ ...nextState, hydrated: true });
      return;
    }

    try {
      const parsed = JSON.parse(stored) as PersistedStyleState;
      if ((parsed.ownerUserId ?? null) !== normalizedUserId) {
        const resetState = {
          ownerUserId: normalizedUserId,
          session: emptySession()
        };
        await persist(resetState);
        set({ ...resetState, hydrated: true });
        return;
      }

      set({
        ownerUserId: parsed.ownerUserId ?? null,
        session: parsed.session ?? emptySession(),
        hydrated: true
      });
    } catch {
      const resetState = {
        ownerUserId: normalizedUserId,
        session: emptySession()
      };
      await persist(resetState);
      set({ ...resetState, hydrated: true });
    }
  },
  startWardrobeSession: async ({ portrait, bagItems, favorites }) => {
    const current = get();
    const inventory = buildBuilderInventory({ bagItems, favorites });
    const session: BuilderSession = {
      portrait,
      inventory,
      activeSelections: buildSelections(inventory),
      updatedAt: new Date().toISOString()
    };
    const nextState = {
      ownerUserId: current.ownerUserId,
      session
    };
    await persist(nextState);
    set({ session });
    return session;
  },
  updatePortrait: async (portrait) => {
    const current = get();
    const session: BuilderSession = {
      ...current.session,
      portrait,
      updatedAt: new Date().toISOString()
    };
    const nextState = {
      ownerUserId: current.ownerUserId,
      session
    };
    await persist(nextState);
    set({ session });
  },
  selectSlotItem: async (slot, itemId) => {
    const current = get();
    const session: BuilderSession = {
      ...current.session,
      activeSelections: {
        ...current.session.activeSelections,
        [slot]: itemId
      },
      updatedAt: new Date().toISOString()
    };
    const nextState = {
      ownerUserId: current.ownerUserId,
      session
    };
    await persist(nextState);
    set({ session });
  },
  clearSession: async () => {
    const current = get();
    const nextState = {
      ownerUserId: current.ownerUserId,
      session: emptySession()
    };
    await persist(nextState);
    set({ session: nextState.session });
  }
}));
