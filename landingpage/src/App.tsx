import { AuroraBackground } from "./components/Brand";
import { Nav } from "./sections/Nav";
import { Hero } from "./sections/Hero";
import { Compatibility } from "./sections/Compatibility";
import { Features } from "./sections/Features";
import { HowItWorks } from "./sections/HowItWorks";
import { Metrics } from "./sections/Metrics";
import { Pricing } from "./sections/Pricing";
import { Faq } from "./sections/Faq";
import { Footer } from "./sections/Footer";

export default function App() {
  return (
    <div className="relative min-h-screen">
      <AuroraBackground />
      <div className="relative z-10">
        <Nav />
        <main>
          <Hero />
          <Compatibility />
          <Features />
          <HowItWorks />
          <Metrics />
          <Pricing />
          <Faq />
        </main>
        <Footer />
      </div>
    </div>
  );
}
