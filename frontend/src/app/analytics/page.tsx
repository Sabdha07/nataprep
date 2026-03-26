"use client";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { masteryColor, formatMastery } from "@/lib/utils";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
} from "recharts";
import Link from "next/link";

export default function AnalyticsPage() {
  const { data: dashboard, isLoading } = useQuery({
    queryKey: ["analytics-dashboard"],
    queryFn: () => analyticsApi.getDashboard().then((r) => r.data),
  });

  const { data: progress } = useQuery({
    queryKey: ["analytics-progress"],
    queryFn: () => analyticsApi.getProgress(30).then((r) => r.data),
  });

  if (isLoading) {
    return <div className="p-8 animate-pulse"><div className="h-8 bg-gray-200 rounded w-1/3"></div></div>;
  }

  const breakdown = dashboard?.predicted_score?.breakdown || {};
  const radarData = Object.entries(breakdown).map(([key, val]) => ({
    subject: key.replace("_", " "),
    score: val as number,
    fullMark: 100,
  }));

  return (
    <div className="p-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="text-gray-500 mt-1">Detailed performance analysis for NATA 2026</p>
      </div>

      {/* Predicted Score Banner */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl p-6 text-white mb-8">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-blue-200 text-sm font-medium mb-1">Predicted NATA Aptitude Score</p>
            <div className="text-5xl font-bold">
              {dashboard?.predicted_score?.aptitude_score ?? "—"}
              <span className="text-2xl text-blue-300 font-normal">/120</span>
            </div>
            <p className="text-blue-200 text-sm mt-1">
              Based on {dashboard?.total_questions_attempted ?? 0} questions attempted
            </p>
          </div>
          <div className="text-right">
            <div className="text-blue-200 text-sm mb-1">Confidence</div>
            <div className="text-2xl font-bold capitalize">
              {dashboard?.predicted_score?.confidence ?? "Low"}
            </div>
            <Link href="/practice/adaptive" className="mt-2 block text-xs bg-white/20 hover:bg-white/30 px-3 py-1.5 rounded-lg transition-colors">
              Practice to improve →
            </Link>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Radar Chart */}
        <div className="bg-white rounded-2xl border p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Category Performance</h2>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
              <Radar dataKey="score" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* 30-Day Progress */}
        <div className="bg-white rounded-2xl border p-6">
          <h2 className="font-semibold text-gray-900 mb-4">30-Day Accuracy Trend</h2>
          {progress?.progress?.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={progress.progress}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} tick={{ fontSize: 10 }} />
                <Tooltip formatter={(v: number) => `${(v * 100).toFixed(1)}%`} />
                <Line type="monotone" dataKey="accuracy" stroke="#3b82f6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-400 text-sm">
              Complete more sessions to see trends
            </div>
          )}
        </div>
      </div>

      {/* Weak vs Strong Areas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-2xl border p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Weak Areas — Need Attention</h2>
          <div className="space-y-3">
            {(dashboard?.weak_areas ?? []).map((area: { concept_id: string; concept_name: string; mastery_score: number; accuracy: number; recommended_action: string; priority: string }) => (
              <div key={area.concept_id}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700 truncate">{area.concept_name}</span>
                  <span className={`text-sm font-bold ${masteryColor(area.mastery_score)}`}>
                    {(area.mastery_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-red-400 rounded-full"
                    style={{ width: `${area.mastery_score * 100}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-0.5">{area.recommended_action}</p>
              </div>
            ))}
            {(dashboard?.weak_areas ?? []).length === 0 && (
              <p className="text-sm text-gray-400 text-center py-4">No weak areas identified yet</p>
            )}
          </div>
        </div>

        <div className="bg-white rounded-2xl border p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Strong Areas — Keep It Up</h2>
          <div className="space-y-3">
            {(dashboard?.strong_areas ?? []).map((area: { concept_id: string; concept_name: string; mastery_score: number }) => (
              <div key={area.concept_id}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700 truncate">{area.concept_name}</span>
                  <span className="text-sm font-bold text-green-600">
                    {(area.mastery_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-400 rounded-full"
                    style={{ width: `${area.mastery_score * 100}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400 capitalize">{formatMastery(area.mastery_score)}</p>
              </div>
            ))}
            {(dashboard?.strong_areas ?? []).length === 0 && (
              <p className="text-sm text-gray-400 text-center py-4">Master concepts to see your strengths</p>
            )}
          </div>
        </div>
      </div>

      {/* AI Insights */}
      <div className="bg-white rounded-2xl border p-6">
        <h2 className="font-semibold text-gray-900 mb-4">AI Personalized Insights</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {(dashboard?.insights ?? []).map((insight: string, i: number) => (
            <div key={i} className="flex gap-3 p-3 bg-blue-50 rounded-xl">
              <span className="text-blue-500 text-lg flex-shrink-0">💡</span>
              <p className="text-sm text-gray-700">{insight}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
