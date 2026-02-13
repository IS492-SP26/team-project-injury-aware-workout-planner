## Paper 1

Wu, J., Fang, Z., Lyu, P., Zhang, C., Chen, F., Lu, G., & Pei, W. (2025).  
WeCromCL: Weakly Supervised Cross-Modality Contrastive Learning for Transcription-only Supervised Text Spotting.  
arXiv.  
https://arxiv.org/abs/2407.19507

This paper studies how to detect text inside images when only the text transcription is available, but not the exact location of the text in the image. Normally, text detection needs bounding boxes, which are expensive to label. The authors propose a method called WeCromCL that learns to match text and image regions without location labels. Instead of matching the whole image with the whole text, it matches characters with specific image areas. These matched areas are then used as pseudo labels to train a text detection system. Their method performs well on several benchmarks.

1. Even without exact labels, models can still learn useful location information through smart training design.
2. Matching small pieces such as characters can be more effective than matching entire images and text.
3. Pseudo labels can be a practical way to reduce annotation cost while still training strong systems.


1. The method may struggle if the text in the image is blurry or very small.
2. It still depends on good feature learning, so weak image representations could reduce accuracy.

We could use a similar weak supervision idea by matching exercise names from transcripts to likely video segments, even if we do not have exact time labels at first.


## Paper 2

Shin, D., Hsieh, G., & Kim, Y. (2025).  
PlanFitting: Personalized Exercise Planning with Large Language Model-driven Conversational Agent.  
Proceedings of CUI 2025.  
https://doi.org/10.1145/3719160.3736607

This paper introduces PlanFitting, a conversational agent that helps users create weekly exercise plans. The system uses an LLM to ask questions about goals, schedule, and constraints. It then generates exercise plans that follow official exercise guidelines. The researchers tested the system with users and experts. They found that the plans were generally useful and aligned with exercise principles. However, experts noted that some combinations of exercises could be improved.


1. Users need guidance when creating exercise plans, not just tracking tools.
2. Iteration and feedback are very important in exercise planning.
3. LLMs can help collect user constraints in a natural way through conversation.



1. The system still depends on the quality of prompts and guideline integration.
2. LLMs can generate plausible but not fully accurate plans if not carefully grounded.

We should structure our questionnaire carefully so the model clearly understands injury type, recovery stage, and pain level before giving exercise substitutes.

## Paper 3


Lai, X., Chen, J., Lai, Y., Huang, S., Cai, Y., Sun, Z., Wang, X., Pan, K., Gao, Q., & Huang, C. (2025).  
Using Large Language Models to Enhance Exercise Recommendations and Physical Activity in Clinical and Healthy Populations: Scoping Review.  
JMIR Medical Informatics.  
https://doi.org/10.2196/59309



This paper reviews how large language models are being used in exercise recommendations and physical activity guidance. The authors analyzed 11 studies that used LLMs in clinical and healthy settings. They found that LLMs can generate personalized exercise suggestions and save time for professionals. However, the review also shows that LLMs are not ready to replace experts. Validation and safety checks are still necessary. The paper highlights the need for more testing before wide clinical use.


1. LLMs are promising tools for personalization in exercise guidance.
2. Expert validation is essential before using LLM outputs in health settings.
3. There is still limited large-scale evidence on safety and reliability.


1. Most studies were small and not large clinical trials.
2. There is a risk of incorrect or unsafe recommendations if models are not validated.

We must clearly position our system as a support tool, not a medical replacement, and design evaluation steps to test safety and accuracy.
