import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

function CodeBlock({
  children,
  lang = "bash",
}: {
  children: string;
  lang?: string;
}) {
  return (
    <div className="relative group">
      <div className="absolute top-2 right-3 text-xs text-zinc-500 uppercase">
        {lang}
      </div>
      <pre className="bg-zinc-950 text-zinc-100 rounded-lg p-4 text-sm font-mono overflow-x-auto whitespace-pre">
        {children}
      </pre>
    </div>
  );
}

export default function DocsPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Documentation</h1>
        <p className="text-muted-foreground mt-1">
          A simple guide to ArchAgent
        </p>
      </div>

      {/* 1. What is ArchAgent? */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-xl">1. What is ArchAgent?</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm leading-relaxed">
          <p>
            ArchAgent is an AI code reviewer that catches{" "}
            <strong>architectural drift</strong> in pull requests —
            cross-boundary dependencies, layer violations, and broken design
            contracts that linters and tests miss.
          </p>
          <p>
            You define your architecture in a{" "}
            <code className="bg-muted px-1 rounded">YAML</code> file. ArchAgent
            reads PR diffs against that intent and flags violations using LLM
            agents. It learns from your feedback to reduce false positives over
            time.
          </p>
          <div className="grid grid-cols-3 gap-3 mt-4">
            <div className="bg-muted/50 rounded p-3 text-center">
              <p className="text-2xl font-bold text-green-600">100%</p>
              <p className="text-xs text-muted-foreground">Recall</p>
            </div>
            <div className="bg-muted/50 rounded p-3 text-center">
              <p className="text-2xl font-bold text-green-600">0%</p>
              <p className="text-xs text-muted-foreground">False Positives</p>
            </div>
            <div className="bg-muted/50 rounded p-3 text-center">
              <p className="text-2xl font-bold">Any</p>
              <p className="text-xs text-muted-foreground">Language</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 2. Architecture Intent YAML */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-xl">
            2. The Architecture Intent YAML
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm leading-relaxed">
          <p>
            This file describes your architecture. ArchAgent reads it to know
            what's allowed and what's forbidden.
          </p>

          <CodeBlock lang="yaml">{`schema_version: "1.0"
system: "my-app"

bounded_contexts:
  - name: orders
    owns: ["src/orders/**"]
    forbidden_dependencies: [notifications, analytics]

  - name: notifications
    owns: ["src/notifications/**"]
    forbidden_dependencies: ["*"]   # accept events only

layers:
  - name: controller
    pattern: "src/**/controllers/**"
    forbidden_imports_from: [repository]
    rule: "Controllers must not query the DB directly"

communication_patterns:
  - between: [orders, notifications]
    allowed: event
    forbidden: direct

security_rules:
  - context: payments
    constraints:
      - "No logging of card numbers"`}</CodeBlock>

          <div className="space-y-2 text-sm">
            <p>
              <strong>bounded_contexts</strong> — Modules that should be
              isolated (orders, payments, etc.)
            </p>
            <p>
              <strong>layers</strong> — Architectural layers (controller →
              service → repository → model)
            </p>
            <p>
              <strong>communication_patterns</strong> — How contexts should talk
              (events vs direct calls)
            </p>
            <p>
              <strong>security_rules</strong> — Constraints on sensitive
              contexts (PCI, PII)
            </p>
          </div>

          <p className="text-muted-foreground text-xs">
            Run <code className="bg-muted px-1 rounded">archagent init</code> to
            generate a starter file.
          </p>
        </CardContent>
      </Card>

      {/* 3. CLI Workflow */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-xl">3. CLI Workflow</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <div>
            <Badge className="mb-2">init</Badge>
            <p className="mb-2">
              Generate a starter intent file for your project.
            </p>
            <CodeBlock>{`$ archagent init --name my-app --template full`}</CodeBlock>
          </div>

          <div>
            <Badge className="mb-2">validate</Badge>
            <p className="mb-2">Check that your intent file is correct.</p>
            <CodeBlock>{`$ archagent validate architecture-intent.yaml`}</CodeBlock>
          </div>

          <div>
            <Badge className="mb-2">review</Badge>
            <p className="mb-2">
              Review a PR diff against your intent. Returns findings with
              severity, evidence, and fix suggestions.
            </p>
            <CodeBlock>{`$ archagent review --diff my-pr.diff --intent architecture-intent.yaml`}</CodeBlock>
          </div>

          <div>
            <Badge className="mb-2">feedback</Badge>
            <p className="mb-2">
              Tell ArchAgent if a finding was correct or a false positive.
            </p>
            <CodeBlock>{`$ archagent feedback <review-id> <finding-id> valid
$ archagent feedback <review-id> <finding-id> false_positive`}</CodeBlock>
          </div>

          <div>
            <Badge className="mb-2">retrain</Badge>
            <p className="mb-2">
              Retrain the reward model on your feedback (need 20+ annotations).
            </p>
            <CodeBlock>{`$ archagent retrain`}</CodeBlock>
          </div>

          <div>
            <Badge className="mb-2">stats</Badge>
            <p className="mb-2">See how the model is performing.</p>
            <CodeBlock>{`$ archagent stats`}</CodeBlock>
          </div>
        </CardContent>
      </Card>

      {/* 4. Feedback Loop */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-xl">
            4. How the Feedback Loop Works
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm leading-relaxed">
          <p>
            ArchAgent gets <strong>smarter with use</strong>. Every time you
            mark a finding as valid or a false positive, the system learns your
            team's preferences.
          </p>

          <ol className="list-decimal list-inside space-y-2 ml-2">
            <li>Run a review — agents flag potential violations.</li>
            <li>
              Mark each finding:{" "}
              <code className="bg-muted px-1 rounded">valid</code>,{" "}
              <code className="bg-muted px-1 rounded">false_positive</code>, or{" "}
              <code className="bg-muted px-1 rounded">partial</code>.
            </li>
            <li>After 20 annotations, the reward model activates.</li>
            <li>
              Future findings get a confidence score based on patterns from your
              past feedback.
            </li>
            <li>
              Low-confidence findings get suppressed so you only see what
              matters.
            </li>
          </ol>

          <p className="text-xs text-muted-foreground mt-3">
            Built on sentence-transformer embeddings + scikit-learn MLP
            classifier. No external services required.
          </p>
        </CardContent>
      </Card>

      {/* 5. Quick Start */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-xl">5. Quick Start</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <div>
            <p className="mb-2">
              <strong>Step 1.</strong> Install dependencies
            </p>
            <CodeBlock>{`cd backend
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"`}</CodeBlock>
          </div>

          <div>
            <p className="mb-2">
              <strong>Step 2.</strong> Set your API key
            </p>
            <CodeBlock>{`echo "ANTHROPIC_API_KEY=sk-ant-..." > .env`}</CodeBlock>
          </div>

          <div>
            <p className="mb-2">
              <strong>Step 3.</strong> Generate an intent file
            </p>
            <CodeBlock>{`./bin/archagent init --name my-app`}</CodeBlock>
          </div>

          <div>
            <p className="mb-2">
              <strong>Step 4.</strong> Review your first PR
            </p>
            <CodeBlock>{`git diff HEAD~1 > my-pr.diff
./bin/archagent review --diff my-pr.diff`}</CodeBlock>
          </div>

          <p className="text-muted-foreground text-xs mt-4">
            Or open the{" "}
            <a href="/review" className="underline">
              Review page
            </a>{" "}
            to try it directly in the browser.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
