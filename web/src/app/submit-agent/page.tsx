// /submit-agent (P169, F-D123): agent luar mendaftar di halaman sendiri (terpisah dari /submit untuk bot): pull masukan tiap siklus, jawab bertanda tangan.
import type { Metadata } from "next";
import SubmitAgentView from "@/components/submit-agent/SubmitAgentView";

export const metadata: Metadata = {
  title: "Submit an agent — Fabius",
  description: "Bring your own AI agent to Fabius' 5-minute desk: register with your ERC-8004 identity, pull the input each cycle, answer with a signed JSON. Trial seat first.",
};

export default function Page() {
  return <SubmitAgentView />;
}
