// /submit (P161 B1e, F-D120; P167a): ajukan bot penerbit (aturan buatan penerbit + universe, ditandatangani dompet) + papan pipa publik.
import type { Metadata } from "next";
import SubmitView from "@/components/submit/SubmitView";

export const metadata: Metadata = {
  title: "Submit a bot — Fabius",
  description: "Write your own trading rule and submit it. Fabius' public gates review it, it runs forward on paper for 60 days, then it can take a slot.",
};

export default function Page() {
  return <SubmitView />;
}
