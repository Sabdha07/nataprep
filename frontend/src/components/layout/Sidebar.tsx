"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/practice/adaptive", label: "Adaptive Practice", icon: "🧠" },
  { href: "/practice/concept", label: "Concept Mode", icon: "📚" },
  { href: "/practice/mock-test", label: "Mock Test", icon: "📝" },
  { href: "/practice/drawing", label: "Drawing", icon: "🎨" },
  { href: "/analytics", label: "Analytics", icon: "📈" },
  { href: "/concepts", label: "Concept Map", icon: "🗺️" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();

  return (
    <aside className="w-60 min-h-screen bg-gray-950 flex flex-col">
      {/* Logo */}
      <div className="p-5 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-blue-500 rounded-md flex items-center justify-center">
            <span className="text-white font-bold text-xs">N</span>
          </div>
          <span className="font-bold text-white">NATAPrep</span>
          <span className="text-xs bg-blue-900 text-blue-300 px-1.5 py-0.5 rounded text-[10px]">2026</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-0.5">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
              pathname.startsWith(item.href)
                ? "bg-blue-600 text-white"
                : "text-gray-400 hover:text-white hover:bg-gray-800"
            )}
          >
            <span className="text-base">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>

      {/* Admin link */}
      {user?.role === "admin" && (
        <Link
          href="/admin"
          className={cn(
            "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
            pathname.startsWith("/admin")
              ? "bg-blue-600 text-white"
              : "text-gray-400 hover:text-white hover:bg-gray-800"
          )}
        >
          <span className="text-base">⚙️</span>
          Admin
        </Link>
      )}

      {/* User */}
      <div className="p-3 border-t border-gray-800">
        <div className="flex items-center gap-3 px-3 py-2 rounded-lg">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
            <span className="text-white text-sm font-medium">
              {user?.full_name?.[0] || user?.email?.[0] || "U"}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-white text-sm font-medium truncate">
              {user?.full_name || "Student"}
            </p>
            <p className="text-gray-400 text-xs truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="mt-1 w-full text-left px-3 py-1.5 text-xs text-gray-500 hover:text-gray-300 rounded transition-colors"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
