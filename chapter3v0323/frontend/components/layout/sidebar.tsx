"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";


const items = [
  { href: "/", label: "系统首页" },
  { href: "/models", label: "模型管理" },
  { href: "/prompt-templates", label: "提示词模板" },
  { href: "/datasets", label: "评测数据管理" },
  { href: "/evaluations", label: "评测任务" },
  { href: "/ontology", label: "本体学习任务" },
  { href: "/exports", label: "导出中心" },
];


export function Sidebar() {
  const pathname = usePathname();

  function isActive(href: string) {
    if (href === "/") {
      return pathname === "/";
    }
    return pathname === href || pathname.startsWith(`${href}/`);
  }

  return (
    <aside className="flex min-h-screen w-[272px] flex-col border-r border-white/50 bg-[linear-gradient(180deg,rgba(241,238,231,0.96)_0%,rgba(247,248,247,0.94)_100%)] px-6 py-8 backdrop-blur">
      <div className="space-y-2">
        <div className="inline-flex rounded-full bg-sage/15 px-3 py-1 text-xs font-semibold uppercase tracking-[0.28em] text-sageDark">
          管理系统
        </div>
        <h2 className="text-xl font-semibold text-ink">RDFS 本体学习与评估</h2>
        <p className="text-sm leading-6 text-slate-600">
          覆盖本体学习、评测分析、报告导出与本体图谱管理的一体化系统。
        </p>
      </div>

      <nav className="mt-10 flex flex-1 flex-col gap-2.5">
        {items.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "rounded-xl border border-transparent px-4 py-3 text-sm font-medium text-slate-700 transition-all hover:border-white/70 hover:bg-white/70 hover:text-ink",
              isActive(item.href) ? "border-white/80 bg-white shadow-sm text-ink" : "",
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
