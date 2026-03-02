from sentence_transformers import SentenceTransformer
from ollama import Client
import chromadb, json, re, os
from collections import defaultdict
from math import inf
import pandas as pd

# Embedding + DB + LLM clients
embedder = SentenceTransformer('all-MiniLM-L6-v2')
# Use absolute path to database (backend/rice_courses_db)
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'rice_courses_db'))
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection("rice_courses")
ollama = Client(host="http://localhost:11434")

EXPANSION_SYSTEM = """\
You are helping improve a Rice University course search system powered by a vector database.
Your job is to convert a student's messy natural-language request into structured search hints.

You MUST return a SINGLE, VALID, MINIFIED JSON OBJECT with EXACTLY these keys:
- semantic_query        (string)
- expanded_queries      (array of strings)
- must_have_keywords    (array of strings)
- nice_to_have_keywords (array of strings)
- never_have_keywords   (array of strings)
- facet_filters         (object)

All keys MUST be present, even if some arrays are empty or facet_filters is {}.

STRUCTURE:

1) semantic_query
- Short paraphrase of the user's intent (5–20 words, no quotes around the whole string).
- Example: "first-year writing seminars focused on academic writing skills"

2) expanded_queries
- 3–6 alternate phrasings of the request.
- Natural language, 5–20 words each.
- Use different vocabulary and phrasing to cover plausible catalog-style descriptions.
- Do NOT simply repeat semantic_query with tiny changes.

3) must_have_keywords
- 0–5 highly important keywords or short phrases.
- Include:
  - Any course codes explicitly mentioned (e.g. "COMP 140", "FWIS 100").
  - Strongly required concepts (e.g. "writing intensive", "seminar", "machine learning").
  - For FWIS / first-year writing seminars, ALWAYS include "FWIS".
- Do NOT include generic words like "course", "class", "Rice", "university".
- If the user is vague and has no clear constraints, this array may be empty [].

4) nice_to_have_keywords
- 0–10 helpful but non-essential keywords or short phrases.
- Can include topics, skills, or contextual hints:
  - e.g. "academic writing", "composition", "project-based", "statistics", "data analysis".
- Avoid repeating must_have_keywords unless very natural.

5) never_have_keywords
- 0–10 keywords or phrases to exclude.
- ONLY add items when the user explicitly negates something with words like:
  "not", "no", "except", "without", "but not", "avoid", "exclude".
- Example: user says "not linear algebra" → include "linear algebra" here.
- Lowercase phrases, no punctuation.
- If there is no explicit negation, return an empty array [].

6) facet_filters
An OBJECT (possibly empty: {}) containing zero or more of these keys:
  {
    "distribution_group": string,
    "diversity_credit": boolean,
    "department": string,
    "level": string,
    "program": string
  }

GENERAL RULES FOR facet_filters:
- If you are unsure about a facet, OMIT that facet.
- Do NOT invent departments, levels, or programs not clearly implied by the query.

RICE-SPECIFIC LOGIC:

distribution_group:
- Only set when the user clearly requests a specific Distribution Group.
- Allowed values: "Distribution Group I", "Distribution Group II", "Distribution Group III".
- If the user is asking about FWIS (First-Year Writing Intensive Seminar),
  DO NOT set a distribution_group facet, because FWIS is a separate requirement.

diversity_credit:
- Set to true ONLY if the user clearly wants a diversity course (e.g. "counts for diversity credit").
- Set to false ONLY if the user clearly wants courses without diversity credit.
- Otherwise, omit this field.

department:
- Use catalog-style department names when clearly implied, such as:
  "Computer Science", "Mathematics", "Statistics", "Economics",
  "English and Creative Writing", etc.
- IMPORTANT: For FWIS / first-year writing seminars:
  - FWIS courses are identified by course codes like "FWIS 100", "FWIS 126", etc.
  - DO NOT set a special department for FWIS.
  - Instead, ensure "FWIS" appears in must_have_keywords.
- If the department is not clear, omit this field.

level:
- Use a SINGLE value like "100", "200", "300", or "400" only when the user clearly specifies a level:
  - "100-level" → "100"
  - "introductory" MAY imply "100", but only use it when very clear.
- NEVER output ranges like "100/200" or "200/300".
- If level is not clearly specified, omit this field.

program:
- Use for high-level tracks (e.g., "Computer Science", "Data Science", "Neuroscience") when clearly specified.
- If program/major context is not important or not clearly stated, omit this field.

NEGATION EXAMPLES (DO NOT OUTPUT THESE EXAMPLES, JUST FOLLOW THEM):

- User: "I need a Distribution Group III science class without diversity credit."
  facet_filters might be:
    { "distribution_group": "Distribution Group III", "diversity_credit": false }
  never_have_keywords: []  (no explicit content to exclude by name)

- User: "Give me 100-level computer science courses, not linear algebra."
  facet_filters might be:
    { "department": "Computer Science", "level": "100" }
  never_have_keywords might include:
    ["linear algebra"]

- User: "Find me first-year writing intensive seminar classes."
  semantic_query should mention first-year writing seminars.
  must_have_keywords might include:
    ["FWIS", "writing", "seminar", "first-year"]
  facet_filters should usually be {} unless the user adds extra constraints (e.g. a distribution group).

FINAL REQUIREMENT:
- Respond with ONLY the JSON object. No extra text, no markdown, no comments.
"""

def expand_query_with_llm(raw_query: str) -> dict:
    user_prompt = f"""\
Raw user query:
{raw_query}

Consider Rice University context and common catalog language (e.g., "Distribution Group I/II/III", "Diversity Credit").
Infer relevant synonyms 
"""
    response = ollama.generate(
        # use a REAL model (pick one):
        # model="llama3:latest",
        model="gemma3:1b",
        prompt=EXPANSION_SYSTEM + "\n" + user_prompt,
        options={"temperature": 0.2}
    )
    text = response["response"].strip()
    json_str = re.search(r'\{.*\}', text, flags=re.S).group(0)
    return json.loads(json_str)

def _encode(q: str):
    return embedder.encode([q], normalize_embeddings=True)[0]

def rrf_fuse(result_lists, k=50, k_rrf=60):
    ranks = defaultdict(lambda: inf)
    for results in result_lists:
        for rank, (rid, _score, meta, doc) in enumerate(results, start=1):
            ranks[(rid, doc)] = min(ranks[(rid, doc)], rank)

    fused = defaultdict(float)
    payload = {}
    for results in result_lists:
        for rank, (rid, _score, meta, doc) in enumerate(results, start=1):
            key = (rid, doc)
            fused[key] += 1.0 / (k_rrf + rank)
            payload[key] = (meta, _score)

    ordered = sorted(fused.items(), key=lambda x: x[1], reverse=True)
    final = []
    for (rid, doc), fused_score in ordered[:k]:
        meta, orig_score = payload[(rid, doc)]
        final.append({
            "id": rid,
            "doc": doc,
            "meta": meta,
            "fused_score": fused_score,
            "orig_score": orig_score
        })
    return final

def query_chroma_multi(collection, queries, where=None, n_results=20):
    result_lists = []
    for q in queries:
        emb = _encode(q)
        res = collection.query(
            query_embeddings=[emb],
            n_results=n_results,
            where=where   # we'll keep this None for FWIS search
        )
        ids = res["ids"][0]
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        dists = res["distances"][0]
        out = list(zip(ids, dists, metas, docs))
        result_lists.append(out)
    fused = rrf_fuse(result_lists, k=50)
    return fused

def _exclude_never_have(results, never_have_keywords):
    if not never_have_keywords:
        return results

    forbidden = [kw.strip().lower() for kw in never_have_keywords if kw.strip()]
    if not forbidden:
        return results

    def is_forbidden_hit(r):
        meta = r.get("meta") or {}
        text_parts = [
            meta.get("title", ""),
            meta.get("course", ""),
            meta.get("description", ""),
            r.get("doc") or "",
        ]
        text = " ".join(text_parts).lower()
        return any(f in text for f in forbidden)

    return [r for r in results if not is_forbidden_hit(r)]

def expanded_retrieve(raw_query: str, base_where=None, top_k=25):
    exp = expand_query_with_llm(raw_query)

    # Build candidate queries
    candidate_queries = [raw_query]
    if exp.get("semantic_query"):
        candidate_queries.append(exp["semantic_query"])
    if exp.get("expanded_queries"):
        candidate_queries.extend(exp["expanded_queries"])

    facets = exp.get("facet_filters") or {}
    

    # For now, no metadata where-filtering (you can add it back later)
    if base_where is not None:
        where = base_where
    else:
        where = None

    fused = query_chroma_multi(collection, candidate_queries, where=where, n_results=50)

    # Apply optional "never-have" keyword post-filter
    never_have = exp.get("never_have_keywords") or []
    fused = _exclude_never_have(fused, never_have)

    # 🔎 Detect if this query is really about FWIS/first-year writing
    def wants_fwis(expansion: dict) -> bool:
        # Check must_have_keywords and the raw query/semantic query
        kws = [kw.lower() for kw in expansion.get("must_have_keywords", [])]
        text_blob = " ".join([
            raw_query.lower(),
            expansion.get("semantic_query", "").lower()
        ])
        return (
            "fwis" in kws or
            "fwis" in text_blob or
            "first-year writing" in text_blob or
            "first year writing" in text_blob
        )

    if wants_fwis(exp):
        fwis_only = []
        for r in fused:
            meta = r.get("meta") or {}
            course_code = (meta.get("course") or "").upper()
            if "FWIS" in course_code:
                fwis_only.append(r)

        # If we found FWIS matches, use them; otherwise, fall back to original list
        if fwis_only:
            fused = fwis_only
    
    
    return exp, fused[:top_k]


