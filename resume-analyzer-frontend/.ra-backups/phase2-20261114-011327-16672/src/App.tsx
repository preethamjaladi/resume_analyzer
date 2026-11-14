import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import Landing from "./pages/Landing";
import Analyzer from "./pages/Analyzer";

type View = "landing" | "analyzer";

const viewFromHash = (): View =>
  window.location.hash === "#/analyzer" ? "analyzer" : "landing";

export default function App() {
  const [view, setView] = useState<View>(viewFromHash);

  useEffect(() => {
    const syncView = () => setView(viewFromHash());
    window.addEventListener("hashchange", syncView);
    return () => window.removeEventListener("hashchange", syncView);
  }, []);

  const navigate = (nextView: View) => {
    window.location.hash = nextView === "analyzer" ? "/analyzer" : "/";
    setView(nextView);
    window.scrollTo({ top: 0, behavior: "auto" });
  };

  if (view === "analyzer") {
    return (
      <>
        <div className="ra-back-bar">
          <button type="button" onClick={() => navigate("landing")}>
            <ArrowLeft size={16} aria-hidden="true" />
            Back to home
          </button>
          <span>Resume Analyzer</span>
        </div>
        {/* Existing analyzer retained until its redesign phase. */}
        <Analyzer />
      </>
    );
  }

  return <Landing onStart={() => navigate("analyzer")} />;
}
