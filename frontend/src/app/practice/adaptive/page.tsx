"use client";
import { useState, useEffect, useCallback, useRef } from "react";
import { practiceApi } from "@/lib/api";
import { difficultyLabel, difficultyClass, cn } from "@/lib/utils";
import Link from "next/link";

interface Question {
  id: string;
  text: string;
  options: { id: string; text: string }[];
  difficulty: number;
  time_limit_seconds: number;
  image_url?: string;
  tags?: string[];
}

interface SessionState {
  sessionId: string;
  questionsAnswered: number;
  correct: number;
  currentQuestion: Question | null;
}

export default function AdaptivePracticePage() {
  const [session, setSession] = useState<SessionState | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<{
    is_correct: boolean;
    correct_option_id: string;
    explanation: string;
    mastery_update?: { old_mastery: number; new_mastery: number; delta: number };
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [timeLeft, setTimeLeft] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startSession = useCallback(async () => {
    setLoading(true);
    try {
      const sessRes = await practiceApi.createSession("adaptive", { max_questions: 50 });
      const sessionId = sessRes.data.id;
      const qRes = await practiceApi.getNextQuestion(sessionId);
      setSession({
        sessionId,
        questionsAnswered: 0,
        correct: 0,
        currentQuestion: qRes.data,
      });
      setTimeLeft(qRes.data.time_limit_seconds);
    } finally {
      setLoading(false);
    }
  }, []);

  // Timer
  useEffect(() => {
    if (!session?.currentQuestion || result) return;
    timerRef.current = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          clearInterval(timerRef.current!);
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current!);
  }, [session?.currentQuestion, result]);

  const submitAnswer = async (optionId: string) => {
    if (!session || result) return;
    clearInterval(timerRef.current!);
    const timeTaken = (session.currentQuestion?.time_limit_seconds ?? 90) - timeLeft;
    setSelected(optionId);
    setLoading(true);
    try {
      const res = await practiceApi.submitAnswer(session.sessionId, {
        question_id: session.currentQuestion!.id,
        selected_option_id: optionId,
        time_taken_seconds: timeTaken,
      });
      setResult(res.data);
      setSession((s) => s ? {
        ...s,
        questionsAnswered: s.questionsAnswered + 1,
        correct: s.correct + (res.data.is_correct ? 1 : 0),
      } : null);
    } finally {
      setLoading(false);
    }
  };

  const nextQuestion = async () => {
    if (!session) return;
    setLoading(true);
    setResult(null);
    setSelected(null);
    try {
      const qRes = await practiceApi.getNextQuestion(session.sessionId);
      setSession((s) => s ? { ...s, currentQuestion: qRes.data } : null);
      setTimeLeft(qRes.data.time_limit_seconds);
    } finally {
      setLoading(false);
    }
  };

  if (!session) {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <Link href="/dashboard" className="text-sm text-gray-400 hover:text-gray-600 mb-6 inline-block">
          ← Back
        </Link>
        <div className="bg-white rounded-2xl border p-8 text-center">
          <div className="text-4xl mb-4">🧠</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Adaptive Practice</h1>
          <p className="text-gray-500 mb-6">
            AI selects the perfect question for you based on your mastery levels and spaced repetition schedule.
          </p>
          <div className="grid grid-cols-3 gap-4 mb-8 text-center text-sm">
            <div className="p-3 bg-blue-50 rounded-xl">
              <div className="font-bold text-blue-600">Smart</div>
              <div className="text-gray-500 text-xs">Targets weak areas</div>
            </div>
            <div className="p-3 bg-green-50 rounded-xl">
              <div className="font-bold text-green-600">Adaptive</div>
              <div className="text-gray-500 text-xs">Adjusts difficulty</div>
            </div>
            <div className="p-3 bg-purple-50 rounded-xl">
              <div className="font-bold text-purple-600">Efficient</div>
              <div className="text-gray-500 text-xs">Spaced repetition</div>
            </div>
          </div>
          <button
            onClick={startSession}
            disabled={loading}
            className="bg-blue-600 text-white px-8 py-3 rounded-xl font-medium hover:bg-blue-700 transition-colors disabled:opacity-60"
          >
            {loading ? "Starting..." : "Start Adaptive Session"}
          </button>
        </div>
      </div>
    );
  }

  const q = session.currentQuestion;
  const accuracy = session.questionsAnswered > 0
    ? ((session.correct / session.questionsAnswered) * 100).toFixed(0)
    : "—";

  return (
    <div className="p-8 max-w-2xl mx-auto">
      {/* Session Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span className="font-medium text-gray-900">{session.questionsAnswered} answered</span>
          <span>•</span>
          <span className="text-green-600 font-medium">{accuracy}% accuracy</span>
        </div>
        <div className={cn(
          "text-sm font-bold px-3 py-1 rounded-full",
          timeLeft <= 10 ? "bg-red-100 text-red-600" : "bg-gray-100 text-gray-600"
        )}>
          {timeLeft}s
        </div>
      </div>

      {/* Question Card */}
      {q && (
        <div className="bg-white rounded-2xl border p-6">
          {/* Meta */}
          <div className="flex items-center gap-2 mb-4">
            <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium", difficultyClass(q.difficulty))}>
              {difficultyLabel(q.difficulty)}
            </span>
            {q.tags?.slice(0, 2).map((tag) => (
              <span key={tag} className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
                {tag}
              </span>
            ))}
          </div>

          {/* Question Text */}
          <p className="text-gray-900 font-medium text-base leading-relaxed mb-6">{q.text}</p>

          {/* Options */}
          <div className="space-y-2">
            {q.options.map((opt) => {
              let optStyle = "border-gray-200 hover:border-blue-300 hover:bg-blue-50/50 cursor-pointer";
              if (result) {
                if (opt.id === result.correct_option_id) {
                  optStyle = "border-green-400 bg-green-50";
                } else if (opt.id === selected && !result.is_correct) {
                  optStyle = "border-red-400 bg-red-50";
                } else {
                  optStyle = "border-gray-200 opacity-50";
                }
              } else if (selected === opt.id) {
                optStyle = "border-blue-400 bg-blue-50";
              }

              return (
                <button
                  key={opt.id}
                  onClick={() => !result && submitAnswer(opt.id)}
                  disabled={!!result || loading}
                  className={cn(
                    "w-full text-left px-4 py-3 rounded-xl border text-sm transition-all",
                    optStyle
                  )}
                >
                  <span className="font-medium text-gray-500 mr-2">{opt.id}.</span>
                  {opt.text}
                </button>
              );
            })}
          </div>

          {/* Result */}
          {result && (
            <div className={cn(
              "mt-4 p-4 rounded-xl",
              result.is_correct ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200"
            )}>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{result.is_correct ? "✓" : "✗"}</span>
                <span className={cn("font-semibold text-sm", result.is_correct ? "text-green-700" : "text-red-700")}>
                  {result.is_correct ? "Correct!" : "Incorrect"}
                </span>
                {result.mastery_update && (
                  <span className={cn(
                    "ml-auto text-xs font-medium",
                    (result.mastery_update.delta ?? 0) > 0 ? "text-green-600" : "text-red-500"
                  )}>
                    Mastery {(result.mastery_update.delta ?? 0) > 0 ? "+" : ""}
                    {((result.mastery_update.delta ?? 0) * 100).toFixed(1)}%
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-700 leading-relaxed">{result.explanation}</p>
              <button
                onClick={nextQuestion}
                disabled={loading}
                className="mt-3 bg-blue-600 text-white text-sm px-5 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                {loading ? "Loading..." : "Next Question →"}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
