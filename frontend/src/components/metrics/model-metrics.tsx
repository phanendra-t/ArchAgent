"use client";

import { Progress } from "@/components/ui/progress";

interface RetrainResult {
  status: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  annotation_count: number;
}

interface ModelMetricsProps {
  result: RetrainResult | null;
}

export function ModelMetrics({ result }: ModelMetricsProps) {
  if (!result) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Click "Retrain Model" to train on current annotations and see performance metrics.
        </p>
        <div className="space-y-3">
          {["Accuracy", "Precision", "Recall", "F1 Score"].map((metric) => (
            <div key={metric}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-muted-foreground">{metric}</span>
                <span className="text-muted-foreground">—</span>
              </div>
              <Progress value={0} className="h-2" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const metrics = [
    { name: "Accuracy", value: result.accuracy },
    { name: "Precision", value: result.precision },
    { name: "Recall", value: result.recall },
    { name: "F1 Score", value: result.f1 },
  ];

  const getColor = (value: number) => {
    if (value >= 0.8) return "text-green-600";
    if (value >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        {metrics.map((metric) => (
          <div key={metric.name}>
            <div className="flex justify-between text-xs mb-1">
              <span className="font-medium">{metric.name}</span>
              <span className={`font-bold ${getColor(metric.value)}`}>
                {(metric.value * 100).toFixed(1)}%
              </span>
            </div>
            <Progress value={metric.value * 100} className="h-2" />
          </div>
        ))}
      </div>
      <div className="pt-2 border-t">
        <p className="text-xs text-muted-foreground">
          Trained on {result.annotation_count} annotations
        </p>
      </div>
    </div>
  );
}
