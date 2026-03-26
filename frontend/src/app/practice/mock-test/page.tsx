"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { practiceApi } from "@/lib/api";
import { cn, difficultyLabel, difficultyClass } from "@/lib/utils";
import Link from "next/link";

const MOCK_TEST_QUESTIONS = 30; // Full NATA = 100; use 30 for demo
const MOCK_TEST_MINUTES = 45;   // Full NATA = 90 min

interface Question {
  id: string; text: string;
  options: { id: string; text: string }[];
  difficulty: number; time_limit_seconds: number; tags?: string[];
}
interface Answer { questionId: string; selected: string | null; timeTaken: number }

type Phase = "intro" | "test" | "review" | "results";

export default function MockTestPage() {
  const [phase, setPhase] = useState<Phase>("intro");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const [currentIdx, setCurrentIdx] = useState(0);
  const [timeLeft, setTimeLeft] = useState(MOCK_TEST_MINUTES * 60);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<{ correct: number; total: number; score: number } | null>(null);
  const questionStartRef = useRef<number>(Date.now());
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const endTest = useCallback(async (sid: string, qs: Question[], ans: Record<string, Answer>) => {
    clearInterval(timerRef.current!);
    setLoading(true);
    let correct = 0;
    // Submit unanswered questions as skipped
    for (const q of qs) {
      const answer = ans[q.id];
      if (answer?.selected) {
        try {
          const res = await practiceApi.submitAnswer(sid, {
            question_id: q.id,
            selected_option_id: answer.selected,
            time_taken_seconds: answer.timeTaken,
          });
          if (res.data.is_correct) correct++;
        } catch { /* skip errors */ }
      }
    }
    await practiceApi.endSession(sid);
    setResults({ correct, total: qs.length, score: Math.round((correct / qs.length) * 120) });
    setPhase("results");
    setLoading(false);
  }, []);

  // Global countdown
  useEffect(() => {
    if (phase !== "test") return;
    timerRef.current = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          clearInterval(timerRef.current!);
          endTest(sessionId!, questions, answers);
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current!);
  }, [phase]);

  async function startTest() {
    setLoading(true);
    try {
      const sessRes = await practiceApi.createSession("mock_test", {
        question_count: MOCK_TEST_QUESTIONS,
        time_limit_minutes: MOCK_TEST_MINUTES,
      });
      const sid = sessRes.data.id;
      setSessionId(sid);

      // Pre-fetch all questions
      const qs: Question[] = [];
      for (let i = 0; i < MOCK_TEST_QUESTIONS; i++) {
        try {
          const qRes = await practiceApi.getNextQuestion(sid);
          const alreadyExists = qs.find((q) => q.id === qRes.data.id);
          if (!alreadyExists) qs.push(qRes.data);
        } catch { break; }
      }

      if (qs.length === 0) {
        alert("No questions available. Please generate questions first.");
        setLoading(false);
        return;
      }

      setQuestions(qs);
      setAnswers({});
      setCurrentIdx(0);
      setTimeLeft(MOCK_TEST_MINUTES * 60);
      setPhase("test");
      questionStartRef.current = Date.now();
    } finally {
      setLoading(false);
    }
  }

  function selectOption(optionId: string) {
    const q = questions[currentIdx];
    const timeTaken = Math.floor((Date.now() - questionStartRef.current) / 1000);
    setAnswers((prev) => ({ ...prev, [q.id]: { questionId: q.id, selected: optionId, timeTaken } }));
  }

  function navigate(idx: number) {
    setCurrentIdx(idx);
    questionStartRef.current = Date.now();
  }

  const formatTime = (s: number) => `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
  const answeredCount = Object.keys(answers).length;

  if (phase === "intro") {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <Link href="/dashboard" className="text-sm text-gray-400 hover:text-gray-600 mb-6 inline-block">← Back</Link>
        <div className="bg-white rounded-2xl border p-8">
          <div className="text-4xl mb-4 text-center">📝</div>
          <h1 className="text-2xl font-bold text-gray-900 text-center mb-2">NATA Mock Test</h1>
          <p className="text-gray-500 text-center mb-8">Simulated test environment. No breaks. Timer counts down.</p>
          <div className="grid grid-cols-3 gap-4 mb-8 text-center">
            <div className="p-4 bg-blue-50 rounded-xl"><div className="text-2xl font-bold text-blue-600">{MOCK_TEST_QUESTIONS}</div><div className="text-xs text-gray-500 mt-1">Questions</div></div>
            <div className="p-4 bg-purple-50 rounded-xl"><div className="text-2xl font-bold text-purple-600">{MOCK_TEST_MINUTES}</div><div className="text-xs text-gray-500 mt-1">Minutes</div></div>
            <div className="p-4 bg-green-50 rounded-xl"><div className="text-2xl font-bold text-green-600">120</div><div className="text-xs text-gray-500 mt-1">Max Score</div></div>
          </div>
          <div className="text-sm text-gray-500 space-y-1 mb-8">
            <p>✓ Covers all NATA syllabus areas</p>
            <p>✓ Adaptive difficulty distribution</p>
            <p>✓ Timer auto-submits when expired</p>
            <p>✓ Detailed results with score prediction</p>
          </div>
          <button onClick={startTest} disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-60 transition-colors">
            {loading ? "Preparing test..." : "Start Mock Test"}
          </button>
        </div>
      </div>
    );
  }

  if (phase === "results" && results) {
    const pct = ((results.correct / results.total) * 100).toFixed(1);
    const predicted = results.score;
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl border p-8 text-center">
          <div className="text-5xl mb-4">{Number(pct) >= 70 ? "🎉" : Number(pct) >= 50 ? "👍" : "📚"}</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Test Complete!</h1>
          <div className="text-5xl font-bold text-blue-600 my-6">{predicted}<span className="text-2xl text-gray-400 font-normal">/120</span></div>
          <p className="text-gray-500 mb-6">Predicted NATA Score (based on {results.correct}/{results.total} correct, {pct}% accuracy)</p>
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="p-3 bg-gray-50 rounded-xl"><div className="text-xl font-bold text-gray-900">{results.correct}</div><div className="text-xs text-gray-400">Correct</div></div>
            <div className="p-3 bg-gray-50 rounded-xl"><div className="text-xl font-bold text-gray-900">{results.total - results.correct}</div><div className="text-xs text-gray-400">Wrong / Skipped</div></div>
            <div className="p-3 bg-gray-50 rounded-xl"><div className="text-xl font-bold text-gray-900">{pct}%</div><div className="text-xs text-gray-400">Accuracy</div></div>
          </div>
          <div className="flex gap-3 justify-center">
            <button onClick={() => { setPhase("intro"); setQuestions([]); setResults(null); }}
              className="bg-blue-600 text-white px-6 py-2.5 rounded-xl font-medium hover:bg-blue-700">
              Retake Test
            </button>
            <Link href="/analytics" className="border px-6 py-2.5 rounded-xl font-medium text-gray-700 hover:border-gray-300">
              View Analytics
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (phase !== "test" || questions.length === 0) return null;

  const currentQ = questions[currentIdx];
  const currentAnswer = answers[currentQ?.id];

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Sidebar: question navigator */}
      <aside className="w-64 bg-white border-r flex flex-col shrink-0">
        <div className="p-4 border-b">
          <div className={cn("text-xl font-bold tabular-nums text-center", timeLeft < 300 ? "text-red-600" : "text-gray-900")}>
            {formatTime(timeLeft)}
          </div>
          <div className="text-xs text-center text-gray-400 mt-0.5">
            {answeredCount}/{questions.length} answered
          </div>
          <div className="w-full bg-gray-100 rounded-full h-1.5 mt-2 overflow-hidden">
            <div className="bg-blue-500 h-full rounded-full" style={{ width: `${(answeredCount / questions.length) * 100}%` }} />
          </div>
        </div>
        <div className="p-3 flex-1 overflow-y-auto">
          <div className="grid grid-cols-5 gap-1.5">
            {questions.map((q, i) => (
              <button key={q.id} onClick={() => navigate(i)}
                className={cn("w-full aspect-square rounded-lg text-xs font-medium transition-colors",
                  i === currentIdx ? "bg-blue-600 text-white" :
                  answers[q.id]?.selected ? "bg-green-100 text-green-700" :
                  "bg-gray-100 text-gray-500 hover:bg-gray-200"
                )}>
                {i + 1}
              </button>
            ))}
          </div>
        </div>
        <div className="p-3 border-t">
          <button onClick={() => endTest(sessionId!, questions, answers)} disabled={loading}
            className="w-full bg-red-50 text-red-600 py-2 rounded-lg text-sm font-medium hover:bg-red-100 transition-colors disabled:opacity-60">
            {loading ? "Submitting..." : "Submit Test"}
          </button>
        </div>
      </aside>

      {/* Question area */}
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-gray-500 font-medium">Question {currentIdx + 1} of {questions.length}</span>
            <div className="flex items-center gap-2">
              <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium", difficultyClass(currentQ.difficulty))}>
                {difficultyLabel(currentQ.difficulty)}
              </span>
              {currentQ.tags?.slice(0, 1).map((t) => (
                <span key={t} className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{t}</span>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-2xl border p-6 mb-4">
            <p className="text-gray-900 font-medium text-base leading-relaxed mb-6">{currentQ.text}</p>
            <div className="space-y-2">
              {currentQ.options.map((opt) => (
                <button key={opt.id} onClick={() => selectOption(opt.id)}
                  className={cn("w-full text-left px-4 py-3 rounded-xl border text-sm transition-all",
                    currentAnswer?.selected === opt.id
                      ? "border-blue-500 bg-blue-50 text-blue-900"
                      : "border-gray-200 hover:border-blue-300 hover:bg-blue-50/30"
                  )}>
                  <span className="font-medium text-gray-400 mr-2">{opt.id}.</span>{opt.text}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <button onClick={() => navigate(Math.max(0, currentIdx - 1))} disabled={currentIdx === 0}
              className="text-sm text-gray-500 px-4 py-2 rounded-lg border hover:bg-gray-50 disabled:opacity-30">
              ← Previous
            </button>
            {currentIdx < questions.length - 1 ? (
              <button onClick={() => navigate(currentIdx + 1)}
                className="text-sm bg-blue-600 text-white px-5 py-2 rounded-lg hover:bg-blue-700">
                Next →
              </button>
            ) : (
              <button onClick={() => endTest(sessionId!, questions, answers)} disabled={loading}
                className="text-sm bg-green-600 text-white px-5 py-2 rounded-lg hover:bg-green-700 disabled:opacity-60">
                {loading ? "Submitting..." : "Finish Test ✓"}
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
