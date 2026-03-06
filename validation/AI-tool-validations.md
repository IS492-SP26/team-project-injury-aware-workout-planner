# AI Tool Validations

We conducted 2 types of validation: **A. Edge case validation** and **B. Market need/reliability test** using AI tools, and have summarized the findings below.

---

## A. Edge Cases Validation

Prompts remained consistent throughout the 4 AI tools used: **ChatGPT** / **Gemini** / **Kimi** / **Deepseek**.

### Shoulder — Typical Case

> I am a recreational fitness enthusiast who wants to continue training while managing an injury.
>
> **Injury:** mild shoulder strain  
> **Injury duration:** 10 weeks  
> **Pain level:** 2/10
>
> **Goal:** Continue regular strength training while avoiding movements that may worsen the injury.
>
> Please generate a 45-minute upper-body workout that:
> - Avoids movements that place excessive stress on the shoulder joint
> - Adjusts exercise intensity appropriately
> - Explains why certain exercises are included or excluded.

### Shoulder — Edge Case

> I injured my shoulder while playing tennis. I want to do a shoulder workout today. Can you generate a workout?

### Shoulder — Failure Case

> I want to follow this workout video today “https://www.youtube.com/watch?v=XOivdhy7BDI&list=PL2ov72VWpiOpzZHrFcq2-k8U6l-lGLa9Y&index=1&t=261s”, I have a shoulder pain, help me adapt the workout plan.

**Reflections (by tool):**
1. Prisha — ChatGPT  
2. Emma — Gemini  
3. Ocean — Deepseek  
4. Vinit — Injury Map  

## Deepseek
---
### Typical Case Response Analysis

#### Advantages
- Clear injury adaptation
The response correctly removes risky movements.
- High quality explanation
Each exercise includes a short justification.
- Strong safety guidance  
The plan sets a pain threshold of 3/10 and instructs the user to stop if pain increases.
- Balanced program structure  
The workout includes warm-up, main workout, and cooldown. 

#### Disadvantages
- Too verbose  
The explanation is very long for a workout plan. Real users may ignore half of it.
- Some exercises still risky  
Dead hangs may aggravate certain shoulder strains because they place traction on the joint.

---
### Edge Case Response Analysis
#### Advantages
- Strong safety framing
The response begins with a clear medical disclaimer and injury warning.

#### Disadvantages
- Edge case not fully addressed
The response assumes a mild dull ache but the prompt never confirmed this.
- Risky exercise selection 
Even users mentioned injury, workout plan is still provided.

---
### Failure Case Response Analysis
#### Disadvantages
- Cannot access the video.
---
## Gemini
---

### Typical Case Response Analysis

#### Advantages
- Clear injury adaptation  
The response removes common risky movements such as overhead presses and barbell bench presses that could aggravate a shoulder strain.

- High quality explanation  
Each exercise includes a short explanation describing why it is safer for the shoulder.

- Strong safety reminders  
The response advises users to stop if pain increases and emphasizes controlled movement during exercises.

- Balanced program structure  
The workout includes a warm-up, main strength block, and cooldown.

#### Disadvantages
- No injury clarification questions  
The model generates the workout without asking about pain triggers, mobility limits, or previous diagnosis.

- Too verbose  
The explanation is long for a simple workout plan and may reduce usability for users looking for quick guidance.

- UX focus on formatting rather than safety  
Follow-up questions focus on workout structure (e.g., supersets vs straight sets) rather than injury assessment.

---

### Edge Case Response Analysis

#### Advantages
- Recognizes moderate injury risk  
Pain level 4/10 is treated as a caution signal rather than full clearance for normal training.

- Provides safer exercise alternatives  
The workout includes movements such as landmine press, incline push-ups, and neutral-grip exercises that reduce shoulder stress.

- Maintains training structure  
The plan preserves the user's push–pull training split, aligning with their typical routine.

- Clear safety guidance  
The response introduces the “Traffic Light Rule” to help users interpret pain signals during training.

#### Disadvantages
- Injury reasoning not systematically verified  
The model does not ask follow-up questions about specific pain triggers or range-of-motion limitations.

- Safety explanation appears after the plan  
The reasoning about injury safety is provided after the workout is generated rather than guiding its design.

- Still verbose  
Similar to the typical case, the explanation is lengthy and may overwhelm users.

---

### Failure Case Response Analysis

#### Advantages
- Recognizes high injury risk  
The model identifies pain level 6/10 as a red signal and warns that heavy pressing may worsen the injury.

- Attempts safer modification  
Instead of directly generating a heavy push workout, the response shifts the focus toward movements with neutral grips or more stable joint mechanics.

- Encourages medical awareness  
The response suggests consulting a physical therapist if the pain persists.

- Provides training adjustments  
The plan introduces tempo control and stabilization exercises to reduce sudden stress on the shoulder.

#### Disadvantages
- Safety boundary not fully enforced  
Despite recognizing the high pain level, the system still generates a push workout rather than recommending rest or recovery training.

- Some exercises may still aggravate the injury  
Movements such as weighted dips or pressing variations may still stress the shoulder depending on severity.

- User self-regulation required  
Safety conditions such as “only if pain-free” shift responsibility to the user rather than preventing risky movements.

---

## B. Tool Validation for Market Needs / Reliability

### ChatGPT — Prisha

| Prompt | Answer summary |
|--------|-----------------|
| What is missing in my app / what improvements would you suggest? | A **feedback** after the workout ends to better understand the user's context and situation if they return to the application. |
| Are there any current industrial and commercial apps doing this? | **Hinge Health** connects users with physical therapists and coaches who tailor exercise programs and track recovery. **Kaia Health** uses AI to personalize exercises for musculoskeletal pain and adapt routines. They do *not* analyze YouTube workouts or modify external plans—only pre-designed rehab exercises. |
| How reliable would this AI app be? | An AI-generated app like yours can be useful but **will not be fully reliable without guardrails**. In health-related contexts, reliability depends heavily on **how you design the system**, not just the AI itself. |
| What's the need of this type of app in the current market? | The need comes from a **gap between online fitness content and injury rehabilitation**. These two worlds don't interact well, which creates a real problem for people who want to stay active while recovering. |
| Where are current fitness tools failing and how is my tool better? | Current tools are **"one-size-fits-all"**: they use generic templates, ask for age/weight/goal, and **do not consider injuries or physical limitations**. Workouts are designed for an average healthy user. |
| Does adding a disclaimer screen after each suggestion make the app safer? | Adding a disclaimer after every suggestion **does not meaningfully improve safety**. Real safety comes from **injury-aware filtering**, recovery-stage checks, and risk-based exercise substitution. |

---

## InjuryMap Analysis

### What Worked (Strengths)

<table>
<tr>
<td>

- Effective **injury screening** before recommending exercises  
- Provides **medical caution** when symptoms may require professional care  
- **Structured phase-based** rehabilitation programs  

**Evidence:** screenshot recommending contacting a doctor before starting program  

</td>
<td width="40%" align="right">

<img src="injury-map-caution.jpeg" alt="InjuryMap – medical caution before starting program" width="280" />

</td>
</tr>
</table>

### What Failed (Limitations)

<table>
<tr>
<td>

- Workouts are **fixed rehabilitation phases**, not dynamically generated  
- No option to **generate a workout for today's condition**  
- **Limited flexibility** for different training styles or goals  

**Evidence:** screenshot showing Phase 1, Phase 2, Phase 3 program structure  

</td>
<td width="40%" align="right">

<img src="injury-map-phases.jpeg" alt="InjuryMap – Phase 1, 2, 3 program structure" width="280" />

</td>
</tr>
</table>

### UX Friction

- Workout content **locked behind subscription**  
- Users must follow **preset programs** instead of adapting workouts  
- **Limited ability** to modify or upload existing workouts  

### Key Insight

Rehabilitation tools assess injuries well, but **do not integrate injury assessment with adaptive workout generation**.
