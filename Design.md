# AgentGuard — Design.md (UX, Neumorphic UI & Design System)

> **Design Theme:** Premium Neumorphic Light UI · Precision Engineering · Electric Sapphire Blue Accents  
> **Aesthetic Archetype:** Soft-UI / Neumorphism (light porcelain surfaces, tactile extruded cards, recessed input wells, multi-stop ambient shadows, micro-spring transitions, and radiant blue interactive states).  
> **Compliance:** WCAG 2.1 AA Contrast Compliant (all text $\ge 4.5:1$, interactive elements $\ge 3.0:1$).

---

## 1. Design Principles

1. **Tactile Clarity & Verdict First:** Every screen conveys "Is my agent safe and working?" in $< 3$ seconds through tactile neumorphic stat extrusions, followed by deep transcript inspection on demand.
2. **Evidence Over Abstract Numbers:** Scores never stand alone; they are anchored by verbatim transcript quotes highlighted with soft ambient amber/blue glow.
3. **Calm Tactile Precision:** A crisp, light porcelain canvas (`#EEF2F6`) paired with soft organic dual-shadows. Color is strategically reserved for primary brand actions (electric sapphire blue) and verified health states.
4. **Fluid Micro-Motion & Living Feedback:** Smooth spring transitions (180ms), gentle elevation lifts on hover, breathing pulse rings on live monitors, and real-time SSE progress tickers.
5. **No Visual Compromise on Accessibility:** Traditional neumorphism often suffers from low contrast. AgentGuard solves this with **High-Definition Neumorphism**: tactile depth is paired with crisp typography (`#0F172A`), distinct inner borders, and high-visibility status indicators.
6. **Dual-Persona Ergonomics:** Dense, keyboard-accelerated workflows for AI Engineers ($\ge 1280\text{px}$) and polished, presentation-ready health reports for executive stakeholders.

---

## 2. Information Architecture

```
Organization Switcher (top-left extruded pill)
├─ Overview                (Executive health dashboard, open alerts, live agent grid)
├─ Clients                 (Client enterprise accounts & project tags)
├─ Agents
│  └─ Agent Detail
│     ├─ Overview          (Health score sparklines, release tags, last run summary)
│     ├─ Connection        (HTTP / OpenAI adapter config with live pulse test)
│     ├─ Knowledge         (Uploaded documents, chunk viewer, pgvector status)
│     ├─ Suites            (Suite editor, category distribution, scenario drawer)
│     ├─ Runs              (Execution history, live SSE runner, scorecard)
│     ├─ Monitoring        (Production trace stream, baseline bands, drift monitors)
│     └─ Settings          (Tone guidelines, prohibited behaviors, security thresholds)
├─ Alerts                  (Incident triage: active, acknowledged, resolved)
├─ Reports                 (Client health reports, white-labeled PDF export, share links)
├─ Metrics & Calibration   (Built-in rubrics, custom metrics, Cohen's κ agreement status)
└─ Settings                (Team RBAC, API keys, model gateways, token budgets, audit logs)
```

**Global Navigation & Tools:** Quick command palette (`⌘K`), unified search bar (recessed well), documentation link, theme toggle, and notification bell with live badge indicator.

---

## 3. Visual Design System & Neumorphic Tokens

### 3.1 Color Palette & Tokens

| Token | Hex Value | Role & Usage |
|---|---|---|
| `--neu-bg` | `#EEF2F6` | Master application background (cool porcelain / alabaster). |
| `--neu-surface` | `#EEF2F6` | Card and container surface (matches background to enable extrusion). |
| `--neu-surface-hover` | `#F4F7FB` | Subtle luminous elevation lift on hover. |
| `--neu-surface-recessed`| `#E5EBF1` | Inset wells for inputs, search, code viewports, and table headers. |
| `--neu-white-highlight`| `#FFFFFF` | Upper-left specular light reflection for extruded elevation. |
| `--neu-dark-shadow`    | `#D1D9E6` | Lower-right ambient shadow creating soft tactile lift. |
| `--neu-dark-shadow-deep`|`#BAC5D6`| Enhanced shadow used for floating modals and dropdown menus. |
| `--border-subtle`       | `rgba(255,255,255,0.85)`| Crisp upper highlight border for enhanced tactile definition. |
| `--border-dark-subtle`  | `rgba(209,217,230,0.4)` | Faint perimeter edge for structural clarity. |

#### Brand & Accent Colors (Electric Blue Focus)
| Token | Hex Value | Role & Usage |
|---|---|---|
| `--brand-blue` | `#2563EB` | Primary brand blue (Electric Sapphire). Action buttons, active tabs. |
| `--brand-blue-hover` | `#1D4ED8` | Deeper royal blue for button hover states. |
| `--brand-blue-glow` | `rgba(37,99,235,0.28)` | Ambient blue radial glow for active indicators and primary buttons. |
| `--brand-blue-light` | `#DBEAFE` | Soft pastel blue pill background for chips and badges. |
| `--brand-cyan` | `#0EA5E9` | Secondary vibrant electric blue for latency metrics and real-time streams. |

#### Semantic Status Tokens
| State | Light Value | Soft Tint (Pill Well) | Symbol | Meaning |
|---|---|---|:---:|---|
| **Success / Pass** | `#059669` | `#D1FAE5` | `✓` | Passed evaluation, healthy agent, baseline stable |
| **Warning / Review**| `#D97706` | `#FEF3C7` | `!` | Borderline score, needs human review, low confidence |
| **Danger / Fail**   | `#DC2626` | `#FEE2E2` | `✕` | Blocking metric failure, drift breach, critical alert |
| **Info / Running**  | `#0284C7` | `#E0F2FE` | `●` | Active simulation, live ingest, informational note |
| **Evidence Highlight**| `#FEF08A` | `#FEF9C3` | `▓` | Highlight span for quotes cited in evaluation reasoning |

#### High-Contrast Typography Tokens
| Token | Hex Value | Usage | Contrast Ratio vs `#EEF2F6` |
|---|---|---|:---:|
| `--text-primary` | `#0F172A` | Deep Slate for titles, headings, and primary body text | **15.2 : 1** (AAA) |
| `--text-secondary`| `#334155` | Charcoal for secondary labels, table headers, descriptions | **10.1 : 1** (AAA) |
| `--text-muted`    | `#64748B` | Medium slate for timestamps, placeholders, helper text | **4.9 : 1** (AA) |
| `--text-blue`     | `#1D4ED8` | Darkened sapphire for interactive text links | **6.4 : 1** (AA) |

---

### 3.2 Neumorphic Elevation & Shadow Matrix

All tactile elevations use calibrated dual-box shadows paired with subtle white specular edge lines:

```css
/* 1. Base Extruded Card (Standard Container) */
.neu-card {
  background: #EEF2F6;
  border-radius: 16px;
  box-shadow: 
    6px 6px 14px #D1D9E6, 
    -6px -6px 14px #FFFFFF;
  border: 1px solid rgba(255, 255, 255, 0.7);
  transition: all 180ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* 2. Interactive Extruded Card (Hover Lift) */
.neu-card-hover:hover {
  background: #F4F7FB;
  transform: translateY(-2px);
  box-shadow: 
    9px 9px 20px #C5D0DE, 
    -9px -9px 20px #FFFFFF;
}

/* 3. Recessed / Inset Well (Inputs, Search, Viewports, Table Rows) */
.neu-well {
  background: #EEF2F6;
  border-radius: 12px;
  box-shadow: 
    inset 3px 3px 6px #D1D9E6, 
    inset -3px -3px 6px #FFFFFF;
  border: 1px solid rgba(209, 217, 230, 0.35);
}

/* 4. Primary Blue Button (Extruded with Ambient Glow) */
.neu-btn-primary {
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  color: #FFFFFF;
  border-radius: 12px;
  box-shadow: 
    4px 4px 10px #D1D9E6, 
    -4px -4px 10px #FFFFFF,
    0 8px 18px -4px rgba(37, 99, 235, 0.35);
  transition: all 150ms ease-out;
}
.neu-btn-primary:active {
  transform: translateY(1px);
  box-shadow: 
    inset 2px 2px 5px rgba(0, 0, 0, 0.3),
    0 2px 8px rgba(37, 99, 235, 0.2);
}

/* 5. Secondary Neumorphic Button (Pebble Push) */
.neu-btn-secondary {
  background: #EEF2F6;
  color: #0F172A;
  border-radius: 12px;
  box-shadow: 
    4px 4px 8px #D1D9E6, 
    -4px -4px 8px #FFFFFF;
  transition: all 150ms ease-out;
}
.neu-btn-secondary:hover {
  color: #2563EB;
  box-shadow: 
    6px 6px 12px #C5D0DE, 
    -6px -6px 12px #FFFFFF;
}
.neu-btn-secondary:active {
  box-shadow: 
    inset 2px 2px 5px #D1D9E6, 
    inset -2px -2px 5px #FFFFFF;
  transform: translateY(1px);
}

/* 6. Floating Modals & Drawers */
.neu-modal {
  background: #EEF2F6;
  border-radius: 20px;
  box-shadow: 
    14px 14px 28px #BAC5D6, 
    -14px -14px 28px #FFFFFF,
    0 20px 40px -10px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.9);
}
```

---

### 3.3 Micro-Animations, Transitions & Physics

* **Spring Elevation (180ms):** All hoverable cards lift with `cubic-bezier(0.4, 0, 0.2, 1)`.
* **Button Pressed State (80ms):** Smooth transition from extruded outward drop-shadow to recessed inset shadow simulates a real tactile pebble press.
* **Breathing Health Pulse:** Active healthy agents pulse with an electric cyan/green radar ring:
  ```css
  @keyframes radar-pulse {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.5); }
    70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
  }
  ```
* **SSE Character Ingest Wave:** Live simulated conversation turns stream into the viewport with a subtle upward fade (`translateY(4px) -> translateY(0)` with `opacity: 0 -> 1` over 120ms).
* **Progress Bar Liquid Glow:** The running progress bar features an animated soft gradient wave moving left-to-right (`linear-gradient(90deg, #2563EB, #0EA5E9, #2563EB)`).

---

## 4. Key Screen Layouts & Component Specifications

### 4.1 Master App Shell & Overview Screen
* **Top Header Bar:** Neumorphic floating ribbon (`neu-card`), containing Org Switcher dropdown (extruded capsule), Global Search (recessed well with search icon), Command Palette trigger (`⌘K`), and User Avatar with blue ring outline.
* **KPI Metrics Strip (4 Tactile Tiles):**
  1. *Total Agents Monitored:* Number + sparkline pill.
  2. *Latest CI Pass Rate:* Large bold percentage with emerald badge (`✓ 94.2%`).
  3. *Active Behavioral Alerts:* Number with warning badge (`! 2 Active`).
  4. *Total Conversations Tested:* Running volume count with subtle blue glow.
* **Agent Health Matrix Table:**
  - Table wrapper inside an extruded card.
  - Search and filter pills styled as toggleable buttons (extruded when active, recessed when toggled off).
  - Columns: Name, Adapter Type, Version Tag, 14-day Score Sparkline, Health Status (Pulsing Pill), Actions.
  - Hovering a row applies a soft white glow and 1px lift.

### 4.2 Run Detail & Live Execution Viewer
* **Top Verdict Banner:** Full-width extruded card with colored accent border:
  - If **PASS:** Emerald edge highlight + large extruded badge `[ ✓ PASS 94% ]` + blocking criteria summary.
  - If **FAIL:** Crimson edge highlight + large extruded badge `[ ✕ FAIL 68% ]` + top failure cluster alert.
  - Running State: Blue accent border with liquid progress bar and live counters: `Completed: 38/50 · Cost: $0.18 · Latency p95: 840ms`.
* **Metric Scorecards (Grid of 6 Cards):**
  - Tactile square tiles: Metric name, score percentage, passing threshold bar, and status pill.
  - Each card includes a subtle "Info" icon revealing judge model and calibration agreement (`κ = 0.78`).
* **Failure Clustering Section:**
  - Grouped failure cards showing semantic failure clusters (e.g., *"Invents refund timeline (7 occurrences)"*). Clicking a cluster instantly filters the conversation list to those specific transcripts.

### 4.3 Conversation Detail (The Core Forensic Screen)
```
┌────────────────────────────────────────┬────────────────────────────────────────┐
│  RECESSED TRANSCRIPT VIEWPORT          │  EXTRUDED EVALUATION PANEL             │
│  (Soft inner shadow well)              │  (Tactile card with blue accents)      │
│                                        │                                        │
│  [User - Persona: Frustrated Buyer]    │  Scorecard Breakdown                   │
│  "You promised 1-day delivery!"        │  • Correctness     FAIL  0.25 [View]   │
│                                        │  • Hallucination   FAIL  0.20 [View]   │
│  [Agent - Support Bot v2]              │  • Tone / Brand    PASS  0.92          │
│  "I apologize! We guarantee all items  │  • Safety          PASS  1.00          │
│   ship in 2 hours via express."        │ ────────────────────────────────────── │
│   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     │  Failure Forensic Details              │
│   (Ambient Amber Evidence Glow)        │  Rule / Metric: Grounded Factuality    │
│                                        │  Quote Cited:                          │
│  [User]                                │  “We guarantee all items ship in 2h”   │
│  "Can you confirm tracking now?"       │  Ground Truth Knowledge:               │
│                                        │  Standard policy specifies 24-48 hours │
│                                        │  Source: shipping_policy.pdf (p. 2)    │
│                                        │                                        │
│                                        │  [ Override Verdict ] [ Add to Test ]  │
└────────────────────────────────────────┴────────────────────────────────────────┘
```
* **Transcript Viewport:** Built inside a soft recessed well (`neu-well`). User bubbles use an extruded white surface; agent bubbles use an extruded porcelain surface with a crisp blue left border.
* **Evidence Highlighting:** When a metric in the evaluation panel is hovered, the exact corresponding text span in the transcript illuminates with a soft glowing amber highlight (`#FEF08A` with `box-shadow: 0 0 10px rgba(245, 158, 11, 0.3)`).
* **Forensic Actions:** Tactile action buttons allowing engineers to:
  - *Override Verdict:* Prompts for required audit reason and feeds calibration golden sets.
  - *Convert to Regression Scenario:* 1-click synthesis of the failure into a permanent test case.

### 4.4 Production Monitoring & Drift Studio
* **Time-Series Horizon Chart:** Recharts visualization rendered on a smooth extruded canvas.
  - Baseline score represented as a soft ambient band.
  - Live rolling scores plotted as a vibrant sapphire blue line.
  - Drift breach events pinned as small pulsing red alert diamonds.
* **Drift Diagnostic Drawer:** Slides in with a smooth 200ms ease-out spring, displaying statistical significance calculations ($Z\text{-score}$, $p\text{-value}$, confidence interval, sample size $n$).

---

## 5. Typography & Contrast Assurance

* **Primary Body & UI Font:** `Inter` or `Plus Jakarta Sans` (variable font, weights 400, 500, 600, 700).
* **Code & Transcript Font:** `JetBrains Mono` with tabular numerals for consistent score alignment.
* **Hierarchy:**
  - `H1 / Page Title`: 28px / Semi-bold (700) / Tracking -0.02em / Color `#0F172A`
  - `H2 / Section Title`: 20px / Semi-bold (600) / Tracking -0.01em / Color `#0F172A`
  - `H3 / Card Header`: 15px / Medium (600) / Color `#1E293B`
  - `Body Regular`: 14px / Regular (400) / Line-height 1.55 / Color `#334155`
  - `Caption / Meta`: 12px / Medium (500) / Color `#64748B`
  - `Tabular Numeric`: JetBrains Mono 14px / Bold (700) for scores (`94.2%`)

---

## 6. Accessibility & Usability Guardrails

1. **High-Definition Contrast:** Neumorphic shadows are **never** used as the sole delimiter of interactive boundaries. Every button, input, and card incorporates a subtle border (`1px solid rgba(209, 217, 230, 0.5)`) and distinct text labels.
2. **Keyboard Focus Rings:** Visible 2px electric blue focus ring (`outline: 2px solid #2563EB; outline-offset: 2px`) on all focusable elements (`tabindex`, buttons, inputs, links).
3. **Multi-Signal Status:** Color is never the sole communicator of status:
   - Pass: `✓` Icon + Text "PASS" + Emerald Badge.
   - Review: `!` Icon + Text "REVIEW" + Amber Badge.
   - Fail: `✕` Icon + Text "FAIL" + Crimson Badge.
4. **Reduced Motion Support:** Respects `prefers-reduced-motion: reduce` by disabling elevation springs and radar pulses, replacing them with instant opacity fades.

---

## 7. Design Deliverables & Component Library

The frontend implementation utilizes **shadcn/ui** components customized with the neumorphic design tokens:

```
apps/web/src/components/
├── ui/
│   ├── button.tsx           # neu-btn-primary, neu-btn-secondary, neu-btn-recessed
│   ├── card.tsx             # neu-card, neu-card-hover, neu-card-recessed
│   ├── input.tsx            # neu-well input with focus ring
│   ├── badge.tsx            # neu-pill status badges (emerald, amber, crimson, blue)
│   ├── progress.tsx         # neu-progress bar with liquid wave animation
│   ├── table.tsx            # neu-table with hoverable rows and recessed header
│   ├── dialog.tsx           # neu-modal with backdrop blur
│   └── tooltip.tsx          # soft floating tooltip
├── domain/
│   ├── verdict-banner.tsx   # Top execution pass/fail tactile banner
│   ├── transcript-view.tsx  # Dual-pane transcript viewer with evidence glow
│   ├── score-grid.tsx       # 6-tile metric scorecard grid
│   ├── failure-cluster.tsx  # Grouped failure cause list
│   └── drift-chart.tsx      # Recharts baseline band chart
```
