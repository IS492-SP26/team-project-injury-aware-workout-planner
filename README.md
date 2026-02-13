
# Problem statement

# Target users and core tasks

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
