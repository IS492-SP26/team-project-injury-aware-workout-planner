# Paper 1
## Full citation + link
Park, K. H., & Song, M. R. (2017). Development of a Web Exercise Video for Patients With Shoulder Problems. _Computers, Informatics, Nursing_, 35(5), 255–261.  
Available at: http://www.cnubh.com/news/qna.html?code=168987
## Summary
This study developed a web-based shoulder rehabilitation exercise video to support continuous home exercise for patients with shoulder joint disease. The authors used the ADDIE instructional design model, including analysis, design, development, implementation, and evaluation stages. Patient interviews revealed high awareness of exercise necessity but low actual adherence, mainly due to forgetting instructions and lack of time. The final video included stretching and strengthening exercises such as pendulum movements, rotation exercises, wall push-ups, and rowing, designed for home environments. Expert validation and user surveys confirmed content clarity and usefulness, and the video was deployed on both a hospital website and YouTube.
## Insights
1. **Evaluation metrics were clinical, not engagement-based:** They measured pain, ROM, and strength. This is important if your tool wants clinical credibility rather than being “just another fitness app.”
## Limitations
1. Limited sample size and single hospital setting. Results may not generalize.
2. No long-term outcome validation. They suggest future monitoring of pain and ROM but did not provide longitudinal data.
## Idea inspires for our project
Integrate a stage-based rehab evaluation system in the product that evaluates injury stage with structured metrics like pain level, ROM and evaluate strength improvement over time. This can support users in rehab self-measurement.

# Paper 2
## Full citation + link
Cakmak, M. C., & Agarwal, N. (2025). A Keyframe-Based Approach for Auditing Bias in YouTube Shorts Recommendations.
Available at: https://arxiv.org/abs/2509.02543
## Summary
This paper proposed a keyframe-based method to audit algorithmic bias in YouTube Shorts recommendations. Instead of analyzing full videos, the authors extract perceptually salient keyframes using PRISM and generate captions with LLaMA-3.2-Vision-Instruct. Both keyframes and captions are embedded into a shared semantic space using CLIP and visualized with UMAP to detect recommendation drift. The study compares politically sensitive content (South China Sea) with general categories and finds significantly larger divergence and clustering shifts in sensitive topics. Results show that keyframes are an efficient and interpretable proxy for understanding recommendation bias.
## Insights
1. **Experiences in extracting keyframes:** We can extract keyframes to make video semantics, useful in analyzing workout movements in Youtube videos.
2. **Multimodal info improves interpretability:** Combining visual frames and generated captions provided stronger clustering signals.
## Limitations
1. Only two domains were tested. Generalizability to other topics is unclear.
2. Keyframes may miss subtle biomechanical cues important for exercise safety. Visual salience does not equal medical relevance.
## Idea inspires for our project
We can use a keyframe-based movement detection method to divide the video into segments according to different workflow movements. Extract keyframes, generate/extract movement captions, embed them, and classify exercise type.
