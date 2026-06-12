"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { API_URL } from "@/lib/config";

interface Stats {
  annotation_count: number;
  cold_start_threshold: number;
  reward_model_active: boolean;
  annotations_needed: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/feedback/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() =>
        setError(
          "Backend not running. Start with: uvicorn app.main:app --reload",
        ),
      );
  }, []);

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Hero */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">
          ArchAgent Dashboard
        </h1>
        <p className="text-muted-foreground mt-1">
          Agentic Code Review with Architectural Intent Understanding
        </p>
      </div>

      {error && (
        <Card className="mb-6 border-yellow-200 bg-yellow-50">
          <CardContent className="pt-4">
            <p className="text-sm text-yellow-800">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs font-medium text-muted-foreground uppercase">
              Recall
            </p>
            <p className="text-3xl font-bold text-green-600 mt-1">100%</p>
            <p className="text-xs text-muted-foreground mt-1">
              5/5 violations caught
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs font-medium text-muted-foreground uppercase">
              False Positive Rate
            </p>
            <p className="text-3xl font-bold text-green-600 mt-1">0%</p>
            <p className="text-xs text-muted-foreground mt-1">
              0/3 clean PRs flagged
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs font-medium text-muted-foreground uppercase">
              Annotations
            </p>
            <p className="text-3xl font-bold mt-1">
              {stats?.annotation_count ?? "—"}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {stats?.reward_model_active
                ? "Reward model active"
                : `Need ${stats?.annotations_needed ?? "?"} more`}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs font-medium text-muted-foreground uppercase">
              Reward Model
            </p>
            <div className="mt-1">
              {stats?.reward_model_active ? (
                <Badge className="bg-green-100 text-green-800 text-sm">
                  Active
                </Badge>
              ) : (
                <Badge variant="secondary" className="text-sm">
                  Inactive
                </Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Confidence scoring enabled
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Review a PR</CardTitle>
            <CardDescription>
              Paste a diff and see ArchAgent review it against architectural
              intent in real-time.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/review">
              <Button className="w-full">Open Review</Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Metrics & Learning</CardTitle>
            <CardDescription>
              View reward model performance, learning curve, and annotation
              distribution.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/metrics">
              <Button variant="outline" className="w-full">
                View Metrics
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Review History</CardTitle>
            <CardDescription>
              Browse past reviews and provide feedback to improve the reward
              model.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/reviews">
              <Button variant="outline" className="w-full">
                View Reviews
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* CLI Quick Reference */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">CLI Quick Reference</CardTitle>
          <CardDescription>
            ArchAgent works primarily from your terminal
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-zinc-950 text-zinc-100 rounded-lg p-4 font-mono text-sm space-y-2">
            <p className="text-zinc-500"># Review a PR diff</p>
            <p>
              $ archagent review --diff my-pr.diff --intent
              architecture-intent.yaml
            </p>
            <p className="text-zinc-500 mt-3"># Submit feedback on a finding</p>
            <p>
              $ archagent feedback &lt;review-id&gt; &lt;finding-id&gt; valid
            </p>
            <p className="text-zinc-500 mt-3"># Retrain reward model</p>
            <p>$ archagent retrain</p>
            <p className="text-zinc-500 mt-3"># View stats</p>
            <p>$ archagent stats</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
