"use client";

import { Card, CardContent } from "@/components/ui/card";

interface HealthScoreProps {
  score: number;
}

export function HealthScore({ score }: HealthScoreProps) {
  const getColor = () => {
    if (score >= 80) return "text-green-500";
    if (score >= 60) return "text-yellow-500";
    if (score >= 40) return "text-orange-500";
    return "text-red-500";
  };

  const getBg = () => {
    if (score >= 80) return "bg-green-50 border-green-200";
    if (score >= 60) return "bg-yellow-50 border-yellow-200";
    if (score >= 40) return "bg-orange-50 border-orange-200";
    return "bg-red-50 border-red-200";
  };

  return (
    <Card className={getBg()}>
      <CardContent className="pt-4 text-center">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Health Score
        </p>
        <p className={`text-4xl font-bold mt-1 ${getColor()}`}>{score}</p>
        <p className="text-xs text-muted-foreground mt-1">/ 100</p>
      </CardContent>
    </Card>
  );
}
