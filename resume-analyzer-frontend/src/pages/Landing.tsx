import Header from "../components/layout/Header";
import Hero from "../components/landing/Hero";
import FeatureShowcase from "../components/landing/FeatureShowcase";
import HowItWorks from "../components/landing/HowItWorks";

type Props = { onStart: () => void };

export default function Landing({ onStart }: Props) {
  return (
    <div className="ra-app">
      <Header onStart={onStart} />
      <main><Hero onStart={onStart} /><div className="ra-manifesto" aria-label="Our principles"><span>Honest scoring</span><span className="ra-manifesto-star">✳</span><span>Verified evidence</span><span className="ra-manifesto-star">✳</span><span>Your final say</span></div><FeatureShowcase /><HowItWorks onStart={onStart}/></main>
      <footer className="ra-footer"><a href="#top" className="ra-brand"><span className="ra-brand__emoji" aria-hidden="true">🖥️</span><span>Resume Analyzer</span></a><p>Thoughtful tools for your next opportunity.</p><span>© {new Date().getFullYear()} Resume Analyzer</span></footer>
    </div>
  );
}
