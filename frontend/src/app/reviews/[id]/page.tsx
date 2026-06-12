"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FindingsPanel } from "@/components/review/findings-panel";
import { HealthScore } from "@/components/review/health-score";
import { ReviewStats } from "@/components/review/review-stats";
import { API_URL } from "@/lib/config";

interface Finding {
  id: string;
  category: string;
  severity: string;
  title: string;
  description: string;
  evidence: {
    file_path: string;
    line_number: number | null;
    code_snippet: string;
  }[];
  impact: string;
  recommendation: string;
  rule_violated: string | null;
  context_violated: string | null;
  confidence: number;
  reward_score: number | null;
  suppressed: boolean;
}

interface ReviewDetail {
  review_id: string;
  system_name: string;
  diff_hash: string;
  diff_preview: string;
  spec_file: string;
  health_score: number;
  summary: string;
  findings: Finding[];
  suppressed_findings: Finding[];
  stats: {
    total_findings: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
    advisory: number;
    suppressed: number;
    avg_confidence: number;
  };
  reward_model_active: boolean;
  created_at: string;
}

export default function ReviewDetailPage() {
  const params = useParams();
  const reviewId = params.id as string;
  const [review, setReview] = useState<ReviewDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!reviewId) return;

    fetch(`${API_URL}/api/reviews/${reviewId}`)
      .then((r) => {
        if (!r.ok) {
          if (r.status === 404) throw new Error("Review not found");
          throw new Error("Failed to fetch review");
        }
        return r.json();
      })
      .then((data: ReviewDetail) => {
        setReview(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [reviewId]);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-6">
          <h1 className="text-2xl font-bold tracking-tight">Loading...</h1>
        </div>
        <Card className="animate-pulse">
          <CardContent className="py-8">
            <div className="h-32 bg-muted rounded" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !review) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-6">
          <Link href="/reviews">
            <Button variant="ghost" size="sm">
              &larr; Back to Reviews
            </Button>
          </Link>
        </div>
        <Card className="border-destructive">
          <CardContent className="pt-4">
            <p className="text-destructive text-sm">
              {error || "Review not found"}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link href="/reviews">
            <Button variant="ghost" size="sm" className="mb-2">
              &larr; Back to Reviews
            </Button>
          </Link>
          <h1 className="text-2xl font-bold tracking-tight">
            Review {review.review_id}
          </h1>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="outline" className="text-xs">
              {review.system_name}
            </Badge>
            {review.created_at && (
              <span className="text-xs text-muted-foreground">
                {new Date(review.created_at).toLocaleString()}
              </span>
            )}
            {review.reward_model_active && (
              <Badge className="bg-green-100 text-green-800 text-xs">
                Reward Model Active
              </Badge>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left — Diff Preview + Summary */}
        <div className="lg:col-span-4 space-y-4">
          {/* Summary */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm">{review.summary}</p>
            </CardContent>
          </Card>

          {/* Diff Preview */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-mono">Diff Preview</CardTitle>
              <CardDescription className="text-xs">
                Hash: {review.diff_hash}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[300px]">
                <pre className="p-4 text-xs font-mono whitespace-pre-wrap text-muted-foreground leading-relaxed">
                  {review.diff_preview || "No preview available"}
                </pre>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Right — Scores + Findings */}
        <div className="lg:col-span-8 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <HealthScore score={review.health_score} />
            <ReviewStats
              stats={review.stats}
              rewardActive={review.reward_model_active}
            />
          </div>

          <Tabs defaultValue="findings">
            <TabsList>
              <TabsTrigger value="findings">
                Findings ({review.findings.length})
              </TabsTrigger>
              {review.suppressed_findings.length > 0 && (
                <TabsTrigger value="suppressed">
                  Suppressed ({review.suppressed_findings.length})
                </TabsTrigger>
              )}
            </TabsList>
            <TabsContent value="findings">
              <FindingsPanel findings={review.findings} />
            </TabsContent>
            {review.suppressed_findings.length > 0 && (
              <TabsContent value="suppressed">
                <FindingsPanel findings={review.suppressed_findings} />
              </TabsContent>
            )}
          </Tabs>
        </div>
      </div>
    </div>
  );
}
