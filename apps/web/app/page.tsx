// Stage 0 placeholder — proves the Next.js app boots and serves a real route.
// No workspace UI belongs here yet; that starts in later stages per the
// build roadmap. Do not add feature UI to this file without checking
// which stage it belongs to.
export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-2 bg-zinc-50 px-6 text-center dark:bg-black">
      <h1 className="text-2xl font-semibold tracking-tight text-black dark:text-zinc-50">
        TrustLake
      </h1>
      <p className="text-sm text-zinc-500 dark:text-zinc-400">
        Check it. Clean it. Understand it. Model it. Predict with it.
      </p>
      <p className="mt-8 text-xs text-zinc-400 dark:text-zinc-600">
        Stage 0 — environment scaffold. No workspace features yet.
      </p>
    </main>
  );
}
