import { v } from "convex/values";

import { internal } from "./_generated/api";
import {
  internalAction,
  internalMutation,
  internalQuery,
  mutation,
  query,
} from "./_generated/server";
import { getGarmentById } from "../shared/garments";
import {
  buildTryOnPrompt,
  extractGeneratedImageUrl,
} from "../shared/seedream";

const DEFAULT_MODEL_ID = "seedream-4-5-251128";
const DEFAULT_BASE_URL = "https://ark.ap-southeast.bytepluses.com/api/v3";

function getRequiredEnv(name: string) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

export const generateUploadUrl = mutation({
  args: {},
  handler: async (ctx) => {
    return ctx.storage.generateUploadUrl();
  },
});

export const createRenderRequest = mutation({
  args: {
    garmentId: v.string(),
    garmentImageUrl: v.string(),
    userImageStorageId: v.id("_storage"),
  },
  handler: async (ctx, args) => {
    const garment = getGarmentById(args.garmentId);
    if (!garment) {
      throw new Error(`Unknown garment: ${args.garmentId}`);
    }

    const prompt = buildTryOnPrompt(garment);

    const requestId = await ctx.db.insert("renderRequests", {
      garmentId: args.garmentId,
      garmentImageUrl: args.garmentImageUrl,
      prompt,
      status: "pending",
      userImageStorageId: args.userImageStorageId,
    });

    await ctx.scheduler.runAfter(0, internal.renderRequests.runSeedreamRender, {
      requestId,
    });

    return requestId;
  },
});

export const getRenderRequestForAction = internalQuery({
  args: {
    requestId: v.id("renderRequests"),
  },
  handler: async (ctx, args) => {
    const request = await ctx.db.get(args.requestId);
    if (!request) {
      throw new Error("Render request not found");
    }

    const userImageUrl = await ctx.storage.getUrl(request.userImageStorageId);
    if (!userImageUrl) {
      throw new Error("Uploaded user image URL could not be resolved");
    }

    return {
      garmentId: request.garmentId,
      garmentImageUrl: request.garmentImageUrl,
      prompt: request.prompt,
      userImageUrl,
    };
  },
});

export const getRenderRequest = query({
  args: {
    requestId: v.id("renderRequests"),
  },
  handler: async (ctx, args) => {
    const request = await ctx.db.get(args.requestId);
    if (!request) {
      return null;
    }

    const garment = getGarmentById(request.garmentId);
    const userImageUrl = await ctx.storage.getUrl(request.userImageStorageId);

    return {
      errorMessage: request.errorMessage,
      garmentLabel: garment?.label ?? request.garmentId,
      id: request._id,
      resultImageUrl: request.resultImageUrl,
      status: request.status,
      userImageUrl: userImageUrl ?? undefined,
    };
  },
});

export const markRenderRequestDone = internalMutation({
  args: {
    requestId: v.id("renderRequests"),
    resultImageUrl: v.string(),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.requestId, {
      resultImageUrl: args.resultImageUrl,
      status: "done",
    });
  },
});

export const markRenderRequestError = internalMutation({
  args: {
    errorMessage: v.string(),
    requestId: v.id("renderRequests"),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.requestId, {
      errorMessage: args.errorMessage,
      status: "error",
    });
  },
});

export const runSeedreamRender = internalAction({
  args: {
    requestId: v.id("renderRequests"),
  },
  handler: async (ctx, args) => {
    try {
      const request = await ctx.runQuery(
        internal.renderRequests.getRenderRequestForAction,
        {
          requestId: args.requestId,
        },
      );

      const apiKey = getRequiredEnv("SEEDREAM_API_KEY");
      const model = process.env.SEEDREAM_MODEL_ID || DEFAULT_MODEL_ID;
      const baseUrl = process.env.SEEDREAM_BASE_URL || DEFAULT_BASE_URL;

      const response = await fetch(`${baseUrl}/images/generations`, {
        body: JSON.stringify({
          image_urls: [request.userImageUrl, request.garmentImageUrl],
          model,
          prompt: request.prompt,
          response_format: "url",
          size: "1024x1024",
          watermark: false,
        }),
        headers: {
          Authorization: `Bearer ${apiKey}`,
          "Content-Type": "application/json",
        },
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(
          `Seedream request failed (${response.status}): ${await response.text()}`,
        );
      }

      const payload = await response.json();
      const resultImageUrl = extractGeneratedImageUrl(payload);

      await ctx.runMutation(internal.renderRequests.markRenderRequestDone, {
        requestId: args.requestId,
        resultImageUrl,
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unknown Seedream error";

      await ctx.runMutation(internal.renderRequests.markRenderRequestError, {
        errorMessage: message,
        requestId: args.requestId,
      });
    }
  },
});
