"use client";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import Link from "next/link";

interface AgentRun {
  id: string; agent_name: string; status: string;
  started_at: string; completed_at?: string;
  summary?: Record<string, unknown>; error_message?: string;
}
interface PlatformStats { questions: number; drawing_tasks: number; users: number; total_attempts: number }

function statCard(label: string, value: number | string, color: string) {
  return (
    <div className="bg-white rounded-xl border p-5">
      <p className="text-xs text-gray-400 uppercase font-medium mb-1">{label}</p>
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
    </div>
  );
}

export default function AdminPage() {
  const [genConceptId, setGenConceptId] = useState("");
  const [genCount, setGenCount] = useState(5);
  const [genDifficulty, setGenDifficulty] = useState(0.5);
  const [feedback, setFeedback] = useState("");

  const { data: stats } = useQuery<PlatformStats>({
    queryKey: ["admin-stats"],
    queryFn: () => api.get("/admin/stats").then((r) => r.data),
    refetchInterval: 30000,
  });

  const { data: runs, refetch: refetchRuns } = useQuery<AgentRun[]>({
    queryKey: ["agent-runs"],
    queryFn: () => api.get("/admin/agents/runs?limit=20").then((r) => r.data),
    refetchInterval: 10000,
  });

  const generateQuestions = useMutation({
    mutationFn: () =>
      api.post("/admin/agents/generate-questions", null, {
        params: { concept_id: genConceptId || undefined, count: genCount, difficulty: genDifficulty },
      }),
    onSuccess: (res) => {
      setFeedback(`✓ Generated ${res.data.created}/${res.data.requested} questions`);
      refetchRuns();
    },
    onError: () => setFeedback("✗ Generation failed — check API key"),
  });

  const generateTasks = useMutation({
    mutationFn: () => api.post("/admin/agents/generate-drawing-tasks", null, { params: { count: 5 } }),
    onSuccess: (res) => {
      setFeedback(`✓ Generated ${res.data.created} drawing tasks`);
      refetchRuns();
    },
    onError: () => setFeedback("✗ Task generation failed"),
  });

  const statusColor: Record<string, string> = {
    completed: "text-green-600 bg-green-50",
    running: "text-blue-600 bg-blue-50 animate-pulse",
    failed: "text-red-600 bg-red-50",
  };

  return (
    <div className="p-8 max-w-6xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-500 mt-1">Manage agents, data, and platform health</p>
        </div>
        <Link href="/dashboard" className="text-sm text-gray-400 hover:text-gray-600">← Back</Link>
      </div>

      {/* Platform Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {statCard("Questions", stats?.questions ?? "—", "text-blue-600")}
        {statCard("Drawing Tasks", stats?.drawing_tasks ?? "—", "text-purple-600")}
        {statCard("Active Users", stats?.users ?? "—", "text-green-600")}
        {statCard("Total Attempts", stats?.total_attempts ?? "—", "text-orange-600")}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Question Generation */}
        <div className="bg-white rounded-2xl border p-6">
          <h2 className="font-semibold text-gray-900 mb-4">🤖 Generate Questions</h2>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Concept ID (optional)</label>
              <input value={genConceptId} onChange={(e) => setGenConceptId(e.target.value)}
                placeholder="Leave blank for random concept"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Count</label>
                <input type="number" min={1} max={20} value={genCount}
                  onChange={(e) => setGenCount(Number(e.target.value))}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Difficulty (0.1–1.0)</label>
                <input type="number" step={0.1} min={0.1} max={1.0} value={genDifficulty}
                  onChange={(e) => setGenDifficulty(Number(e.target.value))}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
            <button onClick={() => { setFeedback(""); generateQuestions.mutate(); }}
              disabled={generateQuestions.isPending}
              className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-60 transition-colors">
              {generateQuestions.isPending ? "Generating..." : "Generate Questions (Claude API)"}
            </button>
          </div>
        </div>

        {/* Drawing Tasks */}
        <div className="bg-white rounded-2xl border p-6">
          <h2 className="font-semibold text-gray-900 mb-4">🎨 Generate Drawing Tasks</h2>
          <p className="text-sm text-gray-500 mb-4">
            Generate 5 new drawing prompts across different categories using Claude.
            Current pool: <strong>{stats?.drawing_tasks ?? "—"}</strong> tasks.
          </p>
          <button onClick={() => { setFeedback(""); generateTasks.mutate(); }}
            disabled={generateTasks.isPending}
            className="w-full bg-purple-600 text-white py-2.5 rounded-lg font-medium text-sm hover:bg-purple-700 disabled:opacity-60 transition-colors">
            {generateTasks.isPending ? "Generating..." : "Generate 5 Drawing Tasks"}
          </button>

          {feedback && (
            <div className={`mt-3 text-sm p-3 rounded-lg ${feedback.startsWith("✓") ? "bg-green-50 text-green-700" : "bg-red-50 text-red-600"}`}>
              {feedback}
            </div>
          )}
        </div>
      </div>

      {/* Agent Run History */}
      <div className="bg-white rounded-2xl border p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900">Agent Run History</h2>
          <button onClick={() => refetchRuns()} className="text-xs text-blue-600 hover:underline">Refresh</button>
        </div>
        <div className="space-y-2">
          {(runs ?? []).map((run) => (
            <div key={run.id} className="flex items-center gap-4 px-3 py-2.5 rounded-lg border border-gray-100 text-sm">
              <span className="text-gray-400 font-mono text-xs w-36 shrink-0">
                {new Date(run.started_at).toLocaleTimeString()}
              </span>
              <span className="font-medium text-gray-700 flex-1 truncate">
                {run.agent_name.replace(/_/g, " ")}
              </span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColor[run.status] || "text-gray-500 bg-gray-50"}`}>
                {run.status}
              </span>
              {run.summary && (
                <span className="text-xs text-gray-400 max-w-xs truncate">
                  {JSON.stringify(run.summary).slice(0, 60)}
                </span>
              )}
              {run.error_message && (
                <span className="text-xs text-red-400 truncate max-w-xs" title={run.error_message}>
                  {run.error_message.slice(0, 50)}
                </span>
              )}
            </div>
          ))}
          {(runs ?? []).length === 0 && (
            <p className="text-sm text-gray-400 text-center py-6">No agent runs yet</p>
          )}
        </div>
      </div>
    </div>
  );
}
