import { useState } from "react";
import './App.css'

const COURSES = [
  { id: 1, name: "COMP 140", dept: "Computer Science", distribution: "Quantitative" },
  { id: 2, name: "MATH 212", dept: "Mathematics", distribution: "Quantitative" },
  { id: 3, name: "ENGL 205", dept: "English", distribution: "Humanities" },
  { id: 4, name: "PHYS 101", dept: "Physics", distribution: "Natural Sciences" },
  { id: 5, name: "HIST 310", dept: "History", distribution: "Social Sciences" },
];

const DEPARTMENTS = ["All", "Computer Science", "Mathematics", "English", "Physics", "History"];
const DISTRIBUTIONS = ["All", "Group I", "Group II", "Group III"];
const ANALYZINGS = ["All", "Lecture", "Seminar", "Lab"];

export default function CourseSearch() {
  const [selected, setSelected] = useState([COURSES[0], COURSES[1]]);
  const [department, setDepartment] = useState("All");
  const [distribution, setDistribution] = useState("All");
  const [analyzing, setAnalyzing] = useState("All");
  const [textQuery, setTextQuery] = useState("");
  const [results, setResults] = useState(null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const handleSearch = async () => {
    // send the natural-language query to the backend API for retrieval/generation
    if (!textQuery) return;
    setLoading(true);
    setError(null);
    setAnswer("");
    try {
      const res = await fetch('/api/ask/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: textQuery, name: 'Frontend' }),
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

  const toggleSelect = (course) => {
    setSelected((prev) =>
      prev.find((c) => c.id === course.id)
        ? prev.filter((c) => c.id !== course.id)
        : [...prev, course]
    );
  };

  const isSelected = (course) => !!selected.find((c) => c.id === course.id);

  return (
    <div className="min-h-screen bg-stone-100 flex justify-center items-start p-10 font-mono">
      <div className="w-full max-w-xl flex flex-col gap-5">

        {/* Title */}
        <h1 className="text-3xl font-serif tracking-tight text-stone-900 border-b-2 border-stone-900 pb-2">
          Course Search
        </h1>

        {/* Selected Courses Panel */}
        <div className="border-2 border-stone-900 rounded overflow-hidden bg-white">
          <button
            className="w-full flex justify-between items-center px-4 py-3 bg-stone-100 border-b border-stone-900 text-sm text-stone-500 hover:bg-stone-200 transition-colors"
            onClick={() => setDropdownOpen((o) => !o)}
          >
            <span>Course / Department . . .</span>
            <span className="text-stone-900">{dropdownOpen ? "▴" : "▾"}</span>
          </button>

          {/* Selected list */}
          <div>
            {selected.length === 0 && (
              <p className="px-4 py-3 text-sm text-stone-400">No courses selected</p>
            )}
            {selected.map((c) => (
              <div
                key={c.id}
                className="flex justify-between items-center px-4 py-3 border-b border-stone-100 hover:bg-stone-50 cursor-pointer group"
                onClick={() => toggleSelect(c)}
              >
                <span className="text-sm font-medium text-blue-700">{c.name}</span>
                <span className="text-xs text-stone-300 group-hover:text-stone-500 transition-colors">✕</span>
              </div>
            ))}
          </div>

          {/* Dropdown course picker */}
          {dropdownOpen && (
            <div className="border-t border-stone-200">
              {COURSES.filter((c) => !isSelected(c)).map((c) => (
                <div
                  key={c.id}
                  className="flex justify-between items-center px-4 py-2 hover:bg-stone-50 cursor-pointer"
                  onClick={() => toggleSelect(c)}
                >
                  <span className="text-sm text-stone-700">{c.name}</span>
                  <span className="text-xs text-stone-400">{c.dept}</span>
                </div>
              ))}
              {COURSES.filter((c) => !isSelected(c)).length === 0 && (
                <p className="px-4 py-2 text-sm text-stone-400">All courses selected</p>
              )}
            </div>
          )}
        </div>

        {/* Filters */}
        <div className="flex flex-col gap-3">
          <h2 className="text-xl font-serif text-stone-900">Filter :</h2>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-xs uppercase tracking-widest text-stone-400">Department</label>
              <select
                className="border-2 border-stone-900 rounded px-3 py-2 text-sm bg-white text-stone-900 font-mono focus:outline-none focus:ring-2 focus:ring-stone-900"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
              >
                {DEPARTMENTS.map((d) => <option key={d}>{d}</option>)}
              </select>
            </div>

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
              <label className="text-xs uppercase tracking-widest text-stone-400">Analyzing</label>
              <select
                className="border-2 border-stone-900 rounded px-3 py-2 text-sm bg-white text-stone-900 font-mono focus:outline-none focus:ring-2 focus:ring-stone-900"
                value={analyzing}
                onChange={(e) => setAnalyzing(e.target.value)}
              >
                {ANALYZINGS.map((a) => <option key={a}>{a}</option>)}
              </select>
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