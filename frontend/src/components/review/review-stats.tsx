"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Stats {
  total_findings: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  advisory: number;
  suppressed: number;
  avg_confidence: number;
}

interface ReviewStatsProps {
  stats: Stats;
  rewardActive: boolean;
}

export function ReviewStats({ stats, rewardActive }: ReviewStatsProps) {
  return (
    <Card>
      <CardContent className="pt-4">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
          Findings Breakdown
        </p>
        <div className="space-y-1">
          {stats.critical > 0 && (
            <div className="flex justify-between items-center">
              <Badge variant="destructive" className="text-xs">Critical</Badge>
              <span className="text-sm font-mono">{stats.critical}</span>
            </div>
          )}
          {stats.high > 0 && (
            <div className="flex justify-between items-center">
              <Badge className="bg-orange-500 text-xs">High</Badge>
              <span className="text-sm font-mono">{stats.high}</span>
            </div>
          )}
          {stats.medium > 0 && (
            <div className="flex justify-between items-center">
              <Badge className="bg-yellow-500 text-white text-xs">Medium</Badge>
              <span className="text-sm font-mono">{stats.medium}</span>
            </div>
          )}
          {stats.low > 0 && (
            <div className="flex justify-between items-center">
              <Badge variant="secondary" className="text-xs">Low</Badge>
              <span className="text-sm font-mono">{stats.low}</span>
            </div>
          )}
          {stats.suppressed > 0 && (
            <div className="flex justify-between items-center text-muted-foreground">
              <span className="text-xs">Suppressed</span>
              <span className="text-sm font-mono">{stats.suppressed}</span>
            </div>
          )}
        </div>
        {rewardActive && (
          <p className="text-xs text-muted-foreground mt-2">
            Confidence: {(stats.avg_confidence * 100).toFixed(0)}%
          </p>
        )}
      </CardContent>
    </Card>
  );
}
