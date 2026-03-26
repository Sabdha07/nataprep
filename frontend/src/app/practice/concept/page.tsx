"use client";
import { useState, useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { conceptsApi, practiceApi } from "@/lib/api";
import { cn, difficultyLabel, difficultyClass } from "@/lib/utils";
import Link from "next/link";

interface Concept { id: string; name: string; category: string; difficulty_base: number }
interface Question { id: string; text: string; options: { id: string; text: string }[]; difficulty: number; time_limit_seconds: number; tags?: string[] }
interface SubmitResult { is_correct: boolean; correct_option_id: string; explanation: string }

const CATEGORIES = [
  { id: "mathematics", label: "Mathematics", icon: "📐" },
  { id: "visual_reasoning", label: "Visual Reasoning", icon: "👁️" },
  { id: "general_aptitude", label: "General Aptitude", icon: "🧩" },
  { id: "architecture_gk", label: "Architecture GK", icon: "🏛️" },
  { id: "physics", label: "Physics", icon: "⚡" },
];

export default function ConceptModePage() {
  const [selectedConceptId, setSelectedConceptId] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState("mathematics");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState<Question | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [stats, setStats] = useState({ answered: 0, correct: 0 });
  const [loading, setLoading] = useState(false);
  const [timeLeft, setTimeLeft] = useState(90);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const { data: concepts = [] } = useQuery<Concept[]>({
    queryKey: ["concepts", selectedCategory],
    queryFn: () => conceptsApi.list(selectedCategory).then((r) => r.data),
  });

  // Timer
  useEffect(() => {
    if (!question || result) return;
    setTimeLeft(question.time_limit_seconds);
    timerRef.current = setInterval(() => setTimeLeft((t) => Math.max(0, t - 1)), 1000);
    return () => clearInterval(timerRef.current!);
  }, [question?.id]);

  useEffect(() => {
    if (result) clearInterval(timerRef.current!);
  }, [result]);

  async function startConcept(conceptId: string) {
    setLoading(true);
    try {
      const sessRes = await practiceApi.createSession("concept", {
        concept_ids: [conceptId],
      });
      setSessionId(sessRes.data.id);
      setSelectedConceptId(conceptId);
      await fetchQuestion(sessRes.data.id);
    } finally {
      setLoading(false);
    }
  }

  async function fetchQuestion(sid: string) {
    const qRes = await practiceApi.getNextQuestion(sid);
    setQuestion(qRes.data);
    setSelected(null);
    setResult(null);
  }

  async function submitAnswer(optionId: string) {
    if (!sessionId || !question || result) return;
    clearInterval(timerRef.current!);
    const timeTaken = question.time_limit_seconds - timeLeft;
    setSelected(optionId);
    setLoading(true);
    try {
      const res = await practiceApi.submitAnswer(sessionId, {
        question_id: question.id,
        selected_option_id: optionId,
        time_taken_seconds: timeTaken,
      });
      setResult(res.data);
      setStats((s) => ({
        answered: s.answered + 1,
        correct: s.correct + (res.data.is_correct ? 1 : 0),
      }));
    } finally {
      setLoading(false);
    }
  }

  async function nextQuestion() {
    if (!sessionId) return;
    setLoading(true);
    try {
      await fetchQuestion(sessionId);
    } finally {
      setLoading(false);
    }
  }

  function exitConcept() {
    setSelectedConceptId(null);
    setSessionId(null);
    setQuestion(null);
    setResult(null);
    setSelected(null);
    setStats({ answered: 0, correct: 0 });
  }

  // Concept selection screen
  if (!selectedConceptId) {
    return (
      <div className="p-8 max-w-4xl">
        <Link href="/dashboard" className="text-sm text-gray-400 hover:text-gray-600 mb-6 inline-block">← Back</Link>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Concept Mode</h1>
        <p className="text-gray-500 mb-6">Focus on one topic at a time. Master it before moving on.</p>

        <div className="flex gap-2 mb-6 flex-wrap">
          {CATEGORIES.map((cat) => (
            <button key={cat.id} onClick={() => setSelectedCategory(cat.id)}
              className={cn("px-4 py-1.5 rounded-full text-sm font-medium transition-colors flex items-center gap-1",
                selectedCategory === cat.id ? "bg-blue-600 text-white" : "bg-white border text-gray-600 hover:border-blue-300"
              )}>
              {cat.icon} {cat.label}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {(concepts as Concept[]).map((concept) => (
            <button key={concept.id} onClick={() => startConcept(concept.id)} disabled={loading}
              className="text-left p-4 bg-white rounded-xl border hover:border-blue-300 hover:bg-blue-50/30 transition-all disabled:opacity-50">
              <div className="font-medium text-gray-900 mb-1">{concept.name}</div>
              <div className="flex items-center gap-2">
                <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium", difficultyClass(concept.difficulty_base))}>
                  {difficultyLabel(concept.difficulty_base)}
                </span>
              </div>
            </button>
          ))}
          {(concepts as Concept[]).length === 0 && (
            <div className="col-span-3 py-12 text-center text-gray-400">
              No concepts found. Run the seed script first.
            </div>
          )}
        </div>
      </div>
    );
  }

  const conceptName = (concepts as Concept[]).find((c) => c.id === selectedConceptId)?.name || "Concept";

  // Practice screen
  return (
    <div className="p-8 max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <button onClick={exitConcept} className="text-sm text-gray-400 hover:text-gray-600 mb-1 block">← Change Concept</button>
          <h2 className="font-bold text-gray-900">{conceptName}</h2>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-gray-500">{stats.answered} answered</span>
          <span className="text-green-600 font-medium">
            {stats.answered > 0 ? ((stats.correct / stats.answered) * 100).toFixed(0) : "—"}% accuracy
          </span>
          <span className={cn("font-bold px-3 py-1 rounded-full text-sm",
            timeLeft <= 10 ? "bg-red-100 text-red-600" : "bg-gray-100 text-gray-600"
          )}>{timeLeft}s</span>
        </div>
      </div>

      {question ? (
        <div className="bg-white rounded-2xl border p-6">
          <div className="flex items-center gap-2 mb-4">
            <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium", difficultyClass(question.difficulty))}>
              {difficultyLabel(question.difficulty)}
            </span>
            {question.tags?.slice(0, 2).map((tag) => (
              <span key={tag} className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{tag}</span>
            ))}
          </div>

          <p className="text-gray-900 font-medium text-base leading-relaxed mb-6">{question.text}</p>

          <div className="space-y-2">
            {question.options.map((opt) => {
              let style = "border-gray-200 hover:border-blue-300 hover:bg-blue-50/50 cursor-pointer";
              if (result) {
                if (opt.id === result.correct_option_id) style = "border-green-400 bg-green-50";
                else if (opt.id === selected) style = "border-red-400 bg-red-50";
                else style = "border-gray-200 opacity-40";
              } else if (selected === opt.id) style = "border-blue-400 bg-blue-50";
              return (
                <button key={opt.id} disabled={!!result || loading}
                  onClick={() => submitAnswer(opt.id)}
                  className={cn("w-full text-left px-4 py-3 rounded-xl border text-sm transition-all", style)}>
                  <span className="font-medium text-gray-400 mr-2">{opt.id}.</span>{opt.text}
                </button>
              );
            })}
          </div>

          {result && (
            <div className={cn("mt-4 p-4 rounded-xl", result.is_correct ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200")}>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{result.is_correct ? "✓" : "✗"}</span>
                <span className={cn("font-semibold text-sm", result.is_correct ? "text-green-700" : "text-red-700")}>
                  {result.is_correct ? "Correct!" : "Incorrect"}
                </span>
              </div>
              <p className="text-sm text-gray-700 leading-relaxed">{result.explanation}</p>
              <button onClick={nextQuestion} disabled={loading}
                className="mt-3 bg-blue-600 text-white text-sm px-5 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                {loading ? "Loading..." : "Next Question →"}
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-2xl border p-8 text-center text-gray-400">
          {loading ? "Loading question..." : "No questions available for this concept yet."}
        </div>
      )}
    </div>
  );
}
