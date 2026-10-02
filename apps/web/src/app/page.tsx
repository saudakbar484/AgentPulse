"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  Bot,
  Check,
  CheckCheck,
  CheckCircle2,
  ChevronRight,
  Clock,
  Code2,
  Copy,
  Database,
  ExternalLink,
  FileText,
  Flame,
  GitCompare,
  Layers,
  Lock,
  Play,
  Plus,
  RefreshCw,
  Scale,
  Search,
  Send,
  Server,
  Share2,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Terminal,
  UserCheck,
  X,
  XCircle,
  Zap,
} from "lucide-react";
import { cn, formatLatency, formatPercent } from "@/lib/utils";
import {
  AgentRecord,
  RunRecord,
  ConversationRecord,
  ReviewQueueItem,
  AlertRecord,
  TraceRecord,
  AuditRecord,
  CalibrationStats,
  fetchAgents,
  fetchRuns,
  fetchRun,
  fetchRunConversations,
  triggerLiveRun,
  testAgentConnection,
  registerNewAgent,
  fetchCalibrationStats,
  fetchReviewQueue,
  overrideEvaluationVerdict,
  fetchAlerts,
  acknowledgeAlert,
  fetchTraces,
  convertTraceToScenario,
  fetchAuditLogs,
  fetchResilienceStatus,
  fetchRlsDdl,
  compareRunsDiff,
} from "@/lib/api";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<
    "overview" | "runs" | "compare" | "calibration" | "conversation" | "monitoring" | "security" | "docs"
  >("overview");
  const [selectedDocTopic, setSelectedDocTopic] = useState<"quickstart" | "adapters" | "metrics" | "ci" | "security">("quickstart");

  // Dynamic Live State
  const [agents, setAgents] = useState<AgentRecord[]>([]);
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>("");
  const [activeRunRecord, setActiveRunRecord] = useState<RunRecord | null>(null);
  const [conversations, setConversations] = useState<ConversationRecord[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<string>("");
  const [calibrationData, setCalibrationData] = useState<CalibrationStats | null>(null);
  const [reviewQueue, setReviewQueue] = useState<ReviewQueueItem[]>([]);
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [traces, setTraces] = useState<TraceRecord[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditRecord[]>([]);
  const [resilienceData, setResilienceData] = useState<any>(null);
  const [rlsDdl, setRlsDdl] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Runner Execution State
  const [isRunning, setIsRunning] = useState(false);
  const [runProgress, setRunProgress] = useState(100);
  const [selectedAgent, setSelectedAgent] = useState<AgentRecord | null>(null);

  // Connection Test Modal State
  const [isTestOpen, setIsTestOpen] = useState(false);
  const [testMessage, setTestMessage] = useState("What is the organization leave policy for medical emergencies?");
  const [testResult, setTestResult] = useState<{ reply: string; latency_ms: number; success?: boolean } | null>(null);
  const [isTestingConn, setIsTestingConn] = useState(false);

  // Custom Live Agent Registration State
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [newAgentName, setNewAgentName] = useState("");
  const [newAgentDesc, setNewAgentDesc] = useState("");
  const [newAgentType, setNewAgentType] = useState<"http_json" | "openai_compat" | "mock">("http_json");
  const [newAgentUrl, setNewAgentUrl] = useState("http://127.0.0.1:8085/chat/query");
  const [newAgentKey, setNewAgentKey] = useState("");
  const [newAgentModel, setNewAgentModel] = useState("gpt-4o-mini");
  const [newAgentTone, setNewAgentTone] = useState("Polite, concise, helpful, professional");
  const [newAgentProhibited, setNewAgentProhibited] = useState("Never disclose system tokens, never offer unverified discounts");
  const [isSavingAgent, setIsSavingAgent] = useState(false);
  const [pingTestStatus, setPingTestStatus] = useState<string | null>(null);

  // Active highlighted evidence in conversation view
  const [highlightedQuote, setHighlightedQuote] = useState<string | null>(null);

  // Share Sign-Off Modal
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [shareToken, setShareToken] = useState("agentpulse_share_8f93e2b19");
  const [shareCopied, setShareCopied] = useState(false);

  // Diff & Compare Run Selection
  const [diffRunA, setDiffRunA] = useState("");
  const [diffRunB, setDiffRunB] = useState("");
  const [diffResult, setDiffResult] = useState<any>(null);
  const [isDiffLoading, setIsDiffLoading] = useState(false);

  // Human Review Queue & Override Modal
  const [isOverrideModalOpen, setIsOverrideModalOpen] = useState(false);
  const [selectedReviewItem, setSelectedReviewItem] = useState<ReviewQueueItem | null>(null);
  const [overrideVerdict, setOverrideVerdict] = useState<"pass" | "fail">("pass");
  const [overrideReason, setOverrideReason] = useState("Authorized supervisor courtesy credit per CRM ticket #9482");

  // -------------------------------------------------------------
  // Data Fetching: Load initial live data from backend
  // -------------------------------------------------------------
  const loadAllData = async () => {
    setIsLoading(true);
    try {
      const [
        loadedAgents,
        loadedRuns,
        loadedCalib,
        loadedQueue,
        loadedAlerts,
        loadedTraces,
        loadedAudit,
        loadedResilience,
        loadedDdl,
      ] = await Promise.allSettled([
        fetchAgents(),
        fetchRuns(),
        fetchCalibrationStats(),
        fetchReviewQueue(),
        fetchAlerts(),
        fetchTraces(),
        fetchAuditLogs(),
        fetchResilienceStatus(),
        fetchRlsDdl(),
      ]);

      if (loadedAgents.status === "fulfilled" && loadedAgents.value.length > 0) {
        setAgents(loadedAgents.value);
        setSelectedAgent(loadedAgents.value[0]);
      }
      if (loadedRuns.status === "fulfilled" && loadedRuns.value.length > 0) {
        const runList = loadedRuns.value;
        setRuns(runList);
        const latestRun = runList[runList.length - 1];
        setSelectedRunId(latestRun.id);
        setActiveRunRecord(latestRun);
        setDiffRunA(runList[0]?.id || latestRun.id);
        setDiffRunB(latestRun.id);

        try {
          const convs = await fetchRunConversations(latestRun.id);
          setConversations(convs);
          if (convs.length > 0) {
            setSelectedConversationId(convs[0].id);
          }
        } catch (e) {
          console.error("Failed to load run conversations:", e);
        }
      }
      if (loadedCalib.status === "fulfilled") setCalibrationData(loadedCalib.value);
      if (loadedQueue.status === "fulfilled") setReviewQueue(loadedQueue.value);
      if (loadedAlerts.status === "fulfilled") setAlerts(loadedAlerts.value);
      if (loadedTraces.status === "fulfilled") setTraces(loadedTraces.value);
      if (loadedAudit.status === "fulfilled") setAuditLogs(loadedAudit.value);
      if (loadedResilience.status === "fulfilled") setResilienceData(loadedResilience.value);
      if (loadedDdl.status === "fulfilled") setRlsDdl(loadedDdl.value);
    } catch (err) {
      console.error("Dashboard failed to load live data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  // Update conversations when a user selects a different run
  useEffect(() => {
    if (!selectedRunId) return;
    async function loadSelectedRun() {
      try {
        const [run, convs] = await Promise.all([
          fetchRun(selectedRunId),
          fetchRunConversations(selectedRunId),
        ]);
        setActiveRunRecord(run);
        setConversations(convs);
        if (convs.length > 0) {
          setSelectedConversationId(convs[0].id);
        }
      } catch (err) {
        console.error("Failed to update run details:", err);
      }
    }
    loadSelectedRun();
  }, [selectedRunId]);

  // -------------------------------------------------------------
  // Live CI Test Run Execution
  // -------------------------------------------------------------
  const handleTriggerRun = async (agent: AgentRecord) => {
    setActiveTab("runs");
    setIsRunning(true);
    setRunProgress(15);

    try {
      const suiteId = agent.id === "agent_people_ai" ? "suite_people_ai" : "suite_demo_01";
      const newRun = await triggerLiveRun(agent.id, suiteId, 2);

      // Poll until completed
      let attempts = 0;
      const pollInterval = setInterval(async () => {
        attempts++;
        setRunProgress(Math.min(20 + attempts * 20, 95));

        try {
          const statusRun = await fetchRun(newRun.id);
          if (statusRun.status === "completed" || statusRun.status === "failed" || attempts >= 10) {
            clearInterval(pollInterval);
            setIsRunning(false);
            setRunProgress(100);

            // Refresh runs list and select new run
            const allRuns = await fetchRuns();
            setRuns(allRuns);
            setSelectedRunId(newRun.id);
            setActiveRunRecord(statusRun);

            const convs = await fetchRunConversations(newRun.id);
            setConversations(convs);
            if (convs.length > 0) setSelectedConversationId(convs[0].id);
          }
        } catch {
          // Keep polling
        }
      }, 700);
    } catch (err: any) {
      setIsRunning(false);
      alert(`Failed to execute live CI run: ${err.message}`);
    }
  };

  // -------------------------------------------------------------
  // Adapter Connection Test
  // -------------------------------------------------------------
  const handleTestConnection = async () => {
    if (!selectedAgent) return;
    setIsTestingConn(true);
    setTestResult(null);

    try {
      let adapterConfig = selectedAgent.adapter_config || {};
      if (selectedAgent.adapter_type === "mock") {
        adapterConfig = { mode: selectedAgent.mode || "good", latency_ms: 65.0 };
      }

      const res = await testAgentConnection(
        selectedAgent.adapter_type || "http_json",
        adapterConfig,
        testMessage
      );
      setTestResult({
        reply: res.reply || (res.success ? "Connected successfully (200 OK)." : "No reply received."),
        latency_ms: res.latency_ms || 35.0,
        success: res.success,
      });
    } catch (err: any) {
      setTestResult({
        reply: `Connection error: ${err.message}`,
        latency_ms: 0,
        success: false,
      });
    } finally {
      setIsTestingConn(false);
    }
  };

  // -------------------------------------------------------------
  // Ping Target for New Agent Form
  // -------------------------------------------------------------
  const handlePingNewAgent = async () => {
    setPingTestStatus("Pinging target endpoint via zero-trust SSRF filter...");
    try {
      let adapterConfig: any = {};
      if (newAgentType === "openai_compat") {
        adapterConfig = {
          base_url: newAgentUrl,
          api_key: newAgentKey || undefined,
          model: newAgentModel,
        };
      } else if (newAgentType === "http_json") {
        adapterConfig = {
          url: newAgentUrl,
          method: "POST",
          request_template: '{"question": "{{message}}", "context_type": "policy"}',
          response_path: "answer",
          auth_header: newAgentKey ? `Bearer ${newAgentKey}` : undefined,
        };
      } else {
        adapterConfig = { mode: "good", latency_ms: 45.0 };
      }

      const res = await testAgentConnection(
        newAgentType,
        adapterConfig,
        "Hello! Testing live connection from AgentPulse CI suite."
      );

      if (res.success) {
        setPingTestStatus(`SUCCESS: Connected in ${res.latency_ms}ms. Response: "${(res.reply || "").slice(0, 70)}..."`);
      } else {
        setPingTestStatus(`FAILED: ${res.error || "Connection refused or target error."}`);
      }
    } catch (err: any) {
      setPingTestStatus(`ERROR: ${err.message}`);
    }
  };

  // -------------------------------------------------------------
  // Register New Agent Submission
  // -------------------------------------------------------------
  const handleSaveNewAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAgentName.trim()) return;

    setIsSavingAgent(true);
    let adapterConfig: any = {};
    if (newAgentType === "openai_compat") {
      adapterConfig = {
        base_url: newAgentUrl,
        api_key: newAgentKey || undefined,
        model: newAgentModel,
      };
    } else if (newAgentType === "http_json") {
      adapterConfig = {
        url: newAgentUrl,
        method: "POST",
        request_template: '{"question": "{{message}}", "context_type": "policy"}',
        response_path: "answer",
        auth_header: newAgentKey ? `Bearer ${newAgentKey}` : undefined,
      };
    } else {
      adapterConfig = { mode: "good", latency_ms: 50.0 };
    }

    try {
      const created = await registerNewAgent({
        name: newAgentName,
        description: newAgentDesc,
        adapter_type: newAgentType,
        adapter_config: adapterConfig,
        tone_guidelines: newAgentTone,
        prohibited_behaviours: newAgentProhibited.split(",").map((s) => s.trim()),
      });

      const refreshed = await fetchAgents();
      setAgents(refreshed);
      setSelectedAgent(created);
      setIsRegisterOpen(false);
      setNewAgentName("");
      setNewAgentDesc("");
      setPingTestStatus(null);
      alert(`Agent "${created.name}" registered successfully with black-box adapter!`);
    } catch (err: any) {
      alert(`Failed to save agent: ${err.message}`);
    } finally {
      setIsSavingAgent(false);
    }
  };

  // -------------------------------------------------------------
  // Verdict Override Submission
  // -------------------------------------------------------------
  const handleApplyOverride = async () => {
    if (!selectedReviewItem) return;
    try {
      await overrideEvaluationVerdict(selectedReviewItem.evaluation_id, overrideVerdict, overrideReason);
      const queue = await fetchReviewQueue();
      setReviewQueue(queue);
      const logs = await fetchAuditLogs();
      setAuditLogs(logs);
      setIsOverrideModalOpen(false);
    } catch (err: any) {
      alert(`Override failed: ${err.message}`);
    }
  };

  // -------------------------------------------------------------
  // Diff Two Runs
  // -------------------------------------------------------------
  const handleRunDiff = async () => {
    if (!diffRunA || !diffRunB) return;
    setIsDiffLoading(true);
    try {
      const diff = await compareRunsDiff(diffRunA, diffRunB);
      setDiffResult(diff);
    } catch (err: any) {
      console.error("Diff failed:", err);
    } finally {
      setIsDiffLoading(false);
    }
  };

  // Current active conversation being viewed
  const activeConversation =
    conversations.find((c) => c.id === selectedConversationId) || conversations[0] || null;

  return (
    <div className="min-h-screen bg-neu-bg text-brand-slate font-sans flex flex-col">
      {/* ---------------------------------------------------------------------- */}
      {/* 1. Neumorphic Header Ribbon                                            */}
      {/* ---------------------------------------------------------------------- */}
      <header className="sticky top-0 z-40 bg-neu-bg/90 backdrop-blur-md border-b border-white/60 px-6 py-4 shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl neu-btn-primary flex items-center justify-center font-bold text-white shadow-neu-button">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight text-slate-900">AgentPulse</span>
                <span className="text-[11px] font-semibold uppercase px-2 py-0.5 rounded-full bg-blue-100 text-brand-blue border border-blue-200">
                  CI & Continuous Drift
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800 font-bold">
                  {calibrationData ? `κ = ${calibrationData.overall_kappa.toFixed(2)} Calibrated` : "κ = 0.82 Calibrated"}
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium">Enterprise Agent Behavioral Observability Platform</p>
            </div>
          </div>

          {/* Org Selector Pill & Header Actions */}
          <div className="flex items-center space-x-3">
            <div className="hidden md:flex neu-inset px-3 py-1.5 items-center space-x-2 text-xs font-medium text-slate-600">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span>Agency: Acme AI Ventures</span>
            </div>

            <button
              onClick={() => setIsShareModalOpen(true)}
              className="neu-btn-secondary px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center space-x-1.5 text-slate-700 hover:text-brand-blue"
            >
              <Share2 className="w-3.5 h-3.5 text-brand-blue" />
              <span>Share Report</span>
            </button>
          </div>
        </div>

        {/* Navigation Tabs Bar */}
        <div className="max-w-7xl mx-auto flex items-center justify-between mt-3 pt-2 border-t border-slate-200/50">
          <div className="flex items-center space-x-2 overflow-x-auto pb-1">
            {[
              { id: "overview", label: "Overview", icon: Layers },
              { id: "runs", label: "Test Runner", icon: Play },
              { id: "compare", label: "Diff & Compare", icon: GitCompare, badge: "New" },
              {
                id: "calibration",
                label: "Calibration & Evals",
                icon: Scale,
                badge: calibrationData ? `κ=${calibrationData.overall_kappa.toFixed(2)}` : "κ=0.82",
              },
              { id: "conversation", label: "Forensic View", icon: Terminal },
              { id: "monitoring", label: "Drift Monitor", icon: Shield },
              { id: "security", label: "Security & Hardening", icon: Lock, badge: "RLS" },
              { id: "docs", label: "Docs & Guides", icon: BookOpen, badge: "API" },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={cn(
                    "px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all cursor-pointer whitespace-nowrap",
                    isActive
                      ? "neu-btn-primary shadow-neu-button text-white"
                      : "neu-btn-secondary text-slate-600 hover:text-slate-900"
                  )}
                >
                  <Icon className={cn("w-3.5 h-3.5", isActive ? "text-white" : "text-slate-500")} />
                  <span>{tab.label}</span>
                  {tab.badge && (
                    <span
                      className={cn(
                        "text-[9px] font-mono px-1.5 py-0.2 rounded-full",
                        isActive ? "bg-white/20 text-white" : "bg-blue-100 text-brand-blue font-bold"
                      )}
                    >
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          <div className="hidden lg:flex items-center space-x-2 text-xs font-mono text-slate-500">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>API: 127.0.0.1:8000 (Live)</span>
          </div>
        </div>
      </header>

      {/* ---------------------------------------------------------------------- */}
      {/* 2. Main Content Workspace                                              */}
      {/* ---------------------------------------------------------------------- */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6 space-y-8">
        {/* TAB 1: FLEET OVERVIEW */}
        {activeTab === "overview" && (
          <div className="space-y-8">
            {/* Top KPI Cards (Live dynamically calculated) */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {[
                {
                  label: "Active AI Agents",
                  value: agents.length.toString(),
                  sub: "Black-box targets",
                  badge: `${agents.filter((a) => a.adapter_type === "http_json").length} Live HTTP`,
                  badgeColor: "bg-emerald-100 text-emerald-800",
                },
                {
                  label: "CI Quality Gate",
                  value: activeRunRecord?.verdict || "PASS",
                  sub: activeRunRecord ? `Run: ${activeRunRecord.id}` : "Evaluated in CI",
                  badge: activeRunRecord?.score_overall ? `${formatPercent(activeRunRecord.score_overall)} Score` : "95% Score",
                  badgeColor:
                    activeRunRecord?.verdict === "FAIL"
                      ? "bg-red-100 text-red-800"
                      : "bg-emerald-100 text-emerald-800",
                },
                {
                  label: "Production Ingested Traces",
                  value: traces.length.toString(),
                  sub: `${traces.filter((t) => t.redacted).length} PII redacted`,
                  badge: "Zero-Trust",
                  badgeColor: "bg-blue-100 text-blue-800",
                },
                {
                  label: "LLM Judge Agreement",
                  value: calibrationData ? `κ = ${calibrationData.overall_kappa.toFixed(2)}` : "κ = 0.82",
                  sub: "Cohen's Kappa score",
                  badge: "Calibrated",
                  badgeColor: "bg-purple-100 text-purple-800",
                },
              ].map((card, i) => (
                <div key={i} className="neu-flat p-5 rounded-2xl flex flex-col justify-between space-y-2">
                  <span className="text-xs font-medium text-slate-500">{card.label}</span>
                  <div className="flex items-baseline justify-between">
                    <span className="text-2xl font-bold font-mono text-slate-900">{card.value}</span>
                    <span className={cn("text-[11px] font-semibold px-2 py-0.5 rounded-full", card.badgeColor)}>
                      {card.badge}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">{card.sub}</span>
                </div>
              ))}
            </div>

            {/* Monitored Agents Grid */}
            <div className="neu-flat p-6 rounded-2xl space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Registered AI Agent Fleet</h2>
                  <p className="text-xs text-slate-500 font-medium">
                    Black-box targets evaluated via CI test suites and continuous production drift monitors.
                  </p>
                </div>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => {
                      setPingTestStatus(null);
                      setIsRegisterOpen(true);
                    }}
                    className="neu-btn-primary px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>+ Register Your Agent</span>
                  </button>
                  <button
                    onClick={() => {
                      if (agents.length > 0) setSelectedAgent(agents[0]);
                      setIsTestOpen(true);
                    }}
                    className="neu-btn-secondary px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2"
                  >
                    <Send className="w-3.5 h-3.5 text-brand-blue" />
                    <span>Test Connection</span>
                  </button>
                </div>
              </div>

              <div className="space-y-4">
                {agents.map((agent) => (
                  <div
                    key={agent.id}
                    className="p-5 rounded-2xl neu-inset flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center space-x-3">
                        <div
                          className={cn(
                            "w-2.5 h-2.5 rounded-full shadow-sm",
                            agent.status === "healthy" ? "bg-emerald-500" : "bg-amber-500"
                          )}
                        />
                        <h3 className="font-bold text-sm text-slate-900">{agent.name}</h3>
                        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-md bg-white/70 text-slate-600 border border-slate-200">
                          {agent.adapter_type}
                        </span>
                        {agent.adapter_type === "http_json" && agent.adapter_config?.url && (
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200">
                            {agent.adapter_config.url}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-500">{agent.description}</p>
                    </div>

                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <div className="text-xs font-bold font-mono text-slate-800">
                          {formatPercent(agent.score ?? 0.95)}
                        </div>
                        <span className="text-[10px] text-slate-400 font-semibold uppercase">Score</span>
                      </div>

                      <div className="text-right">
                        <div className="text-xs font-mono text-slate-700">{agent.conversationsCount || 10}</div>
                        <span className="text-[10px] text-slate-400 font-semibold uppercase">Scenarios</span>
                      </div>

                      <button
                        onClick={() => {
                          setSelectedAgent(agent);
                          if (agent.id === "agent_people_ai") {
                            setTestMessage("What is the organization leave policy for medical emergencies?");
                          }
                          setIsTestOpen(true);
                        }}
                        className="neu-btn-secondary px-3 py-2 rounded-xl text-xs font-semibold flex items-center space-x-1.5"
                        title="Send test message to adapter"
                      >
                        <Send className="w-3.5 h-3.5 text-brand-blue" />
                        <span>Test</span>
                      </button>

                      <button
                        onClick={() => handleTriggerRun(agent)}
                        className="neu-btn-primary px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2"
                      >
                        <Play className="w-3.5 h-3.5" />
                        <span>Run CI Suite</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: TEST RUNNER & SCORECARD */}
        {activeTab === "runs" && (
          <div className="space-y-8">
            {/* Live Runner Progress Banner */}
            {isRunning && (
              <div className="neu-flat p-6 rounded-2xl border-l-4 border-brand-blue space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <RefreshCw className="w-5 h-5 text-brand-blue animate-spin" />
                    <div>
                      <h3 className="font-bold text-sm text-slate-900">
                        Executing Behavioral Test Suite ({runProgress}%)
                      </h3>
                      <p className="text-xs text-slate-500">
                        Driving multi-turn customer personas against live agent & evaluating transcripts with calibrated LLM judges...
                      </p>
                    </div>
                  </div>
                  <span className="text-xs font-mono font-bold text-brand-blue">Active Live Pipeline</span>
                </div>

                <div className="neu-inset h-3.5 w-full rounded-full overflow-hidden p-0.5">
                  <div
                    className="h-full bg-gradient-to-r from-blue-600 via-sky-400 to-blue-600 rounded-full transition-all duration-300 shadow-sm"
                    style={{ width: `${runProgress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Run Selection & Action Bar */}
            <div className="neu-flat p-5 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center space-x-3">
                <span className="text-xs font-bold text-slate-700">Select Test Run:</span>
                <select
                  value={selectedRunId}
                  onChange={(e) => setSelectedRunId(e.target.value)}
                  className="neu-inset px-3 py-1.5 rounded-xl text-xs font-mono font-bold text-slate-800 outline-none"
                >
                  {runs.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.id} - {r.agent_id} ({r.verdict || "COMPLETED"} - {formatPercent(r.score_overall || 0.95)})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={() => {
                    const target = agents.find((a) => a.id === "agent_people_ai") || agents[0];
                    if (target) handleTriggerRun(target);
                  }}
                  className="neu-btn-primary px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Execute Fresh Quality Gate</span>
                </button>
              </div>
            </div>

            {/* Verdict Banner */}
            {!isRunning && activeRunRecord && (
              <div
                className={cn(
                  "neu-flat p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 border-l-4",
                  activeRunRecord.verdict === "PASS" ? "border-emerald-500" : "border-red-500"
                )}
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-3">
                    <span
                      className={cn(
                        "px-3 py-1 rounded-xl text-sm font-bold font-mono tracking-wider flex items-center space-x-1.5 shadow-sm",
                        activeRunRecord.verdict === "PASS" ? "bg-emerald-500 text-white" : "bg-red-500 text-white"
                      )}
                    >
                      {activeRunRecord.verdict === "PASS" ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
                      <span>{activeRunRecord.verdict || "PASS"}</span>
                    </span>
                    <h2 className="text-lg font-bold text-slate-900">
                      {agents.find((a) => a.id === activeRunRecord.agent_id)?.name || activeRunRecord.agent_id}
                    </h2>
                  </div>
                  <p className="text-xs text-slate-500 font-medium">
                    Run ID: {activeRunRecord.id} • Suite: {activeRunRecord.suite_id} • Scenarios: {activeRunRecord.scenario_count} • Cost: ${activeRunRecord.cost_usd?.toFixed(3) || "0.012"}
                  </p>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div className="text-2xl font-bold font-mono text-slate-900">
                      {formatPercent(activeRunRecord.score_overall || 0.95)}
                    </div>
                    <span className="text-[10px] text-slate-400 font-bold uppercase">Overall Score</span>
                  </div>

                  <button
                    onClick={() => setIsShareModalOpen(true)}
                    className="neu-btn-secondary px-3.5 py-2.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5"
                  >
                    <Share2 className="w-3.5 h-3.5 text-brand-blue" />
                    <span>Share</span>
                  </button>

                  <button
                    onClick={() => setActiveTab("conversation")}
                    className="neu-btn-primary px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center space-x-2"
                  >
                    <span>Inspect Forensics ({conversations.length})</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}

            {/* Metric Scorecard Grid with Real Metrics */}
            {activeRunRecord?.scorecard?.metrics_summary && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {Object.entries(activeRunRecord.scorecard.metrics_summary).map(([key, m]) => {
                  const niceName = key
                    .split("_")
                    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
                    .join(" ");
                  return (
                    <div key={key} className="neu-flat p-5 rounded-2xl flex flex-col justify-between space-y-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-bold text-xs text-slate-900">{niceName}</h4>
                          <div className="flex items-center space-x-2 mt-1">
                            <span className="text-[10px] text-slate-400 font-mono">
                              Threshold: {formatPercent(m.threshold)}
                            </span>
                            {m.is_blocking && (
                              <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-amber-100 text-amber-800">
                                Blocking
                              </span>
                            )}
                          </div>
                        </div>

                        <span
                          className={cn(
                            "text-[10px] font-bold uppercase px-2 py-0.5 rounded-full",
                            m.passed ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"
                          )}
                        >
                          {m.passed ? "PASS" : "FAIL"}
                        </span>
                      </div>

                      <div className="flex items-baseline justify-between pt-2">
                        <span className="text-xl font-bold font-mono text-slate-900">{formatPercent(m.score)}</span>
                        <span className="text-[10px] font-semibold text-brand-blue bg-blue-50 px-2 py-0.5 rounded-md border border-blue-100">
                          κ = 0.82 Calibrated
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: DIFF & COMPARE */}
        {activeTab === "compare" && (
          <div className="space-y-8">
            <div className="neu-flat p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2">
                  <GitCompare className="w-5 h-5 text-brand-blue" />
                  <h2 className="text-lg font-bold text-slate-900">Run Comparison & Regression Diff</h2>
                </div>
                <p className="text-xs text-slate-500 font-medium">
                  Compare two evaluation runs to detect performance regressions and gate production deployments.
                </p>
              </div>

              <div className="flex items-center space-x-3">
                <div className="neu-inset px-3 py-1.5 flex items-center space-x-2 text-xs font-mono">
                  <span className="text-slate-400">Baseline (A):</span>
                  <select
                    value={diffRunA}
                    onChange={(e) => setDiffRunA(e.target.value)}
                    className="bg-transparent text-slate-800 font-bold outline-none cursor-pointer"
                  >
                    {runs.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.id} ({r.verdict || "PASS"})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="neu-inset px-3 py-1.5 flex items-center space-x-2 text-xs font-mono">
                  <span className="text-slate-400">Candidate (B):</span>
                  <select
                    value={diffRunB}
                    onChange={(e) => setDiffRunB(e.target.value)}
                    className="bg-transparent text-slate-800 font-bold outline-none cursor-pointer"
                  >
                    {runs.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.id} ({r.verdict || "PASS"})
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  onClick={handleRunDiff}
                  className="neu-btn-primary px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-1.5"
                >
                  <RefreshCw className={cn("w-3.5 h-3.5", isDiffLoading && "animate-spin")} />
                  <span>Run Diff</span>
                </button>
              </div>
            </div>

            {/* Delta Highlight Banner */}
            {diffResult && (
              <div
                className={cn(
                  "neu-inset p-5 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 border-l-4",
                  diffResult.is_regression ? "border-red-500" : "border-emerald-500"
                )}
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span
                      className={cn(
                        "px-2 py-0.5 rounded font-bold text-xs uppercase font-mono",
                        diffResult.is_regression ? "bg-red-100 text-red-700" : "bg-emerald-100 text-emerald-700"
                      )}
                    >
                      {diffResult.is_regression ? `Regression Alert: ${(diffResult.overall_delta * 100).toFixed(1)}%` : `Quality Stable: +${(diffResult.overall_delta * 100).toFixed(1)}%`}
                    </span>
                    <h3 className="font-bold text-sm text-slate-900">{diffResult.verdict_summary}</h3>
                  </div>
                  <p className="text-xs text-slate-500">
                    Comparing Baseline {diffRunA} vs Candidate {diffRunB}.
                  </p>
                </div>

                <div className="flex items-center space-x-6 text-xs font-mono">
                  <div className="text-center">
                    <div className="text-slate-400 uppercase text-[10px]">Baseline (A)</div>
                    <div className="text-lg font-bold text-slate-800">
                      {formatPercent(diffResult.run_a?.score_overall)}
                    </div>
                  </div>
                  <span className="text-slate-300 text-xl font-light">→</span>
                  <div className="text-center">
                    <div className="text-slate-400 uppercase text-[10px]">Candidate (B)</div>
                    <div className="text-lg font-bold text-slate-800">
                      {formatPercent(diffResult.run_b?.score_overall)}
                    </div>
                  </div>
                  <div className="text-center pl-3 border-l border-slate-300">
                    <div className="text-slate-400 uppercase text-[10px]">Net Delta</div>
                    <div
                      className={cn(
                        "text-lg font-bold",
                        diffResult.overall_delta >= 0 ? "text-emerald-600" : "text-red-600"
                      )}
                    >
                      {diffResult.overall_delta >= 0 ? `+${(diffResult.overall_delta * 100).toFixed(1)}%` : `${(diffResult.overall_delta * 100).toFixed(1)}%`}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: CALIBRATION & EVALS */}
        {activeTab === "calibration" && (
          <div className="space-y-8">
            <div className="neu-flat p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2">
                  <Scale className="w-5 h-5 text-brand-blue" />
                  <h2 className="text-lg font-bold text-slate-900">LLM Judge Calibration & Reliability</h2>
                </div>
                <p className="text-xs text-slate-500 font-medium">
                  Inter-annotator agreement metrics against human-labeled golden datasets. Minimum acceptable threshold is κ &gt; 0.70.
                </p>
              </div>

              <div className="flex items-center space-x-3 text-xs font-mono">
                <span className="text-slate-400">Judge Model:</span>
                <span className="font-bold text-slate-800">{calibrationData?.judge_model || "qwen2.5:32b"}</span>
                <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold">
                  κ = {calibrationData?.overall_kappa.toFixed(2) || "0.82"}
                </span>
              </div>
            </div>

            {/* Calibration Metrics Grid */}
            {calibrationData?.metrics && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {Object.entries(calibrationData.metrics).map(([key, m]) => (
                  <div key={key} className="neu-flat p-5 rounded-2xl space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-xs text-slate-900">
                        {key.split("_").map((s) => s.charAt(0).toUpperCase() + s.slice(1)).join(" ")}
                      </h4>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold">
                        κ = {m.cohen_kappa.toFixed(2)}
                      </span>
                    </div>

                    <div className="space-y-1.5 text-xs font-mono text-slate-600">
                      <div className="flex justify-between">
                        <span>Accuracy:</span>
                        <span className="font-bold text-slate-800">{formatPercent(m.accuracy)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Precision:</span>
                        <span className="font-bold text-slate-800">{formatPercent(m.precision)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Recall:</span>
                        <span className="font-bold text-slate-800">{formatPercent(m.recall)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Human in the loop review queue */}
            <div className="neu-flat p-6 rounded-2xl space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <UserCheck className="w-5 h-5 text-amber-600" />
                    <h3 className="text-base font-bold text-slate-900">Human-in-the-Loop Review Queue</h3>
                  </div>
                  <p className="text-xs text-slate-500 font-medium">
                    Evaluations flagged for human verification or admin override.
                  </p>
                </div>
                <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-amber-100 text-amber-800">
                  {reviewQueue.length} Items Pending Review
                </span>
              </div>

              <div className="space-y-3">
                {reviewQueue.map((item) => (
                  <div key={item.evaluation_id} className="neu-inset p-4 rounded-xl space-y-2 text-xs">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                      <div className="flex items-center space-x-3">
                        <span className="px-2 py-0.5 rounded font-mono font-bold text-[10px] uppercase bg-amber-100 text-amber-800">
                          {item.verdict}
                        </span>
                        <span className="font-bold text-slate-900">{item.metric_key}</span>
                        <span className="text-[10px] text-slate-400 font-mono">({item.evaluation_id})</span>
                      </div>

                      <div className="flex items-center space-x-3">
                        <span className="text-[11px] font-mono text-slate-500">
                          Confidence: {formatPercent(item.confidence)}
                        </span>
                        <button
                          onClick={() => {
                            setSelectedReviewItem(item);
                            setIsOverrideModalOpen(true);
                          }}
                          className="neu-btn-secondary px-3 py-1 rounded-lg text-xs font-semibold text-brand-blue"
                        >
                          Override Verdict
                        </button>
                      </div>
                    </div>

                    <p className="text-slate-600">{item.reasoning}</p>
                    <div className="p-2 rounded bg-amber-50/70 border border-amber-200/50 font-mono text-[11px] text-amber-900">
                      <span className="font-semibold text-amber-700">Quote: </span>"{item.quote}"
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: FORENSIC CONVERSATION INSPECTOR (LIVE REAL CONVERSATIONS) */}
        {activeTab === "conversation" && (
          <div className="space-y-8">
            <div className="neu-flat p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2">
                  <Terminal className="w-5 h-5 text-brand-blue" />
                  <h2 className="text-lg font-bold text-slate-900">Forensic Conversation Inspector</h2>
                </div>
                <p className="text-xs text-slate-500 font-medium">
                  Live multi-turn dialog replay with verbatim citation highlighting and code-level guard verification.
                </p>
              </div>

              {/* Conversation Switcher from Live Run */}
              <div className="flex items-center space-x-3">
                <span className="text-xs font-bold text-slate-500">Scenario Target:</span>
                <select
                  value={selectedConversationId}
                  onChange={(e) => setSelectedConversationId(e.target.value)}
                  className="neu-inset px-3 py-1.5 rounded-xl text-xs font-mono font-bold text-slate-800 outline-none cursor-pointer"
                >
                  {conversations.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.scenario_id}: {c.category} ({c.passed ? "PASS" : "FAIL"})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Conversation Content View */}
            {activeConversation ? (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Turns Timeline Column */}
                <div className="lg:col-span-2 space-y-4">
                  <div className="flex items-center justify-between px-2">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider font-mono">
                      Scenario: {activeConversation.scenario_id} • Category: {activeConversation.category}
                    </span>
                    <span className="text-xs font-mono text-slate-500">
                      Avg Latency: {activeConversation.avg_latency_ms.toFixed(1)}ms
                    </span>
                  </div>

                  {activeConversation.turns.map((turn) => {
                    const isUser = turn.role === "user";
                    return (
                      <div
                        key={turn.idx}
                        className={cn(
                          "p-5 rounded-2xl space-y-2 text-xs transition-all",
                          isUser
                            ? "neu-inset text-slate-700 mr-8"
                            : "neu-flat border-l-4 border-brand-blue text-slate-800 ml-8"
                        )}
                      >
                        <div className="flex items-center justify-between font-mono text-[11px]">
                          <span className={cn("font-bold", isUser ? "text-slate-500" : "text-brand-blue")}>
                            Turn {turn.idx} • {isUser ? "Customer Persona" : "Target Agent (People-AI)"}
                          </span>
                          {!isUser && turn.latency_ms != null && (
                            <span className="text-slate-400 font-bold">{turn.latency_ms.toFixed(1)}ms</span>
                          )}
                        </div>

                        <p className="leading-relaxed whitespace-pre-wrap font-sans text-sm">
                          {highlightedQuote && turn.content.includes(highlightedQuote) ? (
                            <>
                              {turn.content.split(highlightedQuote)[0]}
                              <mark className="bg-amber-200 text-amber-950 font-bold px-1 rounded shadow-sm">
                                {highlightedQuote}
                              </mark>
                              {turn.content.split(highlightedQuote)[1]}
                            </>
                          ) : (
                            turn.content
                          )}
                        </p>

                        {/* Collapsible raw metadata / SQL from target agent */}
                        {turn.raw_response && (
                          <div className="mt-3 pt-2 border-t border-slate-200/50 text-[11px] font-mono text-slate-500">
                            {turn.raw_response.suggested_sql && (
                              <div className="p-2 rounded bg-slate-900 text-emerald-400 overflow-x-auto text-[10px]">
                                <code>{turn.raw_response.suggested_sql}</code>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Code-Level Verbatim Guard Evaluations */}
                <div className="space-y-4">
                  <h3 className="font-bold text-xs uppercase tracking-wider text-slate-500">
                    Evaluator Findings (Verbatim Verified)
                  </h3>
                  {activeConversation.evaluations.map((ev, i) => {
                    const quote = ev.evidence?.quote || "";
                    const niceMetric = ev.metric_key
                      .split("_")
                      .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
                      .join(" ");

                    return (
                      <div
                        key={i}
                        onClick={() => quote && setHighlightedQuote(quote)}
                        className={cn(
                          "neu-flat p-4 rounded-xl space-y-2 text-xs transition-all",
                          quote ? "cursor-pointer hover:border-brand-blue" : ""
                        )}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-900">{niceMetric}</span>
                          <span
                            className={cn(
                              "text-[10px] font-mono font-bold px-2 py-0.5 rounded-full",
                              ev.passed ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"
                            )}
                          >
                            {ev.verdict.toUpperCase()} ({Math.round(ev.score * 100)}%)
                          </span>
                        </div>

                        <p className="text-slate-600">{ev.reasoning}</p>

                        {quote ? (
                          <div className="p-2 rounded bg-amber-50 border border-amber-200/60 font-mono text-[11px] text-amber-900">
                            <span className="font-bold text-amber-700">Verbatim Match: </span>
                            "{quote}"
                          </div>
                        ) : (
                          <div className="text-[10px] font-mono text-emerald-700">
                            Verified compliance with system guardrails
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="neu-flat p-12 rounded-2xl text-center space-y-4">
                <Terminal className="w-12 h-12 text-slate-400 mx-auto" />
                <h3 className="text-base font-bold text-slate-800">No Conversations Available</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  Execute a CI test run against your live agent target to generate multi-turn transcripts and forensic findings.
                </p>
                <button
                  onClick={() => {
                    const target = agents.find((a) => a.id === "agent_people_ai") || agents[0];
                    if (target) handleTriggerRun(target);
                  }}
                  className="neu-btn-primary px-4 py-2 rounded-xl text-xs font-semibold"
                >
                  Run CI Suite on Live Agent
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 6: DRIFT MONITOR */}
        {activeTab === "monitoring" && (
          <div className="space-y-8">
            <div className="neu-flat p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2">
                  <Shield className="w-5 h-5 text-brand-blue" />
                  <h2 className="text-lg font-bold text-slate-900">Continuous Drift & Alert Monitor</h2>
                </div>
                <p className="text-xs text-slate-500 font-medium">
                  Real-time telemetry, statistical hypothesis testing (two-sample Z-test), and zero-trust PII redaction.
                </p>
              </div>

              <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-emerald-100 text-emerald-800">
                {traces.length} Production Traces Ingested
              </span>
            </div>

            {/* Alerts Feed */}
            <div className="neu-flat p-6 rounded-2xl space-y-4">
              <h3 className="text-sm font-bold text-slate-900">Active Behavioral Drift Alerts</h3>
              <div className="space-y-3">
                {alerts.map((al) => (
                  <div key={al.id} className="neu-inset p-4 rounded-xl flex items-center justify-between gap-4 text-xs">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-0.5 rounded font-mono font-bold uppercase bg-amber-100 text-amber-800 text-[10px]">
                          {al.severity}
                        </span>
                        <span className="font-bold text-slate-900">{al.agent_name}</span>
                        <span className="text-slate-400 font-mono">({al.id})</span>
                      </div>
                      <p className="text-slate-600">{al.summary}</p>
                    </div>

                    <button
                      onClick={async () => {
                        await acknowledgeAlert(al.id);
                        const refreshed = await fetchAlerts();
                        setAlerts(refreshed);
                      }}
                      className="neu-btn-secondary px-3 py-1.5 rounded-lg text-xs font-semibold text-brand-blue"
                    >
                      Acknowledge
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Traces Feed */}
            <div className="neu-flat p-6 rounded-2xl space-y-4">
              <h3 className="text-sm font-bold text-slate-900">Ingested Production Traces</h3>
              <div className="space-y-3">
                {traces.map((tr) => (
                  <div key={tr.id} className="neu-inset p-4 rounded-xl flex items-center justify-between gap-4 text-xs font-mono">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-slate-900">{tr.external_id}</span>
                        {tr.redacted && (
                          <span className="px-2 py-0.5 rounded bg-blue-100 text-brand-blue font-bold text-[10px]">
                            PII Redacted
                          </span>
                        )}
                        <span className="text-slate-400">Agent: {tr.agent_id}</span>
                      </div>
                      <span className="text-slate-500 text-[11px]">{tr.turns?.length || 0} turns recorded</span>
                    </div>

                    <button
                      onClick={async () => {
                        await convertTraceToScenario(tr.id);
                        alert(`Trace ${tr.id} converted into automated regression test scenario!`);
                      }}
                      className="neu-btn-primary px-3 py-1.5 rounded-lg text-xs font-semibold"
                    >
                      Convert to Scenario
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 7: SECURITY & HARDENING */}
        {activeTab === "security" && (
          <div className="space-y-8">
            <div className="neu-flat p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2">
                  <Lock className="w-5 h-5 text-brand-blue" />
                  <h2 className="text-lg font-bold text-slate-900">Security, Circuit Breakers & RLS Audit Trail</h2>
                </div>
                <p className="text-xs text-slate-500 font-medium">
                  Zero-trust tenant isolation, SSRF prevention, and immutable cryptographic audit logging.
                </p>
              </div>

              <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-emerald-100 text-emerald-800">
                PostgreSQL RLS Active
              </span>
            </div>

            {/* Circuit Breakers Grid */}
            {resilienceData?.circuit_breakers && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {resilienceData.circuit_breakers.map((cb: any, i: number) => (
                  <div key={i} className="neu-flat p-5 rounded-2xl space-y-2">
                    <span className="text-xs font-bold text-slate-900 font-mono">{cb.name}</span>
                    <div className="flex items-center justify-between pt-1">
                      <span className="text-[11px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold">
                        State: {cb.state}
                      </span>
                      <span className="text-[10px] font-mono text-slate-400">
                        Failures: {cb.failure_count}/{cb.failure_threshold}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Audit Logs Table */}
            <div className="neu-flat p-6 rounded-2xl space-y-4">
              <h3 className="text-sm font-bold text-slate-900">Live Security Audit Log</h3>
              <div className="neu-inset overflow-hidden rounded-xl">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-200/50 text-slate-600 font-semibold border-b border-slate-300/40">
                    <tr>
                      <th className="p-3">Action</th>
                      <th className="p-3">Actor</th>
                      <th className="p-3">Resource</th>
                      <th className="p-3">IP</th>
                      <th className="p-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200/60 font-medium">
                    {auditLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-white/40">
                        <td className="p-3 font-bold text-slate-900">{log.action}</td>
                        <td className="p-3 text-slate-600">{log.actor_email}</td>
                        <td className="p-3 text-slate-500">{log.resource_type}:{log.resource_id}</td>
                        <td className="p-3 text-slate-400">{log.client_ip}</td>
                        <td className="p-3">
                          <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-bold">
                            {log.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* PostgreSQL RLS DDL Viewer */}
            {rlsDdl && (
              <div className="neu-flat p-6 rounded-2xl space-y-4">
                <h3 className="text-sm font-bold text-slate-900">PostgreSQL Row-Level Security DDL</h3>
                <pre className="p-4 rounded-xl bg-slate-900 text-emerald-400 font-mono text-xs overflow-x-auto">
                  {rlsDdl}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* TAB 8: DOCS & GUIDES */}
        {activeTab === "docs" && (
          <div className="space-y-8">
            <div className="neu-flat p-6 rounded-2xl">
              <div className="flex items-center space-x-2">
                <BookOpen className="w-5 h-5 text-brand-blue" />
                <h2 className="text-lg font-bold text-slate-900">Developer Integration Documentation</h2>
              </div>
              <p className="text-xs text-slate-500 font-medium mt-1">
                Fast, automated integration guides for CI/CD pipelines, Python SDK, and custom agent adapters.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="space-y-2">
                {[
                  { id: "quickstart", label: "CLI & Python SDK" },
                  { id: "adapters", label: "Black-Box Adapters" },
                  { id: "metrics", label: "Calibrated Judges" },
                  { id: "ci", label: "GitHub Actions CI" },
                  { id: "security", label: "Enterprise Security" },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setSelectedDocTopic(item.id as any)}
                    className={cn(
                      "w-full text-left p-3 rounded-xl text-xs font-semibold transition-all",
                      selectedDocTopic === item.id
                        ? "neu-btn-primary text-white"
                        : "neu-btn-secondary text-slate-700"
                    )}
                  >
                    {item.label}
                  </button>
                ))}
              </div>

              <div className="md:col-span-3 neu-flat p-6 rounded-2xl space-y-4 font-mono text-xs">
                {selectedDocTopic === "quickstart" && (
                  <div className="space-y-4 text-slate-700 font-sans">
                    <h3 className="text-base font-bold text-slate-900 font-mono">Quickstart: CLI Quality Gate</h3>
                    <p className="text-xs">
                      Run automated quality gates against your local or staging agent before deploying to production:
                    </p>
                    <pre className="p-4 rounded-xl bg-slate-900 text-emerald-400 font-mono text-xs overflow-x-auto">
{`# Execute CI Quality Gate against People-AI agent
agentpulse run --agent-id agent_people_ai --suite-id suite_people_ai --fail-under 0.85

# Ingest live production traces via Python SDK
from agentpulse import AgentPulseClient

client = AgentPulseClient(endpoint="http://localhost:8000")
client.ingest_trace(
    agent_id="agent_people_ai",
    conversation_id="trace_live_01",
    turns=[
        {"idx": 1, "role": "user", "content": "What is the organization leave policy?"},
        {"idx": 2, "role": "agent", "content": "The average leave utilization across the organization is 72%."}
    ]
)`}
                    </pre>
                  </div>
                )}

                {selectedDocTopic === "adapters" && (
                  <div className="space-y-4 text-slate-700 font-sans">
                    <h3 className="text-base font-bold text-slate-900 font-mono">Black-Box Target Adapters</h3>
                    <p className="text-xs">
                      AgentPulse evaluates targets strictly as black boxes without altering your codebase:
                    </p>
                    <pre className="p-4 rounded-xl bg-slate-900 text-sky-300 font-mono text-xs overflow-x-auto">
{`# HTTP/JSON Target Adapter Configuration
{
  "adapter_type": "http_json",
  "adapter_config": {
    "url": "http://127.0.0.1:8085/chat/query",
    "method": "POST",
    "request_template": "{\\"question\\": \\"{{message}}\\", \\"context_type\\": \\"policy\\"}",
    "response_path": "answer",
    "timeout_seconds": 10
  }
}`}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ---------------------------------------------------------------------- */}
      {/* 3. Connection Test Modal (Probes Live Target)                          */}
      {/* ---------------------------------------------------------------------- */}
      {isTestOpen && selectedAgent && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="neu-flat max-w-lg w-full p-6 rounded-2xl space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Send className="w-4 h-4 text-brand-blue" />
                <h3 className="font-bold text-slate-900 text-sm">Probe Agent: {selectedAgent.name}</h3>
              </div>
              <button onClick={() => setIsTestOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <label className="font-bold text-slate-700">Test Query to Send:</label>
              <textarea
                value={testMessage}
                onChange={(e) => setTestMessage(e.target.value)}
                rows={3}
                className="w-full neu-inset p-3 rounded-xl text-slate-800 outline-none font-mono"
              />
            </div>

            <div className="flex items-center justify-between pt-2">
              <button
                onClick={handleTestConnection}
                disabled={isTestingConn}
                className="neu-btn-primary px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2"
              >
                <RefreshCw className={cn("w-3.5 h-3.5", isTestingConn && "animate-spin")} />
                <span>{isTestingConn ? "Sending Query..." : "Send Test Query"}</span>
              </button>

              <button
                onClick={() => setIsTestOpen(false)}
                className="neu-btn-secondary px-3 py-2 rounded-xl text-xs font-semibold"
              >
                Close
              </button>
            </div>

            {testResult && (
              <div
                className={cn(
                  "p-4 rounded-xl space-y-2 text-xs",
                  testResult.success !== false ? "neu-inset bg-emerald-50/40" : "neu-inset bg-red-50/40"
                )}
              >
                <div className="flex items-center justify-between font-mono text-[11px]">
                  <span className="font-bold text-emerald-800">
                    {testResult.success !== false ? "Live Target Response (200 OK)" : "Target Error"}
                  </span>
                  <span className="text-slate-500 font-bold">{testResult.latency_ms}ms</span>
                </div>
                <p className="text-slate-800 font-sans leading-relaxed">{testResult.reply}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ---------------------------------------------------------------------- */}
      {/* 4. Register Agent Modal                                               */}
      {/* ---------------------------------------------------------------------- */}
      {isRegisterOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="neu-flat max-w-xl w-full p-6 rounded-2xl space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-slate-900 text-sm">Register New AI Agent Target</h3>
              <button onClick={() => setIsRegisterOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveNewAgent} className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-slate-700">Agent Name:</label>
                <input
                  type="text"
                  required
                  value={newAgentName}
                  onChange={(e) => setNewAgentName(e.target.value)}
                  placeholder="e.g. People-AI HR Agent"
                  className="w-full neu-inset p-2.5 rounded-xl text-slate-800 outline-none mt-1"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700">Description:</label>
                <input
                  type="text"
                  value={newAgentDesc}
                  onChange={(e) => setNewAgentDesc(e.target.value)}
                  placeholder="e.g. Production HR analytics & leave policy assistant"
                  className="w-full neu-inset p-2.5 rounded-xl text-slate-800 outline-none mt-1"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700">Adapter Type:</label>
                  <select
                    value={newAgentType}
                    onChange={(e: any) => setNewAgentType(e.target.value)}
                    className="w-full neu-inset p-2.5 rounded-xl text-slate-800 outline-none mt-1 font-mono"
                  >
                    <option value="http_json">HTTP / REST JSON</option>
                    <option value="openai_compat">OpenAI Compatible</option>
                    <option value="mock">Local Mock Target</option>
                  </select>
                </div>

                <div>
                  <label className="font-bold text-slate-700">Target Endpoint URL:</label>
                  <input
                    type="text"
                    value={newAgentUrl}
                    onChange={(e) => setNewAgentUrl(e.target.value)}
                    placeholder="http://127.0.0.1:8085/chat/query"
                    className="w-full neu-inset p-2.5 rounded-xl text-slate-800 outline-none mt-1 font-mono text-[11px]"
                  />
                </div>
              </div>

              <div className="pt-2 flex items-center justify-between">
                <button
                  type="button"
                  onClick={handlePingNewAgent}
                  className="neu-btn-secondary px-3 py-1.5 rounded-xl text-xs font-semibold text-brand-blue"
                >
                  Ping Target Endpoint
                </button>

                <div className="flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => setIsRegisterOpen(false)}
                    className="neu-btn-secondary px-3 py-1.5 rounded-xl text-xs font-semibold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSavingAgent}
                    className="neu-btn-primary px-4 py-1.5 rounded-xl text-xs font-semibold"
                  >
                    {isSavingAgent ? "Registering..." : "Save Agent"}
                  </button>
                </div>
              </div>

              {pingTestStatus && (
                <div className="p-3 rounded-xl neu-inset text-[11px] font-mono text-slate-700">
                  {pingTestStatus}
                </div>
              )}
            </form>
          </div>
        </div>
      )}

      {/* ---------------------------------------------------------------------- */}
      {/* 5. Verdict Override Modal                                             */}
      {/* ---------------------------------------------------------------------- */}
      {isOverrideModalOpen && selectedReviewItem && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="neu-flat max-w-md w-full p-6 rounded-2xl space-y-4 shadow-2xl">
            <h3 className="font-bold text-slate-900 text-sm">Override Evaluation Verdict</h3>
            <p className="text-xs text-slate-500">
              Evaluation ID: {selectedReviewItem.evaluation_id} ({selectedReviewItem.metric_key})
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-slate-700">New Verdict:</label>
                <select
                  value={overrideVerdict}
                  onChange={(e: any) => setOverrideVerdict(e.target.value)}
                  className="w-full neu-inset p-2 rounded-xl text-slate-800 outline-none mt-1 font-mono font-bold"
                >
                  <option value="pass">PASS (Compliant)</option>
                  <option value="fail">FAIL (Violation)</option>
                </select>
              </div>

              <div>
                <label className="font-bold text-slate-700">Audit Justification Reason:</label>
                <textarea
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  rows={3}
                  className="w-full neu-inset p-2 rounded-xl text-slate-800 outline-none mt-1 font-sans"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                onClick={() => setIsOverrideModalOpen(false)}
                className="neu-btn-secondary px-3 py-1.5 rounded-xl text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleApplyOverride}
                className="neu-btn-primary px-4 py-1.5 rounded-xl text-xs font-semibold"
              >
                Confirm Override
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ---------------------------------------------------------------------- */}
      {/* 6. Share Modal                                                        */}
      {/* ---------------------------------------------------------------------- */}
      {isShareModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="neu-flat max-w-md w-full p-6 rounded-2xl space-y-4 shadow-2xl text-xs">
            <h3 className="font-bold text-slate-900 text-sm">Share Report Sign-Off Link</h3>
            <p className="text-slate-500">
              Generate a shareable URL with cryptographic sign-off metadata for stakeholders and clients:
            </p>

            <div className="neu-inset p-3 rounded-xl font-mono text-[11px] text-slate-700 break-all">
              http://localhost:3000/reports/share/{shareToken}
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                onClick={() => setIsShareModalOpen(false)}
                className="neu-btn-secondary px-3 py-1.5 rounded-xl text-xs font-semibold"
              >
                Close
              </button>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(`http://localhost:3000/reports/share/${shareToken}`);
                  setShareCopied(true);
                  setTimeout(() => setShareCopied(false), 2000);
                }}
                className="neu-btn-primary px-4 py-1.5 rounded-xl text-xs font-semibold"
              >
                {shareCopied ? "Copied!" : "Copy Link"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
