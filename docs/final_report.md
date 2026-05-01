# AdaptFit AI: Injury-Aware Workout Adaptation for Safer Self-Directed Training

**Authors:** Vinit Agrharkar, Emma Zou, Yuyang Liu, and Prisha Singhania

## Abstract

AdaptFit AI is an injury-aware workout adaptation system designed for people who want to keep exercising while managing common musculoskeletal injuries. Most consumer fitness apps generate generic plans or optimize performance, while rehabilitation tools focus on prescribed therapeutic routines. AdaptFit addresses the gap between these worlds by collecting injury context, analyzing an existing workout video or pasted plan, flagging risky movements, and suggesting safer alternatives. The system combines structured onboarding, recovery readiness checks, YouTube or text workout processing, and LLM-assisted exercise risk adaptation. We evaluated the prototype through literature-grounded design work, AI tool validation, expert and user interviews, and a 21-response persona evaluation with Likert and qualitative questions. Results show strong usability, clear safety framing, and positive perceptions of injury assessment, while trust remains conditional on stronger explanations, sport-specific context, and escalation boundaries. The report summarizes the system, evaluation, limitations, and future directions.

## Introduction and Related Work

Musculoskeletal injuries are common among active people, especially in areas such as the knee, shoulder, ankle, and lower back. Clinical rehabilitation programs are essential for restoring function, but they often focus on localized therapeutic exercises rather than helping a person safely maintain broader full-body training. A person recovering from knee pain, shoulder irritation, or post-surgical weakness may still want to follow a favorite YouTube workout, continue strength training, or maintain general fitness. Without guidance, that person must either stop training beyond narrow rehabilitation exercises or manually guess which movements are unsafe. AdaptFit AI was developed around this gap: people need injury-aware support for modifying the workouts they already want to do.

The project began from the observation that current fitness tools and rehabilitation tools solve adjacent but incomplete problems. Fitness platforms generally optimize for adherence, performance, intensity, or personalization based on goals and equipment. Systems such as Ray and ToneFit illustrate this trend. Ray offers real-time AI training with voice interaction and computer vision, while ToneFit generates structured strength programs with tracking and animated demos. These tools may personalize workouts, but they are not designed to analyze third-party workout content and modify individual movements according to a user's recovery stage. Rehabilitation-oriented tools can be safer, but they often provide fixed exercise libraries or stage-based programs. They do not usually help a user adapt a separate YouTube routine or pasted workout plan.

The clinical and exercise-science literature reinforced that safety cannot be reduced to a simple "injured or not injured" flag. Buckthorpe et al. (2023) emphasize criteria-based rehabilitation after ACL reconstruction rather than progression based only on time. Return to higher intensity should consider strength symmetry, neuromuscular control, psychological readiness, and functional testing. Willy et al. (2019) similarly frame patellofemoral pain management around load management, hip and knee strengthening, and movement retraining. Kolasinski et al. (2020) strongly recommend exercise for osteoarthritis, but also emphasize education, symptom-guided progression, and attention to fluctuating pain. These sources shaped AdaptFit's core decision: ask about pain, movement limitations, and functional readiness before recommending workout modifications.

Other clinical sources pointed to the importance of protecting healing tissue and avoiding premature progression. van der Wal et al. (2022) describe the variability of meniscal repair rehabilitation protocols and the need to stage deep flexion, pivoting, and return-to-sport progression. Park and Song's (2017) work on web-based shoulder exercise videos showed that digital exercise guidance can improve access and clarity, but also that adherence and outcome tracking are difficult. Together, these findings suggested that a useful system should not simply produce a workout. It should structure the user's injury information, connect risk to specific movements, and present recommendations in a way that is easy to follow and conservative when uncertainty is high.

The AI literature provided both motivation and caution. Lai et al. (2025) reviewed LLMs for exercise recommendations and concluded that they may improve personalization and reduce workload, but should be treated as decision-support tools rather than replacements for clinicians. Canzone et al. (2025) describe AI's growing role in exercise programs, including personalization, monitoring, and feedback, but note concerns around data quality, transparency, and clinical validation. Shin et al. (2025) demonstrate how an LLM conversational agent can support exercise planning, while also showing that expert review remains important. For video understanding, keyframe and weak-supervision work such as Cakmak and Agarwal (2025) and Wu et al. (2025) suggested future directions for mapping visual content to workout segments. AdaptFit's current prototype does not fully solve computer vision-based form evaluation, but it uses the broader insight that unstructured workout media must be segmented and translated into a structured representation before injury reasoning can be applied.

The resulting design stance is intentionally narrow: AdaptFit is not a diagnostic system, a physical therapist, or a real-time form coach. It is a support tool that helps users adapt existing workout content by identifying potentially risky movements and proposing safer alternatives. This framing shaped the interface, prompts, evaluation questions, and ethical safeguards.

## Method

### System Description

AdaptFit AI is a web-based prototype with a deployable frontend and FastAPI backend. The user journey begins with sign-in and onboarding, then moves through basic profile information, injury selection, assessment, goals, workout import, and results. The deployed app contains separate pages for sign-in, onboarding-basic, onboarding-injury, onboarding-assessment, onboarding-goals, workouts, and results. Supabase is used in the deployable MVP for authentication and persistence of profile, assessment, and analysis history, while the backend handles survey normalization, YouTube or text workout processing, and AI-assisted adaptation.

The core input layer collects basic user and injury context. The survey normalizes age, training experience, activity level, goals, affected body part, diagnosis, date of injury, pain levels, functional screening, and movement limitations into a consistent `user_input_data` structure. The assessment emphasizes practical signals: daily pain, pain during deep squats, pain on stairs, single-leg balance, bridge hold, step-up tolerance, and movement limitations. These are not formal clinical tests, but they approximate the kind of contextual information needed before deciding whether a workout movement is likely to be safe.

After onboarding, the user can modify an existing workout through two paths. The first path accepts a YouTube link. The backend uses a Gemini-based flow to build `video_information`, including title, duration, description, and chronological chapters or segments. The second path accepts pasted workout text and converts it into a video-information-shaped object so the same adaptation pipeline can be reused. This design makes YouTube analysis the primary user story while keeping text input as a fallback when video extraction is unavailable or unnecessary.

The injury adaptation layer uses structured prompts and schema-constrained JSON output. The system prompt instructs the model to review workout movements against the user's injury profile, prioritize safety over performance goals, avoid inventing information, and return one row per segment with exactly three fields: original movement, modified alternative, and risk flag. Risk flags are constrained to Low, Medium, or High. If risk is Medium or High, the model must provide a safer substitute or regression; if risk is Low, it can recommend keeping the movement as is. The phase-two prompt is stricter for segmented workouts: it tells the model not to re-segment the video, to preserve the order of chapters, and to produce one output row per input segment.

The output is shown as a structured adaptation result. For each movement or segment, the user sees the original exercise, the risk label, and the safer alternative. When video chapters are available, time ranges are attached so the user can identify where in the workout the movement appears. This directly supports the original value proposition: preserve the user's preferred workout content while making injury-aware modifications.

### Evaluation Design

The evaluation had four parts. First, the team reviewed literature on rehabilitation, AI exercise recommendation, injury prevention, and workout video support. This grounded the system around mid-stage rehabilitation, criteria-based progression, symptom-guided load management, and the need for expert validation. Second, the team performed AI-tool validation across tools including ChatGPT, Gemini, DeepSeek, and an InjuryMap analysis. These tests examined whether existing tools could handle typical cases, edge cases, and failure cases involving shoulder pain and video-based workout adaptation.

Third, the team conducted interviews with medical and user stakeholders. A senior resident emphasized that AI-assisted guidance may be acceptable if it includes safety precautions, disclaimers, and physiotherapy-style suggestions rather than intense workouts during recovery. A gym user with shoulder injury experience highlighted the burden of manually deciding which exercises to skip or modify. A musculoskeletal physiotherapist at Vita Health Group UK emphasized the importance of functional screening, adherence, load management, mid-stage rehab, red flags, progress tracking, and human oversight when progress is abnormal. A football enthusiast recovering from knee injury described the difficulty of returning to running, cutting, jumping, and lower-body training without overloading the joint.

Fourth, the team collected 21 structured persona responses in a CSV evaluation. The instrument included ten 5-point Likert items and four open-ended questions. Quantitative items measured whether users understood the tool as support rather than medical replacement, whether it was clear when to pause and consult a professional, workflow ease, confusion about the app's role, injury assessment relevance, appropriateness of risk labels and substitutions, explanation quality, need for outside help, reduced effort, and trust for safer mid-stage recovery workouts. Open-ended questions asked for the most helpful part, least reliable or riskiest part, what should be improved first, and a short feedback blurb. The evaluation mixed personas such as beginner lifters, experienced lifters, cardio-focused users, post-ACL recovery users, dancers, runners, a physiotherapist, and physicians. The goal was not to claim clinical effectiveness, but to understand usability, perceived safety, and trust in the adaptation concept.

## Results, Analysis, and Discussion

### Quantitative Results

The persona evaluation produced encouraging quantitative results. Across 21 responses, the strongest item was "Understood support tool, not medical replacement" with a mean of 4.57 out of 5, standard deviation 0.60, and 95.2% top-2-box agreement. This matters because the product sits in a health-adjacent domain. If users misunderstand the tool as medical authority, the risk profile changes significantly. The result suggests that the current framing successfully communicates AdaptFit as a support tool.

The workflow also performed strongly. "Workflow easy to follow" had a mean of 4.33, standard deviation 0.58, and 95.2% top-2-box agreement. "Injury assessment questions felt relevant" had a mean of 4.43, standard deviation 0.75, and 85.7% top-2-box agreement. This indicates that users understood the flow from injury context to workout modification and recognized the value of movement-specific assessment. The system's design goal was not only to generate outputs, but to collect enough context first. These scores show that users did not perceive that assessment step as unnecessary friction.

The app also appeared to reduce effort. The item "Reduced effort figuring out skips/modifications" received a mean of 4.29, standard deviation 0.78, and 90.5% top-2-box agreement. This supports the main use case: users often do not know whether to skip, substitute, reduce range of motion, or reduce load. AdaptFit helps by translating that decision into a structured set of risk labels and alternatives.

Trust-related scores were positive but lower. "Trust for safer mid-stage recovery workouts with caution" had a mean of 3.81, standard deviation 0.75, and 71.4% top-2-box agreement. "Risk labels/substitutions seemed appropriate" had a mean of 3.95, and "Enough explanation for risky exercise + safer alternative" had a mean of 4.05. These scores suggest that users see value in the system, but their trust is conditional. The interface is understandable, but injury-related recommendations require stronger reasoning, transparent boundaries, and more specific action guidance.

Two reverse or caution-oriented items help interpret the results. "Confused about planning vs coaching vs logging" had a mean of 2.14, where lower is better, and only 4.8% top-2-box agreement. This suggests that most users were not very confused about the product's role. "Would need substantial help from trainer/clinician" had a mean of 2.43, with 9.5% top-2-box agreement. Users generally did not feel the app was unusable without outside support, though the qualitative findings clarify that professional escalation is still important in higher-risk scenarios.

### Qualitative Results

The open-ended responses show three major strengths: injury assessment, step-by-step workflow, and safer substitutions. The CP4 analysis found that about 57.1% of responses mentioned assessment, readiness, pain-specific questions, recovery stage, or functional screening as helpful. Users appreciated that the app did not merely ask "Where is your injury?" but asked how pain appears during specific movements. This distinction is important because two users with the same body part affected may need very different modifications.

About 47.6% of responses mentioned the workflow, speed, ease of use, paste/upload ability, or structured sequence. This shows that AdaptFit is valuable not only because of the final AI output, but also because it organizes a confusing decision process. The product reduces the cognitive effort of moving from "I have discomfort" to "Here is how I should modify this workout today."

About 38.1% of responses mentioned safer alternatives or substitutions. Users liked that the app did not simply tell them to stop exercising. This aligns with the project's original problem statement: many recovering users want to maintain activity, not abandon training. The best experience is therefore not a blanket prohibition, but a safer substitute that preserves the workout's intent when possible.

The most important concern was explanation. About 47.6% of responses mentioned risk labels, explanation quality, score logic, transparency, or wanting to understand why something was flagged. This indicates that a Low, Medium, or High label is not enough by itself. Users want to know the mechanism: Is the issue impact, deep flexion, rotation, overhead loading, instability, fatigue, or load? They also want to know the action: Should they skip the movement, reduce range, reduce weight, slow tempo, or consult someone?

Another concern was escalation for higher-risk cases. About 23.8% of responses mentioned clinician support, red flags, severe symptoms, post-surgical recovery, or uncertainty. This matches the interviews. The physiotherapist specifically warned that early-stage rehab and back-pain-related plans are risky if handled generically. The physician interview similarly emphasized disclaimers and physiotherapy-oriented movements. These findings suggest that future versions should use stricter stop rules when symptoms are severe, worsening, recent, neurological, unstable, or post-surgical.

Sport-specific context was a third theme. About 28.6% of responses mentioned running, hiking, tennis, dance, football, jumping, cutting, repeated footwork, or other activity-specific needs. This reveals a limitation in the current design: AdaptFit works best for general workout modification, but athletes and dancers need recommendations that account for movement patterns, impact, volume, and return-to-sport demands. A knee-safe gym substitution may not answer whether a football player is ready for cutting drills or a Kathak dancer is ready for repeated footwork.

### Discussion

The combined findings show a clear pattern: AdaptFit is promising as a decision-support layer, not as a standalone clinical authority. Users understand the product, find the assessment relevant, and value safer substitutions. However, injury-aware trust depends on more than usability. It depends on explainability, conservative boundaries, and activity-specific personalization.

This distinction explains why the usability scores were higher than the trust score. A user can understand the interface and still hesitate to follow the recommendation. In ordinary fitness apps, usability may be the primary barrier. In injury-aware systems, perceived safety is equally important. Trust must be earned by showing the relationship between the user's reported symptoms, the movement being analyzed, the risk label, and the recommended alternative.

The results also support the project's original gap analysis. Existing LLMs can often generate reasonable exercise suggestions for typical cases, but the AI-tool validation showed several problems: models may provide workouts without enough clarification, continue generating plans even after recognizing high pain, or fail to access and adapt the actual workout video. Existing rehabilitation tools may screen injuries, but they tend to offer fixed programs rather than dynamic modification of user-selected workouts. AdaptFit's contribution is the integration of injury assessment with adaptation of existing content.

The evaluation should be interpreted carefully. The 21-response dataset is useful for formative design feedback, but it is not clinical validation. The personas and stakeholder feedback indicate whether users perceive the tool as understandable, helpful, and appropriately cautious. They do not prove that the substitutions reduce injury risk or improve outcomes. A stronger evaluation would include expert review of generated substitutions, comparison against physiotherapist-created modifications, and longitudinal testing of user adherence, pain response, and progression.

## Limitations, Risks, and Ethical Considerations

The first limitation is sample size and study design. The evaluation used 21 structured persona responses and interviews rather than a controlled clinical study. The results are appropriate for product validation, not medical efficacy. The personas represent a range of user types, but they cannot capture the full diversity of injury histories, body types, access to care, or training contexts.

The second limitation is self-reported input quality. AdaptFit depends on user-entered pain levels, injury context, limitations, and functional screening. Users may underreport pain, misunderstand injury names, skip important details, or misjudge their recovery stage. A recommendation based on incomplete input may be overly permissive or overly cautious. Future designs should include clearer plain-language injury descriptions, examples, and red-flag questions.

The third limitation is workout understanding. The current system can process YouTube metadata, segments, and pasted workout text, but it does not perform reliable real-time form analysis or biomechanical assessment. A video segment labeled "squat" does not reveal the user's depth, load, speed, fatigue, or compensations. It also does not know whether the user will perform the substitute correctly. Therefore, AdaptFit should avoid implying that it can verify form or diagnose movement quality.

The fourth limitation is the use of LLMs. LLMs can produce plausible but unsafe recommendations if prompts are underspecified or if the user's case is outside the intended scope. The current prompt constrains output to structured JSON and emphasizes safety, but model behavior still requires validation. Ethical deployment would require expert-reviewed rule libraries, model output monitoring, and fallback behavior when the model is uncertain.

Key risks include overtrust, delayed professional care, unsafe substitutions, and privacy concerns. Overtrust may occur if users treat AdaptFit as medical advice. Delayed care may occur if a user with severe or worsening symptoms follows modifications instead of seeking help. Unsafe substitutions may occur if the model misunderstands the injury, movement, or sport context. Privacy concerns arise because injury-related information is sensitive even when it is not a formal medical record.

The project's ethical safeguards are therefore central to its design. AdaptFit should consistently present itself as a support tool, not a clinician. It should use conservative recommendations when pain is high, symptoms are recent, or information is missing. It should include escalation prompts for red flags such as severe pain, swelling, instability, numbness, post-surgical restrictions, or worsening symptoms. It should minimize stored data, avoid unnecessary personally identifiable information, and make clear how injury inputs are used.

## Conclusion and Future Work

AdaptFit AI demonstrates that injury-aware workout adaptation is a meaningful and feasible direction for GenAI in fitness. The project addresses a real gap between rehabilitation tools and consumer fitness content: people want to remain active, but they need help modifying existing workouts safely. The prototype collects injury context, converts workout input into structured segments, uses LLM-assisted risk analysis, and returns safer alternatives with risk labels.

The evaluation suggests that users understand the system's purpose, find the workflow easy to follow, and value the assessment and substitution features. Quantitative scores were strongest for safety framing, workflow, assessment relevance, and reduced effort. Qualitative feedback showed that users especially appreciated movement-specific questions and practical substitutions. At the same time, trust remains conditional. Users want clearer explanations, stronger risk-to-action guidance, clinician escalation boundaries, and more sport-specific adaptation.

Future work should focus on five priorities. First, build a more explicit rule layer that connects injury type, recovery stage, pain score, and movement category to recommended actions. Second, expand explanations so every risk label includes a clear rationale and practical next step. Third, add red-flag escalation logic that stops workout adaptation when the case is outside the system's scope. Fourth, support activity-specific modules for running, football, dance, hiking, and tennis. Fifth, evaluate recommendations with clinical experts and real users over time, measuring not only usability but also adherence, pain response, and safety.

The long-term vision is not to replace physiotherapists or trainers, but to give users a safer bridge between professional guidance and the everyday workouts they actually follow. AdaptFit's strongest opportunity is mid-stage recovery: a phase where users are often cleared to move, but still need structured support to avoid returning to normal too quickly.

## References

Buckthorpe, M., Della Villa, F., Della Villa, S., & Roi, G. S. (2023). Recommendations for rehabilitation after anterior cruciate ligament reconstruction. *British Journal of Sports Medicine, 57*(5), 259-270. https://www.aspetar.com/en/professionals/aspetar-clinical-guidelines/recommendations-on-rehabilitation-after-aclr

Cakmak, M. C., & Agarwal, N. (2025). *A keyframe-based approach for auditing bias in YouTube Shorts recommendations*. arXiv. https://arxiv.org/abs/2509.02543

Canzone, A., Belmonte, G., Patti, A., Vicari, D. S. S., Rapisarda, F., Giustino, V., Drid, P., & Bianco, A. (2025). The multiple uses of artificial intelligence in exercise programs: A narrative review. *Frontiers in Public Health, 13*, 1510801. https://doi.org/10.3389/fpubh.2025.1510801

Kolasinski, S. L., et al. (2020). 2019 American College of Rheumatology guideline for the management of osteoarthritis of the hand, hip, and knee. *Arthritis Care & Research, 72*(2), 149-162. https://pubmed.ncbi.nlm.nih.gov/31908163/

Lai, X., Chen, J., Lai, Y., Huang, S., Cai, Y., Sun, Z., Wang, X., Pan, K., Gao, Q., & Huang, C. (2025). Using large language models to enhance exercise recommendations and physical activity in clinical and healthy populations: Scoping review. *JMIR Medical Informatics, 13*, e59309. https://doi.org/10.2196/59309

Park, K. H., & Song, M. R. (2017). Development of a web exercise video for patients with shoulder problems. *Computers, Informatics, Nursing, 35*(5), 255-261.

Shin, D., Hsieh, G., & Kim, Y. (2025). PlanFitting: Personalized exercise planning with large language model-driven conversational agent. *Proceedings of CUI 2025*. https://doi.org/10.1145/3719160.3736607

van der Wal, R. J. P., et al. (2022). Rehabilitation after meniscal repair: A systematic review and evidence-based protocol. *Journal of Experimental Orthopaedics, 9*, 74. https://doi.org/10.1186/s40634-022-00521-8

Willy, R. W., et al. (2019). Patellofemoral pain clinical practice guideline. *Journal of Orthopaedic & Sports Physical Therapy, 49*(9), CPG1-CPG95. https://pubmed.ncbi.nlm.nih.gov/31475628/

Wu, J., Fang, Z., Lyu, P., Zhang, C., Chen, F., Lu, G., & Pei, W. (2025). *WeCromCL: Weakly supervised cross-modality contrastive learning for transcription-only supervised text spotting*. arXiv. https://arxiv.org/abs/2407.19507

Zheng, G., Zeng, S., Li, T., Guo, L., & Li, L. (2025). The effects of training intervention on the prevention of knee joint injuries: A systematic review and meta-analysis. *Frontiers in Physiology, 16*, 1455055. https://doi.org/10.3389/fphys.2025.1455055

## Appendices

### Appendix A. Study Materials

The structured evaluation used the following ten 5-point Likert items:

1. Understood AdaptFit as a support tool, not a medical replacement.
2. Clear when to pause and consult a professional.
3. Workflow easy to follow.
4. Confused about planning vs coaching vs logging.
5. Injury assessment questions felt relevant.
6. Risk labels and substitutions seemed appropriate.
7. Enough explanation for risky exercise and safer alternative.
8. Would need substantial help from trainer or clinician.
9. Reduced effort figuring out skips and modifications.
10. Trust for safer mid-stage recovery workouts with caution.

The open-ended questions asked participants to identify the single most helpful part, the least reliable or riskiest part, what should be improved first, and a short user-written feedback blurb.

### Appendix B. Prompt and System Materials

The adaptation prompt required the model to compare workout movements against the user's injury profile and return structured JSON rows. Safety rules included: do not provide diagnosis, base risk on injury status and pain triggers, prioritize safety over performance goals, state assumptions when information is missing, and return Low, Medium, or High risk flags with safer substitutes for Medium and High movements. The phase-two prompt required one row per workout segment in chronological order.

### Appendix C. Prototype Artifacts

Key repository artifacts include:

- `README.md`: project problem statement, users, competitive landscape, and value proposition.
- `DESIGN_SPEC.md`: user journeys, task flows, screens, system requirements, and success criteria.
- `deploy-app/README.md`: deployable MVP architecture and page structure.
- `validation/interviews.md`: medical professional, physiotherapist, gym user, and athlete interviews.
- `validation/AI-tool-validations.md`: AI tool and market validation notes.
- `docs/AdaptFit_AI - AdaptFit Persona Responses.csv`: structured evaluation data.
- `docs/sus_lite_5_mean_sd.png` and `docs/sus_lite_5_mean_sd_n20.png`: slide-ready quantitative visuals.

### Appendix D. Screenshots and Visual Evidence

The repository includes generated visual assets and prototype screens for onboarding, injury assessment, workout selection, readiness results, and modified workout outputs. The final slide visuals summarize SUS-Lite-style mean and standard deviation scores for five positive usability and safety items.
