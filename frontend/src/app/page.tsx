import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b px-6 py-4 flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">N</span>
          </div>
          <span className="font-bold text-xl">NATAPrep</span>
          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">2026</span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">
            Sign In
          </Link>
          <Link
            href="/register"
            className="text-sm bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Get Started Free
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-6 py-24 text-center">
        <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 text-sm px-4 py-1.5 rounded-full mb-8 font-medium">
          <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
          AI-Powered • Adaptive • Always Improving
        </div>

        <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
          Score <span className="text-blue-600">120/120</span> in<br />
          NATA 2026 Aptitude
        </h1>

        <p className="text-xl text-gray-500 max-w-2xl mx-auto mb-10">
          The only platform that adapts to you. AI agents track your weaknesses,
          generate questions, and evaluate drawings — like a personal NATA tutor.
        </p>

        <div className="flex items-center justify-center gap-4 flex-wrap">
          <Link
            href="/register"
            className="bg-blue-600 text-white px-8 py-3 rounded-xl text-lg font-semibold hover:bg-blue-700 transition-colors shadow-lg"
          >
            Start Free Preparation
          </Link>
          <Link
            href="/dashboard"
            className="border border-gray-200 px-8 py-3 rounded-xl text-lg font-medium text-gray-700 hover:border-gray-300 transition-colors"
          >
            View Demo
          </Link>
        </div>
      </section>

      {/* Features Grid */}
      <section className="max-w-7xl mx-auto px-6 pb-24">
        <h2 className="text-center text-3xl font-bold text-gray-900 mb-12">
          A living system that improves with you
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              icon: "🧠",
              title: "Adaptive Learning Engine",
              desc: "ELO-based mastery tracking selects the perfect next question based on your weak areas and spaced repetition schedule.",
            },
            {
              icon: "🎨",
              title: "AI Drawing Evaluation",
              desc: "Upload your drawings and get Claude Vision feedback across 5 dimensions: perspective, proportion, composition, creativity, execution.",
            },
            {
              icon: "📊",
              title: "Predicted Score Dashboard",
              desc: "Real-time NATA score prediction with category breakdowns, accuracy trends, and AI-generated improvement insights.",
            },
            {
              icon: "🤖",
              title: "Infinite Question Generation",
              desc: "Never run out of practice. AI generates new questions for any concept at any difficulty level, matching NATA patterns.",
            },
            {
              icon: "📚",
              title: "100% Syllabus Coverage",
              desc: "Every concept mapped from the official NATA 2026 syllabus — Mathematics, Visual Reasoning, Architecture GK, and more.",
            },
            {
              icon: "🔄",
              title: "Self-Updating Platform",
              desc: "Automated agents scrape latest papers, detect syllabus changes, and expand the question bank — no manual updates needed.",
            },
          ].map((f) => (
            <div key={f.title} className="p-6 rounded-2xl border border-gray-100 hover:border-blue-100 hover:bg-blue-50/30 transition-all">
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="font-semibold text-lg text-gray-900 mb-2">{f.title}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Practice Modes */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-center text-3xl font-bold text-gray-900 mb-4">6 Practice Modes</h2>
          <p className="text-center text-gray-500 mb-12">Every way you need to practice, built in.</p>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {[
              { mode: "Adaptive", desc: "AI picks questions for you", color: "blue" },
              { mode: "Concept", desc: "Focus on one topic", color: "purple" },
              { mode: "Mock Test", desc: "Full NATA simulation", color: "red" },
              { mode: "Drawing", desc: "Upload & get evaluated", color: "green" },
              { mode: "Mixed", desc: "All topics randomly", color: "yellow" },
              { mode: "Review", desc: "Redo your mistakes", color: "orange" },
            ].map((m) => (
              <div key={m.mode} className="bg-white rounded-xl p-4 text-center border border-gray-100 shadow-sm">
                <div className={`text-sm font-bold text-${m.color}-600 mb-1`}>{m.mode}</div>
                <div className="text-xs text-gray-400">{m.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-7xl mx-auto px-6 py-20 text-center">
        <h2 className="text-4xl font-bold text-gray-900 mb-4">Ready to start?</h2>
        <p className="text-gray-500 mb-8">NATA 2026 is approaching. Your preparation starts today.</p>
        <Link
          href="/register"
          className="inline-block bg-blue-600 text-white px-10 py-4 rounded-xl text-lg font-semibold hover:bg-blue-700 transition-colors"
        >
          Create Free Account
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 text-center text-sm text-gray-400">
        <p>NATAPrep 2026 — Built for architects by AI</p>
      </footer>
    </main>
  );
}
