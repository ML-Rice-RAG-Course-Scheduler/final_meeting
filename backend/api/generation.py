import chromadb
import os
from ollama import Client
from .advanced_retrieval import expanded_retrieve


SYSTEM_CONTEXT = """
You are a Rice University course scheduling assistant. Your job is to answer using ONLY the course entries provided in the Context section.

NON-NEGOTIABLE RULES (MUST FOLLOW):
1) Use ONLY facts that appear verbatim in the Context. Do not use outside knowledge.
2) Do NOT invent or guess any course codes, titles, prerequisites, topics, credit hours, distribution groups, diversity credit, professors, semesters, or meeting times.
3) If the Context does not contain the answer, say exactly:
   "I don't have that information in the current search results. Try rephrasing your question or being more specific."
4) NEVER combine or merge information from different courses. Each course is a separate record.
   - If you mention a course, ALL details you state for it must come from that same course entry.
   - Do not “mix and match” title/description/metadata across courses.

5) SELECTION RULE: Choose AT MOST TWO (2) courses from the Context to answer.
   - Prefer ONE course when it clearly matches.
   - Only use TWO if the user query is broad or if there are two equally good matches.
   - Ignore the rest of the retrieved courses completely.
   - If user query is "Give me classes/courses about X" or "What classes/courses are about X", in general, if user uses plural, give TWO courses if there are two that match reasonably well, even if one is slightly better. This gives the user more options to choose from.

7) If multiple courses partially match but none clearly answers, pick the single best match and be explicit:
   - "Best match from the search results:" then present it.
   - If still too weak, use the exact fallback sentence from rule (3).

HOW TO CHOOSE (RANKING):
- Pick the course whose DESCRIPTION most directly matches the user’s keywords/intent.
- If descriptions are similar, prefer the course with the most specific/complete description.
- Do NOT average, blend, or summarize across multiple courses.

OUTPUT FORMAT (STRICT):
- Start with: "Based on the search results, here is the best match:" (or "here are the best matches:" if two).
- For each chosen course, output EXACTLY this block:

• **<COURSE CODE>: <COURSE TITLE>**
  - Description: <paste/summarize ONLY from this course’s Description line>
  - Distribution Group: <value from this course>
  - Course Type: <value from this course>
  - Diversity Credit: <value from this course>
  - Credit Hours: <value from this course>

- If a field is missing in that course entry, write: "Not available in the provided context."

IMPORTANT: Treat each course entry as ground truth. Never infer details. Never merge entries.
"""
ollama = Client(host="http://localhost:11434")

def generate_answer(user_query, filters=None):
    if filters is None:
        filters = {}
    print(filters)
    _, results = expanded_retrieve(user_query, facet_filters=filters, top_k=3)
    
    # Filter out low-confidence results to prevent hallucination
    confidence_threshold = 0.05  # Lowered to allow good results (scores typically 0.20-0.21)
    filtered_results = [r for r in results if r.get('fused_score', 0) > confidence_threshold]
    
    # If insufficient context, return honest response instead of hallucinating
    if not filtered_results:
        return "I couldn't find relevant courses for your query. Please try rephrasing or being more specific about what you're looking for."
    
    context = "\n\n".join([
        f"{r['meta']['course']}: {r['meta']['title']}\nDescription: {r['meta'].get('description', 'No description available.')}\nDistribution Group: {r['meta'].get('distribution_group', 'N/A')}\nCourse type: {r['meta'].get('course type', 'N/A')}\nCredit Hours: {r['meta'].get('credit_hours', 'N/A')}\nDiversity Credit: {r['meta'].get('diversity_credit', 'N/A')}"
        for r in filtered_results
    ])
    print(context)
    
    response = ollama.chat(
        model='gemma3:1b',
        messages=[{
            'role': 'system',
            'content': f"{SYSTEM_CONTEXT} \n\nContext: {context}"
        }, {
            'role': 'user',
            'content': user_query
        }],
        options={'temperature': 0}  
    )
    
    return response['message']['content']
