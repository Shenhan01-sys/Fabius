"use client";

import { LangProvider } from "./lang";
import Nav from "./Nav";
import Hero from "./hero/Hero";
import Journey from "./sections/Journey";
import ProofFeed from "./sections/ProofFeed";
import Book from "./sections/Book";
import Doors from "./sections/Doors";
import { Claims, Footer } from "./sections/Closing";
import type { Snapshot } from "@/lib/snapshot";

export default function Landing({ snapshot }: { snapshot: Snapshot }) {
  return (
    <LangProvider>
      <div className="p-2 sm:p-3">
        <Nav />
        <Hero s={snapshot} />
        <Journey />
        <ProofFeed s={snapshot} />
        <Book s={snapshot} />
        <Doors s={snapshot} />
        <Claims />
        <Footer s={snapshot} />
      </div>
    </LangProvider>
  );
}
