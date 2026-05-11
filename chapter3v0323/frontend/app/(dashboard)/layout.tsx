import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";


export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-transparent">
      <Sidebar />
      <main className="flex-1 px-6 py-6 lg:px-10 lg:py-8">
        <Topbar />
        <div className="mt-8 space-y-8">{children}</div>
      </main>
    </div>
  );
}
