import ContactForm from '@/components/contact-form';
import Twin from '@/components/twin';

const CERTIFICATIONS = [
  'AWS Generative AI Developer - Professional',
  'AWS Machine Learning Engineer - Associate',
  'AWS Solutions Architect - Associate',
  'AWS AI Practitioner',
];

export default function Home() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#e2e8f0_0%,_#f8fafc_35%,_#eef2ff_100%)]">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:py-12">
        <section className="mb-6 rounded-3xl border border-white/70 bg-white/80 p-6 shadow-xl shadow-slate-200/60 backdrop-blur sm:p-8">
          <div className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr] lg:items-start">
            <div>
              <div className="mb-4 inline-flex items-center rounded-full border border-slate-300 bg-white px-3 py-1 text-xs font-medium tracking-wide text-slate-600 uppercase">
                Welcome to Tumelo&apos;s Portfolio
              </div>
              <h1 className="text-3xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
                Hi, I&apos;m Tumelo. I design and deploy production-grade AI systems.
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">
                I build reliable AI products that move from prototype to production, with strong backend engineering,
                cloud infrastructure, and measurable business impact.
              </p>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">
                Chat below to evaluate my technical depth, deployment decisions, and real-world system design approach.
              </p>
              <div className="mt-5 flex flex-wrap gap-2 text-sm">
                {['AI Applications', 'Production Deployment', 'FastAPI + Next.js', 'Cloud Integrations'].map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-slate-700"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <aside className="rounded-2xl border border-slate-800/80 bg-slate-950 p-5 text-slate-100 shadow-lg">
              <p className="text-xs font-semibold tracking-[0.18em] text-slate-400 uppercase">
                Credibility Snapshot
              </p>
              <p className="mt-3 text-sm text-slate-200">
                6+ years delivering AI/ML systems with an engineering-first approach to production reliability.
              </p>
              <p className="mt-4 text-[11px] font-semibold tracking-[0.14em] text-amber-200/90 uppercase">
                AWS Certifications
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {CERTIFICATIONS.map((cert) => (
                  <span
                    key={cert}
                    className="rounded-full border border-amber-300/35 bg-amber-300/10 px-3 py-1 text-[11px] font-medium text-amber-100"
                  >
                    {cert}
                  </span>
                ))}
              </div>
            </aside>
          </div>
        </section>

        <div className="h-[680px] sm:h-[720px]">
          <Twin />
        </div>

        <ContactForm />

        <footer className="mt-6 text-center text-sm text-slate-500">
          <p>Thanks for taking the time to explore my work.</p>
        </footer>
      </div>
    </main>
  );
}
