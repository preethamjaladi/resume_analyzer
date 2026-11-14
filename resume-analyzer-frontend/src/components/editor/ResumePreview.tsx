import { Download, FileText } from "lucide-react";

type Props = { content: string; onDownload: () => void };
export default function ResumePreview({ content, onDownload }: Props) {
  return <section className="ra-ws-paper-wrap" aria-label="Approved resume preview">
    <div className="ra-ws-paper-toolbar"><span><FileText size={17}/> Approved resume text</span><button type="button" onClick={onDownload}><Download size={15}/> Download .txt</button></div>
    <div className="ra-ws-paper"><pre>{content}</pre></div>
  </section>;
}
