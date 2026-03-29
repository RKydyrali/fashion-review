import type { UserRole } from "@/services/api/types";

type RoutePath = "/(admin)/dashboard" | "/franchise" | "/production" | "/(tabs)/home" | "/welcome";

export function routeForRole(role?: UserRole | null): RoutePath {
  switch (role) {
    case "admin":
      return "/(admin)/dashboard";
    case "franchisee":
      return "/franchise";
    case "production":
      return "/production";
    case "client":
    default:
      return "/(tabs)/home";
  }
}

export function isClientRole(role?: UserRole | null) {
  return role === "client" || role == null;
}
