type PageTitleProps = {
  title: string;
  description: string;
  action?: React.ReactNode;
};


export function PageTitle({ title, description, action }: PageTitleProps) {
  return (
    <div className="flex flex-col gap-5 rounded-[26px] border border-white/70 bg-white/55 px-6 py-5 shadow-soft backdrop-blur-sm md:flex-row md:items-end md:justify-between">
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-sageDark/70">
          基于大语言模型的 RDFS 本体学习与评估系统
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">{title}</h1>
        <p className="max-w-3xl text-sm leading-7 text-slate-600">{description}</p>
      </div>
      {action}
    </div>
  );
}
