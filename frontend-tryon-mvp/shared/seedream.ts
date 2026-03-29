import type { GarmentOption } from "./garments";

export function buildTryOnPrompt(garment: GarmentOption) {
  return [
    "Use image 1 as the person reference and image 2 as the garment reference.",
    "Create a realistic fashion try-on image of the same person wearing the referenced garment.",
    "Preserve the person's pose and identity as much as possible.",
    "Keep the output photorealistic with natural lighting and a clean background.",
    garment.promptHint,
  ]
    .filter(Boolean)
    .join(" ");
}

export function extractGeneratedImageUrl(payload: unknown) {
  if (
    payload &&
    typeof payload === "object" &&
    "data" in payload &&
    Array.isArray(payload.data) &&
    payload.data[0] &&
    typeof payload.data[0] === "object" &&
    payload.data[0] !== null &&
    "url" in payload.data[0] &&
    typeof payload.data[0].url === "string"
  ) {
    return payload.data[0].url;
  }

  throw new Error("Seedream response did not include data[0].url");
}
