"use client";

import { useState, useEffect, useRef } from "react";
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
import { Textarea } from "@/components/ui/textarea";
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

interface ReviewResult {
  review_id: string;
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
}

// ──── Global review state (persists across page navigations) ────
let globalReviewResult: ReviewResult | null = null;
let globalReviewError: string | null = null;
let globalIsReviewing = false;
let globalListeners: Set<() => void> = new Set();

function notifyListeners() {
  globalListeners.forEach((fn) => fn());
}

async function startGlobalReview(diff: string) {
  globalIsReviewing = true;
  globalReviewResult = null;
  globalReviewError = null;
  notifyListeners();

  try {
    const response = await fetch(`${API_URL}/api/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ diff }),
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || "Review failed");
    }

    const data: ReviewResult = await response.json();
    globalReviewResult = data;
    globalReviewError = null;
  } catch (err: any) {
    globalReviewError = err.message || "Failed to connect to engine";
    globalReviewResult = null;
  } finally {
    globalIsReviewing = false;
    notifyListeners();
  }
}

function useGlobalReviewState() {
  const [, forceRender] = useState(0);

  useEffect(() => {
    const listener = () => forceRender((n) => n + 1);
    globalListeners.add(listener);
    return () => {
      globalListeners.delete(listener);
    };
  }, []);

  return {
    result: globalReviewResult,
    error: globalReviewError,
    isReviewing: globalIsReviewing,
  };
}

// ──── Component ────

export default function ReviewPage() {
  const [diffInput, setDiffInput] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { result, error, isReviewing } = useGlobalReviewState();

  const handleReview = () => {
    if (diffInput.trim() && !globalIsReviewing) {
      startGlobalReview(diffInput.trim());
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const content = event.target?.result;
        if (typeof content === "string") {
          setDiffInput(content);
        }
      };
      reader.readAsText(file);
    }
  };

  const handleClear = () => {
    setDiffInput("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const lineCount = diffInput ? diffInput.split("\n").length : 0;

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Review</h1>
        <p className="text-muted-foreground mt-1">
          Paste a unified diff to analyze it against your architectural intent
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Panel — Diff Input */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">PR Diff</CardTitle>
              <CardDescription className="text-xs">
                Paste a unified diff (git diff output) or upload a .diff file
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Textarea
                placeholder={`--- a/src/orders/services/order.service.ts\n+++ b/src/orders/services/order.service.ts\n@@ -1,5 +1,7 @@\n import { OrderRepository } from '../repositories/order.repository';\n+import { NotificationService } from '../../notifications/services/notification.service';\n \n export class OrderService {\n   // ...\n+  private notifications = new NotificationService();\n }`}
                className="font-mono text-xs min-h-[400px] resize-none"
                value={diffInput}
                onChange={(e) => setDiffInput(e.target.value)}
                disabled={isReviewing}
              />

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".diff,.patch,.txt"
                    className="hidden"
                    onChange={handleFileUpload}
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isReviewing}
                  >
                    Upload .diff
                  </Button>
                  {diffInput && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleClear}
                      disabled={isReviewing}
                    >
                      Clear
                    </Button>
                  )}
                </div>
                {diffInput && (
                  <span className="text-xs text-muted-foreground">
                    {lineCount} lines
                  </span>
                )}
              </div>
            </CardContent>
          </Card>

          <Button
            className="w-full"
            size="lg"
            onClick={handleReview}
            disabled={isReviewing || !diffInput.trim()}
          >
            {isReviewing
              ? "Reviewing... (safe to switch tabs)"
              : "Review Diff"}
          </Button>

          {/* CLI hint */}
          <Card className="bg-muted/50">
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">
                Or use the CLI:{" "}
                <code className="bg-background px-1.5 py-0.5 rounded text-foreground">
                  git diff main | archagent review --diff -
                </code>
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Right Panel — Results */}
        <div className="space-y-4">
          {error && (
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
          )}

          {result && (
            <>
              <div className="grid grid-cols-2 gap-3">
                <HealthScore score={result.health_score} />
                <ReviewStats
                  stats={result.stats}
                  rewardActive={result.reward_model_active}
                />
              </div>

              <Card>
                <CardContent className="pt-4">
                  <p className="text-sm">{result.summary}</p>
                  <div className="flex gap-2 mt-2">
                    <Badge variant="outline" className="text-xs">
                      Review: {result.review_id}
                    </Badge>
                    {result.reward_model_active && (
                      <Badge className="bg-green-100 text-green-800 text-xs">
                        Reward Model Active
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Tabs defaultValue="findings">
                <TabsList>
                  <TabsTrigger value="findings">
                    Findings ({result.findings.length})
                  </TabsTrigger>
                  {result.suppressed_findings.length > 0 && (
                    <TabsTrigger value="suppressed">
                      Suppressed ({result.suppressed_findings.length})
                    </TabsTrigger>
                  )}
                </TabsList>
                <TabsContent value="findings">
                  <FindingsPanel findings={result.findings} />
                </TabsContent>
                {result.suppressed_findings.length > 0 && (
                  <TabsContent value="suppressed">
                    <FindingsPanel findings={result.suppressed_findings} />
                  </TabsContent>
                )}
              </Tabs>
            </>
          )}

          {!result && !error && !isReviewing && (
            <Card className="h-[500px] flex items-center justify-center">
              <CardContent className="text-center">
                <div className="space-y-2">
                  <p className="text-muted-foreground text-lg">
                    Ready to Review
                  </p>
                  <p className="text-muted-foreground text-sm">
                    Paste a diff and click "Review Diff" to analyze it
                  </p>
                  <p className="text-xs text-muted-foreground mt-4">
                    The review runs against your mounted architecture-intent.yaml
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {isReviewing && (
            <Card className="h-[500px] flex items-center justify-center">
              <CardContent className="text-center">
                <div className="space-y-3">
                  <div className="h-8 w-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
                  <p className="text-foreground font-medium">Reviewing PR...</p>
                  <p className="text-muted-foreground text-sm">
                    Multi-agent analysis in progress
                  </p>
                  <p className="text-xs text-green-600 mt-4">
                    Safe to switch tabs — review continues in background
                  </p>
                  <div className="text-xs text-muted-foreground space-y-1 mt-2">
                    <p>1. Parsing diff and mapping contexts</p>
                    <p>2. Running context boundary reviewer</p>
                    <p>3. Running layer violation reviewer</p>
                    <p>4. Running security boundary reviewer</p>
                    <p>5. Synthesizing and defending findings</p>
                    <p>6. Scoring with reward model</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
