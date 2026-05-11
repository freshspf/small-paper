import { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";


const variants = {
  default: "bg-sage/15 text-sageDark",
  success: "bg-emerald-100 text-emerald-700",
  warning: "bg-amber-100 text-amber-700",
  muted: "bg-slate-100 text-slate-600",
};


type BadgeVariant = keyof typeof variants;


export function Badge({
  className,
  variant = "default",
  ...props
}: HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-white/70 px-3 py-1 text-xs font-medium shadow-sm",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
