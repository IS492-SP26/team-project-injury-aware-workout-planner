
# Problem statement
Musculoskeletal injuries, particularly those affecting the knee and shoulder, are common among physically active individuals. Clinical rehabilitation programs are typically structured around restoring function at the injured site and are often limited to localized therapeutic exercises. While such programs are essential for recovery, they do not necessarily provide guidance on safely maintaining comprehensive, full-body training routines during or after rehabilitation.

Many individuals recovering from injury want to continue regular physical activity beyond isolated rehabilitation exercises. However, they often lack structured guidance on adapting full-body workouts to account for injury status, time since injury, and recovery progression. As a result, individuals may either restrict themselves to narrow rehabilitation protocols or attempt to modify general fitness programs without sufficient knowledge of movement contraindications and safe load progression.

Most commercial fitness applications are designed for performance optimization rather than injury-aware adaptation. These systems rarely incorporate injury history or recovery stage into their recommendations, leaving users responsible for manually filtering exercises that may aggravate their condition.

This disconnect between localized rehabilitation planning and whole-body training integration creates a significant gap in digital fitness support. Improperly adapted exercise routines may increase the risk of reinjury or delay recovery, particularly in self-directed training environments. As AI-driven personalization continues to advance in digital health, there is an opportunity to develop systems that bridge rehabilitation considerations with safe, full-body training adaptation

# Target users and core tasks

## Target Users

### Individuals recovering from common musculoskeletal injuries
- ACL reconstruction
- Meniscal repair
- Patellofemoral pain (PFP)
- Knee osteoarthritis
- Rotator cuff injuries
- Shoulder impingement

### Users in mid-stage rehabilitation
- Cleared for strengthening
- Managing pain but resuming exercise
- Not in acute post-operative protection phase

### Fitness-conscious users who prefer following YouTube workouts
- Want to continue using existing fitness content
- Need injury-aware modifications

## Core Tasks

### Collect Injury Context
- Injury type
- Time since injury/surgery
- Pain level (0–10 scale)
- Optional user notes

### Analyze Workout Content
- Extract transcript from YouTube link
- Use OCR to detect on-screen exercise names
- Normalize exercise terminology

### Identify Risky Movements
- Flag exercises contraindicated for the selected injury
- Consider movement type (deep knee flexion, pivoting, overhead pressing, etc.)

### Provide Safer Alternatives
- Generate timestamped “avoid” markers
- Suggest substitute exercises that preserve workout intent
- Adjust intensity based on reported pain

### Future Enhancements
- Audio narration overlays
- Embedded GIF or short demo clips
- Adaptive updates based on user feedback

# Competitive landscape
## Existing systems/tools
### 1. Ray - A live AI trainer
https://www.rayfit.com/?ref=producthunt
#### Overview  
Ray creates personalized workout plans and adjusts them dynamically during workouts. It uses voice interaction and computer vision to guide sets and count reps.
#### Strengths
- Hands-free interaction via voice input
- Real-time workout adaptation
- Computer vision-based rep tracking
#### Limitations
- Focused on performance optimization, no structured rehab safety
- Does not have specific injury contextual knowledge
- Does not modify existing third-party workout videos
#### Key Gap  
Ray generates workouts based on users' real time reaction. It does not analyze and surgically modify existing content based on injuries.

### 2. ToneFit - AI fitness planner with tracking and animation
https://www.tonefitai.com/?ref=producthunt
#### Overview  
ToneFit generates structured strength training plans based on goals, equipment, and constraints.
#### Strengths
- Long-term structured plans
- Goal-aware plan generation
- Animated movement demos
- Workout logging and tracking
#### Limitations
- Animated movements are linked externally, not seamlessly embedded
- Focused on structured planning rather than content adaptation
- Limited injury-specific risk modeling
#### Key gap  
ToneFit plans workouts. It does not dynamically edit user-selected workout videos.


# Initial Concept
Concept Overview
We propose an injury-aware workout analysis system that helps users safely follow YouTube fitness videos while recovering from common knee and shoulder injuries.
The system first collects injury context through a short questionnaire (injury type, time since injury, pain level, optional notes). The user then provides a YouTube workout link. Using transcript extraction and OCR for on-screen exercise text, the system identifies potentially unsafe exercises and returns:
Timestamps to avoid
Safer substitute exercises
Future iterations aim to evolve from text-based substitutes to audio narration and eventually short GIF/video clips demonstrating safer alternatives.

# Value Proposition
1. Context-Aware Personalization
Recommendations are adjusted based on injury type, recovery stage, and pain level, not just generic “avoid” lists.
2. Works With Existing Content
Users can continue following their preferred YouTube trainers; the system adapts the workout to their recovery needs.
3. Replace, Don’t Just Remove
Instead of only flagging unsafe movements, the system suggests substitutes that preserve workout intent.
4. Meaningful Use of GenAI
GenAI enables:
Interpretation of unstructured user notes
Normalization of varied exercise naming from transcripts/OCR
Context-sensitive substitute generation
This project explores how generative models can support safer, more personalized fitness guidance for rehab.

# Milestones & roles
## Checkpoint 1: Public GitHub Kickoff + Proposal & Literature
Each member contributes equally to the project discussion and research.
For documentation, roles are:
Problem statement - Emma
Competitive landscape - Ocean
Target Users & Core Tasks - Vinit
Initial Concept & Value Proposition - Prisha
