import { useState } from "react";
import './App.css'

const DISTRIBUTIONS = ["All", "Distribution Group I", "Distribution Group II", "Distribution Group III"];
const COURSE_TYPES = ["All", "Lecture", "Seminar", "Research", "Laboratory", "Internship/Practicum", "Independent Study"];

export default function CourseSearch() {
  const [distribution, setDistribution] = useState("All");
  const [course_type, setCourseType] = useState("All");
  // when true, only include courses with diversity credit; null means "no preference"
  const [diversityCredit, setDiversityCredit] = useState(null);
  const [textQuery, setTextQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    // send the natural-language query to the backend API for retrieval/generation
    if (!textQuery) return;
    setLoading(true);
    setError(null);
    setAnswer("");
    try {
      const filters = {};
      if (distribution !== "All") filters.distribution_group = distribution;
      if (course_type !== "All") filters["course type"] = course_type;
      if (diversityCredit !== null) filters.diversity_credit = diversityCredit;
      
      const res = await fetch('/api/ask/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: textQuery, name: 'Frontend', filters }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Server error');
      }
      setAnswer(data.answer);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-stone-100 flex justify-center items-start p-10 font-mono">
      <div className="w-full max-w-xl flex flex-col gap-5">

        {/* Title */}
        <h1 className="text-3xl font-serif tracking-tight text-stone-900 border-b-2 border-stone-900 pb-2">
          Course Search
        </h1>

        {/* Filters */}
        <div className="flex flex-col gap-3">
          <h2 className="text-xl font-serif text-stone-900">Filter :</h2>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-xs uppercase tracking-widest text-stone-400">Distribution</label>
              <select
                className="border-2 border-stone-900 rounded px-3 py-2 text-sm bg-white text-stone-900 font-mono focus:outline-none focus:ring-2 focus:ring-stone-900"
                value={distribution}
                onChange={(e) => setDistribution(e.target.value)}
              >
                {DISTRIBUTIONS.map((d) => <option key={d}>{d}</option>)}
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs uppercase tracking-widest text-stone-400">Course Type</label>
              <select
                className="border-2 border-stone-900 rounded px-3 py-2 text-sm bg-white text-stone-900 font-mono focus:outline-none focus:ring-2 focus:ring-stone-900"
                value={course_type}
                onChange={(e) => setCourseType(e.target.value)}
              >
                {COURSE_TYPES.map((d) => <option key={d}>{d}</option>)}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="diversityCredit"
                checked={diversityCredit === true}
                onChange={(e) => setDiversityCredit(e.target.checked ? true : null)}
                className="h-4 w-4 text-stone-900 border-stone-900 rounded"
              />
              <label htmlFor="diversityCredit" className="text-xs text-stone-400">
                Diversity credit 
              </label>
            </div>
          </div>
        </div>

        {/* Text Query */}
        <div className="flex flex-col gap-2">
          <h2 className="text-xl font-serif text-stone-900">Text Query :</h2>
          <input
            type="text"
            placeholder="Search by keyword..."
            value={textQuery}
            onChange={(e) => setTextQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="w-full border-2 border-stone-900 rounded px-4 py-3 text-sm font-mono bg-white text-stone-900 placeholder-stone-300 focus:outline-none focus:ring-2 focus:ring-stone-900"
          />
        </div>

        {/* Search Button */}
        <div className="flex justify-center">
          <button
            onClick={handleSearch}
            className="px-12 py-3 bg-stone-900 text-stone-100 text-sm font-mono tracking-widest rounded hover:bg-stone-700 active:scale-95 transition-all"
          >
            Search
          </button>
        </div>

        {/* Backend answer display */}
        {loading && <p className="text-sm text-stone-500">Loading...</p>}
        {error && <p className="text-sm text-red-600">{error}</p>}
        {answer && (
          <div className="mt-4 p-4 bg-white border-2 border-stone-900 rounded">
            <pre className="whitespace-pre-wrap text-sm text-stone-800">{answer}</pre>
          </div>
        )}
      </div>
    </div>
  );
}