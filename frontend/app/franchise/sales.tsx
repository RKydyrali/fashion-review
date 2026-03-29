import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Pressable, StyleSheet, Text, View, Dimensions } from "react-native";

import {
  BodyText,
  CardFrame,
  EditorialButton,
  EditorialPill,
  EditorialTitle,
  MetricTile,
  Screen,
  SectionLabel,
  SkeletonBlock,
  editorialSerif,
  editorialTheme
} from "@/components/ui";
import { api } from "@/services/api";
import { useAuthStore } from "@/state/auth-store";

type PeriodType = "today" | "week" | "month" | "year";

const periodLabels: Record<PeriodType, string> = {
  today: "Today",
  week: "This Week",
  month: "This Month",
  year: "This Year"
};

function formatCurrency(amount?: number | null, currency: string = "KZT"): string {
  if (!amount) return "0 ₸";
  return `${(amount / 100).toLocaleString()} ${currency}`;
}

function SimpleBarChart({ data }: { data: Array<{ label: string; value: number; maxValue: number }> }) {
  const screenWidth = Dimensions.get("window").width - 80;
  const barWidth = Math.max(20, (screenWidth - (data.length - 1) * 8) / data.length);

  return (
    <View style={chartStyles.container}>
      {data.map((item, index) => {
        const height = item.maxValue > 0 ? (item.value / item.maxValue) * 120 : 0;
        return (
          <View key={index} style={chartStyles.barWrapper}>
            <View style={chartStyles.barContainer}>
              <View
                style={[
                  chartStyles.bar,
                  { height: Math.max(4, height), width: barWidth - 4 }
                ]}
              />
            </View>
            <Text style={chartStyles.barLabel}>{item.label}</Text>
          </View>
        );
      })}
    </View>
  );
}

const chartStyles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "flex-end",
    height: 150,
    paddingTop: 10
  },
  barWrapper: {
    flex: 1,
    alignItems: "center"
  },
  barContainer: {
    height: 120,
    justifyContent: "flex-end"
  },
  bar: {
    backgroundColor: editorialTheme.text,
    borderRadius: 2
  },
  barLabel: {
    marginTop: 8,
    fontSize: 10,
    color: editorialTheme.textSoft,
    textTransform: "uppercase",
    letterSpacing: 0.5
  }
});

export default function FranchiseSales() {
  const { accessToken, user } = useAuthStore();
  const queryEnabled = Boolean(accessToken) && user?.role === "franchisee";
  const [selectedPeriod, setSelectedPeriod] = useState<PeriodType>("week");

  const { data: salesData, isLoading } = useQuery({
    queryKey: ["franchise-sales", selectedPeriod],
    queryFn: () => api.franchiseSales(selectedPeriod),
    enabled: queryEnabled
  });

  const periods: PeriodType[] = ["today", "week", "month", "year"];

  const chartData = salesData?.daily_breakdown.slice(-7).map((day) => ({
    label: new Date(day.date).toLocaleDateString("en", { weekday: "short" }).slice(0, 2),
    value: day.revenue,
    maxValue: Math.max(...salesData.daily_breakdown.map((d) => d.revenue), 1)
  })) ?? [];

  const handleExportCSV = async () => {
    if (!salesData) return;
    const csvContent = [
      "Date,Orders,Revenue",
      ...salesData.daily_breakdown.map(
        (d) => `${d.date},${d.orders},${d.revenue}`
      ),
      `Total,${salesData.order_count},${salesData.total_revenue.amount_minor}`
    ].join("\n");

    console.log("CSV Export:", csvContent);
    alert("CSV exported! Check console for content.");
  };

  const handleExportPDF = async () => {
    if (!salesData) return;
    alert("PDF export would generate a PDF report with charts and data.");
  };

  return (
    <Screen contentContainerStyle={styles.screenContent}>
      <SectionLabel>Franchise</SectionLabel>
      <EditorialTitle style={styles.pageTitle}>Sales Report</EditorialTitle>
      <BodyText style={styles.pageCopy}>
        Track your branch performance and export reports
      </BodyText>

      <View style={styles.filterRow}>
        {periods.map((period) => {
          const isActive = selectedPeriod === period;
          return (
            <Pressable
              key={period}
              style={({ pressed }) => [
                styles.filterPill,
                isActive ? styles.filterPillActive : null,
                pressed ? styles.filterPillPressed : null
              ]}
              onPress={() => setSelectedPeriod(period)}
            >
              <Text style={[styles.filterPillText, isActive ? styles.filterPillTextActive : null]}>
                {periodLabels[period]}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {isLoading ? (
        <>
          <SkeletonBlock height={100} />
          <SkeletonBlock height={200} />
        </>
      ) : (
        <>
          <CardFrame style={styles.metricsCard}>
            <View style={styles.metricsRow}>
              <MetricTile
                label="Revenue"
                value={formatCurrency(salesData?.total_revenue.amount_minor)}
              />
              <MetricTile
                label="Orders"
                value={String(salesData?.order_count ?? 0)}
              />
            </View>
            <View style={styles.metricsRow}>
              <MetricTile
                label="Avg Order"
                value={formatCurrency(salesData?.avg_order_value.amount_minor)}
              />
              <MetricTile
                label="Period"
                value={salesData?.period ?? selectedPeriod}
              />
            </View>
          </CardFrame>

          <CardFrame style={styles.chartCard}>
            <Text style={styles.chartTitle}>Revenue Trend</Text>
            {chartData.length > 0 ? (
              <SimpleBarChart data={chartData} />
            ) : (
              <BodyText style={styles.emptyText}>No data for this period</BodyText>
            )}
          </CardFrame>

          {salesData?.top_products && salesData.top_products.length > 0 && (
            <CardFrame style={styles.topProductsCard}>
              <Text style={styles.chartTitle}>Top Products</Text>
              {salesData.top_products.map((product, index) => (
                <View key={index} style={styles.topProductRow}>
                  <Text style={styles.topProductName}>{product.product_name}</Text>
                  <View style={styles.topProductStats}>
                    <Text style={styles.topProductQty}>×{product.quantity_sold}</Text>
                    <Text style={styles.topProductRevenue}>
                      {formatCurrency(product.revenue)}
                    </Text>
                  </View>
                </View>
              ))}
            </CardFrame>
          )}

          <View style={styles.exportRow}>
            <Pressable
              style={({ pressed }) => [
                styles.exportButton,
                pressed && styles.buttonPressed
              ]}
              onPress={handleExportCSV}
            >
              <Text style={styles.exportButtonText}>Export CSV</Text>
            </Pressable>
            <Pressable
              style={({ pressed }) => [
                styles.exportButton,
                pressed && styles.buttonPressed
              ]}
              onPress={handleExportPDF}
            >
              <Text style={styles.exportButtonText}>Export PDF</Text>
            </Pressable>
          </View>
        </>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  screenContent: {
    paddingBottom: 100
  },
  backButton: {
    marginBottom: 16
  },
  backButtonText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 14,
    color: editorialTheme.textMuted
  },
  pageTitle: {
    fontSize: 32,
    lineHeight: 38
  },
  pageCopy: {
    marginTop: 10,
    marginBottom: 16
  },
  filterRow: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 16
  },
  filterPill: {
    flex: 1,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 2,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surface,
    alignItems: "center"
  },
  filterPillActive: {
    backgroundColor: editorialTheme.text,
    borderColor: editorialTheme.text
  },
  filterPillPressed: {
    opacity: 0.7
  },
  filterPillText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    letterSpacing: 0.8,
    textTransform: "uppercase",
    color: editorialTheme.textMuted
  },
  filterPillTextActive: {
    color: editorialTheme.surface
  },
  metricsCard: {
    marginBottom: 16
  },
  metricsRow: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 10
  },
  chartCard: {
    marginBottom: 16
  },
  chartTitle: {
    fontFamily: editorialSerif,
    fontSize: 18,
    lineHeight: 24,
    textTransform: "uppercase",
    color: editorialTheme.text,
    marginBottom: 16
  },
  emptyText: {
    textAlign: "center",
    paddingVertical: 40
  },
  topProductsCard: {
    marginBottom: 16
  },
  topProductRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: editorialTheme.border
  },
  topProductName: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 14,
    color: editorialTheme.text,
    flex: 1
  },
  topProductStats: {
    flexDirection: "row",
    gap: 16
  },
  topProductQty: {
    fontSize: 14,
    color: editorialTheme.textSoft
  },
  topProductRevenue: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 14,
    color: editorialTheme.text
  },
  exportRow: {
    flexDirection: "row",
    gap: 12
  },
  exportButton: {
    flex: 1,
    minHeight: 50,
    borderRadius: 2,
    borderWidth: 1,
    borderColor: editorialTheme.borderStrong,
    backgroundColor: editorialTheme.surface,
    alignItems: "center",
    justifyContent: "center"
  },
  buttonPressed: {
    opacity: 0.7
  },
  exportButtonText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 12,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.text
  }
});
