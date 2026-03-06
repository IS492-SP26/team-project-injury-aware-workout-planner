## AdaptFit AI - Injury-Aware Workout Generation System

### Overview

The Injury-Aware Workout Generation system is designed to help users safely continue training while recovering from injuries. The system prioritizes **re-injury prevention** by assessing injury status before allowing workout generation or modification.

Instead of generic workout programs, the system uses **injury assessment + AI-assisted workout generation** to adapt workouts based on:

* Injury type
* Recovery stage
* Pain level
* Movement limitations
* Desired training focus

The core design goal is to ensure **safe exercise recommendations while maintaining training continuity.**

---

# 1. Key Design Principles

### Safety First

Users must pass a recovery readiness check before generating workouts.

### Adaptive Workouts

Workouts are modified dynamically based on injury and user goals.

### Minimal Friction

The workflow is designed to quickly move users from **assessment → workout generation.**

### AI-Assisted Personalization

AI generates safe workouts or modifies existing workouts based on injury constraints.

---

# 2. Primary User Journey

### Journey 1 — Generate a Safe Workout

1. User logs in
2. Sets up profile
3. Selects injury type
4. Completes injury assessment questionnaire
5. System evaluates recovery readiness
6. If cleared:

   * Select training type
   * Generate AI workout
7. AI generates safe workout plan

**Outcome:** Personalized injury-safe workout.

---

### Journey 2 — Modify Existing Workout

1. User logs in
2. Injury assessment completed
3. User chooses **Modify Existing Workout**
4. User pastes or uploads workout
5. AI removes risky exercises
6. AI replaces exercises with safer alternatives

**Outcome:** Existing workout adapted to injury.

---

### Journey 3 — Not Cleared for Training

1. User completes injury questionnaire
2. System determines user is not ready for training
3. User receives:

   * Recovery advice
   * Light mobility / physio suggestions

**Outcome:** Prevents unsafe workouts.

---

# 3. Task Flows

### Link to access user Task Flow: https://www.figma.com/board/Md3dmuTmp6ZitBkIMeSz0p/Task-Flow?node-id=0-1&t=HxkMTzP2tZcoH1FK-1

## Task Flow 1 — Injury Assessment

```
Login
   ↓
Profile Setup
   ↓
Injury Identification
   ↓
Injury Questionnaire
   ↓
Recovery Readiness Evaluation
```

Possible outputs:

* Cleared for workouts
* Not cleared for workouts

---

## Task Flow 2 — Generate New Workout

```
Recovery Cleared
   ↓
Select Training Style
   ↓
Select Workout Focus
   ↓
Generate Workout
   ↓
AI Processing
   ↓
Tailored Workout Plan
```

---

## Task Flow 3 — Modify Existing Workout

```
Recovery Cleared
   ↓
Choose "Modify Existing Workout"
   ↓
Import / Paste Workout
   ↓
AI Risk Detection
   ↓
Replace Unsafe Exercises
   ↓
Modified Workout
```

---

# 4. Key Screens & Interactions

### Link to access the UI prototype: https://stitch.withgoogle.com/projects/6423118269167892265
---

## 4.1 Login & Welcome

**Purpose**
Entry point for users.

**Key Elements**

* Login
* Sign up
* App introduction

**Primary Interaction**

User authenticates to access workout system.

---

## 4.2 User Profile Setup

**Purpose**
Collect basic user information.

**Key Data**

* Age
* Fitness level
* Training experience

**Outcome**

Profile stored for personalized workout generation.

---

## 4.3 Injury Identification

**Purpose**
Identify injury location and type.

**Examples**

* Knee
* Shoulder
* Back
* Ankle

**Interaction**

User selects injured body area.

---

## 4.4 Injury Assessment Questionnaire

**Purpose**
Evaluate recovery readiness.

**Inputs**

* Pain level
* Mobility restrictions
* Recent activity tolerance
* Recovery duration

**Output**

Recovery readiness score.

---

## 4.5 Recovery Readiness Result

### Cleared State

User is cleared to train.

Options displayed:

* Generate workout
* Modify existing workout

---

### Not Cleared State

User receives warning and recovery advice.

Suggested actions:

* Rest
* Light rehab
* Mobility exercises

---

## 4.6 Workout Type Selection

User selects training style.

**Options**

* Strength Training
* HIIT
* Endurance
* Running

---

## 4.7 Strength Training Setup

If strength training is selected:

**Workout Categories**

* Single muscle group

  * Chest
  * Back
  * Shoulders
  * Legs
  * Arms

* Compound workouts

  * Upper body
  * Lower body
  * Full body

---

## 4.8 Choose Generation Path

Users choose between two actions:

### Generate New Workout

AI creates workout from scratch.

### Modify Existing Workout

AI adjusts an existing workout plan.

---

## 4.9 Import or Paste Workout

User inputs their workout plan.

Examples:

* Text workout plan
* Structured list
* Copy-pasted program

---

## 4.10 AI Generation Loading State

Displays progress while AI:

* Analyzes injury constraints
* Detects risky exercises
* Generates alternatives

---

## 4.11 Modified Workout Results

AI returns modified workout.

Features:

* Risky exercises removed
* Safe alternatives suggested
* Notes explaining changes

---

## 4.12 New Tailored Workout Plan

AI generates a complete workout.

Each exercise includes:

* Sets
* Reps
* Intensity
* Injury safety notes

---

# 5. Critical Interactions

### Injury Risk Detection

AI identifies exercises that stress the injured body part.

Example:

```
Squats → Risky for knee injury
Replacement → Leg press (controlled range)
```

---

### Workout Substitution Logic

The system uses:

```
Exercise Risk Mapping
+
Injury Type
+
Recovery Stage
```

To generate safe alternatives.

---

# 6. System Requirements

### Functional Requirements

1. Injury assessment module
2. Recovery readiness evaluation
3. Workout generation engine
4. Workout modification engine
5. Exercise risk detection

---

### Non-Functional Requirements

Safety critical recommendations
Low latency generation
Scalable AI inference
Clear UX feedback

---

# 7. Success Criteria

The system succeeds if it:

* Prevents unsafe exercises for injured users
* Generates personalized workouts
* Reduces friction in injury-safe training
* Provides clear reasoning for modifications


