import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  renderRequests: defineTable({
    status: v.union(v.literal("pending"), v.literal("done"), v.literal("error")),
    userImageStorageId: v.id("_storage"),
    garmentId: v.string(),
    garmentImageUrl: v.string(),
    prompt: v.string(),
    resultImageUrl: v.optional(v.string()),
    errorMessage: v.optional(v.string()),
  }),
});
