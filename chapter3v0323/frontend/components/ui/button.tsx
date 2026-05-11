import { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";


const variants = {
  primary: "bg-ink text-white shadow-sm hover:bg-[#172029]",
  secondary: "bg-sage text-white shadow-sm hover:bg-sageDark",
  outline: "border border-line bg-white/88 text-ink shadow-sm hover:bg-mist",
};


type ButtonVariant = keyof typeof variants;


export function Button({
  className,
  variant = "primary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-xl px-4 py-2.5 text-sm font-medium transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-60",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
