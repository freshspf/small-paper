import { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";


export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-[26px] border border-white/75 bg-card/92 shadow-soft backdrop-blur-sm",
        className,
      )}
      {...props}
    />
  );
}
