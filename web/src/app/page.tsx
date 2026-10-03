import snapshot from "../../public/data/snapshot.json";
import Landing from "@/components/Landing";
import type { Snapshot } from "@/lib/snapshot";

export default function Page() {
  return <Landing snapshot={snapshot as unknown as Snapshot} />;
}
