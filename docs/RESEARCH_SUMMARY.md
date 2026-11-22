# Research Summary & Theoretical Grounding

**Course:** Prompt Engineering (SCSE4041)  
**Project:** C20 AI-Powered Study Plan Generator  
**Reference Citation:** Liu et al. (2026) Meta-Analysis  

---

## 1. Primary Empirical Literature

> **Liu, B., Ma, P., and Jia, F. (2026).**  
> *“Systematic review and meta-analysis of the impact of time management on college students' learning outcomes.”*  
> **Frontiers in Psychology.**  
> DOI: [https://doi.org/10.3389/fpsyg.2026.1700298](https://doi.org/10.3389/fpsyg.2026.1700298)

### Key Meta-Analytic Parameters
- **Sample Size:** 31 independent empirical studies.
- **Participant Pool:** 13,506 college and university students.
- **Core Findings:** 
  1. A statistically significant, moderate positive correlation ($r \approx 0.38$, $p < 0.001$) exists between structured time-management strategies and academic learning outcomes.
  2. Setting explicit, bounded time limits per task significantly reduces cognitive fatigue and academic procrastination.
  3. Pre-planned revision intervals yield a higher effect size ($d = 0.44$) on exam retention than massed cramming sessions.

---

## 2. Synthesis with Prompt Engineering Principles

The findings of Liu et al. directly justify the necessity of **Constraint-Based Prompting** in Project C20:

| Psychological / Cognitive Finding | LLM Analogue / Vulnerability | C20 Prompt Engineering Solution |
| :--- | :--- | :--- |
| **Cognitive Overload & Planning Fallacy:** Students consistently underestimate task duration and overbook daily schedules. | **Naive Generation (V1):** Baseline LLMs exhibit optimism bias, easily scheduling 7–9 hours into a 4-hour budget. | **Constraint-Aware Prompting (V2):** Hard numerical bounds on daily study hours ($\sum \text{hours} \le \text{limit}$). |
| **Active Recall vs. Passive Reading:** Retention peaks when students interleave practice questions with concept review. | **Monolithic Schedules:** Naive prompts generate repetitive "read chapter" tasks without pedagogical variance. | **Structured Output (V3):** Enforces explicit session categorization into `Concept Learning`, `Revision`, and `Practice Questions`. |
| **Procrastination & Weak Subject Avoidance:** Learners defer cognitively demanding topics until days before the exam. | **Syllabus Drift:** Zero-shot prompts fail to prioritize weak subjects without designated quotas. | **Weak Subject Boosting (V2–V4):** Explicit prompt constraint allocating $\ge 35\%$ additional time and earlier review slots to weak subjects. |
| **Temporal Disorientation:** Cramming immediately prior to or after deadlines causes high stress and poor retention. | **Temporal Hallucinations:** Schedulers mistakenly place study sessions on or after exam dates. | **Cutoff Constraints & CoVe (V4):** Programmatic and prompt-level audit enforcing zero study after the official exam cutoff date. |
