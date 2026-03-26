"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { drawingApi } from "@/lib/api";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface DrawingTask {
  id: string;
  prompt: string;
  category: string;
  difficulty: number;
  rubric: { dimensions: { name: string; weight: number; description: string }[] };
}

interface Evaluation {
  total_score: number;
  dimension_scores: Record<string, { score: number; observations: string; suggestion: string }>;
  feedback: string;
  improvement_suggestions: { skill: string; suggestion: string; priority: string }[];
}

export default function DrawingPracticePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [startTime] = useState<number>(Date.now());

  const { data: task, isLoading } = useQuery<DrawingTask>({
    queryKey: ["next-drawing-task"],
    queryFn: () => drawingApi.getNextTask().then((r) => r.data),
  });

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onload = (ev) => setPreview(ev.target?.result as string);
    reader.readAsDataURL(file);
  }

  async function handleSubmit() {
    if (!selectedFile || !task) return;
    setSubmitting(true);
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("task_id", task.id);
    formData.append("time_taken_seconds", String(Math.floor((Date.now() - startTime) / 1000)));

    try {
      const res = await drawingApi.submitDrawing(formData);
      if (res.data.evaluation) {
        setEvaluation(res.data.evaluation);
      } else {
        // Poll for evaluation
        const submissionId = res.data.id;
        await pollForEvaluation(submissionId);
      }
    } catch (err) {
      console.error("Submission failed", err);
    } finally {
      setSubmitting(false);
    }
  }

  async function pollForEvaluation(submissionId: string) {
    for (let i = 0; i < 20; i++) {
      await new Promise((r) => setTimeout(r, 2000));
      try {
        const res = await drawingApi.getEvaluation(submissionId);
        setEvaluation(res.data);
        return;
      } catch {
        // Still processing
      }
    }
  }

  

  return (
    <div className="p-8 max-w-4xl">
      <Link href="/dashboard" className="text-sm text-gray-400 hover:text-gray-600 mb-6 inline-block">
        ← Back to Dashboard
      </Link>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Drawing Practice</h1>
        <p className="text-gray-500 mt-1">Upload your drawing for AI evaluation across 5 dimensions</p>
      </div>

      {isLoading ? (
        <div className="animate-pulse bg-gray-200 rounded-2xl h-48"></div>
      ) : task && !evaluation ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Task */}
          <div className="bg-white rounded-2xl border p-6">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full font-medium capitalize">
                {task.category.replace("_", " ")}
              </span>
              <span className="text-xs text-gray-400">
                Difficulty: {(task.difficulty * 10).toFixed(0)}/10
              </span>
            </div>

            <h2 className="text-lg font-semibold text-gray-900 mb-3">Drawing Prompt</h2>
            <p className="text-gray-700 leading-relaxed mb-6">{task.prompt}</p>

            <div className="border-t pt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Evaluation Rubric</h3>
              <div className="space-y-2">
                {task.rubric?.dimensions?.map((dim) => (
                  <div key={dim.name} className="flex items-start gap-3 text-sm">
                    <div className="w-20 flex-shrink-0">
                      <span className="text-gray-500 capitalize">{dim.name}</span>
                    </div>
                    <div className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded font-medium">
                      {(dim.weight * 100).toFixed(0)}%
                    </div>
                    <span className="text-gray-400 text-xs">{dim.description}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Upload */}
          <div className="bg-white rounded-2xl border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload Your Drawing</h2>

            <label className={cn(
              "block border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors",
              preview ? "border-blue-300 bg-blue-50/30" : "border-gray-200 hover:border-gray-300"
            )}>
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={handleFileSelect}
                className="hidden"
              />
              {preview ? (
                <img src={preview} alt="Preview" className="max-h-48 mx-auto rounded-lg object-contain" />
              ) : (
                <div>
                  <div className="text-4xl mb-2">📤</div>
                  <p className="text-sm text-gray-500">Click to upload JPG, PNG, or WebP</p>
                  <p className="text-xs text-gray-400 mt-1">Max 10MB</p>
                </div>
              )}
            </label>

            {selectedFile && (
              <div className="mt-3 text-xs text-gray-500 flex items-center gap-2">
                <span className="text-green-500">✓</span>
                {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(1)}MB)
              </div>
            )}

            <button
              onClick={handleSubmit}
              disabled={!selectedFile || submitting}
              className="mt-4 w-full bg-blue-600 text-white py-3 rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {submitting ? "Evaluating your drawing..." : "Submit for AI Evaluation"}
            </button>

            {submitting && (
              <p className="text-xs text-center text-gray-400 mt-2 animate-pulse">
                Claude Vision is analyzing your drawing...
              </p>
            )}
          </div>
        </div>
      ) : evaluation ? (
        <EvaluationResult evaluation={evaluation} task={task!} onNew={() => {
          setEvaluation(null);
          setPreview(null);
          setSelectedFile(null);
        }} />
      ) : null}
    </div>
  );
}

function EvaluationResult({
  evaluation,
  task,
  onNew,
}: {
  evaluation: Evaluation;
  task: DrawingTask;
  onNew: () => void;
}) {
  const scoreColor = evaluation.total_score >= 70 ? "text-green-600" : evaluation.total_score >= 50 ? "text-yellow-600" : "text-red-600";
  const scoreLabel = evaluation.total_score >= 80 ? "Excellent" : evaluation.total_score >= 65 ? "Good" : evaluation.total_score >= 50 ? "Average" : "Needs Work";

  return (
    <div className="space-y-6">
      {/* Score Overview */}
      <div className="bg-white rounded-2xl border p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">AI Evaluation Result</h2>
          <div className="text-right">
            <div className={`text-4xl font-bold ${scoreColor}`}>{evaluation.total_score.toFixed(0)}</div>
            <div className="text-xs text-gray-400">/100 — {scoreLabel}</div>
          </div>
        </div>
        <p className="text-gray-700 text-sm leading-relaxed">{evaluation.feedback}</p>
      </div>

      {/* Dimension Scores */}
      <div className="bg-white rounded-2xl border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Breakdown by Dimension</h3>
        <div className="space-y-4">
          {Object.entries(evaluation.dimension_scores).map(([dim, data]) => (
            <div key={dim}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-700 capitalize">{dim}</span>
                <span className={cn(
                  "text-sm font-bold",
                  data.score >= 70 ? "text-green-600" : data.score >= 50 ? "text-yellow-600" : "text-red-500"
                )}>
                  {data.score.toFixed(0)}/100
                </span>
              </div>
              <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden mb-1">
                <div
                  className={cn(
                    "h-full rounded-full transition-all",
                    data.score >= 70 ? "bg-green-400" : data.score >= 50 ? "bg-yellow-400" : "bg-red-400"
                  )}
                  style={{ width: `${data.score}%` }}
                />
              </div>
              <p className="text-xs text-gray-500">{data.observations}</p>
              {data.suggestion && (
                <p className="text-xs text-blue-600 mt-0.5">→ {data.suggestion}</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Improvement Suggestions */}
      {evaluation.improvement_suggestions?.length > 0 && (
        <div className="bg-white rounded-2xl border p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Improvement Priorities</h3>
          <div className="space-y-3">
            {evaluation.improvement_suggestions.map((s, i) => (
              <div key={i} className="flex gap-3">
                <span className={cn(
                  "text-xs font-bold px-2 py-0.5 rounded-full h-fit mt-0.5",
                  s.priority === "high" ? "bg-red-100 text-red-600" : "bg-yellow-100 text-yellow-600"
                )}>
                  {s.priority.toUpperCase()}
                </span>
                <div>
                  <div className="text-sm font-medium capitalize text-gray-700">{s.skill}</div>
                  <div className="text-sm text-gray-500">{s.suggestion}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <button
        onClick={onNew}
        className="w-full bg-blue-600 text-white py-3 rounded-xl font-medium hover:bg-blue-700 transition-colors"
      >
        Try Another Drawing Task
      </button>
    </div>
  );
}
