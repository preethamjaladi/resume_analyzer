import { ArrowUpRight } from "lucide-react";

type Props = { onStart: () => void };
const steps = [
  { number: "01", title: "Share your resume", body: "Paste your resume and the job description you want to target." },
  { number: "02", title: "Understand your alignment", body: "Explore a weighted match score, individual requirements, and supporting evidence." },
  { number: "03", title: "Make it yours", body: "Correct any assessments, review suggestions, and approve only the edits you want." },
];

export default function HowItWorks({ onStart }: Props) {
  return (
    <section className="ra-how" id="how-it-works">
      <div className="ra-how-inner ra-section"><div className="ra-section-heading"><div><span className="ra-section-kicker">THE PROCESS</span><h2>Three steps.<br/><em>One stronger story.</em></h2></div><p>Designed to feel simple, even when the technology underneath isn't.</p></div>
        <div className="ra-steps">{steps.map((step) => <div className="ra-step" key={step.number}><div className="ra-step-index">{step.number}</div><h3>{step.title}</h3><p>{step.body}</p></div>)}</div>
        <div className="ra-final-cta"><div><span className="ra-section-kicker">READY WHEN YOU ARE</span><h2>Make your next<br/>application <em>count.</em></h2><p>Clear feedback. Thoughtful improvements. Your experience, told better.</p></div><button type="button" className="ra-button ra-button--primary ra-button--large" onClick={onStart}>Get started <ArrowUpRight size={19} aria-hidden="true" /></button></div>
      </div>
    </section>
  );
}
