import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Play,
  Server,
  XCircle,
} from "lucide-react";
import "./styles.css";

const DEFAULT_IDS = "i-086d21b7ed6e3aaa6\ni-06ac0cdfca64c2d72";

function App() {
  const [jobId, setJobId] = useState(`gpu-check-${new Date().toISOString().slice(0, 10)}`);
  const [profile, setProfile] = useState("distributed-gpu");
  const [mode, setMode] = useState("aws");
  const [instanceText, setInstanceText] = useState(DEFAULT_IDS);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const instanceIds = useMemo(
    () =>
      instanceText
        .split(/[\s,]+/)
        .map((value) => value.trim())
        .filter(Boolean),
    [instanceText],
  );

  async function runCheck(event) {
    event.preventDefault();
    setIsRunning(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("/v1/preflight-check", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          job_id: jobId,
          profile,
          instance_ids: instanceIds,
          mode,
          apply_actions: false,
        }),
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail || "Health check failed");
      }
      setResult(body);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Health check failed");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <main className="appShell">
      <section className="controlBand">
        <div className="titleGroup">
          <div className="systemMark">
            <Activity size={22} aria-hidden="true" />
          </div>
          <div>
            <h1>EC2Check</h1>
            <p>GPU fleet health gate</p>
          </div>
        </div>

        <form className="checkForm" onSubmit={runCheck}>
          <label className="field">
            <span>Job ID</span>
            <input value={jobId} onChange={(event) => setJobId(event.target.value)} required />
          </label>

          <div className="fieldRow">
            <label className="field">
              <span>Profile</span>
              <select value={profile} onChange={(event) => setProfile(event.target.value)}>
                <option value="distributed-gpu">distributed-gpu</option>
                <option value="single-node-gpu">single-node-gpu</option>
              </select>
            </label>

            <div className="field">
              <span>Mode</span>
              <div className="segmented" role="group" aria-label="Mode">
                <button
                  type="button"
                  className={mode === "aws" ? "selected" : ""}
                  onClick={() => setMode("aws")}
                >
                  AWS
                </button>
                <button
                  type="button"
                  className={mode === "mock" ? "selected" : ""}
                  onClick={() => setMode("mock")}
                >
                  Mock
                </button>
              </div>
            </div>
          </div>

          <label className="field">
            <span>Instance IDs</span>
            <textarea
              value={instanceText}
              onChange={(event) => setInstanceText(event.target.value)}
              rows={6}
              required
            />
          </label>

          <button className="runButton" type="submit" disabled={isRunning || instanceIds.length === 0}>
            {isRunning ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Play size={18} aria-hidden="true" />}
            Run health check
          </button>
        </form>
      </section>

      <section className="resultsPane" aria-live="polite">
        {!result && !error && (
          <div className="emptyState">
            <Server size={42} aria-hidden="true" />
            <h2>{instanceIds.length} instance{instanceIds.length === 1 ? "" : "s"} queued</h2>
          </div>
        )}

        {error && (
          <div className="notice fail">
            <XCircle size={20} aria-hidden="true" />
            <span>{error}</span>
          </div>
        )}

        {result && <Results result={result} />}
      </section>
    </main>
  );
}

function Results({ result }) {
  return (
    <div className="resultsStack">
      <div className={`decisionBanner ${result.decision.toLowerCase()}`}>
        {iconForDecision(result.decision)}
        <div>
          <h2>{result.decision}</h2>
          <p>{result.summary}</p>
        </div>
      </div>

      <div className="metricGrid">
        <Metric label="Passed" value={result.aggregate_counts.passed} tone="pass" />
        <Metric label="Warned" value={result.aggregate_counts.warned} tone="warn" />
        <Metric label="Failed" value={result.aggregate_counts.failed} tone="fail" />
      </div>

      <div className="instanceGrid">
        {result.instances.map((instance) => (
          <article className="instanceCard" key={instance.instance_id}>
            <header>
              <div>
                <h3>{instance.instance_id}</h3>
                <span>{instance.check_depth}</span>
              </div>
              <StatusPill status={instance.status} />
            </header>

            <div className="checkList">
              {instance.checks.map((check) => (
                <div className="checkRow" key={`${instance.instance_id}-${check.check_name}`}>
                  <StatusDot status={check.status} />
                  <div>
                    <strong>{check.check_name}</strong>
                    <p>
                      observed <code>{check.observed}</code>
                      {check.expected ? (
                        <>
                          {" "}
                          expected <code>{check.expected}</code>
                        </>
                      ) : null}
                    </p>
                    <small>{check.evidence}</small>
                  </div>
                </div>
              ))}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function Metric({ label, value, tone }) {
  return (
    <div className={`metric ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function StatusPill({ status }) {
  return <span className={`statusPill ${status.toLowerCase()}`}>{status}</span>;
}

function StatusDot({ status }) {
  return <span className={`statusDot ${status.toLowerCase()}`} aria-hidden="true" />;
}

function iconForDecision(decision) {
  if (decision === "GO") return <CheckCircle2 size={24} aria-hidden="true" />;
  if (decision === "WARN") return <AlertTriangle size={24} aria-hidden="true" />;
  return <XCircle size={24} aria-hidden="true" />;
}

createRoot(document.getElementById("root")).render(<App />);
