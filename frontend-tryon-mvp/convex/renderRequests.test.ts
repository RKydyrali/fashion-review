import { convexTest } from "convex-test";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import schema from "./schema";

describe("render request pipeline", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    process.env.SEEDREAM_API_KEY = "test-api-key";
    process.env.SEEDREAM_BASE_URL = "https://seedream.test/api/v3";
    process.env.SEEDREAM_MODEL_ID = "seedream-test-model";
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    delete process.env.SEEDREAM_API_KEY;
    delete process.env.SEEDREAM_BASE_URL;
    delete process.env.SEEDREAM_MODEL_ID;
  });

  it("creates a pending render request and stores the finished image URL", async () => {
    const modules = import.meta.glob("./**/*.*s");
    const t = convexTest({ schema, modules });

    const storedUserImageId = await t.run(async (ctx) =>
      ctx.storage.store(new Blob(["user-photo"], { type: "image/jpeg" })),
    );

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          data: [{ url: "https://example.com/generated-look.png" }],
        }),
      }),
    );

    const { api } = await import("./_generated/api");

    const requestId = await t.mutation(api.renderRequests.createRenderRequest, {
      garmentId: "beige-trench",
      garmentImageUrl: "https://example.com/garments/trench.jpg",
      userImageStorageId: storedUserImageId,
    });

    const pendingRequest = await t.query(api.renderRequests.getRenderRequest, {
      requestId,
    });

    expect(pendingRequest?.status).toBe("pending");
    expect(pendingRequest?.resultImageUrl).toBeUndefined();

    await t.finishAllScheduledFunctions(() => {
      vi.runAllTimers();
    });

    const completedRequest = await t.query(api.renderRequests.getRenderRequest, {
      requestId,
    });

    expect(completedRequest).toMatchObject({
      id: requestId,
      status: "done",
      garmentLabel: "Beige Trench Coat",
      resultImageUrl: "https://example.com/generated-look.png",
    });
  });

  it("marks the render request as error when the image API fails", async () => {
    const modules = import.meta.glob("./**/*.*s");
    const t = convexTest({ schema, modules });

    const storedUserImageId = await t.run(async (ctx) =>
      ctx.storage.store(new Blob(["user-photo"], { type: "image/jpeg" })),
    );

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        text: async () => "seedream exploded",
      }),
    );

    const { api } = await import("./_generated/api");

    const requestId = await t.mutation(api.renderRequests.createRenderRequest, {
      garmentId: "black-tshirt",
      garmentImageUrl: "https://example.com/garments/black-tee.jpg",
      userImageStorageId: storedUserImageId,
    });

    await t.finishAllScheduledFunctions(() => {
      vi.runAllTimers();
    });

    const failedRequest = await t.query(api.renderRequests.getRenderRequest, {
      requestId,
    });

    expect(failedRequest?.status).toBe("error");
    expect(failedRequest?.errorMessage).toContain("Seedream request failed");
  });
});
