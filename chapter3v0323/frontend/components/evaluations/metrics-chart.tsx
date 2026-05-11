"use client";

import { useEffect, useRef } from "react";
import * as echarts from "echarts";

import { Card } from "@/components/ui/card";


type MetricsChartProps = {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
};


export function MetricsChart({ accuracy, precision, recall, f1 }: MetricsChartProps) {
  const chartRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!chartRef.current) {
      return;
    }

    const chart = echarts.init(chartRef.current);
    chart.setOption({
      animation: false,
      grid: {
        left: 40,
        right: 20,
        top: 40,
        bottom: 30,
      },
      tooltip: {
        trigger: "axis",
        axisPointer: {
          type: "shadow",
        },
      },
      xAxis: {
        type: "category",
        data: ["Accuracy", "Precision", "Recall", "F1"],
        axisLine: {
          lineStyle: {
            color: "#D8DEE4",
          },
        },
        axisLabel: {
          color: "#4B5563",
        },
      },
      yAxis: {
        type: "value",
        min: 0,
        max: 1,
        axisLine: {
          show: false,
        },
        splitLine: {
          lineStyle: {
            color: "#E5E7EB",
          },
        },
        axisLabel: {
          color: "#6B7280",
        },
      },
      series: [
        {
          type: "bar",
          barWidth: 36,
          data: [accuracy, precision, recall, f1],
          itemStyle: {
            color: "#8FA8A1",
            borderRadius: [10, 10, 0, 0],
          },
          label: {
            show: true,
            position: "top",
            color: "#1F2933",
            formatter: ({ value }: { value: number }) => value.toFixed(3),
          },
        },
      ],
    });

    const handleResize = () => chart.resize();
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.dispose();
    };
  }, [accuracy, precision, recall, f1]);

  return (
    <Card className="p-6">
      <div className="mb-5">
        <h3 className="text-lg font-semibold text-ink">整体指标柱状图</h3>
        <p className="text-sm text-slate-600">基于后端统计接口生成 Accuracy、Precision、Recall 与 F1 对比图。</p>
      </div>
      <div ref={chartRef} className="h-[320px] w-full" />
    </Card>
  );
}
