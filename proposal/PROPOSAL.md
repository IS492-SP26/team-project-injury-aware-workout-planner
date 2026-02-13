# Problem & importance
Musculoskeletal injuries, particularly those affecting the knee and shoulder, are common among physically active individuals. While clinical rehabilitation programs restore function at the injured site, they typically focus on localized therapeutic exercises and do not provide structured guidance for safely maintaining full-body training during or after recovery.

As a result, individuals who wish to remain active often face a practical dilemma: either restrict themselves to narrow rehabilitation routines or attempt to adapt general fitness programs without clear knowledge of movement contraindications, recovery stage considerations, or safe load progression. This gap is amplified in self-directed training environments, where users rely heavily on commercial fitness applications.

However, most existing fitness platforms prioritize performance optimization rather than injury-aware adaptation. The absence of integrated, context-sensitive guidance increases the risk of reinjury and delayed recovery, underscoring the need for systems that bridge rehabilitation considerations with everyday training.

# Prior Systems & Gaps

Several AI-based fitness tools attempt to personalize exercise:

**Ray (Live AI Trainer)** dynamically adjusts workouts using voice and computer vision. It optimizes performance in real time but lacks structured injury-specific clinical grounding and does not modify third-party content.

**ToneFit (AI Fitness Planner)** generates structured strength programs based on goals and constraints. While it supports long-term planning, it does not analyze or adapt user-selected workout videos and has limited injury-aware safety modeling.

Academic literature also explores large language models (LLMs) for exercise prescription. A recent scoping review found that LLMs can generate personalized exercise recommendations and enhance engagement but emphasized that they must function as decision-support systems rather than replacements for clinicians (Lai et al., 2025). The review highlights the need for structured grounding, safety validation, and expert oversight.

The critical gap across prior systems is this:

> No system surgically analyzes and modifies *existing* workout content (video or text) based on structured injury constraints.

Current tools generate new plans but do not adapt unstructured third-party content to align with rehabilitation principles. This leaves a clear opportunity for an injury-aware content adaptation engine.

# Proposed Approach

We propose an **Injury-Aware Workout Adaptation System** that modifies both video-based and text-based workout content according to structured injury constraints.

### Input Layer

The system accepts:

* YouTube workout links
* User-pasted text workout plans

Users complete a short injury-context questionnaire:

* Injury type (knee or shoulder condition)
* Recovery stage
* Pain level (0–10)
* Optional notes

### Content Processing

For video input:

* Extract transcript
* Apply OCR to detect on-screen exercise names
* Normalize exercise terminology

For text input:

* Parse exercise names
* Structure sets, reps, and sequence

### Injury Logic Layer

Exercises are mapped to injury-specific risk categories (e.g., deep knee flexion, pivoting, overhead loading). The system flags unsafe movements and generates safer substitutes that preserve workout intent (e.g., replace jump squats with step-ups; replace overhead press with neutral-grip floor press).

### Output

The system returns:

* Timestamps to avoid (for video)
* Identified risky exercises
* Context-aware substitutes
* Short rationale for each substitution

Unlike prior tools, this system does not generate entirely new workouts. Instead, it modifies existing content to maintain user familiarity while improving safety.

This improves upon prior art by:

1. Operating as a content adaptation layer rather than a generator.
2. Embedding structured rehabilitation logic into unstructured fitness content.
3. Supporting both recovery users and injury-aware fitness enthusiasts.

