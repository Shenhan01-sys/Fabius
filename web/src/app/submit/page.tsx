// /submit (P161 B1e, F-D120): ajukan bot penerbit (metode terkunci + satu parameter + universe, ditandatangani dompet) + papan pipa publik.
import type { Metadata } from "next";
import SubmitView from "@/components/submit/SubmitView";

export const metadata: Metadata = {
  title: "Submit a bot — Fabius",
  description: "Submit a bot built on one of Fabius' locked methods. Public gates review it, it runs forward on paper for 60 days, then it can take a slot.",
};

export default function Page() {
  return <SubmitView />;
}
