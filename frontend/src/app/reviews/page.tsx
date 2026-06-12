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
import { API_URL } from "@/lib/config";

interface ReviewSummary {
  review_id: string;
  system_name: string;
  diff_hash: string;
  diff_preview: string;
  spec_file: string;
  health_score: number;
  summary: string;
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

interface ReviewsResponse {
  reviews: ReviewSummary[];
  total: number;
}

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<ReviewSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/reviews?limit=50`)
      .then((r) => {
        if (!r.ok) throw new Error("Failed to fetch reviews");
        return r.json();
      })
      .then((data: ReviewsResponse) => {
        setReviews(data.reviews);
        setTotal(data.total);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to connect to engine");
        setLoading(false);
      });
  }, []);

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBg = (score: number) => {
    if (score >= 80) return "bg-green-50";
    if (score >= 60) return "bg-yellow-50";
    return "bg-red-50";
  };

  const formatTimestamp = (iso: string) => {
    const date = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMin / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMin < 1) return "just now";
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight">Review History</h1>
          <p className="text-muted-foreground mt-1">Loading reviews...</p>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="py-4">
                <div className="h-12 bg-muted rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight">Review History</h1>
        </div>
        <Card className="border-destructive">
          <CardContent className="pt-4">
            <p className="text-destructive text-sm">{error}</p>
            <p className="text-xs text-muted-foreground mt-2">
              Make sure the engine is running:{" "}
              <code className="bg-muted px-1.5 py-0.5 rounded">
                docker compose up -d
              </code>
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight">Review History</h1>
        <p className="text-muted-foreground mt-1">
          {total} review{total !== 1 ? "s" : ""} performed
        </p>
      </div>

      {reviews.length === 0 ? (
        <Card className="py-12">
          <CardContent className="text-center">
            <p className="text-muted-foreground text-lg mb-2">
              No reviews yet
            </p>
            <p className="text-muted-foreground text-sm mb-4">
              Submit your first diff on the{" "}
              <Link href="/review" className="underline">
                Review page
              </Link>{" "}
              or via the CLI
            </p>
            <div className="bg-zinc-950 text-zinc-100 rounded-lg p-3 font-mono text-sm inline-block">
              git diff main | archagent review --diff -
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {reviews.map((review) => (
            <Link
              key={review.review_id}
              href={`/reviews/${review.review_id}`}
              className="block"
            >
              <Card className="hover:border-foreground/20 transition-colors cursor-pointer">
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      {/* Score */}
                      <div
                        className={`w-12 h-12 rounded-lg flex items-center justify-center ${getScoreBg(review.health_score)}`}
                      >
                        <span
                          className={`text-lg font-bold ${getScoreColor(review.health_score)}`}
                        >
                          {review.health_score}
                        </span>
                      </div>

                      {/* Info */}
                      <div>
                        <p className="font-mono text-sm">
                          {review.summary
                            ? review.summary.slice(0, 80) +
                              (review.summary.length > 80 ? "..." : "")
                            : `Review ${review.review_id}`}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-muted-foreground">
                            ID: {review.review_id}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {review.system_name}
                          </span>
                          {review.created_at && (
                            <span className="text-xs text-muted-foreground">
                              {formatTimestamp(review.created_at)}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Findings badges */}
                    <div className="flex items-center gap-2">
                      {review.stats.total_findings === 0 ? (
                        <Badge className="bg-green-100 text-green-800">
                          Clean
                        </Badge>
                      ) : (
                        <>
                          {review.stats.critical > 0 && (
                            <Badge variant="destructive">
                              {review.stats.critical} critical
                            </Badge>
                          )}
                          {review.stats.high > 0 && (
                            <Badge className="bg-orange-500 text-white">
                              {review.stats.high} high
                            </Badge>
                          )}
                          {review.stats.medium > 0 && (
                            <Badge className="bg-yellow-500 text-white">
                              {review.stats.medium} medium
                            </Badge>
                          )}
                          {review.stats.low > 0 && (
                            <Badge variant="secondary">
                              {review.stats.low} low
                            </Badge>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
