"use client";

import { useState } from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { API_URL } from "@/lib/config";

interface Evidence {
  file_path: string;
  line_number: number | null;
  code_snippet: string;
}

interface Finding {
  id: string;
  category: string;
  severity: string;
  title: string;
  description: string;
  evidence: Evidence[];
  impact: string;
  recommendation: string;
  rule_violated: string | null;
  context_violated: string | null;
  confidence: number;
  reward_score: number | null;
  suppressed: boolean;
}

interface FindingsPanelProps {
  findings: Finding[];
}

export function FindingsPanel({ findings }: FindingsPanelProps) {
  const [feedbackState, setFeedbackState] = useState<Record<string, string>>(
    {},
  );

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "critical":
        return <Badge variant="destructive">Critical</Badge>;
      case "high":
        return <Badge className="bg-orange-500">High</Badge>;
      case "medium":
        return <Badge className="bg-yellow-500 text-white">Medium</Badge>;
      case "low":
        return <Badge variant="secondary">Low</Badge>;
      default:
        return <Badge variant="outline">Advisory</Badge>;
    }
  };

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      bounded_context_violation: "Context Boundary",
      layer_violation: "Layer Violation",
      security_boundary_violation: "Security",
      communication_pattern_violation: "Communication Pattern",
      dependency_rule_violation: "Dependency Rule",
      principle_violation: "Principle",
    };
    return labels[category] || category;
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.7) {
      return (
        <Badge
          variant="outline"
          className="text-green-600 border-green-300 text-xs"
        >
          High Confidence
        </Badge>
      );
    }
    if (confidence >= 0.4) {
      return (
        <Badge
          variant="outline"
          className="text-yellow-600 border-yellow-300 text-xs"
        >
          Uncertain
        </Badge>
      );
    }
    return (
      <Badge variant="outline" className="text-red-600 border-red-300 text-xs">
        Low Confidence
      </Badge>
    );
  };

  const handleFeedback = async (findingId: string, label: string) => {
    setFeedbackState((prev) => ({ ...prev, [findingId]: label }));

    try {
      await fetch(`${API_URL}/api/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          review_id: "current",
          finding_id: findingId,
          label,
        }),
      });
    } catch (err) {
      console.error("Failed to submit feedback:", err);
    }
  };

  if (findings.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6 text-center text-muted-foreground">
          No findings to display.
        </CardContent>
      </Card>
    );
  }

  return (
    <Accordion multiple className="space-y-2">
      {findings.map((finding) => (
        <AccordionItem
          key={finding.id}
          value={finding.id}
          className="border rounded-lg px-4"
        >
          <AccordionTrigger className="hover:no-underline">
            <div className="flex items-center gap-3 text-left">
              {getSeverityBadge(finding.severity)}
              <span className="font-medium text-sm">{finding.title}</span>
              <Badge variant="outline" className="text-xs">
                {getCategoryLabel(finding.category)}
              </Badge>
              {finding.reward_score !== null &&
                getConfidenceBadge(finding.confidence)}
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-4 pt-2">
              {/* Description */}
              <p className="text-sm">{finding.description}</p>

              {/* Evidence */}
              {finding.evidence.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground uppercase mb-2">
                    Evidence
                  </p>
                  {finding.evidence.map((ev, i) => (
                    <div key={i} className="bg-muted rounded-md p-3 mb-2">
                      <p className="text-xs text-muted-foreground mb-1">
                        {ev.file_path}
                        {ev.line_number ? `:${ev.line_number}` : ""}
                      </p>
                      <code className="text-xs font-mono block whitespace-pre-wrap">
                        {ev.code_snippet}
                      </code>
                    </div>
                  ))}
                </div>
              )}

              {/* Impact */}
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase mb-1">
                  Impact
                </p>
                <p className="text-sm">{finding.impact}</p>
              </div>

              {/* Recommendation */}
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase mb-1">
                  Recommendation
                </p>
                <p className="text-sm">{finding.recommendation}</p>
              </div>

              {/* Rule reference */}
              {finding.rule_violated && (
                <div>
                  <p className="text-xs text-muted-foreground">
                    Rule:{" "}
                    <code className="bg-muted px-1 rounded">
                      {finding.rule_violated}
                    </code>
                  </p>
                </div>
              )}

              <Separator />

              {/* Feedback buttons */}
              <div className="flex items-center gap-2">
                <p className="text-xs text-muted-foreground mr-2">
                  Is this valid?
                </p>
                <Button
                  size="sm"
                  variant={
                    feedbackState[finding.id] === "valid"
                      ? "default"
                      : "outline"
                  }
                  className="text-xs h-7"
                  onClick={() => handleFeedback(finding.id, "valid")}
                >
                  Valid
                </Button>
                <Button
                  size="sm"
                  variant={
                    feedbackState[finding.id] === "false_positive"
                      ? "destructive"
                      : "outline"
                  }
                  className="text-xs h-7"
                  onClick={() => handleFeedback(finding.id, "false_positive")}
                >
                  False Positive
                </Button>
                <Button
                  size="sm"
                  variant={
                    feedbackState[finding.id] === "partial"
                      ? "secondary"
                      : "outline"
                  }
                  className="text-xs h-7"
                  onClick={() => handleFeedback(finding.id, "partial")}
                >
                  Partial
                </Button>
                {feedbackState[finding.id] && (
                  <span className="text-xs text-green-600 ml-2">Saved</span>
                )}
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  );
}
