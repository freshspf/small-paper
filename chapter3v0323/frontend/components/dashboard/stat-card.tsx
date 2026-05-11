import { Card } from "@/components/ui/card";


type StatCardProps = {
  title: string;
  value: string;
  description: string;
};


export function StatCard({ title, value, description }: StatCardProps) {
  return (
    <Card className="p-6">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-ink">{value}</p>
      <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
    </Card>
  );
}
