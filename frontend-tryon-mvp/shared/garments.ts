export type GarmentOption = {
  id: string;
  label: string;
  imageUrl: string;
  promptHint?: string;
};

export const GARMENTS: GarmentOption[] = [
  {
    id: "beige-trench",
    label: "Beige Trench Coat",
    imageUrl:
      "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=800&q=80",
    promptHint:
      "Dress the person in the beige trench coat from the garment reference image.",
  },
  {
    id: "black-tshirt",
    label: "Black T-Shirt",
    imageUrl:
      "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=800&q=80",
    promptHint:
      "Dress the person in the black t-shirt from the garment reference image.",
  },
  {
    id: "denim-jacket",
    label: "Denim Jacket",
    imageUrl:
      "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=800&q=80",
    promptHint:
      "Dress the person in the denim jacket from the garment reference image.",
  },
];

export function getGarmentById(garmentId: string) {
  return GARMENTS.find((garment) => garment.id === garmentId);
}
