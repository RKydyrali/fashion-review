import { describe, expect, it } from "vitest";

import { GARMENTS } from "./garments";
import { buildTryOnPrompt, extractGeneratedImageUrl } from "./seedream";

describe("seedream helpers", () => {
  it("builds a try-on prompt using the selected garment", () => {
    const prompt = buildTryOnPrompt(GARMENTS[0]);

    expect(prompt).toContain("image 1");
    expect(prompt).toContain("image 2");
    expect(prompt).toContain("beige trench coat");
  });

  it("extracts the generated image URL from the API response", () => {
    expect(
      extractGeneratedImageUrl({
        data: [{ url: "https://example.com/result.png" }],
      }),
    ).toBe("https://example.com/result.png");
  });

  it("throws when the API response has no image URL", () => {
    expect(() => extractGeneratedImageUrl({ data: [] })).toThrow(
      "Seedream response did not include data[0].url",
    );
  });
});
