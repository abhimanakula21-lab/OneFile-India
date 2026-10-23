
import { useCallback, useEffect, useState } from "react";
import "./App.css";

const API = "https://onefile-india-api.onrender.com/";

function Metric({ label, value, note, tone = "blue" }) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <p className="metric-label">{label}</p>
      <h2>{value ?? "—"}</h2>
      <p className="metric-note">{note}</p>
    </article>
  );
}

function BureauWorkloadChart({ data = {} }) {
  const entries = Object.entries(data).sort(
    ([, a], [, b]) => Number(b) - Number(a)
  );
  const total = entries.reduce((sum, [, n]) => sum + (Number(n) || 0), 0);
  const max = Math.max(1, ...entries.map(([, n]) => Number(n) || 0));

  return (
    <section className="panel chart-panel">
      <div className="section-heading">
        <div>
          <h2>Bureau Workload</h2>
          <p>Distribution of recorded cases across bureaus</p>
        </div>
        <span className="count-badge">{total} cases</span>
      </div>
      {entries.length ? (
        <div className="workload-chart">
          {entries.map(([name, count]) => (
            <div className="workload-row" key={name}>
              <div className="workload-label">
                <span>{name}</span><strong>{Number(count) || 0}</strong>
              </div>
              <div
                className="workload-track"
                role="img"
                aria-label={`${name}: ${count} cases`}
              >
                <div
                  className="workload-bar"
                  style={{ width: `${((Number(count) || 0) / max) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      ) : <p className="empty-state">No bureau workload data available.</p>}
      <p className="chart-footnote">
        Case counts indicate recorded volume, not staff performance.
      </p>
    </section>
  );
}

function CaseStatusChart({ data = {} }) {
  const entries = Object.entries(data).sort(([a], [b]) => a.localeCompare(b));
  const total = entries.reduce((sum, [, n]) => sum + (Number(n) || 0), 0);
  const max = Math.max(1, ...entries.map(([, n]) => Number(n) || 0));

  return (
    <section className="panel chart-panel">
      <div className="section-heading">
        <div>
          <h2>Case Status Breakdown</h2>
          <p>Current distribution by recorded status</p>
        </div>
        <span className="count-badge">{total} cases</span>
      </div>
      {entries.length ? (
        <div className="workload-chart">
          {entries.map(([status, count]) => (
            <div className="workload-row" key={status}>
              <div className="workload-label">
                <span>{status.replaceAll("_", " ")}</span>
                <strong>{Number(count) || 0}</strong>
              </div>
              <div className="workload-track" role="img"
                aria-label={`${status}: ${count} cases`}>
                <div className="status-chart-bar"
                  style={{ width: `${((Number(count) || 0) / max) * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      ) : <p className="empty-state">No case-status data available.</p>}
      <p className="chart-footnote">
        Status totals may include closed as well as open cases.
      </p>
    </section>
  );
}

function getCaseId1(item) {
  return item.case_id_1 ?? item.case_a ?? "";
}

function getCaseId2(item) {
  return item.case_id_2 ?? item.case_b ?? "";
}

function getPairKey(item) {
  return [getCaseId1(item), getCaseId2(item)].sort().join("::");
}

function isReviewed(item) {
  return ["confirmed_duplicate", "not_duplicate"].includes(item.review_status);
}

function StatusBadge({ value }) {
  const status = String(value || "unknown").toLowerCase().replaceAll("_", " ");
  let tone = "neutral";
  if (/closed|resolved|completed|approved/.test(status)) tone = "success";
  else if (/overdue|rejected|critical/.test(status)) tone = "danger";
  else if (/pending|review|open|progress/.test(status)) tone = "warning";

  return <span className={`status-badge status-${tone}`}>{status}</span>;
}

export default function App() {
  const [dashboard, setDashboard] = useState(null);
  const [cases, setCases] = useState([]);
  const [institutions, setInstitutions] = useState([]);
  const [selectedInstitution, setSelectedInstitution] = useState("");
  const [institutionHistory, setInstitutionHistory] = useState(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [duplicateInstitution, setDuplicateInstitution] = useState("DEMO-001");
  const [duplicateResults, setDuplicateResults] = useState([]);
  const [duplicateMessage, setDuplicateMessage] = useState("");
  const [reviewingPair, setReviewingPair] = useState("");
  const [reviewMessage, setReviewMessage] = useState("");
  const [checkingDuplicates, setCheckingDuplicates] = useState(false);

  const [selectedCase, setSelectedCase] = useState("RB-2002");
  const [riskAlerts, setRiskAlerts] = useState([]);
  const [riskMessage, setRiskMessage] = useState("");
  const [checkingAlerts, setCheckingAlerts] = useState(false);

  const [auditCaseId, setAuditCaseId] = useState("PGRC-1001");
  const [auditHistory, setAuditHistory] = useState([]);
  const [auditMessage, setAuditMessage] = useState("");
  const [loadingAudit, setLoadingAudit] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const responses = await Promise.all([
        fetch(`${API}/api/dashboard`),
        fetch(`${API}/api/cases`),
        fetch(`${API}/api/institutions`),
      ]);
      if (responses.some((response) => !response.ok)) {
        throw new Error("The backend returned an error.");
      }
      const [d, c, i] = await Promise.all(responses.map((r) => r.json()));
      const caseList = c.results ?? [];
      const institutionList = i.results ?? [];

      setDashboard(d);
      setCases(caseList);
      setInstitutions(institutionList);
      setSelectedCase((old) =>
        caseList.some((item) => item.case_id === old)
          ? old : caseList[0]?.case_id ?? ""
      );
      setAuditCaseId((old) =>
        caseList.some((item) => item.case_id === old)
          ? old : caseList[0]?.case_id ?? ""
      );
      setDuplicateInstitution((old) =>
        institutionList.some((item) => item.institution_id === old)
          ? old : institutionList[0]?.institution_id ?? ""
      );
    } catch {
      setError(`Cannot connect to ${API}. Make sure FastAPI is running.`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function viewInstitution(id) {
    setSelectedInstitution(id);
    setInstitutionHistory(null);
    setError("");
    if (!id) return;
    try {
      const response = await fetch(
        `${API}/api/institutions/${encodeURIComponent(id)}`
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Institution lookup failed.");
      setInstitutionHistory(data);
    } catch (err) {
      setError(err.message || "Could not load institution history.");
    }
  }

  const filteredCases = cases.filter((item) => {
    const term = search.trim().toLowerCase();
    const matchesSearch = !term || [
      item.case_id, item.institution_id, item.bureau,
      item.category, item.description, item.status,
    ].some((v) => String(v ?? "").toLowerCase().includes(term));
    return matchesSearch &&
      (!selectedInstitution || item.institution_id === selectedInstitution);
  });

  async function checkDuplicates() {
    if (!duplicateInstitution) {
      setDuplicateMessage("Select an institution first.");
      return;
    }
    setCheckingDuplicates(true);
    setDuplicateMessage("");
    setDuplicateResults([]);
    setReviewMessage("");
    try {
      const response = await fetch(
        `${API}/api/duplicates?institution_id=${encodeURIComponent(
          duplicateInstitution
        )}&threshold=0.2`
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Duplicate detection failed.");

      const results = (data.results ?? []).map((item) => ({
        ...item,
        case_id_1: getCaseId1(item),
        case_id_2: getCaseId2(item),
        description_1: item.description_1 ?? item.description_a ?? "",
        description_2: item.description_2 ?? item.description_b ?? "",
        review_status: item.review_status || "pending_review",
      }));
      setDuplicateResults(results);
      setDuplicateMessage(results.length
        ? `${results.length} potential match(es) found. Human review is required.`
        : "No potential duplicates found at this threshold.");
    } catch (err) {
      setDuplicateMessage(err.message || "Could not check duplicates.");
    } finally {
      setCheckingDuplicates(false);
    }
  }

  async function submitDuplicateReview(item, decision) {
    const caseId1 = getCaseId1(item);
    const caseId2 = getCaseId2(item);
    if (!caseId1 || !caseId2) {
      setReviewMessage("Review failed: case IDs are missing.");
      return;
    }
    const pairKey = getPairKey(item);
    setReviewingPair(pairKey);
    setReviewMessage("");
    try {
      const response = await fetch(`${API}/api/duplicates/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_id_1: caseId1,
          case_id_2: caseId2,
          decision,
          actor_role: "Demo Reviewer",
          similarity_score: item.similarity_score,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(typeof data.detail === "string"
          ? data.detail : JSON.stringify(data.detail || "Could not save review."));
      }
      setDuplicateResults((previous) => previous.map((candidate) =>
        getPairKey(candidate) !== pairKey ? candidate : {
          ...candidate,
          review_status: data.review_status,
          relationship_type: data.relationship_type,
        }
      ));
      setReviewMessage(`${caseId1} and ${caseId2}: ${
        data.message || "Review saved successfully."
      }`);
      try {
        const response = await fetch(`${API}/api/dashboard`);
        if (response.ok) setDashboard(await response.json());
      } catch { /* The saved review remains successful. */ }
    } catch (err) {
      setReviewMessage(`Review failed: ${err.message}`);
    } finally {
      setReviewingPair("");
    }
  }

  async function checkRiskAlerts() {
    if (!selectedCase) {
      setRiskMessage("Select a case first.");
      return;
    }
    setCheckingAlerts(true);
    setRiskMessage("");
    setRiskAlerts([]);
    try {
      const response = await fetch(
        `${API}/api/cases/${encodeURIComponent(selectedCase)}/risk-alerts`
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not load risk alerts.");
      setRiskAlerts(data.alerts ?? []);
      setRiskMessage(data.alerts?.length
        ? `${data.alerts.length} cross-bureau advisory alert(s) found.`
        : data.message || "No cross-bureau alerts found for this case.");
    } catch (err) {
      setRiskMessage(err.message || "Could not load risk alerts.");
    } finally {
      setCheckingAlerts(false);
    }
  }

  async function loadAuditHistory() {
    if (!auditCaseId) {
      setAuditMessage("Select a case first.");
      return;
    }
    setLoadingAudit(true);
    setAuditMessage("");
    setAuditHistory([]);
    try {
      const response = await fetch(
        `${API}/api/cases/${encodeURIComponent(auditCaseId)}/audit`
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not load audit history.");
      setAuditHistory(data.results ?? []);
      setAuditMessage(data.results?.length
        ? `${data.results.length} recorded action(s) found.`
        : "No audit actions have been recorded for this case.");
    } catch (err) {
      setAuditMessage(err.message || "Could not load audit history.");
    } finally {
      setLoadingAudit(false);
    }
  }

  return (
    <div className="site">
      <div className="government-strip">
        <div className="container government-inner">
          <span>Case Coordination Prototype</span>
          <span>Technical prototype · Demonstration data</span>
        </div>
      </div>

      <header className="masthead">
        <div className="container masthead-inner">
          <a className="brand" href="#overview" aria-label="CaseLink home">
            <div className="brand-emblem" aria-hidden="true">
              <span>OF</span>
            </div>
            <div>
              <span className="brand-kicker">ONE INSTITUTION · ONE VIEW</span>
              <strong>OneFile India</strong>
              <small>Unified Case Monitoring & Coordination</small>
            </div>
          </a>
          <div className="masthead-actions">
            <span className="prototype-badge"><span /> Prototype mode</span>
            <button className="refresh-button" onClick={loadData} disabled={loading}>
              <span aria-hidden="true">↻</span> {loading ? "Refreshing…" : "Refresh data"}
            </button>
          </div>
        </div>
      </header>

      <nav className="main-nav" aria-label="Main navigation">
        <div className="container nav-inner">
          <a className="nav-link active" href="#overview">Overview</a>
          <a className="nav-link" href="#institutions">Institutions</a>
          <a className="nav-link" href="#case-register">Case Register</a>
          <a className="nav-link" href="#duplicate-review">Duplicate Review</a>
          <a className="nav-link" href="#advisory-alerts">Advisory Alerts</a>
          <a className="nav-link" href="#audit-history">Audit History</a>
        </div>
      </nav>

      <main className="container main-content">
        {error && <div className="error-banner" role="alert">
          <strong>Connection notice</strong><span>{error}</span>
        </div>}

        <section className="page-intro" id="overview">
          <div>
            <p className="breadcrumb">Home <span>/</span> Dashboard</p>
            <h1>Case Monitoring Dashboard</h1>
            <p className="intro-copy">
              A consolidated view of institutional complaints, bureau workloads,
              service timelines and cross-bureau coordination.
            </p>
          </div>
          <div className="updated-note">
            <span className={`connection-dot ${error ? "offline" : ""}`} />
            {loading ? "Loading data…" : error ? "API unavailable" : "Dashboard connected"}
          </div>
        </section>

        <section className="metrics-grid" aria-label="Case overview metrics">
          <Metric label="Total cases" value={dashboard?.total_cases}
            note="All recorded complaints" tone="blue" />
          <Metric label="Open cases" value={dashboard?.open_cases}
            note="Across all bureaus" tone="amber" />
          <Metric label="Overdue cases" value={dashboard?.overdue_cases}
            note="Past the recorded due date" tone="red" />
          <Metric label="Potential duplicates" value={dashboard?.potential_duplicates}
            note="Requiring review" tone="violet" />
          <Metric label="Institutions" value={dashboard?.institutions}
            note="In the demonstration database" tone="teal" />
          <Metric label="Pending transfers" value={dashboard?.pending_transfers}
            note="Awaiting acknowledgement" tone="slate" />
        </section>

        <div className="charts-grid">
          <BureauWorkloadChart data={dashboard?.cases_by_bureau ?? {}} />
          <CaseStatusChart data={dashboard?.cases_by_status ?? {}} />
        </div>

        <section className="panel" id="institutions">
          <div className="section-heading">
            <div>
              <span className="section-kicker">INSTITUTION RECORDS</span>
              <h2>Institution Explorer</h2>
              <p>Inspect an institution's consolidated case history.</p>
            </div>
          </div>
          <label className="field-label" htmlFor="institution-select">Select institution</label>
          <select id="institution-select" value={selectedInstitution}
            onChange={(e) => viewInstitution(e.target.value)}>
            <option value="">All institutions</option>
            {institutions.map((item) => (
              <option key={item.institution_id} value={item.institution_id}>
                {item.name} ({item.institution_id})
              </option>
            ))}
          </select>
          {institutionHistory && (
            <div className="institution-summary">
              <div className="institution-heading">
                <div>
                  <span className="section-kicker">INSTITUTION PROFILE</span>
                  <h3>{institutionHistory.institution.name}</h3>
                  <p>
                    Institution ID: <strong>{institutionHistory.institution.institution_id}</strong>
                    {" · "}Region: <strong>{institutionHistory.institution.region || "—"}</strong>
                  </p>
                </div>
                <span className="profile-icon" aria-hidden="true">IN</span>
              </div>
              <div className="history-stats">
                <div><span>Total cases</span><strong>{institutionHistory.total_cases ?? 0}</strong></div>
                <div><span>Open cases</span><strong>{institutionHistory.open_cases ?? 0}</strong></div>
                <div><span>Overdue cases</span><strong>{institutionHistory.overdue_cases ?? 0}</strong></div>
              </div>
            </div>
          )}
        </section>

        <section className="panel" id="case-register">
          <div className="section-heading">
            <div>
              <span className="section-kicker">CASE MANAGEMENT</span>
              <h2>Case Register</h2>
              <p>Search cases by ID, institution, bureau, category or status.</p>
            </div>
            <span className="count-badge">{filteredCases.length} records</span>
          </div>
          <div className="search-wrap">
            <span aria-hidden="true">⌕</span>
            <input className="search-input" value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search case ID, institution, bureau…" aria-label="Search cases" />
            {search && <button className="clear-search" onClick={() => setSearch("")}>Clear</button>}
          </div>
          {loading ? <p className="empty-state">Loading case records…</p>
            : filteredCases.length === 0 ? <p className="empty-state">No matching cases found.</p>
            : <div className="table-wrapper">
              <table>
                <thead><tr>
                  <th>Case ID</th><th>Institution ID</th><th>Bureau</th>
                  <th>Category</th><th>Status</th><th>Due date</th><th>SLA</th>
                </tr></thead>
                <tbody>
                  {filteredCases.map((item) => (
                    <tr key={item.case_id}>
                      <td className="case-id">{item.case_id}</td>
                      <td>{item.institution_id || "—"}</td>
                      <td>{item.bureau || "—"}</td>
                      <td>{item.category || "—"}</td>
                      <td><StatusBadge value={item.status} /></td>
                      <td>{item.due_at ?? "—"}</td>
                      <td>{item.is_overdue
                        ? <span className="sla-overdue">Overdue</span>
                        : <span className="sla-ok">Within SLA</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>}
        </section>

        <section className="panel" id="duplicate-review">
          <div className="section-heading">
            <div>
              <span className="section-kicker">INTELLIGENCE & QUALITY</span>
              <h2>Duplicate Complaint Review</h2>
              <p>Find similar complaints and record a human review decision.</p>
            </div>
          </div>
          <div className="intelligence-controls">
            <div className="control-field">
              <label className="field-label" htmlFor="duplicate-institution">Institution</label>
              <select id="duplicate-institution" value={duplicateInstitution}
                onChange={(e) => {
                  setDuplicateInstitution(e.target.value);
                  setDuplicateResults([]);
                  setDuplicateMessage("");
                  setReviewMessage("");
                }}>
                {institutions.map((item) => (
                  <option key={item.institution_id} value={item.institution_id}>
                    {item.name} ({item.institution_id})
                  </option>
                ))}
              </select>
            </div>
            <button onClick={checkDuplicates}
              disabled={checkingDuplicates || !duplicateInstitution}>
              {checkingDuplicates ? "Checking…" : "Find similar complaints"}
            </button>
          </div>
          {duplicateMessage && <p className="feedback-message" role="status">{duplicateMessage}</p>}
          {duplicateResults.map((item, index) => {
            const id1 = getCaseId1(item);
            const id2 = getCaseId2(item);
            const key = getPairKey(item);
            const saving = reviewingPair === key;
            const reviewed = isReviewed(item);
            return (
              <article className="intelligence-card" key={`${key}-${index}`}>
                <div className="intelligence-card-header">
                  <div><span className="section-kicker">POTENTIAL MATCH</span>
                    <h3>{id1} <span className="pair-arrow">↔</span> {id2}</h3></div>
                  <span className="similarity-score">
                    {(Number(item.similarity_score ?? 0) * 100).toFixed(1)}% similarity
                  </span>
                </div>
                <div className="comparison-grid">
                  <div><span className="comparison-label">{id1}</span>
                    <p>{item.description_1 || "No description available."}</p></div>
                  <div><span className="comparison-label">{id2}</span>
                    <p>{item.description_2 || "No description available."}</p></div>
                </div>
                <div className="review-actions">
                  <span className="review-status">Review status: <StatusBadge value={item.review_status} /></span>
                  <button disabled={saving || reviewed}
                    onClick={() => submitDuplicateReview(item, "confirm_duplicate")}disabled={reviewingPair === getPairKey(item)}>
                    {saving ? "Saving…" : "Confirm duplicate"}
                  </button>
                  <button className="button-secondary" disabled={saving || reviewed}
                    onClick={() => submitDuplicateReview(item, "not_duplicate")}disabled={reviewingPair === getPairKey(item)}>
                    Not a duplicate
                  </button>
                </div>
                {reviewed && <p className="review-note">
                  A review decision has been recorded for this pair. Run the duplicate check again to reload results.
                </p>}
                <p className="review-note">
                  Text similarity is an indicator, not proof. A reviewer must assess the complaints before deciding.
                </p>
              </article>
            );
          })}
          {reviewMessage && <p className="feedback-message" role="status">{reviewMessage}</p>}
        </section>

        <section className="panel" id="advisory-alerts">
          <div className="section-heading">
            <div>
              <span className="section-kicker">CROSS-BUREAU COORDINATION</span>
              <h2>Cross-Bureau Advisory Alerts</h2>
              <p>Identify related open cases associated with the selected case.</p>
            </div>
          </div>
          <div className="intelligence-controls">
            <div className="control-field">
              <label className="field-label" htmlFor="risk-case">Select case</label>
              <select id="risk-case" value={selectedCase}
                onChange={(e) => {
                  setSelectedCase(e.target.value);
                  setRiskAlerts([]);
                  setRiskMessage("");
                }}>
                {cases.map((item) => <option key={item.case_id} value={item.case_id}>
                  {item.case_id} — {item.category} ({item.bureau})
                </option>)}
              </select>
            </div>
            <button onClick={checkRiskAlerts} disabled={checkingAlerts || !cases.length}>
              {checkingAlerts ? "Checking…" : "Check related cases"}
            </button>
          </div>
          {riskMessage && <p className="feedback-message" role="status">{riskMessage}</p>}
          {riskAlerts.map((alert) => (
            <article className="intelligence-card alert-card" key={alert.related_case_id}>
              <div className="intelligence-card-header">
                <h3>{alert.related_case_id}</h3><span className="advisory-badge">Advisory</span>
              </div>
              <div className="alert-details">
                <p><strong>Bureau</strong>{alert.bureau || "—"}</p>
                <p><strong>Category</strong>{alert.category || "—"}</p>
                <p><strong>Status</strong><StatusBadge value={alert.status} /></p>
              </div>
              <p>{alert.message}</p>
            </article>
          ))}
          <p className="review-note">
            Alerts support coordination only. They do not automatically block or determine approval or renewal decisions.
          </p>
        </section>

        <section className="panel" id="audit-history">
          <div className="section-heading">
            <div>
              <span className="section-kicker">ACCOUNTABILITY & TRACEABILITY</span>
              <h2>Case Audit History</h2>
              <p>Review recorded decisions, transfers and other case actions.</p>
            </div>
          </div>
          <div className="intelligence-controls">
            <div className="control-field">
              <label className="field-label" htmlFor="audit-case">Select case</label>
              <select id="audit-case" value={auditCaseId}
                onChange={(e) => {
                  setAuditCaseId(e.target.value);
                  setAuditHistory([]);
                  setAuditMessage("");
                }}>
                {cases.map((item) => <option key={item.case_id} value={item.case_id}>
                  {item.case_id} — {item.category} ({item.bureau})
                </option>)}
              </select>
            </div>
            <button onClick={loadAuditHistory} disabled={loadingAudit || !cases.length}>
              {loadingAudit ? "Loading…" : "View audit history"}
            </button>
          </div>
          {auditMessage && <p className="feedback-message" role="status">{auditMessage}</p>}
          {auditHistory.length > 0 && <div className="table-wrapper">
            <table>
              <thead><tr><th>Date & time</th><th>Action</th><th>Actor</th><th>Details</th></tr></thead>
              <tbody>{auditHistory.map((action) => <tr key={action.id}>
                <td>{action.created_at ? new Date(action.created_at).toLocaleString() : "—"}</td>
                <td><StatusBadge value={action.action_type} /></td>
                <td>{action.actor_role || "—"}</td>
                <td className="audit-details">{action.details || "—"}</td>
              </tr>)}</tbody>
            </table>
          </div>}
        </section>

        <footer className="site-footer">
          <div className="footer-brand">OneFile India <span>·</span> Demonstration Prototype</div>
          <p>One institution. One consolidated view. Better bureau coordination.</p>
          <p className="footer-disclaimer">
            Independent prototype for demonstration purposes. Not an official AICTE service.
          </p>
        </footer>
      </main>
    </div>
  );
}
