"use client";

import { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AnnotationChart } from "@/components/metrics/annotation-chart";
import { ModelMetrics } from "@/components/metrics/model-metrics";
import { API_URL } from "@/lib/config";

interface Stats {
  annotation_count: number;
  cold_start_threshold: number;
  reward_model_active: boolean;
  annotations_needed: number;
}

interface RetrainResult {
  status: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  annotation_count: number;
}

export default function MetricsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [retrainResult, setRetrainResult] = useState<RetrainResult | null>(
    null,
  );
  const [isRetraining, setIsRetraining] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = () => {
    fetch(`${API_URL}/api/feedback/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => setError("Backend not running"));
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleRetrain = async () => {
    setIsRetraining(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/feedback/retrain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail);
      }
      const data = await response.json();
      setRetrainResult(data);
      fetchStats();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsRetraining(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Metrics & Learning
          </h1>
          <p className="text-muted-foreground mt-1">
            Reward model performance and annotation analytics
          </p>
        </div>
        <Button
          onClick={handleRetrain}
          disabled={
            isRetraining ||
            (!stats?.reward_model_active &&
              (stats?.annotations_needed ?? 1) > 0)
          }
        >
          {isRetraining ? "Retraining..." : "Retrain Model"}
        </Button>
      </div>

      {error && (
        <Card className="mb-6 border-destructive">
          <CardContent className="pt-4">
            <p className="text-destructive text-sm">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Model Status Banner */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div>
                <p className="text-sm font-medium">Reward Model Status</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {stats?.reward_model_active
                    ? "Actively filtering findings by confidence"
                    : `Need ${stats?.annotations_needed ?? "?"} more annotations to activate`}
                </p>
              </div>
            </div>
            {stats?.reward_model_active ? (
              <Badge className="bg-green-100 text-green-800">Active</Badge>
            ) : (
              <Badge variant="secondary">Inactive</Badge>
            )}
          </div>
          {stats && !stats.reward_model_active && (
            <div className="mt-4">
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all"
                  style={{
                    width: `${Math.min(100, (stats.annotation_count / stats.cold_start_threshold) * 100)}%`,
                  }}
                />
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {stats.annotation_count} / {stats.cold_start_threshold}{" "}
                annotations
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Annotation Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Annotation Distribution</CardTitle>
            <CardDescription>
              Breakdown of human feedback labels
            </CardDescription>
          </CardHeader>
          <CardContent>
            <AnnotationChart />
          </CardContent>
        </Card>

        {/* Model Metrics */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Model Performance</CardTitle>
            <CardDescription>
              {retrainResult
                ? "Latest training results"
                : "Train the model to see metrics"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ModelMetrics result={retrainResult} />
          </CardContent>
        </Card>
      </div>

      {/* Performance Over Time (simulated for demo) */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">Learning Curve</CardTitle>
          <CardDescription>
            How model accuracy improves with more annotations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <LearningCurve annotationCount={stats?.annotation_count ?? 0} />
        </CardContent>
      </Card>
    </div>
  );
}

function LearningCurve({ annotationCount }: { annotationCount: number }) {
  // Simulated learning curve data points
  const data = [
    { annotations: 0, accuracy: 50, falsePositives: 35 },
    { annotations: 5, accuracy: 55, falsePositives: 30 },
    { annotations: 10, accuracy: 60, falsePositives: 25 },
    { annotations: 15, accuracy: 65, falsePositives: 20 },
    { annotations: 20, accuracy: 71, falsePositives: 15 },
    { annotations: 30, accuracy: 78, falsePositives: 12 },
    { annotations: 50, accuracy: 85, falsePositives: 8 },
    { annotations: 100, accuracy: 92, falsePositives: 5 },
  ];

  // Filter to show only up to current annotation count + projections
  const activeData = data.filter((d) => d.annotations <= annotationCount);
  const projectedData = data.filter((d) => d.annotations > annotationCount);

  return (
    <div className="space-y-4">
      {/* Chart using basic bars (recharts would be better but keeping it simple) */}
      <div className="grid grid-cols-8 gap-1 items-end h-40">
        {data.map((point) => {
          const isActive = point.annotations <= annotationCount;
          return (
            <div
              key={point.annotations}
              className="flex flex-col items-center gap-1"
            >
              <div className="w-full flex flex-col items-center gap-0.5">
                <div
                  className={`w-full rounded-t ${isActive ? "bg-green-500" : "bg-green-200"}`}
                  style={{ height: `${point.accuracy * 1.4}px` }}
                  title={`Accuracy: ${point.accuracy}%`}
                />
                <div
                  className={`w-full rounded-b ${isActive ? "bg-red-400" : "bg-red-100"}`}
                  style={{ height: `${point.falsePositives * 3}px` }}
                  title={`FP Rate: ${point.falsePositives}%`}
                />
              </div>
              <span className="text-[10px] text-muted-foreground">
                {point.annotations}
              </span>
            </div>
          );
        })}
      </div>
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-green-500 rounded" /> Accuracy
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-red-400 rounded" /> False Positive Rate
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-green-200 rounded" /> Projected
        </span>
      </div>
      <p className="text-xs text-muted-foreground">
        X-axis: number of annotations | Current: {annotationCount} annotations
      </p>
    </div>
  );
}
