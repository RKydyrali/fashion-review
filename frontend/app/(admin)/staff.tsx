import { router } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { AdminEmptyState, AdminField, AdminFormTitle, AdminHero, AdminOptionGroup, AdminSection, AdminStatCard, AdminStatGrid, AdminToggle } from "@/components/admin-ui";
import { BodyText, CardFrame, EditorialButton, EditorialPill, Screen, SectionLabel, editorialTheme } from "@/components/ui";
import { api } from "@/services/api";
import type { AdminUserCreate, AdminUserRead, AdminUserUpdate, LocaleCode } from "@/services/api/types";

type StaffDraft = {
  email: string;
  full_name: string;
  password: string;
  role: "client" | "franchisee" | "production";
  preferred_language: LocaleCode;
  branch_id: number | null;
  is_active: boolean;
};

const roleOptions = [
  { label: "Client", value: "client" },
  { label: "Franchisee", value: "franchisee" },
  { label: "Production", value: "production" }
] as const;

const languageOptions = [
  { label: "English", value: "en" },
  { label: "Russian", value: "ru" },
  { label: "Kazakh", value: "kk" }
] as const;

function createEmptyDraft(): StaffDraft {
  return {
    email: "",
    full_name: "",
    password: "",
    role: "client",
    preferred_language: "en",
    branch_id: null,
    is_active: true
  };
}

function draftFromUser(user: AdminUserRead): StaffDraft {
  return {
    email: user.email,
    full_name: user.full_name,
    password: "",
    role: user.role === "admin" ? "client" : user.role,
    preferred_language: user.preferred_language,
    branch_id: user.branch_id ?? null,
    is_active: user.is_active
  };
}

export default function AdminStaffScreen() {
  const queryClient = useQueryClient();
  const [searchValue, setSearchValue] = useState("");
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [draft, setDraft] = useState<StaffDraft>(createEmptyDraft());
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { data: users } = useQuery({ queryKey: ["admin-users"], queryFn: () => api.adminUsers() });
  const { data: branches } = useQuery({ queryKey: ["admin-branches"], queryFn: api.adminBranches });

  const filteredUsers = useMemo(() => {
    const normalized = searchValue.trim().toLowerCase();
    return (users ?? []).filter((user) => {
      if (user.role === "admin") {
        return false;
      }
      if (!normalized) {
        return true;
      }
      return user.email.toLowerCase().includes(normalized) || user.full_name.toLowerCase().includes(normalized);
    });
  }, [searchValue, users]);
  const selectedUser = (users ?? []).find((user) => user.id === selectedUserId) ?? null;

  const saveMutation = useMutation({
    mutationFn: async () => {
      setErrorMessage(null);
      if (selectedUserId == null) {
        const payload: AdminUserCreate = {
          email: draft.email,
          full_name: draft.full_name,
          password: draft.password,
          role: draft.role,
          preferred_language: draft.preferred_language,
          branch_id: draft.role === "franchisee" ? draft.branch_id : null
        };
        return api.adminCreateUser(payload);
      }

      const payload: AdminUserUpdate = {
        full_name: draft.full_name,
        role: draft.role,
        preferred_language: draft.preferred_language,
        is_active: draft.is_active,
        branch_id: draft.role === "franchisee" ? draft.branch_id : null
      };
      if (draft.password.trim()) {
        payload.password = draft.password;
      }
      return api.adminUpdateUser(selectedUserId, payload);
    },
    onSuccess: async (savedUser) => {
      setSelectedUserId(savedUser.id);
      setDraft(draftFromUser(savedUser));
      await queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      await queryClient.invalidateQueries({ queryKey: ["admin-branches"] });
    },
    onError: (error) => {
      setErrorMessage(error instanceof Error ? error.message : "Unable to save staff member.");
    }
  });

  const isCreateMode = selectedUserId == null;
  const availableBranches = branches ?? [];
  const franchiseCount = (filteredUsers ?? []).filter((user) => user.role === "franchisee" && user.is_active).length;
  const productionCount = (filteredUsers ?? []).filter((user) => user.role === "production" && user.is_active).length;
  const inactiveCount = (filteredUsers ?? []).filter((user) => !user.is_active).length;

  return (
    <Screen contentContainerStyle={styles.content}>
      <SectionLabel>Admin / Staff</SectionLabel>
      <AdminHero
        eyebrow="People Management"
        title="Assign staff roles without losing track of branch responsibility."
        description="This view keeps search, role changes, and account setup in one place so staff onboarding stays lightweight on mobile."
      >
        <AdminStatGrid>
          <AdminStatCard label="Visible Staff" value={String(filteredUsers.length)} note="Filtered by your current search input." tone="accent" />
          <AdminStatCard label="Franchisees" value={String(franchiseCount)} note="Each one can be tied to a single existing branch." />
          <AdminStatCard label="Production" value={String(productionCount)} note={`${inactiveCount} currently inactive accounts.`} tone={inactiveCount > 0 ? "danger" : "success"} />
        </AdminStatGrid>
      </AdminHero>

      <View style={styles.topActions}>
        <EditorialButton label="Back To Admin" inverse onPress={() => router.push("/(admin)/dashboard")} />
        <EditorialButton
          label="Start New Staff Draft"
          inverse
          onPress={() => {
            setSelectedUserId(null);
            setDraft(createEmptyDraft());
            setErrorMessage(null);
          }}
        />
      </View>

      <AdminSection
        title="Directory"
        description="Search by email or name, then tap a card to load that person into the editor below."
        style={styles.sectionGap}
      >
        <AdminField label="Search by email" value={searchValue} onChangeText={setSearchValue} placeholder="franchise@example.com" />
        {filteredUsers.length === 0 ? (
          <AdminEmptyState
            title="No staff in this view"
            description="Try a different search, or start a new draft to create a franchisee or production account."
          />
        ) : null}
        {filteredUsers.map((user) => (
          <Pressable
            key={user.id}
            style={[styles.listCard, selectedUserId === user.id ? styles.listCardActive : null]}
            onPress={() => {
              setSelectedUserId(user.id);
              setDraft(draftFromUser(user));
              setErrorMessage(null);
            }}
          >
            <View style={styles.listRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.listTitle}>{user.full_name}</Text>
                <Text style={styles.listMeta}>{user.email}</Text>
                <Text style={styles.listHint}>
                  {user.role === "franchisee"
                    ? user.branch_id
                      ? `Assigned to branch ${user.branch_id}`
                      : "Needs branch assignment"
                    : user.role === "production"
                      ? "Global production access"
                      : "Standard customer role"}
                </Text>
              </View>
              <View style={styles.listPills}>
                <EditorialPill label={user.role} strong />
                {user.branch_id ? <EditorialPill label={`branch ${user.branch_id}`} /> : null}
                <EditorialPill label={user.is_active ? "active" : "inactive"} />
              </View>
            </View>
          </Pressable>
        ))}
      </AdminSection>

      <AdminSection
        title={isCreateMode ? "Create Staff Account" : "Edit Staff Account"}
        description={isCreateMode ? "New staff accounts are created immediately with an admin-set password." : "Update role, password, language, branch assignment, or active status."}
        style={styles.sectionGap}
      >
        <CardFrame style={styles.editorHint}>
          <Text style={styles.editorHintTitle}>{isCreateMode ? "New account" : "Editing existing account"}</Text>
          <BodyText style={styles.editorHintBody}>
            {isCreateMode
              ? "Use franchisee for branch managers and production for technical staff. Client removes staff-level access."
              : "If you switch away from franchisee, branch assignment will be cleared automatically on save."}
          </BodyText>
        </CardFrame>
        <View style={styles.formGrid}>
          <AdminField
            label="Email"
            value={draft.email}
            onChangeText={(value) => setDraft((current) => ({ ...current, email: value }))}
            placeholder="staff@example.com"
            keyboardType="email-address"
          />
          <AdminField label="Full Name" value={draft.full_name} onChangeText={(value) => setDraft((current) => ({ ...current, full_name: value }))} placeholder="Staff Name" />
        </View>

        <AdminField
          label={isCreateMode ? "Password" : "New Password"}
          value={draft.password}
          onChangeText={(value) => setDraft((current) => ({ ...current, password: value }))}
          placeholder={isCreateMode ? "Required" : "Leave blank to keep"}
        />

        <AdminOptionGroup
          label="Role"
          activeValue={draft.role}
          onChange={(value) => setDraft((current) => ({ ...current, role: value as StaffDraft["role"], branch_id: value === "franchisee" ? current.branch_id : null }))}
          options={roleOptions.map((option) => ({ label: option.label, value: option.value }))}
        />

        <AdminOptionGroup
          label="Preferred Language"
          activeValue={draft.preferred_language}
          onChange={(value) => setDraft((current) => ({ ...current, preferred_language: value as LocaleCode }))}
          options={languageOptions.map((option) => ({ label: option.label, value: option.value }))}
        />

        {draft.role === "franchisee" ? (
          <AdminOptionGroup
            label="Branch Assignment"
            activeValue={draft.branch_id ? String(draft.branch_id) : ""}
            onChange={(value) => setDraft((current) => ({ ...current, branch_id: Number(value) }))}
            options={availableBranches.map((branch) => ({
              label: `${branch.code} / ${branch.city}`,
              value: String(branch.id)
            }))}
          />
        ) : null}

        {!isCreateMode ? (
          <AdminToggle
            label="Active account"
            value={draft.is_active}
            onToggle={() => setDraft((current) => ({ ...current, is_active: !current.is_active }))}
          />
        ) : null}

        {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}

        <View style={styles.actionRow}>
          <EditorialButton label={saveMutation.isPending ? "Saving" : isCreateMode ? "Create Staff" : "Save Staff"} onPress={() => saveMutation.mutate()} />
          <EditorialButton
            label="Reset Draft"
            inverse
            onPress={() => {
              setDraft(isCreateMode || !selectedUser ? createEmptyDraft() : draftFromUser(selectedUser));
              setErrorMessage(null);
            }}
          />
        </View>
      </AdminSection>
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: {
    gap: 16
  },
  pageCopy: {
    marginTop: 8
  },
  topActions: {
    gap: 10
  },
  sectionGap: {
    marginTop: 8
  },
  listCard: {
    borderWidth: 1,
    borderColor: editorialTheme.border,
    padding: 16,
    backgroundColor: editorialTheme.surfaceMuted,
    borderRadius: 2
  },
  listCardActive: {
    borderColor: editorialTheme.text,
    backgroundColor: "#F0ECE4"
  },
  listRow: {
    gap: 10,
    alignItems: "flex-start"
  },
  listTitle: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 13,
    lineHeight: 18,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  listMeta: {
    marginTop: 4,
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 13,
    lineHeight: 18,
    color: editorialTheme.textMuted
  },
  listHint: {
    marginTop: 8,
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 12,
    lineHeight: 18,
    color: editorialTheme.textSoft
  },
  listPills: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  formGrid: {
    gap: 14
  },
  editorHint: {
    backgroundColor: "#F8F4EC"
  },
  editorHintTitle: {
    fontFamily: "SpaceGrotesk_700Bold",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  editorHintBody: {
    marginTop: 8,
    fontSize: 14,
    lineHeight: 24
  },
  actionRow: {
    gap: 10
  },
  errorText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 13,
    lineHeight: 18,
    color: "#8E1F1F"
  }
});
