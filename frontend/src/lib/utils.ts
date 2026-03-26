import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatMastery(score: number): string {
  if (score < 0.2) return "Not Started";
  if (score < 0.4) return "Beginner";
  if (score < 0.6) return "Developing";
  if (score < 0.8) return "Proficient";
  return "Mastered";
}

export function masteryColor(score: number): string {
  if (score < 0.4) return "text-red-500";
  if (score < 0.6) return "text-yellow-500";
  if (score < 0.8) return "text-blue-500";
  return "text-green-500";
}

export function difficultyLabel(difficulty: number): string {
  if (difficulty < 0.35) return "Easy";
  if (difficulty < 0.55) return "Medium";
  if (difficulty < 0.75) return "Hard";
  return "Very Hard";
}

export function difficultyClass(difficulty: number): string {
  if (difficulty < 0.35) return "difficulty-easy";
  if (difficulty < 0.55) return "difficulty-medium";
  return "difficulty-hard";
}
