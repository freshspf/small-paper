import type { Metadata } from "next";

import "./globals.css";


export const metadata: Metadata = {
  title: "基于大语言模型的RDFS本体学习与评估系统",
  description: "面向本体学习、评测、解释标注与稳定性分析的一体化管理系统。",
};


export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
