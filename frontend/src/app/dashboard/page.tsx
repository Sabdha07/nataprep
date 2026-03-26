"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { analyticsApi } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { formatMastery, masteryColor } from "@/lib/utils";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { data: dashboard, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => analyticsApi.getDashboard().then((r) => r.data),
  });

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded-xl"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Good {getTimeOfDay()}, {user?.full_name?.split(" ")[0] || "Student"}
        </h1>
        <p className="text-gray-500 mt-1">
          Here&apos;s your NATA 2026 preparation overview
        </p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Questions Attempted"
          value={dashboard?.total_questions_attempted ?? 0}
          sub="total"
          color="blue"
        />
        <StatCard
          label="Overall Accuracy"
          value={`${((dashboard?.overall_accuracy ?? 0) * 100).toFixed(1)}%`}
          sub={`${dashboard?.total_correct ?? 0} correct`}
          color="green"
        />
        <StatCard
          label="Overall Mastery"
          value={`${((dashboard?.overall_mastery ?? 0) * 100).toFixed(0)}%`}
          sub={formatMastery(dashboard?.overall_mastery ?? 0)}
          color="purple"
        />
        <StatCard
          label="Study Streak"
          value={`${dashboard?.study_streak_days ?? 0} days`}
          sub="consecutive"
          color="orange"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Predicted Score */}
        <div className="bg-white rounded-2xl border p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Predicted NATA Score</h2>
          <div className="text-center py-4">
            <div className="text-5xl font-bold text-blue-600 mb-1">
              {dashboard?.predicted_score?.aptitude_score ?? "—"}
            </div>
            <div className="text-gray-400 text-sm">out of 120 (Aptitude)</div>
            <div className={`mt-2 text-xs px-3 py-1 rounded-full inline-block font-medium ${
              dashboard?.predicted_score?.confidence === "high"
                ? "bg-green-100 text-green-700"
                : dashboard?.predicted_score?.confidence === "medium"
                ? "bg-yellow-100 text-yellow-700"
                : "bg-gray-100 text-gray-500"
            }`}>
              {dashboard?.predicted_score?.confidence?.toUpperCase() || "LOW"} CONFIDENCE
            </div>
          </div>
          <div className="mt-4 space-y-2">
            {Object.entries(dashboard?.predicted_score?.breakdown ?? {}).map(([cat, score]) => (
              <div key={cat} className="flex items-center justify-between text-xs">
                <span className="text-gray-500 capitalize">{cat.replace("_", " ")}</span>
                <div className="flex items-center gap-2">
                  <div className="w-20 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-400 rounded-full"
                      style={{ width: `${score as number}%` }}
                    />
                  </div>
                  <span className="text-gray-700 font-medium w-8 text-right">{score as number}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Weak Areas */}
        <div className="bg-white rounded-2xl border p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900">Top Weak Areas</h2>
            <Link href="/analytics" className="text-xs text-blue-600 hover:underline">View all</Link>
          </div>
          <div className="space-y-3">
            {(dashboard?.weak_areas ?? []).slice(0, 5).map((area: { concept_id: string; concept_name: string; mastery_score: number; priority: string; recommended_action: string }) => (
              <div key={area.concept_id} className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                  area.priority === "high" ? "bg-red-500" : "bg-yellow-500"
                }`} />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900 truncate">{area.concept_name}</div>
                  <div className="text-xs text-gray-400">{area.recommended_action}</div>
                </div>
                <div className={`text-xs font-bold ${masteryColor(area.mastery_score)}`}>
                  {(area.mastery_score * 100).toFixed(0)}%
                </div>
              </div>
            ))}
            {(dashboard?.weak_areas ?? []).length === 0 && (
              <p className="text-sm text-gray-400 text-center py-4">
                Practice more questions to identify weak areas
              </p>
            )}
          </div>
          {(dashboard?.weak_areas ?? []).length > 0 && (
            <Link
              href="/practice/adaptive"
              className="mt-4 block w-full text-center bg-red-50 text-red-600 text-sm py-2 rounded-lg font-medium hover:bg-red-100 transition-colors"
            >
              Practice Weak Areas Now
            </Link>
          )}
        </div>

        {/* AI Insights */}
        <div className="bg-white rounded-2xl border p-6">
          <h2 className="font-semibold text-gray-900 mb-4">AI Insights</h2>
          <div className="space-y-3">
            {(dashboard?.insights ?? ["Start practicing to unlock personalized insights."]).map((insight: string, i: number) => (
              <div key={i} className="flex gap-2 text-sm text-gray-600">
                <span className="text-blue-400 flex-shrink-0 mt-0.5">→</span>
                <span>{insight}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Progress Chart */}
      <div className="bg-white rounded-2xl border p-6 mb-8">
        <h2 className="font-semibold text-gray-900 mb-6">14-Day Progress</h2>
        {(dashboard?.recent_progress ?? []).length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={dashboard?.recent_progress ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: number) => `${(v * 100).toFixed(1)}%`} />
              <Line type="monotone" dataKey="accuracy" stroke="#3b82f6" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-48 flex items-center justify-center text-gray-400 text-sm">
            Complete practice sessions to see your progress chart
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { href: "/practice/adaptive", icon: "🧠", label: "Adaptive Practice", desc: "AI-selected questions" },
          { href: "/practice/mock-test", icon: "📝", label: "Mock Test", desc: "90 min full test" },
          { href: "/practice/drawing", icon: "🎨", label: "Drawing Task", desc: "Upload for evaluation" },
          { href: "/concepts", icon: "🗺️", label: "Concept Map", desc: "Browse all topics" },
        ].map((action) => (
          <Link
            key={action.href}
            href={action.href}
            className="bg-white rounded-xl border p-4 hover:border-blue-200 hover:bg-blue-50/30 transition-all group"
          >
            <div className="text-2xl mb-2">{action.icon}</div>
            <div className="font-medium text-gray-900 text-sm group-hover:text-blue-600">{action.label}</div>
            <div className="text-xs text-gray-400 mt-0.5">{action.desc}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function StatCard({ label, value, sub, color }: { label: string; value: string | number; sub: string; color: string }) {
  const colorMap: Record<string, string> = {
    blue: "bg-blue-50 text-blue-600",
    green: "bg-green-50 text-green-600",
    purple: "bg-purple-50 text-purple-600",
    orange: "bg-orange-50 text-orange-600",
  };
  return (
    <div className="bg-white rounded-xl border p-5">
      <p className="text-xs text-gray-400 font-medium uppercase tracking-wide mb-1">{label}</p>
      <p className={`text-2xl font-bold ${colorMap[color]?.split(" ")[1] || "text-gray-900"}`}>{value}</p>
      <p className="text-xs text-gray-400 mt-0.5">{sub}</p>
    </div>
  );
}

function getTimeOfDay() {
  const h = new Date().getHours();
  if (h < 12) return "morning";
  if (h < 17) return "afternoon";
  return "evening";
}
