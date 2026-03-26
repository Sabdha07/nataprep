"use client";
import { useQuery } from "@tanstack/react-query";
import { conceptsApi } from "@/lib/api";
import { masteryColor, formatMastery } from "@/lib/utils";
import { useState } from "react";
import Link from "next/link";

const CATEGORIES = [
  { id: "all", label: "All" },
  { id: "mathematics", label: "Mathematics" },
  { id: "visual_reasoning", label: "Visual Reasoning" },
  { id: "general_aptitude", label: "General Aptitude" },
  { id: "architecture_gk", label: "Architecture GK" },
  { id: "physics", label: "Physics" },
];

interface Concept {
  id: string;
  name: string;
  description: string;
  category: string;
  parent_id: string | null;
  difficulty_base: number;
  syllabus_weight: number;
}

export default function ConceptsPage() {
  const [activeCategory, setActiveCategory] = useState("all");

  const { data: concepts = [], isLoading } = useQuery({
    queryKey: ["concepts", activeCategory],
    queryFn: () =>
      conceptsApi.list(activeCategory === "all" ? undefined : activeCategory).then((r) => r.data),
  });

  const grouped = (concepts as Concept[]).reduce((acc, c) => {
    if (!acc[c.category]) acc[c.category] = [];
    acc[c.category].push(c);
    return acc;
  }, {} as Record<string, Concept[]>);

  return (
    <div className="p-8 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Concept Map</h1>
        <p className="text-gray-500 mt-1">Browse all NATA 2026 syllabus concepts and your mastery levels</p>
      </div>

      {/* Category Filter */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              activeCategory === cat.id
                ? "bg-blue-600 text-white"
                : "bg-white border text-gray-600 hover:border-blue-300"
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-20 bg-gray-200 rounded-xl"></div>
          ))}
        </div>
      ) : (
        <div className="space-y-8">
          {Object.entries(grouped).map(([category, cats]) => (
            <div key={category}>
              <h2 className="text-lg font-semibold text-gray-800 capitalize mb-3">
                {category.replace("_", " ")}
                <span className="text-sm font-normal text-gray-400 ml-2">({cats.length} topics)</span>
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {cats.map((concept) => (
                  <ConceptCard key={concept.id} concept={concept} />
                ))}
              </div>
            </div>
          ))}
          {Object.keys(grouped).length === 0 && (
            <div className="text-center py-12 text-gray-400">
              No concepts found. Run the seed script to populate the concept graph.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ConceptCard({ concept }: { concept: Concept }) {
  const { data: mastery } = useQuery({
    queryKey: ["concept-mastery", concept.id],
    queryFn: () => conceptsApi.getMastery(concept.id).then((r) => r.data),
    staleTime: 2 * 60 * 1000,
  });

  const masteryScore = mastery?.mastery_score ?? 0;
  const difficultyStars = Math.round(concept.difficulty_base * 5);

  return (
    <div className="bg-white rounded-xl border p-4 hover:border-blue-200 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-medium text-gray-900 text-sm">{concept.name}</h3>
        <span className={`text-xs font-bold ${masteryColor(masteryScore)}`}>
          {(masteryScore * 100).toFixed(0)}%
        </span>
      </div>
      {concept.description && (
        <p className="text-xs text-gray-400 mb-3 line-clamp-2">{concept.description}</p>
      )}
      <div className="flex items-center justify-between">
        <div className="flex gap-0.5">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className={`w-2 h-2 rounded-full ${i < difficultyStars ? "bg-blue-400" : "bg-gray-200"}`}
            />
          ))}
        </div>
        <div className="flex items-center gap-2">
          <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${
                masteryScore >= 0.8 ? "bg-green-400" : masteryScore >= 0.5 ? "bg-blue-400" : masteryScore > 0 ? "bg-yellow-400" : "bg-gray-200"
              }`}
              style={{ width: `${masteryScore * 100}%` }}
            />
          </div>
          <span className="text-xs text-gray-400">{formatMastery(masteryScore)}</span>
        </div>
      </div>
      {mastery?.attempt_count > 0 && (
        <p className="text-xs text-gray-300 mt-1">{mastery.attempt_count} attempts</p>
      )}
    </div>
  );
}
